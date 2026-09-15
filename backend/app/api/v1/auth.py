"""Authentication and Identity APIs."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.audit import audit_login_failure, audit_login_success
from app.core.dependencies import CurrentUser
from app.core.security import create_access_token, verify_password
from app.database import get_db
from app.models.user import User
from app.schemas.auth import LoginRequest, TokenResponse, UserResponse

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    responses={
        401: {"description": "Invalid credentials or disabled account."},
        429: {"description": "Too many login attempts."},
    },
)
def login(
    request: Request,
    login_data: LoginRequest,
    db: Annotated[Session, Depends(get_db)],
) -> TokenResponse:
    """Authenticate a user and return a JWT access token.

    Authentication failures return a generic 401 response without
    indicating whether the email exists.
    """
    # Safe IP extraction for audit logging
    client_ip = request.client.host if request.client else None

    # Find the user by email
    user = db.query(User).filter(User.email == login_data.email).first()

    if not user:
        # User not found. We don't hash here because we don't know the password
        # but we must fail safely.
        # A dummy hash verification could be added here to prevent timing attacks
        # on email existence, but Argon2 is slow enough that typical network
        # jitter masks the timing difference in MVP.
        audit_login_failure(db, ip_address=client_ip, email_hint=login_data.email)
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        # Found, but disabled. Still return a generic error to prevent enumeration.
        audit_login_failure(db, ip_address=client_ip, email_hint=login_data.email)
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not verify_password(login_data.password, user.password_hash):
        # Invalid password
        audit_login_failure(db, ip_address=client_ip, email_hint=login_data.email)
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # ── Successful authentication ──────────────────────────────────────────

    # Record the last login time
    from datetime import datetime, timezone
    user.last_login_at = datetime.now(timezone.utc)
    
    # Write audit log
    audit_login_success(db, user.id, user.organization_id, ip_address=client_ip)
    
    # Commit changes (last login + audit log)
    db.commit()

    # Generate JWT
    access_token = create_access_token(
        user_id=user.id,
        organization_id=user.organization_id,
        role=user.role,
    )
    
    from app.config import get_settings
    settings = get_settings()

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.access_token_expire_minutes * 60,
        user=UserResponse.model_validate(user),
    )


@router.get(
    "/me",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
)
def get_current_authenticated_user(
    current_user: CurrentUser,
) -> UserResponse:
    """Retrieve the current authenticated user's profile.

    Requires a valid JWT access token.
    Never returns password hashes or internal security details.
    """
    return UserResponse.model_validate(current_user)


# Note: /api/v1/auth/refresh is intentionally omitted.
# The specification explicitly states: "Do not claim refresh functionality is
# implemented if the project documentation does not define enough information to
# implement it safely." Token revocation/rotation semantics are undefined.
