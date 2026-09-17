"""Authenticated WebSocket endpoint for tenant-scoped security events."""
from __future__ import annotations

import jwt
from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect, WebSocketException, status
from sqlalchemy import select

from app.core.security import decode_access_token
from app.database import SessionLocal
from app.models.user import User
from app.services.realtime import realtime_manager

router = APIRouter(tags=["realtime"])


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

    await realtime_manager.connect(org_id, websocket)
    try:
        await realtime_manager.publish(
            org_id,
            "connection.ready",
            {"user_id": str(user_id), "role": user.role},
        )
        while True:
            message = await websocket.receive_json()
            if message.get("type") == "ping":
                await realtime_manager.send_heartbeat(org_id, websocket)
            elif message.get("type") == "subscribe":
                session_id = message.get("session_id")
                await websocket.send_json(
                    {
                        "event_type": "connection.ready",
                        "organization_id": str(org_id),
                        "payload": {"subscribed_session_id": session_id},
                    }
                )
    except WebSocketDisconnect:
        pass
    finally:
        realtime_manager.disconnect(org_id, websocket)
