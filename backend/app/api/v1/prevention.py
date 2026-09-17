"""Authenticated Phase 07 prevention and response endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, require_roles
from app.database import get_db
from app.models.audit_log import AuditLog
from app.models.user import User
from app.schemas.prevention import PreventionPolicyResponse, PreventionRequestResponse
from app.services.prevention_service import (
    PreventionServiceError,
    generate_prevention_decision,
    get_owned_risk_score,
    get_prevention_decision,
)
from app.services.response_policy_service import POLICY_VERSION, RISK_TO_RESPONSE

router = APIRouter(prefix="/prevention", tags=["prevention"])
PREVENTION_ROLES = ("OPERATOR", "SECURITY_ANALYST", "ADMIN", "SUPER_ADMIN")


def _audit_denied(db: Session, user: User, session_id: UUID, risk_score_id: UUID, request: Request) -> None:
    db.add(AuditLog(
        organization_id=user.organization_id,
        user_id=user.id,
        event_type="PREVENTION",
        action="PREVENTION_ACCESS_DENIED",
        entity_type="RISK_SCORE",
        entity_id=risk_score_id,
        event_metadata={"session_id": str(session_id)},
        ip_address=request.client.host if request.client else None,
    ))
    db.commit()


@router.get("/policy", response_model=PreventionPolicyResponse)
def get_active_policy(current_user: User = Depends(get_current_user)) -> PreventionPolicyResponse:
    """Return the active policy definition without exposing internal configuration."""
    return PreventionPolicyResponse(
        policy_version=POLICY_VERSION,
        risk_to_response=dict(RISK_TO_RESPONSE),
    )


@router.post(
    "/calls/{session_id}/risk/{risk_score_id}",
    response_model=PreventionRequestResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_prevention_decision(
    session_id: UUID,
    risk_score_id: UUID,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*PREVENTION_ROLES)),
) -> PreventionRequestResponse:
    """Evaluate and persist a prevention decision for one completed risk result."""
    risk = get_owned_risk_score(db, current_user, session_id, risk_score_id)
    if risk is None:
        _audit_denied(db, current_user, session_id, risk_score_id, request)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Risk assessment not found")

    try:
        decision = generate_prevention_decision(
            db,
            current_user,
            session_id,
            risk_score_id,
            ip_address=request.client.host if request.client else None,
        )
    except PreventionServiceError as exc:
        message = str(exc)
        code = status.HTTP_422_UNPROCESSABLE_ENTITY
        if "not found" in message.lower():
            code = status.HTTP_404_NOT_FOUND
        elif "could not be persisted" in message.lower():
            code = status.HTTP_500_INTERNAL_SERVER_ERROR
        raise HTTPException(status_code=code, detail=message) from None

    return PreventionRequestResponse(decision=decision)


@router.get(
    "/calls/{session_id}/risk/{risk_score_id}",
    response_model=PreventionRequestResponse,
)
def retrieve_prevention_decision(
    session_id: UUID,
    risk_score_id: UUID,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PreventionRequestResponse:
    """Retrieve a previously generated decision within the authenticated tenant."""
    risk = get_owned_risk_score(db, current_user, session_id, risk_score_id)
    if risk is None:
        _audit_denied(db, current_user, session_id, risk_score_id, request)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Risk assessment not found")

    decision = get_prevention_decision(db, current_user, session_id, risk_score_id)
    if decision is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prevention decision not found")
    return PreventionRequestResponse(decision=decision)
