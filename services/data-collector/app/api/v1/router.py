"""
API Router
"""
from fastapi import APIRouter
from app.api.v1.endpoints import collector, viral, viral_alert, scheduled_task

api_router = APIRouter()

# Include routers
api_router.include_router(collector.router, prefix="/collector", tags=["Collector"])
api_router.include_router(viral.router, prefix="/viral", tags=["Viral Detection"])
api_router.include_router(viral_alert.router, prefix="/collector", tags=["爆款雷达"])
api_router.include_router(scheduled_task.router, prefix="/scheduler", tags=["定时任务管理"])
