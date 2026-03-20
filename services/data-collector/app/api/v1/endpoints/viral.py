"""
Viral Detection API Endpoints
"""
from typing import List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from loguru import logger

from app.adapters import get_platform_adapter
from app.services.viral_detector import viral_detector
from app.services.cleaning_pipeline import cleaning_pipeline
from app.core.response import success_response
from app.core.exceptions import ValidationException, NotFoundException

router = APIRouter()


# Request/Response Models
class TrendingRequest(BaseModel):
    """获取热门视频请求"""
    platform: str = Field(..., description="平台: douyin/bilibili/xiaohongshu")
    category: Optional[str] = Field(None, description="分类")
    limit: int = Field(default=50, description="返回数量")


class VideoDetailRequest(BaseModel):
    """获取视频详情请求"""
    platform: str = Field(..., description="平台")
    video_id: str = Field(..., description="视频ID")


class ViralDetectRequest(BaseModel):
    """爆款检测请求"""
    platform: str = Field(..., description="平台")
    video_id: str = Field(..., description="视频ID")
    comments: Optional[List[str]] = Field(None, description="评论列表")


class SearchRequest(BaseModel):
    """搜索视频请求"""
    keyword: str = Field(..., description="关键词")
    platform: Optional[str] = Field(None, description="平台筛选")
    limit: int = Field(default=20)


# API Endpoints
@router.post("/trending", summary="获取热门视频")
async def get_trending_videos(request: TrendingRequest):
    """
    获取指定平台的热门视频

    - **platform**: 平台 (douyin/bilibili/xiaohongshu)
    - **category**: 分类筛选(可选)
    - **limit**: 返回数量
    """
    try:
        adapter = get_platform_adapter(request.platform)

        # 获取热门视频
        videos = await adapter.get_trending_videos(
            category=request.category,
            limit=request.limit
        )

        # 数据清洗
        cleaned_videos = cleaning_pipeline.process_batch(videos)

        return success_response(data={
            "platform": request.platform,
            "videos": [v.to_dict() for v in cleaned_videos],
            "total": len(cleaned_videos)
        })

    except ValueError as e:
        raise ValidationException(str(e))
    except Exception as e:
        logger.error(f"Failed to get trending videos: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/detail", summary="获取视频详情")
async def get_video_detail(request: VideoDetailRequest):
    """
    获取视频详情

    - **platform**: 平台
    - **video_id**: 视频ID
    """
    try:
        adapter = get_platform_adapter(request.platform)

        video = await adapter.get_video_detail(request.video_id)

        if not video:
            raise NotFoundException(f"Video not found: {request.video_id}")

        # 数据清洗
        cleaned_video = cleaning_pipeline.process_video(video)

        return success_response(data=cleaned_video.to_dict() if cleaned_video else None)

    except ValueError as e:
        raise ValidationException(str(e))
    except NotFoundException:
        raise
    except Exception as e:
        logger.error(f"Failed to get video detail: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/detect", summary="爆款检测")
async def detect_viral(request: ViralDetectRequest):
    """
    检测视频是否具有爆款潜力

    - **platform**: 平台
    - **video_id**: 视频ID
    - **comments**: 评论列表(可选)
    """
    try:
        # 获取视频详情
        adapter = get_platform_adapter(request.platform)
        video = await adapter.get_video_detail(request.video_id)

        if not video:
            raise NotFoundException(f"Video not found: {request.video_id}")

        # 爆款检测
        signal = await viral_detector.detect(
            video=video,
            comments=request.comments
        )

        return success_response(data={
            "video": video.to_dict(),
            "signal": signal.to_dict()
        })

    except ValueError as e:
        raise ValidationException(str(e))
    except NotFoundException:
        raise
    except Exception as e:
        logger.error(f"Failed to detect viral: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/search", summary="搜索视频")
async def search_videos(request: SearchRequest):
    """
    搜索视频

    - **keyword**: 关键词
    - **platform**: 平台筛选(可选)
    - **limit**: 返回数量
    """
    try:
        if request.platform:
            # 指定平台搜索
            adapter = get_platform_adapter(request.platform)
            videos = await adapter.search_videos(
                keyword=request.keyword,
                limit=request.limit
            )
            platforms = [request.platform]
        else:
            # 全平台搜索
            platforms = ['douyin', 'bilibili', 'xiaohongshu']
            all_videos = []

            for platform in platforms:
                try:
                    adapter = get_platform_adapter(platform)
                    videos = await adapter.search_videos(
                        keyword=request.keyword,
                        limit=request.limit
                    )
                    all_videos.extend(videos)
                except Exception as e:
                    logger.warning(f"Failed to search {platform}: {e}")

            videos = all_videos

        # 数据清洗
        cleaned_videos = cleaning_pipeline.process_batch(videos)

        return success_response(data={
            "keyword": request.keyword,
            "videos": [v.to_dict() for v in cleaned_videos[:request.limit]],
            "total": len(cleaned_videos)
        })

    except ValueError as e:
        raise ValidationException(str(e))
    except Exception as e:
        logger.error(f"Failed to search videos: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/platforms", summary="获取支持的平台")
async def get_platforms():
    """获取支持的数据采集平台列表"""
    return success_response(data={
        "platforms": [
            {
                "name": "douyin",
                "display_name": "抖音",
                "features": ["热点扫描", "账号监控", "爆款检测"]
            },
            {
                "name": "bilibili",
                "display_name": "B站",
                "features": ["分区热榜", "弹幕分析", "投币率检测"]
            },
            {
                "name": "xiaohongshu",
                "display_name": "小红书",
                "features": ["笔记热门", "收藏分析", "带货潜力检测"]
            }
        ]
    })
