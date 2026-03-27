import asyncio
import math
from datetime import datetime, timedelta
from typing import Dict, List, Any

from app.schemas import Video, Creator
from app.models import CategoryBenchmark
from app.models import db_manager


class ViralVideoAnalyzer:
    """爆款视频分析器"""

    def __init__(self, benchmarks: List[CategoryBenchmark]):
        # 平台系数（基准：抖音 = 1.0）
        self.platform_factor = {}
        # 分类系数（基准：搞笑 = 1.0）
        self.category_factor = {}
        # 最佳时长（秒）
        self.optimal_duration = {}
        # 最优更新间隔（小时）
        self.optimal_update_interval = {}
        # 分类生命周期
        self.decay_period = {}
        for benchmark in benchmarks:
            self.platform_factor[benchmark.platform] = benchmark.platform_factor
            self.category_factor[benchmark.category] = benchmark.category_factor
            self.optimal_duration[benchmark.category] = (
                benchmark.video_duration_seconds_min, benchmark.video_duration_seconds_max)
            self.optimal_update_interval[benchmark.category] = benchmark.creator_update_interval_hours
            self.decay_period[benchmark.category] = benchmark.decay_period

        # 互动权重
        self.alpha = 0.35  # 点赞权重
        self.beta = 0.25  # 收藏权重
        self.gamma = 0.40  # 评论权重

        # 时间衰减系数（小时^-1），不同平台更新频率
        self.lambda_decay = 0.02

        # 爆款等级阈值
        self.thresholds = {
            "yellow": 3.0,  # 流量型（黄）
            "orange": 8.0,  # 人设型（橙）
            "red": 20.0  # 资产型（红）
        }

        # 基准粉丝数
        self.base_follower = 10000

        # 基准平均播放量
        self.base_avg_play = 100000

    def init_params(self, video: Video, creator: Creator = None):
        match video.platform:
            case "douyin":
                self.lambda_decay = 0.02
            case "bilibili":
                self.lambda_decay = 0.01
            case _:
                pass

    def calculate_follower_factor(self, follower_count: int) -> float:
        """计算粉丝数调整系数"""
        return math.pow(follower_count / self.base_follower, 0.2)

    def calculate_update_interval_factor(self, category: str, actual_interval: float) -> float:
        """计算更新间隔调整系数"""
        optimal_interval = self.optimal_update_interval.get(category, 48)
        ratio = actual_interval / optimal_interval
        return 1 / (1 + (ratio - 1) * 0.2)  # 最大惩罚20%
        # return ratio

    def calculate_duration_factor(self, category: str, duration: int) -> float:
        """计算时长修正系数"""
        if category not in self.optimal_duration:
            return 1.0

        opt_min, opt_max = self.optimal_duration[category]

        # 如果在最佳区间内，系数为1
        if opt_min <= duration <= opt_max:
            return 1.0

        # 偏离惩罚
        if duration < opt_min:
            deviation = (opt_min - duration) / 60  # 以60秒为基准
        else:
            deviation = (duration - opt_max) / 60

        # 偏离惩罚系数，最大惩罚不超过0.5
        penalty = min(deviation * 0.1, 0.5)
        return 1.0 - penalty

    def calculate_time_decay(self, publish_time: datetime, current_time: datetime, decay_period: float) -> float:
        """
        指数衰减模型

        Args:
            publish_time: 发布时间
            current_time: 当前时间
            decay_period: 半衰期

        公式: factor = math.pow(2, -days_passed / half_life_days)
        """
        days_passed = (current_time - publish_time).total_seconds() / 86400
        if days_passed <= 0:
            return 1.0

        factor = math.pow(2, -days_passed / decay_period)
        return factor

    def calculate_interaction_score(self, video: Video) -> float:
        """计算互动得分"""
        return (self.alpha * video.like_rate +
                self.beta * video.favorite_rate +
                self.gamma * video.comment_rate)

    def calculate_viral_index(self, video: Video, creator: Creator, current_time: datetime) -> float:
        """计算爆款指数 H"""
        # 播放量倍数
        play_multiplier = video.play_count / creator.avg_play_count if creator.avg_play_count > 0 else 0

        # 平台与分类系数
        platform_f = self.platform_factor.get(video.platform, 1.0)
        category_f = self.category_factor.get(video.category, 1.0)

        # 粉丝数调整系数
        follower_factor = self.calculate_follower_factor(creator.follower_count)

        # 互动得分
        interaction_score = self.calculate_interaction_score(video)

        # 时间衰减
        time_decay = self.calculate_time_decay(video.publish_time, current_time, self.decay_period[video.category])

        # 时长修正
        duration_factor = self.calculate_duration_factor(video.category, video.duration)

        # 更新间隔修正
        update_interval_factor = self.calculate_update_interval_factor(
            video.category, creator.update_interval
        )

        # 综合计算
        H = (play_multiplier *
             (platform_f / category_f) *
             follower_factor *
             interaction_score *
             time_decay *
             duration_factor *
             (1 / update_interval_factor))

        return H

    def get_alert_level(self, viral_index: float) -> str:
        """根据爆款指数返回警报等级"""
        if viral_index >= self.thresholds["red"]:
            return "red"
        elif viral_index >= self.thresholds["orange"]:
            return "orange"
        elif viral_index >= self.thresholds["yellow"]:
            return "yellow"
        else:
            return ""

    def collect_factors(self, video: Video, creator: Creator, viral_index: float,
                        current_time: datetime) -> List[str]:
        """收集分析因素"""
        factors = []

        # 1. 播放量分析
        play_ratio = video.play_count / creator.avg_play_count if creator.avg_play_count > 0 else 0
        if play_ratio >= 20:
            factors.append(f"🚀 播放量爆发 ({video.play_count / 10000:.0f}万) 是平均值的{play_ratio:.1f}倍")
        elif play_ratio >= 10:
            factors.append(f"📈 播放量优秀 ({video.play_count / 10000:.0f}万) 是平均值的{play_ratio:.1f}倍")
        elif play_ratio >= 5:
            factors.append(f"👍 播放量良好 ({video.play_count / 10000:.0f}万) 是平均值的{play_ratio:.1f}倍")

        # 2. 互动率分析
        if video.like_rate >= 10:
            factors.append(f"❤️ 超高点赞率 ({video.like_rate:.1f}%)，远超优秀标准(5%)")
        elif video.like_rate >= 5:
            factors.append(f"👍 高点赞率 ({video.like_rate:.1f}%)，高于平均水平")
        elif video.like_rate >= 3:
            factors.append(f"📊 点赞率良好 ({video.like_rate:.1f}%)")

        if video.favorite_rate >= 5:
            factors.append(f"🔖 超高收藏率 ({video.favorite_rate:.1f}%)，内容价值极高")
        elif video.favorite_rate >= 2:
            factors.append(f"📌 高收藏率 ({video.favorite_rate:.1f}%)，实用性强")

        if video.comment_rate >= 2:
            factors.append(f"💬 超高评论率 ({video.comment_rate:.1f}%)，引发热烈讨论")
        elif video.comment_rate >= 0.8:
            factors.append(f"🗣️ 高评论率 ({video.comment_rate:.1f}%)，互动活跃")

        # 3. 粉丝基数分析
        if creator.follower_count < 10000:
            factors.append(f"🌟 小号逆袭 (粉丝{creator.follower_count / 10000:.1f}万)，播放量远超粉丝基数")
        elif creator.follower_count < 100000:
            factors.append(f"📊 腰部账号 (粉丝{creator.follower_count / 10000:.1f}万)，表现优异")

        # 4. 时间因素
        hours_ago = (current_time - video.publish_time).total_seconds() / 3600
        if hours_ago <= 5:
            factors.append(f"⚡ 新发布视频 ({hours_ago:.0f}小时前)，正处于流量上升期")
        elif hours_ago <= 24:
            factors.append(f"🕐 发布{hours_ago:.0f}小时，黄金传播期")

        # 5. 时长分析
        opt_min, opt_max = self.optimal_duration.get(video.category, (30, 60))
        if opt_min <= video.duration <= opt_max:
            factors.append(f"⏱️ 时长精准 ({video.duration}秒)，符合{video.category}类最佳区间")
        elif video.duration < opt_min:
            factors.append(f"⚡ 短小精悍 ({video.duration}秒)，完播率高")
        else:
            factors.append(f"📺 深度内容 ({video.duration}秒)，需要强钩子维持完播率")

        # 6. 更新频率分析
        optimal_interval = self.optimal_update_interval.get(video.category, 48)
        if creator.update_interval <= optimal_interval * 1.2:
            factors.append(f"📅 更新频率稳定 ({creator.update_interval:.0f}h/更)，粉丝粘性高")
        else:
            factors.append(f"⚠️ 更新间隔较长 ({creator.update_interval:.0f}h/更)，可能影响流量权重")

        # 7. 平台与分类适配
        platform_factor = self.platform_factor.get(video.platform, 1.0)
        category_factor = self.category_factor.get(video.category, 1.0)
        if platform_factor >= 1.0:
            factors.append(f"🎯 主战场优势 ({video.platform})，流量池大")
        if category_factor >= 1.0:
            factors.append(f"🎭 赛道优势 ({video.category})，易于传播")

        # 8. 爆款指数定位
        if viral_index >= self.thresholds["red"]:
            factors.append(f"🏆 综合爆款指数 {viral_index:.1f}，达到资产型爆款标准，具备跨圈层传播潜力")
        elif viral_index >= self.thresholds["orange"]:
            factors.append(f"⭐ 综合爆款指数 {viral_index:.1f}，达到人设型爆款标准，粉丝转化率高")
        elif viral_index >= self.thresholds["yellow"]:
            factors.append(f"✨ 综合爆款指数 {viral_index:.1f}，达到流量型爆款标准，单点爆发力强")

        return factors

    def analyze(self, video: Video, creator: Creator, current_time: datetime = None) -> Dict[str, Any]:
        """
        分析视频的爆款等级

        Args:
            video: 视频对象
            creator: 创作者对象
            current_time: 当前时间，默认为现在

        Returns:
            包含 alert_level 和 factors 的字典
        """
        if current_time is None:
            current_time = datetime.now()

        # 初始化参数
        self.init_params(video, creator)

        # 计算爆款指数
        score = self.calculate_viral_index(video, creator, current_time)

        # 获取警报等级
        alert_level = self.get_alert_level(score)

        # 收集分析因素
        factors = self.collect_factors(video, creator, score, current_time)

        return {
            "alert_level": alert_level,
            "factors": factors,
            "score": score,
        }


async def get_benchmarks(platform):
    db_manager.init_db()

    async with db_manager.get_session() as session:
        from sqlalchemy import select
        stmt = select(CategoryBenchmark).where(CategoryBenchmark.platform == platform)
        result = await session.execute(stmt)
        return result.scalars().all()
