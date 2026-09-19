"""Application configuration loaded from environment variables."""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Validated application settings."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="ignore")

    app_env: str = Field(default="development")
    app_host: str = Field(default="0.0.0.0")
    app_port: int = Field(default=8000)
    log_level: str = Field(default="INFO")
    cors_allowed_origins: str = Field(default="http://localhost:5173,http://localhost:3000")

    database_url: str = Field(...)
    test_database_url: str | None = Field(default=None)

    jwt_secret: str = Field(...)
    jwt_algorithm: str = Field(default="HS256")
    access_token_expire_minutes: int = Field(default=30)
    refresh_token_expire_days: int = Field(default=7)

    # Phase 03 audio intake configuration.
    audio_storage_path: str = Field(default="storage/audio")
    audio_max_upload_size_mb: int = Field(default=25)
    audio_allowed_extensions: str = Field(default="wav,mp3,ogg,flac,m4a")

    # Phase 04 preprocessing configuration. These values are configurable so
    # the preprocessing target can be aligned with the eventual ML model.
    audio_processing_sample_rate: int = Field(default=16000)
    audio_processing_channels: int = Field(default=1)
    audio_processing_max_duration_seconds: int = Field(default=1800)
    audio_processing_ffmpeg_binary: str = Field(default="ffmpeg")

    # Phase 05 ASVspoof 2019 LA dataset configuration. The dataset itself is
    # intentionally external to the repository and must not be committed.
    asvspoof_dataset_root: str = Field(default="")

    # Phase 06 runtime detector configuration. The checkpoint is an external
    # runtime artifact and remains ignored by Git. The threshold was frozen
    # from the DEV split threshold analysis (balanced-accuracy operating point).
    aasist_checkpoint_path: str = Field(default="artifacts/checkpoints/aasist_balanced/best.pt")
    aasist_model_name: str = Field(default="AASIST-family spoof detector")
    aasist_model_version: str = Field(default="balanced-v1")
    aasist_target_duration_seconds: float = Field(default=4.0)
    aasist_detection_threshold: float = Field(default=0.5977)

    @property
    def is_development(self) -> bool:
        return self.app_env.lower() == "development"

    @property
    def is_testing(self) -> bool:
        return self.app_env.lower() == "testing"

    @property
    def allowed_audio_extensions(self) -> set[str]:
        return {item.strip().lower().lstrip(".") for item in self.audio_allowed_extensions.split(",") if item.strip()}

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_allowed_origins.split(",") if origin.strip()]

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

    @field_validator("audio_max_upload_size_mb")
    @classmethod
    def _audio_upload_size_positive(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("AUDIO_MAX_UPLOAD_SIZE_MB must be positive.")
        return v

    @field_validator("audio_processing_sample_rate", "audio_processing_channels", "audio_processing_max_duration_seconds")
    @classmethod
    def _audio_processing_values_positive(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("Audio processing configuration values must be positive.")
        return v

    @field_validator("aasist_target_duration_seconds")
    @classmethod
    def _aasist_target_duration_positive(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("AASIST_TARGET_DURATION_SECONDS must be positive.")
        return v

    @field_validator("aasist_detection_threshold")
    @classmethod
    def _aasist_threshold_in_range(cls, v: float) -> float:
        if not 0.0 < v < 1.0:
            raise ValueError("AASIST_DETECTION_THRESHOLD must be between 0 and 1.")
        return v

    def safe_database_url(self) -> str:
        """Return the database URL with the password redacted for logging."""
        try:
            from urllib.parse import urlparse, urlunparse
            parsed = urlparse(self.database_url)
            if parsed.password:
                safe = parsed._replace(netloc=f"{parsed.username}:***@{parsed.hostname}" + (f":{parsed.port}" if parsed.port else ""))
                return urlunparse(safe)
        except Exception:
            pass
        return "<database_url>"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


def get_fresh_settings() -> Settings:
    return Settings()
