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

    log_level: str = "INFO"
    log_json: bool = True
    allowed_hosts_value: str = Field(
        default="localhost,127.0.0.1", validation_alias="ALLOWED_HOSTS"
    )
    enable_proxy_headers: bool = True
    trusted_proxy_ips_value: str = Field(default="*", validation_alias="TRUSTED_PROXY_IPS")
    max_request_body_bytes: int = 10_485_760
    enable_gzip: bool = True
    gzip_minimum_size: int = 1000

    request_id_header: str = Field(default="X-Request-ID")

    @property
    def allowed_origins(self) -> list[str]:
        return [origin.strip().rstrip("/") for origin in self.frontend_origin.split(",") if origin.strip()]

    @property
    def allowed_hosts(self) -> list[str]:
        return _split_csv(self.allowed_hosts_value)

    @property
    def trusted_proxy_ips(self) -> str | list[str]:
        hosts = _split_csv(self.trusted_proxy_ips_value)
        if hosts == ["*"]:
            return "*"
        return hosts


@lru_cache
def get_settings() -> Settings:
    return Settings()


def _split_csv(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]
