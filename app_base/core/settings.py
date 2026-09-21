"""Application settings, powered by pydantic-settings.

Sources (highest priority first):
  1. process environment (useful in tests / docker-compose)
  2. values from `./.env` (local dev — never committed)
  3. defaults declared below

Instantiated at module import time as `settings` — importers do
`from app_base.core.settings import settings`.
"""

from __future__ import annotations

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    app_name: str = "DiddiGo"
    environment: str = Field(default="development", validation_alias=AliasChoices("ENVIRONMENT", "APP_ENV"))
    api_prefix: str = "/v1"
    cors_origins: str = ""
    cors_origin_regex: str | None = r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$"
    log_level: str = "INFO"
    log_format: str = "json"

    # The runtime async engine uses `database_url` (asyncpg driver).
    # Alembic and any sync-only tooling can coexist with a separate url later.
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:15432/diddi_go"
    redis_url: str = "redis://localhost:16379/0"

    jwt_secret: str = "change-me-in-prod-at-least-32-characters-long"
    jwt_access_lifetime_minutes: int = 15
    jwt_refresh_lifetime_days: int = 30

    otp_rate_limit_seconds: int = 60
    otp_code_lifetime_seconds: int = 300

    diddimap_base_url: str = "http://localhost:4000"
    diddimap_access_token: str | None = None

    # Internal Pilotage reports are intentionally bounded to a recent window
    # so a service caller cannot turn a daily endpoint into an unbounded scan.
    ride_summary_max_age_days: int = Field(default=31, ge=0, le=3660)

    identity_base_url: str | None = None
    identity_jwks_url: str | None = None
    identity_issuer: str = "diddifree-id"
    identity_profile_url: str | None = None
    identity_service_key: str | None = None

    push_enabled: bool = False
    fcm_project_id: str | None = None
    fcm_service_account_json: str | None = None
    fcm_service_account_file: str | None = None

    diddipay_base_url: str | None = None
    diddipay_client_id: str = "diddigo"
    diddipay_service_key: str | None = None
    diddipay_callback_secret: str | None = None
    diddipay_http_timeout_seconds: float = 15.0
    diddigo_payment_callback_url: str | None = None
    driver_min_balance: int = 0
    driver_max_estimated_commission: int = 0

    # Manual ride waiting. GPS drift is tolerated up to the configured speed;
    # telemetry older than the Redis TTL cannot authorize a waiting start.
    waiting_price_per_minute_xof: int = Field(default=100, ge=0)
    waiting_stationary_speed_threshold_kmh: float = Field(default=3.0, ge=0)
    waiting_telemetry_ttl_seconds: int = Field(default=30, ge=5, le=300)

    emergency_support_email: str = "direction.generale@diddifree.com"
    emergency_support_whatsapp: str | None = None
    emergency_whatsapp_webhook_url: str | None = None
    emergency_whatsapp_api_key: str | None = None
    emergency_email_from: str = "alerts@diddifree.com"
    emergency_smtp_host: str | None = None
    emergency_smtp_port: int = 587
    emergency_smtp_username: str | None = None
    emergency_smtp_password: str | None = None
    emergency_smtp_use_tls: bool = True
    emergency_notification_timeout_seconds: float = 10.0

    # Reconciliation re-reads GET /payment-intents/{id} for anything still
    # waiting on a DiddiPay callback, so a lost webhook self-heals instead of
    # stranding a payment in `requires_action` forever.
    payment_reconciliation_enabled: bool = True
    payment_reconciliation_interval_seconds: int = 300
    payment_reconciliation_batch_size: int = 50
    # Grace period before an intent is considered late — the payer may still be
    # on the checkout page.
    payment_reconciliation_min_age_seconds: int = 120
    # Past this age DiddiPay has expired the intent; chasing it is pointless.
    payment_reconciliation_max_age_seconds: int = 259_200  # 72h

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def effective_identity_jwks_url(self) -> str | None:
        if self.identity_jwks_url:
            return self.identity_jwks_url
        if self.identity_base_url:
            return f"{self.identity_base_url.rstrip('/')}/.well-known/jwks.json"
        return None

    @property
    def effective_identity_profile_url(self) -> str | None:
        if self.identity_profile_url:
            return self.identity_profile_url
        if self.identity_base_url:
            return f"{self.identity_base_url.rstrip('/')}/identity/v1/users/me"
        return None


settings = Settings()
