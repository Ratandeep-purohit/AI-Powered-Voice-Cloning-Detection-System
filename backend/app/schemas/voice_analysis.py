"""Pydantic schemas for detector inference results."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class VoiceAnalysisResponse(BaseModel):
    """Persisted ML detector result exposed by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    call_id: UUID
    audio_segment_id: UUID | None
    model_name: str
    model_version: str | None
    detection_status: str
    synthetic_score: float | None
    synthetic_probability: float | None
    authentic_probability: float | None
    confidence: float | None
    processing_time_ms: int | None
    analyzed_at: datetime
    created_at: datetime


class DetectionResponse(BaseModel):
    """Immediate response returned after synchronous detector inference."""

    analysis: VoiceAnalysisResponse
    decision: str
    threshold: float
