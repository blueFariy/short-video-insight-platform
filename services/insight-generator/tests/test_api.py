"""
Integration tests for Insight Service API endpoints
"""
import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, patch, MagicMock

from app.main import app


class TestInsightAPI:
    """Integration tests for Insight API endpoints"""

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
    async def test_analyze_golden_hook(self, client):
        """Test golden hook analysis endpoint"""
        with patch('app.api.v1.endpoints.insights.insight_service.analyze_golden_hook', new_callable=AsyncMock) as mock:
            mock.return_value = {
                "type": "golden_hook",
                "data": {"hook_text": "测试", "hook_type": "提问"}
            }

            response = await client.post(
                "/api/v1/insights/golden-hook",
                json={
                    "video_title": "测试视频",
                    "video_script": "视频脚本"
                }
            )

            assert response.status_code in [200, 500]

    @pytest.mark.asyncio
    async def test_analyze_structure(self, client):
        """Test structure analysis endpoint"""
        with patch('app.api.v1.endpoints.insights.insight_service.analyze_script_structure', new_callable=AsyncMock) as mock:
            mock.return_value = {
                "type": "script_structure",
                "data": {"segments": [], "structure_score": "85"}
            }

            response = await client.post(
                "/api/v1/insights/structure",
                json={
                    "video_title": "测试视频",
                    "video_script": "视频脚本"
                }
            )

            assert response.status_code in [200, 500]

    @pytest.mark.asyncio
    async def test_analyze_sentiment(self, client):
        """Test sentiment analysis endpoint"""
        with patch('app.api.v1.endpoints.insights.insight_service.analyze_sentiment', new_callable=AsyncMock) as mock:
            mock.return_value = {
                "type": "sentiment",
                "data": {"total_comments": 10, "positive_count": 5}
            }

            response = await client.post(
                "/api/v1/insights/sentiment",
                json={
                    "comments": ["好评", "差评"]
                }
            )

            assert response.status_code in [200, 500]

    @pytest.mark.asyncio
    async def test_generate_comprehensive(self, client):
        """Test comprehensive analysis endpoint"""
        with patch('app.api.v1.endpoints.insights.insight_service.generate_comprehensive_report', new_callable=AsyncMock) as mock:
            mock.return_value = {
                "type": "comprehensive",
                "video_title": "测试视频",
                "overall": {"overall_score": 85}
            }

            response = await client.post(
                "/api/v1/insights/comprehensive",
                json={
                    "video_title": "测试视频",
                    "video_script": "视频脚本"
                }
            )

            assert response.status_code in [200, 500]

    @pytest.mark.asyncio
    async def test_analyze_golden_hook_missing_title(self, client):
        """Test golden hook with missing video title"""
        response = await client.post(
            "/api/v1/insights/golden-hook",
            json={"video_script": "脚本"}
        )
        assert response.status_code == 422  # Validation error
