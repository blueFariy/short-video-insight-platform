"""
Xiaohongshu (RED) Data Adapter
"""
import asyncio
import json
import re
import hashlib
from typing import List, Optional, Dict, Any
from datetime import datetime
from loguru import logger
import aiohttp

from app.adapters.base import PlatformAdapter
from app.models import Video, Creator, VideoMetrics
from app.core.config import settings


class XiaohongshuDataProvider:
    """小红书数据提供方 - 网页端爬取"""

    def __init__(self, api_key: str = None):
        self.api_key = api_key or settings.XHS_API_KEY
        self.base_url = "https://www.xiaohongshu.com"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Referer": "https://www.xiaohongshu.com/",
            "Cookie": ""  # 可选：添加cookie提高成功率
        }

    async def _get(self, url: str, params: Dict = None) -> str:
        """发送GET请求"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, headers=self.headers, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                    return await resp.text()
        except Exception as e:
            logger.error(f"Request failed: {e}")
            return ""

    async def _post(self, url: str, json: Dict = None) -> str:
        """发送POST请求"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=json, headers=self.headers, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                    return await resp.text()
        except Exception as e:
            logger.error(f"Request failed: {e}")
            return ""

    async def get_hot_notes(
        self,
        category: str = None,
        time_range: str = "1h",
        note_type: str = "video"
    ) -> List[Dict]:
        """
        获取热门笔记 - 从网页端获取
        小红书没有公开API，需要通过网页爬取
        """
        logger.info(f"Fetching Xiaohongshu hot notes: category={category}, type={note_type}")
        
        # 尝试从发现页面获取热门
        try:
            url = f"{self.base_url}/api/sns/web/v1/feed"
            # 构造请求payload
            payload = {
                "category": category or "all",
                "note_type": note_type,
                "page_size": 50,
                "refresh_type": 1
            }
            
            # 小红书API需要签名，这里先尝试简单方案
            # 实际可使用 selenium/playwright 模拟登录获取cookie
            
        except Exception as e:
            logger.error(f"Failed to fetch hot notes: {e}")
        
        # 备用：从搜索接口获取热门
        return await self._get_hot_from_search(category)

    async def _get_hot_from_search(self, category: str = None) -> List[Dict]:
        """从搜索接口获取热门"""
        keywords = ['热门', '爆款', '推荐']
        if category:
            keywords = [category]
        
        all_notes = []
        
        for keyword in keywords:
            try:
                url = f"{self.base_url}/api/sns/web/v1/search/notes"
                payload = {
                    "keyword": keyword,
                    "page": 1,
                    "page_size": 30,
                    "search_id": hashlib.md5(f"{keyword}_{datetime.now().strftime('%Y%m%d')}".encode()).hexdigest()
                }
                
                # 这里实际请求可能失败，因为需要登录态
                # 返回空列表
                
            except Exception as e:
                logger.error(f"Search failed for {keyword}: {e}")
                continue
        
        # 如果无法获取真实数据，返回空列表而非模拟数据
        return all_notes

    async def get_note_detail(self, note_id: str) -> Dict:
        """获取笔记详情"""
        logger.info(f"Fetching Xiaohongshu note detail: {note_id}")
        
        # 笔记详情API同样需要登录态
        # 这里返回空字典
        return {}

    async def get_user_notes(self, user_id: str, limit: int = 20) -> List[Dict]:
        """获取用户笔记"""
        logger.info(f"Fetching Xiaohongshu user notes: {user_id}")
        return []


class XiaohongshuSpider:
    """小红书爬虫（兜底方案）- 使用Selenium/Playwright可实现更稳定爬取"""

    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        }

    async def search_notes(self, keyword: str, limit: int = 20) -> List[Dict]:
        """搜索笔记 - 需要登录态"""
        logger.info(f"Searching Xiaohongshu notes: {keyword}")
        # 搜索API需要登录态，返回空列表
        return []


class XiaohongshuAdapter(PlatformAdapter):
    """小红书数据适配器"""

    def __init__(self):
        super().__init__()
        self.platform = "xiaohongshu"

        # 小红书没有公开API，主要依赖网页爬取（需要登录态）
        self.provider = XiaohongshuDataProvider(api_key=settings.XHS_API_KEY)
        self.spider = XiaohongshuSpider()

    async def get_trending_videos(
        self,
        category: Optional[str] = None,
        limit: int = 100
    ) -> List[Video]:
        """获取小红书热门视频笔记"""
        logger.info(f"Fetching trending videos from Xiaohongshu, limit: {limit}")

        try:
            # 按分类获取热门
            categories = ['beauty', 'fashion', 'food', 'travel', 'fitness']
            if category:
                categories = [category]

            trending = []

            for cat in categories:
                try:
                    notes = await self.provider.get_hot_notes(
                        category=cat,
                        time_range='1h',
                        note_type='video'
                    )

                    if not notes:
                        logger.info(f"No data fetched for category {cat}, trying search fallback")
                        # 尝试从搜索接口获取
                        notes = await self._get_notes_from_search(cat)

                    for note in notes[:min(30, limit // len(categories))]:
                        video_note = self._parse_xiaohongshu_note(note)
                        # 小红书特有的爆款特征识别
                        video_note.viral_factors = self._detect_xhs_viral_patterns(note)
                        trending.append(video_note)

                except Exception as e:
                    logger.error(f"Failed to fetch category {cat}: {e}")

            logger.info(f"Fetched {len(trending)} videos from Xiaohongshu")
            return trending[:limit]

        except Exception as e:
            logger.error(f"Failed to fetch trending videos: {e}")
            return []

    async def _get_notes_from_search(self, keyword: str) -> List[Dict]:
        """从搜索接口获取笔记"""
        try:
            notes = await self.spider.search_notes(keyword, 30)
            return notes
        except Exception as e:
            logger.error(f"Search fallback failed: {e}")
            return []

    async def get_video_detail(self, video_id: str) -> Optional[Video]:
        """获取视频详情"""
        logger.info(f"Fetching video detail: {video_id}")

        try:
            detail = await self.provider.get_note_detail(video_id)
            return self._parse_xiaohongshu_note(detail)

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
        # 实现获取创作者信息
        return None

    def _parse_xiaohongshu_note(self, data: Dict[str, Any]) -> Video:
        """解析小红书笔记数据"""
        stats = data.get('stats', {})
        user = data.get('user', {})
        cover = data.get('cover', {})
        video = data.get('video', {})

        # 统一指标
        metrics = VideoMetrics(
            video_id=data.get('note_id', ''),
            platform='xiaohongshu',
            play_count=stats.get('liked_count', 0) * 10,  # 小红书不公开播放量，用点赞估算
            like_count=stats.get('liked_count', 0),
            comment_count=stats.get('commented_count', 0),
            share_count=stats.get('shared_count', 0),
            collect_count=stats.get('collected_count', 0)
        )
        metrics.calculate_ratios()

        # 小红书特有指标
        max_like = max(metrics.like_count, 1)
        metrics.collect_ratio = metrics.collect_count / max_like

        duration = video.get('duration', 30) if video else 30

        video_obj = Video(
            video_id=data.get('note_id', ''),
            platform='xiaohongshu',
            title=data.get('title', '') or data.get('desc', ''),
            url=f"https://www.xiaohongshu.com/discovery/item/{data.get('note_id', '')}",
            creator_id=user.get('user_id', ''),
            creator_name=user.get('nickname', ''),
            cover_url=cover.get('url', '') if cover else '',
            duration=duration,
            metrics=metrics,
            publish_time=datetime.fromtimestamp(data.get('create_time', 0)) if data.get('create_time') else None,
            note_id=data.get('note_id', ''),
            viral_factors={}
        )

        return video_obj

    def _detect_xhs_viral_patterns(self, note: Dict[str, Any]) -> Dict[str, Any]:
        """小红书爆款特征识别"""
        patterns = {}

        stats = note.get('stats', {})
        like_count = stats.get('liked_count', 1)
        collect_count = stats.get('collected_count', 0)

        # 特征1: 封面图点击率（小红书很吃封面）
        if note.get('cover_ctr', 0) > 0.1:  # 封面点击率>10%
            patterns['high_ctr_cover'] = True

        # 特征2: 标题关键词（是否包含爆款标题公式）
        title = note.get('title', '')
        viral_title_patterns = [
            '实测', '测评', '干货', '避坑', '必看',
            '一招', '3分钟', '教程', '平价', '大牌平替'
        ]
        if any(pattern in title for pattern in viral_title_patterns):
            patterns['viral_title'] = True

        # 特征3: 收藏/点赞比（小红书用户喜欢收藏）
        if collect_count / like_count > 0.5:  # 收藏数超过点赞数一半
            patterns['high_collect_ratio'] = True

        # 特征4: 高互动率
        engagement = (like_count + collect_count + stats.get('commented_count', 0)) / max(like_count, 1)
        if engagement > 1.0:  # 互动数超过点赞数
            patterns['high_engagement'] = True

        # 特征5: 评论区"求链接"密度（带货潜力）
        comments = note.get('comments', [])
        ask_link_count = sum(
            1 for c in comments
            if '链接' in c.get('content', '') or '怎么买' in c.get('content', '')
        )
        if ask_link_count > 10:
            patterns['high_purchase_intent'] = True

        return patterns


# Singleton instance
xiaohongshu_adapter = XiaohongshuAdapter()


def get_xiaohongshu_adapter() -> XiaohongshuAdapter:
    """Get Xiaohongshu adapter instance"""
    return xiaohongshu_adapter
