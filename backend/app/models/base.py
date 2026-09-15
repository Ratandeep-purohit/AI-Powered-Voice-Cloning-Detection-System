"""Declarative base and shared mixins for all ORM models."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Project-wide declarative base.

    All models inherit from this class so Alembic can discover their
    metadata automatically via ``target_metadata = Base.metadata``.
    """


class TimestampMixin:
    """Adds ``created_at`` and ``updated_at`` columns to a model.

    Both columns are timezone-aware (TIMESTAMPTZ in PostgreSQL).
    ``updated_at`` is set by the application layer on every update;
    a database-level trigger is not required for the MVP.
    """

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )


def new_uuid() -> uuid.UUID:
    """Return a new random UUID (v4)."""
    return uuid.uuid4()
