from sqlalchemy import Column, String, Integer, DateTime, Text, Float, Boolean, BigInteger, ARRAY, ForeignKey
from datetime import datetime

from app.models import Base
from sqlalchemy.orm import relationship


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
