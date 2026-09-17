"""Phase 07 prevention decision generation and persistence."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog
from app.models.call import Call
from app.models.prevention_decision import PreventionDecision
from app.models.risk_score import RiskScore
from app.models.user import User
from app.services.response_policy_service import ResponsePolicyError, evaluate_policy


class PreventionServiceError(ValueError):
    """Raised when a prevention decision cannot be safely generated."""


def _validate_risk_score(risk: RiskScore) -> tuple[float, str]:
    try:
        score = float(risk.risk_score)
    except (TypeError, ValueError) as exc:
        raise PreventionServiceError("Risk score is invalid") from exc
    if not 0 <= score <= 100:
        raise PreventionServiceError("Risk score must be between 0 and 100")
    level = risk.risk_level.strip().upper() if isinstance(risk.risk_level, str) else ""
    if level not in {"SAFE", "LOW", "MEDIUM", "HIGH", "CRITICAL"}:
        raise PreventionServiceError("Risk level is invalid")
    return score, level


def get_owned_risk_score(db: Session, user: User, session_id: UUID, risk_score_id: UUID) -> RiskScore | None:
    """Load a risk result only through the authenticated user's tenant."""
    return db.scalar(
        select(RiskScore)
        .join(Call, Call.id == RiskScore.call_id)
        .where(
            RiskScore.id == risk_score_id,
            RiskScore.call_id == session_id,
            Call.organization_id == user.organization_id,
        )
    )


def get_prevention_decision(db: Session, user: User, session_id: UUID, risk_score_id: UUID) -> PreventionDecision | None:
    return db.scalar(
        select(PreventionDecision).where(
            PreventionDecision.risk_score_id == risk_score_id,
            PreventionDecision.call_id == session_id,
            PreventionDecision.organization_id == user.organization_id,
        ).order_by(PreventionDecision.created_at.desc())
    )


def generate_prevention_decision(
    db: Session,
    user: User,
    session_id: UUID,
    risk_score_id: UUID,
    ip_address: str | None = None,
) -> PreventionDecision:
    """Evaluate one completed risk result and persist an idempotent decision."""
    risk = get_owned_risk_score(db, user, session_id, risk_score_id)
    if risk is None:
        raise PreventionServiceError("Risk assessment not found")

    score, level = _validate_risk_score(risk)
    if risk.call_id != session_id:
        raise PreventionServiceError("Risk assessment does not belong to this analysis session")

    try:
        policy = evaluate_policy(level)
    except ResponsePolicyError as exc:
        raise PreventionServiceError(str(exc)) from exc

    existing = db.scalar(
        select(PreventionDecision).where(
            PreventionDecision.risk_score_id == risk.id,
            PreventionDecision.policy_version == policy.policy_version,
            PreventionDecision.organization_id == user.organization_id,
        )
    )
    if existing is not None:
        return existing

    decision = PreventionDecision(
        organization_id=user.organization_id,
        call_id=risk.call_id,
        risk_score_id=risk.id,
        risk_score=score,
        risk_level=level,
        response_action=policy.response_action,
        policy_version=policy.policy_version,
        reason=policy.reason,
    )
    db.add(decision)
    db.flush()

    db.add(AuditLog(
        organization_id=user.organization_id,
        user_id=user.id,
        event_type="PREVENTION",
        action="PREVENTION_DECISION_GENERATED",
        entity_type="PREVENTION_DECISION",
        entity_id=decision.id,
        event_metadata={
            "call_id": str(risk.call_id),
            "risk_score_id": str(risk.id),
            "risk_score": score,
            "risk_level": level,
            "response_action": policy.response_action,
            "policy_version": policy.policy_version,
        },
        ip_address=ip_address,
    ))

    try:
        db.commit()
    except SQLAlchemyError as exc:
        db.rollback()
        raise PreventionServiceError("Prevention decision could not be persisted") from exc

    db.refresh(decision)
    return decision
