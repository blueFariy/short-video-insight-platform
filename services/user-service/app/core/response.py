"""
Unified Response Format
"""
from typing import Any, Generic, Optional, TypeVar
from pydantic import BaseModel, Field

T = TypeVar("T")


class ResponseModel(BaseModel, Generic[T]):
    """统一响应格式"""

    code: int = Field(default=200, description="响应状态码")
    message: str = Field(default="success", description="响应消息")
    data: Optional[T] = Field(default=None, description="响应数据")
    request_id: Optional[str] = Field(default=None, description="请求追踪ID")

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "code": 200,
                "message": "success",
                "data": {"id": 1, "username": "test"},
                "request_id": "abc123"
            }
        }


class PageResult(BaseModel, Generic[T]):
    """分页结果"""

    items: list[T] = Field(default_factory=list, description="数据列表")
    total: int = Field(default=0, description="总数量")
    page: int = Field(default=1, description="当前页码")
    page_size: int = Field(default=20, description="每页数量")
    total_pages: int = Field(default=0, description="总页数")

    class Config:
        from_attributes = True


def success_response(data: Any = None, message: str = "success") -> ResponseModel:
    """成功响应"""
    return ResponseModel(code=200, message=message, data=data)


def error_response(code: int = 400, message: str = "error", data: Any = None) -> ResponseModel:
    """错误响应"""
    return ResponseModel(code=code, message=message, data=data)


def page_response(items: list, total: int, page: int = 1, page_size: int = 20) -> PageResult:
    """分页响应"""
    total_pages = (total + page_size - 1) // page_size
    return PageResult(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )
