"""Audit logging service.

Creates append-oriented AuditLog records for security-relevant events.

SECURITY RULES:
- Audit records NEVER contain passwords, password hashes, JWTs, or secrets.
- Audit logging failures are caught and logged — they must NOT interrupt
  the authentication or authorization flow.
- IP addresses are recorded where available (future: GDPR review for PII).
"""

from __future__ import annotations

import logging
from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog

logger = logging.getLogger(__name__)


def record_audit_event(
    db: Session,
    *,
    event_type: str,
    action: str,
    organization_id: UUID | None = None,
    user_id: UUID | None = None,
    entity_type: str | None = None,
    entity_id: UUID | None = None,
    ip_address: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> None:
    """Insert an audit log record.

    This function MUST NOT be called with passwords, hashes, JWTs, or
    Authorization header values in *metadata*.

    If writing fails, the error is logged and silently swallowed so that
    the audit logging itself never causes an authentication response to fail.
    """
    try:
        entry = AuditLog(
            organization_id=organization_id,
            user_id=user_id,
            event_type=event_type,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            ip_address=ip_address,
            event_metadata=metadata,
        )
        db.add(entry)
        db.flush()  # Assign the PK without committing — caller commits.
    except Exception:
        logger.error(
            "Failed to write audit log: event_type=%s action=%s",
            event_type,
            action,
            exc_info=True,
        )


# ── Named audit event helpers ──────────────────────────────────────────────

def audit_login_success(
    db: Session,
    user_id: UUID,
    organization_id: UUID,
    ip_address: str | None = None,
) -> None:
    """Record a successful login event."""
    record_audit_event(
        db,
        event_type="AUTH",
        action="LOGIN_SUCCESS",
        organization_id=organization_id,
        user_id=user_id,
        entity_type="user",
        entity_id=user_id,
        ip_address=ip_address,
    )


def audit_login_failure(
    db: Session,
    ip_address: str | None = None,
    email_hint: str | None = None,
) -> None:
    """Record a failed login attempt.

    email_hint is a safe hint (e.g., a hash of the email) for correlation only.
    The raw email must NOT be stored in metadata to avoid enumeration leaks.
    """
    record_audit_event(
        db,
        event_type="AUTH",
        action="LOGIN_FAILURE",
        ip_address=ip_address,
        metadata={"hint": email_hint} if email_hint else None,
    )


def audit_authorization_denial(
    db: Session,
    user_id: UUID,
    organization_id: UUID,
    resource: str,
    ip_address: str | None = None,
) -> None:
    """Record an authorization denial event."""
    record_audit_event(
        db,
        event_type="AUTHZ",
        action="ACCESS_DENIED",
        organization_id=organization_id,
        user_id=user_id,
        entity_type="resource",
        ip_address=ip_address,
        metadata={"resource": resource},
    )


def audit_user_created(
    db: Session,
    actor_id: UUID,
    new_user_id: UUID,
    organization_id: UUID,
    ip_address: str | None = None,
) -> None:
    """Record that an admin created a new user."""
    record_audit_event(
        db,
        event_type="USER_MANAGEMENT",
        action="USER_CREATED",
        organization_id=organization_id,
        user_id=actor_id,
        entity_type="user",
        entity_id=new_user_id,
        ip_address=ip_address,
    )


def audit_user_updated(
    db: Session,
    actor_id: UUID,
    target_user_id: UUID,
    organization_id: UUID,
    changes: dict[str, Any],
    ip_address: str | None = None,
) -> None:
    """Record that an admin updated a user (role or active state)."""
    # Do not include sensitive values in changes metadata.
    safe_changes = {k: v for k, v in changes.items() if k not in {"password", "password_hash"}}
    record_audit_event(
        db,
        event_type="USER_MANAGEMENT",
        action="USER_UPDATED",
        organization_id=organization_id,
        user_id=actor_id,
        entity_type="user",
        entity_id=target_user_id,
        ip_address=ip_address,
        metadata={"changes": safe_changes},
    )
