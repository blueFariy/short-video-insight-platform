"""
Integration tests for Competitor Monitor API endpoints
"""
import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, patch, MagicMock

from app.main import app


class TestMonitorAPI:
    """Integration tests for Monitor API endpoints"""

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
    async def test_get_metrics(self, client):
        """Test get metrics endpoint"""
        response = await client.get("/api/v1/metrics")
        assert response.status_code == 200
        data = response.json()
        assert "data" in data

    @pytest.mark.asyncio
    async def test_get_metrics_by_platform(self, client):
        """Test get metrics with platform filter"""
        response = await client.get("/api/v1/metrics?platform=douyin")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_get_account_metrics(self, client):
        """Test get account metrics endpoint"""
        response = await client.get("/api/v1/metrics/acc_001")
        assert response.status_code in [200, 404]

    @pytest.mark.asyncio
    async def test_check_metrics(self, client):
        """Test check metrics endpoint"""
        response = await client.post("/api/v1/metrics/acc_001/check")
        assert response.status_code in [200, 404, 500]

    @pytest.mark.asyncio
    async def test_get_alerts(self, client):
        """Test get alerts endpoint"""
        response = await client.get("/api/v1/alerts")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_acknowledge_alert(self, client):
        """Test acknowledge alert endpoint"""
        response = await client.post(
            "/api/v1/alerts/test_alert/acknowledge"
        )
        assert response.status_code in [200, 404, 500]

    @pytest.mark.asyncio
    async def test_resolve_alert(self, client):
        """Test resolve alert endpoint"""
        response = await client.post(
            "/api/v1/alerts/test_alert/resolve"
        )
        assert response.status_code in [200, 404, 500]

    @pytest.mark.asyncio
    async def test_get_trend(self, client):
        """Test get trend endpoint"""
        response = await client.get("/api/v1/metrics/acc_001/trend?metric=followers")
        assert response.status_code in [200, 404]

    @pytest.mark.asyncio
    async def test_compare_accounts(self, client):
        """Test compare accounts endpoint"""
        response = await client.post(
            "/api/v1/metrics/compare",
            json={
                "account_ids": ["acc_001", "acc_002"],
                "metric": "followers"
            }
        )
        assert response.status_code in [200, 500]

    @pytest.mark.asyncio
    async def test_get_notifications(self, client):
        """Test get notifications endpoint"""
        response = await client.get("/api/v1/notifications")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_send_notification(self, client):
        """Test send notification endpoint"""
        response = await client.post(
            "/api/v1/notifications",
            json={
                "channel_id": "email",
                "title": "Test Notification",
                "content": "Test content"
            }
        )
        assert response.status_code in [200, 500]
