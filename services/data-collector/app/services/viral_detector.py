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


class CreatorAnalyzer:
    """UP主维度分析"""

    def __init__(self):
        pass

    def analyze(
            self,
            creator: Creator,
            current_video_metrics: VideoMetrics,
            benchmark: dict = None
    ) -> Dict[str, Any]:
        """
        分析UP主维度

        Args:
            creator: 创作者信息
            current_video_metrics: 当前视频指标
            benchmark: category_benchmarks中的基准数据

        Returns:
            Dict with up_level, is_outstanding, factors
        """
        platform = creator.platform

        # 从基准数据获取阈值，如果没有则使用默认配置
        if benchmark:
            conf = {
                "small_up_followers": benchmark.get("creator_follower_count", 10000),
                "medium_up_followers": benchmark.get("creator_follower_count", 100000) * 2,
            }
        else:
            conf = DEFAULT_THRESHOLDS.get(platform, DEFAULT_THRESHOLDS["bilibili"])

        follower_count = creator.follower_count
        video_count = creator.video_count
        avg_play = creator.avg_play_count

        # 判断UP主层级
        if follower_count < conf.get("small_up_followers", 10000):
            up_level = "small"  # 小UP主
        elif follower_count < conf.get("medium_up_followers", 100000):
            up_level = "medium"  # 中UP主
        else:
            up_level = "big"  # 大UP主

        factors = []
        is_outstanding = False

        # 分析维度1：该视频播放量是否远超UP主平均水平
        if avg_play > 0 and current_video_metrics.play_count > avg_play * 3:
            factors.append(f"播放量是UP主平均的{current_video_metrics.play_count / avg_play:.1f}倍")
            is_outstanding = True

        # 分析维度2：该视频互动是否远超UP主日常
        current_engagement = current_video_metrics.engagement_rate
        if current_engagement > 0.15:  # 15%以上互动率为优秀
            factors.append(f"超高互动率{current_engagement:.1%}")
            is_outstanding = True

        # 分析维度3：小UP主的爆款更值得关注
        if up_level == "small" and current_video_metrics.play_count > 10000:
            factors.append(f"小UP主({follower_count}粉丝)达成{current_video_metrics.play_count}播放")
            is_outstanding = True

        return {
            "up_level": up_level,
            "follower_count": follower_count,
            "video_count": video_count,
            "avg_play_count": avg_play,
            "is_outstanding": is_outstanding,
            "factors": factors
        }


class VideoContentAnalyzer:
    """视频内容维度分析"""

    def __init__(self):
        pass

    def analyze(
            self,
            video: Video,
            creator: Creator = None,
            benchmark: dict = None
    ) -> Dict[str, Any]:
        """
        分析视频内容维度

        Args:
            video: 视频数据
            creator: 创作者信息（可选）
            benchmark: category_benchmarks中的基准数据（可选）

        Returns:
            Dict with content_score, factors, is_viral
        """
        platform = video.platform

        # 优先使用基准数据，否则使用默认配置
        if benchmark:
            # 基准值100表示100%阈值 -> 转换为小数 1.0
            # 基准值1表示1%阈值 -> 转换为小数 0.01
            video_like_ratio = benchmark.get("video_like_ratio", 100) / 100.0
            video_collect_ratio = benchmark.get("video_collect_ratio", 100) / 100.0
            video_comment_ratio = benchmark.get("video_comment_ratio", 100) / 100.0

            conf = {
                "absolutely_viral_play_count": 500000,  # 默认绝对爆款阈值
                "small_up_like_ratio": video_like_ratio,
                "medium_up_like_ratio": video_like_ratio * 0.6,
                "big_up_like_ratio": video_like_ratio * 0.4,
                "coin_ratio_threshold": 0.005,
                "short_video_max": 180,
                "medium_video_max": 600,
                "new_video_hours": benchmark.get("video_publish_hours", 24),
                # 基准中的收藏率、评论率
                "video_collect_ratio": video_collect_ratio,
                "video_comment_ratio": video_comment_ratio,
                # 爆款阈值
                "viral_threshold": benchmark.get("viral_threshold", 50),
            }
        else:
            conf = DEFAULT_THRESHOLDS.get(platform, DEFAULT_THRESHOLDS["bilibili"])

        metrics = video.metrics

        factors = []
        score = 0.0
        is_viral = False

        # 维度1：绝对爆款（播放量超过阈值）
        if metrics.play_count >= conf.get("absolutely_viral_play_count", 500000):
            factors.append(f"绝对爆款：{metrics.play_count // 10000}万播放")
            score += 50
            is_viral = True

        # 维度2：点赞率（根据UP主层级不同标准）
        like_ratio = metrics.like_ratio
        if creator:
            up_level = "small" if creator.follower_count < conf.get("small_up_followers", 10000) \
                else "medium" if creator.follower_count < conf.get("medium_up_followers", 100000) \
                else "big"
            threshold_key = f"{up_level}_up_like_ratio"
            like_threshold = conf.get(threshold_key, 0.03)
        else:
            like_threshold = conf.get("small_up_like_ratio", 0.05)

        if like_ratio >= like_threshold:
            factors.append(f"高点赞率{like_ratio:.1%}")
            score += 20 * (like_ratio / like_threshold)  # 越高分越高
            is_viral = True

        # 维度2.1: 收藏率（如果有基准数据）
        if "video_collect_ratio" in conf:
            collect_ratio = metrics.collect_ratio if hasattr(metrics, 'collect_ratio') else 0
            if collect_ratio >= conf.get("video_collect_ratio", 0.05):
                factors.append(f"高收藏率{collect_ratio:.1%}")
                score += 15 * (collect_ratio / conf.get("video_collect_ratio", 0.05))
                is_viral = True

        # 维度2.2: 评论率（如果有基准数据）
        if "video_comment_ratio" in conf:
            comment_ratio = metrics.comment_ratio if hasattr(metrics, 'comment_ratio') else 0
            if comment_ratio >= conf.get("video_comment_ratio", 0.02):
                factors.append(f"高评论率{comment_ratio:.1%}")
                score += 10 * (comment_ratio / conf.get("video_comment_ratio", 0.02))
                is_viral = True

        # 维度3：投币率（B站特有）
        if platform == "bilibili":
            coin_ratio = metrics.coin_ratio
            if coin_ratio >= conf.get("coin_ratio_threshold", 0.005):
                factors.append(f"高投币率{coin_ratio:.1%}")
                score += 15 * (coin_ratio / conf.get("coin_ratio_threshold", 0.005))
                is_viral = True

            # 弹幕密度（B站特有）
            if metrics.danmaku_count > 0 and video.duration > 0:
                danmaku_per_min = metrics.danmaku_count / (video.duration / 60)
                if danmaku_per_min > 50:  # 每分钟超过50条弹幕
                    factors.append(f"高弹幕密度{danmaku_per_min} 条/分钟")
                    score += 10

        # 维度4：发布时间（24小时内为新视频，72小时内为热视频）
        if video.publish_time:
            hours_ago = (datetime.now() - video.publish_time).total_seconds() / 3600
            if hours_ago < conf.get("new_video_hours", 24):
                factors.append(f"新发布视频({hours_ago:.0f}小时前)")
                score += 10
            elif hours_ago < 72:
                factors.append(f"热榜视频({hours_ago:.0f}小时前)")
                score += 5

            # 播放量/发布时间 = 时速（判断增长趋势）
            if hours_ago > 0 and hours_ago < 24:
                play_per_hour = metrics.play_count / hours_ago
                if play_per_hour > 10000:  # 每小时1万播放
                    factors.append(f"高速增长{play_per_hour:.0f}播放/小时")
                    score += 20
                    is_viral = True

        # 维度5：时长分析
        duration = video.duration
        if duration > 0:
            if duration < conf.get("short_video_max", 180):
                factors.append(f"短视频{duration // 60}分钟")
            elif duration < conf.get("medium_video_max", 600):
                factors.append(f"中视频{duration // 60}分钟")
            else:
                factors.append(f"长视频{duration // 60}分钟")

        # 维度6：互动综合分
        total_engagement = (
                metrics.like_count +
                metrics.comment_count * 2 +  # 评论权重更高
                metrics.share_count * 3 +  # 分享权重最高
                metrics.collect_count * 2
        ) if hasattr(metrics, 'collect_count') else (
                metrics.like_count +
                metrics.comment_count * 2 +
                metrics.share_count * 3
        )
        if metrics.play_count > 0:
            engagement_score = total_engagement / metrics.play_count
            if engagement_score > 0.2:
                factors.append(f"高综合互动{engagement_score:.1%}")
                score += 15

        return {
            "score": score,
            "factors": factors,
            "is_viral": is_viral,
            "is_absolutely_viral": metrics.play_count >= conf.get("absolutely_viral_play_count", 500000)
        }


class ViralDetector:
    """爆款识别器 - 多维度判断"""

    def __init__(self):
        self.creator_analyzer = CreatorAnalyzer()
        self.content_analyzer = VideoContentAnalyzer()

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
