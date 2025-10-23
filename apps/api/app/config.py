"""Application configuration"""
import os
from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """App settings loaded from environment"""

    # Database
    database_url: str = os.getenv(
        "DATABASE_URL",
        "postgresql://dev:dev@localhost:5432/app"
    )

    # Redis
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379")

    # Qdrant
    qdrant_url: str = os.getenv("QDRANT_URL", "http://localhost:6333")
    qdrant_api_key: str | None = os.getenv("QDRANT_API_KEY")

    # OpenAI
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")

    # Optional auth
    app_secret: str | None = os.getenv("APP_SECRET")

    # App
    environment: str = os.getenv("ENVIRONMENT", "development")
    log_level: str = os.getenv("LOG_LEVEL", "INFO")

    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache
def get_settings() -> Settings:
    """Cached settings singleton"""
    return Settings()
