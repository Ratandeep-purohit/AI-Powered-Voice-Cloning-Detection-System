"""RiskScore model — deterministic security risk assessment results."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Numeric, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, new_uuid

if TYPE_CHECKING:
    from app.models.alert import Alert
    from app.models.call import Call
    from app.models.voice_analysis import VoiceAnalysis

VALID_RISK_LEVELS = ("SAFE", "LOW", "MEDIUM", "HIGH", "CRITICAL")


class RiskScore(Base):
    """Deterministic risk assessment.  Must never be set directly by an LLM."""

    __tablename__ = "risk_scores"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=new_uuid, nullable=False
    )
    call_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("calls.id", ondelete="CASCADE"),
        nullable=False,
    )
    voice_analysis_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("voice_analyses.id", ondelete="SET NULL"),
        nullable=True,
    )

    # 0–100 deterministic score
    risk_score: Mapped[float] = mapped_column(Numeric, nullable=False)
    risk_level: Mapped[str] = mapped_column(Text, nullable=False)

    # JSONB stores the normalised contributing factors
    risk_factors: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    policy_version: Mapped[str | None] = mapped_column(Text, nullable=True)

    calculated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    # ── Relationships ──────────────────────────────────────────────────────
    call: Mapped["Call"] = relationship("Call", back_populates="risk_scores")
    voice_analysis: Mapped["VoiceAnalysis | None"] = relationship(
        "VoiceAnalysis", back_populates="risk_scores"
    )
    alerts: Mapped[list["Alert"]] = relationship(
        "Alert", back_populates="risk_score", lazy="select"
    )

    # ── Constraints & indexes ──────────────────────────────────────────────
    __table_args__ = (
        CheckConstraint(
            "risk_score >= 0 AND risk_score <= 100",
            name="ck_risk_scores_score_range",
        ),
        CheckConstraint(
            "risk_level IN ('SAFE','LOW','MEDIUM','HIGH','CRITICAL')",
            name="ck_risk_scores_risk_level",
        ),
        Index("ix_risk_scores_call_id", "call_id"),
        Index("ix_risk_scores_risk_level", "risk_level"),
    )

    def __repr__(self) -> str:
        return (
            f"<RiskScore id={self.id} score={self.risk_score} level={self.risk_level!r}>"
        )
