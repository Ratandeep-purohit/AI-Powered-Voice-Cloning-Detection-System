"""Phase 09 alert endpoints."""
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, require_roles
from app.database import get_db
from app.models.alert import Alert, VALID_ALERT_STATUSES, VALID_SEVERITIES
from app.models.audit_log import AuditLog
from app.models.user import User
from app.schemas.alert import AlertActionsResponse, AlertGenerateResponse, AlertListResponse, AlertPolicyResponse, AlertResponse, AlertTransitionRequest
from app.services.alert_policy_service import ALERT_TYPE, ALERTING_LEVELS, POLICY_VERSION
from app.services.alert_service import STATUS_ACKNOWLEDGED, STATUS_DISMISSED, STATUS_INVESTIGATING, STATUS_RESOLVED, generate_alert, get_alert, get_alert_actions, list_alerts, transition_alert

router = APIRouter(prefix="/alerts", tags=["alerts"])
ALERT_WRITE_ROLES = ("OPERATOR", "SECURITY_ANALYST", "ADMIN", "SUPER_ADMIN")


def _audit_denied(db: Session, user: User, alert_id: UUID, request: Request) -> None:
    db.add(AuditLog(organization_id=user.organization_id, user_id=user.id, event_type="ALERTING", action="ALERT_ACCESS_DENIED", entity_type="ALERT", entity_id=alert_id, event_metadata={"reason": "tenant_or_role_access_denied"}, ip_address=request.client.host if request.client else None))
    db.commit()


@router.get("/policy", response_model=AlertPolicyResponse)
def get_alert_policy(current_user: User = Depends(get_current_user)) -> AlertPolicyResponse:
    return AlertPolicyResponse(policy_version=POLICY_VERSION, alerting_risk_levels=sorted(ALERTING_LEVELS), alert_type=ALERT_TYPE, lifecycle={"OPEN": ["ACKNOWLEDGED", "INVESTIGATING", "RESOLVED", "DISMISSED"], "ACKNOWLEDGED": ["INVESTIGATING", "RESOLVED", "DISMISSED"], "INVESTIGATING": ["RESOLVED", "DISMISSED"], "RESOLVED": [], "DISMISSED": []})


@router.post("/risk/{risk_score_id}", response_model=AlertGenerateResponse, status_code=status.HTTP_201_CREATED)
def create_alert(risk_score_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(require_roles(*ALERT_WRITE_ROLES))) -> AlertGenerateResponse:
    try:
        alert = generate_alert(db, risk_score_id, current_user.organization_id, current_user.id)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from None
    return AlertGenerateResponse(alert=AlertResponse.model_validate(alert) if alert else None, generated=alert is not None)


@router.get("", response_model=AlertListResponse)
def get_alerts(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> AlertListResponse:
    items = list_alerts(db, current_user.organization_id)
    return AlertListResponse(items=[AlertResponse.model_validate(item) for item in items], limit=50, offset=0)


@router.get("/{alert_id}", response_model=AlertResponse)
def get_alert_detail(alert_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> AlertResponse:
    alert = get_alert(db, alert_id, current_user.organization_id)
    if alert is None:
        raise HTTPException(status_code=404, detail="Alert not found")
    return AlertResponse.model_validate(alert)


@router.get("/{alert_id}/actions", response_model=AlertActionsResponse)
def get_alert_history(alert_id: UUID, request: Request, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> AlertActionsResponse:
    try:
        items = get_alert_actions(db, alert_id, current_user.organization_id)
    except LookupError:
        _audit_denied(db, current_user, alert_id, request)
        raise HTTPException(status_code=404, detail="Alert not found") from None
    return AlertActionsResponse(items=items)


@router.post("/{alert_id}/transition", response_model=AlertResponse)
def change_alert_status(alert_id: UUID, payload: AlertTransitionRequest, db: Session = Depends(get_db), current_user: User = Depends(require_roles(*ALERT_WRITE_ROLES))) -> AlertResponse:
    if payload.status not in VALID_ALERT_STATUSES:
        raise HTTPException(status_code=400, detail="Invalid alert status")
    alert = get_alert(db, alert_id, current_user.organization_id)
    if alert is None:
        raise HTTPException(status_code=404, detail="Alert not found")
    try:
        updated = transition_alert(db, alert, payload.status, current_user.id, payload.notes)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from None
    return AlertResponse.model_validate(updated)


@router.post("/{alert_id}/acknowledge", response_model=AlertResponse)
def acknowledge(alert_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(require_roles(*ALERT_WRITE_ROLES))) -> AlertResponse:
    return _transition_short(alert_id, STATUS_ACKNOWLEDGED, db, current_user)


@router.post("/{alert_id}/investigate", response_model=AlertResponse)
def investigate(alert_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(require_roles(*ALERT_WRITE_ROLES))) -> AlertResponse:
    return _transition_short(alert_id, STATUS_INVESTIGATING, db, current_user)


@router.post("/{alert_id}/resolve", response_model=AlertResponse)
def resolve(alert_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(require_roles(*ALERT_WRITE_ROLES))) -> AlertResponse:
    return _transition_short(alert_id, STATUS_RESOLVED, db, current_user)


@router.post("/{alert_id}/dismiss", response_model=AlertResponse)
def dismiss(alert_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(require_roles(*ALERT_WRITE_ROLES))) -> AlertResponse:
    return _transition_short(alert_id, STATUS_DISMISSED, db, current_user)


def _transition_short(alert_id: UUID, new_status: str, db: Session, current_user: User) -> AlertResponse:
    alert = get_alert(db, alert_id, current_user.organization_id)
    if alert is None:
        raise HTTPException(status_code=404, detail="Alert not found")
    try:
        return AlertResponse.model_validate(transition_alert(db, alert, new_status, current_user.id))
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from None
