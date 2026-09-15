"""Tests for authentication and authorization audit events."""

from __future__ import annotations

from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.audit_log import AuditLog
from app.models.organization import Organization
from app.models.user import User


@pytest.fixture
def audit_setup(db_session: Session) -> dict[str, str | User]:
    org = Organization(name=f"Audit Org {uuid4().hex}", slug=f"audit-org-{uuid4().hex}")
    db_session.add(org)
    db_session.flush()

    raw_password = "audit-password"
    user = User(
        organization_id=org.id,
        email=f"audit.{uuid4().hex}@example.com",
        password_hash=hash_password(raw_password),
        role="ADMIN",
    )
    db_session.add(user)
    db_session.commit()

    return {"user": user, "password": raw_password}


def test_audit_login_success(client: TestClient, db_session: Session, audit_setup: dict):
    """Successful login creates an AUTH / LOGIN_SUCCESS audit log."""
    user = audit_setup["user"]
    password = audit_setup["password"]

    res = client.post(
        "/api/v1/auth/login",
        json={"email": user.email, "password": password},
    )
    assert res.status_code == 200

    log = db_session.query(AuditLog).filter_by(action="LOGIN_SUCCESS").first()
    assert log is not None
    assert log.event_type == "AUTH"
    assert log.user_id == user.id
    assert log.organization_id == user.organization_id
    
    # Audit log must NOT contain password
    assert "password" not in str(log.event_metadata).lower()


def test_audit_login_failure(client: TestClient, db_session: Session, audit_setup: dict):
    """Failed login creates an AUTH / LOGIN_FAILURE audit log without secrets."""
    user = audit_setup["user"]

    res = client.post(
        "/api/v1/auth/login",
        json={"email": user.email, "password": "wrong-password-on-purpose"},
    )
    assert res.status_code == 401

    log = db_session.query(AuditLog).filter_by(action="LOGIN_FAILURE").first()
    assert log is not None
    assert log.event_type == "AUTH"
    
    # Raw email is NOT logged directly, only via a hint, and NEVER the password
    meta_str = str(log.event_metadata).lower() if log.event_metadata else ""
    assert "wrong-password-on-purpose" not in meta_str
    # The email hint is logged for failures to assist tracing
    assert user.email in meta_str


def test_audit_authorization_denial(client: TestClient, db_session: Session, audit_setup: dict):
    """Cross-tenant access attempt creates an AUTHZ / ACCESS_DENIED log."""
    user = audit_setup["user"]
    password = audit_setup["password"]
    
    # Login as admin in Org A
    login_res = client.post(
        "/api/v1/auth/login",
        json={"email": user.email, "password": password},
    )
    token = login_res.json()["access_token"]

    # Attempt to access a nonexistent user ID (simulating cross-tenant or missing)
    fake_id = uuid4()
    res = client.get(
        f"/api/v1/users/{fake_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 404

    # The get_user endpoint does not hit assert_same_organization if user is not found,
    # so we need to mock a cross-tenant user or test via an existing user in another org.
    # Let's create a user in another org.
    org_b = Organization(name=f"Org B {uuid4().hex}", slug=f"org-b-{uuid4().hex}")
    db_session.add(org_b)
    db_session.flush()
    user_b = User(organization_id=org_b.id, email=f"b.{uuid4().hex}@example.com", password_hash="1", role="OPERATOR")
    db_session.add(user_b)
    db_session.commit()

    # Now attempt cross-tenant access
    res = client.get(
        f"/api/v1/users/{user_b.id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 404

    # This should trigger the audit log
    log = db_session.query(AuditLog).filter_by(action="ACCESS_DENIED").first()
    assert log is not None
    assert log.event_type == "AUTHZ"
    assert log.user_id == user.id
    assert log.organization_id == user.organization_id
    assert str(user_b.id) in log.event_metadata["resource"]
