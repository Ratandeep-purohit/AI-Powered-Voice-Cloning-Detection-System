"""FastAPI authentication and authorization dependencies.

These are the reusable injectable dependencies that protect endpoints.

Flow:
  Request → Authorization header → JWT extraction → JWT validation
  → User DB lookup → Account state check → Authenticated context

RBAC dependencies are composable:
  require_roles([ADMIN, SUPER_ADMIN]) returns a dependency that
  rejects authenticated users whose role is not in the list.

TENANT ISOLATION:
  Organization is always resolved from the database-backed user record.
  Client-supplied organization_id / role values are NEVER trusted.
"""

from __future__ import annotations

import logging
from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.security import TokenValidationError, decode_access_token
from app.database import get_db
from app.models.user import User

logger = logging.getLogger(__name__)

# ── Bearer token extractor ─────────────────────────────────────────────────

_bearer = HTTPBearer(auto_error=True)


# ── Helper: current authenticated user ────────────────────────────────────

def _get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(_bearer)],
    db: Annotated[object, Depends(get_db)],
) -> User:
    """Resolve the current authenticated user from the JWT.

    Raises 401 for any authentication problem.
    Raises 401 (not 404) if the user is not found — avoids user-enumeration.
    """
    from sqlalchemy.orm import Session

    db_session: Session = db  # type: ignore[assignment]
    token = credentials.credentials

    # ── 1. Decode and validate the JWT ────────────────────────────────────
    try:
        payload = decode_access_token(token)
    except TokenValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials are invalid or expired.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    # ── 2. Extract user_id claim (validated inside decode_access_token) ───
    raw_sub = payload.get("sub")
    try:
        user_id = UUID(str(raw_sub))
    except (TypeError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials are invalid.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # ── 3. Load the user from the database (never trust JWT role/org) ─────
    user: User | None = db_session.get(User, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials are invalid.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # ── 4. Validate account state ─────────────────────────────────────────
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account is disabled.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


# ── Public dependency ──────────────────────────────────────────────────────

def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(_bearer)],
    db: Annotated[object, Depends(get_db)],
) -> User:
    """FastAPI dependency: resolve the authenticated User or raise 401."""
    return _get_current_user(credentials, db)


CurrentUser = Annotated[User, Depends(get_current_user)]


# ── RBAC dependency factory ────────────────────────────────────────────────

def require_roles(allowed_roles: list[str]):
    """Return a FastAPI dependency that requires one of *allowed_roles*.

    Uses server-side user.role — client cannot override this.
    Raises 403 if the authenticated user's role is not in allowed_roles.
    Default-deny: if allowed_roles is empty, all authenticated users are denied.
    """
    def _check_role(current_user: Annotated[User, Depends(get_current_user)]) -> User:
        if current_user.role not in allowed_roles:
            logger.info(
                "Authorization denied: user %s role=%s required one of %s",
                current_user.id,
                current_user.role,
                allowed_roles,
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions for this operation.",
            )
        return current_user

    return _check_role


# ── Convenience role dependencies ──────────────────────────────────────────

def require_admin_or_superadmin(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """Dependency: ADMIN or SUPER_ADMIN only."""
    if current_user.role not in ("ADMIN", "SUPER_ADMIN"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions for this operation.",
        )
    return current_user


def require_superadmin(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """Dependency: SUPER_ADMIN only."""
    if current_user.role != "SUPER_ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions for this operation.",
        )
    return current_user


# ── Tenant isolation helper ────────────────────────────────────────────────

def assert_same_organization(
    current_user: User,
    resource_organization_id: UUID,
) -> None:
    """Raise 404 if *resource_organization_id* does not match the authenticated user's org.

    Uses 404 (not 403) to avoid revealing whether a resource exists
    in another organization — per API.md § 15.
    SUPER_ADMIN is still constrained to their own organisation at this layer;
    cross-organisation access requires an explicit future design decision.
    """
    if current_user.organization_id != resource_organization_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resource not found.",
        )
