"""
Unified Response Format
"""
from typing import Any, Optional
from pydantic import BaseModel, Field


class ResponseModel(BaseModel):
    """统一响应格式"""
    code: int = Field(default=200)
    message: str = Field(default="success")
    data: Optional[Any] = Field(default=None)

    class Config:
        from_attributes = True


def success_response(data: Any = None, message: str = "success") -> ResponseModel:
    """成功响应"""
    return ResponseModel(code=200, message=message, data=data)
