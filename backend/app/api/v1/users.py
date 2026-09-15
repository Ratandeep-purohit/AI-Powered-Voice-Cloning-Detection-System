"""Administrative user-management endpoints for Phase 02."""

import uuid
from pydantic import BaseModel, Field, EmailStr
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.dependencies import require_roles
from app.core.security import hash_password
from app.database import get_db
from app.models.user import User, VALID_ROLES
from app.schemas.auth import UserProfile

router = APIRouter(prefix="/users", tags=["users"])


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str | None = Field(default=None, max_length=200)
    role: str


class UserUpdate(BaseModel):
    role: str | None = None
    is_active: bool | None = None


@router.get("", response_model=list[UserProfile])
def list_users(current_user: User = Depends(require_roles("ADMIN", "SUPER_ADMIN")), db: Session = Depends(get_db)) -> list[User]:
    return list(db.scalars(select(User).where(User.organization_id == current_user.organization_id).order_by(User.created_at)).all())


@router.get("/{user_id}", response_model=UserProfile)
def get_user(user_id: uuid.UUID, current_user: User = Depends(require_roles("ADMIN", "SUPER_ADMIN")), db: Session = Depends(get_db)) -> User:
    user = db.scalar(select(User).where(User.id == user_id, User.organization_id == current_user.organization_id))
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.post("", response_model=UserProfile, status_code=status.HTTP_201_CREATED)
def create_user(payload: UserCreate, current_user: User = Depends(require_roles("ADMIN", "SUPER_ADMIN")), db: Session = Depends(get_db)) -> User:
    if payload.role not in VALID_ROLES:
        raise HTTPException(status_code=422, detail="Invalid role")
    if db.scalar(select(User).where(User.email == payload.email.lower())):
        raise HTTPException(status_code=409, detail="An account with this email already exists")
    user = User(organization_id=current_user.organization_id, email=payload.email.lower(), password_hash=hash_password(payload.password), full_name=payload.full_name, role=payload.role, is_active=True)
    db.add(user)
    db.flush()
    return user


@router.patch("/{user_id}", response_model=UserProfile)
def update_user(user_id: uuid.UUID, payload: UserUpdate, current_user: User = Depends(require_roles("ADMIN", "SUPER_ADMIN")), db: Session = Depends(get_db)) -> User:
    user = db.scalar(select(User).where(User.id == user_id, User.organization_id == current_user.organization_id))
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    if payload.role is not None:
        if payload.role not in VALID_ROLES:
            raise HTTPException(status_code=422, detail="Invalid role")
        user.role = payload.role
    if payload.is_active is not None:
        user.is_active = payload.is_active
    return user
