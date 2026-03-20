"""
Video Update Tasks - Refresh active videos
"""
from celery import shared_task
from loguru import logger
from datetime import datetime, timedelta


@shared_task(bind=True, max_retries=2)
def refresh_active_videos(self):
    """
    更新发布后24小时内的视频数据
    每5分钟执行一次（密集监控期）
    """
    logger.info("Starting active videos refresh")

    # 获取最近24小时内发布的视频
    recent_videos = _get_recent_videos(hours=24)

    updated_count = 0
    viral_alerts = 0

    for video_info in recent_videos:
        try:
            # 获取最新数据
            platform = video_info['platform']
            video_id = video_info['video_id']

            adapter = get_platform_adapter(platform)
            latest_video = adapter.get_video_detail(video_id)

            if latest_video:
                # 更新数据库中的数据
                _update_video_metrics(video_id, latest_video.metrics)

                # 检测增长趋势
                history = _get_video_metric_history(video_id)

                if len(history) >= 2:
                    # 计算增长率
                    latest = history[-1].play_count
                    previous = history[-2].play_count

                    if previous > 0:
                        growth_rate = (latest - previous) / previous

                        # 如果增长率超过阈值，触发预警
                        if growth_rate > 0.5:  # 50%增长率
                            send_viral_alert.delay(
                                latest_video.to_dict(),
                                {"growth_rate": growth_rate, "stage": "explosion"}
                            )
                            viral_alerts += 1

                updated_count += 1

        except Exception as e:
            logger.error(f"Failed to refresh video {video_info.get('video_id')}: {e}")

    logger.info(f"Active videos refresh completed. Updated: {updated_count}, Alerts: {viral_alerts}")
    return {
        "videos_refreshed": updated_count,
        "viral_alerts": viral_alerts
    }


@shared_task
def send_viral_alert(video_data: dict, signal_data: dict):
    """
    发送爆款预警
    """
    logger.info(f"Sending viral alert for video: {video_data.get('video_id')}")

    # 实际项目中需要调用通知服务
    return {
        "status": "sent",
        "video": video_data,
        "signal": signal_data
    }


def _get_recent_videos(hours: int = 24):
    """
    获取最近发布的视频列表
    模拟从数据库获取
    """
    # 实际项目中从数据库查询
    # SELECT * FROM videos WHERE publish_time > NOW() - INTERVAL '24 hours'
    return [
        {"video_id": "dy_001", "platform": "douyin", "publish_time": datetime.now() - timedelta(hours=6)},
        {"video_id": "bilibili_001", "platform": "bilibili", "publish_time": datetime.now() - timedelta(hours=12)},
        {"video_id": "xhs_001", "platform": "xiaohongshu", "publish_time": datetime.now() - timedelta(hours=3)}
    ]


def _update_video_metrics(video_id: str, metrics):
    """
    更新视频指标数据
    """
    logger.debug(f"Updating metrics for video: {video_id}")
    # 实际项目中更新数据库


def _get_video_metric_history(video_id: str):
    """
    获取视频的历史指标
    """
    # 实际项目中从数据库查询
    from app.models import VideoMetrics
    return []


from app.adapters import get_platform_adapter
