"""Call model — audio call, stream, upload, or analysis session metadata."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, CheckConstraint, DateTime, ForeignKey, Index, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, new_uuid

if TYPE_CHECKING:
    from app.models.alert import Alert
    from app.models.audio_input import AudioInput
    from app.models.audio_segment import AudioSegment
    from app.models.organization import Organization
    from app.models.risk_score import RiskScore
    from app.models.user import User
    from app.models.voice_analysis import VoiceAnalysis

VALID_SOURCE_TYPES = ("UPLOAD", "MICROPHONE", "STREAM", "SIMULATED")
VALID_CALL_STATUSES = ("PENDING", "PROCESSING", "COMPLETED", "FAILED", "CANCELLED")


class Call(Base, TimestampMixin):
    """Represents one audio analysis session."""

    __tablename__ = "calls"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid, nullable=False)
    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False)
    initiated_by_user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    source_type: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=False, default="PENDING")
    external_reference: Mapped[str | None] = mapped_column(Text, nullable=True)
    caller_identifier: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    duration_ms: Mapped[int | None] = mapped_column(BigInteger, nullable=True)

    organization: Mapped["Organization"] = relationship("Organization", back_populates="calls")
    initiated_by_user: Mapped["User | None"] = relationship("User", back_populates="calls")
    audio_inputs: Mapped[list["AudioInput"]] = relationship("AudioInput", back_populates="call", cascade="all, delete-orphan", lazy="select")
    audio_segments: Mapped[list["AudioSegment"]] = relationship("AudioSegment", back_populates="call", lazy="select")
    voice_analyses: Mapped[list["VoiceAnalysis"]] = relationship("VoiceAnalysis", back_populates="call", lazy="select")
    risk_scores: Mapped[list["RiskScore"]] = relationship("RiskScore", back_populates="call", lazy="select")
    alerts: Mapped[list["Alert"]] = relationship("Alert", back_populates="call", lazy="select")

    __table_args__ = (
        CheckConstraint("source_type IN ('UPLOAD','MICROPHONE','STREAM','SIMULATED')", name="ck_calls_source_type"),
        CheckConstraint("status IN ('PENDING','PROCESSING','COMPLETED','FAILED','CANCELLED')", name="ck_calls_status"),
        CheckConstraint("duration_ms IS NULL OR duration_ms >= 0", name="ck_calls_duration_ms_non_negative"),
        Index("ix_calls_organization_id", "organization_id"),
        Index("ix_calls_initiated_by_user_id", "initiated_by_user_id"),
        Index("ix_calls_status", "status"),
        Index("ix_calls_created_at", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<Call id={self.id} status={self.status!r}>"
