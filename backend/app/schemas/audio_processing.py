"""Schemas for Phase 04 audio preprocessing."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class AudioProcessingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    audio_input_id: UUID
    status: str
    source_sample_rate: int | None
    source_channels: int | None
    source_duration_ms: int | None
    processed_sample_rate: int | None
    processed_channels: int | None
    processed_duration_ms: int | None
    processed_size_bytes: int | None
    processed_sha256: str | None
    normalization_applied: bool
    error_message: str | None
    started_at: datetime | None
    completed_at: datetime | None
    created_at: datetime
