"""
Collection Service
"""
from typing import Optional, List
from datetime import datetime
from sqlalchemy import select, and_, func, delete
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from app.models import Collection, Video, Creator
from app.core.exceptions import NotFoundException, ConflictException


# 有效的收藏类型
VALID_ITEM_TYPES = ["video", "script", "insight", "creator"]


class CollectionService:
    """收藏服务"""

    @staticmethod
    async def create_collection(
        db: AsyncSession,
        user_id: int,
        item_type: str,
        item_id: int,
        notes: Optional[str] = None,
        tags: Optional[List[str]] = None,
        folder: Optional[str] = None
    ) -> Collection:
        """
        创建收藏

        Args:
            db: 数据库会话
            user_id: 用户ID
            item_type: 收藏类型
            item_id: 收藏项ID
            notes: 备注
            tags: 标签
            folder: 文件夹

        Returns:
            收藏对象

        Raises:
            ValidationException: 无效的收藏类型
            ConflictException: 已收藏
        """
        # 验证收藏类型
        if item_type not in VALID_ITEM_TYPES:
            raise ConflictException(message=f"Invalid item type: {item_type}")

        # 检查是否已收藏
        result = await db.execute(
            select(Collection).where(
                and_(
                    Collection.user_id == user_id,
                    Collection.item_type == item_type,
                    Collection.item_id == item_id
                )
            )
        )
        if result.scalar_one_or_none():
            raise ConflictException(message="Item already collected")

        # 创建收藏
        collection = Collection(
            user_id=user_id,
            item_type=item_type,
            item_id=item_id,
            notes=notes,
            tags=tags,
            folder=folder,
            is_favorite=False
        )
        db.add(collection)
        await db.commit()
        await db.refresh(collection)

        logger.info(f"Collection created: user={user_id}, type={item_type}, id={item_id}")
        return collection

    @staticmethod
    async def delete_collection(db: AsyncSession, user_id: int, collection_id: int) -> bool:
        """删除收藏"""
        result = await db.execute(
            select(Collection).where(
                and_(
                    Collection.id == collection_id,
                    Collection.user_id == user_id
                )
            )
        )
        collection = result.scalar_one_or_none()

        if not collection:
            raise NotFoundException(message="Collection not found")

        await db.delete(collection)
        await db.commit()

        logger.info(f"Collection deleted: id={collection_id}")
        return True

    @staticmethod
    async def delete_collections(db: AsyncSession, user_id: int, collection_ids: List[int]) -> int:
        """批量删除收藏"""
        result = await db.execute(
            delete(Collection).where(
                and_(
                    Collection.id.in_(collection_ids),
                    Collection.user_id == user_id
                )
            )
        )
        await db.commit()

        deleted_count = result.rowcount
        logger.info(f"Collections deleted: count={deleted_count}")
        return deleted_count

    @staticmethod
    async def update_collection(
        db: AsyncSession,
        user_id: int,
        collection_id: int,
        notes: Optional[str] = None,
        tags: Optional[List[str]] = None,
        folder: Optional[str] = None,
        is_favorite: Optional[bool] = None
    ) -> Collection:
        """更新收藏"""
        result = await db.execute(
            select(Collection).where(
                and_(
                    Collection.id == collection_id,
                    Collection.user_id == user_id
                )
            )
        )
        collection = result.scalar_one_or_none()

        if not collection:
            raise NotFoundException(message="Collection not found")

        # 更新字段
        if notes is not None:
            collection.notes = notes
        if tags is not None:
            collection.tags = tags
        if folder is not None:
            collection.folder = folder
        if is_favorite is not None:
            collection.is_favorite = is_favorite

        await db.commit()
        await db.refresh(collection)

        logger.info(f"Collection updated: id={collection_id}")
        return collection

    @staticmethod
    async def get_collection(
        db: AsyncSession,
        user_id: int,
        collection_id: int
    ) -> Optional[Collection]:
        """获取单个收藏"""
        result = await db.execute(
            select(Collection).where(
                and_(
                    Collection.id == collection_id,
                    Collection.user_id == user_id
                )
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_collections(
        db: AsyncSession,
        user_id: int,
        item_type: Optional[str] = None,
        folder: Optional[str] = None,
        is_favorite: Optional[bool] = None,
        page: int = 1,
        page_size: int = 20
    ) -> tuple[List[Collection], int]:
        """获取收藏列表"""
        # 构建查询条件
        conditions = [Collection.user_id == user_id]

        if item_type:
            conditions.append(Collection.item_type == item_type)
        if folder:
            conditions.append(Collection.folder == folder)
        if is_favorite is not None:
            conditions.append(Collection.is_favorite == is_favorite)

        # 查询总数
        count_result = await db.execute(
            select(func.count()).select_from(Collection).where(and_(*conditions))
        )
        total = count_result.scalar()

        # 查询列表
        offset = (page - 1) * page_size
        result = await db.execute(
            select(Collection)
            .where(and_(*conditions))
            .order_by(Collection.created_at.desc())
            .offset(offset)
            .limit(page_size)
        )
        collections = result.scalars().all()

        return list(collections), total

    @staticmethod
    async def move_collections(
        db: AsyncSession,
        user_id: int,
        collection_ids: List[int],
        folder: str
    ) -> int:
        """移动收藏到文件夹"""
        result = await db.execute(
            update(Collection).where(
                and_(
                    Collection.id.in_(collection_ids),
                    Collection.user_id == user_id
                )
            ).values(folder=folder)
        )
        await db.commit()

        updated_count = result.rowcount
        logger.info(f"Collections moved to folder '{folder}': count={updated_count}")
        return updated_count

    @staticmethod
    async def toggle_favorite(
        db: AsyncSession,
        user_id: int,
        collection_id: int
    ) -> Collection:
        """切换收藏标星状态"""
        result = await db.execute(
            select(Collection).where(
                and_(
                    Collection.id == collection_id,
                    Collection.user_id == user_id
                )
            )
        )
        collection = result.scalar_one_or_none()

        if not collection:
            raise NotFoundException(message="Collection not found")

        collection.is_favorite = not collection.is_favorite
        await db.commit()
        await db.refresh(collection)

        logger.info(f"Collection favorite toggled: id={collection_id}, is_favorite={collection.is_favorite}")
        return collection

    @staticmethod
    async def check_collected(
        db: AsyncSession,
        user_id: int,
        item_type: str,
        item_id: int
    ) -> bool:
        """检查是否已收藏"""
        result = await db.execute(
            select(Collection).where(
                and_(
                    Collection.user_id == user_id,
                    Collection.item_type == item_type,
                    Collection.item_id == item_id
                )
            )
        )
        return result.scalar_one_or_none() is not None

    @staticmethod
    async def get_collection_stats(db: AsyncSession, user_id: int) -> dict:
        """获取收藏统计"""
        # 统计总数
        total_result = await db.execute(
            select(func.count()).select_from(Collection).where(Collection.user_id == user_id)
        )
        total = total_result.scalar()

        # 按类型统计
        type_result = await db.execute(
            select(Collection.item_type, func.count())
            .where(Collection.user_id == user_id)
            .group_by(Collection.item_type)
        )
        by_type = {row[0]: row[1] for row in type_result.fetchall()}

        # 按文件夹统计
        folder_result = await db.execute(
            select(Collection.folder, func.count())
            .where(
                and_(
                    Collection.user_id == user_id,
                    Collection.folder.isnot(None)
                )
            )
            .group_by(Collection.folder)
        )
        by_folder = [
            {"name": row[0] or "未分类", "count": row[1]}
            for row in folder_result.fetchall()
        ]

        # 标星数量
        fav_result = await db.execute(
            select(func.count()).select_from(Collection).where(
                and_(
                    Collection.user_id == user_id,
                    Collection.is_favorite == True
                )
            )
        )
        favorites = fav_result.scalar()

        return {
            "total": total,
            "by_type": by_type,
            "by_folder": by_folder,
            "favorites": favorites
        }

    @staticmethod
    async def get_folders(db: AsyncSession, user_id: int) -> List[str]:
        """获取用户的所有文件夹"""
        result = await db.execute(
            select(Collection.folder)
            .where(
                and_(
                    Collection.user_id == user_id,
                    Collection.folder.isnot(None)
                )
            )
            .group_by(Collection.folder)
        )
        folders = [row[0] for row in result.fetchall() if row[0]]
        return folders


collection_service = CollectionService()
