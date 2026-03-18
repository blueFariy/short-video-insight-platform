"""
Database Connection - PostgreSQL with SQLAlchemy 2.0
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
from sqlalchemy import create_engine
from loguru import logger

from app.core.config import settings


class Base(DeclarativeBase):
    """SQLAlchemy声明性基类"""
    pass


class DatabaseManager:
    """数据库管理器"""

    def __init__(self):
        self._engine: Optional[AsyncEngine] = None
        self._session_factory: Optional[async_sessionmaker[AsyncSession]] = None

    def init_db(self, database_url: Optional[str] = None) -> None:
        """初始化数据库连接"""
        db_url = database_url or settings.DATABASE_URL
        logger.info(f"Initializing database: {db_url}")

        # 创建异步引擎
        self._engine = create_async_engine(
            db_url,
            echo=settings.DEBUG,
            pool_size=10,
            max_overflow=20,
            pool_pre_ping=True,
            pool_recycle=3600
        )

        # 创建会话工厂
        self._session_factory = async_sessionmaker(
            bind=self._engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
            autocommit=False
        )

        logger.info("Database initialized successfully")

    async def close(self) -> None:
        """关闭数据库连接"""
        if self._engine:
            await self._engine.dispose()
            logger.info("Database connection closed")

    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """获取数据库会话"""
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
        """创建所有表"""
        if not self._engine:
            raise RuntimeError("Database not initialized")

        async with self._engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("All tables created")

    async def drop_tables(self) -> None:
        """删除所有表"""
        if not self._engine:
            raise RuntimeError("Database not initialized")

        async with self._engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        logger.info("All tables dropped")


# 全局数据库管理器实例
db_manager = DatabaseManager()


# 依赖注入函数
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI依赖注入 - 获取数据库会话"""
    async with db_manager.get_session() as session:
        try:
            yield session
        finally:
            await session.close()
