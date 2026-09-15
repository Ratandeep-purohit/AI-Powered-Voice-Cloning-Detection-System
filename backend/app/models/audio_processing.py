"""Audio processing job metadata for Phase 04 preprocessing."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, CheckConstraint, DateTime, ForeignKey, Index, Integer, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, new_uuid

if TYPE_CHECKING:
    from app.models.audio_input import AudioInput

VALID_PROCESSING_STATUSES = ("PENDING", "PROCESSING", "COMPLETED", "FAILED")


class AudioProcessingJob(Base):
    """Metadata for one deterministic preprocessing run."""

    __tablename__ = "audio_processing_jobs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid, nullable=False)
    audio_input_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("audio_inputs.id", ondelete="CASCADE"), nullable=False
    )
    status: Mapped[str] = mapped_column(Text, nullable=False, default="PENDING")
    source_sample_rate: Mapped[int | None] = mapped_column(Integer, nullable=True)
    source_channels: Mapped[int | None] = mapped_column(Integer, nullable=True)
    source_duration_ms: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    processed_sample_rate: Mapped[int | None] = mapped_column(Integer, nullable=True)
    processed_channels: Mapped[int | None] = mapped_column(Integer, nullable=True)
    processed_duration_ms: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    processed_storage_key: Mapped[str | None] = mapped_column(Text, nullable=True, unique=True)
    processed_size_bytes: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    processed_sha256: Mapped[str | None] = mapped_column(Text, nullable=True)
    normalization_applied: Mapped[bool] = mapped_column(nullable=False, default=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    audio_input: Mapped["AudioInput"] = relationship("AudioInput", back_populates="processing_jobs")

    __table_args__ = (
        CheckConstraint("status IN ('PENDING','PROCESSING','COMPLETED','FAILED')", name="ck_audio_processing_jobs_status"),
        CheckConstraint("source_sample_rate IS NULL OR source_sample_rate > 0", name="ck_audio_processing_source_rate_positive"),
        CheckConstraint("processed_sample_rate IS NULL OR processed_sample_rate > 0", name="ck_audio_processing_processed_rate_positive"),
        CheckConstraint("source_channels IS NULL OR source_channels > 0", name="ck_audio_processing_source_channels_positive"),
        CheckConstraint("processed_channels IS NULL OR processed_channels > 0", name="ck_audio_processing_processed_channels_positive"),
        CheckConstraint("source_duration_ms IS NULL OR source_duration_ms >= 0", name="ck_audio_processing_source_duration_non_negative"),
        CheckConstraint("processed_duration_ms IS NULL OR processed_duration_ms >= 0", name="ck_audio_processing_processed_duration_non_negative"),
        Index("ix_audio_processing_jobs_audio_input_id", "audio_input_id"),
        Index("ix_audio_processing_jobs_status", "status"),
    )
