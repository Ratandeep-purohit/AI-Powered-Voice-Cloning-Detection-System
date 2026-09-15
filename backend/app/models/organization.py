"""Organization model — tenant root entity."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Index, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, new_uuid

if TYPE_CHECKING:
    from app.models.alert import Alert
    from app.models.audit_log import AuditLog
    from app.models.call import Call
    from app.models.user import User


class Organization(Base, TimestampMixin):
    """Tenant root.  Every user, call, alert, and audit log belongs to one."""

    __tablename__ = "organizations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=new_uuid,
        nullable=False,
    )
    name: Mapped[str] = mapped_column(Text, nullable=False)
    slug: Mapped[str] = mapped_column(Text, nullable=False, unique=True)

    # ── Relationships ──────────────────────────────────────────────────────
    users: Mapped[list["User"]] = relationship(
        "User", back_populates="organization", lazy="select"
    )
    calls: Mapped[list["Call"]] = relationship(
        "Call", back_populates="organization", lazy="select"
    )
    alerts: Mapped[list["Alert"]] = relationship(
        "Alert", back_populates="organization", lazy="select"
    )
    audit_logs: Mapped[list["AuditLog"]] = relationship(
        "AuditLog", back_populates="organization", lazy="select"
    )

    # ── Indexes ────────────────────────────────────────────────────────────
    __table_args__ = (
        Index("ix_organizations_slug", "slug", unique=True),
    )

    def __repr__(self) -> str:
        return f"<Organization id={self.id} slug={self.slug!r}>"
