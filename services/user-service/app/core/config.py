"""
Application Configuration
"""
from typing import List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings"""

    # App
    APP_NAME: str = "User Service"
    DEBUG: bool = True

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/short_video_insight"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 10080  # 7天 = 7 * 24 * 60 分钟

    # Elasticsearch
    ELASTICSEARCH_URL: str = "http://localhost:9200"

    # CORS
    CORS_ORIGINS: List[str] = ["*"]

    class Config:
        env_file = "env/.env"
        case_sensitive = True
        extra = "ignore"


settings = Settings()
