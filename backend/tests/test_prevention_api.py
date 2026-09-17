"""API-level authorization and routing tests for Phase 07."""


def test_prevention_routes_are_registered(fastapi_app):
    paths = {route.path for route in fastapi_app.routes}
    assert "/api/v1/prevention/policy" in paths
    assert "/api/v1/prevention/calls/{session_id}/risk/{risk_score_id}" in paths


def test_prevention_policy_requires_authentication(client):
    response = client.get("/api/v1/prevention/policy")
    assert response.status_code == 401


def test_prevention_generation_requires_authentication(client):
    response = client.post(
        "/api/v1/prevention/calls/00000000-0000-0000-0000-000000000001/risk/00000000-0000-0000-0000-000000000002"
    )
    assert response.status_code == 401
