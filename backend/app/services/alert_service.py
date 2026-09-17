"""Phase 09 alert generation and lifecycle service."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.models.alert import Alert
from app.models.alert_action import AlertAction
from app.models.audit_log import AuditLog
from app.models.risk_score import RiskScore
from app.services.alert_policy_service import ALERT_TYPE, POLICY_VERSION, evaluate_alert_policy

STATUS_OPEN = "OPEN"
STATUS_ACKNOWLEDGED = "ACKNOWLEDGED"
STATUS_INVESTIGATING = "INVESTIGATING"
STATUS_RESOLVED = "RESOLVED"
STATUS_DISMISSED = "DISMISSED"

TRANSITIONS = {
    STATUS_OPEN: {STATUS_ACKNOWLEDGED, STATUS_INVESTIGATING, STATUS_RESOLVED, STATUS_DISMISSED},
    STATUS_ACKNOWLEDGED: {STATUS_INVESTIGATING, STATUS_RESOLVED, STATUS_DISMISSED},
    STATUS_INVESTIGATING: {STATUS_RESOLVED, STATUS_DISMISSED},
    STATUS_RESOLVED: set(),
    STATUS_DISMISSED: set(),
}


@dataclass(frozen=True)
class AlertAssessment:
    should_alert: bool
    severity: str | None
    alert_type: str | None
    title: str | None
    description: str | None


def assess_risk(risk_score: RiskScore) -> AlertAssessment:
    decision = evaluate_alert_policy(risk_score.risk_level, float(risk_score.risk_score))
    return AlertAssessment(decision.should_alert, decision.severity, decision.alert_type, decision.title, decision.description)


def get_risk_score_for_org(db: Session, risk_score_id: UUID, organization_id: UUID) -> RiskScore | None:
    return db.scalar(select(RiskScore).where(RiskScore.id == risk_score_id, RiskScore.call.has(organization_id=organization_id)))


def get_alert(db: Session, alert_id: UUID, organization_id: UUID) -> Alert | None:
    return db.scalar(select(Alert).where(Alert.id == alert_id, Alert.organization_id == organization_id))


def list_alerts(db: Session, organization_id: UUID, status: str | None = None, severity: str | None = None, limit: int = 50, offset: int = 0) -> list[Alert]:
    stmt = select(Alert).where(Alert.organization_id == organization_id)
    if status:
        stmt = stmt.where(Alert.status == status)
    if severity:
        stmt = stmt.where(Alert.severity == severity)
    return list(db.scalars(stmt.order_by(Alert.created_at.desc()).limit(min(limit, 100)).offset(max(offset, 0))).all())


def generate_alert(db: Session, risk_score_id: UUID, organization_id: UUID, user_id: UUID | None = None) -> Alert | None:
    risk_score = get_risk_score_for_org(db, risk_score_id, organization_id)
    if risk_score is None:
        raise LookupError("Risk score not found")
    assessment = assess_risk(risk_score)
    if not assessment.should_alert:
        return None
    existing = db.scalar(select(Alert).where(Alert.organization_id == organization_id, Alert.risk_score_id == risk_score_id, Alert.alert_type == ALERT_TYPE))
    if existing is not None:
        return existing
    alert = Alert(organization_id=organization_id, call_id=risk_score.call_id, risk_score_id=risk_score.id, alert_type=assessment.alert_type, severity=assessment.severity, status=STATUS_OPEN, title=assessment.title, description=assessment.description)
    db.add(alert)
    try:
        db.flush()
        db.add(AlertAction(alert_id=alert.id, performed_by_user_id=user_id, action_type="ALERT_CREATED", previous_status=None, new_status=STATUS_OPEN, notes=f"Alert policy version {POLICY_VERSION}"))
        db.add(AuditLog(organization_id=organization_id, user_id=user_id, event_type="ALERTING", action="ALERT_GENERATED", entity_type="ALERT", entity_id=alert.id, event_metadata={"risk_score_id": str(risk_score.id), "policy_version": POLICY_VERSION}))
        db.commit()
    except SQLAlchemyError as exc:
        db.rollback()
        existing = db.scalar(select(Alert).where(Alert.organization_id == organization_id, Alert.risk_score_id == risk_score_id, Alert.alert_type == ALERT_TYPE))
        if existing is not None:
            return existing
        raise
    db.refresh(alert)
    return alert


def transition_alert(db: Session, alert: Alert, new_status: str, user_id: UUID, notes: str | None = None) -> Alert:
    if new_status not in TRANSITIONS.get(alert.status, set()):
        raise ValueError(f"Invalid alert transition: {alert.status} -> {new_status}")
    previous = alert.status
    alert.status = new_status
    if new_status in {STATUS_RESOLVED, STATUS_DISMISSED}:
        alert.resolved_at = datetime.now(timezone.utc)
        alert.resolved_by_user_id = user_id
    db.add(AlertAction(alert_id=alert.id, performed_by_user_id=user_id, action_type=f"ALERT_{new_status}", previous_status=previous, new_status=new_status, notes=notes))
    db.add(AuditLog(organization_id=alert.organization_id, user_id=user_id, event_type="ALERTING", action="ALERT_STATUS_CHANGED", entity_type="ALERT", entity_id=alert.id, event_metadata={"previous_status": previous, "new_status": new_status}))
    try:
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        raise
    db.refresh(alert)
    return alert


def get_alert_actions(db: Session, alert_id: UUID, organization_id: UUID) -> list[AlertAction]:
    if get_alert(db, alert_id, organization_id) is None:
        raise LookupError("Alert not found")
    return list(db.scalars(select(AlertAction).where(AlertAction.alert_id == alert_id).order_by(AlertAction.created_at.asc())).all())
