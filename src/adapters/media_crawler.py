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
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from src.core.models import Comment, VideoSnapshot

logger = logging.getLogger(__name__)


class MediaCrawlerBridge:
    def __init__(self, media_crawler_dir: str):
        self.mc_dir = Path(media_crawler_dir)
        if not self.mc_dir.exists():
            raise FileNotFoundError(f"找不到 MediaCrawler 数据目录: {self.mc_dir}")

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
        platform_dir = self.mc_dir / mc_platform
        if not platform_dir.exists():
            logger.warning(f"MediaCrawler 目录下未找到 {platform} 数据: {platform_dir}")
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
        with open(csv_file, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                # 兼容不统一的表头命名 (小红书为 note_id, 抖音为 aweme_id)
                video_id = row.get("note_id") or row.get("aweme_id") or row.get("video_id")
                if not video_id:
                    continue

                title = row.get("title") or row.get("desc") or ""
                
                # 数字安全转换
                def _safe_int(key: str) -> int:
                    val = row.get(key, "0")
                    if not val:
                        return 0
                    if val.isdigit():
                        return int(val)
                    if "w" in val.lower():
                        return int(float(val.lower().replace("w", "")) * 10000)
                    return 0

                snap = VideoSnapshot(
                    platform=platform,
                    video_id=str(video_id),
                    title=str(title),
                    author=str(row.get("nickname", row.get("author_name", ""))),
                    author_id=str(row.get("user_id", row.get("author_id", ""))),
                    snapshot_date=today,
                    view_count=_safe_int("play_count"),   # 小红书可能无 play_count
                    like_count=_safe_int("liked_count") or _safe_int("like_count"),
                    comment_count=_safe_int("comment_count") or _safe_int("comments_count"),
                    share_count=_safe_int("share_count"),
                    favorite_count=_safe_int("collected_count") or _safe_int("collect_count"),
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
        with open(csv_file, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                video_id = row.get("note_id") or row.get("aweme_id") or row.get("video_id")
                comment_id = row.get("comment_id")
                if not video_id or not comment_id:
                    continue
                
                # 数字安全转换
                def _safe_int(key: str) -> int:
                    val = row.get(key, "0")
                    return int(val) if val and val.isdigit() else 0

                c = Comment(
                    platform=platform,
                    video_id=str(video_id),
                    comment_id=str(comment_id),
                    author=str(row.get("nickname", "")),
                    author_id=str(row.get("user_id", "")),
                    content=str(row.get("content", row.get("text", ""))),
                    like_count=_safe_int("like_count"),
                    reply_count=_safe_int("sub_comment_count"),
                    publish_time=str(row.get("create_time", "")),
                    ip_location=str(row.get("ip_location", "")),
                    sentiment="",
                    mentioned_games="",
                )
                comments.append(c)
        return comments
