"""
Monitor API Endpoints
"""
from typing import List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from loguru import logger

from app.services.monitor_service import monitor_service
from app.services.notification_service import notification_service
from app.core.response import success_response
from app.core.exceptions import NotFoundException

router = APIRouter()


# Metrics Endpoints
@router.get("/metrics", summary="获取监控指标列表")
async def get_all_metrics(platform: Optional[str] = None):
    """
    获取所有账号的监控指标

    - **platform**: 按平台筛选
    """
    metrics = await monitor_service.get_all_metrics(platform)
    return success_response(data={
        "metrics": [
            {
                "account_id": m.account_id,
                "account_name": m.account_name,
                "platform": m.platform,
                "current": {
                    "followers": m.current.followers,
                    "likes": m.current.likes,
                    "views": m.current.views,
                    "videos": m.current.videos,
                    "engagement_rate": m.current.engagement_rate,
                    "timestamp": m.current.timestamp.isoformat()
                }
            }
            for m in metrics
        ],
        "total": len(metrics)
    })


@router.get("/metrics/{account_id}", summary="获取账号监控指标")
async def get_account_metrics(account_id: str):
    """获取指定账号的监控指标"""
    metrics = await monitor_service.get_metrics(account_id)
    if not metrics:
        raise NotFoundException(f"Account metrics not found: {account_id}")

    return success_response(data={
        "account_id": metrics.account_id,
        "account_name": metrics.account_name,
        "platform": metrics.platform,
        "current": {
            "followers": metrics.current.followers,
            "likes": metrics.current.likes,
            "views": metrics.current.views,
            "videos": metrics.current.videos,
            "engagement_rate": metrics.current.engagement_rate,
            "timestamp": metrics.current.timestamp.isoformat()
        },
        "history": [
            {
                "followers": h.followers,
                "likes": h.likes,
                "views": h.views,
                "timestamp": h.timestamp.isoformat()
            }
            for h in metrics.history
        ]
    })


@router.get("/metrics/{account_id}/trend", summary="获取指标趋势")
async def get_metric_trend(
    account_id: str,
    metric: str = "followers",
    days: int = 7
):
    """
    获取指标趋势数据

    - **account_id**: 账号ID
    - **metric**: 指标 (followers/likes/views/engagement_rate)
    - **days**: 天数
    """
    trend = await monitor_service.get_trend(account_id, metric, days)
    if not trend:
        raise NotFoundException(f"Account metrics not found: {account_id}")

    return success_response(data=trend)


@router.get("/metrics/compare", summary="对比账号指标")
async def compare_metrics(
    account_ids: List[str],
    metric: str = "followers"
):
    """
    对比多个账号的指标

    - **account_ids**: 账号ID列表
    - **metric**: 指标
    """
    comparison = await monitor_service.compare_accounts(account_ids, metric)
    return success_response(data={
        "metric": metric,
        "comparison": comparison
    })


# Alert Endpoints
@router.post("/alerts/check/{account_id}", summary="检查告警")
async def check_alerts(account_id: str):
    """检查指定账号是否触发告警"""
    alerts = await monitor_service.check_metrics(account_id)

    # Send notifications for new alerts
    for alert in alerts:
        if alert["status"] == "pending":
            await notification_service.send_alert_notification(alert)

    return success_response(data={
        "alerts": alerts,
        "total": len(alerts)
    })


@router.get("/alerts", summary="获取告警列表")
async def get_alerts(
    account_id: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50
):
    """
    获取告警列表

    - **account_id**: 按账号筛选
    - **status**: 按状态筛选 (pending/acknowledged/resolved)
    - **limit**: 返回数量
    """
    alerts = await monitor_service.get_alerts(account_id, status, limit)
    return success_response(data={
        "alerts": alerts,
        "total": len(alerts)
    })


@router.post("/alerts/{alert_id}/acknowledge", summary="确认告警")
async def acknowledge_alert(alert_id: str):
    """确认告警"""
    success = await monitor_service.acknowledge_alert(alert_id)
    if not success:
        raise NotFoundException(f"Alert not found: {alert_id}")
    return success_response(message="Alert acknowledged")


@router.post("/alerts/{alert_id}/resolve", summary="解决告警")
async def resolve_alert(alert_id: str):
    """解决告警"""
    success = await monitor_service.resolve_alert(alert_id)
    if not success:
        raise NotFoundException(f"Alert not found: {alert_id}")
    return success_response(message="Alert resolved")


# Notification Endpoints
@router.get("/notifications/channels", summary="获取通知渠道")
async def get_notification_channels():
    """获取所有通知渠道"""
    channels = await notification_service.get_channels()
    return success_response(data={"channels": channels})


@router.get("/notifications", summary="获取通知历史")
async def get_notifications(
    channel_id: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50
):
    """
    获取通知历史

    - **channel_id**: 按渠道筛选
    - **status**: 按状态筛选
    - **limit**: 返回数量
    """
    notifications = await notification_service.get_notifications(channel_id, status, limit)
    return success_response(data={
        "notifications": notifications,
        "total": len(notifications)
    })


@router.post("/notifications/send", summary="发送通知")
async def send_notification(
    channel_id: str,
    title: str,
    content: str,
    recipients: Optional[List[str]] = None
):
    """
    发送通知

    - **channel_id**: 渠道ID
    - **title**: 标题
    - **content**: 内容
    - **recipients**: 接收人列表
    """
    result = await notification_service.send_notification(
        channel_id=channel_id,
        title=title,
        content=content,
        recipients=recipients
    )
    return success_response(data=result)
