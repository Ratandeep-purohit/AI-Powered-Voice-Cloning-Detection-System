"""AudioSegment model — logical analysis chunks; no raw audio stored here."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, new_uuid

if TYPE_CHECKING:
    from app.models.call import Call
    from app.models.voice_analysis import VoiceAnalysis

VALID_PROCESSING_STATUSES = ("PENDING", "PROCESSING", "COMPLETED", "FAILED", "SKIPPED")


class AudioSegment(Base):
    """One logical chunk of a call.  Raw audio bytes are never stored here."""

    __tablename__ = "audio_segments"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=new_uuid, nullable=False
    )
    call_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("calls.id", ondelete="CASCADE"),
        nullable=False,
    )
    sequence_number: Mapped[int] = mapped_column(Integer, nullable=False)
    start_offset_ms: Mapped[int] = mapped_column(BigInteger, nullable=False)
    end_offset_ms: Mapped[int] = mapped_column(BigInteger, nullable=False)
    duration_ms: Mapped[int] = mapped_column(BigInteger, nullable=False)
    speech_detected: Mapped[bool] = mapped_column(Boolean, nullable=False)
    processing_status: Mapped[str] = mapped_column(
        Text, nullable=False, default="PENDING"
    )

    # created_at only — segments are not updated after creation
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    # ── Relationships ──────────────────────────────────────────────────────
    call: Mapped["Call"] = relationship("Call", back_populates="audio_segments")
    voice_analyses: Mapped[list["VoiceAnalysis"]] = relationship(
        "VoiceAnalysis", back_populates="audio_segment", lazy="select"
    )

    # ── Constraints & indexes ──────────────────────────────────────────────
    __table_args__ = (
        UniqueConstraint("call_id", "sequence_number", name="uq_audio_segments_call_seq"),
        CheckConstraint(
            "processing_status IN ('PENDING','PROCESSING','COMPLETED','FAILED','SKIPPED')",
            name="ck_audio_segments_processing_status",
        ),
        CheckConstraint(
            "sequence_number >= 0",
            name="ck_audio_segments_sequence_number_non_negative",
        ),
        CheckConstraint(
            "start_offset_ms >= 0",
            name="ck_audio_segments_start_offset_non_negative",
        ),
        CheckConstraint(
            "end_offset_ms >= 0",
            name="ck_audio_segments_end_offset_non_negative",
        ),
        CheckConstraint(
            "duration_ms >= 0",
            name="ck_audio_segments_duration_non_negative",
        ),
        Index("ix_audio_segments_call_id", "call_id"),
        Index("ix_audio_segments_call_id_sequence", "call_id", "sequence_number"),
    )

    def __repr__(self) -> str:
        return (
            f"<AudioSegment id={self.id} call_id={self.call_id} seq={self.sequence_number}>"
        )
