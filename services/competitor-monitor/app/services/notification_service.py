"""
Notification Service
"""
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
from loguru import logger
from dataclasses import dataclass


@dataclass
class NotificationChannel:
    """Notification channel configuration"""
    id: str
    name: str
    type: str  # email, webhook, sms
    config: Dict[str, Any]
    enabled: bool = True


@dataclass
class Notification:
    """Notification message"""
    id: str
    title: str
    content: str
    channel: str
    recipients: List[str]
    status: str = "pending"  # pending, sent, failed
    sent_at: Optional[datetime] = None
    created_at: datetime = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()


class NotificationService:
    """Notification service"""

    def __init__(self):
        self.channels: Dict[str, NotificationChannel] = {}
        self.notifications: List[Notification] = []
        self._init_demo_channels()

    def _init_demo_channels(self):
        """Initialize demo notification channels"""
        self.channels = {
            "email": NotificationChannel(
                id="email",
                name="Email Notification",
                type="email",
                config={
                    "smtp_host": "smtp.example.com",
                    "smtp_port": 587,
                    "from_address": "alerts@example.com"
                },
                enabled=True
            ),
            "webhook": NotificationChannel(
                id="webhook",
                name="Webhook Notification",
                type="webhook",
                config={
                    "url": "https://example.com/webhook",
                    "method": "POST"
                },
                enabled=True
            )
        }

    async def send_notification(
        self,
        channel_id: str,
        title: str,
        content: str,
        recipients: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Send a notification"""
        channel = self.channels.get(channel_id)
        if not channel or not channel.enabled:
            logger.warning(f"Channel {channel_id} not found or disabled")
            return {"success": False, "error": "Channel not available"}

        # Create notification
        notification = Notification(
            id=f"notif_{datetime.now().timestamp()}",
            title=title,
            content=content,
            channel=channel_id,
            recipients=recipients or []
        )

        try:
            # Send based on channel type
            if channel.type == "email":
                await self._send_email(channel, notification)
            elif channel.type == "webhook":
                await self._send_webhook(channel, notification)
            else:
                raise ValueError(f"Unknown channel type: {channel.type}")

            notification.status = "sent"
            notification.sent_at = datetime.now()
            logger.info(f"Notification sent: {notification.id}")

        except Exception as e:
            notification.status = "failed"
            logger.error(f"Failed to send notification: {e}")

        self.notifications.append(notification)
        return {
            "success": notification.status == "sent",
            "notification_id": notification.id,
            "status": notification.status
        }

    async def _send_email(self, channel: NotificationChannel, notification: Notification):
        """Send email notification (simulated)"""
        # In production, use aiosmtplib or similar
        logger.info(f"[EMAIL] To: {notification.recipients}, Title: {notification.title}")
        await asyncio.sleep(0.1)  # Simulate network delay

    async def _send_webhook(self, channel: NotificationChannel, notification: Notification):
        """Send webhook notification (simulated)"""
        import aiohttp
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "title": notification.title,
                    "content": notification.content,
                    "timestamp": notification.created_at.isoformat()
                }
                # In production, actually send the request
                logger.info(f"[WEBHOOK] URL: {channel.config['url']}, Payload: {payload}")
        except Exception as e:
            logger.warning(f"Webhook simulation: {e}")

    async def send_alert_notification(
        self,
        alert: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Send notification for an alert"""
        title = f"监控告警: {alert.get('rule', 'Unknown')}"
        content = f"""
账号: {alert.get('account_name', 'Unknown')}
指标: {alert.get('metric', 'Unknown')}
条件: {alert.get('condition', 'Unknown')}
阈值: {alert.get('threshold', 0)}%
实际变化: {alert.get('actual_change', 0):.2f}%
时间: {alert.get('timestamp', '')}
        """.strip()

        results = {}
        for channel_id, channel in self.channels.items():
            if channel.enabled:
                result = await self.send_notification(
                    channel_id=channel_id,
                    title=title,
                    content=content
                )
                results[channel_id] = result

        return results

    async def get_channels(self) -> List[Dict[str, Any]]:
        """Get all notification channels"""
        return [
            {
                "id": c.id,
                "name": c.name,
                "type": c.type,
                "enabled": c.enabled
            }
            for c in self.channels.values()
        ]

    async def get_notifications(
        self,
        channel_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get notification history"""
        results = self.notifications

        if channel_id:
            results = [n for n in results if n.channel == channel_id]
        if status:
            results = [n for n in results if n.status == status]

        results = results[-limit:]
        return [
            {
                "id": n.id,
                "title": n.title,
                "channel": n.channel,
                "status": n.status,
                "sent_at": n.sent_at.isoformat() if n.sent_at else None,
                "created_at": n.created_at.isoformat()
            }
            for n in results
        ]


notification_service = NotificationService()
