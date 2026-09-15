"""Alert model — policy-driven security alert."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, new_uuid

if TYPE_CHECKING:
    from app.models.alert_action import AlertAction
    from app.models.call import Call
    from app.models.organization import Organization
    from app.models.risk_score import RiskScore
    from app.models.user import User

VALID_ALERT_STATUSES = (
    "OPEN", "ACKNOWLEDGED", "INVESTIGATING", "RESOLVED", "DISMISSED"
)
VALID_SEVERITIES = ("LOW", "MEDIUM", "HIGH", "CRITICAL")


class Alert(Base, TimestampMixin):
    """Security alert raised from risk and policy evaluation."""

    __tablename__ = "alerts"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=new_uuid, nullable=False
    )
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="RESTRICT"),
        nullable=False,
    )
    call_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("calls.id", ondelete="SET NULL"),
        nullable=True,
    )
    risk_score_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("risk_scores.id", ondelete="SET NULL"),
        nullable=True,
    )
    alert_type: Mapped[str] = mapped_column(Text, nullable=False)
    severity: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=False, default="OPEN")
    title: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    resolved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    resolved_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    # ── Relationships ──────────────────────────────────────────────────────
    organization: Mapped["Organization"] = relationship(
        "Organization", back_populates="alerts"
    )
    call: Mapped["Call | None"] = relationship("Call", back_populates="alerts")
    risk_score: Mapped["RiskScore | None"] = relationship(
        "RiskScore", back_populates="alerts"
    )
    resolved_by_user: Mapped["User | None"] = relationship(
        "User", back_populates="alerts_resolved"
    )
    actions: Mapped[list["AlertAction"]] = relationship(
        "AlertAction", back_populates="alert", lazy="select"
    )

    # ── Constraints & indexes ──────────────────────────────────────────────
    __table_args__ = (
        CheckConstraint(
            "status IN ('OPEN','ACKNOWLEDGED','INVESTIGATING','RESOLVED','DISMISSED')",
            name="ck_alerts_status",
        ),
        CheckConstraint(
            "severity IN ('LOW','MEDIUM','HIGH','CRITICAL')",
            name="ck_alerts_severity",
        ),
        Index("ix_alerts_organization_id", "organization_id"),
        Index("ix_alerts_status", "status"),
        Index("ix_alerts_severity", "severity"),
    )

    def __repr__(self) -> str:
        return (
            f"<Alert id={self.id} severity={self.severity!r} status={self.status!r}>"
        )
