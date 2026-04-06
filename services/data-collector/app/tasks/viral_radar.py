"""
Viral Radar Tasks - 爆款雷达核心任务
"""
import asyncio
import random
import time
from asyncio import Semaphore
from typing import Dict, Any, List, Iterator, Generator, Optional, Set

from celery import shared_task
from loguru import logger
from datetime import datetime

from app.adapters import get_platform_adapter
from app.adapters.api.bilibili_api import get_main_zones_by_category
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
from app.core.redis_client import get_redis_client

# 用于 Celery worker 中运行异步代码
_event_loop = None

# 批次配置
BATCH_SIZE = 10  # 每批处理视频数量
SCAN_PROGRESS_KEY = "viral_radar_scan_progress"  # 扫描进度记录key


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
                if index > 0:
                    await asyncio.sleep(delay_between * index)
                return await coro

        tasks = [controlled_coro(coro, i) for i, coro in enumerate(coros)]
        return await asyncio.gather(*tasks, return_exceptions=True)

    loop = get_event_loop()
    results = loop.run_until_complete(controlled_gather())
    return results


@shared_task(bind=True, max_retries=2)
def scan_and_detect_viral(self):
    """
    扫描新视频并检测爆款 - 生成器模式版
    采用真正的生成器流式处理
    """
    logger.info("Starting viral radar scan and detect (generator mode)")

    results = {
        "videos_scanned": 0,
        "snapshots_saved": 0,
        "alerts_triggered": 0,
        "users_notified": 0,
        "batches_processed": 0,
        "zones_completed": 0,
        "errors": []
    }

    # 初始化服务
    metric_service = get_metric_snapshot_service()
    interest_service = get_user_interest_service()
    alert_service = get_alert_service()

    # 批量处理视频
    batch = []

    # ✅ 使用生成器流式获取视频（已包含创作者信息）
    for video_data in scan_new_videos_generator():
        try:
            # 检查是否是错误信息
            if video_data.get("is_error"):
                logger.warning(f"Error in video scan: {video_data.get('error')}")
                continue

            video = video_data["video"]
            creator = video_data.get("creator")
            platform = video_data["platform"]
            zone = video_data.get("zone", "unknown")

            results["videos_scanned"] += 1
            logger.debug(f"Processing video {video.video_id} from zone {zone}")

            # ✅ 保存指标快照
            if video.metrics:
                run_async(metric_service.save_snapshot(
                    video_id=video.video_id,
                    platform=platform,
                    metrics=video.metrics
                ))
                results["snapshots_saved"] += 1

            # ✅ 添加到批次
            batch.append({
                "video": video,
                "creator": creator,
                "platform": platform
            })

            # ✅ 达到批次大小，立即处理
            if len(batch) >= BATCH_SIZE:
                # 处理批次
                batch_results = _process_video_batch(
                    batch, interest_service, alert_service
                )

                # 累加结果
                results["alerts_triggered"] += batch_results["alerts_triggered"]
                results["users_notified"] += batch_results["users_notified"]
                results["batches_processed"] += 1

                logger.info(f"Processed batch {results['batches_processed']}: "
                            f"{len(batch)} videos, {batch_results['alerts_triggered']} alerts")

                # 清空批次
                batch = []

        except Exception as e:
            logger.error(f"Failed to process video {video_data.get('video', {}).video_id}: {e}")
            results["errors"].append(str(e))

    # ✅ 处理最后一批（不足BATCH_SIZE的）
    if batch:
        batch_results = _process_video_batch(batch, interest_service, alert_service)
        results["alerts_triggered"] += batch_results["alerts_triggered"]
        results["users_notified"] += batch_results["users_notified"]
        results["batches_processed"] += 1
        logger.info(f"Processed final batch: {len(batch)} videos, "
                    f"{batch_results['alerts_triggered']} alerts")

    # 清理扫描进度
    _clear_scan_progress()

    logger.info(f"Viral radar scan completed: {results}")
    return results


def _process_video_batch(batch: List[Dict], interest_service, alert_service) -> Dict:
    """
    处理一批视频：爆款检测 + 用户匹配 + 预警推送
    """
    results = {
        "videos": [],
        "alerts_triggered": 0,
        "users_notified": 0
    }

    for item in batch:
        video = item["video"]
        creator = item["creator"]
        platform = item["platform"]

        try:
            # ✅ 爆款检测（以主分区为主）
            category = video.category
            video.category = get_main_zones_by_category(video.category)
            signal = run_async(viral_detector.detect(video, creator))
            if signal and signal.should_alert:
                logger.info(f'Video {video.title} triggered alert: level={signal.alert_level}')
                # ✅ 匹配用户
                matched_users = run_async(interest_service.match_users_for_video(
                    video, signal.alert_level
                ))
                video.category = category
                # ✅ 为每个用户发送预警
                for user_interest in matched_users:
                    try:
                        # 保存预警记录
                        run_async(get_alert_record_service().save_alert(
                            user_id=user_interest.user_id,
                            video=video,
                            signal=signal,
                            alert_level=signal.alert_level
                        ))

                        # 发送通知
                        run_async(alert_service.send_viral_alert(
                            user_id=user_interest.user_id,
                            video=video,
                            signal=signal
                        ))

                        results["users_notified"] += 1
                        results["alerts_triggered"] += 1

                    except Exception as e:
                        logger.error(f"Failed to send alert to user {user_interest.user_id}: {e}")

            results["videos"].append(video.video_id)

        except Exception as e:
            logger.error(f"Failed to detect viral for video {video.video_id}: {e}")

    return results


def _fetch_creator_with_retry(adapter, creator_id: str, max_retries: int = 2):
    """
    带重试机制的创作者信息获取
    控制请求频率，避免触发反爬
    """
    for attempt in range(max_retries + 1):
        try:
            start_time = time.time()
            logger.debug(f"Fetching creator {creator_id} (attempt {attempt + 1})")

            # 获取创作者信息
            creator_info = run_async(adapter.get_creator_info(creator_id))
            if not creator_info:
                raise Exception("")

            elapsed = time.time() - start_time
            logger.debug(f"Fetched creator {creator_id} in {elapsed:.2f}s")

            # ✅ 成功后随机延迟，避免请求过快
            if elapsed < 3:
                wait_time = random.uniform(3, 5)
                logger.debug(f"Waiting {wait_time:.2f}s before next request")
                time.sleep(wait_time)

            return creator_info

        except Exception as e:
            logger.warning(f"Failed to fetch creator {creator_id} (attempt {attempt + 1}): {e}")

            if attempt < max_retries:
                wait_time = random.uniform(3, 5)  # 重试前也随机等待
                logger.debug(f"Waiting {wait_time:.2f}s before retry")
                time.sleep(wait_time)
            else:
                logger.error(f"Failed to fetch creator {creator_id} after {max_retries + 1} attempts")
                return None

    return None


def scan_new_videos_generator() -> Generator[Dict[str, Any], None, None]:
    """
    分批扫描各平台新发布的视频，并获取创作者信息

    特点：
    1. 每爬取到一个视频就立即获取其创作者信息
    2. 视频和创作者信息一起 yield
    3. 爬取完一个分区后记录进度
    4. 支持断点续传
    """
    # B站分区视频扫描
    from app.adapters.api.bilibili_api import get_videos_zones

    zones = get_videos_zones()
    bilibili_rids = []
    for zone in zones.values():
        bilibili_rids.extend(zone.values())
    bilibili_rids = bilibili_rids[:]

    try:
        from app.core.config import settings
        adapter = BilibiliAdapter(cookie=settings.BILIBILI_COOKIE)

        # ✅ 获取已完成的分区进度
        completed_rids = _get_completed_rids()
        logger.info(f"Starting scan, {len(completed_rids)} zones already completed")

        for idx, rid in enumerate(bilibili_rids):
            # 跳过已完成的分区（断点续传）
            if rid in completed_rids:
                logger.info(f"Skipping already completed zone: {rid}")
                continue

            logger.info(f"Scanning B站分区 {rid} ({idx + 1}/{len(bilibili_rids)})")

            try:
                # ✅ 爬取单个分区
                coros = [adapter.get_region_videos(rid=rid, pn=1, ps=20)]
                videos = run_async_batch(coros, max_concurrent=3, delay_between=1)

                zone_video_count = 0

                # ✅ 处理该分区的每个视频
                for result in videos:
                    # 处理异常
                    if isinstance(result, Exception):
                        logger.warning(f"Zone {rid} API error: {result}")
                        continue

                    if not isinstance(result, list):
                        logger.warning(f"Zone {rid} returned unexpected type: {type(result)}")
                        continue

                    # ✅ 逐个视频处理并获取创作者信息
                    for video in result:
                        if not hasattr(video, 'video_id'):
                            continue

                        cleaned = cleaning_pipeline.process_video(video)
                        if not cleaned:
                            continue

                        # ✅ 检查视频是否已存在
                        if check_video_exists(cleaned.video_id):
                            logger.debug(f"Video {cleaned.video_id} already exists, skipping")
                            continue

                        # ✅ 保存视频到数据库
                        save_video_to_db(cleaned)
                        zone_video_count += 1

                        # ✅ 获取创作者信息（带重试和延迟）
                        creator_info = None
                        if cleaned.creator_id:
                            creator_info = _fetch_creator_with_retry(adapter, cleaned.creator_id)

                        # ✅ 立即 yield 视频和创作者信息
                        yield {
                            "video": cleaned,
                            "creator": creator_info,
                            "platform": "bilibili",
                            "zone": rid
                        }

                # ✅ 记录完成的分区
                _mark_zone_completed(rid)
                logger.info(f"Zone {rid} completed: {zone_video_count} new videos")

            except Exception as e:
                logger.warning(f"Failed to scan B站分区 {rid}: {e}")
                # 出错时记录错误但不中断
                yield {
                    "error": str(e),
                    "zone": rid,
                    "is_error": True
                }

        # 关闭适配器
        run_async(adapter.close())

    except Exception as e:
        logger.error(f"Failed to scan B站 videos: {e}")


def _get_completed_rids() -> Set[int]:
    """获取已完成的分区ID集合"""
    try:
        redis_client = get_redis_client()
        completed = redis_client.smembers(SCAN_PROGRESS_KEY)
        if isinstance(completed, set):
            return {int(rid) for rid in completed if rid}
        return set()
    except Exception as e:
        logger.warning(f"Failed to get completed rids: {e}")
        return set()


def _mark_zone_completed(rid: int):
    """标记分区为已完成"""
    try:
        redis_client = get_redis_client()
        redis_client.sadd(SCAN_PROGRESS_KEY, rid)
        redis_client.expire(SCAN_PROGRESS_KEY, 86400)  # 24小时过期
    except Exception as e:
        logger.warning(f"Failed to mark zone completed: {e}")


def _clear_scan_progress():
    """清理扫描进度"""
    try:
        redis_client = get_redis_client()
        redis_client.delete(SCAN_PROGRESS_KEY)
    except Exception as e:
        logger.warning(f"Failed to clear scan progress: {e}")


def scan_new_videos() -> List[Dict[str, Any]]:
    """兼容旧版本的扫描函数"""
    return list(scan_new_videos_generator())


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
    """采集指定分区的视频"""
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
        logger.warning(f"Platform {platform} not supported")
        return {"error": "Platform not supported"}


@shared_task
def update_video_metrics_task(video_id: str, platform: str):
    """更新单个视频的指标"""
    logger.info(f"Updating metrics for video: {video_id}")

    try:
        adapter = get_platform_adapter(platform)
        video = run_async(adapter.get_video_detail(video_id))

        if not video:
            return {"status": "not_found"}

        if video.metrics:
            metric_service = get_metric_snapshot_service()
            run_async(metric_service.save_snapshot(
                video_id=video.video_id,
                platform=platform,
                metrics=video.metrics
            ))

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
                from sqlalchemy import select
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