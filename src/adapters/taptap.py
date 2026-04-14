"""
SLG Sentinel — TapTap 适配器

完全自建，免登录。通过 requests 直接调用 TapTap 移动端 API。

API 来源：TapTap 移动端 okhttp 请求（逆向分析）
礼貌爬取：每次请求间隔 ≥ 1 秒（规格书铁律）
"""

from __future__ import annotations

import logging
import time
from datetime import datetime
from typing import List, Optional

import requests

from src.adapters.base import BaseAdapter
from src.core.models import Comment, TapTapReview, VideoSnapshot

logger = logging.getLogger(__name__)

# 请求间隔
REQUEST_INTERVAL = 1.0

# TapTap WebAPI v2 基础配置（当前有效端点，2026-04）
WEB_BASE = "https://www.taptap.cn/webapiv2"
REVIEW_API = f"{WEB_BASE}/review/v2/list-by-app"
GAME_API = f"{WEB_BASE}/app/v3/detail"
SEARCH_API = f"{WEB_BASE}/search/v4/search"

HEADERS = {
    "User-Agent": "TapTap/2.21.3 (Android 11)",
    "Accept": "application/json",
    "Accept-Language": "zh-CN",
    "X-UA": "V=1&PN=TapTap&VN_CODE=2213300&LOC=CN&LANG=zh_CN&CH=default",
}
X_UA = "V=1&PN=TapTap&VN_CODE=2213300&LOC=CN&LANG=zh_CN&CH=default"

# 请求超时（秒）
TIMEOUT = 15


class TapTapAdapter(BaseAdapter):
    """
    TapTap 适配器（完全自建，免登录）

    主要功能：
      - get_reviews: 获取游戏评论列表
      - get_game_info: 获取游戏基础信息
      - search_games: 搜索游戏
      - get_user_games: 获取用户玩过的游戏列表（公开数据）

    BaseAdapter 接口：
      - search_videos → 复用 search_games（TapTap 无视频概念）
      - get_video_info → 复用 get_game_info
      - get_comments → 复用 get_reviews
    """

    def __init__(self, session: Optional[requests.Session] = None):
        """
        Args:
            session: 可复用的 requests.Session（可选，默认新建）
        """
        self.session = session or requests.Session()
        self.session.headers.update(HEADERS)

    # ─── BaseAdapter 抽象方法实现 ──────────────────────────────────

    def search_videos(self, keyword: str, **kwargs) -> List[VideoSnapshot]:
        """
        搜索游戏（复用 search_games，将结果映射为 VideoSnapshot 格式）。
        TapTap 无视频概念，此方法返回游戏数据作为近似替代。
        """
        games = self.search_games(keyword)
        # 将游戏映射为 VideoSnapshot（video_id = app_id）
        today = datetime.now().strftime("%Y-%m-%d")
        snapshots = []
        for g in games:
            snap = VideoSnapshot(
                platform="taptap",
                video_id=str(g.get("id", "")),
                title=g.get("title", {}).get("zh_CN", "") or g.get("title", {}).get("en_US", ""),
                author=g.get("developer", {}).get("name", ""),
                author_id=str(g.get("developer", {}).get("id", "")),
                snapshot_date=today,
                view_count=int(g.get("stat", {}).get("downloads", 0) or 0),
                like_count=int(g.get("stat", {}).get("fans_count", 0) or 0),
                comment_count=int(g.get("stat", {}).get("reviews_count", 0) or 0),
                share_count=0,
                favorite_count=int(g.get("stat", {}).get("wish_list_count", 0) or 0),
                coin_count=0,
                danmaku_count=0,
                publish_date="",
                tags=",".join(g.get("tags", {}).get("list", []) or []),
                url=f"https://www.taptap.cn/app/{g.get('id', '')}",
            )
            snapshots.append(snap)
        return snapshots

    def get_video_info(self, video_id: str) -> Optional[VideoSnapshot]:
        """获取游戏信息（video_id = app_id）"""
        info = self.get_game_info(video_id)
        if not info:
            return None
        today = datetime.now().strftime("%Y-%m-%d")
        return VideoSnapshot(
            platform="taptap",
            video_id=video_id,
            title=info.get("title", {}).get("zh_CN", ""),
            author=info.get("developer", {}).get("name", ""),
            author_id=str(info.get("developer", {}).get("id", "")),
            snapshot_date=today,
            view_count=int(info.get("stat", {}).get("downloads", 0) or 0),
            like_count=int(info.get("stat", {}).get("fans_count", 0) or 0),
            comment_count=int(info.get("stat", {}).get("reviews_count", 0) or 0),
            share_count=0,
            favorite_count=int(info.get("stat", {}).get("wish_list_count", 0) or 0),
            coin_count=0,
            danmaku_count=0,
            publish_date="",
            tags=",".join(info.get("tags", {}).get("list", []) or []),
            url=f"https://www.taptap.cn/app/{video_id}",
        )

    def get_comments(self, video_id: str, **kwargs) -> List[Comment]:
        """获取游戏评论（video_id = app_id，映射到 Comment 模型）"""
        max_pages = kwargs.get("max_pages", 10)
        reviews = self.get_reviews(video_id, max_pages=max_pages)
        comments = []
        for r in reviews:
            c = Comment(
                platform="taptap",
                video_id=r.game_id,
                comment_id=r.review_id,
                author=r.author,
                author_id=r.author_id,
                content=r.content,
                like_count=r.ups,
                reply_count=0,
                publish_time=r.publish_time,
                ip_location="",
                sentiment=r.sentiment,
                mentioned_games=r.mentioned_games,
            )
            comments.append(c)
        return comments

    # ─── TapTap 专有方法 ──────────────────────────────────────────

    def get_reviews(
        self,
        app_id: str,
        game_name: str = "",
        sort: str = "new",
        max_pages: int = 50,
    ) -> List[TapTapReview]:
        """
        获取游戏评论——免登录。

        Args:
            app_id: TapTap 游戏 ID
            game_name: 游戏名称（可选，用于填充 game_name 字段）
            sort: 排序方式（'new' / 'hot'）
            max_pages: 最大页数（每页 10 条，默认 50 页 = 500 条）

        Returns:
            TapTapReview 列表
        """
        reviews = []
        # webapiv2 使用 cursor-based 分页
        cursor = ""
        for page in range(max_pages):
            try:
                params: dict = {
                    "app_id": app_id,
                    "sort": sort,   # 'new' 或 'hot'
                    "limit": 10,
                }
                if cursor:
                    params["cursor"] = cursor

                resp = self.session.get(
                    REVIEW_API, params=params, timeout=TIMEOUT
                )
                resp.raise_for_status()
                data = resp.json()

                items = data.get("data", {}).get("list", [])
                if not items:
                    logger.info(f"TapTap 评论第 {page+1} 页为空，停止翻页")
                    break

                # 更新 cursor（webapiv2 支持 next_cursor）
                next_cursor = data.get("data", {}).get("next_cursor", "")

                for item in items:
                    try:
                        # webapiv2 结构: item.moment.review
                        moment = item.get("moment", item)
                        review_data = moment.get("review", moment)
                        user_data = moment.get("user", {})

                        content_obj = review_data.get("contents", {})
                        content_text = (
                            content_obj.get("text", "")
                            if isinstance(content_obj, dict)
                            else str(content_obj)
                        )
                        review = TapTapReview(
                            game_id=app_id,
                            game_name=game_name,
                            review_id=str(moment.get("id", review_data.get("id", ""))),
                            author=user_data.get("name", ""),
                            author_id=str(user_data.get("id", "")),
                            score=int(review_data.get("score", 0) or 0),
                            content=content_text,
                            device=review_data.get("device", "") or "",
                            spent=review_data.get("stage_label", "") or "",  # 玩过/在玩等
                            ups=int(moment.get("count_of_like", 0) or 0),
                            downs=0,
                            publish_time=str(moment.get("created_time", "")),
                            sentiment="",
                            mentioned_games="",
                        )
                        reviews.append(review)
                    except Exception as e:
                        logger.warning(f"解析 TapTap 评论失败: {e}")

                if not next_cursor:
                    break
                cursor = next_cursor

                logger.info(
                    f"TapTap 评论 app_id={app_id} 第{page+1}页，累计 {len(reviews)} 条"
                )
                time.sleep(REQUEST_INTERVAL)

            except requests.exceptions.RequestException as e:
                logger.error(f"TapTap 评论请求失败 页{page}: {e}")
                break
            except Exception as e:
                logger.error(f"TapTap 评论解析失败 页{page}: {e}")
                break

        return reviews

    def get_game_info(self, app_id: str) -> Optional[dict]:
        """
        获取游戏详情（下载量、关注数、评论数等）。

        Args:
            app_id: TapTap 游戏 ID

        Returns:
            游戏信息字典，失败返回 None
        """
        try:
            params = {"id": app_id}  # webapiv2 v3 使用 id 参数
            resp = self.session.get(GAME_API, params=params, timeout=TIMEOUT)
            resp.raise_for_status()
            data = resp.json()
            info = data.get("data", {}).get("app", {})
            logger.info(f"获取 TapTap 游戏信息成功: app_id={app_id}")
            time.sleep(REQUEST_INTERVAL)
            return info
        except Exception as e:
            logger.error(f"获取 TapTap 游戏 {app_id} 信息失败: {e}")
            return None

    def search_games(self, keyword: str, limit: int = 10) -> List[dict]:
        """
        搜索游戏。

        Args:
            keyword: 搜索关键词
            limit: 最大结果数

        Returns:
            游戏信息字典列表
        """
        try:
            params = {
                "q": keyword,
                "from": 0,
                "limit": limit,
                "X-UA": X_UA,
            }
            resp = self.session.get(SEARCH_API, params=params, timeout=TIMEOUT)
            resp.raise_for_status()
            data = resp.json()
            items = data.get("data", {}).get("list", [])
            # 过滤出游戏类型
            games = [
                item.get("app", item)
                for item in items
                if item.get("type") in ("app", None)
            ]
            logger.info(f"TapTap 搜索 '{keyword}' 获取 {len(games)} 个游戏")
            time.sleep(REQUEST_INTERVAL)
            return games
        except Exception as e:
            logger.error(f"TapTap 搜索失败 '{keyword}': {e}")
            return []

    def get_user_games(self, user_id: str) -> List[str]:
        """
        获取用户玩过的游戏列表——免登录，公开数据。

        Args:
            user_id: TapTap 用户 ID

        Returns:
            游戏名称列表
        """
        try:
            url = f"{BASE_URL}/user/v1/played-games"
            params = {"user_id": user_id, "X-UA": X_UA}
            resp = self.session.get(url, params=params, timeout=TIMEOUT)
            resp.raise_for_status()
            data = resp.json()
            games = data.get("data", {}).get("list", [])
            game_names = [g.get("title", {}).get("zh_CN", "") for g in games if g]
            logger.info(f"用户 {user_id} 玩过 {len(game_names)} 款游戏")
            time.sleep(REQUEST_INTERVAL)
            return game_names
        except Exception as e:
            logger.error(f"获取用户 {user_id} 游戏列表失败: {e}")
            return []
