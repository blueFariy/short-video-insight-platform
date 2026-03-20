"""
Tests for Bilibili Adapter
"""
import pytest
from datetime import datetime


class TestBilibiliAdapter:
    """Test Bilibili adapter functionality"""

    def test_adapter_initialization(self):
        """Test adapter can be initialized"""
        from app.adapters.bilibili_adapter import BilibiliAdapter
        
        adapter = BilibiliAdapter()
        assert adapter.platform == "bilibili"
        assert adapter.api is not None

    @pytest.mark.asyncio
    async def test_get_trending_videos(self):
        """Test getting trending videos from Bilibili"""
        from app.adapters.bilibili_adapter import BilibiliAdapter
        
        adapter = BilibiliAdapter()
        videos = await adapter.get_trending_videos(limit=10)
        print(videos)
        # 验证返回的是视频列表
        assert isinstance(videos, list)
        
        # 如果获取到数据，验证数据结构
        if videos:
            video = videos[0]
            assert hasattr(video, 'video_id')
            assert hasattr(video, 'title')
            assert hasattr(video, 'platform')
            assert video.platform == 'bilibili'

    @pytest.mark.asyncio
    async def test_get_trending_videos_with_category(self):
        """Test getting trending videos with category filter"""
        from app.adapters.bilibili_adapter import BilibiliAdapter
        
        adapter = BilibiliAdapter()
        videos = await adapter.get_trending_videos(category="game", limit=10)
        print(videos)
        assert isinstance(videos, list)

    @pytest.mark.asyncio
    async def test_get_video_detail(self):
        """Test getting video detail"""
        from app.adapters.bilibili_adapter import BilibiliAdapter
        
        adapter = BilibiliAdapter()
        
        # 测试一个真实的BV号
        video = await adapter.get_video_detail("BV1GJ411x7h7")
        
        # 如果能获取到数据，验证结构
        if video:
            assert video.platform == 'bilibili'
            assert hasattr(video, 'metrics')

    @pytest.mark.asyncio
    async def test_get_creator_info(self):
        """Test getting creator info"""
        from app.adapters.bilibili_adapter import BilibiliAdapter
        
        adapter = BilibiliAdapter()
        
        # 测试一个真实的UP主ID
        creator = await adapter.get_creator_info("3368963")
        
        # 如果能获取到数据
        if creator:
            assert creator.platform == 'bilibili'
            assert hasattr(creator, 'name')
            assert hasattr(creator, 'follower_count')

    @pytest.mark.asyncio
    async def test_get_partition_id(self):
        """Test partition ID mapping"""
        from app.adapters.bilibili_adapter import BilibiliAdapter
        
        adapter = BilibiliAdapter()
        
        assert adapter._get_partition_id("douga") == "1"
        assert adapter._get_partition_id("music") == "3"
        assert adapter._get_partition_id("game") == "4"
        assert adapter._get_partition_id("technology") == "36"

    @pytest.mark.asyncio
    async def test_parse_duration(self):
        """Test duration parsing"""
        from app.adapters.bilibili_adapter import BilibiliAdapter
        
        adapter = BilibiliAdapter()
        
        assert adapter._parse_duration("10:00") == 600
        assert adapter._parse_duration("1:30:00") == 5400
        assert adapter._parse_duration("5:30") == 330

    @pytest.mark.asyncio
    async def test_detect_bilibili_viral_patterns(self):
        """Test viral pattern detection"""
        from app.adapters.bilibili_adapter import BilibiliAdapter
        from app.models import VideoMetrics
        
        adapter = BilibiliAdapter()
        
        # 测试高投币率
        metrics = VideoMetrics(
            video_id="test",
            platform="bilibili",
            play_count=10000,
            coin_count=600,  # 6% 投币率
            like_count=1000,
            danmaku_count=500
        )
        metrics.calculate_ratios()
        
        patterns = adapter._detect_bilibili_viral_patterns(metrics)
        
        # 验证爆款特征检测
        assert isinstance(patterns, dict)


class TestBilibiliAPI:
    """Test Bilibili API client"""

    @pytest.mark.asyncio
    async def test_api_initialization(self):
        """Test API client initialization"""
        from app.adapters.bilibili_adapter import BilibiliOpenAPI
        
        api = BilibiliOpenAPI()
        assert api.base_url == "https://api.bilibili.com"

    @pytest.mark.asyncio
    async def test_get_ranking(self):
        """Test getting ranking data"""
        from app.adapters.bilibili_adapter import BilibiliOpenAPI
        
        api = BilibiliOpenAPI()
        
        try:
            result = await api.get_ranking(rid="0", day=3)
            assert isinstance(result, list)
        except Exception as e:
            # 网络请求可能失败
            pytest.skip(f"Network request failed: {e}")

    @pytest.mark.asyncio
    async def test_get_video_info(self):
        """Test getting video info"""
        from app.adapters.bilibili_adapter import BilibiliOpenAPI
        
        api = BilibiliOpenAPI()
        
        try:
            result = await api.get_video_info("BV1GJ411x7h7")
            assert isinstance(result, dict)
        except Exception as e:
            pytest.skip(f"Network request failed: {e}")

    @pytest.mark.asyncio
    async def test_get_user_info(self):
        """Test getting user info"""
        from app.adapters.bilibili_adapter import BilibiliOpenAPI
        
        api = BilibiliOpenAPI()
        
        try:
            result = await api.get_user_info("3368963")
            assert isinstance(result, dict)
        except Exception as e:
            pytest.skip(f"Network request failed: {e}")
