"""
Exception Handlers
"""
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from loguru import logger

from app.core.exceptions import AppException
from app.core.response import error_response


async def app_exception_handler(request: Request, exc: AppException):
    """Handle application exceptions"""
    logger.error(f"App exception: {exc.message}")
    return JSONResponse(
        status_code=exc.code,
        content=error_response(code=exc.code, message=exc.message).model_dump()
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation exceptions"""
    errors = exc.errors()
    error_msg = "; ".join([f"{e['loc'][-1]}: {e['msg']}" for e in errors])
    logger.error(f"Validation error: {error_msg}")
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=error_response(code=400, message=error_msg).model_dump()
    )


async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions"""
    logger.error(f"Unexpected error: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_response(code=500, message="Internal server error").model_dump()
    )
