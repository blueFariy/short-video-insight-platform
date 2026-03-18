"""
Logging Middleware
"""
import time
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from loguru import logger


class LoggingMiddleware(BaseHTTPMiddleware):
    """日志中间件 - 记录请求日志"""

    async def dispatch(self, request: Request, call_next) -> Response:
        # 记录请求开始
        request_id = getattr(request.state, "request_id", "-")
        logger.info(
            f"Request started | {request.method} {request.url.path} | "
            f"Client: {request.client.host if request.client else '-'} | "
            f"Request-ID: {request_id}"
        )

        # 记录请求体大小（如果有）
        content_length = request.headers.get("content-length")
        if content_length:
            logger.debug(f"Content-Length: {content_length}")

        # 记录请求处理时间
        start_time = time.time()

        # 处理请求
        try:
            response = await call_next(request)
        except Exception as e:
            logger.error(f"Request failed: {str(e)}")
            raise

        # 计算处理时间
        process_time = (time.time() - start_time) * 1000

        # 记录响应日志
        logger.info(
            f"Request completed | {request.method} {request.url.path} | "
            f"Status: {response.status_code} | "
            f"Duration: {process_time:.2f}ms | "
            f"Request-ID: {request_id}"
        )

        # 添加响应头
        response.headers["X-Process-Time"] = str(process_time)

        return response
