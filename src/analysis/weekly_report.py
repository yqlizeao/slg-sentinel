"""
SLG Sentinel — 周报生成模块

收集全平台上一周数据的增量，执行情感分析汇总，最后输出为 Markdown 报表。
"""

from __future__ import annotations

import logging
import os
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Set

from src.analysis.sentiment import SentimentAnalyzer
from src.core.config import SentinelConfig
from src.core.csv_store import CSVStore
from src.core.models import Comment, TapTapReview, VideoSnapshot

logger = logging.getLogger(__name__)


class WeeklyReportGenerator:
    """周报生成器"""

    def __init__(self, config: SentinelConfig):
        self.config = config
        self.store = CSVStore()
        self.sentiment = SentimentAnalyzer()

    @staticmethod
    def _reviews_to_comments(reviews: List[TapTapReview]) -> List[Comment]:
        """将 TapTapReview 列表转换为 Comment 列表（统一分析接口）"""
        return [Comment(
            platform="taptap", video_id=r.game_id, comment_id=r.review_id,
            author=r.author, author_id=r.author_id, content=r.content,
            like_count=r.ups, reply_count=0, publish_time=r.publish_time,
            ip_location="", sentiment="", mentioned_games=""
        ) for r in reviews]

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
        
        # 建立报表随附的 JSON 载荷
        stats_payload = {
            "sentiment": {"positive": 0, "negative": 0, "neutral": 0},
            "mentions": {}
        }

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
                    # TapTap 异构为 TapTapReview，需转换为 Comment 展示
                    reviews = self.store.load(TapTapReview, platform, "reviews", date_str=date_str)
                    comments = self._reviews_to_comments(reviews)
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
            neu_count = sum(1 for c in comments if c.sentiment == "neutral")
            
            stats_payload["sentiment"]["positive"] += pos_count
            stats_payload["sentiment"]["negative"] += neg_count
            stats_payload["sentiment"]["neutral"] += neu_count
            
            mentions_counter = {}
            for c in comments:
                if c.mentioned_games:
                    for g in c.mentioned_games.split(","):
                        g = g.strip()
                        mentions_counter[g] = mentions_counter.get(g, 0) + 1
                        stats_payload["mentions"][g] = stats_payload["mentions"].get(g, 0) + 1
            
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
                    reviews = self.store.load(TapTapReview, platform, "reviews", date_str=date_str)
                    comments = self._reviews_to_comments(reviews)
                else:
                    # 遍历目录下所有当天评论
                    comments = []
                    from src.core.csv_store import VIDEO_PLATFORMS, COMMUNITY_PLATFORMS
                    if platform in VIDEO_PLATFORMS:
                        cat = "video_platforms"
                    elif platform in COMMUNITY_PLATFORMS:
                        cat = "community_platforms"
                    else:
                        cat = "misc_platforms"
                    dir_path = self.store.data_dir / cat / platform / "comments"
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

        # 4. 深度语义聚类摘要（LLM 驱动）
        report_lines.append("## 4. 深度语义宏观洞察")
        report_lines.append("")

        llm_insights = self._generate_llm_insights(platforms, date_str)
        if llm_insights:
            stats_payload["insights"] = llm_insights
            report_lines.append("| 主题 | 情感 | 核心诉求 | 出现次数 | 代表性原文 |")
            report_lines.append("| --- | --- | --- | --- | --- |")
            for item in llm_insights:
                topic = item.get("topic", "未知")
                sentiment = item.get("sentiment", "mixed")
                demand = item.get("core_demand", "").replace("|", "/")
                count = item.get("count", 0)
                quotes = item.get("representative_quotes", [])
                quote_text = "；".join(q[:40].replace("|", "/").replace("\n", " ") for q in quotes[:2])
                report_lines.append(f"| {topic} | {sentiment} | {demand} | {count} | {quote_text} |")
            report_lines.append("")
        else:
            report_lines.append("> ℹ️ 未能生成 LLM 聚类摘要（可能缺少 API Key 或评论数据不足）。")
            report_lines.append("> 请结合上方情感分布与负面预警数据进行人工研判。")
            report_lines.append("")

        # 写入文件
        with open(file_path, "w", encoding="utf-8") as f:
            f.write("\n".join(report_lines))
            
        json_path = output_path / f"{date_str}_weekly_report.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(stats_payload, f, ensure_ascii=False, indent=2)

        logger.info(f"周报已生成: {file_path}")
        return file_path

    def _generate_llm_insights(self, platforms: list[str], date_str: str) -> list[dict]:
        """
        收集高赞评论并调用 LLM 进行主题聚类。

        Returns:
            聚类结果列表，每个元素: {topic, sentiment, core_demand, representative_quotes, count}
            如果 LLM 不可用或无数据则返回空列表。
        """
        try:
            from src.core.llm_client import LLMClient
        except ImportError:
            return []

        llm = LLMClient(self.config)
        provider = llm.get_available_provider()
        if not provider:
            logger.info("未配置任何 LLM API Key，跳过深度语义聚类")
            return []

        # 收集所有平台的评论
        all_comments: list[Comment] = []
        for platform in platforms:
            try:
                if platform == "taptap":
                    reviews = self.store.load(TapTapReview, platform, "reviews", date_str=date_str)
                    all_comments.extend(self._reviews_to_comments(reviews))
                else:
                    from src.core.csv_store import VIDEO_PLATFORMS, COMMUNITY_PLATFORMS
                    cat = "video_platforms" if platform in VIDEO_PLATFORMS else "community_platforms"
                    dir_path = self.store.data_dir / cat / platform / "comments"
                    if dir_path.exists():
                        for f in dir_path.glob(f"{date_str}_*_comments.csv"):
                            all_comments.extend(self.store._load_single_file(Comment, f))
            except Exception:
                continue

        if len(all_comments) < 3:
            logger.info(f"评论数量不足 ({len(all_comments)})，跳过 LLM 聚类")
            return []

        # 取高赞 Top 100
        all_comments.sort(key=lambda c: c.like_count, reverse=True)
        top_comments = all_comments[:100]

        entries = []
        for i, c in enumerate(top_comments):
            text = c.content[:150].replace("\n", " ")
            entries.append(f"[{i}] (赞{c.like_count}) {text}")

        prompt = f"""以下是本周 SLG 手游玩家社区中获赞最高的 {len(entries)} 条评论。
请按核心观点将它们聚类为 5-8 个主题组。

{chr(10).join(entries)}

返回 JSON 数组，每个元素：
[{{"topic": "主题标签（4字以内）", "sentiment": "positive/negative/mixed", "core_demand": "一句话核心诉求", "representative_quotes": ["原文1", "原文2"], "count": 该主题下的评论条数}}]

要求：
- topic 简洁有力，如"氪金焦虑"、"玩法深度"、"画面表现"
- core_demand 是该组玩家的真实诉求
- representative_quotes 选 2 条最有代表性的原文（取前 60 字）
- 只返回 JSON，不要其他内容"""

        try:
            result = llm.chat_json(prompt, provider=provider, temperature=0.3, timeout=120)
            if isinstance(result, list):
                logger.info(f"LLM 聚类成功，识别出 {len(result)} 个主题")
                return result
            return []
        except Exception as e:
            logger.warning(f"LLM 聚类摘要失败: {e}")
            return []
