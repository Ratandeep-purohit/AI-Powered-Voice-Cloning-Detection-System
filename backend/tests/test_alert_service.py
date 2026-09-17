from uuid import uuid4

import pytest

from app.services.alert_service import (
    STATUS_ACKNOWLEDGED,
    STATUS_DISMISSED,
    STATUS_INVESTIGATING,
    STATUS_OPEN,
    STATUS_RESOLVED,
    TRANSITIONS,
    AlertAssessment,
    assess_risk,
)


class FakeRisk:
    def __init__(self, level):
        self.risk_level = level
        self.risk_score = 72.5


def test_safe_and_low_do_not_generate_alerts():
    assert assess_risk(FakeRisk("SAFE")).should_alert is False
    assert assess_risk(FakeRisk("LOW")).should_alert is False


@pytest.mark.parametrize("level", ["MEDIUM", "HIGH", "CRITICAL"])
def test_alerting_risk_levels_map_to_same_severity(level):
    result = assess_risk(FakeRisk(level))
    assert result.should_alert is True
    assert result.severity == level
    assert result.alert_type == "SYNTHETIC_VOICE_RISK"


def test_lifecycle_has_terminal_states():
    assert TRANSITIONS[STATUS_RESOLVED] == set()
    assert TRANSITIONS[STATUS_DISMISSED] == set()
    assert STATUS_ACKNOWLEDGED in TRANSITIONS[STATUS_OPEN]
    assert STATUS_INVESTIGATING in TRANSITIONS[STATUS_ACKNOWLEDGED]
    assert STATUS_RESOLVED in TRANSITIONS[STATUS_INVESTIGATING]
