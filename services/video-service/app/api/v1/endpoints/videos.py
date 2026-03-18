"""
Video Processing Endpoints
"""
from typing import Optional, List
from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, Field

from app.core.response import success_response, ResponseModel
from app.services.video_processor import video_processor
from app.services.video_search import video_search_service
from app.services.embedding import embedding_service


router = APIRouter(prefix="/videos", tags=["视频处理"])


class ProcessVideoRequest(BaseModel):
    """处理视频请求"""
    url: str = Field(..., description="视频URL")
    platform: Optional[str] = Field(None, description="视频平台")
    options: Optional[dict] = Field(default={}, description="处理选项")


class SearchByTextRequest(BaseModel):
    """文本搜索请求"""
    query: str = Field(..., description="搜索文本")
    platform: Optional[str] = Field(None, description="平台过滤")
    category: Optional[str] = Field(None, description="分类过滤")
    page: int = Field(1, description="页码")
    page_size: int = Field(10, description="每页数量")


class SearchByVectorRequest(BaseModel):
    """向量搜索请求"""
    vector: List[float] = Field(..., description="查询向量")
    platform: Optional[str] = Field(None, description="平台过滤")
    page: int = Field(1, description="页码")
    page_size: int = Field(10, description="每页数量")


class IndexVideoRequest(BaseModel):
    """索引视频请求"""
    video_id: str = Field(..., description="视频ID")
    video_data: dict = Field(..., description="视频数据")
    vector: Optional[List[float]] = Field(None, description="视频向量")


@router.post(
    "/process",
    response_model=ResponseModel,
    summary="处理视频"
)
async def process_video(request: ProcessVideoRequest):
    """
    完整处理视频：下载、关键帧、ASR、OCR

    - **url**: 视频URL
    - **platform**: 视频平台 (douyin/bilibili/xiaohongshu)
    - **options**: 处理选项
    """
    result = await video_processor.process_video(
        url=request.url,
        platform=request.platform,
        options=request.options
    )
    return success_response(data=result)


@router.post(
    "/download",
    response_model=ResponseModel,
    summary="下载视频"
)
async def download_video(url: str, platform: Optional[str] = None):
    """下载视频"""
    result = await video_processor.download_only(url, platform)
    return success_response(data=result)


@router.post(
    "/keyframes",
    response_model=ResponseModel,
    summary="提取关键帧"
)
async def extract_keyframes(
    video_path: str,
    num_frames: int = 10,
    method: str = "scene_change"
):
    """提取关键帧"""
    result = await video_processor.extract_keyframes_only(
        video_path=video_path,
        num_frames=num_frames,
        method=method
    )
    return success_response(data=result)


@router.post(
    "/asr",
    response_model=ResponseModel,
    summary="语音识别"
)
async def run_asr(
    video_path: str,
    provider: str = "whisper",
    language: str = "zh"
):
    """语音识别"""
    result = await video_processor.asr_only(
        video_path=video_path,
        provider=provider,
        language=language
    )
    return success_response(data=result)


@router.post(
    "/ocr",
    response_model=ResponseModel,
    summary="文字识别"
)
async def run_ocr(
    image_paths: List[str],
    provider: str = "easyocr"
):
    """文字识别"""
    result = await video_processor.ocr_only(
        image_paths=image_paths,
        provider=provider
    )
    return success_response(data=result)


# ============ 搜索接口 ============

@router.post(
    "/search/text",
    response_model=ResponseModel,
    summary="文本搜索"
)
async def search_by_text(request: SearchByTextRequest):
    """文本搜索视频"""
    filters = {}
    if request.platform:
        filters["platform"] = request.platform
    if request.category:
        filters["category"] = request.category

    result = await video_search_service.search_by_text(
        query=request.query,
        filters=filters,
        page=request.page,
        page_size=request.page_size
    )
    return success_response(data=result)


@router.post(
    "/search/vector",
    response_model=ResponseModel,
    summary="向量搜索"
)
async def search_by_vector(request: SearchByVectorRequest):
    """向量相似度搜索"""
    filters = {}
    if request.platform:
        filters["platform"] = request.platform

    result = await video_search_service.search_by_vector(
        vector=request.vector,
        filters=filters,
        page=request.page,
        page_size=request.page_size
    )
    return success_response(data=result)


@router.post(
    "/search/similar/{video_id}",
    response_model=ResponseModel,
    summary="查找相似视频"
)
async def search_similar(
    video_id: str,
    platform: Optional[str] = None,
    page: int = 1,
    page_size: int = 10
):
    """查找相似视频"""
    filters = {}
    if platform:
        filters["platform"] = platform

    result = await video_search_service.search_similar(
        video_id=video_id,
        filters=filters,
        page=page,
        page_size=page_size
    )
    return success_response(data=result)


@router.post(
    "/search/image",
    response_model=ResponseModel,
    summary="图片搜索"
)
async def search_by_image(
    image_path: str,
    platform: Optional[str] = None,
    page: int = 1,
    page_size: int = 10
):
    """通过图片搜索相似视频"""
    filters = {}
    if platform:
        filters["platform"] = platform

    result = await video_search_service.search_by_image(
        image_path=image_path,
        filters=filters,
        page=page,
        page_size=page_size
    )
    return success_response(data=result)


# ============ 索引接口 ============

@router.post(
    "/index",
    response_model=ResponseModel,
    summary="索引视频"
)
async def index_video(request: IndexVideoRequest):
    """索引视频到搜索引擎"""
    doc_id = await video_search_service.index_video(
        video_id=request.video_id,
        video_data=request.video_data,
        vector=request.vector
    )
    return success_response(data={"doc_id": doc_id})


@router.delete(
    "/index/{video_id}",
    response_model=ResponseModel,
    summary="删除视频索引"
)
async def delete_video_index(video_id: str):
    """删除视频索引"""
    await video_search_service.delete_video(video_id)
    return success_response(message="Video deleted from index")


# ============ Embedding 接口 ============

@router.post(
    "/embed/text",
    response_model=ResponseModel,
    summary="文本向量化"
)
async def embed_texts(texts: List[str], provider: Optional[str] = None):
    """文本向量化"""
    vectors = await embedding_service.embed_texts(texts, provider)
    return success_response(data={"vectors": vectors})


@router.post(
    "/embed/image",
    response_model=ResponseModel,
    summary="图像向量化"
)
async def embed_images(image_paths: List[str]):
    """图像向量化"""
    vectors = await embedding_service.embed_images(image_paths)
    return success_response(data={"vectors": vectors})
