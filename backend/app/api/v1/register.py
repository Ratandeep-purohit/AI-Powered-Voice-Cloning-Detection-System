"""Public registration endpoint.

Allows new organizations + admin users to self-register.
This is needed for the frontend signup flow.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator
from sqlalchemy.orm import Session

from app.core.security import create_access_token, hash_password
from app.database import get_db
from app.models.organization import Organization
from app.models.user import User
from app.schemas.auth import TokenResponse, UserResponse

router = APIRouter(prefix="/auth", tags=["Authentication"])


class RegisterRequest(BaseModel):
    """Public self-registration payload."""

    organization_name: str = Field(min_length=2, max_length=128)
    email: EmailStr
    password: str = Field(min_length=8, max_length=256)
    full_name: str | None = Field(default=None, max_length=256)

    model_config = ConfigDict(extra="forbid")

    @field_validator("password")
    @classmethod
    def _password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters.")
        return v


@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
)
def register(
    request: Request,
    payload: RegisterRequest,
    db: Annotated[Session, Depends(get_db)],
) -> TokenResponse:
    """Create a new organization and SUPER_ADMIN user.

    Returns a JWT token immediately so the user is logged in after registration.
    Password hash is never returned.
    """
    # Check email uniqueness
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists.",
        )

    # Create organisation
    import re
    slug_base = re.sub(r"[^a-z0-9]+", "-", payload.organization_name.lower()).strip("-")
    # Ensure slug uniqueness
    slug = slug_base
    counter = 1
    while db.query(Organization).filter(Organization.slug == slug).first():
        slug = f"{slug_base}-{counter}"
        counter += 1

    org = Organization(name=payload.organization_name, slug=slug)
    db.add(org)
    db.flush()

    # Create user as SUPER_ADMIN of their own org
    user = User(
        organization_id=org.id,
        email=payload.email,
        password_hash=hash_password(payload.password),
        full_name=payload.full_name,
        role="SUPER_ADMIN",
        is_active=True,
    )
    db.add(user)
    db.flush()

    db.commit()
    db.refresh(user)

    # Issue JWT immediately — user is now logged in
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
