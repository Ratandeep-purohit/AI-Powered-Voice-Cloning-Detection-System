"""SQLAlchemy engine, session factory, and database connectivity helpers.

The database URL is always loaded from the application settings (environment).
Credentials are never hardcoded.  Connection errors are caught and re-raised
without exposing the original connection string.
"""

from __future__ import annotations

import logging
from collections.abc import Generator
from contextlib import contextmanager

from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError, SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from app.config import get_settings

logger = logging.getLogger(__name__)


def _build_engine(database_url: str):  # type: ignore[no-untyped-def]
    """Create a SQLAlchemy engine from the given URL."""
    return create_engine(
        database_url,
        # Use a connection pool suitable for a single-process FastAPI app.
        pool_pre_ping=True,   # Detect stale connections before using them.
        pool_size=5,
        max_overflow=10,
        echo=False,           # Do not log SQL; avoid leaking query details.
    )


def _get_engine():  # type: ignore[no-untyped-def]
    """Return the application-level engine, created lazily on first call."""
    settings = get_settings()
    return _build_engine(settings.database_url)


# Session factory — call SessionLocal() to obtain a session.
def _make_session_factory(engine):  # type: ignore[no-untyped-def]
    return sessionmaker(
        bind=engine,
        autocommit=False,
        autoflush=False,
        expire_on_commit=False,
    )


# Module-level singletons, initialised on first import.
_engine = None
_SessionLocal = None


def get_engine():  # type: ignore[no-untyped-def]
    """Return (and lazily create) the shared engine."""
    global _engine  # noqa: PLW0603
    if _engine is None:
        _engine = _get_engine()
    return _engine


def get_session_factory():  # type: ignore[no-untyped-def]
    """Return (and lazily create) the shared session factory."""
    global _SessionLocal  # noqa: PLW0603
    if _SessionLocal is None:
        _SessionLocal = _make_session_factory(get_engine())
    return _SessionLocal


# ── FastAPI dependency ─────────────────────────────────────────────────────


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency that yields a database session.

    Commits on success, rolls back on any exception, always closes.
    """
    SessionLocal = get_session_factory()
    db: Session = SessionLocal()
    try:
        yield db
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        raise
    finally:
        db.close()


# ── Context manager for non-FastAPI callers (e.g., scripts, tests) ─────────


@contextmanager
def session_scope() -> Generator[Session, None, None]:
    """Provide a transactional database session as a context manager."""
    SessionLocal = get_session_factory()
    db: Session = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


# ── Connectivity check ─────────────────────────────────────────────────────


def check_database_connection() -> bool:
    """Return True when PostgreSQL is reachable; False otherwise.

    Connection errors are logged without exposing the connection string.
    """
    try:
        engine = get_engine()
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except OperationalError:
        logger.warning("Database connectivity check failed: connection refused or unavailable.")
        return False
    except Exception:
        logger.warning("Database connectivity check failed: unexpected error.", exc_info=True)
        return False
