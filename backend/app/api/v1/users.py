"""User management APIs.

Requires ADMIN or SUPER_ADMIN role.
Enforces organization tenant isolation — admins can only manage users
within their own organization.
"""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.audit import audit_user_created, audit_user_updated, audit_authorization_denial
from app.core.dependencies import CurrentUser, assert_same_organization, require_admin_or_superadmin
from app.core.security import hash_password
from app.database import get_db
from app.models.user import User
from app.schemas.auth import CreateUserRequest, UpdateUserRequest, UserResponse

router = APIRouter(prefix="/users", tags=["User Management"])


@router.post(
    "",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_admin_or_superadmin)],
)
def create_user(
    request: Request,
    payload: CreateUserRequest,
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> UserResponse:
    """Create a new user within the authenticated admin's organization."""
    # Check if email already exists
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email already exists.",
        )

    # Hash the password
    hashed = hash_password(payload.password)

    new_user = User(
        organization_id=current_user.organization_id,
        email=payload.email,
        password_hash=hashed,
        full_name=payload.full_name,
        role=payload.role,
        is_active=True,
    )
    
    db.add(new_user)
    db.flush()

    # Audit log
    audit_user_created(
        db,
        actor_id=current_user.id,
        new_user_id=new_user.id,
        organization_id=current_user.organization_id,
        ip_address=request.client.host if request.client else None,
    )

    db.commit()
    db.refresh(new_user)

    return UserResponse.model_validate(new_user)


@router.get(
    "",
    response_model=list[UserResponse],
    dependencies=[Depends(require_admin_or_superadmin)],
)
def list_users(
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
    skip: int = 0,
    limit: int = 100,
) -> list[UserResponse]:
    """List users within the authenticated admin's organization."""
    users = (
        db.query(User)
        .filter(User.organization_id == current_user.organization_id)
        .order_by(User.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return [UserResponse.model_validate(u) for u in users]


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    dependencies=[Depends(require_admin_or_superadmin)],
)
def get_user(
    request: Request,
    user_id: UUID,
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> UserResponse:
    """Retrieve a specific user."""
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    # Tenant isolation validation
    try:
        assert_same_organization(current_user, user.organization_id)
    except HTTPException:
        audit_authorization_denial(
            db,
            user_id=current_user.id,
            organization_id=current_user.organization_id,
            resource=f"user:{user_id}",
            ip_address=request.client.host if request.client else None,
        )
        db.commit()
        raise

    return UserResponse.model_validate(user)


@router.patch(
    "/{user_id}",
    response_model=UserResponse,
    dependencies=[Depends(require_admin_or_superadmin)],
)
def update_user(
    request: Request,
    user_id: UUID,
    payload: UpdateUserRequest,
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> UserResponse:
    """Update a user's role or active status."""
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    # Tenant isolation validation
    try:
        assert_same_organization(current_user, user.organization_id)
    except HTTPException:
        audit_authorization_denial(
            db,
            user_id=current_user.id,
            organization_id=current_user.organization_id,
            resource=f"user:{user_id}",
            ip_address=request.client.host if request.client else None,
        )
        db.commit()
        raise

    # Do not allow users to disable themselves
    if payload.is_active is False and user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot disable your own account.",
        )

    # Apply changes
    changes = {}
    if payload.role is not None and payload.role != user.role:
        changes["role"] = {"old": user.role, "new": payload.role}
        user.role = payload.role
    if payload.is_active is not None and payload.is_active != user.is_active:
        changes["is_active"] = {"old": user.is_active, "new": payload.is_active}
        user.is_active = payload.is_active

    if changes:
        audit_user_updated(
            db,
            actor_id=current_user.id,
            target_user_id=user.id,
            organization_id=current_user.organization_id,
            changes=changes,
            ip_address=request.client.host if request.client else None,
        )
        db.commit()
        db.refresh(user)

    return UserResponse.model_validate(user)
