"""
Exception Handlers
"""
import traceback
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from loguru import logger
from pydantic import ValidationError

from app.core.exceptions import AppException
from app.core.response import ResponseModel


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    """应用异常处理器"""
    logger.warning(f"App exception: {exc.message}")
    return JSONResponse(
        status_code=exc.code,
        content=ResponseModel(code=exc.code, message=exc.message).model_dump()
    )


async def validation_exception_handler(request: Request, exc: ValidationError) -> JSONResponse:
    """验证异常处理器"""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=ResponseModel(code=422, message="Validation failed").model_dump()
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """通用异常处理器"""
    logger.error(f"Unhandled exception: {type(exc).__name__}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ResponseModel(code=500, message="Internal server error").model_dump()
    )


def register_exception_handlers(app: FastAPI) -> None:
    """注册异常处理器"""
    app.add_exception_handler(AppException, app_exception_handler)
    app.add_exception_handler(ValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, generic_exception_handler)
