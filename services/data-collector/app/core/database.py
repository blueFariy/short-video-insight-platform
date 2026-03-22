"""
Database Connection - PostgreSQL with SQLAlchemy 2.0
Data Collector Service
"""
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    AsyncEngine,
    create_async_engine,
    async_sessionmaker
)
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import Column, String, Integer, DateTime, Text, Float, Boolean
from datetime import datetime
from loguru import logger

from app.core.config import settings


class Base(DeclarativeBase):
    """SQLAlchemy declarative base"""
    pass


class MonitoredAccount(Base):
    """Monitored account model"""
    __tablename__ = "monitored_accounts"

    id = Column(String(50), primary_key=True)
    name = Column(String(100), nullable=False)
    platform = Column(String(50), nullable=False)  # douyin, bilibili, xiaohongshu, kuaishou
    account_id = Column(String(100), nullable=False)  # Platform account ID
    url = Column(String(500), nullable=False)
    category = Column(String(50), default="general")
    status = Column(String(20), default="active")  # active, paused
    follower_count = Column(Integer, default=0)
    video_count = Column(Integer, default=0)
    last_collection_time = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class CollectedVideo(Base):
    """Collected video model"""
    __tablename__ = "collected_videos"

    id = Column(String(50), primary_key=True)
    video_id = Column(String(100), nullable=False, index=True)  # Platform video ID
    title = Column(String(500), nullable=False)
    platform = Column(String(50), nullable=False)
    account_id = Column(String(100), nullable=False)
    account_name = Column(String(100))
    url = Column(String(500))
    cover_url = Column(String(500))
    duration = Column(Integer, default=0)

    # Metrics
    play_count = Column(Integer, default=0)
    like_count = Column(Integer, default=0)
    comment_count = Column(Integer, default=0)
    share_count = Column(Integer, default=0)
    favorite_count = Column(Integer, default=0)

    # Calculated metrics
    engagement_rate = Column(Float, default=0.0)

    # Timestamps
    publish_time = Column(DateTime, nullable=True)
    collected_at = Column(DateTime, default=datetime.now)

    # Status
    is_deleted = Column(Boolean, default=False)


class CollectionTask(Base):
    """Collection task log"""
    __tablename__ = "collection_tasks"

    id = Column(String(50), primary_key=True)
    task_type = Column(String(50))  # hot_search, keyword, account, all
    platform = Column(String(50))
    account_id = Column(String(100), nullable=True)
    keyword = Column(String(100), nullable=True)
    status = Column(String(20))  # pending, running, completed, failed
    videos_collected = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    started_at = Column(DateTime, default=datetime.now)
    completed_at = Column(DateTime, nullable=True)


class DatabaseManager:
    """Database manager"""

    def __init__(self):
        self._engine: Optional[AsyncEngine] = None
        self._session_factory: Optional[async_sessionmaker[AsyncSession]] = None

    def init_db(self, database_url: Optional[str] = None) -> None:
        """Initialize database connection"""
        db_url = database_url or settings.DATABASE_URL
        logger.info(f"Initializing database: {db_url}")

        self._engine = create_async_engine(
            db_url,
            echo=False,
            pool_size=10,
            max_overflow=20,
            pool_pre_ping=True,
            pool_recycle=3600
        )

        self._session_factory = async_sessionmaker(
            bind=self._engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
            autocommit=False
        )

        logger.info("Database initialized successfully")

    async def close(self) -> None:
        """Close database connection"""
        if self._engine:
            await self._engine.dispose()
            logger.info("Database connection closed")

    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get database session"""
        if not self._session_factory:
            raise RuntimeError("Database not initialized. Call init_db() first.")

        async with self._session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()

    async def create_tables(self) -> None:
        """Create all tables"""
        if not self._engine:
            raise RuntimeError("Database not initialized")

        async with self._engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("All tables created")


# Global database manager instance
db_manager = DatabaseManager()
