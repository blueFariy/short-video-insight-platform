"""
Data Collector Service Configuration
"""
from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Dict, List


class Settings(BaseSettings):
    """Application settings"""

    # Service
    SERVICE_NAME: str = "data-collector"
    SERVICE_HOST: str = "0.0.0.0"
    SERVICE_PORT: int = 8004

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/short_video_insight"

    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0

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

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings():
    return Settings()


settings = get_settings()
