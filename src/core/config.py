"""
SLG Sentinel 全局配置模块

加载 keywords.yaml 和 targets.yaml 配置文件。
所有 Cookie / API Key 只通过环境变量注入，绝不在代码中硬编码任何凭证。
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import yaml

logger = logging.getLogger(__name__)

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent.parent

# 默认配置文件路径
DEFAULT_KEYWORDS_FILE = PROJECT_ROOT / "keywords.yaml"
DEFAULT_TARGETS_FILE = PROJECT_ROOT / "targets.yaml"

# 日志格式（规格书要求）
LOG_FORMAT = "[%(asctime)s] %(levelname)s %(name)s: %(message)s"


@dataclass
class ExpansionConfig:
    """关键词扩展配置"""

    enabled: bool = True
    llm_provider: str = "deepseek"
    max_expanded_keywords: int = 50


@dataclass
class KeywordsConfig:
    """关键词配置"""

    games: list[str] = field(default_factory=list)
    categories: list[str] = field(default_factory=list)
    expansion: ExpansionConfig = field(default_factory=ExpansionConfig)

    def all_keywords(self) -> list[str]:
        """返回所有种子关键词（游戏 + 分类）"""
        return self.games + self.categories


@dataclass
class BilibiliChannel:
    """B站频道/UP主"""

    name: str
    uid: str


@dataclass
class YouTubeChannel:
    """YouTube 频道"""

    name: str
    channel_id: str


@dataclass
class TapTapGame:
    """TapTap 游戏"""

    name: str
    app_id: str


@dataclass
class TargetsConfig:
    """跟踪目标配置"""

    bilibili_channels: list[BilibiliChannel] = field(default_factory=list)
    youtube_channels: list[YouTubeChannel] = field(default_factory=list)
    taptap_games: list[TapTapGame] = field(default_factory=list)


@dataclass
class SentinelConfig:
    """全局配置"""

    keywords: KeywordsConfig = field(default_factory=KeywordsConfig)
    targets: TargetsConfig = field(default_factory=TargetsConfig)

    # 环境变量注入的敏感配置
    deepseek_api_key: str = ""
    bili_sessdata: str = ""


def setup_logging(level: int = logging.INFO) -> None:
    """配置日志格式"""
    logging.basicConfig(level=level, format=LOG_FORMAT)


def load_keywords(filepath: str | Path | None = None) -> KeywordsConfig:
    """
    加载关键词配置文件。

    Args:
        filepath: keywords.yaml 路径，默认为项目根目录下的 keywords.yaml

    Returns:
        KeywordsConfig 实例
    """
    filepath = Path(filepath) if filepath else DEFAULT_KEYWORDS_FILE

    if not filepath.exists():
        logger.warning(f"关键词配置文件不存在: {filepath}，使用默认配置")
        return KeywordsConfig()

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
    except Exception as e:
        logger.error(f"加载关键词配置失败: {e}")
        return KeywordsConfig()

    seed = data.get("seed_keywords", {})
    expansion_data = data.get("expansion", {})

    expansion = ExpansionConfig(
        enabled=expansion_data.get("enabled", True),
        llm_provider=expansion_data.get("llm_provider", "deepseek"),
        max_expanded_keywords=expansion_data.get("max_expanded_keywords", 50),
    )

    return KeywordsConfig(
        games=seed.get("games", []),
        categories=seed.get("categories", []),
        expansion=expansion,
    )


def load_targets(filepath: str | Path | None = None) -> TargetsConfig:
    """
    加载跟踪目标配置文件。

    Args:
        filepath: targets.yaml 路径，默认为项目根目录下的 targets.yaml

    Returns:
        TargetsConfig 实例
    """
    filepath = Path(filepath) if filepath else DEFAULT_TARGETS_FILE

    if not filepath.exists():
        logger.warning(f"目标配置文件不存在: {filepath}，使用默认配置")
        return TargetsConfig()

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
    except Exception as e:
        logger.error(f"加载目标配置失败: {e}")
        return TargetsConfig()

    targets_data = data.get("targets", data)

    bilibili_channels = [
        BilibiliChannel(name=ch.get("name", ""), uid=ch.get("uid", ""))
        for ch in targets_data.get("bilibili_channels", [])
    ]

    youtube_channels = [
        YouTubeChannel(name=ch.get("name", ""), channel_id=ch.get("channel_id", ""))
        for ch in targets_data.get("youtube_channels", [])
    ]

    taptap_games = [
        TapTapGame(name=g.get("name", ""), app_id=g.get("app_id", ""))
        for g in targets_data.get("taptap_games", [])
    ]

    return TargetsConfig(
        bilibili_channels=bilibili_channels,
        youtube_channels=youtube_channels,
        taptap_games=taptap_games,
    )


def load_config(
    keywords_file: str | Path | None = None,
    targets_file: str | Path | None = None,
) -> SentinelConfig:
    """
    加载完整配置（关键词 + 目标 + 环境变量）。

    Args:
        keywords_file: keywords.yaml 路径
        targets_file: targets.yaml 路径

    Returns:
        SentinelConfig 实例
    """
    return SentinelConfig(
        keywords=load_keywords(keywords_file),
        targets=load_targets(targets_file),
        deepseek_api_key=os.environ.get("DEEPSEEK_API_KEY", ""),
        bili_sessdata=os.environ.get("BILI_SESSDATA", ""),
    )
