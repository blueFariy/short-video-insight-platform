"""
Data Models for Platform Adapters
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any


@dataclass
class VideoMetrics:
    """Video metrics data"""
    video_id: str
    platform: str
    play_count: int = 0
    like_count: int = 0
    comment_count: int = 0
    share_count: int = 0
    favorite_count: int = 0
    coin_count: int = 0  # B站特有
    danmaku_count: int = 0  # B站特有（弹幕）
    collect_count: int = 0  # 小红书特有

    # 计算指标
    engagement_rate: float = 0.0  # 互动率
    like_ratio: float = 0.0  # 点赞/播放比
    comment_ratio: float = 0.0  # 评论/播放比
    share_ratio: float = 0.0  # 分享/播放比

    # 质量指标
    coin_ratio: float = 0.0  # B站：投币率
    danmaku_density: float = 0.0  # B站：弹幕密度
    collect_ratio: float = 0.0  # 小红书：收藏率

    timestamp: datetime = field(default_factory=datetime.now)

    def calculate_ratios(self):
        """计算各项比率"""
        max_play = max(self.play_count, 1)

        self.like_ratio = self.like_count / max_play
        self.comment_ratio = self.comment_count / max_play
        self.share_ratio = self.share_count / max_play
        self.engagement_rate = (self.like_count + self.comment_count + self.share_count) / max_play

        # B站特有指标
        if self.play_count > 0 and self.danmaku_count > 0:
            self.danmaku_density = self.danmaku_count / 60  # 假设平均1分钟

        # 小红书特有
        max_like = max(self.like_count, 1)
        self.collect_ratio = self.collect_count / max_like


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

    # Platform-specific fields
    bvid: Optional[str] = None  # B站
    note_id: Optional[str] = None  # 小红书

    # Viral detection
    viral_factors: Dict[str, Any] = field(default_factory=dict)

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


@dataclass
class Creator:
    """Creator/Account data model"""
    creator_id: str
    platform: str
    name: str
    url: str
    avatar_url: Optional[str] = None
    category: str = "general"
    description: Optional[str] = None

    # Stats
    follower_count: int = 0
    video_count: int = 0
    avg_play_count: float = 0.0  # 平均播放量

    # Timestamps
    created_at: datetime = field(default_factory=datetime.now)
    last_updated: datetime = field(default_factory=datetime.now)


@dataclass
class VideoMetricHistory:
    """Historical metrics for a video"""
    video_id: str
    metrics: List[VideoMetrics] = field(default_factory=list)

    def add_metric(self, metric: VideoMetrics):
        """Add a metric snapshot"""
        self.metrics.append(metric)

    def get_growth_rate(self) -> float:
        """Calculate growth rate"""
        if len(self.metrics) < 2:
            return 0.0

        latest = self.metrics[-1]
        previous = self.metrics[-2]

        if previous.play_count == 0:
            return 0.0

        return (latest.play_count - previous.play_count) / previous.play_count


@dataclass
class ViralSignal:
    """Viral detection signal"""
    video_id: str

    # Scores
    growth_score: float = 0.0
    growth_stage: str = "unknown"  # 'embryo', 'takeoff', 'explosion', 'plateau'
    authenticity: float = 1.0  # 数据真实性
    sentiment_shift: float = 0.0  # 情感变化

    # Cross-platform
    cross_platform_spread: Dict[str, Any] = field(default_factory=dict)

    # Benchmark
    vs_benchmark: Dict[str, Any] = field(default_factory=dict)

    # Decision
    should_alert: bool = False
    alert_level: str = "none"  # 'none', 'yellow', 'orange', 'red'
    message: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "video_id": self.video_id,
            "growth_score": self.growth_score,
            "growth_stage": self.growth_stage,
            "authenticity": self.authenticity,
            "sentiment_shift": self.sentiment_shift,
            "cross_platform_spread": self.cross_platform_spread,
            "vs_benchmark": self.vs_benchmark,
            "should_alert": self.should_alert,
            "alert_level": self.alert_level,
            "message": self.message
        }
