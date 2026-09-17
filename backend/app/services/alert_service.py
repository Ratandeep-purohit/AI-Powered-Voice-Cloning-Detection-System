"""Phase 09 alert generation and lifecycle service."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.alert import Alert
from app.models.alert_action import AlertAction
from app.models.audit_log import AuditLog
from app.models.risk_score import RiskScore

POLICY_VERSION = "1.0"

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
    level = risk_score.risk_level
    if level in {"SAFE", "LOW"}:
        return AlertAssessment(False, None, None, None, None)
    severity = level if level in {"MEDIUM", "HIGH", "CRITICAL"} else "HIGH"
    return AlertAssessment(
        True,
        severity,
        "SYNTHETIC_VOICE_RISK",
        f"{severity} synthetic voice risk detected",
        f"Risk score {float(risk_score.risk_score):.2f} reached the {level} policy band.",
    )


async def get_risk_score_for_org(
    session: AsyncSession, risk_score_id: uuid.UUID, organization_id: uuid.UUID
) -> RiskScore | None:
    result = await session.execute(
        select(RiskScore)
        .join(RiskScore.call)
        .where(RiskScore.id == risk_score_id, RiskScore.call.has(organization_id=organization_id))
    )
    return result.scalar_one_or_none()


async def get_alert(
    session: AsyncSession, alert_id: uuid.UUID, organization_id: uuid.UUID
) -> Alert | None:
    result = await session.execute(
        select(Alert).where(Alert.id == alert_id, Alert.organization_id == organization_id)
    )
    return result.scalar_one_or_none()


async def list_alerts(
    session: AsyncSession,
    organization_id: uuid.UUID,
    status: str | None = None,
    severity: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[Alert]:
    stmt = select(Alert).where(Alert.organization_id == organization_id)
    if status:
        stmt = stmt.where(Alert.status == status)
    if severity:
        stmt = stmt.where(Alert.severity == severity)
    result = await session.execute(
        stmt.order_by(Alert.created_at.desc()).limit(min(limit, 100)).offset(max(offset, 0))
    )
    return list(result.scalars().all())


async def generate_alert(
    session: AsyncSession,
    risk_score_id: uuid.UUID,
    organization_id: uuid.UUID,
    user_id: uuid.UUID | None = None,
) -> Alert | None:
    risk_score = await get_risk_score_for_org(session, risk_score_id, organization_id)
    if risk_score is None:
        raise LookupError("Risk score not found")

    existing = await session.execute(
        select(Alert).where(
            Alert.organization_id == organization_id,
            Alert.risk_score_id == risk_score_id,
            Alert.alert_type == "SYNTHETIC_VOICE_RISK",
        )
    )
    alert = existing.scalar_one_or_none()
    if alert is not None:
        return alert

    assessment = assess_risk(risk_score)
    if not assessment.should_alert:
        return None

    alert = Alert(
        organization_id=organization_id,
        call_id=risk_score.call_id,
        risk_score_id=risk_score.id,
        alert_type=assessment.alert_type,
        severity=assessment.severity,
        status=STATUS_OPEN,
        title=assessment.title,
        description=assessment.description,
    )
    session.add(alert)
    await session.flush()
    session.add(
        AlertAction(
            alert_id=alert.id,
            performed_by_user_id=user_id,
            action_type="ALERT_CREATED",
            previous_status=None,
            new_status=STATUS_OPEN,
            notes=f"Alert policy version {POLICY_VERSION}",
        )
    )
    session.add(
        AuditLog(
            organization_id=organization_id,
            user_id=user_id,
            action="ALERT_GENERATED",
            resource_type="ALERT",
            resource_id=str(alert.id),
            details={"risk_score_id": str(risk_score.id), "policy_version": POLICY_VERSION},
        )
    )
    await session.commit()
    await session.refresh(alert)
    return alert


async def transition_alert(
    session: AsyncSession,
    alert: Alert,
    new_status: str,
    user_id: uuid.UUID,
    notes: str | None = None,
) -> Alert:
    allowed = TRANSITIONS.get(alert.status)
    if allowed is None or new_status not in allowed:
        raise ValueError(f"Invalid alert transition: {alert.status} -> {new_status}")

    previous = alert.status
    alert.status = new_status
    if new_status in {STATUS_RESOLVED, STATUS_DISMISSED}:
        alert.resolved_at = datetime.now(timezone.utc)
        alert.resolved_by_user_id = user_id

    session.add(
        AlertAction(
            alert_id=alert.id,
            performed_by_user_id=user_id,
            action_type=f"ALERT_{new_status}",
            previous_status=previous,
            new_status=new_status,
            notes=notes,
        )
    )
    session.add(
        AuditLog(
            organization_id=alert.organization_id,
            user_id=user_id,
            action="ALERT_STATUS_CHANGED",
            resource_type="ALERT",
            resource_id=str(alert.id),
            details={"previous_status": previous, "new_status": new_status},
        )
    )
    try:
        await session.commit()
        await session.refresh(alert)
    except SQLAlchemyError:
        await session.rollback()
        raise
    return alert


async def get_alert_actions(
    session: AsyncSession, alert_id: uuid.UUID, organization_id: uuid.UUID
) -> list[AlertAction]:
    alert = await get_alert(session, alert_id, organization_id)
    if alert is None:
        raise LookupError("Alert not found")
    result = await session.execute(
        select(AlertAction).where(AlertAction.alert_id == alert_id).order_by(AlertAction.created_at.asc())
    )
    return list(result.scalars().all())
