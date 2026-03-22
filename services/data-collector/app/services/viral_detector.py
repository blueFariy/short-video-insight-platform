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

from app.models import Video, VideoMetrics, VideoMetricHistory, ViralSignal, Creator


# ============== 各平台爆款阈值配置 ==============
thresholds = {
    "bilibili": {
        # 绝对爆款播放量阈值
        "absolutely_viral_play_count": 500000,  # 50万播放以上为绝对爆款
        
        # UP主维度阈值
        "small_up_followers": 10000,       # 小UP主粉丝数上限
        "medium_up_followers": 100000,      # 中UP主粉丝数上限
        
        # 互动率阈值（小UP标准更宽松）
        "small_up_like_ratio": 0.05,       # 小UP主点赞率 > 5%
        "medium_up_like_ratio": 0.03,      # 中UP主点赞率 > 3%
        "big_up_like_ratio": 0.02,         # 大UP主点赞率 > 2%
        
        # 投币率阈值
        "coin_ratio_threshold": 0.005,     # 投币率 > 0.5%
        
        # 时长阈值（秒）
        "short_video_max": 180,            # 3分钟以内为短视频
        "medium_video_max": 600,           # 10分钟以内为中视频
        
        # 发布时间（小时）- 24小时内为新视频
        "new_video_hours": 24,
    },
    "douyin": {
        "absolutely_viral_play_count": 1000000,  # 100万播放
        "small_up_followers": 100000,
        "medium_up_followers": 1000000,
        "small_up_like_ratio": 0.08,
        "medium_up_like_ratio": 0.05,
        "big_up_like_ratio": 0.03,
        "new_video_hours": 12,
    },
    "xiaohongshu": {
        "absolutely_viral_play_count": 100000,   # 10万播放
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
        current_video_metrics: VideoMetrics
    ) -> Dict[str, Any]:
        """
        分析UP主维度
        
        Returns:
            Dict with up_level, is_outstanding, factors
        """
        platform = creator.platform
        conf = thresholds.get(platform, thresholds["bilibili"])
        
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
            factors.append(f"播放量是UP主平均的{current_video_metrics.play_count/avg_play:.1f}倍")
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
        creator: Creator = None
    ) -> Dict[str, Any]:
        """
        分析视频内容维度
        
        Returns:
            Dict with content_score, factors, is_viral
        """
        platform = video.platform
        conf = thresholds.get(platform, thresholds["bilibili"])
        metrics = video.metrics
        
        factors = []
        score = 0.0
        is_viral = False
        
        # 维度1：绝对爆款（播放量超过阈值）
        if metrics.play_count >= conf.get("absolutely_viral_play_count", 500000):
            factors.append(f"绝对爆款：{metrics.play_count//10000}万播放")
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
                factors.append(f"短视频{duration//60}分钟")
            elif duration < conf.get("medium_video_max", 600):
                factors.append(f"中视频{duration//60}分钟")
            else:
                factors.append(f"长视频{duration//60}分钟")
        
        # 维度6：互动综合分
        total_engagement = (
            metrics.like_count + 
            metrics.comment_count * 2 +  # 评论权重更高
            metrics.share_count * 3 +   # 分享权重最高
            metrics.favorite_count * 2
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


class AuthenticityChecker:
    """数据真实性检查"""
    
    def __init__(self):
        pass
    
    def check(self, video: Video) -> float:
        """
        检查数据真实性
        
        Returns:
            真实性分数 0-1
        """
        score = 1.0
        metrics = video.metrics
        
        # 基础比例检查
        # 点赞/播放比（不同平台不同标准）
        if video.platform == "bilibili":
            # B站高质量视频10%+点赞率是正常的
            if metrics.like_ratio > 0.5:
                score *= 0.3
            elif metrics.like_ratio > 0.35:
                score *= 0.7
        else:
            if metrics.like_ratio > 0.3:
                score *= 0.3
            elif metrics.like_ratio > 0.2:
                score *= 0.7
        
        # 投币/点赞比（B站特有）
        if video.platform == "bilibili" and metrics.like_count > 0:
            coin_like_ratio = metrics.coin_count / metrics.like_count
            # 真实粉丝会有一定投币比例，0.05-0.3为正常范围
            if 0.05 <= coin_like_ratio <= 0.5:
                score = min(1.0, score * 1.2)  # 提升真实性
        
        # 评论/播放比
        if metrics.play_count > 0:
            comment_ratio = metrics.comment_count / metrics.play_count
            # 1%-10%为正常评论率
            if comment_ratio < 0.001:  # 几乎无评论
                score *= 0.8
            elif comment_ratio > 0.2:  # 评论异常高
                score *= 0.7
        
        return max(0.1, min(1.0, score))


class ViralDetector:
    """爆款识别器 - 多维度判断"""
    
    def __init__(self):
        self.creator_analyzer = CreatorAnalyzer()
        self.content_analyzer = VideoContentAnalyzer()
        self.authenticity_checker = AuthenticityChecker()
    
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
        
        # 1. UP主维度分析
        creator_analysis = None
        if creator:
            creator_analysis = self.creator_analyzer.analyze(creator, video.metrics)
            logger.info(f"Creator analysis: {creator_analysis}")
        
        # 2. 视频内容维度分析
        content_analysis = self.content_analyzer.analyze(video, creator)
        signals.growth_score = content_analysis.get("score", 0.0)
        
        # 3. 数据真实性检查
        authenticity = self.authenticity_checker.check(video)
        signals.authenticity = authenticity
        
        # 4. 判断爆款阶段
        is_absolutely_viral = content_analysis.get("is_absolutely_viral", False)
        is_content_viral = content_analysis.get("is_viral", False)
        
        if is_absolutely_viral:
            signals.growth_stage = "explosion"
            signals.message = f"绝对爆款！播放量{video.metrics.play_count//10000}万"
        elif is_content_viral:
            signals.growth_stage = "takeoff"
            signals.message = "多维度爆款特征"
        elif creator_analysis and creator_analysis.get("is_outstanding"):
            signals.growth_stage = "takeoff"
            signals.message = f"UP主维度爆款: {', '.join(creator_analysis.get('factors', []))}"
        else:
            signals.growth_stage = "normal"
            signals.message = "未达到爆款标准"
        
        # 添加分析因素
        all_factors = content_analysis.get("factors", [])
        if creator_analysis:
            all_factors.extend(creator_analysis.get("factors", []))
        
        signals.vs_benchmark = {
            "factors": all_factors,
            "content_score": content_analysis.get("score", 0),
            "creator_analysis": creator_analysis
        }
        
        # 5. 决定预警级别
        should_alert, alert_level = self._decide_alert(
            signals, 
            is_absolutely_viral,
            is_content_viral,
            authenticity
        )
        signals.should_alert = should_alert
        signals.alert_level = alert_level
        
        logger.info(
            f"Viral result: {video.video_id}, "
            f"stage={signals.growth_stage}, alert={should_alert}, level={alert_level}"
        )
        
        return signals
    
    def _decide_alert(
        self, 
        signals: ViralSignal,
        is_absolutely_viral: bool,
        is_content_viral: bool,
        authenticity: float
    ) -> tuple[bool, str]:
        """
        决定预警级别
        """
        # 数据不真实，不预警
        if authenticity < 0.3:
            return False, "none"
        
        # 绝对爆款 - 红色预警
        if is_absolutely_viral and authenticity > 0.5:
            return True, "red"
        
        # 多维度爆款 - 橙色预警
        if is_content_viral and authenticity > 0.5:
            return True, "orange"
        
        # 较高分数 - 黄色预警
        if signals.growth_score > 30 and authenticity > 0.5:
            return True, "yellow"
        
        return False, "none"


# Singleton instance
viral_detector = ViralDetector()


def get_viral_detector() -> ViralDetector:
    """Get viral detector instance"""
    return viral_detector
