"""Tenant-scoped in-process WebSocket event manager for Phase 11."""
from __future__ import annotations

import asyncio
import json
import logging
from collections import defaultdict
from datetime import datetime, timezone
from threading import Lock
from typing import Any
from uuid import UUID, uuid4

from fastapi import WebSocket

from app.schemas.realtime import RealtimeEvent, RealtimeEventType

logger = logging.getLogger(__name__)


class RealtimeConnectionManager:
    """Manage authenticated WebSocket connections grouped by organization.

    This is intentionally process-local for the MVP. A future horizontally-scaled
    deployment can replace the manager with Redis/pub-sub without changing the
    event contract or API surface.
    """

    def __init__(self) -> None:
        self._connections: dict[UUID, set[WebSocket]] = defaultdict(set)
        self._lock = Lock()
        self._loop: asyncio.AbstractEventLoop | None = None

    async def connect(self, organization_id: UUID, websocket: WebSocket) -> None:
        await websocket.accept()
        with self._lock:
            self._connections[organization_id].add(websocket)
            self._loop = asyncio.get_running_loop()

    def disconnect(self, organization_id: UUID, websocket: WebSocket) -> None:
        with self._lock:
            connections = self._connections.get(organization_id)
            if not connections:
                return
            connections.discard(websocket)
            if not connections:
                self._connections.pop(organization_id, None)

    async def publish(
        self,
        organization_id: UUID,
        event_type: RealtimeEventType,
        payload: dict[str, Any] | None = None,
        *,
        session_id: UUID | None = None,
    ) -> None:
        event = RealtimeEvent(
            event_id=uuid4(),
            event_type=event_type,
            organization_id=organization_id,
            session_id=session_id,
            occurred_at=datetime.now(timezone.utc),
            payload=payload or {},
        )
        message = event.model_dump(mode="json")
        with self._lock:
            connections = tuple(self._connections.get(organization_id, set()))

        stale: list[WebSocket] = []
        for websocket in connections:
            try:
                await websocket.send_json(message)
            except Exception:
                stale.append(websocket)

        for websocket in stale:
            self.disconnect(organization_id, websocket)

    def publish_sync(
        self,
        organization_id: UUID,
        event_type: RealtimeEventType,
        payload: dict[str, Any] | None = None,
        *,
        session_id: UUID | None = None,
    ) -> None:
        """Schedule an event from a synchronous worker without blocking it."""
        with self._lock:
            loop = self._loop
        if loop is None or loop.is_closed():
            return
        future = asyncio.run_coroutine_threadsafe(
            self.publish(organization_id, event_type, payload, session_id=session_id),
            loop,
        )
        future.add_done_callback(self._log_publish_error)

    @staticmethod
    def _log_publish_error(future: Any) -> None:
        try:
            future.result()
        except Exception:
            logger.exception("Realtime event publication failed")

    async def send_heartbeat(self, organization_id: UUID, websocket: WebSocket) -> None:
        event = RealtimeEvent(
            event_id=uuid4(),
            event_type="heartbeat",
            organization_id=organization_id,
            occurred_at=datetime.now(timezone.utc),
            payload={},
        )
        await websocket.send_json(json.loads(event.model_dump_json()))


realtime_manager = RealtimeConnectionManager()
