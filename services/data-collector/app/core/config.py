"""
Data Collector Service Configuration
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
from typing import Dict, List, Optional


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file="env/.env",
        case_sensitive=True,
        extra="ignore"
    )
    """Application settings"""

    # Service
    SERVICE_NAME: str = "data-collector"
    SERVICE_HOST: str = "0.0.0.0"
    SERVICE_PORT: int = 8004

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/short_video_insight"

    # Redis (for Celery)
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[str] = None

    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"

    # Elasticsearch
    ELASTICSEARCH_HOST: str = "localhost"
    ELASTICSEARCH_PORT: int = 9200

    # Collection Settings
    COLLECTION_INTERVAL: int = 3600  # 1 hour
    MAX_VIDEOS_PER_ACCOUNT: int = 50
    VIDEO_PLATFORMS: List[str] = ["douyin", "bilibili", "xiaohongshu", "kuaishou"]

    # Download Settings
    DOWNLOAD_DIR: str = "./downloads"
    TEMP_DIR: str = "./temp"

    # Platform API Settings
    # Douyin
    DOUYIN_API_KEY: Optional[str] = None
    DOUYIN_API_SECRET: Optional[str] = None
    SHUJU_API_TOKEN: Optional[str] = None  # 第三方数据服务

    # Bilibili
    BILI_APP_KEY: Optional[str] = None
    BILI_APP_SECRET: Optional[str] = None

    # Xiaohongshu
    XHS_API_KEY: Optional[str] = None

    # Viral Detection Settings
    VIRAL_GROWTH_THRESHOLD: float = 0.5  # 增长率阈值
    VIRAL_ENGAGEMENT_THRESHOLD: float = 0.05  # 互动率阈值
    VIRAL_AUTHENTICITY_THRESHOLD: float = 0.7  # 真实性阈值

    # Alert Settings
    ALERT_ENABLED: bool = True
    ALERT_CHANNELS: List[str] = ["app", "email"]


@lru_cache()
def get_settings():
    return Settings()


settings = get_settings()
