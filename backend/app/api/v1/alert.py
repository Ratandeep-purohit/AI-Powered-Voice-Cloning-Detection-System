"""Phase 09 alert endpoints."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.alert import VALID_ALERT_STATUSES, VALID_SEVERITIES
from app.schemas.alert import (
    AlertActionsResponse,
    AlertGenerateResponse,
    AlertListResponse,
    AlertPolicyResponse,
    AlertResponse,
    AlertTransitionRequest,
)
from app.services.alert_service import (
    POLICY_VERSION,
    STATUS_ACKNOWLEDGED,
    STATUS_DISMISSED,
    STATUS_INVESTIGATING,
    STATUS_RESOLVED,
    assess_risk,
    generate_alert,
    get_alert,
    get_alert_actions,
    list_alerts,
    transition_alert,
)

router = APIRouter(prefix="/alerts", tags=["alerts"])
WRITE_ROLES = {"OPERATOR", "SECURITY_ANALYST", "ADMIN", "SUPER_ADMIN"}


def _org_id(user) -> UUID:
    value = getattr(user, "organization_id", None)
    if value is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Organization membership required")
    return value


def _require_write_role(user) -> None:
    role = getattr(user, "role", None)
    role_value = getattr(role, "value", role)
    if role_value not in WRITE_ROLES:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient role")


@router.get("/policy", response_model=AlertPolicyResponse)
async def get_alert_policy(user=Depends(get_current_user)):
    return AlertPolicyResponse(
        policy_version=POLICY_VERSION,
        alerting_risk_levels=["MEDIUM", "HIGH", "CRITICAL"],
        alert_type="SYNTHETIC_VOICE_RISK",
        lifecycle={
            "OPEN": ["ACKNOWLEDGED", "INVESTIGATING", "RESOLVED", "DISMISSED"],
            "ACKNOWLEDGED": ["INVESTIGATING", "RESOLVED", "DISMISSED"],
            "INVESTIGATING": ["RESOLVED", "DISMISSED"],
            "RESOLVED": [],
            "DISMISSED": [],
        },
    )


@router.post("/risk/{risk_score_id}", response_model=AlertGenerateResponse)
async def generate_alert_for_risk(
    risk_score_id: UUID,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    _require_write_role(user)
    alert = await generate_alert(db, risk_score_id, _org_id(user), getattr(user, "id", None))
    return AlertGenerateResponse(alert=alert, generated=alert is not None)


@router.get("", response_model=AlertListResponse)
async def get_alerts(
    status_filter: str | None = Query(default=None, alias="status"),
    severity: str | None = None,
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    if status_filter and status_filter not in VALID_ALERT_STATUSES:
        raise HTTPException(status_code=400, detail="Invalid alert status")
    if severity and severity not in VALID_SEVERITIES:
        raise HTTPException(status_code=400, detail="Invalid alert severity")
    items = await list_alerts(db, _org_id(user), status_filter, severity, limit, offset)
    return AlertListResponse(items=items, limit=limit, offset=offset)


@router.get("/{alert_id}", response_model=AlertResponse)
async def get_alert_by_id(
    alert_id: UUID,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    alert = await get_alert(db, alert_id, _org_id(user))
    if alert is None:
        raise HTTPException(status_code=404, detail="Alert not found")
    return alert


@router.get("/{alert_id}/actions", response_model=AlertActionsResponse)
async def get_alert_action_history(
    alert_id: UUID,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    try:
        items = await get_alert_actions(db, alert_id, _org_id(user))
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return AlertActionsResponse(items=items)


@router.post("/{alert_id}/transition", response_model=AlertResponse)
async def transition_alert_status(
    alert_id: UUID,
    payload: AlertTransitionRequest,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    _require_write_role(user)
    if payload.status not in VALID_ALERT_STATUSES:
        raise HTTPException(status_code=400, detail="Invalid alert status")
    alert = await get_alert(db, alert_id, _org_id(user))
    if alert is None:
        raise HTTPException(status_code=404, detail="Alert not found")
    try:
        return await transition_alert(db, alert, payload.status, user.id, payload.notes)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post("/{alert_id}/acknowledge", response_model=AlertResponse)
async def acknowledge_alert(alert_id: UUID, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    _require_write_role(user)
    alert = await get_alert(db, alert_id, _org_id(user))
    if alert is None:
        raise HTTPException(status_code=404, detail="Alert not found")
    try:
        return await transition_alert(db, alert, STATUS_ACKNOWLEDGED, user.id)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post("/{alert_id}/investigate", response_model=AlertResponse)
async def investigate_alert(alert_id: UUID, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    _require_write_role(user)
    alert = await get_alert(db, alert_id, _org_id(user))
    if alert is None:
        raise HTTPException(status_code=404, detail="Alert not found")
    try:
        return await transition_alert(db, alert, STATUS_INVESTIGATING, user.id)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post("/{alert_id}/resolve", response_model=AlertResponse)
async def resolve_alert(alert_id: UUID, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    _require_write_role(user)
    alert = await get_alert(db, alert_id, _org_id(user))
    if alert is None:
        raise HTTPException(status_code=404, detail="Alert not found")
    try:
        return await transition_alert(db, alert, STATUS_RESOLVED, user.id)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post("/{alert_id}/dismiss", response_model=AlertResponse)
async def dismiss_alert(alert_id: UUID, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    _require_write_role(user)
    alert = await get_alert(db, alert_id, _org_id(user))
    if alert is None:
        raise HTTPException(status_code=404, detail="Alert not found")
    try:
        return await transition_alert(db, alert, STATUS_DISMISSED, user.id)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
