"""
Exception Handlers
"""
import traceback
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from loguru import logger
from pydantic import ValidationError

from app.core.exceptions import (
    AppException,
    ValidationException,
    UnauthorizedException,
    ForbiddenException,
    NotFoundException,
    ConflictException,
    RateLimitException,
    InternalServerException,
    ExternalServiceException
)
from app.core.response import ResponseModel


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    """应用异常处理器"""
    logger.warning(f"App exception: {exc.message}, details: {exc.details}")
    return JSONResponse(
        status_code=exc.code,
        content=ResponseModel(
            code=exc.code,
            message=exc.message,
            data=exc.details
        ).model_dump()
    )


async def validation_exception_handler(request: Request, exc: ValidationError) -> JSONResponse:
    """Pydantic验证异常处理器"""
    errors = []
    for error in exc.errors():
        errors.append({
            "field": ".".join(str(loc) for loc in error["loc"]),
            "message": error["msg"],
            "type": error["type"]
        })
    logger.warning(f"Validation error: {errors}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=ResponseModel(
            code=422,
            message="Validation failed",
            data=errors
        ).model_dump()
    )


async def unauthorized_exception_handler(request: Request, exc: UnauthorizedException) -> JSONResponse:
    """未授权异常处理器"""
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content=ResponseModel(
            code=401,
            message=exc.message,
            data=exc.details
        ).model_dump(),
        headers={"WWW-Authenticate": "Bearer"}
    )


async def forbidden_exception_handler(request: Request, exc: ForbiddenException) -> JSONResponse:
    """禁止访问异常处理器"""
    return JSONResponse(
        status_code=status.HTTP_403_FORBIDDEN,
        content=ResponseModel(
            code=403,
            message=exc.message,
            data=exc.details
        ).model_dump()
    )


async def not_found_exception_handler(request: Request, exc: NotFoundException) -> JSONResponse:
    """资源不存在异常处理器"""
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content=ResponseModel(
            code=404,
            message=exc.message,
            data=exc.details
        ).model_dump()
    )


async def conflict_exception_handler(request: Request, exc: ConflictException) -> JSONResponse:
    """资源冲突异常处理器"""
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content=ResponseModel(
            code=409,
            message=exc.message,
            data=exc.details
        ).model_dump()
    )


async def rate_limit_exception_handler(request: Request, exc: RateLimitException) -> JSONResponse:
    """请求频率超限异常处理器"""
    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content=ResponseModel(
            code=429,
            message=exc.message,
            data=exc.details
        ).model_dump()
    )


async def internal_server_exception_handler(request: Request, exc: InternalServerException) -> JSONResponse:
    """服务器内部异常处理器"""
    logger.error(f"Internal server error: {exc.message}, trace: {traceback.format_exc()}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ResponseModel(
            code=500,
            message="Internal server error",
            data=None
        ).model_dump()
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """通用异常处理器"""
    logger.error(f"Unhandled exception: {type(exc).__name__}, trace: {traceback.format_exc()}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ResponseModel(
            code=500,
            message="Internal server error",
            data={"type": type(exc).__name__}
        ).model_dump()
    )


def register_exception_handlers(app: FastAPI) -> None:
    """注册异常处理器"""
    app.add_exception_handler(AppException, app_exception_handler)
    app.add_exception_handler(ValidationException, validation_exception_handler)
    app.add_exception_handler(UnauthorizedException, unauthorized_exception_handler)
    app.add_exception_handler(ForbiddenException, forbidden_exception_handler)
    app.add_exception_handler(NotFoundException, not_found_exception_handler)
    app.add_exception_handler(ConflictException, conflict_exception_handler)
    app.add_exception_handler(RateLimitException, rate_limit_exception_handler)
    app.add_exception_handler(InternalServerException, internal_server_exception_handler)
    app.add_exception_handler(Exception, generic_exception_handler)
