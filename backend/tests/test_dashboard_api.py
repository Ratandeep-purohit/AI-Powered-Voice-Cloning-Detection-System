from app.main import create_app


def test_phase_10_dashboard_route_is_registered():
    paths = {route.path for route in create_app().routes}
    assert "/api/v1/dashboard/overview" in paths
