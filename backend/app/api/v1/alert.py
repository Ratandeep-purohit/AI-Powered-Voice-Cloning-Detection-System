"""Phase 09 alert endpoints."""
from __future__ import annotations

from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, require_roles
from app.database import get_db
from app.models.alert import VALID_ALERT_SEVERITIES if False else Alert
