from __future__ import annotations

from uuid import uuid4

import pytest

from app.services.realtime import RealtimeConnectionManager


class FakeWebSocket:
    def __init__(self) -> None:
        self.accepted = False
        self.messages: list[dict] = []

    async def accept(self) -> None:
        self.accepted = True

    async def send_json(self, message: dict) -> None:
        self.messages.append(message)


@pytest.mark.asyncio
async def test_realtime_events_are_tenant_scoped() -> None:
    manager = RealtimeConnectionManager()
    org_a = uuid4()
    org_b = uuid4()
    socket_a = FakeWebSocket()
    socket_b = FakeWebSocket()

    await manager.connect(org_a, socket_a)  # type: ignore[arg-type]
    await manager.connect(org_b, socket_b)  # type: ignore[arg-type]
    await manager.publish(org_a, "alert.created", {"alert_id": "a1"})

    assert socket_a.accepted is True
    assert len(socket_a.messages) == 1
    assert socket_a.messages[0]["event_type"] == "alert.created"
    assert socket_a.messages[0]["organization_id"] == str(org_a)
    assert socket_b.messages == []


@pytest.mark.asyncio
async def test_realtime_disconnect_stops_delivery() -> None:
    manager = RealtimeConnectionManager()
    org_id = uuid4()
    socket = FakeWebSocket()

    await manager.connect(org_id, socket)  # type: ignore[arg-type]
    manager.disconnect(org_id, socket)  # type: ignore[arg-type]
    await manager.publish(org_id, "analysis.completed", {"analysis_id": "x"})

    assert socket.messages == []
