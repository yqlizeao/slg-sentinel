"""
网络请求重试工具

为所有适配器提供统一的轻量级重试机制，无需引入 tenacity 等外部依赖。
"""

import time
import logging
from functools import wraps

logger = logging.getLogger(__name__)


def retry_on_failure(max_retries: int = 3, base_delay: float = 1.0, backoff_factor: float = 2.0, 
                     retryable_exceptions: tuple = (Exception,)):
    """
    装饰器：对函数执行自动重试，支持指数退避。
    
    Args:
        max_retries: 最大重试次数（不含首次执行）
        base_delay: 首次重试等待秒数
        backoff_factor: 退避倍数（每次等待时间 = base_delay * backoff_factor^重试次数）
        retryable_exceptions: 可重试的异常类型元组
    
    Example:
        @retry_on_failure(max_retries=3, base_delay=1.0)
        def fetch_data(url):
            resp = requests.get(url, timeout=10)
            resp.raise_for_status()
            return resp.json()
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except retryable_exceptions as e:
                    last_exception = e
                    if attempt < max_retries:
                        delay = base_delay * (backoff_factor ** attempt)
                        logger.warning(
                            f"[重试 {attempt+1}/{max_retries}] {func.__name__} 失败: {e}，"
                            f"{delay:.1f}s 后重试..."
                        )
                        time.sleep(delay)
                    else:
                        logger.error(
                            f"[放弃] {func.__name__} 在 {max_retries} 次重试后仍然失败: {e}"
                        )
            raise last_exception
        return wrapper
    return decorator
