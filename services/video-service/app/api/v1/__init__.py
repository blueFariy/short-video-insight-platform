"""
API v1 Router
"""
from fastapi import APIRouter
from app.api.v1.endpoints import videos

api_router = APIRouter()

# 视频处理
api_router.include_router(videos.router)
