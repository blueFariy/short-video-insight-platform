from dataclasses import dataclass
from typing import Optional, List


@dataclass
class CategoryBenchmarkSchema:
    """分类基准数据 Schema"""
    id: Optional[int] = None
    platform: str = ""
    category: str = ""

    # 平台、分类系数
    platform_factor: float = 0.0
    category_factor: float = 0.0

    # 创作者维度
    creator_follower_factor: float = 0.0
    creator_avg_play_count_factor: float = 0.0
    creator_update_interval_hours: Optional[int] = None

    # 视频数据维度
    video_like_ratio: float = 0.0
    video_collect_ratio: float = 0.0
    video_comment_ratio: float = 0.0
    video_publish_hours: Optional[int] = None
    video_duration_seconds_min: Optional[int] = None
    video_duration_seconds_max: Optional[int] = None
    decay_period: Optional[float] = 60.0

    # 爆款阈值 [yellow, orange, red]
    viral_threshold: List[float] = None

    # 预警类型
    alert_level: List[str] = None

    def __post_init__(self):
        if self.viral_threshold is None:
            self.viral_threshold = [3.0, 8.0, 20.0]
        if self.alert_level is None:
            self.alert_level = ["yellow", "orange", "red"]