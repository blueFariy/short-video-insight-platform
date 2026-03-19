"""
Data Collector Service - Comprehensive Tests
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime


class TestAccountModel:
    """Test Account model"""

    def test_account_creation(self):
        """Test account creation"""
        from app.services.account_service import Account
        account = Account(
            id="test_001",
            name="测试账号",
            platform="douyin",
            account_id="test123",
            url="https://v.douyin.com/test/",
            category="测试"
        )
        assert account.id == "test_001"
        assert account.name == "测试账号"
        assert account.platform == "douyin"
        assert account.status == "active"

    def test_account_to_dict(self):
        """Test account serialization"""
        from app.services.account_service import Account
        account = Account(
            id="test_001",
            name="测试账号",
            platform="douyin",
            account_id="test123",
            url="https://v.douyin.com/test/"
        )
        data = account.to_dict()
        assert data["id"] == "test_001"
        assert data["name"] == "测试账号"
        assert "platform" in data


class TestAccountService:
    """Test account service"""

    def test_account_service_initialization(self):
        """Test account service initialization"""
        from app.services.account_service import AccountService
        service = AccountService()
        assert len(service.accounts) > 0  # Demo accounts

    @pytest.mark.asyncio
    async def test_create_account(self):
        """Test account creation"""
        from app.services.account_service import AccountService
        service = AccountService()
        account = await service.create_account(
            name="新账号",
            platform="douyin",
            account_id="new123",
            url="https://v.douyin.com/new/",
            category="测试"
        )
        assert account.name == "新账号"
        assert account.platform == "douyin"

    @pytest.mark.asyncio
    async def test_get_account(self):
        """Test get account"""
        from app.services.account_service import AccountService
        service = AccountService()
        account = await service.get_account("acc_001")
        assert account is not None
        assert account.name == "疯狂小杨哥"

    @pytest.mark.asyncio
    async def test_get_account_not_found(self):
        """Test get non-existent account"""
        from app.services.account_service import AccountService
        service = AccountService()
        account = await service.get_account("nonexistent")
        assert account is None

    @pytest.mark.asyncio
    async def test_list_accounts(self):
        """Test list accounts"""
        from app.services.account_service import AccountService
        service = AccountService()
        accounts = await service.list_accounts()
        assert len(accounts) > 0

    @pytest.mark.asyncio
    async def test_list_accounts_by_platform(self):
        """Test list accounts by platform"""
        from app.services.account_service import AccountService
        service = AccountService()
        accounts = await service.list_accounts(platform="douyin")
        assert all(a.platform == "douyin" for a in accounts)

    @pytest.mark.asyncio
    async def test_list_accounts_by_status(self):
        """Test list accounts by status"""
        from app.services.account_service import AccountService
        service = AccountService()
        accounts = await service.list_accounts(status="active")
        assert all(a.status == "active" for a in accounts)

    @pytest.mark.asyncio
    async def test_update_account(self):
        """Test account update"""
        from app.services.account_service import AccountService
        service = AccountService()
        account = await service.update_account("acc_001", name="新名称", category="新分类")
        assert account is not None
        assert account.name == "新名称"

    @pytest.mark.asyncio
    async def test_delete_account(self):
        """Test account deletion"""
        from app.services.account_service import AccountService
        service = AccountService()
        # First create an account
        account = await service.create_account(
            name="待删除账号",
            platform="douyin",
            account_id="delete123",
            url="https://v.douyin.com/delete/"
        )
        result = await service.delete_account(account.id)
        assert result is True

    @pytest.mark.asyncio
    async def test_get_active_accounts(self):
        """Test get active accounts"""
        from app.services.account_service import AccountService
        service = AccountService()
        accounts = await service.get_active_accounts()
        assert all(a.status == "active" for a in accounts)


class TestVideoInfo:
    """Test VideoInfo model"""

    def test_video_info_creation(self):
        """Test video info creation"""
        from app.services.collector_service import VideoInfo
        video = VideoInfo(
            video_id="test_video_001",
            title="测试视频",
            platform="douyin",
            account_id="test123",
            account_name="测试账号",
            url="https://v.douyin.com/test/",
            cover_url="https://example.com/cover.jpg",
            duration=60
        )
        assert video.video_id == "test_video_001"
        assert video.title == "测试视频"
        assert video.likes == 0

    def test_video_info_to_dict(self):
        """Test video info serialization"""
        from app.services.collector_service import VideoInfo
        video = VideoInfo(
            video_id="test_video_001",
            title="测试视频",
            platform="douyin",
            account_id="test123",
            account_name="测试账号",
            url="https://v.douyin.com/test/",
            cover_url="https://example.com/cover.jpg",
            duration=60,
            likes=100
        )
        data = video.to_dict()
        assert data["video_id"] == "test_video_001"
        assert data["likes"] == 100


class TestCollectorService:
    """Test collector service"""

    def test_collector_service_initialization(self):
        """Test collector service initialization"""
        from app.services.collector_service import CollectorService
        service = CollectorService()
        assert service.platform_collectors is not None

    @pytest.mark.asyncio
    async def test_collect_douyin(self):
        """Test Douyin collection"""
        from app.services.collector_service import CollectorService
        from app.services.account_service import Account

        service = CollectorService()
        account = Account(
            id="test_acc",
            name="测试账号",
            platform="douyin",
            account_id="test123",
            url="https://v.douyin.com/test/"
        )

        videos = await service._collect_douyin(account, limit=5)
        assert len(videos) <= 5
        assert all(v.platform == "douyin" for v in videos)

    @pytest.mark.asyncio
    async def test_collect_bilibili(self):
        """Test Bilibili collection"""
        from app.services.collector_service import CollectorService
        from app.services.account_service import Account

        service = CollectorService()
        account = Account(
            id="test_acc",
            name="测试账号",
            platform="bilibili",
            account_id="test123",
            url="https://space.bilibili.com/test"
        )

        videos = await service._collect_bilibili(account, limit=5)
        assert len(videos) <= 5
        assert all(v.platform == "bilibili" for v in videos)

    @pytest.mark.asyncio
    async def test_collect_xiaohongshu(self):
        """Test Xiaohongshu collection"""
        from app.services.collector_service import CollectorService
        from app.services.account_service import Account

        service = CollectorService()
        account = Account(
            id="test_acc",
            name="测试账号",
            platform="xiaohongshu",
            account_id="test123",
            url="https://www.xiaohongshu.com/user/profile/test"
        )

        videos = await service._collect_xiaohongshu(account, limit=5)
        assert len(videos) <= 5

    @pytest.mark.asyncio
    async def test_collect_unsupported_platform(self):
        """Test unsupported platform"""
        from app.services.collector_service import CollectorService
        from app.services.account_service import Account

        service = CollectorService()
        account = Account(
            id="test_acc",
            name="测试账号",
            platform="unknown",
            account_id="test123",
            url="https://example.com/test"
        )

        videos = await service.collect_account(account)
        assert len(videos) == 0

    @pytest.mark.asyncio
    async def test_get_video(self):
        """Test get video by ID"""
        from app.services.collector_service import CollectorService
        from app.services.account_service import Account

        service = CollectorService()
        account = Account(
            id="test_acc",
            name="测试账号",
            platform="douyin",
            account_id="test123",
            url="https://v.douyin.com/test/"
        )

        videos = await service._collect_douyin(account, limit=1)
        video = await service.get_video(videos[0].video_id)
        assert video is not None

    @pytest.mark.asyncio
    async def test_get_videos_by_account(self):
        """Test get videos by account"""
        from app.services.collector_service import CollectorService
        from app.services.account_service import Account

        service = CollectorService()
        account = Account(
            id="test_acc",
            name="测试账号",
            platform="douyin",
            account_id="test123",
            url="https://v.douyin.com/test/"
        )

        await service._collect_douyin(account, limit=3)
        videos = await service.get_videos_by_account("test123")
        assert len(videos) > 0

    @pytest.mark.asyncio
    async def test_search_videos(self):
        """Test video search"""
        from app.services.collector_service import CollectorService
        from app.services.account_service import Account

        service = CollectorService()
        account = Account(
            id="test_acc",
            name="测试账号",
            platform="douyin",
            account_id="test123",
            url="https://v.douyin.com/test/"
        )

        await service._collect_douyin(account, limit=5)
        results = await service.search_videos("视频")
        assert isinstance(results, list)


class TestResponseModel:
    """Test response models"""

    def test_success_response(self):
        """Test success response"""
        from app.core.response import success_response
        response = success_response(data={"account": "test"})
        assert response.code == 200
        assert response.message == "success"

    def test_error_response(self):
        """Test error response"""
        from app.core.response import error_response
        response = error_response(code=500, message="Error")
        assert response.code == 500
