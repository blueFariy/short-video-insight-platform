from sqlalchemy import Column, String, Integer, DateTime, Text, Float, Boolean, BigInteger
from datetime import datetime

from app.models import Base
from sqlalchemy.orm import relationship


class Creator(Base):
    """Creator model - synced from user-service"""
    __tablename__ = "creators"

    # creator_id 作为主键 (复合主键: platform + creator_id)
    platform = Column(String(20), nullable=False)
    creator_id = Column(String(100), nullable=False, primary_key=True)
    name = Column(String(100), nullable=False)
    url = Column(Text)
    avatar_url = Column(Text)
    bio = Column(Text)
    follower_count = Column(BigInteger, default=0)
    following_count = Column(BigInteger, default=0)
    total_likes = Column(BigInteger, default=0)
    video_count = Column(BigInteger, default=0)
    avg_play_count = Column(BigInteger, default=0)
    avg_interaction_rate = Column(Float)
    main_category = Column(String(50))
    last_video_date = Column(DateTime, default=None)
    first_video_date = Column(DateTime, default=None)
    stats_updated_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.now)
    is_monitored = Column(Boolean, default=False)
