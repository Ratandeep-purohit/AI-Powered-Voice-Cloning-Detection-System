"""Schemas for policy and prevention decisions."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class PolicyDecisionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    call_id: str
    risk_score: float = Field(ge=0, le=100)
    risk_level: str
    detection_decision: str | None = None
    confidence: float | None = Field(default=None, ge=0, le=1)
    action: str
    policy_version: str
    requires_review: bool
    should_alert: bool
    should_block: bool
    explanation: str
