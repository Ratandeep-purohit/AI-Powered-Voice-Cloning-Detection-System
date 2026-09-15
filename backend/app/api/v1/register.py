"""Initial organization account registration for the MVP."""

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.v1.auth import REFRESH_COOKIE, _audit, _issue_tokens
from app.config import get_settings
from app.core.security import hash_password
from app.database import get_db
from app.models.organization import Organization
from app.models.user import User
from app.schemas.auth import RegisterRequest, TokenResponse

router = APIRouter(prefix="/register", tags=["registration"])


@router.post("", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(payload: RegisterRequest, request: Request, response: Response, db: Session = Depends(get_db)) -> TokenResponse:
    if payload.role != "ADMIN":
        raise HTTPException(status_code=400, detail="Initial account role must be ADMIN")
    if db.scalar(select(User).where(User.email == payload.email.lower())):
        raise HTTPException(status_code=409, detail="An account with this email already exists")
    if db.scalar(select(Organization).where(Organization.slug == payload.organization_slug)):
        raise HTTPException(status_code=409, detail="Organization slug already exists")

    organization = Organization(name=payload.organization_name.strip(), slug=payload.organization_slug)
    db.add(organization)
    db.flush()
    user = User(
        organization_id=organization.id,
        email=payload.email.lower(),
        password_hash=hash_password(payload.password),
        full_name=None,
        role="ADMIN",
        is_active=True,
    )
    db.add(user)
    db.flush()
    access, refresh = _issue_tokens(user, db)
    _audit(db, user, "AUTHENTICATION", "ACCOUNT_REGISTERED", request)
    settings = get_settings()
    response.set_cookie(REFRESH_COOKIE, refresh, httponly=True, secure=not settings.is_development, samesite="lax", max_age=settings.refresh_token_expire_days * 86400, path="/api/v1/auth")
    return TokenResponse(access_token=access, expires_in=settings.access_token_expire_minutes * 60, user=user)
