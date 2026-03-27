"""
Video Update Tasks - Refresh active videos from database
"""
import asyncio

from celery import shared_task
from loguru import logger
from datetime import datetime, timedelta
from sqlalchemy import select, and_

from app.adapters import get_platform_adapter
from app.models import db_manager, Video


@shared_task(bind=True, max_retries=2)
def refresh_active_videos(self):
    """
    更新发布后24小时内的视频数据
    每5分钟执行一次（密集监控期）
    """
    logger.info("Starting active videos refresh")

    # 获取最近24小时内发布的视频
    recent_videos = _get_recent_videos_from_db(hours=24)

    updated_count = 0
    viral_alerts = 0

    for video_info in recent_videos:
        try:
            platform = video_info['platform']
            video_id = video_info['video_id']

            adapter = get_platform_adapter(platform)
            latest_video = asyncio.run(adapter.get_video_detail(video_id))

            if latest_video:
                # 更新数据库中的数据
                _update_video_metrics_in_db(video_id, latest_video)

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
    使用 AlertService 发送多渠道通知
    """
    from app.services.alert_service import alert_service
    from app.schemas import Video, VideoMetrics, ViralSignal

    logger.info(f"Sending viral alert for video: {video_data.get('video_id')}")

    try:
        # 将字典转换为模型对象
        video = Video(
            video_id=video_data.get('video_id', ''),
            platform=video_data.get('platform', ''),
            title=video_data.get('title', ''),
            url=video_data.get('url', ''),
            creator_id=video_data.get('creator_id', ''),
            creator_name=video_data.get('creator_name', ''),
            cover_url=video_data.get('cover_url', ''),
            duration=video_data.get('duration', 0),
            metrics=VideoMetrics(
                video_id=video_data.get('video_id', ''),
                platform=video_data.get('platform', ''),
                play_count=video_data.get('play_count', 0),
                like_count=video_data.get('like_count', 0),
                comment_count=video_data.get('comment_count', 0),
                share_count=video_data.get('share_count', 0),
                favorite_count=video_data.get('favorite_count', 0),
                engagement_rate=video_data.get('engagement_rate', 0.0)
            )
        )

        signal = ViralSignal(
            video_id=signal_data.get('video_id', ''),
            growth_score=signal_data.get('growth_score', 0.0),
            growth_stage=signal_data.get('growth_stage', 'unknown'),
            should_alert=signal_data.get('should_alert', False),
            alert_level=signal_data.get('alert_level', 'none'),
            message=signal_data.get('message', '')
        )

        # 发送预警通知
        result = asyncio.run(alert_service.send_viral_alert(
            user_id=1,  # TODO: 从任务上下文获取用户ID
            video=video,
            signal=signal
        ))

        logger.info(f"Viral alert sent successfully: {result}")
        return result

    except Exception as e:
        logger.error(f"Failed to send viral alert: {e}")
        return {
            "status": "error",
            "video": video_data,
            "error": str(e)
        }


def _get_recent_videos_from_db(hours: int = 24):
    """
    从数据库获取最近发布的视频列表
    """
    try:
        db_manager.init_db()
        videos = []

        async def _query():
            async with db_manager.get_session() as session:
                # 获取最近24小时发布的视频
                cutoff_time = datetime.now() - timedelta(hours=hours)
                stmt = select(Video).where(
                    Video.publish_time >= cutoff_time
                )
                result = await session.execute(stmt)
                db_videos = result.scalars().all()

                return [
                    {
                        "video_id": v.video_id,
                        "platform": v.platform,
                        "account_id": str(v.creator_id) if v.creator_id else "",
                        "publish_time": v.publish_time
                    }
                    for v in db_videos
                ]

        return asyncio.run(_query())
    except Exception as e:
        logger.warning(f"Failed to get recent videos from database: {e}, returning empty list")
        return []


def _update_video_metrics_in_db(video_id: str, latest_video):
    """
    更新视频指标数据到数据库
    """
    try:
        async def _update():
            async with db_manager.get_session() as session:
                stmt = select(Video).where(Video.video_id == video_id)
                result = await session.execute(stmt)
                db_video = result.scalar_one_or_none()

                if db_video:
                    # 更新指标
                    if latest_video.metrics:
                        db_video.play_count = latest_video.metrics.play_count
                        db_video.like_count = latest_video.metrics.like_count
                        db_video.comment_count = latest_video.metrics.comment_count
                        db_video.share_count = latest_video.metrics.share_count

                    await session.commit()
                    logger.debug(f"Updated metrics for video: {video_id}")

        asyncio.run(_update())
    except Exception as e:
        logger.error(f"Failed to update video metrics: {e}")


# 导入需要用到的模块（在文件底部避免循环导入）
from app.adapters import get_platform_adapter
