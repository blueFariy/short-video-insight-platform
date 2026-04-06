"""
Database Models
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import (
    BigInteger,
    Boolean,
    Date,
    DateTime,
    Float,
    Index,
    Integer,
    JSON,
    Numeric,
    String,
    Text,
    ARRAY,
    ForeignKey,
    UniqueConstraint
)
from sqlalchemy import String as SQLString
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import JSONB, TIMESTAMP

from app.core.database import Base


class User(Base):
    """用户模型"""
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(20), default="user")
    avatar_url: Mapped[Optional[str]] = mapped_column(Text)
    company: Mapped[Optional[str]] = mapped_column(String(100))
    job_title: Mapped[Optional[str]] = mapped_column(String(50))
    preferences: Mapped[Optional[dict]] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default="NOW()")
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default="NOW()")
    last_login: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    subscription_tier: Mapped[str] = mapped_column(String(20), default="free")
    subscription_expires: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True))

    # 关系
    collections: Mapped[list["Collection"]] = relationship("Collection", back_populates="user", cascade="all, delete-orphan")
    competitor_watches: Mapped[list["CompetitorWatch"]] = relationship("CompetitorWatch", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(id={self.id}, username={self.username})>"


class Creator(Base):
    """创作者模型"""
    __tablename__ = "creators"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    platform: Mapped[str] = mapped_column(String(20), nullable=False)
    creator_id: Mapped[str] = mapped_column(String(100), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    avatar_url: Mapped[Optional[str]] = mapped_column(Text)
    bio: Mapped[Optional[str]] = mapped_column(Text)
    follower_count: Mapped[int] = mapped_column(BigInteger, default=0, index=True)
    following_count: Mapped[int] = mapped_column(BigInteger, default=0)
    total_likes: Mapped[int] = mapped_column(BigInteger, default=0)
    avg_play_count: Mapped[int] = mapped_column(BigInteger, default=0)
    avg_interaction_rate: Mapped[Optional[float]] = mapped_column(Float)
    main_category: Mapped[Optional[str]] = mapped_column(String(50))
    stats_updated_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True))
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default="NOW()")
    is_monitored: Mapped[bool] = mapped_column(Boolean, default=False)

    __table_args__ = (
        UniqueConstraint("platform", "creator_id", name="uq_creator_platform_id"),
    )

    # 关系
    videos: Mapped[list["Video"]] = relationship("Video", back_populates="creator")
    competitor_watches: Mapped[list["CompetitorWatch"]] = relationship("CompetitorWatch", back_populates="creator")

    def __repr__(self):
        return f"<Creator(id={self.id}, name={self.name}, platform={self.platform})>"


class Video(Base):
    """视频模型"""
    __tablename__ = "videos"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    platform: Mapped[str] = mapped_column(String(20), nullable=False)
    video_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    video_url: Mapped[str] = mapped_column(Text, nullable=False)
    title: Mapped[Optional[str]] = mapped_column(String(500))
    description: Mapped[Optional[str]] = mapped_column(Text)
    cover_image_url: Mapped[Optional[str]] = mapped_column(Text)
    duration: Mapped[Optional[int]] = mapped_column(Integer)
    publish_time: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True), index=True)
    play_count: Mapped[int] = mapped_column(BigInteger, default=0, index=True)
    like_count: Mapped[int] = mapped_column(BigInteger, default=0)
    comment_count: Mapped[int] = mapped_column(BigInteger, default=0)
    share_count: Mapped[int] = mapped_column(BigInteger, default=0)
    collect_count: Mapped[int] = mapped_column(BigInteger, default=0)
    forward_count: Mapped[int] = mapped_column(BigInteger, default=0)
    creator_id: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("creators.id"), index=True)
    category: Mapped[Optional[str]] = mapped_column(String(50), index=True)
    tags: Mapped[Optional[list]] = mapped_column(ARRAY(Text))
    ai_generated_tags: Mapped[Optional[list]] = mapped_column(ARRAY(Text))
    data_quality_score: Mapped[float] = mapped_column(Float, default=1.0)
    is_denoised: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default="NOW()")
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default="NOW()")

    __table_args__ = (
        UniqueConstraint("platform", "video_id", name="uq_video_platform_id"),
    )

    # 关系
    creator: Mapped[Optional["Creator"]] = relationship("Creator", back_populates="videos")
    scripts: Mapped[list["VideoScript"]] = relationship("VideoScript", back_populates="video", cascade="all, delete-orphan")
    insights: Mapped[list["VideoInsight"]] = relationship("VideoInsight", back_populates="video", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Video(id={self.id}, title={self.title})>"


class VideoScript(Base):
    """视频脚本模型"""
    __tablename__ = "video_scripts"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    video_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("videos.id", ondelete="CASCADE"), nullable=False, index=True)
    asr_text: Mapped[Optional[str]] = mapped_column(Text)
    asr_confidence: Mapped[Optional[float]] = mapped_column(Float)
    ocr_text: Mapped[Optional[str]] = mapped_column(Text)
    ocr_frames: Mapped[Optional[dict]] = mapped_column(JSONB)
    keyframes: Mapped[Optional[dict]] = mapped_column(JSONB)
    bgm_info: Mapped[Optional[dict]] = mapped_column(JSONB)
    audio_emotion: Mapped[Optional[str]] = mapped_column(String(20))
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default="NOW()")
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default="NOW()")

    # 关系
    video: Mapped["Video"] = relationship("Video", back_populates="scripts")

    def __repr__(self):
        return f"<VideoScript(id={self.id}, video_id={self.video_id})>"


class VideoInsight(Base):
    """视频洞察模型"""
    __tablename__ = "video_insights"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    video_id: Mapped[String] = mapped_column(String, ForeignKey("videos.video_id", ondelete="CASCADE"),nullable=False, index=True)
    ai_summary: Mapped[Optional[str]] = mapped_column(Text)
    hook_3s: Mapped[Optional[str]] = mapped_column(Text)
    hook_type: Mapped[Optional[str]] = mapped_column(String(30), index=True)
    structure_type: Mapped[Optional[str]] = mapped_column(String(30), index=True)
    structure_analysis: Mapped[Optional[dict]] = mapped_column(JSONB)
    keywords: Mapped[Optional[list]] = mapped_column(ARRAY(Text))
    entity_tags: Mapped[Optional[dict]] = mapped_column(JSONB)
    sentiment_score: Mapped[Optional[float]] = mapped_column(Float)
    comment_high_freq: Mapped[Optional[list]] = mapped_column(ARRAY(Text))
    user_feedback: Mapped[Optional[dict]] = mapped_column(JSONB)
    viral_factors: Mapped[Optional[dict]] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default="NOW()")

    # 关系
    video: Mapped["Video"] = relationship("Video", back_populates="insights")

    def __repr__(self):
        return f"<VideoInsight(id={self.id}, video_id={self.video_id})>"


class Collection(Base):
    """收藏模型"""
    __tablename__ = "collections"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    item_type: Mapped[str] = mapped_column(String(20), nullable=False)
    item_id: Mapped[str] = mapped_column(String(100), nullable=False)  # 支持字符串如B站BV号
    notes: Mapped[Optional[str]] = mapped_column(Text)
    tags: Mapped[Optional[list]] = mapped_column(ARRAY(Text))
    folder: Mapped[Optional[str]] = mapped_column(String(100))
    is_analysis: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default="NOW()")

    __table_args__ = (
        Index("idx_collections_item", "item_type", "item_id"),
    )

    # 关系
    user: Mapped["User"] = relationship("User", back_populates="collections")

    def __repr__(self):
        return f"<Collection(id={self.id}, user_id={self.user_id}, item_type={self.item_type})>"


class CompetitorWatch(Base):
    """竞品监控模型"""
    __tablename__ = "competitor_watch"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    creator_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("creators.id", ondelete="CASCADE"), nullable=False)
    watch_name: Mapped[Optional[str]] = mapped_column(String(100))
    alert_threshold: Mapped[int] = mapped_column(Integer, default=20)
    last_alert_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default="NOW()")

    __table_args__ = (
        UniqueConstraint("user_id", "creator_id", name="uq_competitor_watch_user_creator"),
    )

    # 关系
    user: Mapped["User"] = relationship("User", back_populates="competitor_watches")
    creator: Mapped["Creator"] = relationship("Creator", back_populates="competitor_watches")

    def __repr__(self):
        return f"<CompetitorWatch(id={self.id}, user_id={self.user_id}, creator_id={self.creator_id})>"


class TrendReport(Base):
    """趋势报告模型"""
    __tablename__ = "trend_reports"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    report_type: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    summary: Mapped[Optional[str]] = mapped_column(Text)
    ai_insights: Mapped[Optional[str]] = mapped_column(Text)
    hot_topics: Mapped[Optional[dict]] = mapped_column(JSONB)
    rising_creators: Mapped[Optional[dict]] = mapped_column(JSONB)
    content_trends: Mapped[Optional[dict]] = mapped_column(JSONB)
    user_interest_shift: Mapped[Optional[dict]] = mapped_column(JSONB)
    period_start: Mapped[datetime] = mapped_column(Date, nullable=False)
    period_end: Mapped[datetime] = mapped_column(Date, nullable=False)
    related_videos: Mapped[Optional[list]] = mapped_column(ARRAY(BigInteger))
    related_creators: Mapped[Optional[list]] = mapped_column(ARRAY(BigInteger))
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default="NOW()")

    __table_args__ = (
        Index("idx_trend_reports_period", "period_start", "period_end"),
    )

    def __repr__(self):
        return f"<TrendReport(id={self.id}, title={self.title})>"
