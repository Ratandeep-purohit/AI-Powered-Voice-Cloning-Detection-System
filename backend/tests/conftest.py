"""Pytest fixtures for Phase 00 foundation tests.

Tests use environment variables with a synthetic DATABASE_URL so they
do not require a live PostgreSQL instance for Phase 00.  Any test that
truly needs the database must be marked separately.
"""

from __future__ import annotations

import os

import pytest
from fastapi.testclient import TestClient

from dotenv import load_dotenv

# ── Force test environment before any app import ──────────────────────────
os.environ["APP_ENV"] = "testing"

# Load variables from .env if present
load_dotenv()

# Fallback if TEST_DATABASE_URL isn't in .env
os.environ.setdefault(
    "TEST_DATABASE_URL",
    "postgresql://test_user:test_pass@localhost:5432/voice_cloning_test",
)
# Ensure config uses the test DB
os.environ["DATABASE_URL"] = os.environ["TEST_DATABASE_URL"]

from app.database import get_engine, get_session_factory
from app.models.base import Base

@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    """Create all tables in the test database once per session."""
    engine = get_engine()
    # Create the schema for tests
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    # Clean up after tests are done
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def db_session():
    """Yield a database session and rollback after the test."""
    SessionLocal = get_session_factory()
    session = SessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()

@pytest.fixture(scope="session")
def fastapi_app():  # type: ignore[no-untyped-def]
    """Return the FastAPI application instance.

    Named 'fastapi_app' to avoid collision with pytest-flask's 'app' fixture.
    """
    from app.main import app as _app  # noqa: PLC0415

    return _app


@pytest.fixture(scope="session")
def client(fastapi_app):  # type: ignore[no-untyped-def]
    """Return a TestClient bound to the FastAPI app."""
    with TestClient(fastapi_app, raise_server_exceptions=False) as c:
        yield c
