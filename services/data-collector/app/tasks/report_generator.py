"""
Report Generation Tasks - Using database
"""
import asyncio

from celery import shared_task
from loguru import logger
from datetime import datetime, timedelta
from sqlalchemy import select, func

from app.core.database import db_manager, CollectedVideo, MonitoredAccount


@shared_task(bind=True, max_retries=1)
def generate_daily(self):
    """
    生成每日报告
    每天23:59执行
    """
    logger.info("Starting daily report generation")

    try:
        # 获取今日数据统计
        stats = _collect_daily_stats()

        # 生成各维度报告
        report = {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "overview": _generate_overview(stats),
            "platform_breakdown": _generate_platform_stats(stats),
            "top_videos": _get_top_videos_from_db(),
            "trends": _analyze_trends(stats),
            "generated_at": datetime.now().isoformat()
        }

        # 保存报告
        _save_report(report)

        logger.info("Daily report generated successfully")
        return {"status": "success", "report_date": report["date"]}

    except Exception as e:
        logger.error(f"Failed to generate daily report: {e}")
        raise self.retry(countdown=300, exc=e)


def _collect_daily_stats():
    """从数据库收集每日统计数据"""
    try:
        db_manager.init_db()

        async def _query():
            async with db_manager.get_session() as session:
                # 统计总视频数
                total_stmt = select(func.count(CollectedVideo.id))
                total_result = await session.execute(total_stmt)
                total_videos = total_result.scalar() or 0

                # 统计总播放量
                plays_stmt = select(func.sum(CollectedVideo.play_count))
                plays_result = await session.execute(plays_stmt)
                total_plays = plays_result.scalar() or 0

                # 按平台统计
                platforms = {}
                for platform in ['douyin', 'bilibili', 'xiaohongshu']:
                    platform_stmt = select(
                        func.count(CollectedVideo.id),
                        func.sum(CollectedVideo.play_count)
                    ).where(CollectedVideo.platform == platform)
                    platform_result = await session.execute(platform_stmt)
                    row = platform_result.one()
                    platforms[platform] = {
                        "videos": row[0] or 0,
                        "plays": row[1] or 0
                    }

                return {
                    "total_videos": total_videos,
                    "total_plays": total_plays,
                    "platforms": platforms
                }

        return asyncio.run(_query())
    except Exception as e:
        logger.error(f"Failed to collect daily stats: {e}")
        return {
            "total_videos": 0,
            "total_plays": 0,
            "platforms": {}
        }


def _generate_overview(stats: dict) -> dict:
    """生成概览"""
    return {
        "total_videos": stats["total_videos"],
        "total_plays": stats["total_plays"],
        "growth_rate": 0.15,  # TODO: 计算实际增长率
        "viral_videos_count": 0  # TODO: 统计爆款视频数
    }


def _generate_platform_stats(stats: dict) -> dict:
    """生成各平台统计"""
    return stats.get("platforms", {})


def _get_top_videos_from_db() -> list:
    """从数据库获取TOP视频"""
    try:
        db_manager.init_db()

        async def _query():
            async with db_manager.get_session() as session:
                stmt = select(CollectedVideo).order_by(
                    CollectedVideo.play_count.desc()
                ).limit(10)
                result = await session.execute(stmt)
                videos = result.scalars().all()

                return [
                    {
                        "video_id": v.video_id,
                        "title": v.title,
                        "plays": v.play_count or 0,
                        "platform": v.platform
                    }
                    for v in videos
                ]

        return asyncio.run(_query())
    except Exception as e:
        logger.error(f"Failed to get top videos: {e}")
        return []


def _analyze_trends(stats: dict) -> dict:
    """分析趋势"""
    # TODO: 基于实际数据做趋势分析
    return {
        "rising_categories": [],
        "declining_categories": [],
        "predictions": []
    }


def _save_report(report: dict):
    """保存报告"""
    logger.info(f"Saving report: {report['date']}")
    # TODO: 保存到数据库或文件存储
