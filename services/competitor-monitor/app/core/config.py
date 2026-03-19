"""
Competitor Monitor Service Configuration
"""
from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import List


class Settings(BaseSettings):
    """Application settings"""

    # Service
    SERVICE_NAME: str = "competitor-monitor"
    SERVICE_HOST: str = "0.0.0.0"
    SERVICE_PORT: int = 8005

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/short_video_insight"

    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0

    # Monitoring Settings
    CHECK_INTERVAL: int = 300  # 5 minutes
    ALERT_THRESHOLD_FANS: float = 0.1  # 10% change
    ALERT_THRESHOLD_LIKES: float = 0.2  # 20% change
    ALERT_THRESHOLD_VIEWS: float = 0.3  # 30% change

    # Notification Settings
    NOTIFICATION_ENABLED: bool = True
    NOTIFICATION_CHANNELS: List[str] = ["email", "webhook"]

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings():
    return Settings()


settings = get_settings()
