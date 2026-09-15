"""Phase 00 – Configuration tests."""

from __future__ import annotations

import os

import pytest


def test_settings_loads_with_valid_env() -> None:
    """Settings must load successfully when DATABASE_URL is provided."""
    from app.config import Settings  # noqa: PLC0415

    s = Settings(
        database_url="postgresql://u:p@localhost:5432/db",
        app_env="testing",
    )
    assert s.database_url.startswith("postgresql://")
    assert s.app_env == "testing"


def test_settings_fails_without_database_url() -> None:
    """Settings must raise when DATABASE_URL is missing."""
    from pydantic import ValidationError  # noqa: PLC0415

    from app.config import Settings  # noqa: PLC0415

    env_backup = os.environ.pop("DATABASE_URL", None)
    try:
        with pytest.raises((ValidationError, Exception)):
            Settings(_env_file=None)  # type: ignore[call-arg]
    finally:
        if env_backup is not None:
            os.environ["DATABASE_URL"] = env_backup


def test_safe_database_url_redacts_password() -> None:
    """Password must not appear in the safe URL representation."""
    from app.config import Settings  # noqa: PLC0415

    s = Settings(database_url="postgresql://admin:supersecret@db:5432/mydb")
    safe = s.safe_database_url()
    assert "supersecret" not in safe
    assert "***" in safe


def test_is_development_flag() -> None:
    from app.config import Settings  # noqa: PLC0415

    s = Settings(database_url="postgresql://u:p@h/db", app_env="development")
    assert s.is_development is True
    assert s.is_testing is False


def test_is_testing_flag() -> None:
    from app.config import Settings  # noqa: PLC0415

    s = Settings(database_url="postgresql://u:p@h/db", app_env="testing")
    assert s.is_testing is True
    assert s.is_development is False
