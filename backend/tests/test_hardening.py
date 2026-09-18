"""Phase 12 security hardening tests."""

from __future__ import annotations


def test_security_headers_are_present(client) -> None:  # type: ignore[no-untyped-def]
    response = client.get("/api/v1/health/live")
    assert response.status_code == 200
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert response.headers["Referrer-Policy"] == "strict-origin-when-cross-origin"
    assert response.headers["Permissions-Policy"] == "camera=(), microphone=(), geolocation=()"
    assert response.headers["Cross-Origin-Opener-Policy"] == "same-origin"
    assert response.headers["Cross-Origin-Resource-Policy"] == "same-origin"
    assert response.headers["Cache-Control"] == "no-store"
    assert response.headers["Content-Security-Policy"] == "default-src 'none'; frame-ancestors 'none'"


def test_request_id_is_returned_and_propagated(client) -> None:  # type: ignore[no-untyped-def]
    response = client.get("/api/v1/health/live")
    request_id = response.headers.get("X-Request-ID")
    assert request_id
    second = client.get("/api/v1/health/live", headers={"X-Request-ID": "phase12-test-request"})
    assert second.headers["X-Request-ID"] == "phase12-test-request"
