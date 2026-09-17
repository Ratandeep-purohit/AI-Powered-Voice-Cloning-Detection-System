"""Pydantic schemas for Phase 08 risk scoring."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class RiskScoreResponse(BaseModel):
    """Persisted deterministic risk assessment."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    call_id: UUID
    voice_analysis_id: UUID
    risk_score: float = Field(ge=0, le=100)
    risk_level: str
    risk_factors: dict
    policy_version: str
    calculated_at: datetime
    created_at: datetime


class RiskScoreRequestResponse(BaseModel):
    """API response containing the generated risk assessment."""

    risk: RiskScoreResponse


class RiskScoringPolicyResponse(BaseModel):
    """Public read-only representation of the active scoring policy."""

    policy_version: str
    risk_level_bands: dict[str, str]
    formula: str
