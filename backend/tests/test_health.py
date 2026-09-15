"""Phase 00 – Health endpoint tests."""

from __future__ import annotations


def test_health_endpoint_returns_200_or_503(client) -> None:  # type: ignore[no-untyped-def]
    """Health endpoint must respond (200 when DB up, 503 when DB unavailable)."""
    response = client.get("/api/v1/health")
    assert response.status_code in (200, 503)


def test_health_response_contains_status_field(client) -> None:  # type: ignore[no-untyped-def]
    """Health response body must contain a 'status' field."""
    response = client.get("/api/v1/health")
    body = response.json()
    assert "status" in body


def test_health_response_contains_service_field(client) -> None:  # type: ignore[no-untyped-def]
    """Health response must identify the service."""
    response = client.get("/api/v1/health")
    body = response.json()
    assert "service" in body
    assert body["service"] == "voice-cloning-detection-backend"


def test_health_response_does_not_expose_credentials(client) -> None:  # type: ignore[no-untyped-def]
    """Health response body must never contain database passwords."""
    response = client.get("/api/v1/health")
    raw = response.text
    assert "test_pass" not in raw
    assert "voice_password" not in raw


def test_health_database_field_present(client) -> None:  # type: ignore[no-untyped-def]
    """Health response must include a 'database' field."""
    response = client.get("/api/v1/health")
    body = response.json()
    assert "database" in body
