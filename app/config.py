from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Vibedm API"
    api_v1_prefix: str = "/api/v1"
    public_api_prefix: str = "/api/public"
    environment: str = "development"

    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:54322/postgres"
    supabase_url: str = ""
    supabase_service_role_key: str = ""
    supabase_jwt_secret: str = "dev-secret"
    frontend_origin: str = "http://localhost:3000"

    instagram_app_id: str = ""
    instagram_app_secret: str = ""
    instagram_redirect_uri: str = "http://localhost:3000/auth/instagram/callback"
    instagram_webhook_secret: str = ""
    instagram_verify_token: str = "dev-instagram-verify-token"

    stripe_secret_key: str = ""
    stripe_webhook_secret: str = ""
    razorpay_key_id: str = ""
    razorpay_key_secret: str = ""
    razorpay_webhook_secret: str = ""

    job_worker_id: str = ""
    job_poll_interval_seconds: float = 2
    job_lock_timeout_minutes: int = 15

    request_id_header: str = Field(default="X-Request-ID")

    @property
    def allowed_origins(self) -> list[str]:
        return [origin.strip() for origin in self.frontend_origin.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
