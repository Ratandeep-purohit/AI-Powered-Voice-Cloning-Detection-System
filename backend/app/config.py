"""Application configuration loaded from environment variables."""

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

    app_env: str = Field(default="development")
    app_host: str = Field(default="0.0.0.0")
    app_port: int = Field(default=8000)
    log_level: str = Field(default="INFO")

    database_url: str = Field(...)
    test_database_url: str | None = Field(default=None)

    # Phase 02 authentication configuration.
    jwt_secret: str = Field(...)
    jwt_algorithm: str = Field(default="HS256")
    access_token_expire_minutes: int = Field(default=30)
    refresh_token_expire_days: int = Field(default=7)

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

    @field_validator("access_token_expire_minutes")
    @classmethod
    def _access_token_expiry_positive(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("ACCESS_TOKEN_EXPIRE_MINUTES must be positive.")
        return v

    @field_validator("refresh_token_expire_days")
    @classmethod
    def _refresh_token_expiry_positive(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("REFRESH_TOKEN_EXPIRE_DAYS must be positive.")
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
    return Settings()


def get_fresh_settings() -> Settings:
    return Settings()
