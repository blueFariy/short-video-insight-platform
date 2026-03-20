"""
Content Collector Service
"""
import asyncio
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
from loguru import logger

from app.services.account_service import Account, account_service


class VideoInfo:
    """Video information model"""

    def __init__(
        self,
        video_id: str,
        title: str,
        platform: str,
        account_id: str,
        account_name: str,
        url: str,
        cover_url: str,
        duration: int,
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
    """Content collector service"""

    def __init__(self):
        self.collected_videos: Dict[str, VideoInfo] = {}
        self.platform_collectors = {
            "douyin": self._collect_douyin,
            "bilibili": self._collect_bilibili,
            "xiaohongshu": self._collect_xiaohongshu,
            "kuaishou": self._collect_kuaishou
        }

    async def collect_account(self, account: Account, limit: int = 50) -> List[VideoInfo]:
        """
        Collect videos from an account

        Args:
            account: Account to collect from
            limit: Maximum videos to collect

        Returns:
            List of collected videos
        """
        logger.info(f"Collecting videos from {account.name} ({account.platform})")

        collector = self.platform_collectors.get(account.platform)
        if not collector:
            logger.warning(f"Unsupported platform: {account.platform}")
            return []

        try:
            videos = await collector(account, limit)
            logger.info(f"Collected {len(videos)} videos from {account.name}")

            # Update account collection time
            await account_service.update_collection_time(account.id)

            return videos
        except Exception as e:
            logger.error(f"Failed to collect from {account.name}: {e}")
            return []

    async def collect_all_active(self, platform: Optional[str] = None) -> Dict[str, List[VideoInfo]]:
        """
        Collect from all active accounts

        Args:
            platform: Filter by platform

        Returns:
            Dictionary of account_id -> videos
        """
        accounts = await account_service.get_active_accounts(platform)
        results = {}

        for account in accounts:
            videos = await self.collect_account(account)
            results[account.id] = videos

        return results

    async def _collect_douyin(self, account: Account, limit: int) -> List[VideoInfo]:
        """Collect from Douyin - 使用适配器爬取真实数据"""
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
        """Collect from Bilibili - 使用适配器爬取真实数据"""
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
        """Collect from Xiaohongshu - 使用适配器爬取真实数据"""
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

    async def _collect_kuaishou(self, account: Account, limit: int) -> List[VideoInfo]:
        """Collect from Kuaishou - 暂不支持真实爬取"""
        logger.warning("Kuaishou scraping not implemented yet, returning empty list")
        return []

    async def get_video(self, video_id: str) -> Optional[VideoInfo]:
        """Get video by ID"""
        return self.collected_videos.get(video_id)

    async def get_videos_by_account(self, account_id: str) -> List[VideoInfo]:
        """Get all videos from an account"""
        return [v for v in self.collected_videos.values() if v.account_id == account_id]

    async def get_videos_by_platform(self, platform: str) -> List[VideoInfo]:
        """Get all videos from a platform"""
        return [v for v in self.collected_videos.values() if v.platform == platform]

    async def search_videos(
        self,
        keyword: str,
        platform: Optional[str] = None,
        limit: int = 20
    ) -> List[VideoInfo]:
        """Search videos by keyword"""
        results = []
        for video in self.collected_videos.values():
            if keyword.lower() in video.title.lower():
                if platform is None or video.platform == platform:
                    results.append(video)

        return results[:limit]


collector_service = CollectorService()
