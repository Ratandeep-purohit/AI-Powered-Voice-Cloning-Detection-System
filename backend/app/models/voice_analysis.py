"""VoiceAnalysis model — model-agnostic ML analysis results."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, CheckConstraint, DateTime, ForeignKey, Index, Numeric, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, new_uuid

if TYPE_CHECKING:
    from app.models.audio_segment import AudioSegment
    from app.models.call import Call
    from app.models.risk_score import RiskScore

VALID_DETECTION_STATUSES = (
    "PENDING", "PROCESSING", "COMPLETED", "FAILED",
    "LOW_CONFIDENCE", "UNSUPPORTED",
)


class VoiceAnalysis(Base):
    """ML model output for one call or audio segment."""

    __tablename__ = "voice_analyses"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=new_uuid, nullable=False
    )
    call_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("calls.id", ondelete="CASCADE"),
        nullable=False,
    )
    audio_segment_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("audio_segments.id", ondelete="SET NULL"),
        nullable=True,
    )
    model_name: Mapped[str] = mapped_column(Text, nullable=False)
    model_version: Mapped[str | None] = mapped_column(Text, nullable=True)
    detection_status: Mapped[str] = mapped_column(
        Text, nullable=False, default="PENDING"
    )

    # Nullable — not all models return calibrated probability values.
    synthetic_score: Mapped[float | None] = mapped_column(Numeric, nullable=True)
    synthetic_probability: Mapped[float | None] = mapped_column(Numeric, nullable=True)
    authentic_probability: Mapped[float | None] = mapped_column(Numeric, nullable=True)
    confidence: Mapped[float | None] = mapped_column(Numeric, nullable=True)

    processing_time_ms: Mapped[int | None] = mapped_column(BigInteger, nullable=True)

    analyzed_at: Mapped[datetime] = mapped_column(
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
    call: Mapped["Call"] = relationship("Call", back_populates="voice_analyses")
    audio_segment: Mapped["AudioSegment | None"] = relationship(
        "AudioSegment", back_populates="voice_analyses"
    )
    risk_scores: Mapped[list["RiskScore"]] = relationship(
        "RiskScore", back_populates="voice_analysis", lazy="select"
    )

    # ── Constraints & indexes ──────────────────────────────────────────────
    __table_args__ = (
        CheckConstraint(
            "detection_status IN ('PENDING','PROCESSING','COMPLETED','FAILED','LOW_CONFIDENCE','UNSUPPORTED')",
            name="ck_voice_analyses_detection_status",
        ),
        CheckConstraint(
            "processing_time_ms IS NULL OR processing_time_ms >= 0",
            name="ck_voice_analyses_processing_time_non_negative",
        ),
        Index("ix_voice_analyses_call_id", "call_id"),
        Index("ix_voice_analyses_audio_segment_id", "audio_segment_id"),
    )

    def __repr__(self) -> str:
        return (
            f"<VoiceAnalysis id={self.id} model={self.model_name!r} "
            f"status={self.detection_status!r}>"
        )
