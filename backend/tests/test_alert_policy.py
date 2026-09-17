import pytest

from app.services.alert_policy_service import evaluate_alert_policy


def test_safe_low_are_silent():
    assert not evaluate_alert_policy("SAFE", 10).should_alert
    assert not evaluate_alert_policy("LOW", 30).should_alert


@pytest.mark.parametrize("level", ["MEDIUM", "HIGH", "CRITICAL"])
def test_medium_high_critical_generate_alerts(level):
    decision = evaluate_alert_policy(level, 65.0)
    assert decision.should_alert
    assert decision.severity == level
    assert decision.alert_type == "SYNTHETIC_VOICE_RISK"


def test_unknown_level_is_rejected():
    with pytest.raises(ValueError):
        evaluate_alert_policy("UNKNOWN", 50.0)
