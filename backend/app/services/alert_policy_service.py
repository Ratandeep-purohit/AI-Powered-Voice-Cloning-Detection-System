"""Deterministic Phase 09 alert policy."""

from __future__ import annotations

from dataclasses import dataclass

POLICY_VERSION = "1.0"
ALERT_TYPE = "SYNTHETIC_VOICE_RISK"
ALERTING_LEVELS = frozenset({"MEDIUM", "HIGH", "CRITICAL"})


@dataclass(frozen=True)
class AlertPolicyDecision:
    should_alert: bool
    severity: str | None
    alert_type: str | None
    title: str | None
    description: str | None


def evaluate_alert_policy(risk_level: str, risk_score: float) -> AlertPolicyDecision:
    if risk_level in {"SAFE", "LOW"}:
        return AlertPolicyDecision(False, None, None, None, None)
    if risk_level not in ALERTING_LEVELS:
        raise ValueError(f"Unsupported risk level: {risk_level}")
    severity = risk_level
    return AlertPolicyDecision(
        True,
        severity,
        ALERT_TYPE,
        f"{severity} synthetic voice risk detected",
        f"Risk score {risk_score:.2f} reached the {risk_level} policy band.",
    )
