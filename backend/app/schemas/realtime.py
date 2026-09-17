"""Schemas for authenticated Phase 11 real-time events."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


RealtimeEventType = Literal[
    "connection.ready",
    "analysis.started",
    "analysis.processing_completed",
    "analysis.detection_completed",
    "analysis.risk_scored",
    "analysis.prevention_decided",
    "alert.created",
    "analysis.completed",
    "analysis.failed",
    "heartbeat",
]


class RealtimeEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    event_id: UUID
    event_type: RealtimeEventType
    organization_id: UUID
    session_id: UUID | None = None
    occurred_at: datetime
    payload: dict[str, Any] = Field(default_factory=dict)
