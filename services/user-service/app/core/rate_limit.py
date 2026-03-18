"""
Rate Limiter Decorator
"""
import time
import functools
from typing import Callable, Optional
from loguru import logger

from app.core.exceptions import RateLimitException


class RateLimiter:
    """基于滑动窗口的简单限流器"""

    def __init__(self, max_calls: int, period: int):
        """
        初始化限流器

        Args:
            max_calls: 时间窗口内最大请求数
            period: 时间窗口大小（秒）
        """
        self.max_calls = max_calls
        self.period = period
        self.calls: dict[str, list[float]] = {}

    def _get_client_id(self, key: Optional[str] = None) -> str:
        """获取客户端标识"""
        return key or "default"

    def is_allowed(self, key: Optional[str] = None) -> bool:
        """检查请求是否允许"""
        client_id = self._get_client_id(key)
        current_time = time.time()

        # 初始化客户端调用记录
        if client_id not in self.calls:
            self.calls[client_id] = []

        # 清理过期记录
        self.calls[client_id] = [
            call_time for call_time in self.calls[client_id]
            if current_time - call_time < self.period
        ]

        # 检查是否超过限制
        if len(self.calls[client_id]) >= self.max_calls:
            return False

        # 记录本次调用
        self.calls[client_id].append(current_time)
        return True

    def get_remaining(self, key: Optional[str] = None) -> int:
        """获取剩余可用次数"""
        client_id = self._get_client_id(key)
        current_time = time.time()

        if client_id not in self.calls:
            return self.max_calls

        # 清理过期记录
        valid_calls = [
            call_time for call_time in self.calls[client_id]
            if current_time - call_time < self.period
        ]

        return max(0, self.max_calls - len(valid_calls))

    def get_reset_time(self, key: Optional[str] = None) -> float:
        """获取重置时间戳"""
        client_id = self._get_client_id(key)

        if client_id not in self.calls or not self.calls[client_id]:
            return current_time = time.time()

        current_time = time.time()
        valid_calls = [
            call_time for call_time in self.calls[client_id]
            if current_time - call_time < self.period
        ]

        if not valid_calls:
            return current_time

        return min(valid_calls) + self.period


def rate_limit(max_calls: int, period: int, key_func: Optional[Callable] = None):
    """
    限流装饰器

    Args:
        max_calls: 时间窗口内最大请求数
        period: 时间窗口大小（秒）
        key_func: 获取限流key的函数，默认为客户端IP

    Usage:
        @rate_limit(max_calls=100, period=60)
        async def my_endpoint(request: Request):
            ...

        # 或自定义key
        @rate_limit(max_calls=10, period=60, key_func=lambda request: request.state.user_id)
        async def protected_endpoint(request: Request):
            ...
    """
    limiter = RateLimiter(max_calls=max_calls, period=period)

    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # 获取限流key
            request = kwargs.get("request") or (args[0] if args else None)

            if key_func:
                key = key_func(request) if request else None
            else:
                # 默认使用客户端IP
                if request and hasattr(request, "client") and request.client:
                    key = request.client.host
                else:
                    key = "default"

            # 检查限流
            if not limiter.is_allowed(key):
                remaining = limiter.get_remaining(key)
                reset_time = limiter.get_reset_time(key)
                logger.warning(f"Rate limit exceeded for key: {key}")
                raise RateLimitException(
                    message="Rate limit exceeded",
                    details={
                        "max_calls": max_calls,
                        "period": period,
                        "remaining": remaining,
                        "reset_in": int(reset_time - time.time())
                    }
                )

            return await func(*args, **kwargs)

        return wrapper

    return decorator
