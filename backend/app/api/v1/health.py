"""Health check endpoint – GET /api/v1/health.

Reports application availability and, when PostgreSQL is reachable,
database connectivity status.  No sensitive configuration details are
exposed in the response body.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/health", tags=["health"])


@router.get(
    "",
    summary="Health check",
    description="Returns application and database connectivity status.",
    response_description="Health status payload.",
)
async def health_check() -> JSONResponse:
    """Return service health.  Attempts a lightweight database probe."""
    status: dict[str, object] = {
        "status": "ok",
        "service": "voice-cloning-detection-backend",
    }
    http_status = 200

    # Lazy import to avoid import-time failures when DB is not yet available.
    try:
        from app.database import check_database_connection  # noqa: PLC0415

        db_ok = check_database_connection()
        status["database"] = "ok" if db_ok else "unavailable"
        if not db_ok:
            status["status"] = "degraded"
            http_status = 503
    except Exception:
        logger.warning("Health check: database probe failed.", exc_info=True)
        status["database"] = "unavailable"
        status["status"] = "degraded"
        http_status = 503

    return JSONResponse(content=status, status_code=http_status)
