"""
Logging Middleware
"""
import time
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from loguru import logger


class LoggingMiddleware(BaseHTTPMiddleware):
    """日志中间件"""

    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = getattr(request.state, "request_id", "-")
        logger.info(f"Request: {request.method} {request.url.path} | ID: {request_id}")

        start_time = time.time()
        try:
            response = await call_next(request)
        except Exception as e:
            logger.error(f"Request failed: {str(e)}")
            raise

        process_time = (time.time() - start_time) * 1000
        logger.info(f"Response: {response.status_code} | Duration: {process_time:.2f}ms")

        response.headers["X-Process-Time"] = str(process_time)
        return response
