"""
Content Collector Service - Using PostgreSQL Database
"""
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime
from loguru import logger
from sqlalchemy import select, and_

from app.core.database import db_manager, CollectedVideo
from app.services.account_service import Account, account_service


class VideoInfo:
    """Video information model (for API compatibility)"""

    def __init__(
        self,
        video_id: str,
        title: str,
        platform: str,
        account_id: str,
        account_name: str,
        url: str,
        cover_url: str = "",
        duration: int = 0,
        likes: int = 0,
        comments: int = 0,
        shares: int = 0,
        views: int = 0,
        publish_time: Optional[datetime] = None,
        collected_at: Optional[datetime] = None
    ):
        self.video_id = video_id
        self.title = title
        self.platform = platform
        self.account_id = account_id
        self.account_name = account_name
        self.url = url
        self.cover_url = cover_url
        self.duration = duration
        self.likes = likes
        self.comments = comments
        self.shares = shares
        self.views = views
        self.publish_time = publish_time
        self.collected_at = collected_at or datetime.now()

    @classmethod
    def from_db_model(cls, db_video: CollectedVideo) -> "VideoInfo":
        """Create from database model"""
        return cls(
            video_id=db_video.video_id,
            title=db_video.title,
            platform=db_video.platform,
            account_id=db_video.account_id,
            account_name=db_video.account_name or "",
            url=db_video.url or "",
            cover_url=db_video.cover_url or "",
            duration=db_video.duration or 0,
            likes=db_video.like_count or 0,
            comments=db_video.comment_count or 0,
            shares=db_video.share_count or 0,
            views=db_video.play_count or 0,
            publish_time=db_video.publish_time,
            collected_at=db_video.collected_at
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "video_id": self.video_id,
            "title": self.title,
            "platform": self.platform,
            "account_id": self.account_id,
            "account_name": self.account_name,
            "url": self.url,
            "cover_url": self.cover_url,
            "duration": self.duration,
            "likes": self.likes,
            "comments": self.comments,
            "shares": self.shares,
            "views": self.views,
            "publish_time": self.publish_time.isoformat() if self.publish_time else None,
            "collected_at": self.collected_at.isoformat() if self.collected_at else None
        }


class CollectorService:
    """Content collector service using database"""

    def __init__(self):
        self._initialized = False

    async def _ensure_initialized(self):
        """Ensure database is initialized"""
        if not self._initialized:
            try:
                db_manager.init_db()
                await db_manager.create_tables()
                self._initialized = True
                logger.info("Collector service database initialized")
            except Exception as e:
                logger.warning(f"Database initialization failed: {e}, using in-memory fallback")
                self._initialized = False

    async def collect_account(self, account: Account, limit: int = 50) -> List[VideoInfo]:
        """Collect videos from an account"""
        logger.info(f"Collecting videos from {account.name} ({account.platform})")

        collector = self._get_platform_collector(account.platform)
        if not collector:
            logger.warning(f"Unsupported platform: {account.platform}")
            return []

        try:
            videos = await collector(account, limit)
            logger.info(f"Collected {len(videos)} videos from {account.name}")

            # Save to database
            await self._save_videos(videos)

            # Update account collection time
            await account_service.update_collection_time(account.id)

            return videos
        except Exception as e:
            logger.error(f"Failed to collect from {account.name}: {e}")
            return []

    async def _get_platform_collector(self, platform: str):
        """Get platform collector function"""
        collectors = {
            "douyin": self._collect_douyin,
            "bilibili": self._collect_bilibili,
            "xiaohongshu": self._collect_xiaohongshu
        }
        return collectors.get(platform)

    async def _collect_douyin(self, account: Account, limit: int) -> List[VideoInfo]:
        """Collect from Douyin"""
        from app.adapters import get_platform_adapter

        try:
            adapter = get_platform_adapter("douyin")
            videos = await adapter.get_trending_videos(limit=limit)

            return [
                VideoInfo(
                    video_id=v.video_id,
                    title=v.title,
                    platform=v.platform,
                    account_id=account.account_id,
                    account_name=account.name,
                    url=v.url or f"https://v.douyin.com/{v.video_id}/",
                    cover_url=v.cover_url or "",
                    duration=v.duration or 0,
                    likes=v.metrics.like_count if v.metrics else 0,
                    comments=v.metrics.comment_count if v.metrics else 0,
                    shares=v.metrics.share_count if v.metrics else 0,
                    views=v.metrics.play_count if v.metrics else 0,
                    publish_time=v.publish_time
                )
                for v in videos
            ]
        except Exception as e:
            logger.error(f"Failed to collect from Douyin: {e}")
            return []

    async def _collect_bilibili(self, account: Account, limit: int) -> List[VideoInfo]:
        """Collect from Bilibili"""
        from app.adapters import get_platform_adapter

        try:
            adapter = get_platform_adapter("bilibili")

            if account.account_id:
                videos = await adapter.get_creator_videos(account.account_id, limit=limit)
            else:
                videos = await adapter.get_trending_videos(limit=limit)

            return [
                VideoInfo(
                    video_id=v.video_id,
                    title=v.title,
                    platform=v.platform,
                    account_id=account.account_id,
                    account_name=account.name,
                    url=v.url or f"https://www.bilibili.com/video/{v.video_id}/",
                    cover_url=v.cover_url or "",
                    duration=v.duration or 0,
                    likes=v.metrics.like_count if v.metrics else 0,
                    comments=v.metrics.danmaku_count if v.metrics else 0,
                    shares=v.metrics.share_count if v.metrics else 0,
                    views=v.metrics.play_count if v.metrics else 0,
                    publish_time=v.publish_time
                )
                for v in videos
            ]
        except Exception as e:
            logger.error(f"Failed to collect from Bilibili: {e}")
            return []

    async def _collect_xiaohongshu(self, account: Account, limit: int) -> List[VideoInfo]:
        """Collect from Xiaohongshu"""
        from app.adapters import get_platform_adapter

        try:
            adapter = get_platform_adapter("xiaohongshu")
            videos = await adapter.get_trending_videos(limit=limit)

            return [
                VideoInfo(
                    video_id=v.video_id,
                    title=v.title,
                    platform=v.platform,
                    account_id=account.account_id,
                    account_name=account.name,
                    url=v.url or f"https://www.xiaohongshu.com/discovery/item/{v.video_id}",
                    cover_url=v.cover_url or "",
                    duration=v.duration or 0,
                    likes=v.metrics.like_count if v.metrics else 0,
                    comments=v.metrics.comment_count if v.metrics else 0,
                    shares=v.metrics.share_count if v.metrics else 0,
                    views=v.metrics.play_count if v.metrics else 0,
                    publish_time=v.publish_time
                )
                for v in videos
            ]
        except Exception as e:
            logger.error(f"Failed to collect from Xiaohongshu: {e}")
            return []

    async def _save_videos(self, videos: List[VideoInfo]) -> int:
        """Save videos to database"""
        await self._ensure_initialized()

        if not self._initialized:
            return 0

        saved = 0
        try:
            async with db_manager.get_session() as session:
                for video in videos:
                    # Check if video already exists
                    stmt = select(CollectedVideo).where(
                        and_(
                            CollectedVideo.video_id == video.video_id,
                            CollectedVideo.platform == video.platform
                        )
                    )
                    result = await session.execute(stmt)
                    existing = result.scalar_one_or_none()

                    if not existing:
                        db_video = CollectedVideo(
                            id=f"vid_{uuid.uuid4().hex[:8]}",
                            video_id=video.video_id,
                            title=video.title,
                            platform=video.platform,
                            account_id=video.account_id,
                            account_name=video.account_name,
                            url=video.url,
                            cover_url=video.cover_url,
                            duration=video.duration,
                            play_count=video.views,
                            like_count=video.likes,
                            comment_count=video.comments,
                            share_count=video.shares,
                            publish_time=video.publish_time
                        )
                        session.add(db_video)
                        saved += 1

                await session.commit()
                logger.info(f"Saved {saved} new videos to database")
        except Exception as e:
            logger.error(f"Failed to save videos to database: {e}")

        return saved

    async def collect_all_active(self, platform: Optional[str] = None) -> Dict[str, List[VideoInfo]]:
        """Collect from all active accounts"""
        accounts = await account_service.get_active_accounts(platform)
        results = {}

        for account in accounts:
            videos = await self.collect_account(account)
            results[account.id] = videos

        return results

    async def get_video(self, video_id: str) -> Optional[VideoInfo]:
        """Get video by ID"""
        await self._ensure_initialized()

        if self._initialized:
            try:
                async with db_manager.get_session() as session:
                    stmt = select(CollectedVideo).where(CollectedVideo.video_id == video_id)
                    result = await session.execute(stmt)
                    db_video = result.scalar_one_or_none()
                    if db_video:
                        return VideoInfo.from_db_model(db_video)
            except Exception as e:
                logger.error(f"Failed to get video from database: {e}")

        return None

    async def get_videos_by_account(self, account_id: str) -> List[VideoInfo]:
        """Get all videos from an account"""
        await self._ensure_initialized()

        if self._initialized:
            try:
                async with db_manager.get_session() as session:
                    stmt = select(CollectedVideo).where(
                        CollectedVideo.account_id == account_id
                    )
                    result = await session.execute(stmt)
                    db_videos = result.scalars().all()
                    return [VideoInfo.from_db_model(v) for v in db_videos]
            except Exception as e:
                logger.error(f"Failed to get videos from database: {e}")

        return []

    async def get_videos_by_platform(self, platform: str) -> List[VideoInfo]:
        """Get all videos from a platform"""
        await self._ensure_initialized()

        if self._initialized:
            try:
                async with db_manager.get_session() as session:
                    stmt = select(CollectedVideo).where(
                        CollectedVideo.platform == platform
                    ).order_by(CollectedVideo.collected_at.desc()).limit(100)
                    result = await session.execute(stmt)
                    db_videos = result.scalars().all()
                    return [VideoInfo.from_db_model(v) for v in db_videos]
            except Exception as e:
                logger.error(f"Failed to get videos from database: {e}")

        return []

    async def search_videos(
        self,
        keyword: str,
        platform: Optional[str] = None,
        limit: int = 20
    ) -> List[VideoInfo]:
        """Search videos by keyword"""
        await self._ensure_initialized()

        if self._initialized:
            try:
                async with db_manager.get_session() as session:
                    stmt = select(CollectedVideo).where(
                        CollectedVideo.title.ilike(f"%{keyword}%")
                    )
                    if platform:
                        stmt = stmt.where(CollectedVideo.platform == platform)
                    stmt = stmt.order_by(CollectedVideo.collected_at.desc()).limit(limit)
                    result = await session.execute(stmt)
                    db_videos = result.scalars().all()
                    return [VideoInfo.from_db_model(v) for v in db_videos]
            except Exception as e:
                logger.error(f"Failed to search videos: {e}")

        return []

    async def get_all_videos(self, limit: int = 100) -> List[VideoInfo]:
        """Get all videos from database"""
        await self._ensure_initialized()

        if self._initialized:
            try:
                async with db_manager.get_session() as session:
                    stmt = select(CollectedVideo).order_by(
                        CollectedVideo.collected_at.desc()
                    ).limit(limit)
                    result = await session.execute(stmt)
                    db_videos = result.scalars().all()
                    return [VideoInfo.from_db_model(v) for v in db_videos]
            except Exception as e:
                logger.error(f"Failed to get videos from database: {e}")

        return []


collector_service = CollectorService()
