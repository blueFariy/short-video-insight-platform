"""
Custom Exceptions
"""


class AppException(Exception):
    """Base application exception"""
    def __init__(self, message: str, code: int = 500):
        self.message = message
        self.code = code
        super().__init__(message)


class ValidationException(AppException):
    """Validation error"""
    def __init__(self, message: str = "Validation error"):
        super().__init__(message, code=400)


class UnauthorizedException(AppException):
    """Unauthorized access"""
    def __init__(self, message: str = "Unauthorized"):
        super().__init__(message, code=401)


class NotFoundException(AppException):
    """Resource not found"""
    def __init__(self, message: str = "Resource not found"):
        super().__init__(message, code=404)


class AIException(AppException):
    """AI service error"""
    def __init__(self, message: str = "AI service error"):
        super().__init__(message, code=500)
