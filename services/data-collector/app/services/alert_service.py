"""
Alert Service - 预警推送服务
"""
from typing import List, Dict, Any, Optional
from loguru import logger
from dataclasses import dataclass

from app.schemas import Video, ViralSignal
from app.core.config import settings


@dataclass
class AlertContent:
    """预警内容"""
    title: str
    body: str
    level: str  # 'yellow', 'orange', 'red'
    video: Dict[str, Any]
    signal: Dict[str, Any]


class AlertService:
    """预警推送服务"""

    def __init__(self):
        self.push_providers = {
            'app': AppPushProvider(),
            'email': EmailPushProvider(),
            'wechat': WeChatPushProvider(),
            'sms': SMSPushProvider()
        }

    async def send_viral_alert(
        self,
        user_id: int,
        video: Video,
        signal: ViralSignal
    ) -> Dict[str, Any]:
        """发送爆款预警"""

        # 1. 构建预警内容
        content = self._build_alert_content(video, signal)

        # 2. 获取用户通知偏好
        user_prefs = self._get_user_preferences(user_id)

        # 3. 根据预警级别和用户偏好选择推送渠道
        channels = self._determine_channels(content.level, user_prefs)

        # 4. 多渠道推送
        results = []
        for channel in channels:
            try:
                provider = self.push_providers.get(channel)
                if provider:
                    result = await provider.send(
                        user_id=user_id,
                        title=content.title,
                        body=content.body,
                        data={
                            "video": video.to_dict(),
                            "signal": signal.to_dict()
                        }
                    )
                    results.append({"channel": channel, "status": "sent", "result": result})
                else:
                    results.append({"channel": channel, "status": "failed", "error": "Provider not found"})
            except Exception as e:
                logger.error(f"Failed to send alert via {channel}: {e}")
                results.append({"channel": channel, "status": "error", "error": str(e)})

        # 5. 记录预警日志
        await self._log_alert(user_id, video.video_id, signal, results)

        return {
            "status": "sent",
            "video_id": video.video_id,
            "alert_level": content.level,
            "channels": results
        }

    def _build_alert_content(
        self,
        video: Video,
        signal: ViralSignal
    ) -> AlertContent:
        """构建预警内容"""

        # 格式化数字
        play_count = self._format_number(video.metrics.play_count)
        growth_rate = f"{signal.growth_score:.1%}"

        if signal.alert_level == "red":
            # 红色预警 - 爆款确认
            title = f"【红色预警】{video.platform}爆款确认！"

            body = f"""
🔥 视频: {video.title[:30]}

📊 核心数据:
- 播放量: {play_count}
- 增长率: {growth_rate}
- 互动率: {video.metrics.engagement_rate:.1%}

💡 AI洞察: {signal.message}

🔗 查看详情: {video.url}
            """.strip()

        elif signal.alert_level == "orange":
            # 橙色预警 - 快速增长中
            title = f"【橙色预警】{video.platform}视频快速增长！"

            body = f"""
📈 视频: {video.title[:30]}

🔥 增长信号:
- 增长阶段: {signal.growth_stage}
- 真实性: {signal.authenticity:.0%}

🎯 建议: 建议尽快分析，抢占先机！

🔗 {video.url}
            """.strip()

        else:
            # 黄色预警 - 潜力发现
            title = f"【黄色预警】{video.platform}潜力视频！"

            body = f"""
✨ 视频: {video.title[:30]}

📊 初步分析:
- 互动率: {video.metrics.engagement_rate:.1%}
- vs平均: {signal.vs_benchmark.get('is_above_average', False) and '高于平均' or '一般'}

🎯 建议: 持续关注

🔗 {video.url}
            """.strip()

        return AlertContent(
            title=title,
            body=body,
            level=signal.alert_level,
            video=video.to_dict(),
            signal=signal.to_dict()
        )

    def _get_user_preferences(self, user_id: int) -> Dict[str, Any]:
        """获取用户通知偏好"""
        # 实际项目中从数据库查询
        return {
            "notification_channels": settings.ALERT_CHANNELS,
            "alert_levels": ["yellow", "orange", "red"]
        }

    def _determine_channels(
        self,
        alert_level: str,
        user_prefs: Dict[str, Any]
    ) -> List[str]:
        """确定推送渠道"""
        channels = user_prefs.get("notification_channels", [])

        # 红色预警额外启用短信
        if alert_level == "red" and 'sms' not in channels:
            channels.append('sms')

        return channels

    async def _log_alert(
        self,
        user_id: int,
        video_id: str,
        signal: ViralSignal,
        results: List[Dict]
    ):
        """记录预警日志"""
        logger.info(
            f"Alert logged: user={user_id}, video={video_id}, "
            f"level={signal.alert_level}, results={results}"
        )
        # 实际项目中保存到数据库

    def _format_number(self, num: int) -> str:
        """格式化数字"""
        if num >= 1_000_000:
            return f"{num / 1_000_000:.1f}M"
        elif num >= 1_000:
            return f"{num / 1_000:.1f}K"
        else:
            return str(num)


# Push Providers
class AppPushProvider:
    """应用内推送"""

    async def send(
        self,
        user_id: int,
        title: str,
        body: str,
        data: Dict
    ) -> Dict:
        logger.info(f"Sending app push to user {user_id}")
        # 实际实现
        return {"status": "ok"}


class EmailPushProvider:
    """邮件推送"""

    async def send(
        self,
        user_id: int,
        title: str,
        body: str,
        data: Dict
    ) -> Dict:
        logger.info(f"Sending email to user {user_id}")
        # 实际实现
        return {"status": "ok"}


class WeChatPushProvider:
    """微信推送"""

    async def send(
        self,
        user_id: int,
        title: str,
        body: str,
        data: Dict
    ) -> Dict:
        logger.info(f"Sending WeChat notification to user {user_id}")
        # 实际实现
        return {"status": "ok"}


class SMSPushProvider:
    """短信推送"""

    async def send(
        self,
        user_id: int,
        title: str,
        body: str,
        data: Dict
    ) -> Dict:
        logger.info(f"Sending SMS to user {user_id}")
        # 实际实现
        return {"status": "ok"}


# Singleton instance
alert_service = AlertService()


def get_alert_service() -> AlertService:
    """Get alert service instance"""
    return alert_service
