"""
Trend Report Scheduled Tasks - 趋势报告定时任务
"""
import sys
from pathlib import Path

# Add parent directory to Python path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from loguru import logger

from app.celery_app import celery_app
from app.services.trend_report_service import trend_report_service


@celery_app.task(bind=True, name="app.tasks.trend_tasks.generate_daily_report")
def generate_daily_report(self):
    """
    生成每日趋势报告
    每天凌晨2点执行
    """
    task_id = self.request.id
    logger.info(f"[{task_id}] Starting daily trend report generation")

    try:
        # 初始化数据库连接
        from app.core.database import db_manager
        db_manager.init_db()
        logger.info(f"[{task_id}] Database connection initialized")

        # 生成每日报告
        report = trend_report_service.generate_trend_report(
            report_type="daily",
            platform=None,  # 全平台
            category=None    # 全部分类
        )

        logger.info(f"[{task_id}] Daily report generated successfully: {report['title']}")

        return {
            "status": "success",
            "report_id": report.get("id"),
            "title": report["title"],
            "type": "daily"
        }

    except Exception as e:
        logger.error(f"[{task_id}] Error generating daily report: {e}")
        raise self.retry(exc=e, countdown=60, max_retries=3)


@celery_app.task(bind=True, name="app.tasks.trend_tasks.generate_weekly_report")
def generate_weekly_report(self, platform: str = None):
    """
    生成每周趋势报告
    每周一凌晨3点执行

    Args:
        platform: 可选，指定平台生成报告
    """
    task_id = self.request.id
    logger.info(f"[{task_id}] Starting weekly trend report generation, platform={platform}")

    try:
        # 初始化数据库连接
        from app.core.database import db_manager
        db_manager.init_db()
        logger.info(f"[{task_id}] Database connection initialized")

        # 生成周报
        report = trend_report_service.generate_trend_report(
            report_type="weekly",
            platform=platform,
            category=None
        )

        logger.info(f"[{task_id}] Weekly report generated successfully: {report['title']}")

        # 如果没有指定平台，为每个平台单独生成报告
        if not platform:
            platforms = ["douyin", "bilibili", "xiaohongshu", "kuaishou"]
            for plat in platforms:
                try:
                    plat_report = trend_report_service.generate_trend_report(
                        report_type="weekly",
                        platform=plat,
                        category=None
                    )
                    logger.info(f"[{task_id}] Platform report generated: {plat} - {plat_report['title']}")
                except Exception as e:
                    logger.error(f"[{task_id}] Error generating {plat} report: {e}")

        return {
            "status": "success",
            "report_id": report.get("id"),
            "title": report["title"],
            "type": "weekly"
        }

    except Exception as e:
        logger.error(f"[{task_id}] Error generating weekly report: {e}")
        raise self.retry(exc=e, countdown=300, max_retries=3)


@celery_app.task(bind=True, name="app.tasks.trend_tasks.generate_monthly_report")
def generate_monthly_report(self, platform: str = None):
    """
    生成每月趋势报告
    每月1日凌晨4点执行

    Args:
        platform: 可选，指定平台生成报告
    """
    task_id = self.request.id
    logger.info(f"[{task_id}] Starting monthly trend report generation, platform={platform}")

    try:
        # 初始化数据库连接
        from app.core.database import db_manager
        db_manager.init_db()
        logger.info(f"[{task_id}] Database connection initialized")

        # 生成月报
        report = trend_report_service.generate_trend_report(
            report_type="monthly",
            platform=platform,
            category=None
        )

        logger.info(f"[{task_id}] Monthly report generated successfully: {report['title']}")

        # 如果没有指定平台，为每个平台单独生成报告
        if not platform:
            platforms = ["douyin", "bilibili", "xiaohongshu", "kuaishou"]
            for plat in platforms:
                try:
                    plat_report = trend_report_service.generate_trend_report(
                        report_type="monthly",
                        platform=plat,
                        category=None
                    )
                    logger.info(f"[{task_id}] Platform report generated: {plat} - {plat_report['title']}")
                except Exception as e:
                    logger.error(f"[{task_id}] Error generating {plat} report: {e}")

        return {
            "status": "success",
            "report_id": report.get("id"),
            "title": report["title"],
            "type": "monthly"
        }

    except Exception as e:
        logger.error(f"[{task_id}] Error generating monthly report: {e}")
        raise self.retry(exc=e, countdown=600, max_retries=3)


@celery_app.task(bind=True, name="app.tasks.trend_tasks.update_trend_statistics")
def update_trend_statistics(self, days: int = 7):
    """
    更新趋势统计数据缓存
    每小时执行一次，用于保持统计数据新鲜

    Args:
        days: 统计天数
    """
    task_id = self.request.id
    logger.info(f"[{task_id}] Starting trend statistics update for {days} days")

    try:
        # 初始化数据库连接
        from app.core.database import db_manager
        db_manager.init_db()

        # 获取统计数据（但不保存，只是预热）
        statistics = trend_report_service.get_statistics(days=days)

        logger.info(f"[{task_id}] Trend statistics updated: {statistics['total_videos']} videos")

        return {
            "status": "success",
            "total_videos": statistics["total_videos"],
            "total_views": statistics["total_views"]
        }

    except Exception as e:
        logger.error(f"[{task_id}] Error updating trend statistics: {e}")
        raise self.retry(exc=e, countdown=60, max_retries=3)


# 手动触发报告生成的任务
@celery_app.task(bind=True, name="app.tasks.trend_tasks.trigger_report_generation")
def trigger_report_generation(self, report_type: str, platform: str = None, category: str = None):
    """
    手动触发报告生成（供 API 调用）

    Args:
        report_type: 报告类型 (daily/weekly/monthly)
        platform: 平台筛选
        category: 分类筛选
    """
    task_id = self.request.id
    logger.info(f"[{task_id}] Manually triggering report generation: type={report_type}")

    try:
        # 初始化数据库连接
        from app.core.database import db_manager
        db_manager.init_db()

        # 生成报告
        report = trend_report_service.generate_trend_report(
            report_type=report_type,
            platform=platform,
            category=category
        )

        logger.info(f"[{task_id}] Report generated: {report['title']}")

        return {
            "status": "success",
            "report_id": report.get("id"),
            "title": report["title"]
        }

    except Exception as e:
        logger.error(f"[{task_id}] Error generating report: {e}")
        raise
