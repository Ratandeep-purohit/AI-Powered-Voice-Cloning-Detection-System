"""Phase 01 – Database constraints tests."""

from __future__ import annotations

import pytest
from sqlalchemy.exc import IntegrityError

from app.models import Call, Organization, RiskScore, User


def test_unique_organization_slug(db_session) -> None:
    """Test that organization slugs must be unique."""
    import uuid
    slug = f"unique-slug-{uuid.uuid4().hex}"
    org1 = Organization(name=f"Org 1 {uuid.uuid4().hex}", slug=slug)
    db_session.add(org1)
    db_session.commit()

    with pytest.raises(IntegrityError):
        org2 = Organization(name=f"Org 2 {uuid.uuid4().hex}", slug=slug)
        db_session.add(org2)
        db_session.flush()
    db_session.rollback()


def test_invalid_user_role(db_session) -> None:
    """Test that invalid user roles are rejected by the CHECK constraint."""
    import uuid
    org = Organization(name=f"Role Test Org {uuid.uuid4().hex}", slug=f"role-test-{uuid.uuid4().hex}")
    db_session.add(org)
    db_session.flush()

    user = User(
        organization_id=org.id,
        email=f"invalid.role.{uuid.uuid4().hex}@example.com",
        password_hash="fake",
        role="SUPER_HACKER",  # Not in the valid list
    )
    db_session.add(user)

    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_risk_score_range(db_session) -> None:
    """Risk score must be between 0 and 100."""
    import uuid
    org = Organization(name=f"Risk Org {uuid.uuid4().hex}", slug=f"risk-test-{uuid.uuid4().hex}")
    db_session.add(org)
    db_session.flush()

    call = Call(
        organization_id=org.id,
        source_type="UPLOAD",
        status="PENDING",
    )
    db_session.add(call)
    db_session.flush()

    risk = RiskScore(
        call_id=call.id,
        risk_score=105.0,  # Invalid
        risk_level="CRITICAL",
    )
    db_session.add(risk)

    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()
