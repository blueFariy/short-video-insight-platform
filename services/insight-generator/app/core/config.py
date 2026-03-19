"""
Insight Service Configuration
"""
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings"""

    # Service
    SERVICE_NAME: str = "insight-service"
    SERVICE_HOST: str = "0.0.0.0"
    SERVICE_PORT: int = 8003

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/short_video_insight"

    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0

    # AI Models - OpenAI
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4"
    OPENAI_BASE_URL: str = "https://api.openai.com/v1"

    # AI Models - DeepSeek
    DEEPSEEK_API_KEY: str = ""
    DEEPSEEK_MODEL: str = "deepseek-chat"
    DEEPSEEK_BASE_URL: str = "https://api.deepseek.com/v1"

    # AI Models - Select default provider
    AI_PROVIDER: str = "deepseek"  # "openai" or "deepseek"

    # Analysis
    ANALYSIS_TEMP_DIR: str = "./temp/analysis"
    MAX_VIDEO_DURATION: int = 600  # 10 minutes

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings():
    return Settings()


settings = get_settings()
