"""
Report Service - Comprehensive Tests
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime


class TestReport:
    """Test Report model"""

    def test_report_creation(self):
        """Test report creation"""
        from app.services.report_service import Report
        report = Report(
            id="report_001",
            name="测试报表",
            type="test",
            description="测试描述",
            data={"key": "value"}
        )
        assert report.id == "report_001"
        assert report.name == "测试报表"
        assert report.created_by == "system"


class TestReportTemplate:
    """Test ReportTemplate model"""

    def test_report_template_creation(self):
        """Test report template creation"""
        from app.services.report_service import ReportTemplate
        template = ReportTemplate(
            id="template_001",
            name="测试模板",
            type="test",
            description="测试描述",
            fields=["field1", "field2"]
        )
        assert template.id == "template_001"
        assert len(template.fields) == 2


class TestReportService:
    """Test report service"""

    def test_report_service_initialization(self):
        """Test report service initialization"""
        from app.services.report_service import ReportService
        service = ReportService()
        assert len(service.templates) > 0

    @pytest.mark.asyncio
    async def test_create_report(self):
        """Test report creation"""
        from app.services.report_service import ReportService
        service = ReportService()
        report = await service.create_report(
            name="测试报表",
            report_type="test",
            data={"test": "data"}
        )
        assert report.name == "测试报表"
        assert report.id is not None

    @pytest.mark.asyncio
    async def test_get_report(self):
        """Test get report"""
        from app.services.report_service import ReportService
        service = ReportService()
        report = await service.create_report(
            name="测试报表",
            report_type="test",
            data={}
        )
        retrieved = await service.get_report(report.id)
        assert retrieved is not None
        assert retrieved.id == report.id

    @pytest.mark.asyncio
    async def test_get_report_not_found(self):
        """Test get non-existent report"""
        from app.services.report_service import ReportService
        service = ReportService()
        report = await service.get_report("nonexistent")
        assert report is None

    @pytest.mark.asyncio
    async def test_list_reports(self):
        """Test list reports"""
        from app.services.report_service import ReportService
        service = ReportService()
        await service.create_report(name="报告1", report_type="test", data={})
        await service.create_report(name="报告2", report_type="test", data={})
        reports = await service.list_reports()
        assert len(reports) >= 2

    @pytest.mark.asyncio
    async def test_list_reports_by_type(self):
        """Test list reports by type"""
        from app.services.report_service import ReportService
        service = ReportService()
        await service.create_report(name="类型1", report_type="type_a", data={})
        await service.create_report(name="类型2", report_type="type_b", data={})
        reports = await service.list_reports(report_type="type_a")
        assert all(r.type == "type_a" for r in reports)

    @pytest.mark.asyncio
    async def test_delete_report(self):
        """Test delete report"""
        from app.services.report_service import ReportService
        service = ReportService()
        report = await service.create_report(name="待删除", report_type="test", data={})
        result = await service.delete_report(report.id)
        assert result is True

    @pytest.mark.asyncio
    async def test_generate_video_report(self):
        """Test video report generation"""
        from app.services.report_service import ReportService
        service = ReportService()
        videos = [
            {"video_id": "v1", "title": "视频1", "likes": 100, "comments": 10, "views": 1000},
            {"video_id": "v2", "title": "视频2", "likes": 200, "comments": 20, "views": 2000}
        ]
        report = await service.generate_video_report(videos)
        assert report.type == "video_analysis"
        assert "summary" in report.data

    @pytest.mark.asyncio
    async def test_generate_competitor_report(self):
        """Test competitor report generation"""
        from app.services.report_service import ReportService
        service = ReportService()
        accounts = [
            {"account_id": "a1", "name": "账号1", "platform": "douyin", "followers": 1000},
            {"account_id": "a2", "name": "账号2", "platform": "bilibili", "followers": 2000}
        ]
        report = await service.generate_competitor_report(accounts)
        assert report.type == "competitor_overview"

    @pytest.mark.asyncio
    async def test_generate_trend_report(self):
        """Test trend report generation"""
        from app.services.report_service import ReportService
        service = ReportService()
        report = await service.generate_trend_report(days=7)
        assert report.type == "trend_report"
        assert "trend_data" in report.data

    def test_get_templates(self):
        """Test get templates"""
        from app.services.report_service import ReportService
        service = ReportService()
        templates = service.get_templates()
        assert len(templates) > 0

    def test_get_template(self):
        """Test get template"""
        from app.services.report_service import ReportService
        service = ReportService()
        template = service.get_template("video_analysis")
        assert template is not None
        assert template.id == "video_analysis"

    def test_get_template_not_found(self):
        """Test get non-existent template"""
        from app.services.report_service import ReportService
        service = ReportService()
        template = service.get_template("nonexistent")
        assert template is None


class TestExportService:
    """Test export service"""

    def test_export_service_initialization(self):
        """Test export service initialization"""
        from app.services.export_service import ExportService
        service = ExportService()
        assert service.export_dir is not None

    @pytest.mark.asyncio
    async def test_export_to_json(self):
        """Test JSON export"""
        from app.services.export_service import ExportService
        service = ExportService()
        data = {"key": "value", "number": 123}
        result = await service.export_to_json(data)
        assert "filename" in result
        assert result["filename"].endswith(".json")

    @pytest.mark.asyncio
    async def test_export_to_csv(self):
        """Test CSV export"""
        from app.services.export_service import ExportService
        service = ExportService()
        data = [
            {"name": "Alice", "age": 30},
            {"name": "Bob", "age": 25}
        ]
        result = await service.export_to_csv(data)
        assert "filename" in result
        assert result["filename"].endswith(".csv")
        assert result["rows"] == 2

    @pytest.mark.asyncio
    async def test_export_to_csv_empty_data(self):
        """Test CSV export with empty data"""
        from app.services.export_service import ExportService
        service = ExportService()
        with pytest.raises(ValueError):
            await service.export_to_csv([])

    @pytest.mark.asyncio
    async def test_export_to_excel(self):
        """Test Excel export"""
        from app.services.export_service import ExportService
        service = ExportService()
        data = [{"name": "Test"}]
        result = await service.export_to_excel(data)
        assert "filename" in result

    @pytest.mark.asyncio
    async def test_export_report_json(self):
        """Test report export as JSON"""
        from app.services.export_service import ExportService
        service = ExportService()
        data = {"report": "test"}
        result = await service.export_report(data, format="json")
        assert result["filename"].endswith(".json")

    @pytest.mark.asyncio
    async def test_export_report_csv(self):
        """Test report export as CSV"""
        from app.services.export_service import ExportService
        service = ExportService()
        data = {"videos": [{"id": "v1", "title": "Test"}]}
        result = await service.export_report(data, format="csv")
        assert result["filename"].endswith(".csv")

    def test_get_export_formats(self):
        """Test get export formats"""
        from app.services.export_service import ExportService
        service = ExportService()
        formats = service.get_export_formats()
        assert "json" in formats
        assert "csv" in formats
        assert "excel" in formats


class TestStatisticsService:
    """Test statistics service"""

    @pytest.mark.asyncio
    async def test_calculate_video_statistics(self):
        """Test video statistics calculation"""
        from app.services.statistics_service import StatisticsService
        service = StatisticsService()
        videos = [
            {"likes": 100, "comments": 10, "views": 1000},
            {"likes": 200, "comments": 20, "views": 2000}
        ]
        stats = await service.calculate_video_statistics(videos)
        assert stats["total_videos"] == 2
        assert stats["total_likes"] == 300

    @pytest.mark.asyncio
    async def test_calculate_engagement_rate(self):
        """Test engagement rate calculation"""
        from app.services.statistics_service import StatisticsService
        service = StatisticsService()
        rate = await service.calculate_engagement_rate(likes=100, comments=10, views=1000)
        assert rate == 0.11  # (100 + 10) / 1000


class TestResponseModel:
    """Test response models"""

    def test_success_response(self):
        """Test success response"""
        from app.core.response import success_response
        response = success_response(data={"report": "test"})
        assert response.code == 200
        assert response.message == "success"

    def test_error_response(self):
        """Test error response"""
        from app.core.response import error_response
        response = error_response(code=500, message="Error")
        assert response.code == 500
