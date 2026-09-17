"""Authenticated WebSocket and live-analysis endpoints for Phase 11."""
from __future__ import annotations

import jwt
from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect, WebSocketException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.dependencies import require_roles
from app.core.security import decode_access_token
from app.database import SessionLocal, get_db
from app.models.user import User
from app.schemas.analysis_pipeline import AnalysisPipelineResponse
from app.services.analysis_pipeline import AnalysisPipelineError, run_analysis_pipeline
from app.services.realtime import realtime_manager

router = APIRouter(tags=["realtime"])
ANALYSIS_ROLES = ("OPERATOR", "SECURITY_ANALYST", "ADMIN", "SUPER_ADMIN")


@router.websocket("/realtime/ws")
async def realtime_websocket(websocket: WebSocket, token: str | None = Query(default=None)) -> None:
    """Stream authenticated, organization-scoped security events."""
    if not token:
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION, reason="Authentication required")

    try:
        payload = decode_access_token(token)
        user_id = payload["sub"]
        organization_id = payload["org"]
    except (KeyError, ValueError, jwt.PyJWTError):
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION, reason="Invalid or expired token") from None

    with SessionLocal() as db:
        user = db.scalar(
            select(User).where(User.id == user_id, User.organization_id == organization_id, User.is_active.is_(True))
        )
        if user is None:
            raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION, reason="Invalid or inactive account")
        org_id = user.organization_id
        role = user.role

    await realtime_manager.connect(org_id, websocket)
    try:
        await realtime_manager.publish(org_id, "connection.ready", {"user_id": str(user_id), "role": role})
        while True:
            message = await websocket.receive_json()
            if message.get("type") == "ping":
                await realtime_manager.send_heartbeat(org_id, websocket)
            elif message.get("type") == "subscribe":
                await websocket.send_json({
                    "event_type": "connection.ready",
                    "organization_id": str(org_id),
                    "payload": {"subscribed_session_id": message.get("session_id")},
                })
    except WebSocketDisconnect:
        pass
    finally:
        realtime_manager.disconnect(org_id, websocket)


@router.post("/calls/{session_id}/audio/{audio_input_id}/analyze-realtime", response_model=AnalysisPipelineResponse)
def analyze_audio_realtime(
    session_id: str,
    audio_input_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*ANALYSIS_ROLES)),
) -> AnalysisPipelineResponse:
    """Run the full analysis pipeline while publishing stage events to WebSocket clients."""
    from uuid import UUID

    session_uuid = UUID(session_id)
    audio_uuid = UUID(audio_input_id)

    def publish(event_type: str, payload: dict) -> None:
        realtime_manager.publish_sync(
            current_user.organization_id,
            event_type,  # type: ignore[arg-type]
            payload,
            session_id=session_uuid,
        )

    try:
        return run_analysis_pipeline(
            db,
            current_user,
            session_uuid,
            audio_uuid,
            event_callback=publish,
        )
    except (ValueError, AnalysisPipelineError) as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from None
