"""
Insight Service - Comprehensive Tests
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime


class TestAIService:
    """Test AI service"""

    def test_ai_service_initialization(self):
        """Test AI service initialization"""
        from app.services.ai_service import AIService
        service = AIService()
        assert service.provider in ["openai", "deepseek"]

    def test_build_analysis_prompt_golden_hook(self):
        """Test golden hook prompt building"""
        from app.services.ai_service import AIService
        service = AIService()
        prompt = service._build_analysis_prompt("golden_3_seconds")
        assert "黄金3秒" in prompt
        assert "JSON格式" in prompt

    def test_build_analysis_prompt_structure(self):
        """Test structure prompt building"""
        from app.services.ai_service import AIService
        service = AIService()
        prompt = service._build_analysis_prompt("script_structure")
        assert "脚本结构" in prompt

    def test_build_analysis_prompt_sentiment(self):
        """Test sentiment prompt building"""
        from app.services.ai_service import AIService
        service = AIService()
        prompt = service._build_analysis_prompt("sentiment")
        assert "情感分析" in prompt

    def test_build_analysis_prompt_comprehensive(self):
        """Test comprehensive prompt building"""
        from app.services.ai_service import AIService
        service = AIService()
        prompt = service._build_analysis_prompt("comprehensive")
        assert "爆款潜力" in prompt

    def test_build_analysis_prompt_default(self):
        """Test default prompt"""
        from app.services.ai_service import AIService
        service = AIService()
        prompt = service._build_analysis_prompt("unknown_type")
        assert "爆款潜力" in prompt

    def test_parse_analysis_response_with_json(self):
        """Test parsing response with JSON"""
        from app.services.ai_service import AIService
        service = AIService()
        response = '{"key": "value", "number": 123}'
        result = service._parse_analysis_response(response, "golden_3_seconds")
        assert result["key"] == "value"
        assert result["number"] == 123

    def test_parse_analysis_response_without_json(self):
        """Test parsing response without JSON"""
        from app.services.ai_service import AIService
        service = AIService()
        response = "This is a plain text response"
        result = service._parse_analysis_response(response, "golden_3_seconds")
        assert "raw_response" in result


class TestInsightService:
    """Test insight service"""

    def test_insight_service_initialization(self):
        """Test insight service initialization"""
        from app.services.insight_service import InsightService
        service = InsightService()
        assert service.temp_dir is not None

    @pytest.mark.asyncio
    async def test_analyze_golden_hook(self):
        """Test golden hook analysis"""
        from app.services.insight_service import InsightService

        with patch('app.services.insight_service.ai_service.analyze_video', new_callable=AsyncMock) as mock_analyze:
            mock_analyze.return_value = {
                "hook_text": "测试文案",
                "hook_type": "提问",
                "analysis": "有效分析"
            }

            service = InsightService()
            result = await service.analyze_golden_hook(
                video_title="测试视频",
                video_script="这是视频脚本内容"
            )

            assert result["type"] == "golden_hook"
            assert "data" in result

    @pytest.mark.asyncio
    async def test_analyze_script_structure(self):
        """Test script structure analysis"""
        from app.services.insight_service import InsightService

        with patch('app.services.insight_service.ai_service.analyze_video', new_callable=AsyncMock) as mock_analyze:
            mock_analyze.return_value = {
                "segments": [],
                "structure_score": "85"
            }

            service = InsightService()
            result = await service.analyze_script_structure(
                video_title="测试视频",
                video_script="这是视频脚本内容"
            )

            assert result["type"] == "script_structure"

    @pytest.mark.asyncio
    async def test_analyze_sentiment(self):
        """Test sentiment analysis"""
        from app.services.insight_service import InsightService

        with patch('app.services.insight_service.ai_service.chat', new_callable=AsyncMock) as mock_chat:
            mock_chat.return_value = '{"total_comments": 10, "positive_count": 5, "neutral_count": 3, "negative_count": 2}'

            service = InsightService()
            result = await service.analyze_sentiment(
                comments=["好评", "不错", "差评"],
                video_title="测试视频"
            )

            assert result["type"] == "sentiment"

    @pytest.mark.asyncio
    async def test_generate_comprehensive_report(self):
        """Test comprehensive report generation"""
        from app.services.insight_service import InsightService

        with patch('app.services.insight_service.ai_service.analyze_video', new_callable=AsyncMock) as mock_analyze:
            with patch('app.services.insight_service.ai_service.chat', new_callable=AsyncMock) as mock_chat:
                mock_analyze.return_value = {"hook_text": "测试"}
                mock_chat.return_value = '{"overall_score": 85, "dimensions": {}}'

                service = InsightService()
                result = await service.generate_comprehensive_report(
                    video_title="测试视频",
                    video_script="脚本内容"
                )

                assert result["type"] == "comprehensive"
                assert result["video_title"] == "测试视频"

    @pytest.mark.asyncio
    async def test_generate_comprehensive_report_with_comments(self):
        """Test comprehensive report with comments"""
        from app.services.insight_service import InsightService

        with patch('app.services.insight_service.ai_service.analyze_video', new_callable=AsyncMock) as mock_analyze:
            with patch('app.services.insight_service.ai_service.chat', new_callable=AsyncMock) as mock_chat:
                mock_analyze.return_value = {"hook_text": "测试"}
                mock_chat.return_value = '{"overall_score": 85}'

                service = InsightService()
                result = await service.generate_comprehensive_report(
                    video_title="测试视频",
                    video_script="脚本内容",
                    comments=["好评", "差评"]
                )

                assert "analysis" in result

    @pytest.mark.asyncio
    async def test_extract_script_segments(self):
        """Test script segment extraction"""
        from app.services.insight_service import InsightService

        with patch('app.services.insight_service.ai_service.chat', new_callable=AsyncMock) as mock_chat:
            mock_chat.return_value = '{"segments": [{"start_time": 0, "end_time": 5}]}'

            service = InsightService()
            result = await service.extract_script_segments(
                video_script="测试脚本",
                duration=60
            )

            assert isinstance(result, list)


class TestExceptions:
    """Test exceptions"""

    def test_ai_exception(self):
        """Test AIException"""
        from app.core.exceptions import AIException
        exc = AIException("AI error", code=500)
        assert exc.message == "AI error"
        assert exc.code == 500


class TestResponseModel:
    """Test response models"""

    def test_success_response(self):
        """Test success response"""
        from app.core.response import success_response
        response = success_response(data={"insight": "test"})
        assert response.code == 200
        assert response.message == "success"

    def test_error_response(self):
        """Test error response"""
        from app.core.response import error_response
        response = error_response(code=500, message="Error")
        assert response.code == 500
