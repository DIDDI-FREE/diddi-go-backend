"""Application settings, powered by pydantic-settings.

Sources (highest priority first):
  1. process environment (useful in tests / docker-compose)
  2. values from `./.env` (local dev — never committed)
  3. defaults declared below

Instantiated at module import time as `settings` — importers do
`from app_base.core.settings import settings`.
"""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    app_name: str = "DiddiGo"
    environment: str = "development"
    api_prefix: str = "/v1"

    # The runtime async engine uses `database_url` (asyncpg driver).
    # Alembic and any sync-only tooling can coexist with a separate url later.
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5433/diddi_go"
    redis_url: str = "redis://localhost:6379/0"

    jwt_secret: str = "change-me-in-prod-at-least-32-characters-long"
    jwt_access_lifetime_minutes: int = 15
    jwt_refresh_lifetime_days: int = 30

    otp_rate_limit_seconds: int = 60
    otp_code_lifetime_seconds: int = 300

    diddimap_base_url: str = "http://localhost:4000"


settings = Settings()
