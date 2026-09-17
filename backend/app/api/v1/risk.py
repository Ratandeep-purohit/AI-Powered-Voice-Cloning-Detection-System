"""Authenticated Phase 08 risk scoring endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, require_roles
from app.database import get_db
from app.models.audit_log import AuditLog
from app.models.risk_score import RiskScore
from app.models.user import User
from app.schemas.risk import (
    RiskScoreRequestResponse,
    RiskScoreResponse,
    RiskScoringPolicyResponse,
)
from app.services.risk_scoring import (
    POLICY_VERSION,
    RISK_LEVEL_BANDS,
    RiskScoringError,
    generate_risk_score,
    get_existing_risk_score,
)

router = APIRouter(prefix="/risk", tags=["risk"])
RISK_SCORING_ROLES = ("OPERATOR", "SECURITY_ANALYST", "ADMIN", "SUPER_ADMIN")


def _audit_denied(db: Session, user: User, action: str, session_id: UUID, request: Request) -> None:
    db.add(
        AuditLog(
            organization_id=user.organization_id,
            user_id=user.id,
            event_type="RISK_SCORING",
            action=action,
            entity_type="CALL",
            entity_id=session_id,
            event_metadata={"reason": "tenant_or_resource_access_denied"},
            ip_address=request.client.host if request.client else None,
        )
    )
    db.commit()


@router.get("/policy", response_model=RiskScoringPolicyResponse)
async def get_risk_scoring_policy(
    current_user: User = Depends(get_current_user),
) -> RiskScoringPolicyResponse:
    return RiskScoringPolicyResponse(
        policy_version=POLICY_VERSION,
        risk_level_bands={level: f"< {upper:g}" for upper, level in RISK_LEVEL_BANDS[:-1]}
        | {"CRITICAL": "80-100"},
        formula="synthetic_probability * confidence + 0.5 * (1 - confidence)",
    )


@router.post(
    "/calls/{session_id}/analyses/{analysis_id}/score",
    response_model=RiskScoreRequestResponse,
    status_code=status.HTTP_201_CREATED,
)
async def score_analysis(
    session_id: UUID,
    analysis_id: UUID,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*RISK_SCORING_ROLES)),
) -> RiskScoreRequestResponse:
    try:
        risk = generate_risk_score(
            db,
            current_user,
            session_id,
            analysis_id,
            request.client.host if request.client else None,
        )
    except RiskScoringError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from None
    return RiskScoreRequestResponse(risk=RiskScoreResponse.model_validate(risk))


@router.get(
    "/calls/{session_id}/analyses/{analysis_id}/score",
    response_model=RiskScoreResponse,
)
async def get_analysis_score(
    session_id: UUID,
    analysis_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> RiskScoreResponse:
    risk = get_existing_risk_score(db, current_user, session_id, analysis_id)
    if risk is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Risk score not found")
    return RiskScoreResponse.model_validate(risk)
