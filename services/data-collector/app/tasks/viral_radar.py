"""
Viral Radar Tasks - 爆款雷达核心任务
整合：视频采集 -> 指标快照 -> 增长检测 -> 用户匹配 -> 预警推送
"""
import asyncio
import time
from asyncio import Semaphore

from celery import shared_task
from loguru import logger
from typing import Dict, Any, List
from datetime import datetime

from app.adapters import get_platform_adapter
from app.adapters.bilibili_adapter import BilibiliAdapter
from app.services.viral_detector import viral_detector
from app.services.cleaning_pipeline import cleaning_pipeline
from app.services.metric_snapshot_service import get_metric_snapshot_service
from app.services.user_interest_service import (
    get_user_interest_service,
    get_alert_record_service
)
from app.services.alert_service import get_alert_service
from app.schemas import Video, VideoMetrics, ViralSignal
from app.models import db_manager, Video as VideoModel
from watchfiles import awatch

# 用于 Celery worker 中运行异步代码
_event_loop = None


def get_event_loop():
    """获取或创建事件循环"""
    global _event_loop
    try:
        if _event_loop is None or _event_loop.is_closed():
            _event_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(_event_loop)
        return _event_loop
    except RuntimeError:
        _event_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(_event_loop)
        return _event_loop


def run_async(coro):
    """安全运行异步协程（在Celery worker中）"""
    loop = get_event_loop()
    return loop.run_until_complete(coro)


def run_async_batch(coros, max_concurrent=2, delay_between=2):
    """批量运行协程，控制并发和间隔"""

    async def controlled_gather():
        semaphore = Semaphore(max_concurrent)

        async def controlled_coro(coro, index):
            async with semaphore:
                # 根据索引错开请求时间
                if index > 0:
                    await asyncio.sleep(delay_between * index)
                return await coro

        tasks = [
            controlled_coro(coro, i)
            for i, coro in enumerate(coros)
        ]

        return await asyncio.gather(*tasks, return_exceptions=True)

    loop = get_event_loop()
    results = loop.run_until_complete(controlled_gather())
    return results

@shared_task(bind=True, max_retries=2)
def scan_and_detect_viral(self):
    """
    扫描新视频并检测爆款
    每15分钟执行一次（密集扫描期）

    流程：
    1. 获取新发布视频（通过各平台适配器）
    2. 保存指标快照
    3. 检测增长异常
    4. 匹配用户并发送预警
    """
    logger.info("Starting viral radar scan and detect")

    results = {
        "videos_scanned": 0,
        "snapshots_saved": 0,
        "alerts_triggered": 0,
        "users_notified": 0
    }

    # 1. 扫描各平台新视频
    new_videos = scan_new_videos()
    results["videos_scanned"] = len(new_videos)
    logger.info(f"Scanned {len(new_videos)} new videos")

    # 2. 逐个处理视频
    metric_service = get_metric_snapshot_service()
    interest_service = get_user_interest_service()
    alert_service = get_alert_service()

    for video_data in new_videos:
        try:
            video = video_data["video"]
            platform = video_data["platform"]
            adapter = get_platform_adapter(platform)
            creator = run_async(adapter.get_creator_info(video.creator_id))
            # 避免爬崩
            time.sleep(3)
            # 3. 保存指标快照
            if video.metrics:
                run_async(metric_service.save_snapshot(
                    video_id=video.video_id,
                    platform=platform,
                    metrics=video.metrics
                ))
                results["snapshots_saved"] += 1

            # 4. 使用 ViralDetector 进行深度分析
            signal = run_async(viral_detector.detect(video, creator))
            logger.info(f'{video_data.get("video").title}爆款检测结果：{signal}')

            # 5. 如果 ViralDetector 认为需要预警
            if signal.should_alert:
                alert_level = signal.alert_level

                # 6. 匹配感兴趣的用户
                matched_users = run_async(interest_service.match_users_for_video(video, alert_level))

                for user_interest in matched_users:
                    # 7. 保存预警记录
                    run_async(get_alert_record_service().save_alert(
                        user_id=user_interest.user_id,
                        video=video,
                        signal=signal,
                        alert_level=alert_level
                    ))

                    # 8. 发送预警通知
                    try:
                        run_async(alert_service.send_viral_alert(
                            user_id=user_interest.user_id,
                            video=video,
                            signal=signal
                        ))
                        results["users_notified"] += 1
                    except Exception as e:
                        logger.error(f"Failed to send alert to user {user_interest.user_id}: {e}")

                    results["alerts_triggered"] += 1

        except Exception as e:
            logger.error(f"Failed to process video {video.video_id}: {e}")

    logger.info(f"Viral radar scan completed: {results}")
    return results


def scan_new_videos() -> List[Dict[str, Any]]:
    """
    扫描各平台新发布的视频
    目前支持：B站分区视频（其他平台留空）
    """

    # B站分区视频扫描
    from app.adapters.api.bilibili_api import get_videos_zones
    new_videos = []
    # B站分区视频扫描
    bilibili_rids = []
    zones = get_videos_zones()
    bilibili_rids.extend(zones.keys())
    for zone in zones.values():
        bilibili_rids.extend(zone.values())
    bilibili_rids = bilibili_rids[2:]   # 去除主站与VLOG
    try:
        # 初始化B站适配器（需要cookie）
        from app.core.config import settings
        adapter = BilibiliAdapter(cookie=settings.BILIBILI_COOKIE)

        for rid in bilibili_rids:
            try:
                coros = [
                    adapter.get_region_videos(rid=rid, pn=1, ps=20)
                    for rid in bilibili_rids
                ]

                # 批量执行，最多2个并发，间隔2秒
                videos = run_async_batch(coros, max_concurrent=5, delay_between=2)

                # 数据清洗
                for video in videos:
                    cleaned = cleaning_pipeline.process_video(video)
                    if cleaned:
                        # 检查是否已存在（通过video_id查重）
                        existing = check_video_exists(cleaned.video_id)
                        if not existing:
                            # 保存到数据库
                            save_video_to_db(cleaned)

                        new_videos.append({
                            "video": cleaned,
                            "platform": "bilibili"
                        })

            except Exception as e:
                logger.warning(f"Failed to scan B站分区 {rid}: {e}")

        # 关闭适配器
        run_async(adapter.close())

    except Exception as e:
        logger.error(f"Failed to scan B站 videos: {e}")

    # 其他平台留空，待实现
    # douyin: adapter.get_trending_videos()
    # xiaohongshu: adapter.get_trending_videos()

    return new_videos


def check_video_exists(video_id: str) -> bool:
    """检查视频是否已存在"""
    try:
        db_manager.init_db()

        async def _check():
            async with db_manager.get_session() as session:
                from sqlalchemy import select
                stmt = select(VideoModel).where(VideoModel.video_id == video_id)
                result = await session.execute(stmt)
                return result.scalar_one_or_none() is not None

        return run_async(_check())
    except Exception as e:
        logger.warning(f"Failed to check video existence: {e}")
        return False


def save_video_to_db(video: Video):
    """保存视频到数据库"""
    try:
        db_manager.init_db()

        async def _save():
            async with db_manager.get_session() as session:
                # 检查是否已存在
                from sqlalchemy import select
                stmt = select(VideoModel).where(VideoModel.video_id == video.video_id)
                result = await session.execute(stmt)
                existing = result.scalar_one_or_none()

                if not existing:
                    db_video = VideoModel(
                        platform=video.platform,
                        video_id=video.video_id,
                        video_url=video.url,
                        title=video.title or "",
                        description=video.description or "",
                        cover_image_url=video.cover_url or "",
                        duration=video.duration or 0,
                        publish_time=video.publish_time,
                        play_count=video.metrics.play_count if video.metrics else 0,
                        like_count=video.metrics.like_count if video.metrics else 0,
                        comment_count=video.metrics.comment_count if video.metrics else 0,
                        share_count=video.metrics.share_count if video.metrics else 0,
                        creator_id=video.creator_id or "",
                        creator_name=video.creator_name or "",
                        category=getattr(video, 'category', '') or ""
                    )
                    session.add(db_video)
                    logger.debug(f"Saved new video to DB: {video.video_id}")

        run_async(_save())
    except Exception as e:
        logger.warning(f"Failed to save video to DB: {e}")


@shared_task
def collect_region_videos(platform: str = "bilibili", rid: int = 1):
    """
    采集指定分区的视频
    可手动触发或定时执行
    """
    logger.info(f"Collecting region videos: platform={platform}, rid={rid}")

    if platform == "bilibili":
        try:
            from app.core.config import settings
            adapter = BilibiliAdapter(cookie=settings.BILIBILI_COOKIE)

            videos = run_async(adapter.get_region_videos(rid=rid, pn=1, ps=30))

            saved_count = 0
            for video in videos:
                cleaned = cleaning_pipeline.process_video(video)
                if cleaned:
                    if not check_video_exists(cleaned.video_id):
                        save_video_to_db(cleaned)
                        saved_count += 1

            run_async(adapter.close())

            logger.info(f"Collected {len(videos)} videos, saved {saved_count} new videos")
            return {"total": len(videos), "saved": saved_count}

        except Exception as e:
            logger.error(f"Failed to collect B站 region videos: {e}")
            return {"error": str(e)}

    else:
        logger.warning(f"Platform {platform} not supported for region collection")
        return {"error": "Platform not supported"}


@shared_task
def update_video_metrics_task(video_id: str, platform: str):
    """
    更新单个视频的指标并检测爆款
    用于密集监控期（发布后24小时内）的视频
    """
    logger.info(f"Updating metrics for video: {video_id}")

    try:
        adapter = get_platform_adapter(platform)
        video = run_async(adapter.get_video_detail(video_id))

        if not video:
            return {"status": "not_found"}

        # 保存指标快照
        if video.metrics:
            metric_service = get_metric_snapshot_service()
            run_async(metric_service.save_snapshot(
                video_id=video.video_id,
                platform=platform,
                metrics=video.metrics
            ))

        # 更新数据库中的指标
        update_video_metrics_in_db(video_id, video)

        return {"status": "success", "video_id": video_id}

    except Exception as e:
        logger.error(f"Failed to update video metrics: {e}")
        return {"status": "error", "error": str(e)}


def update_video_metrics_in_db(video_id: str, video: Video):
    """更新数据库中的视频指标"""
    try:
        db_manager.init_db()

        async def _update():
            async with db_manager.get_session() as session:
                from sqlalchemy import select, update
                stmt = select(VideoModel).where(VideoModel.video_id == video_id)
                result = await session.execute(stmt)
                db_video = result.scalar_one_or_none()

                if db_video and video.metrics:
                    db_video.play_count = video.metrics.play_count
                    db_video.like_count = video.metrics.like_count
                    db_video.comment_count = video.metrics.comment_count
                    db_video.share_count = video.metrics.share_count
                    db_video.updated_at = datetime.now()

        run_async(_update())
    except Exception as e:
        logger.warning(f"Failed to update video metrics in DB: {e}")
