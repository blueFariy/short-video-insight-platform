from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class Creator:
    """Creator/Account data model"""
    creator_id: str
    platform: str
    name: str
    url: str
    id: Optional[int] = None
    avatar_url: Optional[str] = None
    category: str = "general"
    description: Optional[str] = None

    # Stats
    follower_count: int = 0
    following_count: int = 0
    total_likes: int = 0
    video_count: int = 0
    avg_play_count: float = 0.0  # 平均播放量

    # Additional fields
    status: str = "active"

    # Timestamps
    last_video_date: datetime = None
    first_video_date: datetime = None
    created_at: datetime = field(default_factory=datetime.now)
    last_updated: datetime = field(default_factory=datetime.now)

    @property
    def update_interval(self) -> float:
        """更新频率（小时）"""
        return (self.last_video_date - self.first_video_date).total_seconds() / self.video_count / 3600
