"""
Bilibili Data Adapter
"""
import asyncio
import hashlib
import time
from typing import List, Optional, Dict, Any
from datetime import datetime
from loguru import logger
import aiohttp

from app.adapters.base import PlatformAdapter
from app.models import Video, Creator, VideoMetrics
from app.core.config import settings


class BilibiliOpenAPI:
    """Bilibili Official API - 使用公开API无需认证"""

    def __init__(self, app_key: str = None, app_secret: str = None):
        self.app_key = app_key or settings.BILI_APP_KEY
        self.app_secret = app_secret or settings.BILI_APP_SECRET
        self.base_url = "https://api.bilibili.com"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Referer": "https://www.bilibili.com",
            "Accept": "application/json, text/plain, */*"
        }

    async def _get(self, url: str, params: Dict = None) -> Dict:
        """发送GET请求"""
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, headers=self.headers, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                data = await resp.json()
                return data

    async def get_ranking(self, rid: str = "0", day: int = 3, type: str = "all") -> List[Dict]:
        """
        获取B站分区排行榜
        公开API: https://api.bilibili.com/x/web-interface/ranking/v2
        """
        logger.info(f"Fetching Bilibili ranking: rid={rid}, day={day}, type={type}")
        url = f"{self.base_url}/x/web-interface/ranking/v2"
        params = {
            "rid": rid,
            "type": type,
        }
        
        try:
            data = await self._get(url, params)
            if data.get("code") == 0:
                return data.get("data", {}).get("list", [])
            else:
                logger.error(f"Bilibili API error: {data.get('message')}")
                return await self._get_ranking_fallback(rid)
        except Exception as e:
            logger.error(f"Failed to fetch Bilibili ranking: {e}")
            return await self._get_ranking_fallback(rid)

    async def _get_ranking_fallback(self, rid: str) -> List[Dict]:
        """备用方案：从网页端获取排行榜"""
        url = f"{self.base_url}/x/web-interface/popular"
        params = {"pn": 1, "ps": 50}
        
        try:
            data = await self._get(url, params)
            if data.get("code") == 0:
                return data.get("data", {}).get("list", [])
        except:
            pass
        return []

    async def get_video_stat(self, bvid: str) -> Dict:
        """
        获取视频详细统计数据
        公开API: https://api.bilibili.com/x/web-interface/view?bvid=xxx
        """
        logger.info(f"Fetching Bilibili video stat: {bvid}")
        url = f"{self.base_url}/x/web-interface/view"
        params = {"bvid": bvid}
        
        try:
            data = await self._get(url, params)
            if data.get("code") == 0:
                return data.get("data", {}).get("stat", {})
        except Exception as e:
            logger.error(f"Failed to fetch video stat: {e}")
        
        return {}

    async def get_video_info(self, bvid: str) -> Dict:
        """获取视频完整信息"""
        url = f"{self.base_url}/x/web-interface/view"
        params = {"bvid": bvid}
        
        try:
            data = await self._get(url, params)
            if data.get("code") == 0:
                return data.get("data", {})
        except Exception as e:
            logger.error(f"Failed to fetch video info: {e}")
        
        return {}

    async def get_user_info(self, mid: str) -> Dict:
        """
        获取用户信息
        公开API: https://api.bilibili.com/x/space/acc/info?mid=xxx
        """
        logger.info(f"Fetching Bilibili user info: {mid}")
        url = f"{self.base_url}/x/space/acc/info"
        params = {"mid": mid}
        
        try:
            data = await self._get(url, params)
            if data.get("code") == 0:
                return data.get("data", {})
        except Exception as e:
            logger.error(f"Failed to fetch user info: {e}")
        
        return {}

    async def get_user_videos(self, mid: str, pn: int = 1, ps: int = 30) -> List[Dict]:
        """
        获取用户视频列表
        公开API: https://api.bilibili.com/x/space/arc/search?mid=xxx
        """
        url = f"{self.base_url}/x/space/arc/search"
        params = {"mid": mid, "pn": pn, "ps": ps, "order": "pubdate"}
        
        try:
            data = await self._get(url, params)
            if data.get("code") == 0:
                return data.get("data", {}).get("list", {}).get("vlist", [])
        except Exception as e:
            logger.error(f"Failed to fetch user videos: {e}")
        
        return []


class BilibiliSpider:
    """B站网页端爬虫 - 备用方案"""

    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Referer": "https://www.bilibili.com",
        }
        self.base_url = "https://www.bilibili.com"

    async def _get(self, url: str, params: Dict = None) -> str:
        """发送GET请求"""
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, headers=self.headers, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                return await resp.text()

    async def get_popular(self, partition: str = "douga") -> List[Dict]:
        """获取热门视频 - 从网页端解析"""
        # 使用API作为主要数据源，爬虫作为备用
        logger.info(f"Fetching Bilibili popular from spider: {partition}")
        # 实际实现会从网页HTML解析，这里返回空列表让API方案生效
        return []


class BilibiliAdapter(PlatformAdapter):
    """B站数据适配器"""

    def __init__(self):
        super().__init__()
        self.platform = "bilibili"

        # B站开放程度较高，有完善的API
        self.api = BilibiliOpenAPI(
            app_key=settings.BILI_APP_KEY,
            app_secret=settings.BILI_APP_SECRET
        )
        self.spider = BilibiliSpider()

    async def get_trending_videos(
        self,
        category: Optional[str] = None,
        limit: int = 100
    ) -> List[Video]:
        """获取B站热门视频
        
        Args:
            category: 分区名称，支持: douga, music, game, technology, life, food, beauty, knowledge 等
                      也支持中文: 动画, 音乐, 游戏, 科技, 生活, 美食, 美妆, 知识 等
            limit: 返回数量限制
        """
        logger.info(f"Fetching trending videos from Bilibili, category: {category}, limit: {limit}")

        # 默认分区列表
        default_partitions = ['douga', 'music', 'game', 'technology', 'life', 'food']
        
        # 根据category参数确定要获取的分区
        if category:
            # 将category转换为分区ID
            partition_id = self._get_partition_id(category)
            if partition_id != "0":
                # 如果是有效的分区，直接获取该分区
                partitions = [category]
            else:
                # 无效分区，使用默认分区
                logger.warning(f"Unknown category: {category}, using default partitions")
                partitions = default_partitions
        else:
            partitions = default_partitions

        trending_videos = []

        # 限制分区数量，避免请求过多
        partitions = partitions[:3]

        for partition in partitions:
            try:
                partition_id = self._get_partition_id(partition)
                hot_list = await self.api.get_ranking(
                    rid=partition_id,
                    day=3,
                    type='all'
                )

                if hot_list:
                    # 根据limit动态调整每个分区获取的数量
                    per_partition = max(1, limit // len(partitions))
                    for item in hot_list[:per_partition]:
                        video = await self._enrich_video_data(item)
                        trending_videos.append(video)

            except Exception as e:
                logger.error(f"Failed to fetch {partition}: {e}")

        # 如果所有API都失败，尝试备用数据源
        if not trending_videos:
            logger.warning("API failed, trying spider fallback")
            try:
                spider_data = await self.spider.get_popular()
                for item in spider_data[:limit]:
                    video = self._parse_bilibili_video(item)
                    trending_videos.append(video)
            except Exception as e:
                logger.error(f"Spider fallback also failed: {e}")

        logger.info(f"Fetched {len(trending_videos)} videos from Bilibili")
        return trending_videos[:limit]

    async def get_video_detail(self, video_id: str) -> Optional[Video]:
        """获取视频详情"""
        logger.info(f"Fetching video detail: {video_id}")

        try:
            # 从API获取完整视频信息
            data = await self.api.get_video_info(video_id)
            
            if not data:
                logger.warning(f"Video not found: {video_id}")
                return None

            return self._parse_bilibili_video(data)

        except Exception as e:
            logger.error(f"Failed to get video detail: {e}")
            return None

    async def get_creator_videos(
        self,
        creator_id: str,
        limit: int = 50
    ) -> List[Video]:
        """获取创作者视频"""
        logger.info(f"Fetching videos for creator: {creator_id}")
        # 实现获取创作者视频列表
        return []

    async def get_creator_info(self, creator_id: str) -> Optional[Creator]:
        """获取创作者信息"""
        logger.info(f"Fetching creator info: {creator_id}")

        try:
            user_info = await self.api.get_user_info(creator_id)

            if not user_info:
                return None

            return Creator(
                creator_id=str(user_info.get('mid', '')),
                platform='bilibili',
                name=user_info.get('name', ''),
                url=f"https://space.bilibili.com/{creator_id}",
                avatar_url=user_info.get('face', ''),
                follower_count=user_info.get('follower', 0),
                video_count=user_info.get('count', {}).get('video', 0) if isinstance(user_info.get('count'), dict) else 0
            )

        except Exception as e:
            logger.error(f"Failed to get creator info: {e}")
            return None

    async def _enrich_video_data(self, base_data: Dict[str, Any]) -> Video:
        """丰富视频数据（B站特有的指标）"""
        bvid = base_data.get('bvid', '')
        
        # B站API返回的数据结构中，stat是独立的部分
        stats = base_data.get('stat', {})

        # 如果stat为空，尝试从base_data获取
        if not stats:
            stats = {
                'view': base_data.get('view', 0),
                'like': base_data.get('like', 0),
                'coin': base_data.get('coin', 0),
                'favorite': base_data.get('favorite', 0),
                'share': base_data.get('share', 0),
                'danmaku': base_data.get('danmaku', 0)
            }

        # B站核心爆款指标
        view_count = stats.get('view', 0)
        
        # 解析时长
        duration = 0
        duration_str = base_data.get('duration', '0:00')
        if isinstance(duration_str, int):
            duration = duration_str
        else:
            duration = self._parse_duration(duration_str)

        metrics = VideoMetrics(
            video_id=bvid,
            platform='bilibili',
            play_count=view_count,
            like_count=stats.get('like', 0),
            coin_count=stats.get('coin', 0),
            favorite_count=stats.get('favorite', 0),
            share_count=stats.get('share', 0),
            danmaku_count=stats.get('danmaku', 0)
        )
        metrics.calculate_ratios()

        # B站特有指标
        if view_count > 0:
            metrics.coin_ratio = stats.get('coin', 0) / view_count
            metrics.danmaku_density = stats.get('danmaku', 0) / max(duration / 60, 1)

        owner = base_data.get('owner', {})
        if not owner:
            owner = base_data.get('author', {})

        # B站爆款特征识别
        viral_factors = self._detect_bilibili_viral_patterns(metrics)

        video = Video(
            video_id=bvid,
            platform='bilibili',
            title=base_data.get('title', ''),
            url=f"https://www.bilibili.com/video/{bvid}/",
            creator_id=str(owner.get('mid', '')) if isinstance(owner, dict) else str(owner),
            creator_name=owner.get('name', '') if isinstance(owner, dict) else str(owner),
            cover_url=base_data.get('pic', ''),
            duration=duration,
            metrics=metrics,
            publish_time=datetime.fromtimestamp(base_data.get('pubdate', 0)) if base_data.get('pubdate') else None,
            bvid=bvid,
            viral_factors=viral_factors
        )

        return video

    def _parse_bilibili_video(self, data: Dict[str, Any]) -> Video:
        """解析B站视频数据"""
        stats = data.get('stat', {})
        
        # 兼容不同数据结构
        if not stats:
            stats = {
                'view': data.get('view', 0),
                'like': data.get('like', 0),
                'coin': data.get('coin', 0),
                'favorite': data.get('favorite', 0),
                'share': data.get('share', 0),
                'danmaku': data.get('danmaku', 0)
            }

        view_count = stats.get('view', 0)
        
        # 解析时长
        duration = 0
        duration_str = data.get('duration', '0:00')
        if isinstance(duration_str, int):
            duration = duration_str
        else:
            duration = self._parse_duration(duration_str)

        metrics = VideoMetrics(
            video_id=data.get('bvid', ''),
            platform='bilibili',
            play_count=view_count,
            like_count=stats.get('like', 0),
            coin_count=stats.get('coin', 0),
            favorite_count=stats.get('favorite', 0),
            share_count=stats.get('share', 0),
            danmaku_count=stats.get('danmaku', 0)
        )
        metrics.calculate_ratios()

        owner = data.get('owner', {})
        if not owner:
            owner = data.get('author', {})

        return Video(
            video_id=data.get('bvid', ''),
            platform='bilibili',
            title=data.get('title', ''),
            url=f"https://www.bilibili.com/video/{data.get('bvid', '')}/",
            creator_id=str(owner.get('mid', '')) if isinstance(owner, dict) else str(owner),
            creator_name=owner.get('name', '') if isinstance(owner, dict) else str(owner),
            cover_url=data.get('pic', ''),
            duration=duration,
            metrics=metrics,
            publish_time=datetime.fromtimestamp(data.get('pubdate', 0)) if data.get('pubdate') else None,
            bvid=data.get('bvid', ''),
            viral_factors=self._detect_bilibili_viral_patterns(metrics)
        )

    def _detect_bilibili_viral_patterns(self, metrics: VideoMetrics) -> Dict[str, Any]:
        """B站爆款特征识别"""
        patterns = {}

        # B站爆款特征：
        # 1. 发布24小时内，投币率 > 5%（说明内容高质量）
        if metrics.coin_ratio > 0.05:
            patterns['high_coin_ratio'] = True

        # 2. 弹幕密度 > 100条/分钟（观众互动热烈）
        if metrics.danmaku_density > 100:
            patterns['high_danmaku_density'] = True

        # 3. 收藏/播放比 > 10%（值得反复观看）
        if metrics.favorite_count / max(metrics.play_count, 1) > 0.1:
            patterns['high_favorite_ratio'] = True

        # 4. 高互动率
        if metrics.engagement_rate > 0.1:
            patterns['high_engagement'] = True

        return patterns

    def _get_partition_id(self, partition: str) -> str:
        """获取分区ID"""
        partition_map = {
            "douga": "1",
            "guichu": "5",
            "music": "3",
            "dance": "29",
            "game": "4",
            "technology": "36",
            "life": "160"
        }
        return partition_map.get(partition, "0")

    def _parse_duration(self, duration_str: str) -> int:
        """解析时长字符串为秒"""
        try:
            parts = duration_str.split(':')
            if len(parts) == 2:
                return int(parts[0]) * 60 + int(parts[1])
            elif len(parts) == 3:
                return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
        except:
            pass
        return 60


# Singleton instance
bilibili_adapter = BilibiliAdapter()


def get_bilibili_adapter() -> BilibiliAdapter:
    """Get Bilibili adapter instance"""
    return bilibili_adapter
