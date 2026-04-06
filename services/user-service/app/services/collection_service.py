"""
Collection Service
"""
from typing import Optional, List, Union
from datetime import datetime
from sqlalchemy import select, and_, func, delete
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from app.models import Collection, Video, Creator, VideoInsight
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
        item_id: Union[int, str],
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
            item_id: 收藏项ID (支持数字或字符串如B站BV号)
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

        # 只有当item_id不为"0"或0时才检查重复（item_id=0表示创建文件夹）
        is_folder = (item_id == 0 or item_id == "0")
        if not is_folder:
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
            is_analysis=False
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
        item_type: Optional[str] = None,
        item_id: Optional[str] = None,
        notes: Optional[str] = None,
        tags: Optional[List[str]] = None,
        folder: Optional[str] = None,
        is_analysis: Optional[bool] = None
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
        if item_type is not None:
            collection.item_type = item_type
        if item_id is not None:
            collection.item_id = item_id
        if notes is not None:
            collection.notes = notes
        if tags is not None:
            collection.tags = tags
        if folder is not None:
            collection.folder = folder
        if is_analysis is not None:
            collection.is_analysis = is_analysis

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
        item_id: Optional[str] = None,
        folder: Optional[str] = None,
        is_analysis: Optional[bool] = None,
        page: int = 1,
        page_size: int = 20
    ) -> tuple[List[Collection], int]:
        """获取收藏列表"""
        # 构建查询条件
        conditions = [Collection.user_id == user_id]
        conditions.append(Collection.item_id != "0")
        if item_type:
            conditions.append(Collection.item_type == item_type)
        if item_id:
            conditions.append(Collection.item_id == item_id)
        if folder:
            conditions.append(Collection.folder == folder)
        if is_analysis is not None:
            conditions.append(Collection.is_analysis == is_analysis)

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

        # 为每个收藏项获取视频详情 - 从videos表查询
        from sqlalchemy import text
        for collection in collections:
            if collection.item_id:

                # 查询视频信息 - 使用videos表
                video_result = await db.execute(
                    text("""
                        SELECT v.id, v.platform, v.video_id, v.title, v.video_url as url, v.cover_image_url as cover_url,
                               v.creator_id,v.creator_name,
                               v.play_count, v.like_count, v.comment_count, v.share_count, v.collect_count,
                               v.publish_time, v.duration
                        FROM videos v
                        WHERE v.video_id = :video_id
                        LIMIT 1
                    """),
                    {"video_id": str(collection.item_id)}
                )
                video_row = video_result.fetchone()
                # 只有当 video_row 存在时才查询 VideoInsight
                if video_row is not None:
                    collection.video_info = {
                        "platform": video_row.platform,
                        "video_id": video_row.video_id,
                        "title": video_row.title or collection.notes,
                        "url": video_row.url,
                        "cover_url": video_row.cover_url,
                        "play_count": video_row.play_count or 0,
                        "like_count": video_row.like_count or 0,
                        "comment_count": video_row.comment_count or 0,
                        "share_count": video_row.share_count or 0,
                        "collect_count": video_row.collect_count or 0,
                        "publish_time": video_row.publish_time.isoformat() if video_row.publish_time else None,
                        "creator_id": video_row.creator_id,
                        "creator_name": video_row.creator_name,
                        "duration": video_row.duration
                    }
                else:
                    # 如果没找到视频，使用收藏时的notes作为标题
                    collection.video_info = {
                        "platform": "",
                        "video_id": str(collection.item_id),
                        "title": collection.notes or "未知视频",
                        "url": "",
                        "cover_url": "",
                        "play_count": 0,
                        "like_count": 0,
                        "comment_count": 0,
                        "share_count": 0,
                        "collect_count": 0,
                        "publish_time": None,
                        "creator_name": "",
                        "duration": 0
                    }
                    # 跳过 VideoInsight 查询
                    continue

                # 查询 VideoInsight
                insight_result = await db.execute(select(VideoInsight).where(VideoInsight.video_id == video_row.video_id))
                if insight_result.scalar_one_or_none():
                    collection.video_info["is_analysis"] = True


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

        collection.is_analysis = not collection.is_analysis
        await db.commit()
        await db.refresh(collection)

        logger.info(f"Collection favorite toggled: id={collection_id}")
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

        # 已分析数量
        analysis_result = await db.execute(
            select(func.count()).select_from(Collection).where(
                and_(
                    Collection.user_id == user_id,
                    Collection.is_analysis == True
                )
            )
        )
        analysis = analysis_result.scalar()

        return {
            "total": total,
            "by_type": by_type,
            "by_folder": by_folder,
            "analysis": analysis
        }

    @staticmethod
    async def get_folders(db: AsyncSession, user_id: int) -> List[dict]:
        """获取用户的所有文件夹及数量"""
        # 先获取所有有folder的记录（包括item_id='0'的文件夹本身）
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
        folder_names = [row[0] for row in result.fetchall() if row[0]]

        # 为每个文件夹统计实际收藏数量（排除item_id='0'的文件夹记录）
        folders = []
        for folder_name in folder_names:
            count_result = await db.execute(
                select(func.count(Collection.id))
                .where(
                    and_(
                        Collection.user_id == user_id,
                        Collection.folder == folder_name,
                        Collection.item_id != "0"
                    )
                )
            )
            count = count_result.scalar() or 0
            folders.append({"name": folder_name, "count": count})

        return folders


collection_service = CollectionService()
