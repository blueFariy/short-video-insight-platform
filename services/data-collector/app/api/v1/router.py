"""
API Router
"""
from fastapi import APIRouter
from app.api.v1.endpoints import collector

api_router = APIRouter()

# Include routers
api_router.include_router(collector.router, prefix="/collector", tags=["Collector"])
