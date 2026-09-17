"""Phase 08 deterministic risk scoring engine."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog
from app.models.call import Call
from app.models.risk_score import RiskScore, VALID_RISK_LEVELS
from app.models.user import User
from app.models.voice_analysis import VoiceAnalysis

POLICY_VERSION = "1.0"

RISK_LEVEL_BANDS: tuple[tuple[float, str], ...] = (
    (20.0, "SAFE"),
    (40.0, "LOW"),
    (60.0, "MEDIUM"),
    (80.0, "HIGH"),
    (100.0, "CRITICAL"),
)


class RiskScoringError(ValueError):
    """Raised when a risk score cannot be safely generated."""


@dataclass(frozen=True, slots=True)
class RiskAssessment:
    risk_score: float
    risk_level: str
    risk_factors: dict
    policy_version: str


def _bounded_probability(value: float | None, field_name: str) -> float:
    if value is None:
        raise RiskScoringError(f"Voice analysis {field_name} is required")
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise RiskScoringError(f"Voice analysis {field_name} is invalid") from exc
    if not 0.0 <= number <= 1.0:
        raise RiskScoringError(f"Voice analysis {field_name} must be between 0 and 1")
    return number


def _risk_level(score: float) -> str:
    for upper_bound, level in RISK_LEVEL_BANDS:
        if score < upper_bound:
            return level
    return "CRITICAL"


def calculate_risk(analysis: VoiceAnalysis) -> RiskAssessment:
    """Convert detector probability/confidence into a bounded, explainable risk score.

    The detector supplies spoof probability and confidence. Confidence acts as
    evidence strength: uncertain predictions are pulled toward the neutral
    midpoint rather than being treated as equally strong evidence.
    """
    status = analysis.detection_status.strip().upper() if isinstance(analysis.detection_status, str) else ""
    if status != "COMPLETED":
        raise RiskScoringError("Risk scoring requires a completed voice analysis")

    spoof_probability = _bounded_probability(analysis.synthetic_probability, "synthetic_probability")
    confidence = _bounded_probability(analysis.confidence, "confidence")
    authentic_probability = _bounded_probability(analysis.authentic_probability, "authentic_probability")

    if abs((spoof_probability + authentic_probability) - 1.0) > 0.02:
        raise RiskScoringError("Voice analysis probabilities must sum to approximately 1")

    evidence_score = spoof_probability * confidence + 0.5 * (1.0 - confidence)
    score_decimal = (Decimal(str(evidence_score * 100)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))
    score = float(score_decimal)
    level = _risk_level(score)

    factors = {
        "synthetic_probability": round(spoof_probability, 6),
        "authentic_probability": round(authentic_probability, 6),
        "confidence": round(confidence, 6),
        "detector_evidence_score": round(evidence_score, 6),
        "formula": "synthetic_probability * confidence + 0.5 * (1 - confidence)",
        "risk_level_bands": {
            "SAFE": "0-19.99",
            "LOW": "20-39.99",
            "MEDIUM": "40-59.99",
            "HIGH": "60-79.99",
            "CRITICAL": "80-100",
        },
    }
    if level not in VALID_RISK_LEVELS:
        raise RiskScoringError("Calculated risk level is invalid")

    return RiskAssessment(score, level, factors, POLICY_VERSION)


def get_owned_voice_analysis(
    db: Session, user: User, session_id: UUID, analysis_id: UUID
) -> VoiceAnalysis | None:
    return db.scalar(
        select(VoiceAnalysis)
        .join(Call, Call.id == VoiceAnalysis.call_id)
        .where(
            VoiceAnalysis.id == analysis_id,
            VoiceAnalysis.call_id == session_id,
            Call.organization_id == user.organization_id,
        )
    )


def get_existing_risk_score(
    db: Session, user: User, session_id: UUID, analysis_id: UUID
) -> RiskScore | None:
    return db.scalar(
        select(RiskScore)
        .join(Call, Call.id == RiskScore.call_id)
        .where(
            RiskScore.voice_analysis_id == analysis_id,
            RiskScore.call_id == session_id,
            Call.organization_id == user.organization_id,
            RiskScore.policy_version == POLICY_VERSION,
        )
    )


def generate_risk_score(
    db: Session,
    user: User,
    session_id: UUID,
    analysis_id: UUID,
    ip_address: str | None = None,
) -> RiskScore:
    """Generate and persist one tenant-scoped, idempotent risk assessment."""
    analysis = get_owned_voice_analysis(db, user, session_id, analysis_id)
    if analysis is None:
        raise RiskScoringError("Voice analysis not found")

    existing = get_existing_risk_score(db, user, session_id, analysis_id)
    if existing is not None:
        return existing

    assessment = calculate_risk(analysis)
    risk = RiskScore(
        call_id=analysis.call_id,
        voice_analysis_id=analysis.id,
        risk_score=assessment.risk_score,
        risk_level=assessment.risk_level,
        risk_factors=assessment.risk_factors,
        policy_version=assessment.policy_version,
    )
    db.add(risk)

    try:
        db.flush()
        db.add(
            AuditLog(
                organization_id=user.organization_id,
                user_id=user.id,
                event_type="RISK_SCORING",
                action="RISK_SCORE_GENERATED",
                entity_type="RISK_SCORE",
                entity_id=risk.id,
                event_metadata={
                    "call_id": str(analysis.call_id),
                    "voice_analysis_id": str(analysis.id),
                    "risk_score": assessment.risk_score,
                    "risk_level": assessment.risk_level,
                    "policy_version": assessment.policy_version,
                },
                ip_address=ip_address,
            )
        )
        db.commit()
    except SQLAlchemyError as exc:
        db.rollback()
        existing = get_existing_risk_score(db, user, session_id, analysis_id)
        if existing is not None:
            return existing
        raise RiskScoringError("Risk score could not be persisted") from exc

    db.refresh(risk)
    return risk
