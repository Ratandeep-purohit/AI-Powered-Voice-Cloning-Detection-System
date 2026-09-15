"""AudioInput model for validated analysis-session uploads."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, CheckConstraint, DateTime, ForeignKey, Index, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, new_uuid

if TYPE_CHECKING:
    from app.models.audio_processing import AudioProcessingJob
    from app.models.call import Call

VALID_INTAKE_STATUSES = ("PENDING", "VALIDATED", "REJECTED", "FAILED")


class AudioInput(Base):
    """Metadata and storage reference for one uploaded audio input.

    Raw audio bytes are kept outside PostgreSQL. The database stores only
    a server-generated storage key and validation metadata.
    """

    __tablename__ = "audio_inputs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid, nullable=False)
    call_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("calls.id", ondelete="CASCADE"), nullable=False
    )
    original_filename: Mapped[str | None] = mapped_column(Text, nullable=True)
    storage_key: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    content_type: Mapped[str] = mapped_column(Text, nullable=False)
    detected_format: Mapped[str] = mapped_column(Text, nullable=False)
    size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    sha256: Mapped[str] = mapped_column(Text, nullable=False)
    intake_status: Mapped[str] = mapped_column(Text, nullable=False, default="PENDING")
    rejection_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    validated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    call: Mapped["Call"] = relationship("Call", back_populates="audio_inputs")
    processing_jobs: Mapped[list["AudioProcessingJob"]] = relationship(
        "AudioProcessingJob", back_populates="audio_input", cascade="all, delete-orphan", lazy="select"
    )

    __table_args__ = (
        CheckConstraint(
            "intake_status IN ('PENDING','VALIDATED','REJECTED','FAILED')",
            name="ck_audio_inputs_intake_status",
        ),
        CheckConstraint("size_bytes > 0", name="ck_audio_inputs_size_positive"),
        Index("ix_audio_inputs_call_id", "call_id"),
        Index("ix_audio_inputs_sha256", "sha256"),
    )

    def __repr__(self) -> str:
        return f"<AudioInput id={self.id} call_id={self.call_id} status={self.intake_status!r}>"
