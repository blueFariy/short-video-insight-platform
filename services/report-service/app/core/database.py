"""
Database Connection Module for Report Service
"""
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


class DatabaseManager:
    """Database manager for report service"""

    def __init__(self):
        self._engine: Optional[AsyncEngine] = None
        self._session_factory: Optional[async_sessionmaker[AsyncSession]] = None

    def init_db(self, database_url: Optional[str] = None) -> None:
        """Initialize database connection"""
        db_url = database_url or settings.DATABASE_URL
        logger.info(f"Initializing database connection: {db_url}")

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

        logger.info("Database connection initialized successfully")

    async def close(self) -> None:
        """Close database connection"""
        if self._engine:
            await self._engine.dispose()
            logger.info("Database connection closed")

    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get database session with automatic commit/rollback"""
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


# Global database manager instance
db_manager = DatabaseManager()
