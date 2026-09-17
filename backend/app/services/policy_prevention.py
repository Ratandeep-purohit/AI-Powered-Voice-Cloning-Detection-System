"""Deterministic policy and prevention engine.

The engine converts persisted risk/detection evidence into an enforcement
instruction. No LLM is involved in this security decision.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class PreventionAction(StrEnum):
    ALLOW = "ALLOW"
    MONITOR = "MONITOR"
    REQUIRE_REVIEW = "REQUIRE_REVIEW"
    BLOCK = "BLOCK"


VALID_RISK_LEVELS = {"SAFE", "LOW", "MEDIUM", "HIGH", "CRITICAL"}
VALID_DETECTION_DECISIONS = {"REAL", "SPOOF"}


@dataclass(frozen=True, slots=True)
class PolicyDecision:
    action: PreventionAction
    risk_level: str
    risk_score: float
    detection_decision: str | None
    confidence: float | None
    policy_version: str
    requires_review: bool
    should_alert: bool
    should_block: bool
    explanation: str


def evaluate_policy(
    *,
    risk_score: float,
    risk_level: str,
    detection_decision: str | None = None,
    confidence: float | None = None,
    policy_version: str = "prevention-v1",
) -> PolicyDecision:
    """Evaluate one call using deterministic, fail-closed policy rules."""
    try:
        score = float(risk_score)
    except (TypeError, ValueError):
        raise ValueError("risk_score must be numeric") from None
    if not 0.0 <= score <= 100.0:
        raise ValueError("risk_score must be between 0 and 100")

    level = str(risk_level).upper().strip()
    if level not in VALID_RISK_LEVELS:
        raise ValueError("risk_level must be SAFE, LOW, MEDIUM, HIGH, or CRITICAL")

    decision = detection_decision.upper().strip() if detection_decision else None
    if decision is not None and decision not in VALID_DETECTION_DECISIONS:
        raise ValueError("detection_decision must be REAL, SPOOF, or omitted")

    confidence_value: float | None = None
    if confidence is not None:
        confidence_value = float(confidence)
        if not 0.0 <= confidence_value <= 1.0:
            raise ValueError("confidence must be between 0 and 1")

    # Critical spoof evidence is the only path that blocks immediately.
    if level == "CRITICAL" and decision == "SPOOF":
        return PolicyDecision(
            action=PreventionAction.BLOCK,
            risk_level=level,
            risk_score=score,
            detection_decision=decision,
            confidence=confidence_value,
            policy_version=policy_version,
            requires_review=True,
            should_alert=True,
            should_block=True,
            explanation="Critical-risk spoof detection requires immediate blocking and security review.",
        )

    # High risk or any confirmed spoof requires a human review gate.
    if level == "HIGH" or decision == "SPOOF":
        return PolicyDecision(
            action=PreventionAction.REQUIRE_REVIEW,
            risk_level=level,
            risk_score=score,
            detection_decision=decision,
            confidence=confidence_value,
            policy_version=policy_version,
            requires_review=True,
            should_alert=True,
            should_block=False,
            explanation="High-risk or spoof-positive audio requires security review before trusted handling.",
        )

    if level == "MEDIUM":
        return PolicyDecision(
            action=PreventionAction.MONITOR,
            risk_level=level,
            risk_score=score,
            detection_decision=decision,
            confidence=confidence_value,
            policy_version=policy_version,
            requires_review=False,
            should_alert=True,
            should_block=False,
            explanation="Medium-risk audio may continue under monitoring and alerting.",
        )

    if level in {"SAFE", "LOW"}:
        return PolicyDecision(
            action=PreventionAction.ALLOW,
            risk_level=level,
            risk_score=score,
            detection_decision=decision,
            confidence=confidence_value,
            policy_version=policy_version,
            requires_review=False,
            should_alert=False,
            should_block=False,
            explanation="The current deterministic policy allows this audio session.",
        )

    # Defensive fail-closed fallback for future/unknown policy states.
    return PolicyDecision(
        action=PreventionAction.REQUIRE_REVIEW,
        risk_level=level,
        risk_score=score,
        detection_decision=decision,
        confidence=confidence_value,
        policy_version=policy_version,
        requires_review=True,
        should_alert=True,
        should_block=False,
        explanation="The policy state is not safely understood; manual review is required.",
    )


def build_policy_prevention_engine(policy_version: str = "prevention-v1"):
    """Build a dependency-injectable policy callable."""
    def decide(**kwargs) -> PolicyDecision:
        return evaluate_policy(policy_version=policy_version, **kwargs)

    return decide
