"""Tests for authentication endpoints and security utilities."""

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import (
    TokenValidationError,
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)
from app.models.organization import Organization
from app.models.user import User


@pytest.fixture
def auth_setup(db_session: Session) -> dict[str, str | User]:
    """Create an organization and a user for authentication tests."""
    org = Organization(name=f"Test Org {uuid4().hex}", slug=f"test-org-{uuid4().hex}")
    db_session.add(org)
    db_session.flush()

    raw_password = "secure-password-123"
    user = User(
        organization_id=org.id,
        email=f"auth.test.{uuid4().hex}@example.com",
        password_hash=hash_password(raw_password),
        role="SECURITY_ANALYST",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()

    return {"user": user, "password": raw_password}


# ── Utility Tests ──────────────────────────────────────────────────────────

def test_password_hashing():
    """Verify password hashing produces safe, verifiable hashes."""
    password = "my-secret-password"
    hashed = hash_password(password)

    # Hash must not contain the plaintext
    assert password not in hashed
    # Hash must be verifiable
    assert verify_password(password, hashed) is True
    # Incorrect password must fail
    assert verify_password("wrong-password", hashed) is False
    # Malformed hash must fail safely
    assert verify_password(password, "not-a-real-hash") is False


def test_jwt_creation_and_validation():
    """Verify JWTs are signed, decodable, and expire correctly."""
    user_id = uuid4()
    org_id = uuid4()
    role = "OPERATOR"

    token = create_access_token(user_id, org_id, role)
    payload = decode_access_token(token)

    assert payload["sub"] == str(user_id)
    assert payload["org"] == str(org_id)
    assert payload["role"] == role
    assert "exp" in payload
    assert "iat" in payload


def test_jwt_validation_failures():
    """Verify malformed and expired JWTs are rejected."""
    # Malformed
    with pytest.raises(TokenValidationError):
        decode_access_token("not-a-token")

    # Expired token (we mock this by generating a token manually with past exp)
    from app.config import get_settings
    import jwt

    settings = get_settings()
    past = datetime.now(timezone.utc) - timedelta(hours=1)
    expired_token = jwt.encode(
        {"sub": str(uuid4()), "org": str(uuid4()), "role": "ADMIN", "exp": past, "iat": past},
        settings.jwt_secret,
        algorithm=settings.jwt_algorithm,
    )
    with pytest.raises(TokenValidationError):
        decode_access_token(expired_token)


# ── Endpoint Tests ─────────────────────────────────────────────────────────

def test_login_success(client: TestClient, auth_setup: dict[str, str | User]):
    """Valid credentials return a token and safe profile."""
    user = auth_setup["user"]
    password = auth_setup["password"]

    response = client.post(
        "/api/v1/auth/login",
        json={"email": user.email, "password": password},
    )
    assert response.status_code == 200
    data = response.json()

    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert "user" in data
    
    # Password hash MUST NOT be exposed
    assert "password_hash" not in data["user"]
    assert "password" not in data["user"]
    assert data["user"]["email"] == user.email


def test_login_invalid_password(client: TestClient, auth_setup: dict[str, str | User]):
    """Invalid password returns generic 401."""
    user = auth_setup["user"]
    response = client.post(
        "/api/v1/auth/login",
        json={"email": user.email, "password": "wrong-password"},
    )
    assert response.status_code == 401
    assert "invalid email or password" in response.text.lower()


def test_login_unknown_user(client: TestClient):
    """Unknown email returns generic 401 (prevent enumeration)."""
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "nobody@example.com", "password": "any-password"},
    )
    assert response.status_code == 401


def test_login_inactive_user(client: TestClient, db_session: Session, auth_setup: dict[str, str | User]):
    """Inactive users cannot login."""
    user = auth_setup["user"]
    user.is_active = False
    db_session.commit()

    response = client.post(
        "/api/v1/auth/login",
        json={"email": user.email, "password": auth_setup["password"]},
    )
    assert response.status_code == 401


def test_get_current_user(client: TestClient, auth_setup: dict[str, str | User]):
    """GET /me returns the current authenticated identity."""
    user = auth_setup["user"]
    password = auth_setup["password"]

    # Login to get token
    login_res = client.post(
        "/api/v1/auth/login",
        json={"email": user.email, "password": password},
    )
    token = login_res.json()["access_token"]

    # Use token
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    
    data = response.json()
    assert data["id"] == str(user.id)
    assert data["role"] == user.role
    assert data["organization_id"] == str(user.organization_id)
    assert "password_hash" not in data


def test_get_current_user_no_token(client: TestClient):
    """Missing token returns 403 (FastAPI HTTPBearer default behavior)."""
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 403


def test_get_current_user_invalid_token(client: TestClient):
    """Invalid token returns 401."""
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer not-a-real-jwt"},
    )
    assert response.status_code == 401
