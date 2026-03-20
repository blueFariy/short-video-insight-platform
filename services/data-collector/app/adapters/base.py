"""
Platform Adapter Base Class
"""
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from loguru import logger

from app.models import Video, Creator, VideoMetrics


class PlatformAdapter(ABC):
    """Base class for platform data adapters"""

    def __init__(self):
        self.platform_name = self.__class__.__name__.replace('Adapter', '').lower()

    @abstractmethod
    async def get_trending_videos(
        self,
        category: Optional[str] = None,
        limit: int = 100
    ) -> List[Video]:
        """
        Get trending videos from the platform

        Args:
            category: Category filter
            limit: Maximum videos to return

        Returns:
            List of trending videos
        """
        pass

    @abstractmethod
    async def get_video_detail(self, video_id: str) -> Optional[Video]:
        """
        Get detailed information for a specific video

        Args:
            video_id: Video ID on the platform

        Returns:
            Video details or None if not found
        """
        pass

    @abstractmethod
    async def get_creator_videos(
        self,
        creator_id: str,
        limit: int = 50
    ) -> List[Video]:
        """
        Get videos from a specific creator

        Args:
            creator_id: Creator ID on the platform
            limit: Maximum videos to return

        Returns:
            List of videos from the creator
        """
        pass

    @abstractmethod
    async def get_creator_info(self, creator_id: str) -> Optional[Creator]:
        """
        Get creator information

        Args:
            creator_id: Creator ID on the platform

        Returns:
            Creator info or None if not found
        """
        pass

    async def search_videos(
        self,
        keyword: str,
        limit: int = 20
    ) -> List[Video]:
        """
        Search videos by keyword (default implementation)

        Args:
            keyword: Search keyword
            limit: Maximum results

        Returns:
            List of matching videos
        """
        # Default: fetch trending and filter
        trending = await self.get_trending_videos(limit=limit * 2)
        results = [v for v in trending if keyword.lower() in v.title.lower()]
        return results[:limit]

    def _detect_viral_patterns(self, video: Video, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Detect viral patterns for the platform

        Args:
            video: Video object
            raw_data: Raw API response data

        Returns:
            Dictionary of viral factors
        """
        factors = {}
        metrics = video.metrics

        # Common viral patterns
        if metrics.engagement_rate > 0.1:  # 互动率超过10%
            factors['high_engagement'] = True

        if metrics.like_ratio > 0.1:  # 点赞率超过10%
            factors['high_likes'] = True

        # Check for viral title patterns
        viral_keywords = ['实测', '测评', '干货', '避坑', '必看', '教程', '一招', '3分钟']
        if any(kw in video.title for kw in viral_keywords):
            factors['viral_title'] = True

        return factors


class DataSourceFallbackMixin:
    """Mixin for handling multiple data sources with fallback"""

    def __init__(self):
        self.data_sources: Dict[str, Any] = {}

    async def _fetch_with_fallback(
        self,
        sources: List[str],
        fetch_func_name: str,
        *args,
        **kwargs
    ) -> Optional[Any]:
        """
        Try multiple data sources in order until one succeeds

        Args:
            sources: List of data source names
            fetch_func_name: Name of the fetch method to call
            *args, **kwargs: Arguments to pass to the fetch method

        Returns:
            Data from the first successful source, or None if all fail
        """
        for source_name in sources:
            source = self.data_sources.get(source_name)
            if not source:
                logger.warning(f"Data source {source_name} not available")
                continue

            try:
                fetch_method = getattr(source, fetch_func_name, None)
                if fetch_method:
                    result = await fetch_method(*args, **kwargs)
                    if result:
                        logger.info(f"Successfully fetched from {source_name}")
                        return result
            except Exception as e:
                logger.error(f"Failed to fetch from {source_name}: {e}")
                continue

        logger.error(f"All data sources failed for {fetch_func_name}")
        return None
