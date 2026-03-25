"""
Content Collector Service - Using PostgreSQL Database
"""
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime
from loguru import logger
from sqlalchemy import select, and_

from app.models import db_manager, Video, Creator
from app.schemas import Video as VideoSchema, Creator as CreatorSchema, VideoMetrics
from app.services.creator_service import creator_service
from sqlalchemy.orm import joinedload


class CollectorService:
    """Content collector service using database"""

    def __init__(self):
        self._initialized = False

    async def _ensure_initialized(self):
        """Ensure database is initialized"""
        if not self._initialized:
            try:
                # Import models so Base.metadata can see them
                db_manager.init_db()
                await db_manager.create_tables()
                self._initialized = True
                logger.info("Collector service database initialized")
            except Exception as e:
                logger.error(f"Database initialization failed: {e}")
                self._initialized = False

    def _parse_duration(self, duration: str) -> int:
        """Convert duration string (HH:MM:SS or MM:SS) to seconds"""
        if not duration:
            return 0
        try:
            parts = duration.split(':')
            if len(parts) == 2:
                return int(parts[0]) * 60 + int(parts[1])
            elif len(parts) == 3:
                return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
            return int(duration)
        except (ValueError, AttributeError):
            return 0

    async def collect_account(self, creator: CreatorSchema, limit: int = 50) -> List[VideoSchema]:
        """Collect videos from a creator

        Args:
            creator: 创作者字典，包含 name, platform, creator_id 等
            limit: 最大采集数量
        """
        platform = creator.platform
        name = creator.name
        creator_id = creator.creator_id

        logger.info(f"Collecting videos from {name} ({platform})")

        collector = await self._get_platform_collector(platform)
        if not collector:
            logger.warning(f"Unsupported platform: {platform}")
            return []

        try:
            # 传递创作者信息给采集器
            videos = await collector(creator, limit)
            logger.info(f"Collected {len(videos)} videos from {name}")

            # Save to database
            await self._save_videos(videos)

            # Update creator collection time
            creator_id_int = creator.id
            if creator_id_int:
                await creator_service.update_creator(creator_id_int, is_monitored=True)

            return videos
        except Exception as e:
            logger.error(f"Failed to collect from {name}: {e}")
            return []

    async def _get_platform_collector(self, platform: str):
        """Get platform collector function"""
        collectors = {
            "douyin": self._collect_douyin,
            "bilibili": self._collect_bilibili,
            "xiaohongshu": self._collect_xiaohongshu
        }
        return collectors.get(platform)

    async def _collect_douyin(self, creator: CreatorSchema, limit: int) -> List[VideoSchema]:
        """Collect from Douyin"""
        from app.adapters import get_platform_adapter

        try:
            adapter = get_platform_adapter("douyin")
            videos = await adapter.get_trending_videos(limit=limit)

            return videos
        except Exception as e:
            logger.error(f"Failed to collect from Douyin: {e}")
            return []

    async def _collect_bilibili(self, creator: CreatorSchema, limit: int) -> List[VideoSchema]:
        """Collect from Bilibili"""
        from app.adapters import get_platform_adapter

        try:
            adapter = get_platform_adapter("bilibili")

            if creator.creator_id:
                videos = await adapter.get_creator_videos(creator.creator_id, limit=limit)
            else:
                videos = await adapter.get_trending_videos(limit=limit)

            for v in videos:
                v.creator_id = creator.creator_id
                v.creator_name = creator.name
            return videos
        except Exception as e:
            logger.error(f"Failed to collect from Bilibili: {e}")
            return []

    async def _collect_xiaohongshu(self, creator: CreatorSchema, limit: int) -> List[VideoSchema]:
        """Collect from Xiaohongshu"""
        from app.adapters import get_platform_adapter

        try:
            adapter = get_platform_adapter("xiaohongshu")
            videos = await adapter.get_trending_videos(limit=limit)

            return [
                self._video_to_schema(v)
                for v in videos
            ]
        except Exception as e:
            logger.error(f"Failed to collect from Xiaohongshu: {e}")
            return []

    async def _save_videos(self, videos: List[VideoSchema]) -> int:
        """Save videos to database"""
        await self._ensure_initialized()

        if not self._initialized:
            return 0

        saved = 0
        try:
            async with db_manager.get_session() as session:
                for video in videos:
                    # Check if video already exists
                    stmt = select(Video).where(
                        and_(
                            Video.video_id == video.video_id,
                            Video.platform == video.platform
                        )
                    )
                    result = await session.execute(stmt)
                    existing = result.scalar_one_or_none()
                    if not existing:
                        db_video = Video(
                            video_id=video.video_id,
                            title=video.title,
                            platform=video.platform,
                            video_url=video.url,
                            description=video.description,
                            cover_image_url=video.cover_url,
                            duration=video.duration,
                            play_count=video.metrics.play_count,
                            like_count=video.metrics.like_count,
                            comment_count=video.metrics.comment_count,
                            share_count=video.metrics.share_count,
                            danmaku_count=video.metrics.danmaku_count,
                            coin_count=video.metrics.coin_count,
                            collect_count=video.metrics.collect_count,
                            creator_id=video.creator_id,
                            creator_name=video.creator_name,
                            publish_time=video.publish_time,
                            updated_at=video.collected_at
                        )
                        session.add(db_video)
                        saved += 1

                await session.commit()
                logger.info(f"Saved {saved} new videos to database")
        except Exception as e:
            logger.error(f"Failed to save videos to database: {e}")

        return saved

    async def collect_all_active(self, platform: Optional[str] = None) -> Dict[str, List[VideoSchema]]:
        """Collect from all active accounts"""
        accounts = await creator_service.get_active_accounts(platform)
        results = {}

        for account in accounts:
            videos = await self.collect_account(account)
            results[account.id] = videos

        return results

    async def get_video(self, video_id: str) -> VideoSchema:
        """Get video by ID"""
        await self._ensure_initialized()

        if self._initialized:
            try:
                async with db_manager.get_session() as session:
                    stmt = select(Video).where(Video.video_id == video_id)
                    result = await session.execute(stmt)
                    db_video = result.scalar_one_or_none()
                    if db_video:
                        return self._video_to_schema(db_video)
            except Exception as e:
                logger.error(f"Failed to get video from database: {e}")

        return None

    async def get_videos_by_account(self, creator_id: str) -> List[VideoSchema]:
        """Get all videos from an account"""
        await self._ensure_initialized()

        if self._initialized:
            try:
                async with db_manager.get_session() as session:
                    # Query videos by creator_id through creator lookup
                    stmt = select(Video).where(Video.creator_id == creator_id)
                    result = await session.execute(stmt)
                    db_videos = result.scalars().all()
                    return [self._video_to_schema(v) for v in db_videos]
            except Exception as e:
                logger.error(f"Failed to get videos from database: {e}")

        return []

    async def get_videos_by_platform(self, platform: str) -> List[VideoSchema]:
        """Get all videos from a platform"""
        await self._ensure_initialized()

        if self._initialized:
            try:
                async with db_manager.get_session() as session:
                    stmt = select(Video).where(
                        Video.platform == platform
                    ).order_by(Video.created_at.desc()).limit(100)
                    result = await session.execute(stmt)
                    db_videos = result.scalars().all()
                    return [self._video_to_schema(v) for v in db_videos]
            except Exception as e:
                logger.error(f"Failed to get videos from database: {e}")

        return []

    async def search_videos(
            self,
            keyword: str,
            platform: Optional[str] = None,
            limit: int = 20
    ) -> List[VideoSchema]:
        """Search videos by keyword"""
        await self._ensure_initialized()

        if self._initialized:
            try:
                async with db_manager.get_session() as session:
                    stmt = select(Video).where(
                        Video.title.ilike(f"%{keyword}%")
                    )
                    if platform:
                        stmt = stmt.where(Video.platform == platform)
                    stmt = stmt.order_by(Video.created_at.desc()).limit(limit)
                    result = await session.execute(stmt)
                    db_videos = result.scalars().all()
                    return [self._video_to_schema(v) for v in db_videos]
            except Exception as e:
                logger.error(f"Failed to search videos: {e}")

        return []

    async def get_all_videos(self, limit: int = 100) -> List[VideoSchema]:
        """Get all videos from database"""
        await self._ensure_initialized()

        if self._initialized:
            try:
                async with db_manager.get_session() as session:
                    stmt = select(Video).order_by(
                        Video.created_at.desc()
                    ).limit(limit)
                    result = await session.execute(stmt)
                    db_videos = result.scalars().all()
                    return [self._video_to_schema(v) for v in db_videos]
            except Exception as e:
                logger.error(f"Failed to get videos from database: {e}")

        return []

    async def save_videos(self, videos: List[VideoSchema], platform: str) -> int:
        """
        保存视频列表到数据库
        用于手动采集入库
        """
        # 转换为 VideoInfo 列表
        video_infos = []
        for v in videos:
            if hasattr(v, 'video_id'):
                video_infos.append(v)

        return await self._save_videos(video_infos)

    def _video_to_schema(self, video: Video) -> VideoSchema:

        metrics = VideoMetrics(
            video_id=video.video_id,
            platform=video.platform,
            play_count=video.play_count,
            comment_count=video.comment_count,
            share_count=video.share_count,
            like_count=video.like_count,
            danmaku_count=video.danmaku_count,
            coin_count=video.coin_count,
            collect_count=video.collect_count,
        )

        metrics.calculate_ratios()

        return VideoSchema(
            video_id=video.video_id,
            title=video.title,
            platform=video.platform,
            url=video.video_url,
            cover_url=video.cover_image_url,
            duration=video.duration,
            metrics=metrics,
            creator_id=video.creator_id,
            creator_name=video.creator_name,
            publish_time=video.publish_time,
            collected_at=video.updated_at
        )


collector_service = CollectorService()
