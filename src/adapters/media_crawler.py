"""
SLG Sentinel — MediaCrawler 适配桥接器

MediaCrawler 是一个开源的强大本地爬虫工具，擅长抓取小红书、抖音、快手等平台。
本模块并不直接抓取，而是通过读取 MediaCrawler 运行后产生的本地 CSV 文件，将其映射到
SLG Sentinel 的统一模型并入库，从而达成数据融合。

假设 MediaCrawler 产出目录结构：
MediaCrawler/data/douyin/
  ├── aweme_xxxx.csv  (视频或图文数据)
  └── aweme_xxxx_comments.csv (评论数据)
"""

from __future__ import annotations

import csv
import logging
import subprocess
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from src.core.models import Comment, VideoSnapshot

logger = logging.getLogger(__name__)


class MediaCrawlerBridge:

    @staticmethod
    def _safe_int(val: str | None, support_wan: bool = False) -> int:
        """安全地将字符串转换为整数，支持 'w'/'万' 后缀"""
        if not val:
            return 0
        val = str(val).strip()
        if val.isdigit():
            return int(val)
        if support_wan and "w" in val.lower():
            try:
                return int(float(val.lower().replace("w", "")) * 10000)
            except ValueError:
                return 0
        return 0

    def __init__(self, media_crawler_root_dir: str):
        self.mc_root = Path(media_crawler_root_dir)
        self.mc_data_dir = self.mc_root / "data"
        if not self.mc_root.exists():
            raise FileNotFoundError(f"找不到 MediaCrawler 根目录(沙盒挂载点): {self.mc_root}")

    def run_spider(self, platform: str, keywords: List[str]) -> bool:
        """
        通过 subprocess 调度 MediaCrawler 本地实例，绕过反爬机制
        """
        MC_CLI_MAP = {
            "xiaohongshu": "xhs",
            "douyin": "douyin",
            "kuaishou": "kuaishou",
        }
        mc_platform = MC_CLI_MAP.get(platform, platform)
        kw_str = ",".join(keywords)
        
        # 组装命令，强制使用扫码（最稳），扫搜模式
        cmd = [
            "python", "main.py",
            "--platform", mc_platform,
            "--lt", "qrcode",
            "--type", "search",
            "--keywords", kw_str
        ]
        
        logger.info(f"即将挂载底层隔离沙盒引擎: {' '.join(cmd)}")
        try:
            # 标准输入输出不做 PIPE 拦截，由于 MediaCrawler 强行依赖前端扫码与状态打点
            result = subprocess.run(cmd, cwd=self.mc_root, check=True)
            return result.returncode == 0
        except subprocess.CalledProcessError as e:
            logger.error(f"MediaCrawler 爬虫由于防风控崩溃或主动阻断退出: {e}")
            return False
        except Exception as e:
            logger.error(f"MediaCrawler 引擎挂载崩溃异常: {e}")
            return False

    def import_platform_data(self, platform: str) -> tuple[List[VideoSnapshot], List[Comment]]:
        """
        从 MediaCrawler 产出中导入指定平台（douyin/kuaishou/xiaohongshu）的数据。
        
        MediaCrawler 实际输出目录名：
          xhs       → --platform xiaohongshu
          douyin    → --platform douyin
          kuaishou  → --platform kuaishou
        """
        # 映射 CLI 平台名 → MediaCrawler 实际目录名
        MC_DIR_MAP = {
            "xiaohongshu": "xhs",
            "douyin": "douyin",
            "kuaishou": "kuaishou",
        }
        mc_platform = MC_DIR_MAP.get(platform, platform)
        platform_dir = self.mc_data_dir / mc_platform
        if not platform_dir.exists():
            logger.warning(f"底层沙盒 {self.mc_data_dir} 未下发 {platform} 的数据快照产出...")
            return [], []

        snapshots = []
        comments = []
        today = datetime.now().strftime("%Y-%m-%d")

        for csv_file in platform_dir.glob("*.csv"):
            filename = csv_file.name.lower()
            try:
                if "comment" in filename:
                    comments.extend(self._parse_comments(csv_file, platform))
                else:
                    snapshots.extend(self._parse_videos(csv_file, platform, today))
            except Exception as e:
                logger.error(f"解析 MediaCrawler 文件 {filename} 失败: {e}")

        logger.info(f"MediaCrawler 桥接: {platform} 解析出 {len(snapshots)} 条视频，{len(comments)} 条评论")
        return snapshots, comments

    def _parse_videos(self, csv_file: Path, platform: str, today: str) -> List[VideoSnapshot]:
        snapshots = []
        si = self._safe_int  # 局部别名，减少属性查找
        with open(csv_file, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                # 兼容不统一的表头命名 (小红书为 note_id, 抖音为 aweme_id)
                video_id = row.get("note_id") or row.get("aweme_id") or row.get("video_id")
                if not video_id:
                    continue

                title = row.get("title") or row.get("desc") or ""

                snap = VideoSnapshot(
                    platform=platform,
                    video_id=str(video_id),
                    title=str(title),
                    author=str(row.get("nickname", row.get("author_name", ""))),
                    author_id=str(row.get("user_id", row.get("author_id", ""))),
                    snapshot_date=today,
                    view_count=si(row.get("play_count"), support_wan=True),
                    like_count=si(row.get("liked_count"), support_wan=True) or si(row.get("like_count"), support_wan=True),
                    comment_count=si(row.get("comment_count")) or si(row.get("comments_count")),
                    share_count=si(row.get("share_count")),
                    favorite_count=si(row.get("collected_count")) or si(row.get("collect_count")),
                    coin_count=0,
                    danmaku_count=0,
                    publish_date=str(row.get("create_time", row.get("add_ts", ""))[:10]),
                    tags=str(row.get("tags", "")),
                    url=str(row.get("note_url", row.get("video_url", ""))),
                )
                snapshots.append(snap)
        return snapshots

    def _parse_comments(self, csv_file: Path, platform: str) -> List[Comment]:
        comments = []
        si = self._safe_int
        with open(csv_file, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                video_id = row.get("note_id") or row.get("aweme_id") or row.get("video_id")
                comment_id = row.get("comment_id")
                if not video_id or not comment_id:
                    continue

                c = Comment(
                    platform=platform,
                    video_id=str(video_id),
                    comment_id=str(comment_id),
                    author=str(row.get("nickname", "")),
                    author_id=str(row.get("user_id", "")),
                    content=str(row.get("content", row.get("text", ""))),
                    like_count=si(row.get("like_count")),
                    reply_count=si(row.get("sub_comment_count")),
                    publish_time=str(row.get("create_time", "")),
                    ip_location=str(row.get("ip_location", "")),
                    sentiment="",
                    mentioned_games="",
                )
                comments.append(c)
        return comments
