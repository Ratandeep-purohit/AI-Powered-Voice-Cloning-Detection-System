"""Phase 10 dashboard read model.

The dashboard is a presentation layer over existing tenant-scoped entities.
It never creates, edits, or reinterprets security decisions.
"""
from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.alert import Alert
from app.models.call import Call
from app.models.organization import Organization
from app.models.prevention_decision import PreventionDecision
from app.models.risk_score import RiskScore, VALID_RISK_LEVELS
from app.models.user import User
from app.models.voice_analysis import VoiceAnalysis
from app.schemas.dashboard import (
    DashboardAlertItem,
    DashboardAnalysisItem,
    DashboardMetric,
    DashboardOverviewResponse,
    DashboardRiskBucket,
    DashboardTrendPoint,
)

DETECTOR_THRESHOLD = 0.5977


def _percent_change(current: float, previous: float) -> float | None:
    if previous == 0:
        return None if current == 0 else 100.0
    return round(((current - previous) / previous) * 100.0, 1)


def build_dashboard_overview(db: Session, user: User) -> DashboardOverviewResponse:
    """Build the authenticated tenant's dashboard snapshot in one read operation set."""
    organization = db.scalar(select(Organization).where(Organization.id == user.organization_id))
    organization_name = organization.name if organization else "Organization"

    now = datetime.now(timezone.utc)
    today = now.date()
    start_today = datetime.combine(today, datetime.min.time(), tzinfo=timezone.utc)
    start_7d = start_today - timedelta(days=6)
    start_14d = start_7d - timedelta(days=7)

    def count_calls(start: datetime | None = None, end: datetime | None = None) -> int:
        stmt = select(func.count(Call.id)).where(Call.organization_id == user.organization_id)
        if start:
            stmt = stmt.where(Call.created_at >= start)
        if end:
            stmt = stmt.where(Call.created_at < end)
        return int(db.scalar(stmt) or 0)

    total_calls = count_calls()
    calls_7d = count_calls(start_7d)
    calls_prev_7d = count_calls(start_14d, start_7d)

    completed_analyses = int(db.scalar(
        select(func.count(VoiceAnalysis.id))
        .join(Call, Call.id == VoiceAnalysis.call_id)
        .where(Call.organization_id == user.organization_id, VoiceAnalysis.detection_status == "COMPLETED")
    ) or 0)

    spoof_detections = int(db.scalar(
        select(func.count(VoiceAnalysis.id))
        .join(Call, Call.id == VoiceAnalysis.call_id)
        .where(
            Call.organization_id == user.organization_id,
            VoiceAnalysis.detection_status == "COMPLETED",
            VoiceAnalysis.synthetic_probability >= DETECTOR_THRESHOLD,
        )
    ) or 0)

    avg_risk_raw = db.scalar(
        select(func.avg(RiskScore.risk_score))
        .join(Call, Call.id == RiskScore.call_id)
        .where(Call.organization_id == user.organization_id)
    )
    avg_risk = round(float(avg_risk_raw or 0), 1)

    active_alert_count = int(db.scalar(
        select(func.count(Alert.id)).where(
            Alert.organization_id == user.organization_id,
            Alert.status.in_(("OPEN", "ACKNOWLEDGED", "INVESTIGATING")),
        )
    ) or 0)
    critical_alert_count = int(db.scalar(
        select(func.count(Alert.id)).where(
            Alert.organization_id == user.organization_id,
            Alert.severity == "CRITICAL",
            Alert.status.in_(("OPEN", "ACKNOWLEDGED", "INVESTIGATING")),
        )
    ) or 0)
    blocked_action_count = int(db.scalar(
        select(func.count(PreventionDecision.id)).where(
            PreventionDecision.organization_id == user.organization_id,
            PreventionDecision.response_action == "BLOCK",
        )
    ) or 0)

    metrics = {
        "calls": DashboardMetric(
            value=calls_7d,
            delta_percent=_percent_change(calls_7d, calls_prev_7d),
            caption="analysis sessions · last 7 days",
        ),
        "analyses": DashboardMetric(
            value=completed_analyses,
            delta_percent=None,
            caption="completed detector runs",
        ),
        "spoof_detections": DashboardMetric(
            value=spoof_detections,
            delta_percent=None,
            caption="above active detector threshold",
        ),
        "average_risk": DashboardMetric(
            value=avg_risk,
            delta_percent=None,
            caption="mean deterministic risk score",
        ),
        "active_alerts": DashboardMetric(
            value=active_alert_count,
            delta_percent=None,
            caption="open, acknowledged or investigating",
        ),
        "blocked_actions": DashboardMetric(
            value=blocked_action_count,
            delta_percent=None,
            caption="policy BLOCK outcomes",
        ),
    }

    # Seven calendar buckets, including empty days, make the chart stable.
    trend_rows = db.execute(
        select(
            func.date(Call.created_at).label("day"),
            func.count(Call.id).label("calls"),
        )
        .where(Call.organization_id == user.organization_id, Call.created_at >= start_7d)
        .group_by(func.date(Call.created_at))
    ).all()
    trend_map = {row.day: int(row.calls) for row in trend_rows}

    alert_rows = db.execute(
        select(func.date(Alert.created_at).label("day"), func.count(Alert.id).label("alerts"))
        .where(Alert.organization_id == user.organization_id, Alert.created_at >= start_7d)
        .group_by(func.date(Alert.created_at))
    ).all()
    alert_map = {row.day: int(row.alerts) for row in alert_rows}

    high_risk_rows = db.execute(
        select(func.date(RiskScore.created_at).label("day"), func.count(RiskScore.id).label("high_risk"))
        .where(
            RiskScore.call.has(organization_id=user.organization_id),
            RiskScore.created_at >= start_7d,
            RiskScore.risk_level.in_(("HIGH", "CRITICAL")),
        )
        .group_by(func.date(RiskScore.created_at))
    ).all()
    high_risk_map = {row.day: int(row.high_risk) for row in high_risk_rows}

    trend = [
        DashboardTrendPoint(
            day=start_7d.date() + timedelta(days=index),
            calls=trend_map.get(start_7d.date() + timedelta(days=index), 0),
            alerts=alert_map.get(start_7d.date() + timedelta(days=index), 0),
            high_risk=high_risk_map.get(start_7d.date() + timedelta(days=index), 0),
        )
        for index in range(7)
    ]

    distribution_rows = db.execute(
        select(RiskScore.risk_level, func.count(RiskScore.id))
        .where(RiskScore.call.has(organization_id=user.organization_id))
        .group_by(RiskScore.risk_level)
    ).all()
    distribution_map = {level: int(count) for level, count in distribution_rows}
    total_risks = sum(distribution_map.values())
    risk_distribution = [
        DashboardRiskBucket(
            level=level,
            count=distribution_map.get(level, 0),
            percentage=round((distribution_map.get(level, 0) / total_risks) * 100, 1) if total_risks else 0,
        )
        for level in VALID_RISK_LEVELS
    ]

    recent_alert_rows = db.execute(
        select(Alert, RiskScore.risk_score)
        .outerjoin(RiskScore, RiskScore.id == Alert.risk_score_id)
        .where(Alert.organization_id == user.organization_id)
        .order_by(Alert.created_at.desc())
        .limit(6)
    ).all()
    recent_alerts = [
        DashboardAlertItem(
            id=alert.id,
            title=alert.title,
            severity=alert.severity,
            status=alert.status,
            risk_score=float(risk_score) if risk_score is not None else None,
            created_at=alert.created_at,
            call_id=alert.call_id,
        )
        for alert, risk_score in recent_alert_rows
    ]

    recent_analysis_rows = db.execute(
        select(VoiceAnalysis, RiskScore.risk_score, RiskScore.risk_level)
        .join(Call, Call.id == VoiceAnalysis.call_id)
        .outerjoin(RiskScore, RiskScore.voice_analysis_id == VoiceAnalysis.id)
        .where(Call.organization_id == user.organization_id)
        .order_by(VoiceAnalysis.analyzed_at.desc())
        .limit(8)
    ).all()
    recent_analyses = [
        DashboardAnalysisItem(
            id=analysis.id,
            call_id=analysis.call_id,
            model_name=analysis.model_name,
            model_version=analysis.model_version,
            detection_status=analysis.detection_status,
            synthetic_probability=float(analysis.synthetic_probability) if analysis.synthetic_probability is not None else None,
            authentic_probability=float(analysis.authentic_probability) if analysis.authentic_probability is not None else None,
            confidence=float(analysis.confidence) if analysis.confidence is not None else None,
            risk_score=float(risk_score) if risk_score is not None else None,
            risk_level=risk_level,
            analyzed_at=analysis.analyzed_at,
        )
        for analysis, risk_score, risk_level in recent_analysis_rows
    ]

    return DashboardOverviewResponse(
        organization_id=user.organization_id,
        organization_name=organization_name,
        generated_at=now,
        metrics=metrics,
        trend=trend,
        risk_distribution=risk_distribution,
        recent_alerts=recent_alerts,
        recent_analyses=recent_analyses,
        active_alert_count=active_alert_count,
        critical_alert_count=critical_alert_count,
        blocked_action_count=blocked_action_count,
    )
