"""
Maintenance Tasks - Using database
"""
import asyncio

from celery import shared_task
from loguru import logger
from datetime import datetime, timedelta
from sqlalchemy import select, delete, and_

from app.core.database import db_manager, CollectedVideo, CollectionTask


@shared_task
def cleanup_old_data():
    """
    清理过期数据
    每天凌晨3点执行
    """
    logger.info("Starting data cleanup")

    # 1. 清理30天前的原始采集数据（保留分析结果）
    cleaned = _cleanup_raw_data(days=30)

    # 2. 清理过期的缓存数据
    cache_cleaned = _cleanup_cache(days=7)

    # 3. 清理失败的预警记录（保留30天）
    alerts_cleaned = _cleanup_failed_alerts(days=30)

    logger.info(
        f"Data cleanup completed. "
        f"Raw data: {cleaned}, Cache: {cache_cleaned}, Alerts: {alerts_cleaned}"
    )

    return {
        "raw_data_cleaned": cleaned,
        "cache_cleaned": cache_cleaned,
        "alerts_cleaned": alerts_cleaned
    }


def _cleanup_raw_data(days: int) -> int:
    """清理原始采集数据"""
    logger.info(f"Cleaning raw data older than {days} days")

    try:
        db_manager.init_db()
        deleted_count = 0

        async def _delete():
            nonlocal deleted_count
            async with db_manager.get_session() as session:
                cutoff_time = datetime.now() - timedelta(days=days)

                # 删除30天前且没有被标记为重要的视频
                stmt = delete(CollectedVideo).where(
                    and_(
                        CollectedVideo.collected_at < cutoff_time,
                        CollectedVideo.play_count < 1000  # 保留高播放量视频
                    )
                )
                result = await session.execute(stmt)
                deleted_count = result.rowcount
                await session.commit()

        asyncio.run(_delete())
        logger.info(f"Deleted {deleted_count} old videos")
        return deleted_count
    except Exception as e:
        logger.error(f"Failed to cleanup raw data: {e}")
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


def _cleanup_failed_alerts(days: int) -> int:
    """清理失败的预警记录"""
    logger.info(f"Cleaning failed alerts older than {days} days")

    try:
        db_manager.init_db()
        deleted_count = 0

        async def _delete():
            nonlocal deleted_count
            async with db_manager.get_session() as session:
                cutoff_time = datetime.now() - timedelta(days=days)

                # 删除30天前的失败任务记录
                stmt = delete(CollectionTask).where(
                    and_(
                        CollectionTask.started_at < cutoff_time,
                        CollectionTask.status == "failed"
                    )
                )
                result = await session.execute(stmt)
                deleted_count = result.rowcount
                await session.commit()

        asyncio.run(_delete())
        return deleted_count
    except Exception as e:
        logger.error(f"Failed to cleanup alerts: {e}")
        return 0


@shared_task
def health_check():
    """
    健康检查任务
    """
    logger.info("Running health check")

    checks = {
        "database": _check_database(),
        "redis": _check_redis(),
        "api_services": _check_api_services()
    }

    all_healthy = all(checks.values())

    return {
        "status": "healthy" if all_healthy else "unhealthy",
        "checks": checks
    }


def _check_database() -> bool:
    """检查数据库连接"""
    try:
        db_manager.init_db()

        async def _check():
            async with db_manager.get_session() as session:
                await session.execute(select(1))
                return True

        return asyncio.run(_check())
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return False


def _check_redis() -> bool:
    """检查Redis连接"""
    try:
        # TODO: 检查Redis连接
        return True
    except Exception as e:
        logger.error(f"Redis health check failed: {e}")
        return False


def _check_api_services() -> bool:
    """检查外部API服务"""
    # TODO: 检查各平台API可用性
    return True
