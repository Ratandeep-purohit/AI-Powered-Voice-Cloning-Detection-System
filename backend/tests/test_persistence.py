"""Phase 01 – Database persistence tests."""

from __future__ import annotations

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


def test_create_organization_and_user(db_session) -> None:
    """Test creating an organization and a related user."""
    import uuid
    org = Organization(name=f"Test Org {uuid.uuid4().hex}", slug=f"test-org-{uuid.uuid4().hex}")
    db_session.add(org)
    db_session.flush()

    user = User(
        organization_id=org.id,
        email=f"test.{uuid.uuid4().hex}@example.com",
        password_hash="fake-hash",
        role="SECURITY_ANALYST",
    )
    db_session.add(user)
    db_session.commit()

    assert user.id is not None
    assert user.organization.name == org.name


def test_create_full_analysis_workflow(db_session) -> None:
    """Test creating a call, segments, analysis, risk, alert, and audit."""
    org = Organization(name="Analysis Org", slug="analysis-org")
    db_session.add(org)
    db_session.flush()

    # 1. Call
    call = Call(
        organization_id=org.id,
        source_type="UPLOAD",
        status="PROCESSING",
    )
    db_session.add(call)
    db_session.flush()

    # 2. Audio segment
    segment = AudioSegment(
        call_id=call.id,
        sequence_number=1,
        start_offset_ms=0,
        end_offset_ms=1000,
        duration_ms=1000,
        speech_detected=True,
    )
    db_session.add(segment)
    db_session.flush()

    # 3. Voice analysis
    analysis = VoiceAnalysis(
        call_id=call.id,
        audio_segment_id=segment.id,
        model_name="test-model",
        detection_status="COMPLETED",
        synthetic_probability=0.85,
    )
    db_session.add(analysis)
    db_session.flush()

    # 4. Risk score
    risk = RiskScore(
        call_id=call.id,
        voice_analysis_id=analysis.id,
        risk_score=85.0,
        risk_level="HIGH",
    )
    db_session.add(risk)
    db_session.flush()

    # 5. Alert
    alert = Alert(
        organization_id=org.id,
        call_id=call.id,
        risk_score_id=risk.id,
        alert_type="SYNTHETIC_VOICE",
        severity="HIGH",
        title="High synthetic voice probability detected",
    )
    db_session.add(alert)
    db_session.flush()

    # 6. Alert Action
    action = AlertAction(
        alert_id=alert.id,
        action_type="STATUS_CHANGE",
        new_status="INVESTIGATING",
    )
    db_session.add(action)
    db_session.flush()

    # 7. Audit Log
    audit = AuditLog(
        organization_id=org.id,
        event_type="CALL_ANALYZED",
        action="Created high risk alert",
        entity_id=alert.id,
    )
    db_session.add(audit)
    db_session.commit()

    # Verify everything persisted with valid UUIDs
    assert call.id is not None
    assert alert.id is not None
    assert audit.id is not None
    assert len(call.audio_segments) == 1
    assert call.risk_scores[0].risk_level == "HIGH"
