"""
Douyin Data Collection Tasks
抖音数据采集定时任务
"""
import asyncio
from celery import shared_task
from loguru import logger
from datetime import datetime

from app.adapters import get_platform_adapter
from app.services.viral_detector import viral_detector
from app.services.cleaning_pipeline import cleaning_pipeline


# 默认监控的关键词列表
DEFAULT_KEYWORDS = [
    "美食", "旅游", "搞笑", "情感", "知识",
    "健身", "美妆", "数码", "母婴", "家居"
]


async def _detect_viral_async(video):
    """异步调用爆款检测"""
    return await viral_detector.detect(video)


@shared_task(bind=True, max_retries=3)
def scan_douyin_hot(self):
    """
    采集抖音热搜数据
    每30分钟执行一次
    """
    logger.info("Starting Douyin hot search scan")

    try:
        adapter = get_platform_adapter("douyin")
        hot_videos = adapter.get_trending_videos(limit=50)

        logger.info(f"Fetched {len(hot_videos)} hot search items from Douyin")

        # 数据清洗
        cleaned_count = 0
        viral_alerts = 0

        for video in hot_videos:
            try:
                # 清洗数据
                cleaned = cleaning_pipeline.process_video(video)
                if cleaned:
                    cleaned_count += 1

                    # 爆款分析（使用asyncio调用异步方法）
                    signal = asyncio.run(_detect_viral_async(cleaned))
                    if signal.should_alert:
                        viral_alerts += 1
                        logger.info(f"Hot video alert: {video.title} - {signal.alert_level}")
            except Exception as e:
                logger.error(f"Failed to process hot video: {e}")
                continue

        logger.info(f"Douyin hot scan completed. Cleaned: {cleaned_count}, Alerts: {viral_alerts}")
        return {
            "platform": "douyin",
            "total_fetched": len(hot_videos),
            "cleaned": cleaned_count,
            "viral_alerts": viral_alerts,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Failed to scan Douyin hot: {e}")
        raise self.retry(countdown=60, exc=e)


@shared_task(bind=True, max_retries=2)
def collect_douyin_by_keywords(self, keywords: list = None, limit_per_keyword: int = 20):
    """
    根据关键词采集抖音视频
    每小时执行一次

    Args:
        keywords: 关键词列表，默认为 DEFAULT_KEYWORDS
        limit_per_keyword: 每个关键词采集数量
    """
    if keywords is None:
        keywords = DEFAULT_KEYWORDS

    logger.info(f"Starting Douyin keyword collection for {len(keywords)} keywords")

    try:
        adapter = get_platform_adapter("douyin")
        total_collected = 0

        for keyword in keywords:
            try:
                # 搜索视频（按热度排序）
                videos = adapter.search_videos(
                    keyword=keyword,
                    limit=limit_per_keyword,
                    sort_by="hot",
                    publish_time="week"  # 近一周
                )

                # 清洗并分析
                for video in videos:
                    try:
                        cleaned = cleaning_pipeline.process_video(video)
                        if cleaned:
                            signal = viral_detector.detect(cleaned)
                            # 可以在这里保存到数据库
                            total_collected += 1
                    except Exception as e:
                        logger.error(f"Failed to process video {video.video_id}: {e}")
                        continue

                logger.info(f"Collected {len(videos)} videos for keyword: {keyword}")

            except Exception as e:
                logger.error(f"Failed to collect videos for keyword {keyword}: {e}")
                continue

        logger.info(f"Douyin keyword collection completed. Total: {total_collected}")
        return {
            "platform": "douyin",
            "keywords": keywords,
            "total_collected": total_collected,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Failed to collect Douyin by keywords: {e}")
        raise self.retry(countdown=120, exc=e)


@shared_task(bind=True, max_retries=2)
def collect_douyin_creator(self, sec_uid: str):
    """
    采集指定创作者的视频
    支持手动触发或定时调用

    Args:
        sec_uid: 创作者 sec_uid
    """
    logger.info(f"Starting Douyin creator collection for: {sec_uid}")

    try:
        adapter = get_platform_adapter("douyin")

        # 获取创作者信息
        creator = adapter.get_creator_info(sec_uid)
        if not creator:
            logger.warning(f"Creator not found: {sec_uid}")
            return {"status": "not_found", "sec_uid": sec_uid}

        # 获取创作者视频
        videos = adapter.get_creator_videos(sec_uid=sec_uid, limit=50)

        # 清洗并分析
        processed_count = 0
        for video in videos:
            try:
                cleaned = cleaning_pipeline.process_video(video)
                if cleaned:
                    signal = viral_detector.detect(cleaned)
                    processed_count += 1
            except Exception as e:
                logger.error(f"Failed to process video: {e}")
                continue

        logger.info(f"Creator collection completed. Videos: {len(videos)}, Processed: {processed_count}")
        return {
            "status": "success",
            "creator": {
                "sec_uid": creator.creator_id,
                "name": creator.name,
                "follower_count": creator.follower_count
            },
            "videos_fetched": len(videos),
            "videos_processed": processed_count,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Failed to collect creator {sec_uid}: {e}")
        raise self.retry(countdown=60, exc=e)


@shared_task
def collect_douyin_video_comments(video_id: str, limit: int = 50):
    """
    采集视频评论数据

    Args:
        video_id: 视频ID
        limit: 评论数量限制
    """
    logger.info(f"Collecting comments for video: {video_id}")

    try:
        adapter = get_platform_adapter("douyin")

        # 获取视频详情
        video = adapter.get_video_detail(video_id)
        if not video:
            logger.warning(f"Video not found: {video_id}")
            return {"status": "not_found", "video_id": video_id}

        # 获取评论
        comments = adapter.get_video_comments(video_id, limit=limit)

        logger.info(f"Collected {len(comments)} comments for video: {video_id}")
        return {
            "status": "success",
            "video_id": video_id,
            "video_title": video.title,
            "comment_count": len(comments),
            "comments": comments[:10],  # 返回前10条评论示例
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Failed to collect comments for {video_id}: {e}")
        return {"status": "error", "video_id": video_id, "error": str(e)}


# 便捷函数：采集多个创作者
@shared_task
def collect_douyin_creators_batch(sec_uids: list):
    """
    批量采集多个创作者

    Args:
        sec_uids: 创作者 sec_uid 列表
    """
    logger.info(f"Starting batch creator collection for {len(sec_uids)} creators")

    results = []
    for sec_uid in sec_uids:
        result = collect_douyin_creator.delay(sec_uid)
        results.append({
            "sec_uid": sec_uid,
            "task_id": result.id
        })

    return {
        "status": "dispatched",
        "creators": results,
        "timestamp": datetime.now().isoformat()
    }
