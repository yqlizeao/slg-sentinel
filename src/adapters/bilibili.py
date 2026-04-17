"""
SLG Sentinel — B站适配器

基于 bilibili-api-python 实现，分为免登录（GitHub Actions 可用）和需 Cookie（仅本地）两部分。
内部自动处理 Wbi 签名，无需手动计算。
异步方法通过 asyncio.run() 在 CLI 层统一调度。

礼貌爬取：每次请求间隔 ≥ 1 秒。
"""

from __future__ import annotations

import asyncio
import logging
import time
from datetime import datetime
from typing import List, Optional

from src.adapters.base import BaseAdapter
from src.core.models import Comment, VideoSnapshot

logger = logging.getLogger(__name__)

# 请求间隔（秒），礼貌爬取
REQUEST_INTERVAL = 1.0


def _run(coro):
    """在当前线程同步运行异步协程"""
    return asyncio.run(coro)


class BilibiliAdapter(BaseAdapter):
    """
    B站适配器（bilibili-api-python）

    免登录能力（GitHub Actions 可用）：
      - search_videos: 关键词搜索
      - get_video_info: 视频详情
      - get_comments: 评论（建议 ≤ 10 页）
      - get_hot_videos: 游戏热门视频

    需 Cookie 能力（仅本地运行）：
      - get_user_favorites: 用户公开收藏夹
      - get_user_followings: 用户关注列表
    """

    def __init__(self, credential=None):
        """
        Args:
            credential: bilibili_api.Credential 实例（可选，需登录功能时传入）
        """
        self.credential = credential

    # ─── 公开接口（实现 BaseAdapter 抽象方法）────────────────────────

    def search_videos(
        self, keyword: str, limit: int = 20, **kwargs
    ) -> List[VideoSnapshot]:
        """
        搜索视频——免登录，Wbi 签名自动处理。

        Args:
            keyword: 搜索关键词
            limit: 最大获取数量 (默认 20)
            kwargs:
                order: 排序方式 (totalrank, click, pubdate, stow)

        Returns:
            VideoSnapshot 列表
        """
        order = kwargs.get("order", "totalrank")
        return _run(self._async_search_videos(keyword, limit, order))

    def get_video_info(self, video_id: str) -> VideoSnapshot:
        """
        获取视频详情——免登录。

        Args:
            video_id: BV 号，如 BV1xxxxxxxxxx

        Returns:
            VideoSnapshot 实例
        """
        return _run(self._async_get_video_info(video_id))

    def get_comments(
        self, video_id: str, max_pages: int = 10, **kwargs
    ) -> List[Comment]:
        """
        获取视频评论——免登录（建议 ≤ 10 页，深度翻页建议传入 Cookie）。

        Args:
            video_id: BV 号
            max_pages: 最大翻页数（默认 10）

        Returns:
            Comment 列表
        """
        return _run(self._async_get_comments(video_id, max_pages))

    def get_hot_videos(self, category: str = "game") -> List[VideoSnapshot]:
        """
        获取热门视频——免登录。

        Args:
            category: 分类（默认 game）

        Returns:
            VideoSnapshot 列表
        """
        return _run(self._async_get_hot_videos())

    # ─── 异步实现（免登录）────────────────────────────────────────────

    async def _async_search_videos(
        self, keyword: str, limit: int = 20, order: str = "totalrank"
    ) -> List[VideoSnapshot]:
        try:
            from bilibili_api import search
            
            # 映射排序枚举
            order_mapping = {
                "totalrank": search.OrderVideo.TOTALRANK,
                "click": search.OrderVideo.CLICK,
                "pubdate": search.OrderVideo.PUBDATE,
                "stow": search.OrderVideo.STOW,
            }
            bili_order = order_mapping.get(order, getattr(search.OrderVideo, 'TOTALRANK', getattr(search.OrderVideo, 'DEFAULT', None)))

            all_snapshots = []
            page = 1
            while len(all_snapshots) < limit:
                result = await search.search_by_type(
                    keyword=keyword,
                    search_type=search.SearchObjectType.VIDEO,
                    order_type=bili_order,
                    page=page,
                )
                items = result.get("result", [])
                if not items:
                    break
                    
                today = datetime.now().strftime("%Y-%m-%d")
                for item in items:
                    try:
                        snap = VideoSnapshot(
                            platform="bilibili",
                            video_id=item.get("bvid", ""),
                            title=item.get("title", "").replace("<em class=\"keyword\">", "").replace("</em>", ""),
                            author=item.get("author", ""),
                            author_id=str(item.get("mid", "")),
                            snapshot_date=today,
                            view_count=int(item.get("play", 0) or 0),
                            like_count=int(item.get("like", 0) or 0),
                            comment_count=int(item.get("review", 0) or 0),
                            share_count=0,
                            favorite_count=int(item.get("favorites", 0) or 0),
                            coin_count=-1,
                            danmaku_count=int(item.get("danmaku", 0) or 0),
                            publish_date=datetime.fromtimestamp(
                                int(item.get("pubdate", 0) or 0)
                            ).strftime("%Y-%m-%d")
                            if item.get("pubdate")
                            else "",
                            tags=item.get("tag", ""),
                            url=f"https://www.bilibili.com/video/{item.get('bvid', '')}",
                        )
                        all_snapshots.append(snap)
                        if len(all_snapshots) >= limit:
                            break
                    except Exception as e:
                        logger.warning(f"解析搜索结果失败: {e}, item={item}")
                        
                logger.info(f"B站搜索 '{keyword}' 第{page}页，已累计获取 {len(all_snapshots)} 条视频")
                if len(all_snapshots) >= limit or len(items) == 0:
                    break
                page += 1
                await asyncio.sleep(REQUEST_INTERVAL)
            return all_snapshots
        except Exception as e:
            logger.error(f"B站搜索失败: {e}")
            return []

    async def _async_get_video_info(self, bvid: str) -> Optional[VideoSnapshot]:
        try:
            from bilibili_api import video

            v = video.Video(bvid=bvid, credential=self.credential)
            info = await v.get_info()
            stat = info.get("stat", {})
            today = datetime.now().strftime("%Y-%m-%d")

            tags_list = []
            try:
                tags_raw = await v.get_tags()
                tags_list = [t.get("tag_name", "") for t in tags_raw]
            except Exception:
                pass

            snap = VideoSnapshot(
                platform="bilibili",
                video_id=bvid,
                title=info.get("title", ""),
                author=info.get("owner", {}).get("name", ""),
                author_id=str(info.get("owner", {}).get("mid", "")),
                snapshot_date=today,
                view_count=int(stat.get("view", 0) or 0),
                like_count=int(stat.get("like", 0) or 0),
                comment_count=int(stat.get("reply", 0) or 0),
                share_count=int(stat.get("share", 0) or 0),
                favorite_count=int(stat.get("favorite", 0) or 0),
                coin_count=int(stat.get("coin", 0) or 0),
                danmaku_count=int(stat.get("danmaku", 0) or 0),
                publish_date=datetime.fromtimestamp(
                    info.get("pubdate", 0)
                ).strftime("%Y-%m-%d"),
                tags=",".join(tags_list),
                url=f"https://www.bilibili.com/video/{bvid}",
            )
            logger.info(f"获取视频详情成功: {bvid} — {snap.title}")
            await asyncio.sleep(REQUEST_INTERVAL)
            return snap
        except Exception as e:
            logger.error(f"获取视频 {bvid} 详情失败: {e}")
            return None

    async def _async_get_comments(
        self, bvid: str, max_pages: int
    ) -> List[Comment]:
        try:
            from bilibili_api import comment as comment_api, video

            v = video.Video(bvid=bvid, credential=self.credential)
            info = await v.get_info()
            aid = info.get("aid", 0)

            all_comments: List[Comment] = []
            for page in range(1, max_pages + 1):
                try:
                    result = await comment_api.get_comments(
                        oid=aid,
                        type_=comment_api.CommentResourceType.VIDEO,
                        page_index=page,
                        credential=self.credential,
                    )
                    replies = result.get("replies", []) or []
                    if not replies:
                        logger.info(f"第 {page} 页无评论，停止翻页")
                        break

                    for item in replies:
                        member = item.get("member", {})
                        content = item.get("content", {})
                        c = Comment(
                            platform="bilibili",
                            video_id=bvid,
                            comment_id=str(item.get("rpid", "")),
                            author=member.get("uname", ""),
                            author_id=str(member.get("mid", "")),
                            content=content.get("message", ""),
                            like_count=int(item.get("like", 0) or 0),
                            reply_count=int(item.get("rcount", 0) or 0),
                            publish_time=datetime.fromtimestamp(
                                item.get("ctime", 0)
                            ).strftime("%Y-%m-%d %H:%M:%S"),
                            ip_location=member.get("location", ""),
                            sentiment="",
                            mentioned_games="",
                        )
                        all_comments.append(c)

                    logger.info(
                        f"B站评论 {bvid} 第{page}页，累计 {len(all_comments)} 条"
                    )
                    await asyncio.sleep(REQUEST_INTERVAL)
                except Exception as e:
                    logger.warning(f"获取评论第{page}页失败: {e}")
                    break

            return all_comments
        except Exception as e:
            logger.error(f"获取视频 {bvid} 评论失败: {e}")
            return []

    async def _async_get_hot_videos(self) -> List[VideoSnapshot]:
        try:
            from bilibili_api import hot

            # 获取热门视频
            result = await hot.get_hot_videos()
            today = datetime.now().strftime("%Y-%m-%d")
            snapshots = []
            for item in result.get("list", []):
                try:
                    stat = item.get("stat", {})
                    snap = VideoSnapshot(
                        platform="bilibili",
                        video_id=item.get("bvid", ""),
                        title=item.get("title", ""),
                        author=item.get("owner", {}).get("name", ""),
                        author_id=str(item.get("owner", {}).get("mid", "")),
                        snapshot_date=today,
                        view_count=int(stat.get("view", 0) or 0),
                        like_count=int(stat.get("like", 0) or 0),
                        comment_count=int(stat.get("reply", 0) or 0),
                        share_count=int(stat.get("share", 0) or 0),
                        favorite_count=int(stat.get("favorite", 0) or 0),
                        coin_count=int(stat.get("coin", 0) or 0),
                        danmaku_count=int(stat.get("danmaku", 0) or 0),
                        publish_date=datetime.fromtimestamp(
                            item.get("pubdate", 0)
                        ).strftime("%Y-%m-%d"),
                        tags="",
                        url=f"https://www.bilibili.com/video/{item.get('bvid', '')}",
                    )
                    snapshots.append(snap)
                except Exception as e:
                    logger.warning(f"解析热门视频失败: {e}")
            logger.info(f"获取热门视频 {len(snapshots)} 条")
            return snapshots
        except Exception as e:
            logger.error(f"获取热门视频失败: {e}")
            return []

    # ─── 需 Cookie 能力（仅本地）─────────────────────────────────────

    async def get_user_favorites(self, uid: int) -> list:
        """
        获取用户公开收藏夹——需要登录态（仅本地运行）。

        Args:
            uid: B站用户 UID

        Returns:
            收藏夹列表
        """
        if not self.credential:
            raise RuntimeError("get_user_favorites 需要 Credential，请在本地模式下使用")
        try:
            from bilibili_api import favorite_list

            result = await favorite_list.get_video_favorite_list(
                uid=uid, credential=self.credential
            )
            await asyncio.sleep(REQUEST_INTERVAL)
            return result.get("list", [])
        except Exception as e:
            logger.error(f"获取用户 {uid} 收藏夹失败: {e}")
            return []

    async def get_user_followings(self, uid: int) -> list:
        """
        获取用户关注列表——需要登录态（仅本地运行）。

        Args:
            uid: B站用户 UID

        Returns:
            关注列表
        """
        if not self.credential:
            raise RuntimeError("get_user_followings 需要 Credential，请在本地模式下使用")
        try:
            from bilibili_api import user

            u = user.User(uid=uid, credential=self.credential)
            result = await u.get_followings()
            await asyncio.sleep(REQUEST_INTERVAL)
            return result.get("list", [])
        except Exception as e:
            logger.error(f"获取用户 {uid} 关注列表失败: {e}")
            return []
