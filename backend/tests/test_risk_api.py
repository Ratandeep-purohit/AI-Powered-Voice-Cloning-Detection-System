from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_risk_policy_requires_authentication() -> None:
    response = client.get("/api/v1/risk/policy")
    assert response.status_code == 401


def test_risk_score_creation_requires_authentication() -> None:
    response = client.post(
        "/api/v1/risk/calls/00000000-0000-0000-0000-000000000001/analyses/00000000-0000-0000-0000-000000000002/score"
    )
    assert response.status_code == 401


def test_risk_score_lookup_requires_authentication() -> None:
    response = client.get(
        "/api/v1/risk/calls/00000000-0000-0000-0000-000000000001/analyses/00000000-0000-0000-0000-000000000002/score"
    )
    assert response.status_code == 401
