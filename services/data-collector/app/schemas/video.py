from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any

from app.schemas.video_metrics import VideoMetrics


@dataclass
class Video:
    """Video data model"""
    # Basic info
    video_id: str
    platform: str
    title: str
    url: str

    # Creator info
    creator_id: str
    creator_name: str

    # Media info
    cover_url: str
    duration: int  # 秒

    # Metrics
    metrics: VideoMetrics

    # Timestamps
    publish_time: Optional[datetime] = None
    collected_at: datetime = field(default_factory=datetime.now)

    # Category (from platform's category/zone)
    category: Optional[str] = None

    # Platform-specific fields
    bvid: Optional[str] = None  # B站
    description: Optional[str] = None  # B站
    note_id: Optional[str] = None  # 小红书

    # Viral detection
    viral_factors: Dict[str, Any] = field(default_factory=dict)

    @property
    def play_count(self) -> int:
        """播放量"""
        return self.metrics.play_count

    @property
    def like_rate(self) -> float:
        """点赞率（%）"""
        if self.metrics.play_count == 0:
            return 0
        return (self.metrics.like_count / self.metrics.play_count) * 100

    @property
    def comment_rate(self) -> float:
        """评论率（%）"""
        if self.metrics.play_count == 0:
            return 0
        return (self.metrics.comment_count / self.metrics.play_count) * 100

    @property
    def favorite_rate(self) -> float:
        """收藏率（%）"""
        if self.metrics.play_count == 0:
            return 0
        return (self.metrics.favorite_count / self.metrics.play_count) * 100

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "video_id": self.video_id,
            "platform": self.platform,
            "title": self.title,
            "url": self.url,
            "creator_id": self.creator_id,
            "creator_name": self.creator_name,
            "cover_url": self.cover_url,
            "duration": self.duration,
            "category": self.category,
            "metrics": {
                "play_count": self.metrics.play_count,
                "like_count": self.metrics.like_count,
                "comment_count": self.metrics.comment_count,
                "share_count": self.metrics.share_count,
                "favorite_count": self.metrics.favorite_count,
                "engagement_rate": self.metrics.engagement_rate,
            },
            "publish_time": self.publish_time.isoformat() if self.publish_time else None,
            "collected_at": self.collected_at.isoformat(),
            "viral_factors": self.viral_factors
        }
