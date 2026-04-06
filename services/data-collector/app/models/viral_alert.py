"""
Viral Alert Models - 用户预警相关数据模型
"""
from sqlalchemy import Column, String, Integer, DateTime, Float, Boolean, BigInteger, ARRAY, Text, JSON, Index
from datetime import datetime
from app.models import Base


class VideoMetricSnapshot(Base):
    """视频指标时序快照 - 存储分钟级指标变化"""
    __tablename__ = "video_metric_snapshots"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    video_id = Column(String(100), nullable=False, index=True)
    platform = Column(String(20), nullable=False)

    # 指标快照
    play_count = Column(BigInteger, default=0)
    like_count = Column(BigInteger, default=0)
    comment_count = Column(BigInteger, default=0)
    share_count = Column(BigInteger, default=0)
    danmaku_count = Column(BigInteger, default=0)
    coin_count = Column(BigInteger, default=0)
    collect_count = Column(BigInteger, default=0)

    # 计算指标
    engagement_rate = Column(Float, default=0.0)
    like_ratio = Column(Float, default=0.0)
    comment_ratio = Column(Float, default=0.0)
    share_ratio = Column(Float, default=0.0)

    # 时间戳
    snapshot_time = Column(DateTime, default=datetime.now, index=True)
    created_at = Column(DateTime, default=datetime.now)

    # 复合索引
    __table_args__ = (
        Index('idx_snapshot_video_time', 'video_id', 'snapshot_time'),
    )


class UserInterest(Base):
    """用户兴趣配置"""
    __tablename__ = "user_interests"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, nullable=False, unique=True, index=True)

    # 关注的领域权重 JSON: {"美食": 0.8, "美妆": 0.6, "搞笑": 0.5}
    category_weights = Column(JSON, default={})

    # 关注的关键词
    interest_keywords = Column(ARRAY(String(200)), default=[])

    # 关注的平台
    platforms = Column(ARRAY(String(20)), default=['douyin', 'bilibili', 'xiaohongshu'])

    # 预警级别偏好: 'yellow', 'orange', 'red' 或 ['yellow', 'orange', 'red']
    alert_levels = Column(ARRAY(String(20)), default=['yellow', 'orange', 'red'])

    # 通知渠道
    notification_channels = Column(ARRAY(String(20)), default=['app'])

    # 状态
    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now)


class ViralAlert(Base):
    """爆款预警记录"""
    __tablename__ = "viral_alerts"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, nullable=False, index=True)

    # 视频信息
    video_id = Column(String(100), nullable=False, index=True)
    platform = Column(String(20))
    category = Column(String(50))  # 视频分类
    title = Column(String(500))
    cover_url = Column(Text)
    video_url = Column(Text)

    # 预警信息
    alert_level = Column(String(20), nullable=False)  # 'yellow', 'orange', 'red'

    # 爆款检测结果
    message = Column(Text)
    factors = Column(JSON)  # 爆款因素列表

    # 状态
    is_read = Column(Boolean, default=False)
    is_dismissed = Column(Boolean, default=False)

    created_at = Column(DateTime, default=datetime.now)

    # 复合索引
    __table_args__ = (
        Index('idx_alert_user_read', 'user_id', 'is_read'),
        Index('idx_alert_user_time', 'user_id', 'created_at'),
    )


class CategoryBenchmark(Base):
    """各分类的基准数据 - 用于对比分析"""
    __tablename__ = "category_benchmarks"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    platform = Column(String(20), nullable=False)
    category = Column(String(50), nullable=False)

    # 平台、分类系数
    platform_factor = Column(Float, default=0, comment="平台系数")
    category_factor = Column(Float, default=0, comment="分类系数")

    # ====== 创作者维度 (单位数据) ======
    creator_follower_factor = Column(Float, default=0, comment="创作者粉丝系数")
    creator_avg_play_count_factor = Column(Float, default=0, comment="创作者平均播放量系数")
    creator_update_interval_hours = Column(Integer, nullable=True, comment="创作者更新间隔时间(小时)")

    # ====== 视频数据维度 (百分比单位: 1 = 1%) ======
    video_like_ratio = Column(Float, default=0.0, comment="视频点赞率(%)系数")
    video_collect_ratio = Column(Float, default=0.0, comment="视频收藏率(%)系数")
    video_comment_ratio = Column(Float, default=0.0, comment="视频评论率(%)系数")
    video_publish_hours = Column(Integer, nullable=True, comment="视频发布后X小时内")
    video_duration_seconds_min = Column(Integer, nullable=True, comment="视频时长最小值(秒)")
    video_duration_seconds_max = Column(Integer, nullable=True, comment="视频时长最大值(秒)")
    decay_period = Column(Float, default=60.0, comment="生命周期")

    # ====== 爆款阈值 (根据单位数据计算得出) ======
    viral_threshold = Column(ARRAY(Float), default=[3.0, 8.0, 20.0], comment="爆款阈值(综合分数)")

    # ====== 预警类型 ======
    alert_level = Column(ARRAY(String), default=["yellow", "orange", "red"], comment="预警类型")

    # ====== 时间 ======
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # 唯一约束
    __table_args__ = (
        Index('idx_benchmark_platform_cat', 'platform', 'category', unique=True),
    )
