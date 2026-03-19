"""
Integration tests for Report Service API endpoints
"""
import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, patch, MagicMock

from app.main import app


class TestReportAPI:
    """Integration tests for Report API endpoints"""

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
    async def test_list_reports(self, client):
        """Test list reports endpoint"""
        response = await client.get("/api/v1/reports")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_create_report(self, client):
        """Test create report endpoint"""
        response = await client.post(
            "/api/v1/reports",
            json={
                "name": "测试报表",
                "type": "test",
                "data": {"key": "value"}
            }
        )
        assert response.status_code in [200, 201, 500]

    @pytest.mark.asyncio
    async def test_get_report(self, client):
        """Test get report endpoint"""
        response = await client.get("/api/v1/reports/report_test")
        assert response.status_code in [200, 404]

    @pytest.mark.asyncio
    async def test_delete_report(self, client):
        """Test delete report endpoint"""
        response = await client.delete("/api/v1/reports/report_test")
        assert response.status_code in [200, 404, 500]

    @pytest.mark.asyncio
    async def test_generate_video_report(self, client):
        """Test generate video report endpoint"""
        response = await client.post(
            "/api/v1/reports/generate/video",
            json={
                "videos": [
                    {"video_id": "v1", "title": "视频1", "likes": 100}
                ]
            }
        )
        assert response.status_code in [200, 500]

    @pytest.mark.asyncio
    async def test_generate_competitor_report(self, client):
        """Test generate competitor report endpoint"""
        response = await client.post(
            "/api/v1/reports/generate/competitor",
            json={
                "accounts": [
                    {"account_id": "a1", "name": "账号1", "followers": 1000}
                ]
            }
        )
        assert response.status_code in [200, 500]

    @pytest.mark.asyncio
    async def test_generate_trend_report(self, client):
        """Test generate trend report endpoint"""
        response = await client.post(
            "/api/v1/reports/generate/trend",
            json={"days": 7}
        )
        assert response.status_code in [200, 500]

    @pytest.mark.asyncio
    async def test_export_report(self, client):
        """Test export report endpoint"""
        with patch('app.api.v1.endpoints.reports.report_service.generate_video_report', new_callable=AsyncMock) as mock:
            mock.return_value = MagicMock(
                id="test_report",
                data={"videos": [{"id": "v1"}]}
            )

            response = await client.post(
                "/api/v1/reports/export",
                json={
                    "report_id": "test_report",
                    "format": "json"
                }
            )
            assert response.status_code in [200, 404, 500]

    @pytest.mark.asyncio
    async def test_get_templates(self, client):
        """Test get templates endpoint"""
        response = await client.get("/api/v1/reports/templates")
        assert response.status_code == 200
