"""User model — identity, authentication data, and RBAC role."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, new_uuid

if TYPE_CHECKING:
    from app.models.alert import Alert
    from app.models.alert_action import AlertAction
    from app.models.audit_log import AuditLog
    from app.models.call import Call
    from app.models.organization import Organization

# Valid RBAC roles — enforced at the database level via CHECK constraint.
VALID_ROLES = ("SUPER_ADMIN", "ADMIN", "SECURITY_ANALYST", "OPERATOR", "AUDITOR")


class User(Base, TimestampMixin):
    """User identity, organisation membership, password hash, and role."""

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=new_uuid,
        nullable=False,
    )
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="RESTRICT"),
        nullable=False,
    )
    email: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)
    full_name: Mapped[str | None] = mapped_column(Text, nullable=True)
    role: Mapped[str] = mapped_column(Text, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    last_login_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # ── Relationships ──────────────────────────────────────────────────────
    organization: Mapped["Organization"] = relationship(
        "Organization", back_populates="users"
    )
    calls: Mapped[list["Call"]] = relationship(
        "Call", back_populates="initiated_by_user", lazy="select"
    )
    alert_actions: Mapped[list["AlertAction"]] = relationship(
        "AlertAction", back_populates="performed_by_user", lazy="select"
    )
    alerts_resolved: Mapped[list["Alert"]] = relationship(
        "Alert", back_populates="resolved_by_user", lazy="select"
    )
    audit_logs: Mapped[list["AuditLog"]] = relationship(
        "AuditLog", back_populates="user", lazy="select"
    )

    # ── Constraints & indexes ──────────────────────────────────────────────
    from sqlalchemy import CheckConstraint

    __table_args__ = (
        CheckConstraint(
            "role IN ('SUPER_ADMIN','ADMIN','SECURITY_ANALYST','OPERATOR','AUDITOR')",
            name="ck_users_role",
        ),
        Index("ix_users_organization_id", "organization_id"),
        Index("ix_users_email", "email", unique=True),
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email!r} role={self.role!r}>"
