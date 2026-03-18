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
    def __init__(self, message: str = "Validation failed", details: Any = None):
        super().__init__(message=message, code=422, details=details)


class NotFoundException(AppException):
    """资源不存在异常"""
    def __init__(self, message: str = "Resource not found", details: Any = None):
        super().__init__(message=message, code=404, details=details)
