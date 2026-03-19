"""
Competitor Monitor Service - Comprehensive Tests
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta


class TestMetricSnapshot:
    """Test MetricSnapshot model"""

    def test_metric_snapshot_creation(self):
        """Test metric snapshot creation"""
        from app.services.monitor_service import MetricSnapshot
        snapshot = MetricSnapshot(
            timestamp=datetime.now(),
            followers=10000,
            likes=50000,
            views=100000,
            videos=100,
            engagement_rate=0.05
        )
        assert snapshot.followers == 10000
        assert snapshot.likes == 50000
        assert snapshot.engagement_rate == 0.05


class TestAccountMetrics:
    """Test AccountMetrics model"""

    def test_account_metrics_creation(self):
        """Test account metrics creation"""
        from app.services.monitor_service import AccountMetrics, MetricSnapshot
        snapshot = MetricSnapshot(
            timestamp=datetime.now(),
            followers=10000
        )
        metrics = AccountMetrics(
            account_id="test_001",
            account_name="测试账号",
            platform="douyin",
            current=snapshot
        )
        assert metrics.account_id == "test_001"
        assert metrics.platform == "douyin"


class TestAlertRule:
    """Test AlertRule model"""

    def test_alert_rule_creation(self):
        """Test alert rule creation"""
        from app.services.monitor_service import AlertRule
        rule = AlertRule(
            id="rule_001",
            name="粉丝增长告警",
            metric="followers",
            condition="increase",
            threshold=10.0
        )
        assert rule.id == "rule_001"
        assert rule.metric == "followers"
        assert rule.enabled is True


class TestMonitorService:
    """Test monitor service"""

    def test_monitor_service_initialization(self):
        """Test monitor service initialization"""
        from app.services.monitor_service import MonitorService
        service = MonitorService()
        assert len(service.metrics) > 0  # Demo data
        assert len(service.alert_rules) > 0

    @pytest.mark.asyncio
    async def test_get_metrics(self):
        """Test get metrics"""
        from app.services.monitor_service import MonitorService
        service = MonitorService()
        metrics = await service.get_metrics("acc_001")
        assert metrics is not None
        assert metrics.account_name == "疯狂小杨哥"

    @pytest.mark.asyncio
    async def test_get_metrics_not_found(self):
        """Test get non-existent metrics"""
        from app.services.monitor_service import MonitorService
        service = MonitorService()
        metrics = await service.get_metrics("nonexistent")
        assert metrics is None

    @pytest.mark.asyncio
    async def test_get_all_metrics(self):
        """Test get all metrics"""
        from app.services.monitor_service import MonitorService
        service = MonitorService()
        metrics = await service.get_all_metrics()
        assert len(metrics) > 0

    @pytest.mark.asyncio
    async def test_get_all_metrics_by_platform(self):
        """Test get metrics by platform"""
        from app.services.monitor_service import MonitorService
        service = MonitorService()
        metrics = await service.get_all_metrics(platform="douyin")
        assert all(m.platform == "douyin" for m in metrics)

    def test_calculate_change(self):
        """Test percentage change calculation"""
        from app.services.monitor_service import MonitorService
        service = MonitorService()
        change = service._calculate_change(110, 100)
        assert change == 10.0

    def test_calculate_change_zero_previous(self):
        """Test calculation with zero previous value"""
        from app.services.monitor_service import MonitorService
        service = MonitorService()
        change = service._calculate_change(100, 0)
        assert change == 0.0

    @pytest.mark.asyncio
    async def test_check_metrics(self):
        """Test check metrics"""
        from app.services.monitor_service import MonitorService
        service = MonitorService()
        alerts = await service.check_metrics("acc_001")
        assert isinstance(alerts, list)

    @pytest.mark.asyncio
    async def test_get_alerts(self):
        """Test get alerts"""
        from app.services.monitor_service import MonitorService
        service = MonitorService()
        alerts = await service.get_alerts()
        assert isinstance(alerts, list)

    @pytest.mark.asyncio
    async def test_get_alerts_by_account(self):
        """Test get alerts by account"""
        from app.services.monitor_service import MonitorService
        service = MonitorService()
        alerts = await service.get_alerts(account_id="acc_001")
        assert isinstance(alerts, list)

    @pytest.mark.asyncio
    async def test_acknowledge_alert(self):
        """Test acknowledge alert"""
        from app.services.monitor_service import MonitorService
        service = MonitorService()
        # Add a test alert
        service.alerts.append({
            "id": "test_alert",
            "status": "pending"
        })
        result = await service.acknowledge_alert("test_alert")
        assert result is True

    @pytest.mark.asyncio
    async def test_resolve_alert(self):
        """Test resolve alert"""
        from app.services.monitor_service import MonitorService
        service = MonitorService()
        service.alerts.append({
            "id": "test_alert_2",
            "status": "pending"
        })
        result = await service.resolve_alert("test_alert_2")
        assert result is True

    @pytest.mark.asyncio
    async def test_get_trend(self):
        """Test get trend"""
        from app.services.monitor_service import MonitorService
        service = MonitorService()
        trend = await service.get_trend("acc_001", "followers", days=7)
        assert "trend" in trend

    @pytest.mark.asyncio
    async def test_get_trend_not_found(self):
        """Test get trend for non-existent account"""
        from app.services.monitor_service import MonitorService
        service = MonitorService()
        trend = await service.get_trend("nonexistent", "followers")
        assert trend == {}

    @pytest.mark.asyncio
    async def test_compare_accounts(self):
        """Test compare accounts"""
        from app.services.monitor_service import MonitorService
        service = MonitorService()
        comparison = await service.compare_accounts(
            account_ids=["acc_001", "acc_002"],
            metric="followers"
        )
        assert len(comparison) == 2


class TestNotificationChannel:
    """Test NotificationChannel model"""

    def test_notification_channel_creation(self):
        """Test notification channel creation"""
        from app.services.notification_service import NotificationChannel
        channel = NotificationChannel(
            id="test_channel",
            name="Test Channel",
            type="email",
            config={"smtp_host": "test.com"}
        )
        assert channel.id == "test_channel"
        assert channel.type == "email"
        assert channel.enabled is True


class TestNotification:
    """Test Notification model"""

    def test_notification_creation(self):
        """Test notification creation"""
        from app.services.notification_service import Notification
        notification = Notification(
            id="notif_001",
            title="Test Title",
            content="Test Content",
            channel="email",
            recipients=["test@example.com"]
        )
        assert notification.id == "notif_001"
        assert notification.status == "pending"
        assert notification.created_at is not None


class TestNotificationService:
    """Test notification service"""

    def test_notification_service_initialization(self):
        """Test notification service initialization"""
        from app.services.notification_service import NotificationService
        service = NotificationService()
        assert len(service.channels) > 0

    @pytest.mark.asyncio
    async def test_send_notification(self):
        """Test send notification"""
        from app.services.notification_service import NotificationService
        service = NotificationService()
        result = await service.send_notification(
            channel_id="email",
            title="Test Notification",
            content="Test content",
            recipients=["test@example.com"]
        )
        assert "success" in result

    @pytest.mark.asyncio
    async def test_send_notification_disabled_channel(self):
        """Test send notification with disabled channel"""
        from app.services.notification_service import NotificationService, NotificationChannel
        service = NotificationService()
        # Disable the channel
        service.channels["email"].enabled = False
        result = await service.send_notification(
            channel_id="email",
            title="Test",
            content="Test"
        )
        assert result["success"] is False

    @pytest.mark.asyncio
    async def test_send_alert_notification(self):
        """Test send alert notification"""
        from app.services.notification_service import NotificationService
        service = NotificationService()
        alert = {
            "rule": "粉丝增长",
            "account_name": "测试账号",
            "metric": "followers",
            "condition": "increase",
            "threshold": 10.0,
            "actual_change": 15.0,
            "timestamp": datetime.now().isoformat()
        }
        result = await service.send_alert_notification(alert)
        assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_get_channels(self):
        """Test get channels"""
        from app.services.notification_service import NotificationService
        service = NotificationService()
        channels = await service.get_channels()
        assert len(channels) > 0

    @pytest.mark.asyncio
    async def test_get_notifications(self):
        """Test get notifications"""
        from app.services.notification_service import NotificationService
        service = NotificationService()
        notifications = await service.get_notifications()
        assert isinstance(notifications, list)


class TestResponseModel:
    """Test response models"""

    def test_success_response(self):
        """Test success response"""
        from app.core.response import success_response
        response = success_response(data={"monitor": "test"})
        assert response.code == 200
        assert response.message == "success"

    def test_error_response(self):
        """Test error response"""
        from app.core.response import error_response
        response = error_response(code=500, message="Error")
        assert response.code == 500
