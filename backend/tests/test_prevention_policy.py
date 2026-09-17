"""Unit tests for the deterministic Phase 07 response policy."""

import pytest

from app.models.prevention_decision import VALID_RESPONSE_ACTIONS
from app.services.response_policy_service import (
    POLICY_VERSION,
    RISK_TO_RESPONSE,
    ResponsePolicyError,
    evaluate_policy,
    validate_policy_configuration,
)


@pytest.mark.parametrize(
    ("risk_level", "action"),
    [
        ("SAFE", "ALLOW"),
        ("LOW", "ALLOW"),
        ("MEDIUM", "MONITOR"),
        ("HIGH", "REQUIRE_REVIEW"),
        ("CRITICAL", "BLOCK"),
    ],
)
def test_risk_levels_map_to_expected_actions(risk_level, action):
    decision = evaluate_policy(risk_level)
    assert decision.response_action == action
    assert decision.risk_level == risk_level
    assert decision.policy_version == POLICY_VERSION
    assert decision.reason


def test_policy_normalizes_risk_level_case_and_whitespace():
    assert evaluate_policy("  critical ").response_action == "BLOCK"


def test_invalid_risk_level_fails_closed():
    with pytest.raises(ResponsePolicyError, match="Unsupported risk level"):
        evaluate_policy("UNKNOWN")


def test_policy_configuration_is_internally_valid():
    validate_policy_configuration()
    assert set(RISK_TO_RESPONSE.values()) <= set(VALID_RESPONSE_ACTIONS)


def test_policy_has_no_hidden_fallback_action():
    assert set(RISK_TO_RESPONSE) == {"SAFE", "LOW", "MEDIUM", "HIGH", "CRITICAL"}
    assert all(action in VALID_RESPONSE_ACTIONS for action in RISK_TO_RESPONSE.values())
