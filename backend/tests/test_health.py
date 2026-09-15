from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app


def test_application_starts() -> None:
    assert app.title == "Voice Cloning Detection System"


def test_health_when_database_is_available() -> None:
    with patch("app.api.v1.health.check_database_connection", return_value=True):
        client = TestClient(app)
        response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "healthy",
        "service": "api",
        "database": "connected",
    }


def test_health_when_database_is_unavailable() -> None:
    with patch("app.api.v1.health.check_database_connection", return_value=False):
        client = TestClient(app)
        response = client.get("/api/v1/health")

    assert response.status_code == 503
    assert response.json()["status"] == "degraded"
    assert response.json()["database"] == "unavailable"
