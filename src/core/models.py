"""
SLG Sentinel 数据模型定义

所有数据模型使用 Python dataclass 定义，字段与 CSV 列一一对应。
"""

from dataclasses import dataclass, fields


@dataclass
class VideoSnapshot:
    """视频指标快照——每日采集一次，用于计算周增量"""

    platform: str           # bilibili / youtube / douyin / kuaishou / xiaohongshu
    video_id: str           # BV号 / YouTube video ID / 其他平台ID
    title: str
    author: str
    author_id: str
    snapshot_date: str      # YYYY-MM-DD
    view_count: int
    like_count: int
    comment_count: int
    share_count: int        # B站=分享, YouTube=N/A
    favorite_count: int     # B站=收藏, YouTube=N/A
    coin_count: int         # B站=投币, 其他平台=0
    danmaku_count: int      # B站=弹幕, 其他平台=0
    publish_date: str       # 视频发布日期
    tags: str               # 逗号分隔的标签
    url: str                # 原始链接


@dataclass
class Comment:
    """评论数据"""

    platform: str
    video_id: str
    comment_id: str
    author: str
    author_id: str
    content: str
    like_count: int
    reply_count: int
    publish_time: str
    ip_location: str        # B站有IP属地
    sentiment: str          # positive / negative / neutral（分析后填充）
    mentioned_games: str    # 评论中提到的游戏名（分析后填充）


@dataclass
class TapTapReview:
    """TapTap游戏评论"""

    game_id: str
    game_name: str
    review_id: str
    author: str
    author_id: str
    score: int              # 1-5星评分
    content: str
    device: str             # 设备型号
    spent: str              # 游玩时长
    ups: int                # 支持数
    downs: int              # 反对数
    publish_time: str
    sentiment: str
    mentioned_games: str


@dataclass
class UserProfile:
    """推断式用户画像"""

    platform: str
    user_id: str
    username: str
    source_video_id: str    # 从哪个视频的评论中发现的
    public_favorites: str   # B站公开收藏夹中的SLG相关内容
    followed_channels: str  # 关注的SLG相关UP主/频道
    taptap_games: str       # TapTap玩过的游戏列表
    comment_mentions: str   # 评论中提到的竞品
    inferred_tags: str      # 推断标签，如"率土+三战双游玩家"
