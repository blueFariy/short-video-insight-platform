"""
Maintenance Tasks
"""
from celery import shared_task
from loguru import logger
from datetime import datetime, timedelta


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
    """清理原始数据"""
    logger.info(f"Cleaning raw data older than {days} days")
    # 实际项目中执行数据库清理
    return 100  # 模拟清理数量


def _cleanup_cache(days: int) -> int:
    """清理缓存"""
    logger.info(f"Cleaning cache older than {days} days")
    # 实际项目中清理Redis缓存
    return 50


def _cleanup_failed_alerts(days: int) -> int:
    """清理失败的预警记录"""
    logger.info(f"Cleaning failed alerts older than {days} days")
    # 实际项目中清理数据库
    return 10


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
    # 实际项目中检查数据库
    return True


def _check_redis() -> bool:
    """检查Redis连接"""
    # 实际项目中检查Redis
    return True


def _check_api_services() -> bool:
    """检查外部API服务"""
    # 实际项目中检查各平台API
    return True
