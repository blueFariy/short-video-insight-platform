"""
Unified Response Format
"""
from typing import Generic, TypeVar, Optional
from pydantic import BaseModel, Field


T = TypeVar('T')


class ResponseModel(BaseModel, Generic[T]):
    """Unified response format"""
    code: int = Field(default=200)
    message: str = Field(default="success")
    data: Optional[T] = None


def success_response(data=None, message: str = "success"):
    """Success response"""
    return ResponseModel(code=200, message=message, data=data)


def error_response(code: int = 500, message: str = "error", data=None):
    """Error response"""
    return ResponseModel(code=code, message=message, data=data)
