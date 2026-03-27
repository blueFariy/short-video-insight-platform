from dataclasses import dataclass, field
from typing import List

from app.schemas.video_metrics import VideoMetrics


@dataclass
class VideoMetricHistory:
    """Historical metrics for a video"""
    video_id: str
    metrics: List[VideoMetrics] = field(default_factory=list)

    def add_metric(self, metric: VideoMetrics):
        """Add a metric snapshot"""
        self.metrics.append(metric)
