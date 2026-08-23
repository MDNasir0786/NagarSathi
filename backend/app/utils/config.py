"""Application settings, loaded from the environment / .env file."""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


def _split_csv(raw: str | None) -> list[str]:
    if not raw:
        return []
    return [item.strip() for item in raw.split(",") if item.strip()]


class Settings(BaseSettings):
    """All runtime configuration. Secrets live in the environment, never in code."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # ----- Application -----------------------------------------------------
    app_name: str = "Bhopal CivicAI"
    app_env: Literal["development", "staging", "production"] = "development"
    debug: bool = False
    api_v1_prefix: str = "/api/v1"
    log_level: str = "INFO"

    # ----- Database --------------------------------------------------------
    # Defaults to a local SQLite file so the API boots without Supabase
    # credentials (useful for local dev and CI). Point DATABASE_URL at the
    # Supabase Postgres pooler for anything real.
    database_url: str = "sqlite:///./bhopal_civicai.db"
    db_pool_size: int = 5
    db_max_overflow: int = 10
    db_echo: bool = False
    auto_create_tables: bool = True
    seed_departments: bool = True

    # ----- Supabase Auth ---------------------------------------------------
    supabase_url: str | None = None
    supabase_anon_key: str | None = None
    supabase_service_role_key: str | None = None
    supabase_jwt_secret: str | None = None
    supabase_jwt_algorithms: str = "HS256"
    supabase_jwt_audience: str = "authenticated"
    supabase_jwt_issuer: str | None = None
    jwks_cache_seconds: int = 600

    # ----- Claude ----------------------------------------------------------
    anthropic_api_key: str | None = None
    claude_model: str = "claude-opus-5"
    claude_effort: Literal["low", "medium", "high", "xhigh", "max"] = "medium"
    claude_max_tokens: int = 8000
    claude_timeout_seconds: float = 120.0
    ai_enabled: bool = True

    # ----- Roles -----------------------------------------------------------
    admin_emails: str = ""
    admin_bootstrap_secret: str | None = None

    # ----- CORS ------------------------------------------------------------
    cors_origins: str = "http://localhost:3000,http://localhost:5173,http://127.0.0.1:5173"

    # ----- Civic / geo -----------------------------------------------------
    city_name: str = "Bhopal"
    city_center_lat: float = 23.2599
    city_center_lon: float = 77.4126
    city_radius_km: float = 40.0
    duplicate_radius_meters: int = 150
    nearby_radius_meters: int = 500
    hotspot_grid_meters: int = 500
    hotspot_min_complaints: int = 3

    # ----- Rate limiting ---------------------------------------------------
    rate_limit_enabled: bool = True
    rate_limit_requests: int = 120
    rate_limit_window_seconds: int = 60
    ai_rate_limit_requests: int = 10

    # ----- Pagination ------------------------------------------------------
    default_page_size: int = Field(default=20, ge=1, le=100)
    max_page_size: int = Field(default=100, ge=1, le=200)

    # ----- Derived ---------------------------------------------------------
    @computed_field  # type: ignore[prop-decorator]
    @property
    def cors_origin_list(self) -> list[str]:
        return _split_csv(self.cors_origins)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def jwt_algorithm_list(self) -> list[str]:
        return _split_csv(self.supabase_jwt_algorithms) or ["HS256"]

    @computed_field  # type: ignore[prop-decorator]
    @property
    def admin_email_list(self) -> list[str]:
        return [email.lower() for email in _split_csv(self.admin_emails)]

    @computed_field  # type: ignore[prop-decorator]
    @property
    def jwks_url(self) -> str | None:
        if not self.supabase_url:
            return None
        return f"{self.supabase_url.rstrip('/')}/auth/v1/.well-known/jwks.json"

    @computed_field  # type: ignore[prop-decorator]
    @property
    def expected_issuer(self) -> str | None:
        if self.supabase_jwt_issuer:
            return self.supabase_jwt_issuer
        if self.supabase_url:
            return f"{self.supabase_url.rstrip('/')}/auth/v1"
        return None

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    @property
    def is_sqlite(self) -> bool:
        return self.database_url.startswith("sqlite")

    @property
    def claude_configured(self) -> bool:
        return bool(self.ai_enabled and self.anthropic_api_key)

    @property
    def auth_configured(self) -> bool:
        return bool(self.supabase_jwt_secret or self.jwks_url)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
