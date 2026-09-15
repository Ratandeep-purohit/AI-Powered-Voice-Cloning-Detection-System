"""Phase 01 – Model instantiation and loading tests."""

from __future__ import annotations

def test_models_importable() -> None:
    """All models must be importable from the models package."""
    from app.models import (
        Alert,
        AlertAction,
        AudioSegment,
        AuditLog,
        Call,
        Organization,
        RiskScore,
        User,
        VoiceAnalysis,
    )

    assert Organization is not None
    assert User is not None
    assert Call is not None
    assert AudioSegment is not None
    assert VoiceAnalysis is not None
    assert RiskScore is not None
    assert Alert is not None
    assert AlertAction is not None
    assert AuditLog is not None
