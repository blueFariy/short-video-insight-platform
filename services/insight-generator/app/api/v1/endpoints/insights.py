"""
Insight API Endpoints
"""
import json
from typing import List, Optional, Union, Dict, Any
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import Column, String, Text, BigInteger, text, Select
from loguru import logger

from app.services.insight_service import insight_service
from app.services.prompt_template import prompt_template_service
from app.core.response import success_response
from app.core.exceptions import ValidationException
from app.models import VideoInsight, Video, get_session_factory

router = APIRouter()


# Helper to get DB session
async def get_db():
    factory = get_session_factory()
    async with factory() as session:
        yield session


# Request model for saving video insight
class SaveVideoInsightRequest(BaseModel):
    """Save video insight request"""
    video_id: Optional[str] = Field(None,
                                    description="Video ID in videos table (optional if platform + platform_video_id provided)")
    platform: Optional[str] = Field(None, description="Video platform (douyin/bilibili/xiaohongshu)")
    platform_video_id: Optional[str] = Field(None, description="Platform video ID or URL")
    video_title: Optional[str] = Field(None, description="Video title")
    video_url: Optional[str] = Field(None, description="Video URL")
    ai_summary: Optional[str] = Field(None, description="AI summary")
    hook_3s: Optional[str] = Field(None, description="Golden 3s hook text")
    hook_type: Optional[str] = Field(None, description="Hook type")
    structure_type: Optional[str] = Field(None, description="Structure type")
    structure_analysis: Optional[dict] = Field(None, description="Structure analysis JSON")
    keywords: Optional[List[str]] = Field(None, description="Keywords")
    entity_tags: Optional[dict] = Field(None, description="Entity tags JSON")
    sentiment_score: Optional[float] = Field(None, description="Sentiment score")
    comment_high_freq: Optional[List[str]] = Field(None, description="Comment high frequency words")
    user_feedback: Optional[dict] = Field(None, description="User feedback JSON")
    viral_factors: Optional[dict] = Field(None, description="Viral factors JSON")
    improvements: Optional[List[str]] = Field(None, description="Improvement suggestions")


# 关键帧类型：字符串路径或对象
KeyframeType = Union[str, Dict[str, Any]]


def convert_keyframes(keyframes: Optional[List[KeyframeType]]) -> Optional[List[str]]:
    """转换关键帧格式：兼容对象数组和字符串数组"""
    if not keyframes:
        return None
    result = []
    for kf in keyframes:
        if isinstance(kf, str):
            result.append(kf)
        elif isinstance(kf, dict) and "path" in kf:
            result.append(kf["path"])
        elif isinstance(kf, dict) and "url" in kf:
            result.append(kf["url"])
    return result if result else None


# Request/Response Models
class GoldenHookRequest(BaseModel):
    """Golden 3-second hook analysis request"""
    video_title: str = Field(..., description="视频标题")
    video_script: str = Field(..., description="视频脚本 (ASR文本)")
    keyframes: Optional[List[KeyframeType]] = Field(default=None, description="关键帧图片路径或对象数组")

    @field_validator('keyframes', mode='before')
    @classmethod
    def parse_keyframes(cls, v):
        return convert_keyframes(v)


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
    keyframes: Optional[List[KeyframeType]] = Field(default=None, description="关键帧路径或对象数组")
    duration: Optional[int] = Field(default=None, description="视频时长(秒)")

    @field_validator('keyframes', mode='before')
    @classmethod
    def parse_keyframes(cls, v):
        return convert_keyframes(v)


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


# Video Insight Save Endpoints
@router.post("/video-insights", summary="保存视频洞察")
async def save_video_insight(
        request: SaveVideoInsightRequest,
        db: AsyncSession = Depends(get_db)
):
    """
    保存视频洞察到数据库

    支持两种方式指定视频：
    1. 直接使用 video_id (videos表主键)
    2. 使用 platform + platform_video_id (会自动查找或创建视频记录)

    - **video_id**: 视频ID (videos表主键) (可选)
    - **platform**: 视频平台 (可选)
    - **platform_video_id**: 平台视频ID (可选)
    - **video_title**: 视频标题 (可选)
    - **video_url**: 视频URL (可选)
    - **ai_summary**: AI总结
    - **hook_3s**: 黄金3秒文案
    - **hook_type**: 钩子类型
    - **structure_type**: 结构类型
    - **structure_analysis**: 结构分析 (JSON)
    - **keywords**: 关键词列表
    - **entity_tags**: 实体标签 (JSON)
    - **sentiment_score**: 情感分数
    - **comment_high_freq**: 评论高频词列表
    - **user_feedback**: 用户反馈 (JSON)
    - **viral_factors**: 爆款因子 (JSON)
    """
    from sqlalchemy import select
    from app.models import Base

    try:
        video_id = request.video_id

        if not video_id:
            raise ValidationException("需要提供 video_id 或 (platform + platform_video_id)")
        existing_video = await db.execute(Select(Video).where(Video.video_id == video_id))
        video = existing_video.scalar_one_or_none()

        existing = await db.execute(
            Select(VideoInsight).where(VideoInsight.video_id == video.video_id)
        )
        if result := existing.scalar_one_or_none():
            return success_response(data={
                "id": result.id,
                "video_id": result.video_id,
                "message": "请勿重复保存"
            })

        insight = VideoInsight(
            video_id=video.video_id,
            ai_summary=request.ai_summary,
            hook_3s=request.hook_3s,
            hook_type=request.hook_type,
            structure_type=request.structure_type,
            structure_analysis=request.structure_analysis,
            keywords=request.keywords,
            entity_tags=request.entity_tags,
            sentiment_score=request.sentiment_score,
            comment_high_freq=request.comment_high_freq,
            user_feedback=request.user_feedback,
            viral_factors=request.viral_factors,
            improvements=request.improvements
        )

        db.add(insight)
        await db.commit()
        await db.refresh(insight)
        logger.info(f"Video insight saved: video_id={video_id}")
        return success_response(data={
            "id": insight.id,
            "video_id": insight.video_id,
            "message": "Insight saved successfully"
        })
    except ValidationException:
        raise
    except Exception as e:
        logger.error(f"Failed to save video insight: {e}")
        raise ValidationException(f"保存失败: {str(e)}")


@router.get(
    "/video-insights/all",
    summary="获取洞察列表"
)
async def get_all_insights(
        page: int = 1,
        page_size: int = 20,
        video_id: Optional[int] = None,
        hook_type: Optional[str] = None,
        structure_type: Optional[str] = None,
        db: AsyncSession = Depends(get_db)
):
    """
    获取洞察列表

    - **video_id**: 按视频ID筛选 (可选)
    - **hook_type**: 按钩子类型筛选 (可选)
    - **structure_type**: 按结构类型筛选 (可选)
    - **page**: 页码 (默认1)
    - **page_size**: 每页数量 (默认20)
    """
    from sqlalchemy import select, desc, func

    # 构建筛选条件字典
    filters = {}
    if video_id is not None:
        filters['video_id'] = video_id
    if hook_type is not None:
        filters['hook_type'] = hook_type
    if structure_type is not None:
        filters['structure_type'] = structure_type

    # 构建查询 - 联合Video表获取视频信息
    stmt = select(VideoInsight, Video).join(
        Video, VideoInsight.video_id == Video.video_id, isouter=True
    )
    for key, value in filters.items():
        stmt = stmt.where(getattr(VideoInsight, key) == value)

    # 排序和分页
    stmt = stmt.order_by(desc(VideoInsight.created_at))
    stmt = stmt.offset((page - 1) * page_size).limit(page_size)

    # 执行查询
    result = await db.execute(stmt)
    rows = result.all()

    # 获取总数
    count_stmt = select(func.count()).select_from(VideoInsight)
    for key, value in filters.items():
        count_stmt = count_stmt.where(getattr(VideoInsight, key) == value)

    total_result = await db.execute(count_stmt)
    total = total_result.scalar()

    if not rows:
        return success_response(data={
            "items": [],
            "total": 0,
            "page": page,
            "page_size": page_size
        })

    # Convert ORM objects to dict for serialization
    insights_data = []
    for insight, video in rows:
        # 计算综合评分
        overall_score = 0
        dimensions = insight.viral_factors or {}
        if dimensions:
            score_values = [v for k, v in dimensions.items() if isinstance(v, (int, float)) and k.endswith('_score')]
            if score_values:
                overall_score = round(sum(score_values) / len(score_values))

        insights_data.append({
            "id": insight.id,
            "video_id": insight.video_id,
            "video_info": {
                "title": video.title if video else None,
                "platform": video.platform if video else None,
                "cover_url": video.cover_image_url if video else None,
                "url": video.video_url if video else None,
                "play_count": video.play_count if video else 0,
                "like_count": video.like_count if video else 0,
                "comment_count": video.comment_count if video else 0,
                "share_count": video.share_count if video else 0
            },
            "ai_summary": insight.ai_summary,
            "hook_3s": insight.hook_3s,
            "hook_type": insight.hook_type,
            "structure_type": insight.structure_type,
            "structure_analysis": insight.structure_analysis,
            "keywords": insight.keywords,
            "entity_tags": insight.entity_tags,
            "sentiment_score": insight.sentiment_score,
            "comment_high_freq": insight.comment_high_freq,
            "user_feedback": insight.user_feedback,
            "viral_factors": insight.viral_factors,
            "improvements": insight.improvements,
            "overall_score": overall_score,
            "created_at": insight.created_at.isoformat() if insight.created_at else None
        })

    return success_response(data={
        "items": insights_data,
        "total": total,
        "page": page,
        "page_size": page_size
    })


@router.get("/video-insights/{video_id}", summary="获取视频洞察详情")
async def get_video_insight(
        video_id: str,
        db: AsyncSession = Depends(get_db)
):
    """获取视频的最新洞察"""
    from sqlalchemy import select, desc
    result = await db.execute(
        select(VideoInsight, Video).join(
            Video, VideoInsight.video_id == Video.video_id, isouter=True
        ).where(VideoInsight.video_id == video_id)
        .order_by(desc(VideoInsight.created_at))
        .limit(1)
    )
    row = result.one_or_none()

    if not row:
        raise HTTPException(status_code=404, detail="Insight not found for this video")

    insight, video = row

    # 计算综合评分
    overall_score = 0
    dimensions = insight.viral_factors or {}
    if dimensions:
        score_values = [v for k, v in dimensions.items() if isinstance(v, (int, float)) and k.endswith('_score')]
        if score_values:
            overall_score = round(sum(score_values) / len(score_values))

    return success_response(data={
        "id": insight.id,
        "video_id": insight.video_id,
        "video_info": {
            "title": video.title if video else None,
            "platform": video.platform if video else None,
            "cover_url": video.cover_image_url if video else None,
            "url": video.video_url if video else None,
            "play_count": video.play_count if video else 0,
            "like_count": video.like_count if video else 0,
            "comment_count": video.comment_count if video else 0,
            "share_count": video.share_count if video else 0
        },
        "ai_summary": insight.ai_summary,
        "hook_3s": insight.hook_3s,
        "hook_type": insight.hook_type,
        "structure_type": insight.structure_type,
        "structure_analysis": insight.structure_analysis,
        "keywords": insight.keywords,
        "entity_tags": insight.entity_tags,
        "sentiment_score": insight.sentiment_score,
        "comment_high_freq": insight.comment_high_freq,
        "user_feedback": insight.user_feedback,
        "viral_factors": insight.viral_factors,
        "improvements": insight.improvements,
        "overall_score": overall_score,
        "created_at": insight.created_at.isoformat() if insight.created_at else None
    })
