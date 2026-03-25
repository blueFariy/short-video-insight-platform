"""
Maintenance Tasks - Using database
"""
import asyncio

from celery import shared_task
from loguru import logger
from datetime import datetime, timedelta
from sqlalchemy import select, delete, and_

from app.core.database import db_manager, Video


@shared_task
def cleanup_old_data():
    """
    清理过期数据
    每天凌晨3点执行
    """
    logger.info("Starting data cleanup")

    # 1. 清理低播放量的旧视频数据
    cleaned = _cleanup_old_videos(days=30)

    # 2. 清理过期的缓存数据
    cache_cleaned = _cleanup_cache(days=7)

    logger.info(
        f"Data cleanup completed. "
        f"Old videos: {cleaned}, Cache: {cache_cleaned}"
    )

    return {
        "old_videos_cleaned": cleaned,
        "cache_cleaned": cache_cleaned
    }


def _cleanup_old_videos(days: int) -> int:
    """清理旧视频数据"""
    logger.info(f"Cleaning videos older than {days} days with low play count")

    try:
        db_manager.init_db()
        deleted_count = 0

        async def _delete():
            nonlocal deleted_count
            async with db_manager.get_session() as session:
                cutoff_time = datetime.now() - timedelta(days=days)

                # 删除30天前且播放量低（<1000）的视频
                stmt = delete(Video).where(
                    and_(
                        Video.created_at < cutoff_time,
                        Video.play_count < 1000  # 保留高播放量视频
                    )
                )
                result = await session.execute(stmt)
                deleted_count = result.rowcount
                await session.commit()

        asyncio.run(_delete())
        logger.info(f"Deleted {deleted_count} old videos")
        return deleted_count
    except Exception as e:
        logger.error(f"Failed to cleanup old videos: {e}")
        return 0


def _cleanup_cache(days: int) -> int:
    """清理缓存"""
    logger.info(f"Cleaning cache older than {days} days")

    try:
        # TODO: 清理Redis缓存
        return 0
    except Exception as e:
        logger.error(f"Failed to cleanup cache: {e}")
        return 0


@shared_task
def health_check():
    """
    健康检查任务
    每5分钟执行一次
    """
    logger.debug("Health check running")

    try:
        # 检查数据库连接
        db_manager.init_db()

        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }
