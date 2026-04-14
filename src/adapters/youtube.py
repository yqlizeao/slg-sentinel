"""
SLG Sentinel — YouTube 适配器

三工具组合策略（全部免登录，GitHub Actions 完全可用）：
  - yt-dlp（主力）: ytsearch 搜索 + 视频元数据提取
  - scrapetube: 按频道/播放量获取频道视频列表
  - youtube-comment-downloader: 高效批量评论采集

礼貌爬取：yt-dlp 内部自带频率控制，评论采集添加适当延迟。
"""

from __future__ import annotations

import logging
import time
from datetime import datetime
from typing import List, Optional

from src.adapters.base import BaseAdapter
from src.core.models import Comment, VideoSnapshot

logger = logging.getLogger(__name__)

# 评论采集间隔（秒）
COMMENT_INTERVAL = 1.0


class YouTubeAdapter(BaseAdapter):
    """
    YouTube 适配器（三工具组合，全部免登录）

    - search_videos: yt-dlp ytsearch
    - get_video_info: yt-dlp extract_info
    - get_channel_videos: scrapetube
    - get_comments: youtube-comment-downloader
    """

    def __init__(self, max_comments_per_video: int = 200):
        """
        Args:
            max_comments_per_video: 每个视频最多采集评论数（默认 200）
        """
        self.max_comments_per_video = max_comments_per_video

    # ─── BaseAdapter 抽象方法实现 ──────────────────────────────────

    def search_videos(
        self, keyword: str, max_results: int = 20, **kwargs
    ) -> List[VideoSnapshot]:
        """
        搜索视频——yt-dlp ytsearch。

        Args:
            keyword: 搜索关键词
            max_results: 最大结果数（默认 20）

        Returns:
            VideoSnapshot 列表
        """
        try:
            import yt_dlp

            ydl_opts = {
                "quiet": True,
                "no_warnings": True,
                "extract_flat": False,
                "skip_download": True,
                "ignoreerrors": True,
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                result = ydl.extract_info(
                    f"ytsearch{max_results}:{keyword}", download=False
                )

            if not result or "entries" not in result:
                logger.warning(f"YouTube 搜索 '{keyword}' 无结果")
                return []

            today = datetime.now().strftime("%Y-%m-%d")
            snapshots = []
            for entry in result.get("entries", []):
                if not entry:
                    continue
                snap = self._entry_to_snapshot(entry, today)
                if snap:
                    snapshots.append(snap)

            logger.info(f"YouTube 搜索 '{keyword}' 获取 {len(snapshots)} 条视频")
            return snapshots

        except Exception as e:
            logger.error(f"YouTube 搜索失败 '{keyword}': {e}")
            return []

    def get_video_info(self, video_id: str) -> Optional[VideoSnapshot]:
        """
        获取单个视频元数据——yt-dlp。

        Args:
            video_id: YouTube 视频 ID（11位）

        Returns:
            VideoSnapshot 实例，失败返回 None
        """
        try:
            import yt_dlp

            url = f"https://www.youtube.com/watch?v={video_id}"
            ydl_opts = {
                "quiet": True,
                "no_warnings": True,
                "skip_download": True,
                "ignoreerrors": True,
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)

            if not info:
                return None

            today = datetime.now().strftime("%Y-%m-%d")
            snap = self._entry_to_snapshot(info, today)
            if snap:
                logger.info(f"获取 YouTube 视频详情: {video_id} — {snap.title}")
            return snap

        except Exception as e:
            logger.error(f"获取 YouTube 视频 {video_id} 详情失败: {e}")
            return None

    def get_comments(
        self, video_id: str, sort_by: int = 0, **kwargs
    ) -> List[Comment]:
        """
        获取视频评论——youtube-comment-downloader。

        Args:
            video_id: YouTube 视频 ID（11位）
            sort_by: 排序方式（0=热度，1=时间）

        Returns:
            Comment 列表
        """
        try:
            from youtube_comment_downloader import YoutubeCommentDownloader, SORT_BY_POPULAR, SORT_BY_RECENT

            url = f"https://www.youtube.com/watch?v={video_id}"
            sort = SORT_BY_POPULAR if sort_by == 0 else SORT_BY_RECENT

            downloader = YoutubeCommentDownloader()
            comments_gen = downloader.get_comments_from_url(url, sort_by=sort)

            comments = []
            for raw in comments_gen:
                if len(comments) >= self.max_comments_per_video:
                    break
                try:
                    # 解析点赞数（youtube-comment-downloader 返回 '1.9K' 格式）
                    votes_raw = raw.get("votes", "0") or "0"
                    like_count = self._parse_view_count(str(votes_raw))
                    c = Comment(
                        platform="youtube",
                        video_id=video_id,
                        comment_id=raw.get("cid", ""),
                        author=raw.get("author", ""),
                        author_id=raw.get("channel", ""),
                        content=raw.get("text", ""),
                        like_count=like_count,
                        reply_count=int(raw.get("reply_count", 0) or 0),
                        publish_time=raw.get("time", ""),
                        ip_location="",  # YouTube 不提供 IP 属地
                        sentiment="",
                        mentioned_games="",
                    )
                    comments.append(c)
                except Exception as e:
                    logger.warning(f"解析评论失败: {e}")

            logger.info(f"YouTube 评论 {video_id} 采集 {len(comments)} 条")
            time.sleep(COMMENT_INTERVAL)
            return comments

        except Exception as e:
            logger.error(f"获取 YouTube 视频 {video_id} 评论失败: {e}")
            return []

    # ─── 额外方法（非 BaseAdapter 接口）──────────────────────────

    def get_channel_videos(
        self,
        channel_id: str,
        sort_by: str = "popular",
        limit: int = 50,
    ) -> List[VideoSnapshot]:
        """
        获取频道视频列表——scrapetube（免登录，按播放量排序）。

        Args:
            channel_id: YouTube 频道 ID（UCxxxxxxxx...）
            sort_by: 排序方式（'popular' / 'newest' / 'oldest'）
            limit: 最大视频数量（默认 50）

        Returns:
            VideoSnapshot 列表（仅基础信息，如需完整 stat 需调 get_video_info）
        """
        try:
            import scrapetube

            videos_gen = scrapetube.get_channel(
                channel_id, sort_by=sort_by, limit=limit
            )

            today = datetime.now().strftime("%Y-%m-%d")
            snapshots = []
            for v in videos_gen:
                video_id = v.get("videoId", "")
                if not video_id:
                    continue
                # scrapetube 返回基础信息，view_count 等需要 yt-dlp 补全
                title_runs = v.get("title", {}).get("runs", [])
                title = "".join(r.get("text", "") for r in title_runs)
                # 尝试解析视频数量（格式: "1.2M views"）
                view_text = (
                    v.get("viewCountText", {}).get("simpleText", "")
                    or v.get("viewCountText", {}).get("runs", [{}])[0].get("text", "")
                )
                view_count = self._parse_view_count(view_text)

                snap = VideoSnapshot(
                    platform="youtube",
                    video_id=video_id,
                    title=title,
                    author="",       # scrapetube 不直接提供，需补全
                    author_id=channel_id,
                    snapshot_date=today,
                    view_count=view_count,
                    like_count=0,
                    comment_count=0,
                    share_count=0,
                    favorite_count=0,
                    coin_count=0,
                    danmaku_count=0,
                    publish_date="",
                    tags="",
                    url=f"https://www.youtube.com/watch?v={video_id}",
                )
                snapshots.append(snap)

            logger.info(f"频道 {channel_id} 获取 {len(snapshots)} 条视频（scrapetube）")
            return snapshots

        except Exception as e:
            logger.error(f"获取 YouTube 频道 {channel_id} 视频失败: {e}")
            return []

    # ─── 私有工具方法 ─────────────────────────────────────────────

    def _entry_to_snapshot(self, entry: dict, today: str) -> Optional[VideoSnapshot]:
        """将 yt-dlp entry 转换为 VideoSnapshot"""
        try:
            video_id = entry.get("id", "")
            if not video_id:
                return None

            # 发布日期：yt-dlp 格式 YYYYMMDD
            upload_date = entry.get("upload_date", "") or ""
            if len(upload_date) == 8:
                publish_date = f"{upload_date[:4]}-{upload_date[4:6]}-{upload_date[6:8]}"
            else:
                publish_date = upload_date

            # Tags
            tags = entry.get("tags", []) or []
            tags_str = ",".join(tags[:20]) if tags else ""  # 最多 20 个 tag

            return VideoSnapshot(
                platform="youtube",
                video_id=video_id,
                title=entry.get("title", ""),
                author=entry.get("channel", "") or entry.get("uploader", ""),
                author_id=entry.get("channel_id", "") or entry.get("uploader_id", ""),
                snapshot_date=today,
                view_count=int(entry.get("view_count", 0) or 0),
                like_count=int(entry.get("like_count", 0) or 0),
                comment_count=int(entry.get("comment_count", 0) or 0),
                share_count=0,      # YouTube 不提供分享数
                favorite_count=0,   # YouTube 不提供收藏数
                coin_count=0,
                danmaku_count=0,
                publish_date=publish_date,
                tags=tags_str,
                url=f"https://www.youtube.com/watch?v={video_id}",
            )
        except Exception as e:
            logger.warning(f"转换 yt-dlp entry 失败: {e}")
            return None

    @staticmethod
    def _parse_view_count(view_text: str) -> int:
        """解析 '1.2M views' 格式的播放量"""
        try:
            if not view_text:
                return 0
            text = view_text.lower().replace(",", "").replace(" views", "").strip()
            if "k" in text:
                return int(float(text.replace("k", "")) * 1_000)
            elif "m" in text:
                return int(float(text.replace("m", "")) * 1_000_000)
            elif "b" in text:
                return int(float(text.replace("b", "")) * 1_000_000_000)
            else:
                return int(text) if text.isdigit() else 0
        except Exception:
            return 0
