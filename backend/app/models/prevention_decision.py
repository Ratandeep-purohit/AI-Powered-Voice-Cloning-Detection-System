"""PreventionDecision model — immutable policy evaluation result."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Numeric, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, new_uuid

if TYPE_CHECKING:
    from app.models.call import Call
    from app.models.risk_score import RiskScore
    from app.models.organization import Organization

VALID_RESPONSE_ACTIONS = (
    "ALLOW", "MONITOR", "FLAG", "REQUIRE_REVIEW", "RESTRICT", "BLOCK"
)


class PreventionDecision(Base):
    """Immutable, organization-scoped response decision for one risk result."""

    __tablename__ = "prevention_decisions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid, nullable=False)
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False
    )
    call_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("calls.id", ondelete="CASCADE"), nullable=False
    )
    risk_score_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("risk_scores.id", ondelete="CASCADE"), nullable=False
    )
    risk_score: Mapped[float] = mapped_column(Numeric, nullable=False)
    risk_level: Mapped[str] = mapped_column(Text, nullable=False)
    response_action: Mapped[str] = mapped_column(Text, nullable=False)
    policy_version: Mapped[str] = mapped_column(Text, nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    organization: Mapped["Organization"] = relationship("Organization")
    call: Mapped["Call"] = relationship("Call", back_populates="prevention_decisions")
    risk_score_record: Mapped["RiskScore"] = relationship("RiskScore")

    __table_args__ = (
        CheckConstraint("risk_score >= 0 AND risk_score <= 100", name="ck_prevention_decisions_score_range"),
        CheckConstraint(
            "risk_level IN ('SAFE','LOW','MEDIUM','HIGH','CRITICAL')",
            name="ck_prevention_decisions_risk_level",
        ),
        CheckConstraint(
            "response_action IN ('ALLOW','MONITOR','FLAG','REQUIRE_REVIEW','RESTRICT','BLOCK')",
            name="ck_prevention_decisions_action",
        ),
        UniqueConstraint("risk_score_id", "policy_version", name="uq_prevention_decision_risk_policy"),
        Index("ix_prevention_decisions_organization_id", "organization_id"),
        Index("ix_prevention_decisions_call_id", "call_id"),
        Index("ix_prevention_decisions_response_action", "response_action"),
        Index("ix_prevention_decisions_created_at", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<PreventionDecision id={self.id} action={self.response_action!r} level={self.risk_level!r}>"
