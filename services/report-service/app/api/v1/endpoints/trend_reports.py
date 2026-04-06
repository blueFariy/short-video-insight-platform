"""
Trend Reports API Endpoints - 趋势报告 API
"""
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from loguru import logger

from app.services.trend_report_service import trend_report_service
from app.core.response import success_response
from app.core.exceptions import NotFoundException, ValidationException

router = APIRouter()


# Request Models
class GenerateTrendReportRequest(BaseModel):
    """生成趋势报告请求"""
    type: str = Field(default="weekly", description="报告类型: daily/weekly/monthly")
    platform: Optional[str] = Field(default=None, description="平台筛选: douyin/bilibili/xiaohongshu/kuaishou")
    category: Optional[str] = Field(default=None, description="分类筛选")


# Statistics Endpoints
@router.get("/trend/statistics", summary="获取趋势统计")
async def get_trend_statistics(
    days: int = Query(default=7, ge=1, le=90, description="统计天数"),
    platform: Optional[str] = Query(default=None, description="平台筛选"),
    category: Optional[str] = Query(default=None, description="分类筛选")
):
    """
    获取趋势统计数据

    - **days**: 统计天数 (1-90)
    - **platform**: 平台筛选 (douyin/bilibili/xiaohongshu/kuaishou)
    - **category**: 分类筛选
    """
    logger.info(f"Getting trend statistics: days={days}, platform={platform}, category={category}")

    try:
        statistics = await trend_report_service.get_statistics(
            days=days,
            platform=platform,
            category=category
        )
        return success_response(data=statistics)
    except Exception as e:
        logger.error(f"Error getting trend statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/trend/viral", summary="获取爆款趋势")
async def get_viral_trends(
    days: int = Query(default=7, ge=1, le=90, description="统计天数"),
    platform: Optional[str] = Query(default=None, description="平台筛选")
):
    """
    获取爆款趋势数据

    - **days**: 统计天数 (1-90)
    - **platform**: 平台筛选
    """
    logger.info(f"Getting viral trends: days={days}, platform={platform}")

    try:
        trends = await trend_report_service.get_viral_trends(
            days=days,
            platform=platform
        )
        return success_response(data=trends)
    except Exception as e:
        logger.error(f"Error getting viral trends: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Report Generation Endpoints
@router.post("/trend/generate", summary="生成趋势报告")
async def generate_trend_report(request: GenerateTrendReportRequest):
    """
    生成趋势报告

    - **type**: 报告类型 (daily/weekly/monthly)
    - **platform**: 平台筛选
    - **category**: 分类筛选
    """
    logger.info(f"Generating trend report: type={request.type}, platform={request.platform}")

    # 验证报告类型
    valid_types = ["daily", "weekly", "monthly"]
    if request.type not in valid_types:
        raise ValidationException(f"Invalid report type. Must be one of: {valid_types}")

    try:
        report = await trend_report_service.generate_trend_report(
            report_type=request.type,
            platform=request.platform,
            category=request.category
        )
        return success_response(data={
            "id": report.get("id"),
            "title": report["title"],
            "report_type": report["report_type"],
            "period_start": report["period_start"],
            "period_end": report["period_end"],
            "created_at": report["created_at"]
        }, message="Report generated successfully")
    except Exception as e:
        logger.error(f"Error generating trend report: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Report List Endpoints
@router.get("/trend/list", summary="获取趋势报告列表")
async def get_trend_report_list(
    type: Optional[str] = Query(default=None, description="报告类型筛选"),
    limit: int = Query(default=10, ge=1, le=50, description="返回数量")
):
    """
    获取趋势报告列表

    - **type**: 报告类型 (daily/weekly/monthly)
    - **limit**: 返回数量 (1-50)
    """
    logger.info(f"Getting trend report list: type={type}, limit={limit}")

    try:
        reports = await trend_report_service.get_report_list(
            report_type=type,
            limit=limit
        )
        return success_response(data={
            "reports": reports,
            "total": len(reports)
        })
    except Exception as e:
        logger.error(f"Error getting trend report list: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/trend/{report_id}", summary="获取趋势报告详情")
async def get_trend_report_detail(report_id: int):
    """
    获取趋势报告详情

    - **report_id**: 报告ID
    """
    logger.info(f"Getting trend report detail: id={report_id}")

    try:
        report = await trend_report_service.get_report_by_id(report_id)
        if not report:
            raise NotFoundException(f"Report not found: {report_id}")

        return success_response(data=report)
    except NotFoundException:
        raise
    except Exception as e:
        logger.error(f"Error getting trend report detail: {e}")
        raise HTTPException(status_code=500, detail=str(e))
