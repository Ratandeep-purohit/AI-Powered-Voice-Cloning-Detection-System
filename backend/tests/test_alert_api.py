from app.main import create_app


def test_phase_09_alert_routes_are_registered():
    paths = {route.path for route in create_app().routes}
    assert "/api/v1/alerts/policy" in paths
    assert "/api/v1/alerts/risk/{risk_score_id}" in paths
    assert "/api/v1/alerts/{alert_id}" in paths
    assert "/api/v1/alerts/{alert_id}/actions" in paths
    assert "/api/v1/alerts/{alert_id}/transition" in paths
    assert "/api/v1/alerts/{alert_id}/acknowledge" in paths
    assert "/api/v1/alerts/{alert_id}/investigate" in paths
    assert "/api/v1/alerts/{alert_id}/resolve" in paths
    assert "/api/v1/alerts/{alert_id}/dismiss" in paths
