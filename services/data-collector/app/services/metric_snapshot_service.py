"""
Metric Snapshot Service - 时序指标快照服务
管理视频指标的分钟级存储
"""
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from loguru import logger
from sqlalchemy import select, and_, desc

from app.models import db_manager, VideoMetricSnapshot, Video
from app.schemas import VideoMetrics


class MetricSnapshotService:
    """时序指标快照服务"""

    async def save_snapshot(
        self,
        video_id: str,
        platform: str,
        metrics: VideoMetrics
    ) -> VideoMetricSnapshot:
        """
        保存视频指标快照
        """
        async with db_manager.get_session() as session:
            snapshot = VideoMetricSnapshot(
                video_id=video_id,
                platform=platform,
                play_count=metrics.play_count,
                like_count=metrics.like_count,
                comment_count=metrics.comment_count,
                share_count=metrics.share_count,
                danmaku_count=getattr(metrics, 'danmaku_count', 0) or 0,
                coin_count=getattr(metrics, 'coin_count', 0) or 0,
                collect_count=getattr(metrics, 'collect_count', 0) or 0,
                engagement_rate=metrics.engagement_rate,
                like_ratio=metrics.like_ratio,
                comment_ratio=metrics.comment_ratio,
                share_ratio=metrics.share_ratio,
                snapshot_time=metrics.timestamp or datetime.now()
            )

            session.add(snapshot)
            await session.flush()

            logger.debug(f"Saved metric snapshot for video {video_id}")
            return snapshot

    async def get_latest_snapshot(self, video_id: str) -> Optional[VideoMetricSnapshot]:
        """获取视频的最新快照"""
        db_manager.init_db()
        async with db_manager.get_session() as session:
            stmt = select(VideoMetricSnapshot).where(
                VideoMetricSnapshot.video_id == video_id
            ).order_by(desc(VideoMetricSnapshot.snapshot_time)).limit(1)

            result = await session.execute(stmt)
            return result.scalar_one_or_none()

    async def get_snapshots(
        self,
        video_id: str,
        hours: int = 2
    ) -> List[VideoMetricSnapshot]:
        """获取最近N小时的快照列表"""
        db_manager.init_db()
        async with db_manager.get_session() as session:
            cutoff = datetime.now() - timedelta(hours=hours)
            stmt = select(VideoMetricSnapshot).where(
                and_(
                    VideoMetricSnapshot.video_id == video_id,
                    VideoMetricSnapshot.snapshot_time >= cutoff
                )
            ).order_by(VideoMetricSnapshot.snapshot_time.asc())

            result = await session.execute(stmt)
            return list(result.scalars().all())


# Singleton
metric_snapshot_service = MetricSnapshotService()


def get_metric_snapshot_service() -> MetricSnapshotService:
    return metric_snapshot_service