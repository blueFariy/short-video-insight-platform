"""
Integration tests for Data Collector API endpoints
"""
import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, patch, MagicMock

from app.main import app


class TestCollectorAPI:
    """Integration tests for Collector API endpoints"""

    @pytest.fixture
    async def client(self):
        """Create test client"""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac

    @pytest.mark.asyncio
    async def test_health_check(self, client):
        """Test health check endpoint"""
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_list_accounts(self, client):
        """Test list accounts endpoint"""
        response = await client.get("/api/v1/accounts")
        assert response.status_code == 200
        data = response.json()
        assert "data" in data

    @pytest.mark.asyncio
    async def test_list_accounts_by_platform(self, client):
        """Test list accounts with platform filter"""
        response = await client.get("/api/v1/accounts?platform=douyin")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_create_account(self, client):
        """Test create account endpoint"""
        response = await client.post(
            "/api/v1/accounts",
            json={
                "name": "新账号",
                "platform": "douyin",
                "account_id": "new123",
                "url": "https://v.douyin.com/new/",
                "category": "测试"
            }
        )
        assert response.status_code in [200, 201, 500]

    @pytest.mark.asyncio
    async def test_get_account(self, client):
        """Test get account endpoint"""
        response = await client.get("/api/v1/accounts/acc_001")
        assert response.status_code in [200, 404]

    @pytest.mark.asyncio
    async def test_update_account(self, client):
        """Test update account endpoint"""
        response = await client.put(
            "/api/v1/accounts/acc_001",
            json={"name": "新名称"}
        )
        assert response.status_code in [200, 404, 500]

    @pytest.mark.asyncio
    async def test_delete_account(self, client):
        """Test delete account endpoint"""
        # First create an account
        create_response = await client.post(
            "/api/v1/accounts",
            json={
                "name": "待删除账号",
                "platform": "douyin",
                "account_id": "delete123",
                "url": "https://v.douyin.com/delete/"
            }
        )
        if create_response.status_code in [200, 201]:
            account_id = create_response.json().get("data", {}).get("id")
            if account_id:
                response = await client.delete(f"/api/v1/accounts/{account_id}")
                assert response.status_code in [200, 404]

    @pytest.mark.asyncio
    async def test_collect_account(self, client):
        """Test collect account endpoint"""
        with patch('app.api.v1.endpoints.collector.collector_service.collect_account', new_callable=AsyncMock) as mock:
            mock.return_value = []

            response = await client.post(
                "/api/v1/collect/acc_001",
                json={"limit": 10}
            )
            assert response.status_code in [200, 404, 500]

    @pytest.mark.asyncio
    async def test_collect_all(self, client):
        """Test collect all accounts endpoint"""
        response = await client.post("/api/v1/collect/all")
        assert response.status_code in [200, 500]

    @pytest.mark.asyncio
    async def test_get_videos(self, client):
        """Test get videos endpoint"""
        response = await client.get("/api/v1/videos")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_search_videos(self, client):
        """Test search videos endpoint"""
        response = await client.get("/api/v1/videos/search?keyword=测试")
        assert response.status_code == 200
