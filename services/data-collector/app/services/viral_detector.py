"""
Viral Detection Service - Multi-dimensional viral video detection
"""
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import numpy as np
from loguru import logger

from app.models import Video, VideoMetrics, VideoMetricHistory, ViralSignal
from app.core.config import settings


class GrowthCurveAnalyzer:
    """增长曲线分析 - 识别爆发拐点"""

    def __init__(self):
        self.min_history_points = 3

    async def analyze(
        self,
        video_id: str,
        history: List[VideoMetrics]
    ) -> Dict[str, Any]:
        """
        分析增长曲线

        Returns:
            Dict with score, stage, message
        """
        if len(history) < self.min_history_points:
            return {
                "score": 0.0,
                "stage": "unknown",
                "message": "数据点不足，无法分析"
            }

        # 提取时间序列
        timestamps = [h.timestamp for h in history]
        play_counts = [h.play_count for h in history]

        # 计算增长率
        growth_rates = []
        for i in range(1, len(play_counts)):
            if play_counts[i-1] > 0:
                rate = (play_counts[i] - play_counts[i-1]) / play_counts[i-1]
                growth_rates.append(rate)
            else:
                growth_rates.append(0.0)

        if not growth_rates:
            return {
                "score": 0.0,
                "stage": "unknown",
                "message": "无法计算增长率"
            }

        # 判断增长阶段
        recent_growth = growth_rates[-1] if growth_rates else 0.0
        avg_growth = sum(growth_rates) / len(growth_rates) if growth_rates else 0.0

        # 爆发特征：增长率突然大幅提升
        if recent_growth > avg_growth * 3 and recent_growth > 0.5:
            return {
                "score": recent_growth,
                "stage": "takeoff",
                "message": f"播放量突然爆发，最近增长率{recent_growth:.1%}",
                "is_viral": True
            }

        # 平稳期
        if recent_growth < 0.05 and avg_growth < 0.1:
            return {
                "score": recent_growth,
                "stage": "plateau",
                "message": "增长趋于平稳",
                "is_viral": False
            }

        # 早期特征：虽然基数小但增长稳定
        if avg_growth > 0.2 and max(play_counts) < 10000:
            return {
                "score": avg_growth,
                "stage": "embryo",
                "message": "早期潜力视频，增速稳定",
                "is_viral": True
            }

        # 正常增长
        return {
            "score": recent_growth,
            "stage": "normal",
            "message": "增长正常",
            "is_viral": False
        }


class AuthenticityChecker:
    """数据真实性检查 - 去噪算法"""

    def __init__(self):
        self.threshold = settings.VIRAL_AUTHENTICITY_THRESHOLD

    def check(self, video: Video, history: List[VideoMetrics] = None) -> float:
        """
        检查数据真实性

        Returns:
            真实性分数 0-1
        """
        score = 1.0
        metrics = video.metrics

        # 1. 检查点赞/播放比是否异常
        like_play_ratio = metrics.like_ratio
        if like_play_ratio > 0.2:  # 点赞超过20%？太假了
            logger.warning(f"Video {video.video_id}: Suspicious like ratio {like_play_ratio:.2%}")
            score *= 0.5
        elif like_play_ratio < 0.001:  # 异常低
            score *= 0.8

        # 2. 检查评论/点赞比
        comment_like_ratio = metrics.comment_count / max(metrics.like_count, 1)
        if comment_like_ratio > 0.5:  # 评论是点赞的一半？也可能是真爆款
            # 需要更严格的检查
            if comment_like_ratio > 0.8:
                score *= 0.7

        # 3. 检查时间分布（如果有历史数据）
        if history and len(history) >= 2:
            # 正常爆款应该是逐渐增长
            latest = history[-1].play_count
            previous = history[-2].play_count

            if previous > 0:
                sudden_jump = latest > previous * 5

                # 如果没有外部导流理由，可能是刷量
                if sudden_jump and not video.viral_factors.get('external_drive'):
                    logger.warning(f"Video {video.video_id}: Sudden jump detected, possible fake")
                    score *= 0.7

        # 4. 平台特异性检查
        if video.platform == 'bilibili':
            # B站：硬币率异常检查
            if metrics.coin_ratio > 0.2:  # 投币率超过20%太假
                score *= 0.6

        elif video.platform == 'xiaohongshu':
            # 小红书：收藏/点赞比检查
            if metrics.collect_ratio > 1.0:  # 收藏超过点赞太假
                score *= 0.5

        return max(0.1, min(1.0, score))


class SentimentAnalyzer:
    """评论区情感分析"""

    def __init__(self):
        # 简化的情感分析（实际项目中可使用更复杂的模型）
        self.positive_keywords = [
            '太棒了', '喜欢', '优秀', '赞', '厉害', '支持', '爱了',
            '实用', '有用', '干货', '学到了', '感谢', '感动'
        ]
        self.negative_keywords = [
            '失望', '垃圾', '差', '坑', '骗', '无语', '后悔',
            '不好', '一般', '没用', '浪费', '吐槽'
        ]

    async def analyze(self, comments: List[str]) -> Dict[str, Any]:
        """
        分析评论情感

        Returns:
            Dict with sentiment analysis results
        """
        if not comments:
            return {
                "positive_count": 0,
                "neutral_count": 0,
                "negative_count": 0,
                "sentiment_ratio": {"positive": 0.0, "neutral": 1.0, "negative": 0.0},
                "sentiment_shift": 0.0,
                "top_keywords": []
            }

        positive_count = 0
        negative_count = 0

        for comment in comments:
            comment_lower = comment.lower()
            if any(kw in comment_lower for kw in self.positive_keywords):
                positive_count += 1
            elif any(kw in comment_lower for kw in self.negative_keywords):
                negative_count += 1

        total = len(comments)
        neutral_count = total - positive_count - negative_count

        positive_ratio = positive_count / total
        negative_ratio = negative_count / total
        neutral_ratio = neutral_count / total

        # 计算情感偏移（正面 - 负面）
        sentiment_shift = positive_ratio - negative_ratio

        return {
            "positive_count": positive_count,
            "neutral_count": neutral_count,
            "negative_count": negative_count,
            "sentiment_ratio": {
                "positive": positive_ratio,
                "neutral": neutral_ratio,
                "negative": negative_ratio
            },
            "sentiment_shift": sentiment_shift,
            "overall_sentiment": "positive" if sentiment_shift > 0.2 else "negative" if sentiment_shift < -0.2 else "neutral"
        }


class CrossPlatformTracker:
    """跨平台扩散追踪"""

    def __init__(self):
        self.platform_keywords = {
            'douyin': ['抖音', 'douyin', 'TikTok'],
            'bilibili': ['B站', 'bilibili', 'b站'],
            'xiaohongshu': ['小红书', 'xhs', 'RED']
        }

    async def track(self, video: Video) -> Dict[str, Any]:
        """
        追踪跨平台扩散

        Returns:
            Dict with cross-platform spread info
        """
        # 简化的跨平台追踪
        # 实际需要查询其他平台是否有相同内容

        spread_info = {
            "has_cross_platform": False,
            "source_platform": video.platform,
            "spreading_to": [],
            "confidence": 0.0
        }

        # 检查视频标题/内容是否包含其他平台关键词
        # 这是一个简化的实现
        title_lower = video.title.lower()

        for platform, keywords in self.platform_keywords.items():
            if platform != video.platform:
                if any(kw in title_lower for kw in keywords):
                    spread_info["spreading_to"].append(platform)
                    spread_info["has_cross_platform"] = True

        if spread_info["has_cross_platform"]:
            spread_info["confidence"] = 0.5  # 降低置信度，因为只是关键词匹配

        return spread_info


class BenchmarkComparator:
    """历史对比 - 与同类视频对比"""

    def __init__(self):
        pass

    async def compare(
        self,
        video: Video,
        benchmark_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        与基准对比

        Args:
            video: 待对比视频
            benchmark_data: 基准数据（同类视频平均数据）

        Returns:
            Dict with comparison results
        """
        metrics = video.metrics

        if not benchmark_data:
            # 使用简单的阈值作为基准
            benchmark_data = {
                "avg_engagement_rate": 0.05,
                "avg_play_count": 10000,
                "avg_like_ratio": 0.05
            }

        vs_engagement = metrics.engagement_rate / max(benchmark_data.get("avg_engagement_rate", 0.05), 0.001)
        vs_likes = metrics.like_ratio / max(benchmark_data.get("avg_like_ratio", 0.05), 0.001)

        return {
            "vs_engagement_benchmark": vs_engagement,
            "vs_like_benchmark": vs_likes,
            "is_above_average": vs_engagement > 1.0 or vs_likes > 1.0,
            "outstanding_factors": self._get_outstanding_factors(video, benchmark_data)
        }

    def _get_outstanding_factors(
        self,
        video: Video,
        benchmark: Dict[str, Any]
    ) -> List[str]:
        """获取突出因素"""
        factors = []
        metrics = video.metrics

        if metrics.engagement_rate > benchmark.get("avg_engagement_rate", 0.05) * 2:
            factors.append("高互动率")

        if metrics.like_ratio > benchmark.get("avg_like_ratio", 0.05) * 2:
            factors.append("高点赞率")

        if video.viral_factors.get('high_sharing'):
            factors.append("高分享率")

        if video.platform == 'bilibili' and metrics.coin_ratio > 0.05:
            factors.append("高投币率")

        if video.platform == 'xiaohongshu' and metrics.collect_ratio > 0.5:
            factors.append("高收藏率")

        return factors


class ViralDetector:
    """爆款识别器 - 多维度判断视频是否处于爆发期"""

    def __init__(self):
        self.growth_analyzer = GrowthCurveAnalyzer()
        self.authenticity_checker = AuthenticityChecker()
        self.sentiment_analyzer = SentimentAnalyzer()
        self.cross_platform_tracker = CrossPlatformTracker()
        self.benchmark_comparator = BenchmarkComparator()

        # 阈值配置
        self.growth_threshold = settings.VIRAL_GROWTH_THRESHOLD
        self.engagement_threshold = settings.VIRAL_ENGAGEMENT_THRESHOLD

    async def detect(
        self,
        video: Video,
        history: List[VideoMetrics] = None,
        comments: List[str] = None
    ) -> ViralSignal:
        """
        检测爆款信号

        Args:
            video: 待检测视频
            history: 历史指标数据
            comments: 视频评论列表

        Returns:
            ViralSignal对象
        """
        logger.info(f"Detecting viral signals for video: {video.video_id}")

        signals = ViralSignal(video_id=video.video_id)

        # 1. 增长曲线分析
        if history and len(history) >= 3:
            growth_result = await self.growth_analyzer.analyze(video.video_id, history)
            signals.growth_score = growth_result.get("score", 0.0)
            signals.growth_stage = growth_result.get("stage", "unknown")
            signals.message = growth_result.get("message", "")
        else:
            # 没有历史数据时，使用当前指标估算
            signals.growth_score = video.metrics.engagement_rate
            if video.metrics.engagement_rate > self.engagement_threshold * 2:
                signals.growth_stage = "takeoff"
                signals.message = "高互动率，可能处于爆发期"
            else:
                signals.growth_stage = "unknown"
                signals.message = "数据不足，无法准确判断"

        # 2. 互动异常检测（数据真实性）
        authenticity_score = self.authenticity_checker.check(video, history)
        signals.authenticity = authenticity_score

        # 3. 评论区情绪分析
        if comments:
            sentiment_result = await self.sentiment_analyzer.analyze(comments)
            signals.sentiment_shift = sentiment_result.get("sentiment_shift", 0.0)

        # 4. 跨平台扩散追踪
        cross_platform = await self.cross_platform_tracker.track(video)
        signals.cross_platform_spread = cross_platform

        # 5. 历史对比
        benchmark = await self.benchmark_comparator.compare(video)
        signals.vs_benchmark = benchmark

        # 综合判断是否预警
        should_alert, alert_level = self._decide_alert(signals)
        signals.should_alert = should_alert
        signals.alert_level = alert_level

        logger.info(
            f"Viral detection result for {video.video_id}: "
            f"stage={signals.growth_stage}, alert={signals.should_alert}, level={signals.alert_level}"
        )

        return signals

    def _decide_alert(self, signals: ViralSignal) -> tuple[bool, str]:
        """
        决定是否推送预警

        Returns:
            (should_alert, alert_level)
        """
        # 预警条件检查
        is_takeoff = signals.growth_stage in ['takeoff', 'embryo']
        is_authentic = signals.authenticity > self.authenticity_checker.threshold
        is_sentiment_positive = signals.sentiment_shift > -0.2

        # 红色预警：多个爆款特征同时出现
        if (is_takeoff and is_authentic and
            signals.growth_score > 0.5 and
            (signals.vs_benchmark.get('is_above_average', False) or
             signals.cross_platform_spread.get('has_cross_platform', False))):
            return True, "red"

        # 橙色预警：增长期 + 真实数据
        if is_takeoff and is_authentic and is_sentiment_positive:
            return True, "orange"

        # 黄色预警：较高互动 + 真实数据
        if (signals.growth_score > self.engagement_threshold and
            is_authentic and
            signals.vs_benchmark.get('is_above_average', False)):
            return True, "yellow"

        # 无预警
        return False, "none"


# Singleton instance
viral_detector = ViralDetector()


def get_viral_detector() -> ViralDetector:
    """Get viral detector instance"""
    return viral_detector
