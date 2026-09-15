"""Password hashing and JWT helpers for Phase 02."""

from datetime import datetime, timedelta, timezone
from uuid import uuid4

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError

from app.config import get_settings

password_hasher = PasswordHasher()


def hash_password(password: str) -> str:
    return password_hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return password_hasher.verify(password_hash, password)
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        return False


def _encode(subject: str, organization_id: str, role: str, token_type: str, expires: timedelta) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": subject,
        "org": organization_id,
        "role": role,
        "type": token_type,
        "jti": str(uuid4()),
        "iat": now,
        "exp": now + expires,
    }
    settings = get_settings()
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def create_access_token(subject: str, organization_id: str, role: str) -> str:
    settings = get_settings()
    return _encode(subject, organization_id, role, "access", timedelta(minutes=settings.access_token_expire_minutes))


def create_refresh_token(subject: str, organization_id: str, role: str) -> str:
    settings = get_settings()
    return _encode(subject, organization_id, role, "refresh", timedelta(days=settings.refresh_token_expire_days))


def decode_token(token: str, expected_type: str) -> dict:
    settings = get_settings()
    payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    if payload.get("type") != expected_type or not payload.get("sub") or not payload.get("org"):
        raise jwt.InvalidTokenError("Invalid token")
    return payload


def decode_access_token(token: str) -> dict:
    return decode_token(token, "access")


def decode_refresh_token(token: str) -> dict:
    return decode_token(token, "refresh")
