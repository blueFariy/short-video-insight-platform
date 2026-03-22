"""
Data Collector API Endpoints
"""
from typing import List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from loguru import logger

from app.services.account_service import account_service
from app.services.collector_service import collector_service
from app.services.scheduler_service import scheduler_service
from app.core.response import success_response
from app.core.exceptions import ValidationException, NotFoundException

router = APIRouter()


# Account Request/Response Models
class CreateAccountRequest(BaseModel):
    """Create account request"""
    name: str = Field(..., description="Account name")
    platform: str = Field(..., description="Platform: douyin/bilibili/xiaohongshu/kuaishou")
    account_id: str = Field(..., description="Account ID on platform")
    url: str = Field(..., description="Account URL")
    category: str = Field(default="general", description="Account category")


class UpdateAccountRequest(BaseModel):
    """Update account request"""
    name: Optional[str] = None
    category: Optional[str] = None
    status: Optional[str] = None


# Collector Request/Response Models
class CollectRequest(BaseModel):
    """Collect videos request"""
    account_id: str = Field(..., description="Account ID")
    limit: int = Field(default=50, description="Max videos to collect")


class CollectAllRequest(BaseModel):
    """Collect all accounts request"""
    platform: Optional[str] = None
    limit: int = Field(default=50)


class SearchRequest(BaseModel):
    """Search videos request"""
    keyword: str
    platform: Optional[str] = None
    limit: int = Field(default=20)


# Account Endpoints
@router.post("/accounts", summary="创建竞品账号")
async def create_account(request: CreateAccountRequest):
    """
    创建新的竞品账号

    - **name**: 账号名称
    - **platform**: 平台 (douyin/bilibili/xiaohongshu/kuaishou)
    - **account_id**: 平台账号ID
    - **url**: 账号URL
    - **category**: 分类
    """
    account = await account_service.create_account(
        name=request.name,
        platform=request.platform,
        account_id=request.account_id,
        url=request.url,
        category=request.category
    )
    return success_response(data=account.to_dict())


@router.get("/accounts", summary="获取账号列表")
async def list_accounts(
    platform: Optional[str] = None,
    category: Optional[str] = None,
    status: Optional[str] = None
):
    """
    获取账号列表

    - **platform**: 按平台筛选
    - **category**: 按分类筛选
    - **status**: 按状态筛选
    """
    accounts = await account_service.list_accounts(platform, category, status)
    return success_response(data={
        "accounts": [a.to_dict() for a in accounts],
        "total": len(accounts)
    })


@router.get("/accounts/{account_id}", summary="获取账号详情")
async def get_account(account_id: str):
    """获取指定账号详情"""
    account = await account_service.get_account(account_id)
    if not account:
        raise NotFoundException(f"Account not found: {account_id}")
    return success_response(data=account.to_dict())


@router.put("/accounts/{account_id}", summary="更新账号")
async def update_account(account_id: str, request: UpdateAccountRequest):
    """更新账号信息"""
    account = await account_service.update_account(
        account_id=account_id,
        name=request.name,
        category=request.category,
        status=request.status
    )
    if not account:
        raise NotFoundException(f"Account not found: {account_id}")
    return success_response(data=account.to_dict())


@router.delete("/accounts/{account_id}", summary="删除账号")
async def delete_account(account_id: str):
    """删除账号"""
    success = await account_service.delete_account(account_id)
    if not success:
        raise NotFoundException(f"Account not found: {account_id}")
    return success_response(message="Account deleted successfully")


# Collector Endpoints
@router.post("/collect", summary="采集指定账号")
async def collect_account(request: CollectRequest):
    """
    采集指定账号的视频

    - **account_id**: 账号ID
    - **limit**: 最大采集数量
    """
    account = await account_service.get_account(request.account_id)
    if not account:
        raise NotFoundException(f"Account not found: {request.account_id}")

    videos = await collector_service.collect_account(account, request.limit)
    return success_response(data={
        "account": account.to_dict(),
        "videos": [v.to_dict() for v in videos],
        "total": len(videos)
    })


@router.post("/collect/all", summary="采集所有账号")
async def collect_all(request: CollectAllRequest):
    """
    采集所有活跃账号的视频

    - **platform**: 按平台筛选(可选)
    - **limit**: 每个账号最大采集数量
    """
    results = await collector_service.collect_all_active(request.platform)

    all_videos = []
    for account_id, videos in results.items():
        all_videos.extend(videos)

    return success_response(data={
        "accounts_collected": len(results),
        "videos": [v.to_dict() for v in all_videos],
        "total": len(all_videos)
    })


@router.get("/videos", summary="获取视频列表")
async def list_videos(
    platform: Optional[str] = None,
    account_id: Optional[str] = None,
    limit: int = 50
):
    """获取已采集的视频列表"""
    if account_id:
        videos = await collector_service.get_videos_by_account(account_id)
    elif platform:
        videos = await collector_service.get_videos_by_platform(platform)
    else:
        videos = await collector_service.get_all_videos(limit)

    videos = videos[:limit]
    return success_response(data={
        "videos": [v.to_dict() for v in videos],
        "total": len(videos)
    })


@router.get("/videos/{video_id}", summary="获取视频详情")
async def get_video(video_id: str):
    """获取视频详情"""
    video = await collector_service.get_video(video_id)
    if not video:
        raise NotFoundException(f"Video not found: {video_id}")
    return success_response(data=video.to_dict())


@router.post("/videos/search", summary="搜索视频")
async def search_videos(request: SearchRequest):
    """
    搜索视频

    - **keyword**: 关键词
    - **platform**: 按平台筛选(可选)
    - **limit**: 返回数量限制
    """
    videos = await collector_service.search_videos(
        keyword=request.keyword,
        platform=request.platform,
        limit=request.limit
    )
    return success_response(data={
        "videos": [v.to_dict() for v in videos],
        "total": len(videos)
    })


# Scheduler Endpoints
@router.get("/scheduler/status", summary="获取调度器状态")
async def get_scheduler_status():
    """获取调度器状态"""
    status = await scheduler_service.get_status()
    return success_response(data=status)


@router.post("/scheduler/tasks/{task_id}/run", summary="手动执行任务")
async def run_task(task_id: str):
    """手动执行指定任务"""
    success = await scheduler_service.run_task_now(task_id)
    if not success:
        raise NotFoundException(f"Task not found: {task_id}")
    return success_response(message="Task executed successfully")
