"""
Request ID Middleware
"""
import uuid
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class RequestIDMiddleware(BaseHTTPMiddleware):
    """请求ID中间件 - 为每个请求生成唯一ID"""

    async def dispatch(self, request: Request, call_next) -> Response:
        # 生成或获取请求ID
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())

        # 将request_id添加到请求状态
        request.state.request_id = request_id

        # 处理请求
        response = await call_next(request)

        # 在响应头中添加request_id
        response.headers["X-Request-ID"] = request_id

        return response
