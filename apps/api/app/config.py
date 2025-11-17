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
    openai_chat_model: str = os.getenv("OPENAI_CHAT_MODEL", "gpt-4.1-mini")
    openai_embedding_model: str = os.getenv(
        "OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")

    # Optional auth
    app_secret: str | None = os.getenv("APP_SECRET")

    # App
    environment: str = os.getenv("ENVIRONMENT", "development")
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    
    # Marketing - Meta
    meta_app_id: str | None = os.getenv("META_APP_ID")
    meta_app_secret: str | None = os.getenv("META_APP_SECRET")
    meta_access_token: str | None = os.getenv("META_ACCESS_TOKEN")
    meta_ad_account_id: str | None = os.getenv("META_AD_ACCOUNT_ID")
    meta_pixel_id: str | None = os.getenv("META_PIXEL_ID")
    
    # Marketing - Google Ads
    google_ads_client_id: str | None = os.getenv("GOOGLE_ADS_CLIENT_ID")
    google_ads_client_secret: str | None = os.getenv("GOOGLE_ADS_CLIENT_SECRET")
    google_ads_developer_token: str | None = os.getenv("GOOGLE_ADS_DEVELOPER_TOKEN")
    google_ads_refresh_token: str | None = os.getenv("GOOGLE_ADS_REFRESH_TOKEN")
    google_ads_customer_id: str | None = os.getenv("GOOGLE_ADS_CUSTOMER_ID")
    
    # Marketing - TikTok
    tiktok_access_token: str | None = os.getenv("TIKTOK_ACCESS_TOKEN")
    tiktok_advertiser_id: str | None = os.getenv("TIKTOK_ADVERTISER_ID")
    tiktok_pixel_id: str | None = os.getenv("TIKTOK_PIXEL_ID")
    
    # Marketing - GA4
    ga4_measurement_id: str | None = os.getenv("GA4_MEASUREMENT_ID")
    ga4_api_secret: str | None = os.getenv("GA4_API_SECRET")

    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache
def get_settings() -> Settings:
    """Cached settings singleton"""
    return Settings()
