"""
SLG Sentinel 适配器抽象基类

所有平台 Adapter 继承自 BaseAdapter，实现统一的数据采集接口。
"""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.core.models import Comment, VideoSnapshot


class BaseAdapter(ABC):
    """平台适配器抽象基类"""

    @abstractmethod
    def search_videos(self, keyword: str, **kwargs) -> list:
        """搜索视频，返回 VideoSnapshot 列表"""
        ...

    @abstractmethod
    def get_video_info(self, video_id: str) -> "VideoSnapshot":
        """获取单个视频元数据"""
        ...

    @abstractmethod
    def get_comments(self, video_id: str, **kwargs) -> list:
        """获取评论，返回 Comment 列表"""
        ...
