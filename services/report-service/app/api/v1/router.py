"""
API Router
"""
from fastapi import APIRouter
from app.api.v1.endpoints import reports, trend_reports

api_router = APIRouter()

# Include routers
api_router.include_router(reports.router, prefix="/reports", tags=["Reports"])
api_router.include_router(trend_reports.router, prefix="/reports", tags=["Trend Reports"])
