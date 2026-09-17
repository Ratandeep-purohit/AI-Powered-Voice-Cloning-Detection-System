from uuid import uuid4

import pytest

from app.models.voice_analysis import VoiceAnalysis
from app.services.risk_scoring import RiskScoringError, calculate_risk


def make_analysis(spoof: float, confidence: float, authentic: float | None = None, status: str = "COMPLETED") -> VoiceAnalysis:
    return VoiceAnalysis(
        id=uuid4(),
        call_id=uuid4(),
        model_name="test-model",
        model_version="test-v1",
        detection_status=status,
        synthetic_probability=spoof,
        authentic_probability=authentic if authentic is not None else 1.0 - spoof,
        confidence=confidence,
    )


@pytest.mark.parametrize(
    ("spoof", "confidence", "expected_level"),
    [
        (0.00, 1.00, "SAFE"),
        (0.30, 1.00, "LOW"),
        (0.50, 1.00, "MEDIUM"),
        (0.70, 1.00, "HIGH"),
        (0.90, 1.00, "CRITICAL"),
    ],
)
def test_calculate_risk_maps_deterministic_bands(spoof: float, confidence: float, expected_level: str) -> None:
    result = calculate_risk(make_analysis(spoof, confidence))
    assert result.risk_level == expected_level
    assert 0 <= result.risk_score <= 100
    assert result.policy_version == "1.0"


def test_low_confidence_pulls_score_toward_neutral_midpoint() -> None:
    result = calculate_risk(make_analysis(0.90, 0.50))
    assert result.risk_score == pytest.approx(70.0)
    assert result.risk_level == "HIGH"


def test_calculate_risk_rejects_incomplete_analysis() -> None:
    with pytest.raises(RiskScoringError, match="completed voice analysis"):
        calculate_risk(make_analysis(0.9, 0.9, status="PROCESSING"))


@pytest.mark.parametrize("field", ["synthetic_probability", "authentic_probability", "confidence"])
def test_calculate_risk_rejects_out_of_range_probability(field: str) -> None:
    analysis = make_analysis(0.9, 0.9)
    setattr(analysis, field, 1.1)
    with pytest.raises(RiskScoringError, match="between 0 and 1"):
        calculate_risk(analysis)


def test_calculate_risk_rejects_probability_mismatch() -> None:
    with pytest.raises(RiskScoringError, match="sum to approximately 1"):
        calculate_risk(make_analysis(0.9, 0.9, authentic=0.2))
