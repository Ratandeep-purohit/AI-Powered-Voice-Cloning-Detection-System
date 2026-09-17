"""Phase 09 alert API schemas."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class AlertResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    organization_id: UUID
    call_id: UUID | None
    risk_score_id: UUID | None
    alert_type: str
    severity: str
    status: str
    title: str
    description: str | None
    resolved_at: datetime | None
    resolved_by_user_id: UUID | None
    created_at: datetime


class AlertActionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    alert_id: UUID
    performed_by_user_id: UUID | None
    action_type: str
    previous_status: str | None
    new_status: str | None
    notes: str | None
    created_at: datetime


class AlertListResponse(BaseModel):
    items: list[AlertResponse]
    limit: int
    offset: int


class AlertActionsResponse(BaseModel):
    items: list[AlertActionResponse]


class AlertGenerateResponse(BaseModel):
    alert: AlertResponse | None
    generated: bool


class AlertTransitionRequest(BaseModel):
    status: str = Field(min_length=1, max_length=32)
    notes: str | None = Field(default=None, max_length=2000)


class AlertPolicyResponse(BaseModel):
    policy_version: str
    alerting_risk_levels: list[str]
    alert_type: str
    lifecycle: dict[str, list[str]]
