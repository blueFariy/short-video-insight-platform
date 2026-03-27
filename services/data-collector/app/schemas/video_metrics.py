from dataclasses import dataclass, field
from datetime import datetime


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
    collect_count: int = 0

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
        self.coin_ratio = (self.coin_count) / max_play
        if self.play_count > 0 and self.danmaku_count > 0:
            self.danmaku_density = self.danmaku_count / 60  # 假设平均1分钟

        # 小红书特有
        max_like = max(self.like_count, 1)
        self.collect_ratio = self.collect_count / max_like
