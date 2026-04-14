"""
SLG Sentinel — 周报生成模块

收集全平台上一周数据的增量，执行情感分析汇总，最后输出为 Markdown 报表。
"""

from __future__ import annotations

import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Set

from src.analysis.sentiment import SentimentAnalyzer
from src.core.config import SentinelConfig
from src.core.csv_store import CSVStore
from src.core.models import Comment, VideoSnapshot

logger = logging.getLogger(__name__)


class WeeklyReportGenerator:
    """周报生成器"""

    def __init__(self, config: SentinelConfig):
        self.config = config
        self.store = CSVStore()
        self.sentiment = SentimentAnalyzer()

    def generate(
        self, date_str: str | None = None, output_dir: str = "reports/"
    ) -> Path:
        """
        生成周报
        
        Args:
            date_str: 报表日期，默认今天
            output_dir: 输出目录
            
        Returns:
            生成的 Markdown 文件路径
        """
        if date_str is None:
            date_str = datetime.now().strftime("%Y-%m-%d")

        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        file_path = output_path / f"{date_str}_weekly_report.md"

        platforms = ["bilibili", "youtube", "taptap"]
        
        report_lines = [
            f"# SLG Sentinel 竞品舆情周报",
            f"**生成日期：** {date_str}",
            f"**数据周期：** {date_str} 往前推 7 天",
            "",
            "---",
            ""
        ]

        # 1. 汇总视频各项数据增量
        report_lines.append("## 1. 内容热度增量（周度）")
        report_lines.append("")
        
        # 记录有增量的实体，后续查询评论
        active_video_ids = {"bilibili": set(), "youtube": set(), "taptap": set()}
        
        total_view_delta = 0
        total_comment_delta = 0

        for platform in platforms:
            try:
                snapshots = self.store.load(VideoSnapshot, platform, "snapshots", date_str=date_str)
            except Exception:
                snapshots = []
                
            if not snapshots:
                continue
                
            report_lines.append(f"### {platform.capitalize()} 平台")
            report_lines.append("| 视频标题/游戏 | 播放量增量 | 互动量(赞+评) | 地址 |")
            report_lines.append("| --- | --- | --- | --- |")
            
            # 按播放量增量排序
            video_deltas = []
            for s in snapshots:
                if s.platform != platform:
                    continue
                if not s.video_id:
                    continue
                delta = self.store.get_weekly_delta(platform, s.video_id, reference_date=date_str)
                # 只有计算出增量（不为0）或者本周新发现的视频才上榜
                if delta.get('view_count', 0) > 0 or s.view_count > 0:
                    delta_view = delta.get('view_count', s.view_count) 
                    delta_interact = delta.get('like_count', s.like_count) + delta.get('comment_count', s.comment_count)
                    video_deltas.append({
                        "snap": s,
                        "delta_view": delta_view,
                        "delta_interact": delta_interact
                    })

            # 取前 10
            video_deltas.sort(key=lambda x: x["delta_view"], reverse=True)
            for v in video_deltas[:10]:
                snap = v["snap"]
                title_short = snap.title[:20] + "..." if len(snap.title) > 20 else snap.title
                title_short = title_short.replace("|", "/") # 防止破坏 markdown 表格
                report_lines.append(f"| {title_short} | +{v['delta_view']:,} | +{v['delta_interact']:,} | [链接]({snap.url}) |")
                
                active_video_ids[platform].add(snap.video_id)
                total_view_delta += v['delta_view']
                total_comment_delta += v['snap'].comment_count
                
            report_lines.append("")

        if total_view_delta == 0:
            report_lines.append("> ⚠️ 本周暂无视频播放量增量数据。可能是初次运行系统，缺乏上周对比快照。")
            report_lines.append("")

        # 2. 情感分析汇总
        report_lines.append("## 2. 玩家情感与竞品提及")
        report_lines.append("")
        
        report_lines.append("| 平台 | 正向评论 | 负向评论 | 竞品提及 |")
        report_lines.append("| --- | --- | --- | --- |")

        for platform in platforms:
            v_ids = active_video_ids[platform]
            if not v_ids and platform == "taptap":
                 # TapTap 的特殊性：如果视频增量部分没抓到，强制去读当天的所有 reviews
                 v_ids = {"all"} 
            
            if not v_ids:
                continue

            try:
                if platform == "taptap":
                    comments = self.store.load(Comment, platform, "reviews", date_str=date_str)
                else:
                    comments = []
                    for vid in v_ids:
                        comments.extend(self.store.load(Comment, platform, "comments", date_str=date_str, video_id=vid))
            except Exception as e:
                logger.error(f"加载 {platform} 评论失败: {e}")
                comments = []

            if not comments:
                report_lines.append(f"| {platform.capitalize()} | 0 | 0 | 无 |")
                continue

            # 执行批量情感分析
            self.sentiment.batch_analyze(comments)

            pos_count = sum(1 for c in comments if c.sentiment == "positive")
            neg_count = sum(1 for c in comments if c.sentiment == "negative")
            
            mentions_counter = {}
            for c in comments:
                if c.mentioned_games:
                    for g in c.mentioned_games.split(","):
                        mentions_counter[g] = mentions_counter.get(g, 0) + 1
            
            # 取 top 3 竞品
            top_mentions = sorted(mentions_counter.items(), key=lambda x: x[1], reverse=True)[:3]
            mentions_str = ", ".join([f"{k}({v})" for k, v in top_mentions]) if top_mentions else "无"

            report_lines.append(f"| {platform.capitalize()} | {pos_count} | {neg_count} | {mentions_str} |")

        report_lines.append("")
        
        # 3. 典型负面舆情摘录
        report_lines.append("## 3. 核心负面反馈摘选（预警）")
        report_lines.append("")
        
        negative_flag = False
        for platform in platforms:
            try:
                if platform == "taptap":
                    comments = self.store.load(Comment, platform, "reviews", date_str=date_str)
                else:
                    # 遍历目录下所有当天评论
                    comments = []
                    dir_path = self.store.data_dir / platform / "comments"
                    if dir_path.exists():
                        for f in dir_path.glob(f"{date_str}_*_comments.csv"):
                            comments.extend(self.store._load_single_file(Comment, f))
            except Exception:
                continue

            # 分析并过滤高赞负面
            self.sentiment.batch_analyze(comments)
            bad_comments = [c for c in comments if c.sentiment == "negative"]
            bad_comments.sort(key=lambda c: c.like_count, reverse=True)
            
            if bad_comments:
                negative_flag = True
                report_lines.append(f"### {platform.capitalize()} 平台")
                for c in bad_comments[:3]:
                    content_short = c.content[:100].replace('\n', ' ') + "..." if len(c.content) > 100 else c.content.replace('\n', ' ')
                    report_lines.append(f"- **[获赞 {c.like_count}]** {content_short}")
                report_lines.append("")

        if not negative_flag:
            report_lines.append("> ✅ 本周未监测到明显的高赞负面舆情。")
            report_lines.append("")

        # 写入文件
        with open(file_path, "w", encoding="utf-8") as f:
            f.write("\n".join(report_lines))

        logger.info(f"周报已生成: {file_path}")
        return file_path
