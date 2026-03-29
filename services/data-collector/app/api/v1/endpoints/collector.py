"""
Data Collector API Endpoints
"""
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from loguru import logger

from app.schemas import Video as VideoSchema
from app.services.creator_service import creator_service
from app.services.collector_service import collector_service
from app.services.scheduler_service import scheduler_service
from app.core.response import success_response
from app.core.exceptions import ValidationException, NotFoundException
from app.adapters import get_platform_adapter

router = APIRouter()


# Creator Request/Response Models
class CreateCreatorRequest(BaseModel):
    """创建创作者请求"""
    name: str = Field(..., description="创作者名称")
    platform: str = Field(..., description="平台: douyin/bilibili/xiaohongshu/kuaishou")
    creator_id: str = Field(..., description="平台账号ID")
    url: str = Field(..., description="账号URL")
    category: str = Field(default="general", description="分类")
    bio: Optional[str] = Field(None, description="简介")
    avatar_url: Optional[str] = Field(None, description="头像URL")


class UpdateCreatorRequest(BaseModel):
    """更新创作者请求"""
    name: Optional[str] = None
    category: Optional[str] = None
    status: Optional[str] = None


# Collector Request/Response Models
class CollectRequest(BaseModel):
    """Collect videos request"""
    creator_id: str = Field(..., description="Platform creator_id")
    platform: Optional[str] = Field(default="douyin", description="Platform: douyin/bilibili/xiaohongshu")
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


# Creator Endpoints
@router.post("/accounts", summary="创建监控创作者")
async def create_account(request: CreateCreatorRequest):
    """
    创建新的监控创作者

    - **name**: 创作者名称
    - **platform**: 平台 (douyin/bilibili/xiaohongshu/kuaishou)
    - **creator_id**: user_id
    - **url**: 账号主页URL
    - **category**: 分类
    - **bio**: 简介
    - **avatar_url**: 头像URL

    后端会根据 platform 和 creator_id 调用对应的 adapter 获取完整的创作者信息
    """

    # 尝试从平台获取创作者详细信息
    adapter_creator = None
    try:
        adapter = get_platform_adapter(request.platform)
        # 调用 adapter 获取创作者信息
        adapter_creator = await adapter.get_creator_info(request.creator_id)
        if adapter_creator:
            logger.info(f"获取到创作者信息: {adapter_creator}")
    except Exception as e:
        logger.warning(f"获取创作者信息失败，使用前端提供的信息: {e}")

    kwargs = {
        'name': adapter_creator.name if adapter_creator else request.name,
        'platform': request.platform,
        'creator_id': request.creator_id,
        'main_category': request.category,
        'bio': adapter_creator.description if adapter_creator else request.bio,
        'avatar_url': adapter_creator.avatar_url if adapter_creator else request.avatar_url,
        'url': request.url,
        'follower_count': adapter_creator.follower_count if adapter_creator else None,
        'following_count': adapter_creator.following_count if adapter_creator else None,
        'total_likes': adapter_creator.total_likes if adapter_creator else None,
        'video_count': adapter_creator.video_count if adapter_creator else None,
        'avg_play_count': adapter_creator.avg_play_count if adapter_creator else None,
        'last_video_date': adapter_creator.last_video_date if adapter_creator else None,
        'first_video_date': adapter_creator.first_video_date if adapter_creator else None,
        'stats_updated_at': adapter_creator.last_updated if adapter_creator else None,
    }
    # 使用 adapter 返回的信息填充字段
    creator = await creator_service.create_creator(**kwargs)
    if not creator:
        raise ValidationException("Failed to create creator")
    return success_response(data=creator)


@router.get("/accounts", summary="获取创作者列表")
async def list_accounts(
        platform: Optional[str] = None,
        category: Optional[str] = None,
        status: Optional[str] = None
):
    """
    获取创作者列表

    - **platform**: 按平台筛选
    - **category**: 按分类筛选
    - **status**: 按状态筛选 (active/inactive)
    """
    # status 转换为 is_monitored
    is_monitored = None
    if status == "active":
        is_monitored = True
    elif status == "inactive":
        is_monitored = False

    creators = await creator_service.list_creators(platform=platform, category=category, is_monitored=is_monitored)
    # 转换 CreatorSchema 为 dict
    accounts = []
    for c in creators:
        accounts.append({
            "platform": c.platform,
            "creator_id": c.creator_id,
            "name": c.name,
            "url": c.url,
            "category": c.category,
            "status": c.status,
            "description": c.description,
            "avatar_url": c.avatar_url,
            "follower_count": c.follower_count,
            "video_count": c.video_count,
            "avg_play_count": c.avg_play_count,
        })
    return success_response(data={
        "accounts": accounts,
        "total": len(accounts)
    })


@router.get("/accounts/detail", summary="获取创作者详情")
async def get_account(platform: str, creator_id: str):
    """获取指定创作者详情"""
    creator = await creator_service.get_creator(platform, creator_id)
    if not creator:
        raise NotFoundException(f"Creator not found: {platform}/{creator_id}")
    return success_response(data={
        "platform": creator.platform,
        "creator_id": creator.creator_id,
        "name": creator.name,
        "url": creator.url,
        "category": creator.category,
        "status": creator.status,
        "description": creator.description,
        "avatar_url": creator.avatar_url,
        "follower_count": creator.follower_count,
        "video_count": creator.video_count,
        "avg_play_count": creator.avg_play_count,
    })


@router.put("/accounts/detail", summary="更新创作者")
async def update_account(platform: str, creator_id: str, request: UpdateCreatorRequest):
    """更新创作者信息"""
    creator = await creator_service.update_creator(
        platform=platform,
        creator_id=creator_id,
        name=request.name,
        main_category=request.category,
        is_monitored=True if request.status == "active" else (False if request.status == "inactive" else None)
    )
    if not creator:
        raise NotFoundException(f"Creator not found: {platform}/{creator_id}")
    return success_response(data={
        "platform": creator.platform,
        "creator_id": creator.creator_id,
        "name": creator.name,
        "url": creator.url,
        "category": creator.category,
        "status": creator.status,
    })


@router.delete("/accounts/detail", summary="删除创作者")
async def delete_account(platform: str, creator_id: str):
    """删除创作者（取消监控）"""
    success = await creator_service.delete_creator(platform, creator_id)
    if not success:
        raise NotFoundException(f"Creator not found: {platform}/{creator_id}")
    return success_response(message="Creator deleted successfully")


# Collector Endpoints
@router.post("/collect", summary="采集指定账号")
async def collect_account(request: CollectRequest):
    """
    采集指定账号的视频

    - **creator_id**: creator_id
    - **platform**: 平台
    - **limit**: 最大采集数量
    """
    platform = request.platform or "douyin"
    creator_id = request.creator_id

    creator = await creator_service.get_creator(platform, creator_id)
    if not creator:
        raise NotFoundException(f"Creator not found: {platform}/{creator_id}")

    # 传入 CreatorSchema 给 collector_service
    videos = await collector_service.collect_account(creator, request.limit)
    return success_response(data={
        "account": {
            "platform": creator.platform,
            "creator_id": creator.creator_id,
            "name": creator.name
        },
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
    # 获取所有被监控的创作者
    creators = await creator_service.get_monitored_creators(platform=request.platform)

    all_videos = []
    for creator in creators:
        videos = await collector_service.collect_account(creator, request.limit)
        all_videos.extend(videos)

    return success_response(data={
        "accounts_collected": len(creators),
        "videos": [v.to_dict() for v in all_videos],
        "total": len(all_videos)
    })


@router.get("/videos/viral", summary="获取爆款视频列表")
async def get_viral_videos(
    limit: int = Query(3, ge=1, le=20, description="返回数量"),
    min_play_count: int = Query(100000, ge=0, description="最小播放量阈值")
):
    """
    获取爆款视频列表，用于首页展示
    - limit: 返回数量，默认3条
    - min_play_count: 最小播放量阈值，默认10万
    """
    from app.models import db_manager, Video

    db_manager.init_db()
    async with db_manager.get_session() as session:
        from sqlalchemy import select, desc
        stmt = (
            select(Video)
            .where(Video.play_count >= min_play_count)
            .order_by(desc(Video.play_count))
            .limit(limit)
        )
        result = await session.execute(stmt)
        videos = list(result.scalars().all())

    videos_list = []
    for v in videos:
        videos_list.append({
            "id": v.id,
            "video_id": v.video_id,
            "video_url": v.video_url,
            "title": v.title,
            "platform": v.platform,
            "cover_url": v.cover_image_url,
            "play_count": v.play_count,
            "like_count": v.like_count,
            "comment_count": v.comment_count,
            "share_count": v.share_count,
            "creator_name": v.creator_name,
            "publish_time": v.publish_time.isoformat() if v.publish_time else None
        })

    return success_response(data={
        "videos": videos_list,
        "total": len(videos_list)
    })


@router.get("/videos", summary="获取视频列表")
async def list_videos(
        platform: Optional[str] = None,
        creator_id: Optional[str] = None,
        limit: int = 50
):
    """获取已采集的视频列表"""
    if creator_id:
        videos = await collector_service.get_videos_by_account(creator_id)
    elif platform:
        videos = await collector_service.get_videos_by_platform(platform)
    else:
        videos = await collector_service.get_all_videos(limit)

    videos = videos[:limit]
    videos_list = []
    for v in videos:
        video_dict = v.to_dict()
        video_dict.update(v.metrics.__dict__.copy())
        videos_list.append(video_dict)
    return success_response(data={
        "videos": videos_list,
        "total": len(videos)
    })

@router.get("/videos/{video_id}/save", summary="手动保存视频到数据库")
async def save_video_to_db(video_id: str, platform: str):
    """手动保存指定视频到数据库"""

    try:
        adapter = get_platform_adapter(platform)
        video = await adapter.get_video_detail(video_id)

        if not video:
            raise NotFoundException(f"Video not found: {video_id}")

        saved_count = await collector_service.save_videos([video], platform)

        return success_response(data={
            "video": video.to_dict(),
            "saved": saved_count
        })

    except Exception as e:
        logger.error(f"Save video failed: {e}")
        raise ValidationException(f"保存视频失败: {str(e)}")

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


# Manual Collection Endpoints - 手动采集入库
class ManualCollectRequest(BaseModel):
    """手动采集请求"""
    platform: str = Field(..., description="平台: douyin/bilibili/xiaohongshu")
    collect_type: str = Field(..., description="采集类型: trending/region/creator/search")
    params: dict = Field(default_factory=dict, description="采集参数")


@router.post("/manual/collect", summary="手动采集并入库")
async def manual_collect(request: ManualCollectRequest):
    """
    手动采集数据并入库

    - **platform**: 平台 (douyin/bilibili/xiaohongshu)
    - **collect_type**: 采集类型
      - trending: 热门/排行榜
      - region: 分区视频(B站)
      - creator: 创作者视频
      - search: 关键词搜索
    - **params**: 参数
      - trending: {"limit": 50}
      - region: {"rid": 1} (B站分区ID)
      - creator: {"creator_id": "xxx"}
      - search: {"keyword": "xxx", "limit": 20}
    """

    try:
        adapter = get_platform_adapter(request.platform)
        videos = []
        creator = None

        if request.collect_type == "trending":
            # 获取热门/排行榜
            limit = request.params.get("limit", 50)
            videos = await adapter.get_trending_videos(limit=limit)
            logger.info(f"采集热门视频: {len(videos)}")

        elif request.collect_type == "region":
            # 按分区获取 (B站)
            rid = request.params.get("rid", 1)
            pn = request.params.get("pn", 1)
            videos = await adapter.get_region_videos(rid=rid, pn=pn)
            logger.info(f"采集分区视频: {len(videos)}")

        elif request.collect_type == "creator":
            # 获取创作者视频
            creator_id = request.params.get("creator_id")
            limit = request.params.get("limit", 50)
            videos = await adapter.get_creator_videos(creator_id, limit=limit)
            logger.info(f"采集创作者视频: {len(videos)}")

        elif request.collect_type == "search":
            # 关键词搜索
            keyword = request.params.get("keyword")
            limit = request.params.get("limit", 20)
            videos = await adapter.search_videos(keyword, limit=limit)
            logger.info(f"搜索视频: {len(videos)}")

        else:
            raise ValidationException(f"Unknown collect_type: {request.collect_type}")

        # 保存到数据库
        saved_count = 0
        if videos:
            saved_count = await collector_service.save_videos(videos, request.platform)

        return success_response(data={
            "platform": request.platform,
            "collect_type": request.collect_type,
            "fetched": len(videos),
            "saved": saved_count,
            "videos": [v.to_dict() for v in videos[:10]]  # 返回前10条
        })

    except Exception as e:
        logger.error(f"Manual collect failed: {e}")
        raise ValidationException(f"采集失败: {str(e)}")


@router.get("/video/save", summary="保存单个视频")
async def video_save(video_id: str):
    videos = []
    adapter = get_platform_adapter("bilibili")
    video = await adapter.get_video_detail(video_id=video_id)
    videos.append(video)
    saved_count = await collector_service.save_videos(videos, video.platform)
    return saved_count


@router.get("/bilibili/regions", summary="获取B站分区列表")
async def get_bilibili_regions():
    """获取B站所有分区列表"""

    try:
        adapter = get_platform_adapter("bilibili")
        regions = await adapter.get_region_list()
        return success_response(data={"regions": regions})
    except Exception as e:
        logger.error(f"Get regions failed: {e}")
        # 返回默认分区
        return success_response(data={
            "regions": [
                {"id": 1, "name": "动画"},
                {"id": 3, "name": "音乐"},
                {"id": 4, "name": "游戏"},
                {"id": 5, "name": "娱乐"},
                {"id": 11, "name": "电视剧"},
                {"id": 13, "name": "番剧"},
                {"id": 23, "name": "电影"},
                {"id": 36, "name": "科技"},
                {"id": 119, "name": "鬼畜"},
                {"id": 129, "name": "舞蹈"},
                {"id": 155, "name": "时尚"},
                {"id": 160, "name": "生活"},
                {"id": 181, "name": "影视"},
                {"id": 188, "name": "数码"},
                {"id": 211, "name": "美食"},
                {"id": 217, "name": "动物圈"},
                {"id": 234, "name": "汽车"},
                {"id": 223, "name": "金句"}
            ]
        })


@router.get("/bilibili/creator/{creator_id}", summary="获取B站UP主信息")
async def get_bilibili_creator(creator_id: str):
    """获取B站UP主详细信息"""
    from app.adapters import get_platform_adapter

    try:
        adapter = get_platform_adapter("bilibili")
        creator = await adapter.get_creator_info(creator_id)
        if not creator:
            raise NotFoundException(f"Creator not found: {creator_id}")
        return success_response(data=creator.to_dict())
    except Exception as e:
        logger.error(f"Get creator failed: {e}")
        raise ValidationException(f"获取创作者信息失败: {str(e)}")


@router.post("/bilibili/creator/collect", summary="采集UP主视频并入库")
async def collect_bilibili_creator(creator_id: str, limit: int = 50):
    """采集B站UP主视频并入库"""

    try:
        adapter = get_platform_adapter("bilibili")

        # 获取UP主信息
        creator = await adapter.get_creator_info(creator_id)
        if not creator:
            raise NotFoundException(f"Creator not found: {creator_id}")

        # 获取UP主视频
        videos = await adapter.get_creator_videos(creator_id, limit=limit)

        # 保存到数据库
        saved_count = 0
        if videos:
            saved_count = await collector_service.save_videos(videos, "bilibili")

        return success_response(data={
            "creator": creator.to_dict(),
            "fetched": len(videos),
            "saved": saved_count,
            "videos": [v.to_dict() for v in videos[:10]]
        })

    except Exception as e:
        logger.error(f"Collect creator failed: {e}")
        raise ValidationException(f"采集失败: {str(e)}")

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


# Image Proxy - 解决B站图片403问题
@router.get("/proxy/image", summary="图片代理")
async def proxy_image(url: str):
    """
    图片代理接口，解决B站图片403问题
    - url: 原始图片URL
    """
    import httpx
    from fastapi.responses import Response

    if not url:
        raise ValidationException("URL is required")

    try:
        headers = {
            "Referer": "https://www.bilibili.com",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, headers=headers)

            if response.status_code != 200:
                raise HTTPException(status_code=response.status_code, detail="Failed to fetch image")

            content_type = response.headers.get("content-type", "image/jpeg")
            return Response(
                content=response.content,
                media_type=content_type,
                headers={
                    "Cache-Control": "public, max-age=86400",
                    "Access-Control-Allow-Origin": "*"
                }
            )
    except httpx.RequestError as e:
        logger.error(f"Failed to proxy image: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch image")
