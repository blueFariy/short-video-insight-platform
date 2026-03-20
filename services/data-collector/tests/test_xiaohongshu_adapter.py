"""
Tests for Xiaohongshu Adapter
"""
import pytest
from datetime import datetime


class TestXiaohongshuAdapter:
    """Test Xiaohongshu adapter functionality"""

    def test_adapter_initialization(self):
        """Test adapter can be initialized"""
        from app.adapters.xiaohongshu_adapter import XiaohongshuAdapter
        
        adapter = XiaohongshuAdapter()
        assert adapter.platform == "xiaohongshu"
        assert adapter.provider is not None

    @pytest.mark.asyncio
    async def test_get_trending_videos(self):
        """Test getting trending videos from Xiaohongshu"""
        from app.adapters.xiaohongshu_adapter import XiaohongshuAdapter
        
        adapter = XiaohongshuAdapter()
        videos = await adapter.get_trending_videos(limit=10)
        
        # 验证返回的是视频列表
        assert isinstance(videos, list)

    @pytest.mark.asyncio
    async def test_get_trending_videos_with_category(self):
        """Test getting trending videos with category filter"""
        from app.adapters.xiaohongshu_adapter import XiaohongshuAdapter
        
        adapter = XiaohongshuAdapter()
        videos = await adapter.get_trending_videos(category="beauty", limit=10)
        
        assert isinstance(videos, list)

    @pytest.mark.asyncio
    async def test_get_video_detail(self):
        """Test getting video detail"""
        from app.adapters.xiaohongshu_adapter import XiaohongshuAdapter
        
        adapter = XiaohongshuAdapter()
        
        # 小红书需要登录态
        video = await adapter.get_video_detail("test_note_id")
        
        # 应该返回None（因为需要认证）
        assert video is None

    @pytest.mark.asyncio
    async def test_parse_xiaohongshu_note(self):
        """Test parsing Xiaohongshu note data"""
        from app.adapters.xiaohongshu_adapter import XiaohongshuAdapter
        
        adapter = XiaohongshuAdapter()
        
        # 模拟笔记数据
        data = {
            "note_id": "test_note_123",
            "title": "测试笔记",
            "desc": "这是一个测试笔记",
            "type": "video",
            "user": {
                "user_id": "user_123",
                "nickname": "测试博主"
            },
            "cover": {
                "url": "https://example.com/cover.jpg"
            },
            "video": {
                "duration": 120
            },
            "stats": {
                "liked_count": 5000,
                "collected_count": 3000,
                "commented_count": 200,
                "shared_count": 100
            },
            "create_time": int(datetime.now().timestamp())
        }
        
        video = adapter._parse_xiaohongshu_note(data)
        
        assert video.platform == "xiaohongshu"
        assert video.title == "测试笔记"
        assert video.creator_name == "测试博主"
        assert video.duration == 120
        assert video.metrics.like_count == 5000
        assert video.metrics.collect_count == 3000


class TestXiaohongshuDataProvider:
    """Test Xiaohongshu data provider"""

    def test_provider_initialization(self):
        """Test provider can be initialized"""
        from app.adapters.xiaohongshu_adapter import XiaohongshuDataProvider
        
        provider = XiaohongshuDataProvider()
        assert provider.base_url == "https://www.xiaohongshu.com"

    def test_provider_with_api_key(self):
        """Test provider with API key"""
        from app.adapters.xiaohongshu_adapter import XiaohongshuDataProvider
        
        provider = XiaohongshuDataProvider(api_key="test_key")
        assert provider.api_key == "test_key"

    @pytest.mark.asyncio
    async def test_get_hot_notes(self):
        """Test getting hot notes"""
        from app.adapters.xiaohongshu_adapter import XiaohongshuDataProvider
        
        provider = XiaohongshuDataProvider()
        
        try:
            result = await provider.get_hot_notes(category="beauty")
            # 小红书需要登录态，可能返回空列表
            assert isinstance(result, list)
        except Exception as e:
            pytest.skip(f"Network request failed: {e}")

    @pytest.mark.asyncio
    async def test_get_note_detail(self):
        """Test getting note detail"""
        from app.adapters.xiaohongshu_adapter import XiaohongshuDataProvider
        
        provider = XiaohongshuDataProvider()
        
        # 需要登录态
        result = await provider.get_note_detail("test_note_id")
        assert result == {}


class TestXiaohongshuSpider:
    """Test Xiaohongshu spider"""

    def test_spider_initialization(self):
        """Test spider can be initialized"""
        from app.adapters.xiaohongshu_adapter import XiaohongshuSpider
        
        spider = XiaohongshuSpider()
        assert spider.headers is not None

    @pytest.mark.asyncio
    async def test_search_notes(self):
        """Test searching notes"""
        from app.adapters.xiaohongshu_adapter import XiaohongshuSpider
        
        spider = XiaohongshuSpider()
        
        # 小红书搜索需要登录态
        result = await spider.search_notes("美妆")
        assert isinstance(result, list)


class TestXiaohongshuViralDetection:
    """Test Xiaohongshu viral pattern detection"""

    @pytest.mark.asyncio
    async def test_detect_high_ctr_cover(self):
        """Test detecting high CTR cover pattern"""
        from app.adapters.xiaohongshu_adapter import XiaohongshuAdapter
        
        adapter = XiaohongshuAdapter()
        
        note = {
            "title": "测试笔记",
            "cover_ctr": 0.15,  # 15% 封面点击率
            "stats": {
                "liked_count": 5000,
                "collected_count": 3000,
                "commented_count": 200
            }
        }
        
        patterns = adapter._detect_xhs_viral_patterns(note)
        
        assert 'high_ctr_cover' in patterns

    @pytest.mark.asyncio
    async def test_detect_viral_title(self):
        """Test detecting viral title pattern"""
        from app.adapters.xiaohongshu_adapter import XiaohongshuAdapter
        
        adapter = XiaohongshuAdapter()
        
        # 测试包含爆款关键词的标题
        note = {
            "title": "实测好物分享！必看测评",
            "cover_ctr": 0.05,
            "stats": {
                "liked_count": 1000,
                "collected_count": 500,
                "commented_count": 100
            }
        }
        
        patterns = adapter._detect_xhs_viral_patterns(note)
        
        assert 'viral_title' in patterns

    @pytest.mark.asyncio
    async def test_detect_high_collect_ratio(self):
        """Test detecting high collect ratio pattern"""
        from app.adapters.xiaohongshu_adapter import XiaohongshuAdapter
        
        adapter = XiaohongshuAdapter()
        
        note = {
            "title": "测试笔记",
            "cover_ctr": 0.05,
            "stats": {
                "liked_count": 1000,
                "collected_count": 600,  # 收藏超过点赞60%
                "commented_count": 100
            }
        }
        
        patterns = adapter._detect_xhs_viral_patterns(note)
        
        assert 'high_collect_ratio' in patterns

    @pytest.mark.asyncio
    async def test_detect_high_engagement(self):
        """Test detecting high engagement pattern"""
        from app.adapters.xiaohongshu_adapter import XiaohongshuAdapter
        
        adapter = XiaohongshuAdapter()
        
        note = {
            "title": "测试笔记",
            "cover_ctr": 0.05,
            "stats": {
                "liked_count": 1000,
                "collected_count": 500,
                "commented_count": 800  # 高评论
            }
        }
        
        patterns = adapter._detect_xhs_viral_patterns(note)
        
        # 互动数超过点赞数
        assert 'high_engagement' in patterns

    @pytest.mark.asyncio
    async def test_detect_purchase_intent(self):
        """Test detecting high purchase intent pattern"""
        from app.adapters.xiaohongshu_adapter import XiaohongshuAdapter
        
        adapter = XiaohongshuAdapter()
        
        note = {
            "title": "测试笔记",
            "cover_ctr": 0.05,
            "stats": {
                "liked_count": 1000,
                "collected_count": 500,
                "commented_count": 200
            },
            "comments": [
                {"content": "求链接"},
                {"content": "怎么买"},
                {"content": "在哪买"},
                {"content": "太棒了"},
                {"content": "求链接"},
                {"content": "求链接"},
                {"content": "求链接"},
                {"content": "求链接"},
                {"content": "求链接"},
                {"content": "求链接"},
                {"content": "求链接"},
                {"content": "很好"},
            ]
        }
        
        patterns = adapter._detect_xhs_viral_patterns(note)
        
        # 超过10条"求链接"评论
        assert 'high_purchase_intent' in patterns
