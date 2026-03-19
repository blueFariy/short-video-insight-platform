"""
Monitoring Service
"""
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from loguru import logger
from dataclasses import dataclass, field


@dataclass
class MetricSnapshot:
    """Metric snapshot at a point in time"""
    timestamp: datetime
    followers: int = 0
    likes: int = 0
    views: int = 0
    videos: int = 0
    engagement_rate: float = 0.0


@dataclass
class AccountMetrics:
    """Account metrics with history"""
    account_id: str
    account_name: str
    platform: str
    current: MetricSnapshot
    history: List[MetricSnapshot] = field(default_factory=list)


@dataclass
class AlertRule:
    """Alert rule configuration"""
    id: str
    name: str
    metric: str  # followers, likes, views, engagement
    condition: str  # increase, decrease, spike, drop
    threshold: float  # percentage
    enabled: bool = True


class MonitorService:
    """Competitor monitoring service"""

    def __init__(self):
        self.metrics: Dict[str, AccountMetrics] = {}
        self.alerts: List[Dict[str, Any]] = []
        self.alert_rules: Dict[str, AlertRule] = {}
        self._init_demo_data()

    def _init_demo_data(self):
        """Initialize demo data"""
        # Demo accounts with historical data
        demo_accounts = [
            {
                "account_id": "acc_001",
                "account_name": "疯狂小杨哥",
                "platform": "douyin",
                "current": MetricSnapshot(
                    timestamp=datetime.now(),
                    followers=10000000,
                    likes=50000000,
                    views=200000000,
                    videos=500,
                    engagement_rate=0.05
                )
            },
            {
                "account_id": "acc_002",
                "account_name": "罗永浩",
                "platform": "douyin",
                "current": MetricSnapshot(
                    timestamp=datetime.now(),
                    followers=2000000,
                    likes=10000000,
                    views=50000000,
                    videos=300,
                    engagement_rate=0.04
                )
            },
            {
                "account_id": "acc_003",
                "account_name": "老高与小茉",
                "platform": "bilibili",
                "current": MetricSnapshot(
                    timestamp=datetime.now(),
                    followers=500000,
                    likes=8000000,
                    views=100000000,
                    videos=200,
                    engagement_rate=0.08
                )
            }
        ]

        for acc in demo_accounts:
            # Add historical data
            history = []
            for i in range(7):  # 7 days of history
                history.append(MetricSnapshot(
                    timestamp=datetime.now() - timedelta(days=i),
                    followers=acc["current"].followers - i * 10000,
                    likes=acc["current"].likes - i * 50000,
                    views=acc["current"].views - i * 2000000,
                    videos=acc["current"].videos - i * 2,
                    engagement_rate=acc["current"].engagement_rate
                ))

            metrics = AccountMetrics(
                account_id=acc["account_id"],
                account_name=acc["account_name"],
                platform=acc["platform"],
                current=acc["current"],
                history=history
            )
            self.metrics[acc["account_id"]] = metrics

        # Demo alert rules
        self.alert_rules = {
            "rule_1": AlertRule(
                id="rule_1",
                name="粉丝快速增长",
                metric="followers",
                condition="increase",
                threshold=10.0,
                enabled=True
            ),
            "rule_2": AlertRule(
                id="rule_2",
                name="播放量暴跌",
                metric="views",
                condition="drop",
                threshold=20.0,
                enabled=True
            ),
            "rule_3": AlertRule(
                id="rule_3",
                name="互动率异常",
                metric="engagement",
                condition="drop",
                threshold=15.0,
                enabled=True
            )
        }

    async def get_metrics(self, account_id: str) -> Optional[AccountMetrics]:
        """Get account metrics"""
        return self.metrics.get(account_id)

    async def get_all_metrics(self, platform: Optional[str] = None) -> List[AccountMetrics]:
        """Get all account metrics"""
        if platform:
            return [m for m in self.metrics.values() if m.platform == platform]
        return list(self.metrics.values())

    async def check_metrics(self, account_id: str) -> List[Dict[str, Any]]:
        """Check metrics against alert rules"""
        account_metrics = self.metrics.get(account_id)
        if not account_metrics:
            return []

        triggered_alerts = []
        current = account_metrics.current

        for rule in self.alert_rules.values():
            if not rule.enabled:
                continue

            # Calculate change from previous snapshot
            if account_metrics.history:
                previous = account_metrics.history[0]
                change_pct = self._calculate_change(
                    getattr(current, rule.metric),
                    getattr(previous, rule.metric)
                )

                # Check if rule triggered
                triggered = False
                if rule.condition == "increase" and change_pct > rule.threshold:
                    triggered = True
                elif rule.condition == "drop" and change_pct < -rule.threshold:
                    triggered = True
                elif rule.condition == "spike" and abs(change_pct) > rule.threshold:
                    triggered = True

                if triggered:
                    alert = {
                        "id": f"alert_{datetime.now().timestamp()}",
                        "account_id": account_id,
                        "account_name": account_metrics.account_name,
                        "rule": rule.name,
                        "metric": rule.metric,
                        "condition": rule.condition,
                        "threshold": rule.threshold,
                        "actual_change": change_pct,
                        "timestamp": datetime.now().isoformat(),
                        "status": "pending"
                    }
                    triggered_alerts.append(alert)
                    self.alerts.append(alert)

        return triggered_alerts

    def _calculate_change(self, current: float, previous: float) -> float:
        """Calculate percentage change"""
        if previous == 0:
            return 0.0
        return ((current - previous) / previous) * 100

    async def get_alerts(
        self,
        account_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get alerts"""
        alerts = self.alerts

        if account_id:
            alerts = [a for a in alerts if a["account_id"] == account_id]
        if status:
            alerts = [a for a in alerts if a["status"] == status]

        return alerts[-limit:]

    async def acknowledge_alert(self, alert_id: str) -> bool:
        """Acknowledge an alert"""
        for alert in self.alerts:
            if alert["id"] == alert_id:
                alert["status"] = "acknowledged"
                return True
        return False

    async def resolve_alert(self, alert_id: str) -> bool:
        """Resolve an alert"""
        for alert in self.alerts:
            if alert["id"] == alert_id:
                alert["status"] = "resolved"
                return True
        return False

    async def get_trend(
        self,
        account_id: str,
        metric: str,
        days: int = 7
    ) -> Dict[str, Any]:
        """Get trend data for a metric"""
        account_metrics = self.metrics.get(account_id)
        if not account_metrics:
            return {}

        history = account_metrics.history[:days]
        if not history:
            return {}

        values = [getattr(h, metric) for h in history]
        timestamps = [h.timestamp.isoformat() for h in history]

        # Calculate trend
        if len(values) >= 2:
            change = values[-1] - values[0]
            change_pct = self._calculate_change(values[-1], values[0])
        else:
            change = 0
            change_pct = 0

        return {
            "metric": metric,
            "values": values,
            "timestamps": timestamps,
            "current": values[-1] if values else 0,
            "change": change,
            "change_percentage": change_pct,
            "trend": "up" if change > 0 else "down" if change < 0 else "stable"
        }

    async def compare_accounts(
        self,
        account_ids: List[str],
        metric: str
    ) -> List[Dict[str, Any]]:
        """Compare multiple accounts"""
        comparison = []
        for account_id in account_ids:
            account_metrics = self.metrics.get(account_id)
            if account_metrics:
                comparison.append({
                    "account_id": account_id,
                    "account_name": account_metrics.account_name,
                    "platform": account_metrics.platform,
                    "value": getattr(account_metrics.current, metric)
                })

        # Sort by value
        comparison.sort(key=lambda x: x["value"], reverse=True)

        return comparison


monitor_service = MonitorService()
