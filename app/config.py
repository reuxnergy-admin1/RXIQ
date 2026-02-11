"""Application configuration using pydantic-settings."""

from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # App
    app_name: str = "RXIQ API"
    app_version: str = "1.0.0"
    app_env: str = "production"
    app_debug: bool = False
    log_level: str = "info"

    # OpenAI
    openai_api_key: str = ""

    # Redis
    redis_url: Optional[str] = None

    # Rate Limiting (per month)
    rate_limit_free: str = "100/month"
    rate_limit_starter: str = "2500/month"
    rate_limit_pro: str = "15000/month"
    rate_limit_business: str = "75000/month"

    # Default rate limit for unauthenticated / free tier
    default_rate_limit: str = "10/minute"

    # Sentry
    sentry_dsn: Optional[str] = None

    # CORS
    cors_origins: str = "*"

    # RapidAPI
    rapidapi_proxy_secret: Optional[str] = None

    # Scraping
    scrape_timeout: int = 15
    blocked_url_patterns: str = ""  # Comma-separated patterns to block

    # Caching
    cache_ttl: int = 3600

    # Content limits
    max_content_length: int = 50000
    max_request_size: int = 1048576  # 1MB

    # Security
    trusted_hosts: str = "*"

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",")]

    @property
    def blocked_url_patterns_list(self) -> list[str]:
        if not self.blocked_url_patterns:
            return []
        return [p.strip() for p in self.blocked_url_patterns.split(",") if p.strip()]

    @property
    def trusted_hosts_list(self) -> list[str]:
        return [h.strip() for h in self.trusted_hosts.split(",")]


@lru_cache
def get_settings() -> Settings:
    """Cached settings instance."""
    return Settings()
