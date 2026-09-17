"""Authenticated deterministic policy/prevention endpoints."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.dependencies import require_roles
from app.database import get_db
from app.models.audit_log import AuditLog
from app.models.call import Call
from app.models.risk_score import RiskScore
from app.models.user import User
from app.models.voice_analysis import VoiceAnalysis
from app.schemas.policy import PolicyDecisionResponse
from app.services.policy_prevention import build_policy_prevention_engine

router = APIRouter(prefix="/calls", tags=["policy"])
POLICY_ROLES = ("OPERATOR", "SECURITY_ANALYST", "ADMIN", "SUPER_ADMIN")


def _audit(
    db: Session,
    user: User,
    action: str,
    call_id: UUID,
    request: Request,
    metadata: dict,
) -> None:
    db.add(
        AuditLog(
            organization_id=user.organization_id,
            user_id=user.id,
            event_type="POLICY",
            action=action,
            entity_type="CALL",
            entity_id=call_id,
            event_metadata=metadata,
            ip_address=request.client.host if request.client else None,
        )
    )
    db.commit()


@router.post(
    "/{session_id}/policy/evaluate",
    response_model=PolicyDecisionResponse,
    status_code=status.HTTP_200_OK,
)
def evaluate_call_policy(
    session_id: UUID,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*POLICY_ROLES)),
) -> PolicyDecisionResponse:
    """Evaluate the latest detection/risk evidence using policy-v1."""
    call = db.scalar(
        select(Call).where(
            Call.id == session_id,
            Call.organization_id == current_user.organization_id,
        )
    )
    if call is None:
        raise HTTPException(status_code=404, detail="Analysis session not found")

    risk = db.scalar(
        select(RiskScore)
        .where(RiskScore.call_id == call.id)
        .order_by(RiskScore.calculated_at.desc())
    )
    if risk is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Risk assessment must be available before policy evaluation",
        )

    analysis = None
    if risk.voice_analysis_id:
        analysis = db.scalar(
            select(VoiceAnalysis).where(VoiceAnalysis.id == risk.voice_analysis_id)
        )
    if analysis is None:
        analysis = db.scalar(
            select(VoiceAnalysis)
            .where(VoiceAnalysis.call_id == call.id)
            .order_by(VoiceAnalysis.analyzed_at.desc())
        )

    detection_decision = None
    confidence = None
    if analysis is not None:
        if analysis.synthetic_probability is not None:
            detection_decision = (
                "SPOOF" if float(analysis.synthetic_probability) >= 0.5 else "REAL"
            )
        confidence = float(analysis.confidence) if analysis.confidence is not None else None

    engine = build_policy_prevention_engine("prevention-v1")
    try:
        decision = engine(
            risk_score=float(risk.risk_score),
            risk_level=risk.risk_level,
            detection_decision=detection_decision,
            confidence=confidence,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from None

    metadata = {
        "risk_score_id": str(risk.id),
        "voice_analysis_id": str(analysis.id) if analysis else None,
        "risk_score": decision.risk_score,
        "risk_level": decision.risk_level,
        "detection_decision": decision.detection_decision,
        "action": decision.action.value,
        "policy_version": decision.policy_version,
        "requires_review": decision.requires_review,
        "should_alert": decision.should_alert,
        "should_block": decision.should_block,
    }
    _audit(db, current_user, "POLICY_EVALUATED", call.id, request, metadata)

    return PolicyDecisionResponse(
        call_id=str(call.id),
        risk_score=decision.risk_score,
        risk_level=decision.risk_level,
        detection_decision=decision.detection_decision,
        confidence=decision.confidence,
        action=decision.action.value,
        policy_version=decision.policy_version,
        requires_review=decision.requires_review,
        should_alert=decision.should_alert,
        should_block=decision.should_block,
        explanation=decision.explanation,
    )
