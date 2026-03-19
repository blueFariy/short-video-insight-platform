"""
API Router
"""
from fastapi import APIRouter
from app.api.v1.endpoints import insights

api_router = APIRouter()

# Include routers
api_router.include_router(insights.router, prefix="/insights", tags=["Insights"])
