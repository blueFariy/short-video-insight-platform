"""
Hot Trend Scanning Tasks
"""
from celery import shared_task
from loguru import logger

from app.adapters import get_platform_adapter
from app.services.viral_detector import viral_detector
from app.services.cleaning_pipeline import cleaning_pipeline


@shared_task(bind=True, max_retries=3)
def scan_all_platforms(self):
    """
    扫描所有平台热点
    每30分钟执行一次
    """
    logger.info("Starting hot trend scan for all platforms")

    platforms = ['douyin', 'bilibili', 'xiaohongshu']
    all_videos = []

    for platform in platforms:
        try:
            adapter = get_platform_adapter(platform)
            hot_videos = adapter.get_trending_videos(limit=100)

            logger.info(f"Fetched {len(hot_videos)} videos from {platform}")

            # 数据清洗
            cleaned_videos = []
            for video in hot_videos:
                cleaned = cleaning_pipeline.process_video(video)
                if cleaned:
                    cleaned_videos.append(cleaned)

            all_videos.extend(cleaned_videos)

            # 触发异步爆款分析任务
            for video in cleaned_videos:
                analyze_video_for_viral.delay(video.video_id, video.platform)

        except Exception as e:
            logger.error(f"Failed to scan {platform}: {e}")
            # 1分钟后重试
            raise self.retry(countdown=60, exc=e)

    logger.info(f"Hot trend scan completed. Total videos: {len(all_videos)}")
    return {
        "platforms_scanned": len(platforms),
        "total_videos": len(all_videos)
    }


@shared_task(bind=True, max_retries=2)
def analyze_video_for_viral(self, video_id: str, platform: str):
    """
    分析单个视频的爆款潜力
    """
    logger.info(f"Analyzing viral potential for video: {video_id}")

    try:
        # 获取视频详情
        adapter = get_platform_adapter(platform)
        video = adapter.get_video_detail(video_id)

        if not video:
            logger.warning(f"Video not found: {video_id}")
            return {"status": "not_found"}

        # 爆款检测
        signal = viral_detector.detect(video)

        logger.info(
            f"Video {video_id} analysis: "
            f"stage={signal.growth_stage}, "
            f"should_alert={signal.should_alert}, "
            f"level={signal.alert_level}"
        )

        # 如果需要预警，触发预警任务
        if signal.should_alert:
            send_viral_alert.delay(video.to_dict(), signal.to_dict())

        return {
            "status": "analyzed",
            "signal": signal.to_dict()
        }

    except Exception as e:
        logger.error(f"Failed to analyze video {video_id}: {e}")
        raise self.retry(countdown=30, exc=e)
