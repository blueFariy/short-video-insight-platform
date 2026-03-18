"""
Custom Exceptions
"""
from typing import Any, Optional


class AppException(Exception):
    """基础异常类"""

    def __init__(self, message: str = "Application error", code: int = 400, details: Optional[Any] = None):
        self.message = message
        self.code = code
        self.details = details
        super().__init__(self.message)


class ValidationException(AppException):
    """参数验证异常"""

    def __init__(self, message: str = "Validation failed", details: Optional[Any] = None):
        super().__init__(message=message, code=422, details=details)


class UnauthorizedException(AppException):
    """未授权异常"""

    def __init__(self, message: str = "Unauthorized", details: Optional[Any] = None):
        super().__init__(message=message, code=401, details=details)


class ForbiddenException(AppException):
    """禁止访问异常"""

    def __init__(self, message: str = "Forbidden", details: Optional[Any] = None):
        super().__init__(message=message, code=403, details=details)


class NotFoundException(AppException):
    """资源不存在异常"""

    def __init__(self, message: str = "Resource not found", details: Optional[Any] = None):
        super().__init__(message=message, code=404, details=details)


class ConflictException(AppException):
    """资源冲突异常"""

    def __init__(self, message: str = "Resource conflict", details: Optional[Any] = None):
        super().__init__(message=message, code=409, details=details)


class RateLimitException(AppException):
    """请求频率超限异常"""

    def __init__(self, message: str = "Rate limit exceeded", details: Optional[Any] = None):
        super().__init__(message=message, code=429, details=details)


class InternalServerException(AppException):
    """服务器内部异常"""

    def __init__(self, message: str = "Internal server error", details: Optional[Any] = None):
        super().__init__(message=message, code=500, details=details)


class ExternalServiceException(AppException):
    """外部服务异常"""

    def __init__(self, message: str = "External service error", details: Optional[Any] = None):
        super().__init__(message=message, code=502, details=details)
