"""
Database models for insight-generator service
"""
from datetime import datetime
from typing import Optional, List
from sqlalchemy import Column, String, Integer, DateTime, Text, Float, Boolean, BigInteger, ARRAY, UniqueConstraint, JSON
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


class VideoInsight(Base):
    """Video insight model - stores AI analysis results"""
    __tablename__ = "video_insights"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    video_id = Column(String, nullable=False, index=True)

    # AI总结
    ai_summary = Column(Text)
    hook_3s = Column(Text)
    hook_type = Column(String(30))

    # 脚本结构
    structure_type = Column(String(30))
    structure_analysis = Column(JSON)

    # 关键词
    keywords = Column(ARRAY(String))
    entity_tags = Column(JSON)

    # 互动分析
    sentiment_score = Column(Float)
    comment_high_freq = Column(ARRAY(String))
    user_feedback = Column(JSON)

    # 爆款因子
    viral_factors = Column(JSON)

    # 改进建议
    improvements = Column(ARRAY(String))

    created_at = Column(DateTime, default=datetime.now)

from sqlalchemy import Column, String, Integer, DateTime, Text, Float, Boolean, BigInteger, ARRAY, ForeignKey
from datetime import datetime

class Video(Base):
    """Video model - synced from user-service"""
    __tablename__ = "videos"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    platform = Column(String(20), nullable=False)
    video_id = Column(String(100), nullable=False)
    video_url = Column(Text, nullable=False)
    title = Column(String(500))
    description = Column(Text)
    cover_image_url = Column(Text)
    duration = Column(Integer)
    publish_time = Column(DateTime)

    # Metrics
    play_count = Column(BigInteger, default=0)
    like_count = Column(BigInteger, default=0)
    comment_count = Column(BigInteger, default=0)
    share_count = Column(BigInteger, default=0)
    danmaku_count = Column(BigInteger, default=0)
    coin_count = Column(BigInteger, default=0)
    collect_count = Column(BigInteger, default=0)

    # Creator reference - 使用 creator_id (非主键id)
    creator_id = Column(String(100), ForeignKey('creators.creator_id'))
    creator_name = Column(String(500))

    # Tags and category
    category = Column(String(50))
    tags = Column(ARRAY(String(100)), default=[])  # Stored as comma-separated string
    ai_generated_tags = Column(ARRAY(String(1000)), default=[])

    # Data quality
    data_quality_score = Column(Float, default=1.0)
    is_denoised = Column(Boolean, default=False)

    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now)

# Database manager
_engine = None
_session_factory = None


def get_engine():
    global _engine
    if _engine is None:
        from app.core.config import settings
        _engine = create_async_engine(
            settings.DATABASE_URL,
            echo=False,
            pool_size=10,
            max_overflow=20
        )
    return _engine


def get_session_factory():
    global _session_factory
    if _session_factory is None:
        _session_factory = async_sessionmaker(
            bind=get_engine(),
            class_=AsyncSession,
            expire_on_commit=False
        )
    return _session_factory


async def get_session() -> AsyncSession:
    factory = get_session_factory()
    async with factory() as session:
        yield session
