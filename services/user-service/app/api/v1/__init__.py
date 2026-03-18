"""
API v1 Router
"""
from fastapi import APIRouter
from app.api.v1.endpoints import users, collections

api_router = APIRouter()

# 用户管理
api_router.include_router(users.router)

# 收藏管理
api_router.include_router(collections.router)
