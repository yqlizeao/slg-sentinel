"""
SLG Sentinel — 自定义异常体系

统一的异常层级，用于替代 `except Exception: continue` 静默吞错模式。
所有异常均继承自 SentinelError，便于上层统一捕获。
"""

from __future__ import annotations


class SentinelError(Exception):
    """SLG Sentinel 基础异常"""


class PlatformRateLimitError(SentinelError):
    """平台触发风控限流"""


class PlatformAuthError(SentinelError):
    """平台鉴权失败（Cookie 过期、SESSDATA 无效等）"""


class NetworkError(SentinelError):
    """网络请求超时或连接失败"""


class ConfigError(SentinelError):
    """配置文件格式错误或缺失必要字段"""


class LLMError(SentinelError):
    """LLM API 调用失败（超时、额度耗尽、返回格式异常）"""


class DataCorruptionError(SentinelError):
    """CSV 数据损坏或表头格式不匹配"""
