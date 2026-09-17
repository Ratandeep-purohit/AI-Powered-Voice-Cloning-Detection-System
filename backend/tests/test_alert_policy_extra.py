from app.services.alert_policy_service import ALERTING_LEVELS, POLICY_VERSION


def test_policy_metadata():
    assert POLICY_VERSION == "1.0"
    assert ALERTING_LEVELS == {"MEDIUM", "HIGH", "CRITICAL"}
