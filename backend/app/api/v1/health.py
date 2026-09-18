"""Health endpoints for liveness and dependency-aware readiness."""

from __future__ import annotations

import logging

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.database import check_database_connection

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/health", tags=["health"])

SERVICE_NAME = "voice-cloning-detection-backend"


@router.get("", summary="Health check")
async def health_check() -> JSONResponse:
    """Return application and database connectivity status."""
    db_ok = check_database_connection()
    status = {"status": "ok" if db_ok else "degraded", "service": SERVICE_NAME, "database": "ok" if db_ok else "unavailable"}
    return JSONResponse(content=status, status_code=200 if db_ok else 503)


@router.get("/live", summary="Liveness probe")
async def liveness() -> JSONResponse:
    """Return 200 when the application process is alive."""
    return JSONResponse(content={"status": "ok", "service": SERVICE_NAME}, status_code=200)


@router.get("/ready", summary="Readiness probe")
async def readiness() -> JSONResponse:
    """Return 200 only when the application can reach its database."""
    db_ok = check_database_connection()
    status = {"status": "ready" if db_ok else "not_ready", "service": SERVICE_NAME, "database": "ok" if db_ok else "unavailable"}
    return JSONResponse(content=status, status_code=200 if db_ok else 503)
