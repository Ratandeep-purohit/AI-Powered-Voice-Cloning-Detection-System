"""Integration tests for Phase 07 prevention persistence and isolation."""

from uuid import uuid4

import pytest
from sqlalchemy import select

from app.models.audit_log import AuditLog
from app.models.call import Call
from app.models.organization import Organization
from app.models.prevention_decision import PreventionDecision, VALID_RESPONSE_ACTIONS
from app.models.risk_score import RiskScore
from app.models.user import User
from app.services.prevention_service import (
    PreventionServiceError,
    _validate_risk_score,
    generate_prevention_decision,
    get_owned_risk_score,
    get_prevention_decision,
)


def _user(db, role="SECURITY_ANALYST"):
    org = Organization(name=f"Org {uuid4()}", slug=f"org-{uuid4().hex}")
    db.add(org)
    db.flush()
    user = User(
        organization_id=org.id,
        email=f"{uuid4().hex}@example.com",
        password_hash="test-hash",
        full_name="Phase 07 Test User",
        role=role,
        is_active=True,
    )
    db.add(user)
    db.flush()
    return org, user


def _risk(db, org, user, level="HIGH", score=68):
    call = Call(
        organization_id=org.id,
        initiated_by_user_id=user.id,
        source_type="SIMULATED",
        status="COMPLETED",
    )
    db.add(call)
    db.flush()
    risk = RiskScore(
        call_id=call.id,
        risk_score=score,
        risk_level=level,
        risk_factors={"source": "phase-07-test"},
        policy_version="risk-1.0",
    )
    db.add(risk)
    db.commit()
    db.refresh(risk)
    return call, risk


def test_high_risk_generates_review_decision_and_audit(db_session):
    org, user = _user(db_session)
    call, risk = _risk(db_session, org, user, "HIGH", 68)

    decision = generate_prevention_decision(db_session, user, call.id, risk.id, "127.0.0.1")

    assert decision.response_action == "REQUIRE_REVIEW"
    assert decision.policy_version == "1.0"
    assert float(decision.risk_score) == pytest.approx(68)
    assert decision.reason
    assert decision.response_action in VALID_RESPONSE_ACTIONS

    audit = db_session.scalar(select(AuditLog).where(AuditLog.entity_id == decision.id))
    assert audit is not None
    assert audit.action == "PREVENTION_DECISION_GENERATED"
    assert audit.event_metadata["response_action"] == "REQUIRE_REVIEW"


def test_duplicate_evaluation_reuses_same_decision(db_session):
    org, user = _user(db_session)
    call, risk = _risk(db_session, org, user, "CRITICAL", 88)

    first = generate_prevention_decision(db_session, user, call.id, risk.id)
    second = generate_prevention_decision(db_session, user, call.id, risk.id)

    assert first.id == second.id
    assert db_session.scalar(
        select(PreventionDecision).where(PreventionDecision.risk_score_id == risk.id)
    ) is not None


def test_cross_tenant_risk_is_not_visible(db_session):
    org_a, user_a = _user(db_session)
    _, user_b = _user(db_session)
    call, risk = _risk(db_session, org_a, user_a, "CRITICAL", 90)

    assert get_owned_risk_score(db_session, user_b, call.id, risk.id) is None
    assert get_prevention_decision(db_session, user_b, call.id, risk.id) is None
    with pytest.raises(PreventionServiceError, match="Risk assessment not found"):
        generate_prevention_decision(db_session, user_b, call.id, risk.id)


def test_invalid_risk_level_fails_closed_without_persistence():
    risk = RiskScore(call_id=uuid4(), risk_score=60, risk_level="NOT_A_LEVEL")
    with pytest.raises(PreventionServiceError, match="Risk level is invalid"):
        _validate_risk_score(risk)


def test_invalid_risk_score_fails_closed_without_persistence():
    risk = RiskScore(call_id=uuid4(), risk_score=101, risk_level="CRITICAL")
    with pytest.raises(PreventionServiceError, match="between 0 and 100"):
        _validate_risk_score(risk)
