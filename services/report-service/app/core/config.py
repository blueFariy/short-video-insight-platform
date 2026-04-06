"""
Report Service Configuration
"""
from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import List, Optional


class Settings(BaseSettings):
    """Application settings"""

    # Service
    SERVICE_NAME: str = "report-service"
    SERVICE_HOST: str = "0.0.0.0"
    SERVICE_PORT: int = 8006

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/short_video_insight"

    # Redis (for Celery)
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[str] = None

    # Celery
    CELERY_BROKER_URL: str = "redis://redis:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://redis:6379/0"

    # Report Settings
    REPORT_DIR: str = "./reports"
    TEMP_DIR: str = "./temp"
    MAX_REPORT_SIZE: int = 10000  # Maximum rows

    # Export Settings
    EXPORT_FORMATS: List[str] = ["excel", "pdf", "csv"]

    class Config:
        env_file = "env/.env"
        case_sensitive = True
        extra = "ignore"


@lru_cache()
def get_settings():
    return Settings()


settings = get_settings()
