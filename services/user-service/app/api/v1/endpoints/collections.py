"""
Collection Endpoints
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import (
    get_db,
    success_response,
    ResponseModel,
    NotFoundException,
    page_response
)
from app.schemas.collection import (
    CollectionCreateRequest,
    CollectionUpdateRequest,
    CollectionBatchDeleteRequest,
    CollectionMoveRequest,
    CollectionResponse,
    CollectionListResponse,
    CollectionStatsResponse,
    FolderInfoResponse
)
from app.services.collection_service import collection_service
from app.api.v1.endpoints.users import get_current_user, get_current_user_id


router = APIRouter(prefix="/collections", tags=["收藏管理"])


@router.post(
    "",
    response_model=ResponseModel[CollectionResponse],
    status_code=status.HTTP_201_CREATED,
    summary="创建收藏"
)
async def create_collection(
    request: CollectionCreateRequest,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    创建一个新的收藏

    - **item_type**: 收藏类型 (video/script/insight/creator)
    - **item_id**: 收藏项ID
    - **notes**: 备注 (可选)
    - **tags**: 标签列表 (可选)
    - **folder**: 收藏夹名称 (可选)
    """
    collection = await collection_service.create_collection(
        db,
        user_id=user_id,
        item_type=request.item_type,
        item_id=request.item_id,
        notes=request.notes,
        tags=request.tags,
        folder=request.folder
    )
    return success_response(
        data=CollectionResponse.model_validate(collection),
        message="Collection created successfully"
    )


@router.delete(
    "/{collection_id}",
    response_model=ResponseModel,
    summary="删除收藏"
)
async def delete_collection(
    collection_id: int,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """删除指定的收藏"""
    await collection_service.delete_collection(db, user_id, collection_id)
    return success_response(message="Collection deleted successfully")


@router.post(
    "/batch-delete",
    response_model=ResponseModel,
    summary="批量删除收藏"
)
async def batch_delete_collections(
    request: CollectionBatchDeleteRequest,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """批量删除收藏"""
    deleted_count = await collection_service.delete_collections(db, user_id, request.ids)
    return success_response(
        message=f"Deleted {deleted_count} collections",
        data={"deleted_count": deleted_count}
    )


@router.put(
    "/{collection_id}",
    response_model=ResponseModel[CollectionResponse],
    summary="更新收藏"
)
async def update_collection(
    collection_id: int,
    request: CollectionUpdateRequest,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    更新收藏信息

    - **notes**: 备注 (可选)
    - **tags**: 标签列表 (可选)
    - **folder**: 收藏夹名称 (可选)
    - **is_favorite**: 是否标星 (可选)
    """
    collection = await collection_service.update_collection(
        db,
        user_id=user_id,
        collection_id=collection_id,
        notes=request.notes,
        tags=request.tags,
        folder=request.folder,
        is_favorite=request.is_favorite
    )
    return success_response(
        data=CollectionResponse.model_validate(collection),
        message="Collection updated successfully"
    )


@router.get(
    "",
    response_model=ResponseModel,
    summary="获取收藏列表"
)
async def get_collections(
    item_type: Optional[str] = None,
    folder: Optional[str] = None,
    is_favorite: Optional[bool] = None,
    page: int = 1,
    page_size: int = 20,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    获取用户的收藏列表

    - **item_type**: 按类型筛选 (可选)
    - **folder**: 按文件夹筛选 (可选)
    - **is_favorite**: 筛选标星收藏 (可选)
    - **page**: 页码 (默认1)
    - **page_size**: 每页数量 (默认20)
    """
    collections, total = await collection_service.get_collections(
        db,
        user_id=user_id,
        item_type=item_type,
        folder=folder,
        is_favorite=is_favorite,
        page=page,
        page_size=page_size
    )

    return success_response(
        data=page_response(
            items=[CollectionListResponse.model_validate(c) for c in collections],
            total=total,
            page=page,
            page_size=page_size
        )
    )


@router.post(
    "/{collection_id}/toggle-favorite",
    response_model=ResponseModel[CollectionResponse],
    summary="切换标星状态"
)
async def toggle_favorite(
    collection_id: int,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """切换收藏的标星状态"""
    collection = await collection_service.toggle_favorite(db, user_id, collection_id)
    return success_response(
        data=CollectionResponse.model_validate(collection),
        message="Favorite toggled successfully"
    )


@router.post(
    "/move",
    response_model=ResponseModel,
    summary="移动收藏到文件夹"
)
async def move_collections(
    request: CollectionMoveRequest,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """批量移动收藏到指定文件夹"""
    updated_count = await collection_service.move_collections(
        db, user_id, request.ids, request.folder
    )
    return success_response(
        message=f"Moved {updated_count} collections",
        data={"updated_count": updated_count}
    )


@router.get(
    "/check",
    response_model=ResponseModel,
    summary="检查是否已收藏"
)
async def check_collected(
    item_type: str,
    item_id: int,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """检查指定项目是否已收藏"""
    is_collected = await collection_service.check_collected(
        db, user_id, item_type, item_id
    )
    return success_response(
        data={"is_collected": is_collected}
    )


@router.get(
    "/stats",
    response_model=ResponseModel[CollectionStatsResponse],
    summary="获取收藏统计"
)
async def get_collection_stats(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """获取用户收藏统计信息"""
    stats = await collection_service.get_collection_stats(db, user_id)
    return success_response(
        data=CollectionStatsResponse(
            total=stats["total"],
            by_type=stats["by_type"],
            by_folder=[FolderInfoResponse(name=f["name"], count=f["count"]) for f in stats["by_folder"]],
            favorites=stats["favorites"]
        )
    )


@router.get(
    "/folders",
    response_model=ResponseModel,
    summary="获取收藏文件夹列表"
)
async def get_folders(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """获取用户的所有收藏文件夹"""
    folders = await collection_service.get_folders(db, user_id)
    return success_response(data=folders)
