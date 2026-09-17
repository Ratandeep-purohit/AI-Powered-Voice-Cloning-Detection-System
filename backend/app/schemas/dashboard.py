"""Phase 10 dashboard API schemas."""
from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field


class DashboardMetric(BaseModel):
    value: int | float
    delta_percent: float | None = None
    caption: str


class DashboardTrendPoint(BaseModel):
    day: date
    calls: int
    alerts: int
    high_risk: int


class DashboardRiskBucket(BaseModel):
    level: str
    count: int
    percentage: float = Field(ge=0, le=100)


class DashboardAlertItem(BaseModel):
    id: UUID
    title: str
    severity: str
    status: str
    risk_score: float | None
    created_at: datetime
    call_id: UUID | None


class DashboardAnalysisItem(BaseModel):
    id: UUID
    call_id: UUID
    model_name: str
    model_version: str | None
    detection_status: str
    synthetic_probability: float | None
    authentic_probability: float | None
    confidence: float | None
    risk_score: float | None
    risk_level: str | None
    analyzed_at: datetime


class DashboardOverviewResponse(BaseModel):
    organization_id: UUID
    organization_name: str
    generated_at: datetime
    metrics: dict[str, DashboardMetric]
    trend: list[DashboardTrendPoint]
    risk_distribution: list[DashboardRiskBucket]
    recent_alerts: list[DashboardAlertItem]
    recent_analyses: list[DashboardAnalysisItem]
    active_alert_count: int
    critical_alert_count: int
    blocked_action_count: int
