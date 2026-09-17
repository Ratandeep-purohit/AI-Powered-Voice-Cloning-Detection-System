"""Schemas for the end-to-end voice analysis pipeline."""
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.schemas.alert import AlertResponse
from app.schemas.prevention import PreventionDecisionResponse
from app.schemas.risk import RiskScoreResponse
from app.schemas.voice_analysis import VoiceAnalysisResponse


class PipelineProcessingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    audio_input_id: UUID
    status: str
    processed_sample_rate: int | None
    processed_channels: int | None
    processed_duration_ms: int | None
    processed_size_bytes: int | None
    processed_sha256: str | None
    normalization_applied: bool
    started_at: datetime | None
    completed_at: datetime | None


class AnalysisPipelineResponse(BaseModel):
    session_id: UUID
    audio_input_id: UUID
    processing: PipelineProcessingResponse
    detection: VoiceAnalysisResponse
    decision: str
    detector_threshold: float
    risk: RiskScoreResponse
    prevention: PreventionDecisionResponse
    alert: AlertResponse | None
    completed_at: datetime
