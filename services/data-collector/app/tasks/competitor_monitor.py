"""
Competitor Monitoring Tasks
"""
from celery import shared_task
from loguru import logger


@shared_task(bind=True, max_retries=2)
def check_all_watchlists(self):
    """
    检查所有用户的竞品监控列表
    每15分钟执行一次
    """
    logger.info("Starting competitor watchlist check")

    # 模拟从数据库获取所有活跃的监控列表
    # 实际项目中需要从数据库查询
    watchlists = _get_active_watchlists()

    alerts_triggered = 0

    for watchlist in watchlists:
        try:
            # 获取竞品最新视频
            creator = watchlist.get('creator')
            recent_videos = _get_creator_recent_videos(
                creator['platform'],
                creator['creator_id'],
                hours=24
            )

            for video in recent_videos:
                # 检查是否达到预警阈值
                threshold = watchlist.get('alert_threshold', 50)  # 默认50%
                avg_play = creator.get('avg_play_count', 0)

                if avg_play > 0 and video['play_count'] > avg_play * (1 + threshold / 100):
                    # 触发预警
                    send_competitor_alert.delay(
                        user_id=watchlist['user_id'],
                        video=video,
                        reason=f"播放量超过平均{threshold}%"
                    )
                    alerts_triggered += 1

        except Exception as e:
            logger.error(f"Failed to check watchlist {watchlist.get('id')}: {e}")

    logger.info(f"Competitor watchlist check completed. Alerts triggered: {alerts_triggered}")
    return {
        "watchlists_checked": len(watchlists),
        "alerts_triggered": alerts_triggered
    }


@shared_task
def send_competitor_alert(user_id: int, video: dict, reason: str):
    """
    发送竞品预警
    """
    logger.info(f"Sending competitor alert to user {user_id}: {video.get('title')}")

    # 实际项目中需要调用通知服务
    # 例如：邮件、短信、应用内推送

    return {
        "status": "sent",
        "user_id": user_id,
        "video_id": video.get('video_id'),
        "reason": reason
    }


def _get_active_watchlists():
    """
    获取所有活跃的监控列表
    模拟从数据库获取
    """
    # 实际项目中从数据库查询
    return [
        {
            "id": "watch_001",
            "user_id": 1,
            "creator": {
                "platform": "douyin",
                "creator_id": "xiaoyange",
                "avg_play_count": 1000000
            },
            "alert_threshold": 30
        },
        {
            "id": "watch_002",
            "user_id": 1,
            "creator": {
                "platform": "bilibili",
                "creator_id": "BV1GJ411x7h7",
                "avg_play_count": 500000
            },
            "alert_threshold": 50
        }
    ]


def _get_creator_recent_videos(platform: str, creator_id: str, hours: int = 24):
    """
    获取创作者最近发布的视频
    模拟从数据源获取
    """
    from app.adapters import get_platform_adapter

    try:
        adapter = get_platform_adapter(platform)
        videos = adapter.get_creator_videos(creator_id, limit=10)

        return [
            {
                "video_id": v.video_id,
                "title": v.title,
                "play_count": v.metrics.play_count,
                "platform": platform
            }
            for v in videos
        ]
    except Exception as e:
        logger.error(f"Failed to get creator videos: {e}")
        return []
