"""
Celery Application Configuration
"""
from celery import Celery
from celery.schedules import crontab
from loguru import logger

from app.core.config import settings


# Create Celery app
celery_app = Celery(
    'data_collector',
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        'app.tasks.hot_scan',
        'app.tasks.competitor_monitor',
        'app.tasks.video_update',
        'app.tasks.report_generator',
    ]
)

# Celery configuration
celery_app.conf.update(
    # Task settings
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Asia/Shanghai',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 hour max
    task_soft_time_limit=3000,  # 50 minutes soft limit

    # Worker settings
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=100,

    # Beat schedule
    beat_schedule={
        # 1. 高频热点扫描（每30分钟）
        'scan-all-hot-trends': {
            'task': 'app.tasks.hot_scan.scan_all_platforms',
            'schedule': crontab(minute='*/30'),
            'options': {'queue': 'hot_scan'}
        },

        # 2. 竞品账号深度监控（每15分钟）
        'monitor-competitors': {
            'task': 'app.tasks.competitor_monitor.check_all_watchlists',
            'schedule': crontab(minute='*/15'),
            'options': {'queue': 'competitor_monitor'}
        },

        # 3. 视频详情更新（发布后24小时内密集追踪，每5分钟）
        'update-recent-videos': {
            'task': 'app.tasks.video_update.refresh_active_videos',
            'schedule': crontab(minute='*/5'),
            'options': {'queue': 'video_update'}
        },

        # 4. 每日领域报告生成
        'generate-daily-reports': {
            'task': 'app.tasks.report_generator.generate_daily',
            'schedule': crontab(hour=23, minute=59),
            'options': {'queue': 'report'}
        },

        # 5. 数据清理任务（每天凌晨3点）
        'cleanup-old-data': {
            'task': 'app.tasks.maintenance.cleanup_old_data',
            'schedule': crontab(hour=3, minute=0),
            'options': {'queue': 'maintenance'}
        }
    }
)

logger.info("Celery app configured successfully")


if __name__ == '__main__':
    celery_app.start()
