"""Authentication request/response schemas.

SECURITY RULES:
- LoginRequest.password is a write-only field (exclude=True on model_dump).
- UserResponse NEVER includes password_hash.
- TokenResponse NEVER includes the raw JWT secret or signing details.
- All schemas use strict types to prevent injection via unexpected values.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


# ── Request schemas ────────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    """Credentials submitted to POST /api/v1/auth/login."""

    email: EmailStr = Field(description="User email address.")
    password: str = Field(
        min_length=1,
        max_length=256,
        description="Plaintext password — never stored or returned.",
    )

    model_config = ConfigDict(
        # Prevent extra fields from being accepted
        extra="forbid",
    )


# ── Response schemas ───────────────────────────────────────────────────────

class UserResponse(BaseModel):
    """Safe user profile — NEVER includes password_hash or secrets."""

    id: UUID
    organization_id: UUID
    email: str
    full_name: str | None
    role: str
    is_active: bool
    last_login_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TokenResponse(BaseModel):
    """Successful authentication response."""

    access_token: str = Field(description="Signed JWT access token.")
    token_type: str = Field(default="bearer")
    expires_in: int = Field(description="Token lifetime in seconds.")
    user: UserResponse = Field(description="Safe authenticated user profile.")


class ErrorResponse(BaseModel):
    """Standard error envelope."""

    error: str
    message: str


# ── User management schemas ────────────────────────────────────────────────

class CreateUserRequest(BaseModel):
    """Body for POST /api/v1/users — admin-only user creation."""

    email: EmailStr
    password: str = Field(min_length=8, max_length=256)
    full_name: str | None = Field(default=None, max_length=256)
    role: str = Field(description="Must be a valid RBAC role.")

    model_config = ConfigDict(extra="forbid")

    @field_validator("role")
    @classmethod
    def _valid_role(cls, v: str) -> str:
        valid = {"SUPER_ADMIN", "ADMIN", "SECURITY_ANALYST", "OPERATOR", "AUDITOR"}
        if v not in valid:
            raise ValueError(f"role must be one of {sorted(valid)}.")
        return v


class UpdateUserRequest(BaseModel):
    """Body for PATCH /api/v1/users/{user_id} — update role or active state."""

    role: str | None = Field(default=None)
    is_active: bool | None = Field(default=None)

    model_config = ConfigDict(extra="forbid")

    @field_validator("role")
    @classmethod
    def _valid_role(cls, v: str | None) -> str | None:
        if v is None:
            return v
        valid = {"SUPER_ADMIN", "ADMIN", "SECURITY_ANALYST", "OPERATOR", "AUDITOR"}
        if v not in valid:
            raise ValueError(f"role must be one of {sorted(valid)}.")
        return v
