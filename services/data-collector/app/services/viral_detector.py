"""
Viral Detection Service - Multi-dimensional viral video detection

爆款检测核心逻辑：
1. UP主维度：粉丝数、视频数、平均播放量
2. 视频维度：播放量、点赞率、投币率、发布时间、时长
3. 绝对爆款：跨平台绝对播放量阈值
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from loguru import logger

from app.schemas import Video, VideoMetrics, VideoMetricHistory, ViralSignal, Creator
from app.models import db_manager
from app.utils import ViralVideoAnalyzer, get_benchmarks

# 默认阈值配置（无基准数据时使用）
DEFAULT_THRESHOLDS = {
    "bilibili": {
        "absolutely_viral_play_count": 500000,
        "small_up_followers": 10000,
        "medium_up_followers": 100000,
        "small_up_like_ratio": 0.05,
        "medium_up_like_ratio": 0.03,
        "big_up_like_ratio": 0.02,
        "coin_ratio_threshold": 0.005,
        "short_video_max": 180,
        "medium_video_max": 600,
        "new_video_hours": 24,
    },
    "douyin": {
        "absolutely_viral_play_count": 1000000,
        "small_up_followers": 100000,
        "medium_up_followers": 1000000,
        "small_up_like_ratio": 0.08,
        "medium_up_like_ratio": 0.05,
        "big_up_like_ratio": 0.03,
        "new_video_hours": 12,
    },
    "xiaohongshu": {
        "absolutely_viral_play_count": 100000,
        "small_up_followers": 5000,
        "medium_up_followers": 50000,
        "small_up_like_ratio": 0.10,
        "medium_up_like_ratio": 0.05,
        "big_up_like_ratio": 0.03,
        "new_video_hours": 24,
    }
}

class ViralDetector:
    """爆款识别器 - 多维度判断"""

    def __init__(self):
        pass

    async def detect(
            self,
            video: Video,
            creator: Creator = None,
            history: List[VideoMetrics] = None
    ) -> ViralSignal:
        """
        多维度爆款检测

        Args:
            video: 视频数据
            creator: UP主信息（可选，提供则分析更准确）
            history: 历史指标数据（可选）

        Returns:
            ViralSignal对象
        """
        logger.info(f"Detecting viral for video: {video.video_id}")

        signals = ViralSignal(video_id=video.video_id)

        # 获取视频分类的基准数据
        platform = video.platform
        benchmarks = await get_benchmarks(platform)
        analyzer = ViralVideoAnalyzer(benchmarks)
        result = analyzer.analyze(video, creator)

        logger.info(f"video viral analyzer result: {result}")

        signals.message = ""

        # 添加分析因素
        all_factors = result.get("factors", [])

        signals.vs_benchmark = {
            "factors": all_factors,
        }

        signals.should_alert = result.get("score", 0.0) >= 3.0
        signals.alert_level = result.get("alert_level")

        return signals


# Singleton instance
viral_detector = ViralDetector()


def get_viral_detector() -> ViralDetector:
    """Get viral detector instance"""
    return viral_detector
