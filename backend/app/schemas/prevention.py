"""Pydantic schemas for Phase 07 prevention decisions."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class PreventionDecisionResponse(BaseModel):
    """Persisted deterministic prevention decision."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    organization_id: UUID
    call_id: UUID
    risk_score_id: UUID
    risk_score: float
    risk_level: str
    response_action: str
    policy_version: str
    reason: str
    created_at: datetime


class PreventionRequestResponse(BaseModel):
    """API response containing the evaluated prevention decision."""

    decision: PreventionDecisionResponse


class PreventionPolicyResponse(BaseModel):
    """Public read-only representation of the active deterministic policy."""

    policy_version: str = Field(min_length=1)
    risk_to_response: dict[str, str]
