"""
Core Package - Core utilities and infrastructure
"""
from app.core.config import settings
from app.core.response import (
    ResponseModel,
    PageResult,
    success_response,
    error_response,
    page_response
)
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
from app.core.handlers import register_exception_handlers
from app.core.database import db_manager, get_db, Base
from app.core.redis_client import redis_manager, get_redis
from app.core.elasticsearch_client import es_manager, get_elasticsearch
from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    decode_access_token
)

__all__ = [
    # Config
    "settings",
    # Response
    "ResponseModel",
    "PageResult",
    "success_response",
    "error_response",
    "page_response",
    # Exceptions
    "AppException",
    "ValidationException",
    "UnauthorizedException",
    "ForbiddenException",
    "NotFoundException",
    "ConflictException",
    "RateLimitException",
    "InternalServerException",
    "ExternalServiceException",
    # Handlers
    "register_exception_handlers",
    # Database
    "db_manager",
    "get_db",
    "Base",
    # Redis
    "redis_manager",
    "get_redis",
    # Elasticsearch
    "es_manager",
    "get_elasticsearch",
    # Security
    "verify_password",
    "get_password_hash",
    "create_access_token",
    "decode_access_token"
]
