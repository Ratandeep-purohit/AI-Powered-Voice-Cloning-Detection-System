"""Authentication endpoints for Phase 02."""

from datetime import datetime, timedelta, timezone
import hashlib

import jwt
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.config import get_settings
from app.core.dependencies import get_current_user
from app.core.security import create_access_token, create_refresh_token, decode_refresh_token, hash_password, verify_password
from app.database import get_db
from app.models.audit_log import AuditLog
from app.models.refresh_token import RefreshToken
from app.models.user import User
from app.schemas.auth import LoginRequest, TokenResponse, UserProfile

router = APIRouter(prefix="/auth", tags=["authentication"])
REFRESH_COOKIE = "voiceguard_refresh"


def _token_hash(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _issue_tokens(user: User, db: Session) -> tuple[str, str]:
    settings = get_settings()
    access = create_access_token(str(user.id), str(user.organization_id), user.role)
    refresh = create_refresh_token(str(user.id), str(user.organization_id), user.role)
    db.add(RefreshToken(
        user_id=user.id,
        organization_id=user.organization_id,
        token_hash=_token_hash(refresh),
        expires_at=datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_expire_days),
    ))
    return access, refresh


def _audit(db: Session, user: User | None, event_type: str, action: str, request: Request) -> None:
    db.add(AuditLog(
        organization_id=user.organization_id if user else None,
        user_id=user.id if user else None,
        event_type=event_type,
        action=action,
        ip_address=request.client.host if request.client else None,
    ))


@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest, request: Request, response: Response, db: Session = Depends(get_db)) -> TokenResponse:
    user = db.scalar(select(User).where(User.email == payload.email.lower()))
    if user is None or not user.is_active or not verify_password(payload.password, user.password_hash):
        _audit(db, user, "AUTHENTICATION", "LOGIN_FAILED", request)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    user.last_login_at = datetime.now(timezone.utc)
    access, refresh = _issue_tokens(user, db)
    _audit(db, user, "AUTHENTICATION", "LOGIN_SUCCESS", request)
    settings = get_settings()
    response.set_cookie(REFRESH_COOKIE, refresh, httponly=True, secure=not settings.is_development, samesite="lax", max_age=settings.refresh_token_expire_days * 86400, path="/api/v1/auth")
    return TokenResponse(access_token=access, expires_in=settings.access_token_expire_minutes * 60, user=user)


@router.get("/me", response_model=UserProfile)
async def me(current_user: User = Depends(get_current_user)) -> User:
    return current_user


@router.post("/refresh", response_model=TokenResponse)
async def refresh(request: Request, response: Response, db: Session = Depends(get_db)) -> TokenResponse:
    raw = request.cookies.get(REFRESH_COOKIE)
    if not raw:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token required")
    try:
        payload = decode_refresh_token(raw)
        user_id = payload["sub"]
    except (jwt.PyJWTError, KeyError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired refresh token") from None

    stored = db.scalar(select(RefreshToken).where(RefreshToken.token_hash == _token_hash(raw), RefreshToken.revoked_at.is_(None)))
    user = db.scalar(select(User).where(User.id == user_id, User.is_active.is_(True)))
    if stored is None or not stored.is_active or user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired refresh token")

    stored.revoked_at = datetime.now(timezone.utc)
    access, new_refresh = _issue_tokens(user, db)
    settings = get_settings()
    response.set_cookie(REFRESH_COOKIE, new_refresh, httponly=True, secure=not settings.is_development, samesite="lax", max_age=settings.refresh_token_expire_days * 86400, path="/api/v1/auth")
    return TokenResponse(access_token=access, expires_in=settings.access_token_expire_minutes * 60, user=user)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(request: Request, response: Response, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> None:
    raw = request.cookies.get(REFRESH_COOKIE)
    if raw:
        db.execute(update(RefreshToken).where(RefreshToken.token_hash == _token_hash(raw), RefreshToken.user_id == current_user.id).values(revoked_at=datetime.now(timezone.utc)))
    _audit(db, current_user, "AUTHENTICATION", "LOGOUT", request)
    response.delete_cookie(REFRESH_COOKIE, path="/api/v1/auth")
    response.status_code = status.HTTP_204_NO_CONTENT
