"""Deterministic Phase 07 risk-to-response policy."""

from __future__ import annotations

from dataclasses import dataclass

from app.models.prevention_decision import VALID_RESPONSE_ACTIONS

POLICY_VERSION = "1.0"

# Centralized policy: the API layer must never own this mapping.
RISK_TO_RESPONSE: dict[str, str] = {
    "SAFE": "ALLOW",
    "LOW": "ALLOW",
    "MEDIUM": "MONITOR",
    "HIGH": "REQUIRE_REVIEW",
    "CRITICAL": "BLOCK",
}

RESPONSE_REASONS: dict[str, str] = {
    "SAFE": "Risk assessment is safe; no prevention restriction is required.",
    "LOW": "Low risk assessment does not require a prevention restriction.",
    "MEDIUM": "Medium risk requires continued monitoring.",
    "HIGH": "High risk requires manual security review before continuation.",
    "CRITICAL": "Critical risk requires the workflow to be blocked.",
}

SUPPORTED_RISK_LEVELS = frozenset(RISK_TO_RESPONSE)


class ResponsePolicyError(ValueError):
    """Raised when a risk result cannot be evaluated safely."""


@dataclass(frozen=True, slots=True)
class PolicyDecision:
    """Pure deterministic output of policy evaluation."""

    risk_level: str
    response_action: str
    policy_version: str
    reason: str


def validate_policy_configuration() -> None:
    """Fail closed if the centralized policy becomes internally inconsistent."""
    if not RISK_TO_RESPONSE:
        raise ResponsePolicyError("Response policy is empty")
    if set(RISK_TO_RESPONSE.values()) - set(VALID_RESPONSE_ACTIONS):
        raise ResponsePolicyError("Response policy contains an unsupported response action")
    if set(RISK_TO_RESPONSE) != set(RESPONSE_REASONS):
        raise ResponsePolicyError("Response policy reasons do not match supported risk levels")


def evaluate_policy(risk_level: str) -> PolicyDecision:
    """Map a validated Phase 06 risk level to one deterministic response."""
    validate_policy_configuration()
    normalized = risk_level.strip().upper() if isinstance(risk_level, str) else ""
    if normalized not in SUPPORTED_RISK_LEVELS:
        raise ResponsePolicyError(f"Unsupported risk level: {risk_level!r}")
    action = RISK_TO_RESPONSE[normalized]
    return PolicyDecision(
        risk_level=normalized,
        response_action=action,
        policy_version=POLICY_VERSION,
        reason=RESPONSE_REASONS[normalized],
    )
