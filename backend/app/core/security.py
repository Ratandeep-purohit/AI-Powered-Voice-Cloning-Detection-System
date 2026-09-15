"""Core security utilities: Argon2 password hashing and JWT handling.

SECURITY RULES enforced here:
- Passwords are NEVER stored in plaintext.
- Password hashes are NEVER returned in any API response.
- JWT secrets come ONLY from the environment (via Settings).
- Nothing in this module is logged that could reveal credentials.
- Tokens are validated server-side; client-supplied claims are never trusted.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerifyMismatchError, VerificationError

from app.config import get_settings

logger = logging.getLogger(__name__)

# ── Argon2 hasher (uses library defaults which are safe for the current era) ──
# RFC 9106 / OWASP recommended: argon2id variant via argon2-cffi defaults.
_ph = PasswordHasher()


# ── Password helpers ──────────────────────────────────────────────────────────

def hash_password(plain_password: str) -> str:
    """Return an Argon2id hash of the provided plaintext password.

    The hash is safe to persist.  The plaintext is never logged.
    """
    return _ph.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify *plain_password* against an Argon2 hash.

    Returns True on match, False on any mismatch or hash error.
    Exceptions are caught to prevent timing-observable crash differences.
    Passwords and hashes are NEVER logged.
    """
    try:
        return _ph.verify(hashed_password, plain_password)
    except VerifyMismatchError:
        return False
    except (VerificationError, InvalidHashError):
        logger.warning("Password verification failed due to invalid hash format.")
        return False
    except Exception:
        logger.warning("Password verification encountered an unexpected error.", exc_info=True)
        return False


def needs_rehash(hashed_password: str) -> bool:
    """Return True if the hash parameters are outdated and should be upgraded."""
    return _ph.check_needs_rehash(hashed_password)


# ── JWT helpers ────────────────────────────────────────────────────────────────

# Claims embedded in the JWT access token.
# user_id and organization_id are UUIDs serialised as strings.
# role is taken from the database record — never from the client.
_REQUIRED_CLAIMS = frozenset({"sub", "org", "role", "exp", "iat"})


def create_access_token(
    user_id: UUID,
    organization_id: UUID,
    role: str,
) -> str:
    """Create a signed JWT access token.

    Claims:
      sub  – user UUID (string)
      org  – organization UUID (string)
      role – RBAC role (from database, never from client)
      iat  – issued-at (UTC)
      exp  – expiry (UTC, configured via ACCESS_TOKEN_EXPIRE_MINUTES)

    The JWT secret comes exclusively from application settings (environment).
    """
    settings = get_settings()
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=settings.access_token_expire_minutes)

    payload: dict[str, Any] = {
        "sub": str(user_id),
        "org": str(organization_id),
        "role": role,
        "iat": now,
        "exp": expire,
    }

    return jwt.encode(
        payload,
        settings.jwt_secret,
        algorithm=settings.jwt_algorithm,
    )


class TokenValidationError(Exception):
    """Raised when a JWT cannot be validated for any reason."""


def decode_access_token(token: str) -> dict[str, Any]:
    """Decode and validate a JWT access token.

    Returns the claims dict on success.
    Raises TokenValidationError on any failure (expired, malformed, bad sig, …).

    IMPORTANT: Never log the raw token or claim values.
    """
    settings = get_settings()
    try:
        payload: dict[str, Any] = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
        )
    except jwt.ExpiredSignatureError:
        raise TokenValidationError("Token has expired.")
    except jwt.InvalidSignatureError:
        raise TokenValidationError("Token signature is invalid.")
    except jwt.DecodeError:
        raise TokenValidationError("Token is malformed.")
    except jwt.InvalidTokenError as exc:
        raise TokenValidationError(f"Token is invalid: {exc}") from exc

    # Verify that all required claims are present.
    missing = _REQUIRED_CLAIMS - payload.keys()
    if missing:
        raise TokenValidationError(f"Token is missing required claims: {missing}.")

    return payload
