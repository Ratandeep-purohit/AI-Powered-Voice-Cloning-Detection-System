"""Application configuration loaded from environment variables.

Credentials are never hardcoded here.  All sensitive values come from
the environment or a local .env file that is excluded from source control.
"""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Validated application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Application ────────────────────────────────────────────────────────
    app_env: str = Field(default="development", description="Runtime environment.")
    app_host: str = Field(default="0.0.0.0", description="Bind host.")
    app_port: int = Field(default=8000, description="Bind port.")
    log_level: str = Field(default="INFO", description="Logging level.")

    # ── Database ───────────────────────────────────────────────────────────
    database_url: str = Field(
        ...,
        description="PostgreSQL connection URL.  Must be set via environment.",
    )
    test_database_url: str | None = Field(
        default=None,
        description="Isolated test database URL.",
    )

    # ── JWT Authentication – Phase 02 ─────────────────────────────────────
    # jwt_secret MUST come from the environment.  No default is permitted;
    # the application will refuse to start if this is absent.
    jwt_secret: str = Field(
        ...,
        description="HMAC-SHA256 JWT signing secret.  Must be set via environment.",
    )
    jwt_algorithm: str = Field(
        default="HS256",
        description="JWT signing algorithm.",
    )
    access_token_expire_minutes: int = Field(
        default=60,
        description="JWT access token lifetime in minutes.",
    )

    # ── Derived helpers ────────────────────────────────────────────────────
    @property
    def is_development(self) -> bool:
        return self.app_env.lower() == "development"

    @property
    def is_testing(self) -> bool:
        return self.app_env.lower() == "testing"

    @field_validator("database_url")
    @classmethod
    def _database_url_must_not_be_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("DATABASE_URL must not be empty.")
        return v

    def safe_database_url(self) -> str:
        """Return the database URL with the password redacted for logging."""
        try:
            from urllib.parse import urlparse, urlunparse

            parsed = urlparse(self.database_url)
            if parsed.password:
                safe = parsed._replace(
                    netloc=f"{parsed.username}:***@{parsed.hostname}"
                    + (f":{parsed.port}" if parsed.port else "")
                )
                return urlunparse(safe)
        except Exception:
            pass
        return "<database_url>"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the cached application settings singleton."""
    return Settings()


def get_fresh_settings() -> Settings:
    """Return a non-cached settings instance (used in tests to reload config)."""
    return Settings()
