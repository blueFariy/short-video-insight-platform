"""
Report API Endpoints
"""
from typing import List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from loguru import logger

from app.services.report_service import report_service
from app.services.export_service import export_service
from app.services.statistics_service import statistics_service
from app.core.response import success_response
from app.core.exceptions import NotFoundException, ValidationException

router = APIRouter()


# Statistics Endpoints
@router.get("/statistics/overview", summary="获取统计概览")
async def get_overview():
    """获取统计数据概览"""
    stats = await statistics_service.get_overview()
    return success_response(data=stats)


@router.get("/statistics/platforms", summary="获取平台统计")
async def get_platform_stats():
    """获取各平台统计数据"""
    stats = await statistics_service.get_platform_stats()
    return success_response(data=stats)


@router.get("/statistics/categories", summary="获取分类统计")
async def get_category_stats():
    """获取分类统计数据"""
    stats = await statistics_service.get_category_stats()
    return success_response(data=stats)


@router.get("/statistics/time", summary="获取时间统计")
async def get_time_stats(days: int = 30):
    """
    获取时间维度统计

    - **days**: 天数
    """
    stats = await statistics_service.get_time_stats(days)
    return success_response(data=stats)


@router.get("/statistics/top", summary="获取热门内容")
async def get_top_content(
    metric: str = "views",
    limit: int = 10
):
    """
    获取热门内容排行

    - **metric**: 指标 (views/likes/comments)
    - **limit**: 返回数量
    """
    stats = await statistics_service.get_top_content(metric, limit)
    return success_response(data=stats)


@router.get("/statistics/engagement", summary="获取互动统计")
async def get_engagement_stats():
    """获取互动统计数据"""
    stats = await statistics_service.get_engagement_stats()
    return success_response(data=stats)


# Report Endpoints
@router.get("/reports", summary="获取报表列表")
async def list_reports(report_type: Optional[str] = None, limit: int = 50):
    """
    获取报表列表

    - **report_type**: 报表类型
    - **limit**: 返回数量
    """
    reports = await report_service.list_reports(report_type, limit)
    return success_response(data={
        "reports": [
            {
                "id": r.id,
                "name": r.name,
                "type": r.type,
                "description": r.description,
                "created_at": r.created_at.isoformat(),
                "created_by": r.created_by
            }
            for r in reports
        ],
        "total": len(reports)
    })


@router.get("/reports/{report_id}", summary="获取报表详情")
async def get_report(report_id: str):
    """获取报表详情"""
    report = await report_service.get_report(report_id)
    if not report:
        raise NotFoundException(f"Report not found: {report_id}")
    return success_response(data={
        "id": report.id,
        "name": report.name,
        "type": report.type,
        "description": report.description,
        "data": report.data,
        "created_at": report.created_at.isoformat(),
        "created_by": report.created_by
    })


@router.delete("/reports/{report_id}", summary="删除报表")
async def delete_report(report_id: str):
    """删除报表"""
    success = await report_service.delete_report(report_id)
    if not success:
        raise NotFoundException(f"Report not found: {report_id}")
    return success_response(message="Report deleted successfully")


# Report Generation Endpoints
@router.post("/reports/generate/video", summary="生成视频分析报表")
async def generate_video_report(videos: List[dict]):
    """生成视频分析报表"""
    if not videos:
        raise ValidationException("No videos provided")

    report = await report_service.generate_video_report(videos)
    return success_response(data={
        "id": report.id,
        "name": report.name,
        "created_at": report.created_at.isoformat()
    })


@router.post("/reports/generate/competitor", summary="生成竞品报表")
async def generate_competitor_report(accounts: List[dict]):
    """生成竞品概览报表"""
    if not accounts:
        raise ValidationException("No accounts provided")

    report = await report_service.generate_competitor_report(accounts)
    return success_response(data={
        "id": report.id,
        "name": report.name,
        "created_at": report.created_at.isoformat()
    })


@router.post("/reports/generate/trend", summary="生成趋势报表")
async def generate_trend_report(days: int = 30):
    """生成趋势分析报表"""
    report = await report_service.generate_trend_report(days)
    return success_response(data={
        "id": report.id,
        "name": report.name,
        "created_at": report.created_at.isoformat()
    })


# Export Endpoints
@router.get("/export/formats", summary="获取导出格式")
async def get_export_formats():
    """获取支持的导出格式"""
    formats = export_service.get_export_formats()
    return success_response(data={"formats": formats})


@router.post("/reports/{report_id}/export", summary="导出报表")
async def export_report(
    report_id: str,
    format: str = "json"
):
    """
    导出报表

    - **report_id**: 报表ID
    - **format**: 导出格式 (json/csv/excel)
    """
    report = await report_service.get_report(report_id)
    if not report:
        raise NotFoundException(f"Report not found: {report_id}")

    result = await export_service.export_report(report.data, format)
    return success_response(data=result)
