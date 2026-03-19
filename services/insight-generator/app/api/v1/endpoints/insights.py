"""
Insight API Endpoints
"""
from typing import List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from loguru import logger

from app.services.insight_service import insight_service
from app.services.prompt_template import prompt_template_service
from app.core.response import success_response
from app.core.exceptions import ValidationException

router = APIRouter()


# Request/Response Models
class GoldenHookRequest(BaseModel):
    """Golden 3-second hook analysis request"""
    video_title: str = Field(..., description="视频标题")
    video_script: str = Field(..., description="视频脚本 (ASR文本)")
    keyframes: Optional[List[str]] = Field(default=None, description="关键帧图片路径")


class ScriptStructureRequest(BaseModel):
    """Script structure analysis request"""
    video_title: str = Field(..., description="视频标题")
    video_script: str = Field(..., description="视频脚本")
    duration: Optional[int] = Field(default=None, description="视频时长(秒)")


class SentimentRequest(BaseModel):
    """Sentiment analysis request"""
    comments: List[str] = Field(..., description="评论列表")
    video_title: Optional[str] = Field(default=None, description="视频标题")


class ComprehensiveRequest(BaseModel):
    """Comprehensive analysis request"""
    video_title: str = Field(..., description="视频标题")
    video_script: str = Field(..., description="视频脚本")
    comments: Optional[List[str]] = Field(default=None, description="评论列表")
    keyframes: Optional[List[str]] = Field(default=None, description="关键帧路径")
    duration: Optional[int] = Field(default=None, description="视频时长(秒)")


class ScriptSegmentsRequest(BaseModel):
    """Script segments extraction request"""
    video_script: str = Field(..., description="完整脚本")
    duration: int = Field(..., description="视频时长(秒)")


# API Endpoints
@router.post("/golden-hook", summary="黄金3秒开场分析")
async def analyze_golden_hook(request: GoldenHookRequest):
    """
    分析视频的黄金3秒开场文案

    - **video_title**: 视频标题
    - **video_script**: 视频脚本 (ASR识别的文字)
    - **keyframes**: 关键帧图片路径列表(可选)
    """
    if not request.video_script.strip():
        raise ValidationException("视频脚本不能为空")

    result = await insight_service.analyze_golden_hook(
        video_title=request.video_title,
        video_script=request.video_script,
        keyframes=request.keyframes
    )

    return success_response(data=result)


@router.post("/script-structure", summary="脚本结构分析")
async def analyze_script_structure(request: ScriptStructureRequest):
    """
    分析视频脚本的内容结构

    - **video_title**: 视频标题
    - **video_script**: 视频脚本
    - **duration**: 视频时长(秒)(可选)
    """
    if not request.video_script.strip():
        raise ValidationException("视频脚本不能为空")

    result = await insight_service.analyze_script_structure(
        video_title=request.video_title,
        video_script=request.video_script,
        duration=request.duration
    )

    return success_response(data=result)


@router.post("/sentiment", summary="评论区情感分析")
async def analyze_sentiment(request: SentimentRequest):
    """
    分析评论区的用户情感倾向

    - **comments**: 评论列表
    - **video_title**: 视频标题(可选)
    """
    if not request.comments or len(request.comments) == 0:
        raise ValidationException("评论列表不能为空")

    result = await insight_service.analyze_sentiment(
        comments=request.comments,
        video_title=request.video_title
    )

    return success_response(data=result)


@router.post("/comprehensive", summary="综合爆款分析")
async def analyze_comprehensive(request: ComprehensiveRequest):
    """
    生成完整的爆款分析报告

    - **video_title**: 视频标题
    - **video_script**: 视频脚本
    - **comments**: 评论列表(可选)
    - **keyframes**: 关键帧路径(可选)
    - **duration**: 视频时长(秒)(可选)
    """
    if not request.video_script.strip():
        raise ValidationException("视频脚本不能为空")

    result = await insight_service.generate_comprehensive_report(
        video_title=request.video_title,
        video_script=request.video_script,
        comments=request.comments,
        keyframes=request.keyframes,
        duration=request.duration
    )

    return success_response(data=result)


@router.post("/segments", summary="脚本分段提取")
async def extract_script_segments(request: ScriptSegmentsRequest):
    """
    提取脚本的时间分段

    - **video_script**: 完整脚本
    - **duration**: 视频时长(秒)
    """
    if not request.video_script.strip():
        raise ValidationException("视频脚本不能为空")
    if request.duration <= 0:
        raise ValidationException("视频时长必须大于0")

    result = await insight_service.extract_script_segments(
        video_script=request.video_script,
        duration=request.duration
    )

    return success_response(data={"segments": result})


# Prompt Template Endpoints
@router.get("/templates", summary="获取提示词模板列表")
async def list_templates(category: Optional[str] = None):
    """
    获取提示词模板列表

    - **category**: 按分类筛选(可选)
    """
    templates = prompt_template_service.list_templates(category)
    return success_response(data={
        "templates": [
            {
                "id": t.id,
                "name": t.name,
                "description": t.description,
                "category": t.category
            }
            for t in templates
        ]
    })


@router.get("/templates/{template_id}", summary="获取提示词模板详情")
async def get_template(template_id: str):
    """获取指定模板的详情"""
    template = prompt_template_service.get_template(template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    return success_response(data={
        "id": template.id,
        "name": template.name,
        "description": template.description,
        "template": template.template,
        "category": template.category
    })
