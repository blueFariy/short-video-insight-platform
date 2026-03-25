"""
Competitor Monitoring Tasks - Using database
"""
import asyncio

from celery import shared_task
from loguru import logger
from datetime import datetime, timedelta
from sqlalchemy import select

from app.adapters import get_platform_adapter
from app.core.database import db_manager, Creator, Video


@shared_task(bind=True, max_retries=2)
def check_all_watchlists(self):
    """
    检查所有监控账号的视频更新
    每15分钟执行一次
    """
    logger.info("Starting competitor watchlist check")

    # 从数据库获取所有活跃的监控账号
    watchlists = _get_active_accounts_from_db()

    alerts_triggered = 0

    for account in watchlists:
        try:
            # 获取账号最新视频
            recent_videos = _get_creator_recent_videos(
                account['platform'],
                account['account_id'],
                hours=24
            )

            # 计算平均播放量
            avg_play_count = account.get('avg_play_count', 0)
            alert_threshold = account.get('alert_threshold', 30)

            for video in recent_videos:
                # 检查是否达到预警阈值
                if avg_play_count > 0 and video['play_count'] > avg_play_count * (1 + alert_threshold / 100):
                    # 触发预警
                    send_competitor_alert.delay(
                        user_id=account.get('user_id', 1),
                        video=video,
                        reason=f"播放量超过平均{alert_threshold}%"
                    )
                    alerts_triggered += 1

        except Exception as e:
            logger.error(f"Failed to check watchlist {account.get('id')}: {e}")

    logger.info(f"Competitor watchlist check completed. Alerts triggered: {alerts_triggered}")
    return {
        "watchlists_checked": len(watchlists),
        "alerts_triggered": alerts_triggered
    }


@shared_task
def send_competitor_alert(user_id: int, video: dict, reason: str):
    """
    发送竞品预警
    使用 AlertService 发送多渠道通知
    """
    from app.services.alert_service import alert_service
    from app.models import Video, VideoMetrics, ViralSignal

    logger.info(f"Sending competitor alert to user {user_id}: {video.get('title')}")

    try:
        # 构建视频对象
        video_obj = Video(
            video_id=video.get('video_id', ''),
            platform=video.get('platform', ''),
            title=video.get('title', ''),
            url=video.get('url', ''),
            creator_id=video.get('creator_id', ''),
            creator_name=video.get('creator_name', ''),
            cover_url=video.get('cover_url', ''),
            duration=video.get('duration', 0),
            metrics=VideoMetrics(
                video_id=video.get('video_id', ''),
                platform=video.get('platform', ''),
                play_count=video.get('play_count', 0),
                like_count=video.get('like_count', 0),
                comment_count=video.get('comment_count', 0),
                share_count=video.get('share_count', 0),
                favorite_count=video.get('favorite_count', 0)
            )
        )

        # 构建信号对象
        signal = ViralSignal(
            video_id=video.get('video_id', ''),
            growth_score=video.get('play_count', 0) / 10000,
            growth_stage='competitor_alert',
            alert_level='orange',
            message=f"竞品预警: {reason}"
        )

        # 发送预警通知
        result = asyncio.run(alert_service.send_viral_alert(
            user_id=user_id,
            video=video_obj,
            signal=signal
        ))

        logger.info(f"Competitor alert sent successfully: {result}")
        return result

    except Exception as e:
        logger.error(f"Failed to send competitor alert: {e}")
        return {
            "status": "error",
            "user_id": user_id,
            "video_id": video.get('video_id'),
            "error": str(e)
        }


def _get_active_accounts_from_db():
    """
    从数据库获取所有活跃的监控账号
    """
    try:
        db_manager.init_db()

        async def _query():
            async with db_manager.get_session() as session:
                # Get only monitored creators
                stmt = select(Creator).where(Creator.is_monitored == True)
                result = await session.execute(stmt)
                accounts = result.scalars().all()

                return [
                    {
                        "id": str(a.id),
                        "user_id": 1,  # 暂时使用默认用户
                        "platform": a.platform,
                        "account_id": a.creator_id,
                        "name": a.name,
                        "avg_play_count": a.avg_play_count or 0,
                        "alert_threshold": 30
                    }
                    for a in accounts
                ]

        return asyncio.run(_query())
    except Exception as e:
        logger.warning(f"Failed to get accounts from database: {e}, returning empty list")
        return []


def _get_creator_recent_videos(platform: str, creator_id: str, hours: int = 24):
    """
    获取创作者最近发布的视频
    """
    from app.adapters import get_platform_adapter

    try:
        adapter = get_platform_adapter(platform)
        videos = asyncio.run(adapter.get_creator_videos(creator_id, limit=10))

        return [
            {
                "video_id": v.video_id,
                "title": v.title,
                "play_count": v.metrics.play_count if v.metrics else 0,
                "platform": platform
            }
            for v in videos
        ]
    except Exception as e:
        logger.error(f"Failed to get creator videos: {e}")
        return []
