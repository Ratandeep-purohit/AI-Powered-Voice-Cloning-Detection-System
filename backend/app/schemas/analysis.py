"""Pydantic schemas for analysis sessions and audio intake."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class AnalysisSessionCreate(BaseModel):
    """Optional metadata supplied when starting an analysis session."""

    external_reference: str | None = Field(default=None, max_length=255)
    caller_identifier: str | None = Field(default=None, max_length=255)


class AudioInputResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    original_filename: str | None
    content_type: str
    detected_format: str
    size_bytes: int
    sha256: str
    intake_status: str
    rejection_reason: str | None
    created_at: datetime
    validated_at: datetime | None


class AnalysisSessionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    organization_id: UUID
    initiated_by_user_id: UUID | None
    source_type: str
    status: str
    external_reference: str | None
    caller_identifier: str | None
    created_at: datetime
    updated_at: datetime
    audio_inputs: list[AudioInputResponse] = Field(default_factory=list)
