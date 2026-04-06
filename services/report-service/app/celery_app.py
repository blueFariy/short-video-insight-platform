"""
Celery Configuration for Report Service
"""
from celery import Celery
from celery.schedules import crontab

from app.core.config import settings

# Create Celery app
celery_app = Celery(
    "report_service",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.tasks.trend_tasks"]
)

# Celery Configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Shanghai",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    worker_prefetch_multiplier=1,
)

# Beat Schedule - Periodic Tasks
celery_app.conf.beat_schedule = {
    # 每日趋势报告 - 每天凌晨2点执行
    "generate-daily-trend-report": {
        "task": "app.tasks.trend_tasks.generate_daily_report",
        "schedule": crontab(hour=2, minute=0),
    },
    # 每周趋势报告 - 每周一凌晨3点执行
    "generate-weekly-trend-report": {
        "task": "app.tasks.trend_tasks.generate_weekly_report",
        "schedule": crontab(hour=3, minute=0, day_of_week=1),
    },
    # 每月趋势报告 - 每月1日凌晨4点执行
    "generate-monthly-trend-report": {
        "task": "app.tasks.trend_tasks.generate_monthly_report",
        "schedule": crontab(hour=4, minute=0, day_of_month=1),
    },
}


@celery_app.task(bind=True)
def debug_task(self):
    """Debug task for testing Celery connectivity"""
    print(f"Debug task executed at: {self.request.id}")
    return {"status": "success"}
