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

        # 最终播放倍数
        self.predicted_multiplier = 1.0

        # 互动权重
        self.alpha = 0.30  # 点赞权重
        self.beta = 0.50  # 收藏权重
        self.gamma = 0.20  # 评论权重

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

        # Logistic 预测模型配置
        self.logistic_config = {
            # 饱和度倍数（根据已发布比例）
            "saturation_factors": {
                "early": 20,  # <10%生命周期
                "early_mid": 7,  # 10-25%
                "mid": 3,  # 25-50%
                "late_mid": 1.5,  # 50-75%
                "late": 1.1,  # >75%
            },
        }

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

        # 偏离惩罚系数，最大惩罚不超过0.2
        penalty = min(deviation * 0.1, 0.2)
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

    def calculate_saturation_factor(self, life_ratio: float, category_factor: float,
                                    current_multiplier: float) -> float:
        """
        计算饱和倍数因子

        根据已发布比例估算最终倍数
        """
        config = self.logistic_config["saturation_factors"]

        if life_ratio < 0.1:
            saturation_factor = config["early"]
        elif life_ratio < 0.25:
            saturation_factor = config["early_mid"]
        elif life_ratio < 0.5:
            saturation_factor = config["mid"]
        elif life_ratio < 0.75:
            saturation_factor = config["late_mid"]
        else:
            saturation_factor = config["late"]

        # 分类系数调整：传播能力强的分类，饱和倍数更高
        saturation_factor = saturation_factor * (0.8 + category_factor * 0.5)

        # 当前播放倍数越高，饱和倍数可以适当降低（已经爆发）
        if current_multiplier > 10:
            saturation_factor = min(saturation_factor, 2.0)
        elif current_multiplier > 5:
            saturation_factor = min(saturation_factor, 3.0)

        return saturation_factor

    def calculate_predicted_multiplier(self,
                                       video: Video,
                                       creator: Creator,
                                       current_time: datetime,
                                       interaction_score: float) -> float:
        """
        基于 Logistic 增长模型预测最终播放倍数
        考虑：分母（作者平均播放量）也会随时间增长
        """
        # 1. 基础数据
        current_play = video.play_count
        current_avg = creator.avg_play_count if creator.avg_play_count > 0 else 1
        current_multiplier = current_play / current_avg

        hours_published = (current_time - video.publish_time).total_seconds() / 3600

        # 2. 获取分类参数
        half_life_days = self.decay_period.get(video.category, 60)
        half_life_hours = half_life_days * 24
        category_factor = self.category_factor.get(video.category, 1.0)

        # 3. 如果已超过生命周期，直接返回当前倍数
        if hours_published >= half_life_hours * 1.5:
            return current_multiplier

        # 4. 计算生命周期比例
        life_ratio = min(hours_published / half_life_hours, 1.0)

        # 5. 计算增长率 r
        r = (self.platform_factor.get(video.platform, 1.0) *
             self.category_factor.get(video.category, 1.0) *
             (interaction_score / 20))
        r = min(max(r, 0.1), 1.5)

        # 6. 计算饱和倍数因子
        saturation_factor = self.calculate_saturation_factor(life_ratio, category_factor, current_multiplier)

        # 7. 预测当前视频的最终播放量（分子）
        predicted_play_final = current_play * saturation_factor

        # ========== 关键修正：预测分母（作者平均播放量）的增长 ==========

        # 8. 估算当前视频对作者平均播放量的提升系数
        # 当前倍数越高，对平均播放量的提升越大
        if current_multiplier > 20:
            avg_boost_base = 1.5  # 爆发式增长，平均播放量提升50%
        elif current_multiplier > 10:
            avg_boost_base = 1.3  # 显著增长，提升30%
        elif current_multiplier > 5:
            avg_boost_base = 1.15  # 一定增长，提升15%
        elif current_multiplier > 2:
            avg_boost_base = 1.05  # 小幅增长，提升5%
        else:
            avg_boost_base = 1.0  # 无明显影响

        # 互动率加成
        if interaction_score > 15:
            avg_boost_base *= 1.1
        elif interaction_score > 8:
            avg_boost_base *= 1.05

        # 9. 计算半衰期结束时的作者平均播放量（分母）
        # 假设：平均播放量从当前值线性增长到提升后的值
        # 增长曲线也遵循 Logistic 模型
        future_avg = current_avg * avg_boost_base

        # 10. 重新计算预测倍数（基于未来的平均播放量）
        predicted_multiplier = predicted_play_final / future_avg

        # 11. 使用 Logistic 曲线微调
        if hours_published > 0 and r > 0 and hours_published <= half_life_hours:
            try:
                K = predicted_play_final
                ratio = K / max(current_play, 1)
                if ratio > 1:
                    ln_term = math.log(ratio - 1)
                    t0 = hours_published + ln_term / r
                    final_time = half_life_hours  # 预测至半衰期
                    if final_time > 0:
                        exponent = -r * (final_time - t0)
                        if exponent < 100:
                            predicted_play = K / (1 + math.exp(exponent))
                            predicted_multiplier = predicted_play / future_avg
            except (ValueError, OverflowError, ZeroDivisionError):
                pass

        return predicted_multiplier

    def calculate_play_bonus(self) -> float:
        """
        计算播放倍数加成（对数压缩）
        """
        if self.predicted_multiplier <= 0:
            return 1.0

        return math.pow(self.predicted_multiplier, 0.7)

    def calculate_viral_index(self, video: Video, creator: Creator, current_time: datetime) -> float:
        """计算爆款指数 H（使用 Logistic 预测模型）"""

        # 互动得分
        interaction_score = self.calculate_interaction_score(video)

        # 预测最终播放倍数（基于 Logistic 模型）
        self.predicted_multiplier = self.calculate_predicted_multiplier(
            video, creator, current_time, interaction_score
        )

        # 播放倍数加成（对数压缩）
        play_bonus = self.calculate_play_bonus()

        # 内容质量分 = 互动得分 × 播放加成
        content_quality = interaction_score * play_bonus

        # 平台与分类系数
        platform_f = self.platform_factor.get(video.platform, 1.0)
        category_f = self.category_factor.get(video.category, 1.0)

        # 粉丝数调整系数
        follower_factor = self.calculate_follower_factor(creator.follower_count)

        # 时间衰减
        time_decay = self.calculate_time_decay(
            video.publish_time, current_time,
            self.decay_period.get(video.category, 60)
        )

        # 时长修正
        duration_factor = self.calculate_duration_factor(video.category, video.duration)

        # 更新间隔修正
        update_interval_factor = self.calculate_update_interval_factor(
            video.category, creator.update_interval
        )

        # 综合计算
        H = (content_quality *
             (platform_f / category_f) *
             follower_factor *
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
        play_count_str = f' ({self.predicted_multiplier * creator.avg_play_count / 10000:.1f}万) 是平均值的{self.predicted_multiplier:.1f}倍'
        if self.predicted_multiplier >= 20:
            factors.append(
                f"🚀 （预计）播放量爆发{play_count_str}")
        elif self.predicted_multiplier >= 10:
            factors.append(
                f"📈 （预计）播放量优秀{play_count_str}")
        elif self.predicted_multiplier >= 5:
            factors.append(
                f"👍 （预计）播放量良好{play_count_str}")

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
        elif creator.follower_count < 1000000:
            factors.append(f"🏆 头部达人 (粉丝{creator.follower_count / 10000:.1f}万)，粉丝基数大且内容穿透力强")
        else:
            factors.append(
                f"👑 超级头部/顶流 (粉丝{creator.follower_count / 10000:.1f}万)，现象级影响力，自带流量引爆能力")

        # 4. 时间因素
        hours_ago = (current_time - video.publish_time).total_seconds() / 3600
        days_ago = hours_ago / 24
        if hours_ago <= 5:
            factors.append(f"⚡ 新发布视频 ({hours_ago:.0f}小时前)，正处于流量上升期")
        elif hours_ago <= 24:
            factors.append(f"🕐 发布{hours_ago:.0f}小时，黄金传播期")
        elif hours_ago <= 72:
            factors.append(f"📊 发布{hours_ago:.0f}小时，仍处于推荐辐射期")
        elif days_ago <= 7:
            factors.append(f"📈 发布{days_ago:.1f}天，流量趋于平稳，长尾效应开始显现")
        elif days_ago <= 30:
            factors.append(f"🌊 发布{days_ago:.0f}天，进入长尾流量期，搜索权重仍有效")
        else:
            factors.append(f"⏰ 发布{days_ago:.0f}天，经典内容，主要靠搜索和推荐召回")

        # 5. 时长分析
        opt_min, opt_max = self.optimal_duration.get(video.category, (30, 60))
        hours = video.duration // 3600
        minutes = (video.duration % 3600) // 60
        remaining_seconds = video.duration % 60

        if hours > 0:
            duration = f"{hours}:{minutes:02d}:{remaining_seconds:02d}"
        else:
            duration = f"{minutes}:{remaining_seconds:02d}"

        if opt_min <= video.duration <= opt_max:
            factors.append(f"⏱️ 时长精准 ({duration})，符合{video.category}类最佳区间 [{opt_min}, {opt_max}]")
        elif video.duration < opt_min:
            if video.duration <= opt_min * 0.5:
                factors.append(
                    f"⚡ 过短视频 ({duration}，最佳区间 [{opt_min}, {opt_max}])，完播率高但内容深度不足")
            else:
                factors.append(f"📱 偏短视频 ({duration}，最佳区间 [{opt_min}, {opt_max}])，信息密度略低")
        else:
            if video.duration >= opt_max * 1.5:
                factors.append(f"📖 长视频 ({duration}，最佳区间 [{opt_min}, {opt_max}])，需要极强的叙事能力")
            else:
                factors.append(f"🔍 略长视频 ({duration}，最佳区间 [{opt_min}, {opt_max}])，轻微超出最佳区间")

        # 6. 更新频率分析
        optimal_interval = self.optimal_update_interval.get(video.category, 48)
        if creator.update_interval <= optimal_interval * 1.2:
            factors.append(f"📅 创作者更新频率稳定 ({creator.update_interval:.0f}h/更)，粉丝粘性高")
        else:
            factors.append(f"⚠️ 创作者更新间隔较长 ({creator.update_interval:.0f}h/更)，可能影响流量权重")

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
