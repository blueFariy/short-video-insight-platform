"""
Database Models for Report Service
"""
from sqlalchemy import Column, Integer, String, Text, Date, DateTime, JSON
from sqlalchemy.sql import func
from app.core.database import Base


class TrendReport(Base):
    """趋势报告模型"""
    __tablename__ = "trend_reports"

    id = Column(Integer, primary_key=True, autoincrement=True)
    report_type = Column(String(20), nullable=False)
    title = Column(String(200), nullable=False)
    summary = Column(JSON)
    ai_insights = Column(Text)
    hot_topics = Column(JSON)
    rising_creators = Column(JSON)
    content_trends = Column(JSON)
    user_interest_shift = Column(JSON)
    period_start = Column(Date, nullable=False)
    period_end = Column(Date, nullable=False)
    related_videos = Column(JSON)
    related_creators = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
