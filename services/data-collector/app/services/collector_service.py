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
        """Collect from Douyin"""
        # In production, this would use yt-dlp or Douyin API
        # For demo, return simulated data
        videos = []
        for i in range(min(5, limit)):
            video = VideoInfo(
                video_id=f"dy_{account.account_id}_{i}",
                title=f"抖音视频标题 {i+1} - {account.name}",
                platform="douyin",
                account_id=account.account_id,
                account_name=account.name,
                url=f"https://v.douyin.com/xxx{i}/",
                cover_url=f"https://picsum.photos/400/300?random={i}",
                duration=60 + i * 30,
                likes=1000 + i * 500,
                comments=50 + i * 20,
                shares=10 + i * 5,
                views=10000 + i * 2000,
                publish_time=datetime.now()
            )
            videos.append(video)
            self.collected_videos[video.video_id] = video

        return videos

    async def _collect_bilibili(self, account: Account, limit: int) -> List[VideoInfo]:
        """Collect from Bilibili"""
        videos = []
        for i in range(min(5, limit)):
            video = VideoInfo(
                video_id=f"bilibili_{account.account_id}_{i}",
                title=f"B站视频标题 {i+1} - {account.name}",
                platform="bilibili",
                account_id=account.account_id,
                account_name=account.name,
                url=f"https://www.bilibili.com/video/BV{i+1:04d}/",
                cover_url=f"https://picsum.photos/400/300?random={i+10}",
                duration=300 + i * 60,
                likes=5000 + i * 1000,
                comments=200 + i * 50,
                shares=100 + i * 20,
                views=50000 + i * 10000,
                publish_time=datetime.now()
            )
            videos.append(video)
            self.collected_videos[video.video_id] = video

        return videos

    async def _collect_xiaohongshu(self, account: Account, limit: int) -> List[VideoInfo]:
        """Collect from Xiaohongshu"""
        videos = []
        for i in range(min(5, limit)):
            video = VideoInfo(
                video_id=f"xhs_{account.account_id}_{i}",
                title=f"小红书笔记 {i+1} - {account.name}",
                platform="xiaohongshu",
                account_id=account.account_id,
                account_name=account.name,
                url=f"https://www.xiaohongshu.com/discovery/item/{i+1}",
                cover_url=f"https://picsum.photos/400/300?random={i+20}",
                duration=30 + i * 15,
                likes=2000 + i * 500,
                comments=100 + i * 30,
                shares=50 + i * 10,
                views=20000 + i * 5000,
                publish_time=datetime.now()
            )
            videos.append(video)
            self.collected_videos[video.video_id] = video

        return videos

    async def _collect_kuaishou(self, account: Account, limit: int) -> List[VideoInfo]:
        """Collect from Kuaishou"""
        videos = []
        for i in range(min(5, limit)):
            video = VideoInfo(
                video_id=f"ks_{account.account_id}_{i}",
                title=f"快手视频 {i+1} - {account.name}",
                platform="kuaishou",
                account_id=account.account_id,
                account_name=account.name,
                url=f"https://www.kuaishou.com/short-video/{i+1}",
                cover_url=f"https://picsum.photos/400/300?random={i+30}",
                duration=45 + i * 20,
                likes=1500 + i * 300,
                comments=80 + i * 25,
                shares=20 + i * 8,
                views=15000 + i * 3000,
                publish_time=datetime.now()
            )
            videos.append(video)
            self.collected_videos[video.video_id] = video

        return videos

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
