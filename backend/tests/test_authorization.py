"""Tests for server-side RBAC and Tenant Isolation."""

from __future__ import annotations

from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import create_access_token, hash_password
from app.models.organization import Organization
from app.models.user import User


@pytest.fixture
def authz_setup(db_session: Session) -> dict[str, dict]:
    """Create two organizations with admins and operators."""
    
    # Org A
    org_a = Organization(name=f"Org A {uuid4().hex}", slug=f"org-a-{uuid4().hex}")
    db_session.add(org_a)
    db_session.flush()

    admin_email_a = f"admin.a.{uuid4().hex}@example.com"
    admin_a = User(
        organization_id=org_a.id,
        email=admin_email_a,
        password_hash=hash_password("password"),
        role="ADMIN",
    )
    operator_a = User(
        organization_id=org_a.id,
        email=f"operator.a.{uuid4().hex}@example.com",
        password_hash=hash_password("password"),
        role="OPERATOR",
    )
    db_session.add_all([admin_a, operator_a])

    # Org B
    org_b = Organization(name=f"Org B {uuid4().hex}", slug=f"org-b-{uuid4().hex}")
    db_session.add(org_b)
    db_session.flush()

    admin_email_b = f"admin.b.{uuid4().hex}@example.com"
    admin_b = User(
        organization_id=org_b.id,
        email=admin_email_b,
        password_hash=hash_password("password"),
        role="ADMIN",
    )
    db_session.add(admin_b)
    db_session.commit()

    return {
        "org_a": org_a,
        "org_b": org_b,
        "admin_a": admin_a,
        "operator_a": operator_a,
        "admin_b": admin_b,
        "admin_email_b": admin_email_b,
    }


def _get_token(user: User) -> str:
    return create_access_token(user.id, user.organization_id, user.role)


# ── RBAC Tests ─────────────────────────────────────────────────────────────

def test_admin_can_list_users(client: TestClient, authz_setup: dict):
    """Admins can access user management endpoints."""
    admin_a = authz_setup["admin_a"]
    token = _get_token(admin_a)

    res = client.get("/api/v1/users", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    assert len(res.json()) == 2  # Admin A + Operator A


def test_operator_cannot_list_users(client: TestClient, authz_setup: dict):
    """Operators (insufficient role) receive 403 Forbidden on user endpoints."""
    operator_a = authz_setup["operator_a"]
    token = _get_token(operator_a)

    res = client.get("/api/v1/users", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 403


# ── Tenant Isolation Tests ─────────────────────────────────────────────────

def test_tenant_isolation_list_users(client: TestClient, authz_setup: dict):
    """Admins can only see users in their own organization."""
    admin_b = authz_setup["admin_b"]
    token = _get_token(admin_b)

    res = client.get("/api/v1/users", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    
    users = res.json()
    assert len(users) == 1
    assert users[0]["email"] == authz_setup["admin_email_b"]
    # Cannot see Admin A or Operator A


def test_tenant_isolation_get_user(client: TestClient, authz_setup: dict):
    """Attempting to access a resource in another organization returns 404."""
    admin_a = authz_setup["admin_a"]
    admin_b = authz_setup["admin_b"]
    token = _get_token(admin_a)

    # Admin A attempts to get Admin B's profile
    res = client.get(f"/api/v1/users/{admin_b.id}", headers={"Authorization": f"Bearer {token}"})
    
    # Must be 404 (not 403) to prevent cross-tenant enumeration leaks
    assert res.status_code == 404


def test_tenant_isolation_update_user(client: TestClient, authz_setup: dict):
    """Attempting to modify a resource in another organization returns 404."""
    admin_a = authz_setup["admin_a"]
    admin_b = authz_setup["admin_b"]
    token = _get_token(admin_a)

    # Admin A attempts to disable Admin B
    res = client.patch(
        f"/api/v1/users/{admin_b.id}",
        json={"is_active": False},
        headers={"Authorization": f"Bearer {token}"},
    )
    
    assert res.status_code == 404


def test_admin_cannot_disable_self(client: TestClient, authz_setup: dict):
    """Self-disabling is prevented via API layer."""
    admin_a = authz_setup["admin_a"]
    token = _get_token(admin_a)

    res = client.patch(
        f"/api/v1/users/{admin_a.id}",
        json={"is_active": False},
        headers={"Authorization": f"Bearer {token}"},
    )
    
    assert res.status_code == 400
    assert "disable your own account" in res.text
