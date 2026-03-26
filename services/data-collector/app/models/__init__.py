from sqlalchemy.orm import DeclarativeBase
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    AsyncEngine,
    create_async_engine,
    async_sessionmaker
)
from loguru import logger

from app.core.config import settings

class Base(DeclarativeBase):
    """SQLAlchemy declarative base"""
    pass

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

        # 确保 creators 表有 is_monitored 列
        await self._ensure_creators_columns()

    async def _ensure_creators_columns(self) -> None:
        """确保 creators 表有必要的列"""
        if not self._engine:
            return

        try:
            async with self._engine.begin() as conn:
                from sqlalchemy import text

                # 检查 is_monitored 列是否存在
                result = await conn.execute(text("""
                    SELECT column_name
                    FROM information_schema.columns
                    WHERE table_name = 'creators' AND column_name = 'is_monitored'
                """))
                if not result.fetchone():
                    await conn.execute(text("""
                        ALTER TABLE creators ADD COLUMN is_monitored BOOLEAN DEFAULT FALSE
                    """))
                    logger.info("Added is_monitored column to creators table")

                # 检查 url 列是否存在
                result = await conn.execute(text("""
                    SELECT column_name
                    FROM information_schema.columns
                    WHERE table_name = 'creators' AND column_name = 'url'
                """))
                if not result.fetchone():
                    await conn.execute(text("""
                        ALTER TABLE creators ADD COLUMN url TEXT
                    """))
                    logger.info("Added url column to creators table")

                # 检查 video_count 列是否存在
                result = await conn.execute(text("""
                    SELECT column_name
                    FROM information_schema.columns
                    WHERE table_name = 'creators' AND column_name = 'video_count'
                """))
                if not result.fetchone():
                    await conn.execute(text("""
                        ALTER TABLE creators ADD COLUMN video_count BIGINT DEFAULT 0
                    """))
                    logger.info("Added video_count column to creators table")

                # 检查 videos 表是否有必要的列
                result = await conn.execute(text("""
                    SELECT column_name
                    FROM information_schema.columns
                    WHERE table_name = 'videos' AND column_name = 'video_url'
                """))
                if not result.fetchone():
                    await conn.execute(text("""
                        ALTER TABLE videos ADD COLUMN video_url TEXT
                    """))
                    logger.info("Added video_url column to videos table")
        except Exception as e:
            logger.warning(f"Failed to ensure database columns: {e}")


# Global database manager instance
db_manager = DatabaseManager()

from app.models.creator import Creator
from app.models.video import Video
from app.models.viral_alert import VideoMetricSnapshot, UserInterest, ViralAlert, CategoryBenchmark
from app.models.scheduled_task import ScheduledTask

__all__ = [
    'Creator',
    'Video',
    'VideoMetricSnapshot',
    'UserInterest',
    'ViralAlert',
    'CategoryBenchmark',
    'ScheduledTask',
]
