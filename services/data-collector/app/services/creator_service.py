"""
Account Management Service - Using PostgreSQL Database
直接操作 Creator 表，主键为 (platform, creator_id)
"""
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from loguru import logger
from sqlalchemy import select, and_, true
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import db_manager, Creator
from app.schemas import Creator as CreatorSchema


class CreatorService:
    """创作者管理服务 - 直接操作 Creator 表"""

    def __init__(self):
        self._initialized = False

    async def _ensure_initialized(self):
        """确保数据库已初始化"""
        if not self._initialized:
            try:
                db_manager.init_db()
                await db_manager.create_tables()
                self._initialized = True
                logger.info("Creator service database initialized")
            except Exception as e:
                logger.error(f"Database initialization failed: {e}")
                self._initialized = False

    async def create_creator(
            self,
            name: str,
            platform: str,
            creator_id: str,
            main_category: str = "general",
            bio: str = None,
            avatar_url: str = None,
            url: str = None,
            follower_count: int = None,
            following_count: int = None,
            total_likes: int = None,
            video_count: int = None,
            avg_play_count: float = None,
            last_video_date: datetime = None,
            first_video_date: datetime = None,
            stats_updated_at: datetime = None,
    ) -> CreatorSchema:
        """
        创建新的监控创作者

        Args:
            name: 创作者名称
            platform: 平台 (douyin/bilibili/xiaohongshu/kuaishou)
            creator_id: 平台创作者ID
            main_category: 分类
            bio: 简介
            avatar_url: 头像URL
            url: 主页URL
            follower_count: 粉丝数
            video_count: 视频数
            avg_play_count: 平均播放量

        Returns:
            创作者 Schema
        """
        await self._ensure_initialized()

        if self._initialized:
            try:
                async with db_manager.get_session() as session:
                    # 检查创作者是否已存在
                    stmt = select(Creator).where(
                        and_(
                            Creator.platform == platform,
                            Creator.creator_id == creator_id
                        )
                    )
                    result = await session.execute(stmt)
                    existing = result.scalar_one_or_none()

                    if existing:
                        # 更新现有创作者为监控状态
                        existing.name = name
                        existing.main_category = main_category
                        if bio is not None:
                            existing.bio = bio
                        if avatar_url is not None:
                            existing.avatar_url = avatar_url
                        if url is not None:
                            existing.url = url
                        if follower_count is not None:
                            existing.follower_count = follower_count
                        if following_count is not None:
                            existing.following_count = following_count
                        if total_likes is not None:
                            existing.total_likes = total_likes
                        if video_count is not None:
                            existing.video_count = video_count
                        if avg_play_count is not None:
                            existing.avg_play_count = avg_play_count
                        if last_video_date is not None:
                            existing.last_video_date = last_video_date
                        if first_video_date is not None:
                            existing.first_video_date = first_video_date
                        if stats_updated_at is not None:
                            existing.stats_updated_at = stats_updated_at
                        existing.is_monitored = True
                        await session.commit()
                        await session.refresh(existing)
                        logger.info(f"Updated creator to monitored: {existing.name}")
                        return self._creator_to_schema(existing)

                    # 创建新创作者
                    creator = Creator(
                        platform=platform,
                        creator_id=creator_id,
                        name=name,
                        main_category=main_category,
                        bio=bio,
                        avatar_url=avatar_url,
                        url=url,
                        follower_count=follower_count or 0,
                        following_count=following_count or 0,
                        total_likes=total_likes or 0,
                        video_count=video_count or 0,
                        avg_play_count=avg_play_count or 0,
                        is_monitored=True,
                        stats_updated_at=stats_updated_at,
                    )
                    session.add(creator)
                    await session.commit()
                    await session.refresh(creator)
                    logger.info(f"Created monitored creator: {creator.name}")
                    return self._creator_to_schema(creator)
            except Exception as e:
                logger.error(f"Failed to create creator: {e}")

        return None

    async def get_creator(self, platform: str, creator_id: str) -> CreatorSchema:
        """获取创作者"""
        await self._ensure_initialized()

        if self._initialized:
            try:
                async with db_manager.get_session() as session:
                    stmt = select(Creator).where(
                        and_(
                            Creator.platform == platform,
                            Creator.creator_id == creator_id
                        )
                    )
                    result = await session.execute(stmt)
                    creator = result.scalar_one_or_none()
                    if creator:
                        return self._creator_to_schema(creator)
            except Exception as e:
                logger.error(f"Failed to get creator: {e}")

        return None

    async def list_creators(
            self,
            platform: Optional[str] = None,
            category: Optional[str] = None,
            is_monitored: Optional[bool] = True
    ) -> List[CreatorSchema]:
        """获取创作者列表"""
        await self._ensure_initialized()

        if self._initialized:
            try:
                async with db_manager.get_session() as session:
                    conditions = []
                    if is_monitored is not None:
                        conditions.append(Creator.is_monitored == is_monitored)
                    if platform:
                        conditions.append(Creator.platform == platform)
                    if category:
                        conditions.append(Creator.main_category == category)

                    stmt = select(Creator)
                    if conditions:
                        stmt = stmt.where(and_(*conditions))

                    result = await session.execute(stmt)
                    creators = result.scalars().all()
                    return [self._creator_to_schema(c) for c in creators]
            except Exception as e:
                logger.error(f"Failed to list creators: {e}")

        return []

    async def update_creator(
            self,
            platform: str,
            creator_id: str,
            name: Optional[str] = None,
            main_category: Optional[str] = None,
            is_monitored: Optional[bool] = None,
            bio: Optional[str] = None,
            avatar_url: Optional[str] = None,
            follower_count: Optional[int] = None,
            avg_play_count: Optional[int] = None
    ) -> CreatorSchema:
        """更新创作者信息"""
        await self._ensure_initialized()

        if self._initialized:
            try:
                async with db_manager.get_session() as session:
                    stmt = select(Creator).where(
                        and_(
                            Creator.platform == platform,
                            Creator.creator_id == creator_id
                        )
                    )
                    result = await session.execute(stmt)
                    creator = result.scalar_one_or_none()
                    if creator:
                        if name:
                            creator.name = name
                        if main_category:
                            creator.main_category = main_category
                        if is_monitored is not None:
                            creator.is_monitored = is_monitored
                        if bio is not None:
                            creator.bio = bio
                        if avatar_url is not None:
                            creator.avatar_url = avatar_url
                        if follower_count is not None:
                            creator.follower_count = follower_count
                        if avg_play_count is not None:
                            creator.avg_play_count = avg_play_count
                        creator.stats_updated_at = datetime.now()
                        await session.commit()
                        await session.refresh(creator)
                        return self._creator_to_schema(creator)
            except Exception as e:
                logger.error(f"Failed to update creator: {e}")

        return None

    async def delete_creator(self, platform: str, creator_id: str) -> bool:
        """删除创作者（设置 is_monitored 为 False）"""
        await self._ensure_initialized()
        print(f"参数{creator_id},{platform}")
        if self._initialized:
            try:
                async with db_manager.get_session() as session:
                    stmt = select(Creator).where(
                        and_(
                            Creator.platform == platform,
                            Creator.creator_id == creator_id
                        )
                    )
                    result = await session.execute(stmt)
                    creator = result.scalar_one_or_none()
                    if creator:
                        creator.is_monitored = False
                        await session.commit()
                        return True
            except Exception as e:
                logger.error(f"Failed to delete creator: {e}")

        return False

    async def get_monitored_creators(self, platform: Optional[str] = None) -> List[CreatorSchema]:
        """获取所有被监控的创作者"""
        return await self.list_creators(platform=platform, is_monitored=True)

    def _creator_to_schema(self, creator: Creator) -> CreatorSchema:
        """将 Creator 对象转换为 Schema"""
        return CreatorSchema(
            platform=creator.platform,
            creator_id=creator.creator_id,
            name=creator.name,
            url=creator.url or f"https://www.{creator.platform}.com/user/{creator.creator_id}",
            avatar_url=creator.avatar_url,
            category=creator.main_category or "general",
            description=creator.bio,
            follower_count=creator.follower_count or 0,
            following_count=creator.following_count or 0,
            total_likes=creator.total_likes or 0,
            video_count=creator.video_count or 0,
            avg_play_count=creator.avg_play_count or 0,
            status="active" if creator.is_monitored else "inactive",
            last_video_date=creator.last_video_date or None,
            first_video_date=creator.first_video_date or None,
            last_updated=creator.stats_updated_at.isoformat() if creator.stats_updated_at else None,
            created_at=creator.created_at if creator.created_at else datetime.now()
        )


# 全局服务实例
creator_service = CreatorService()
