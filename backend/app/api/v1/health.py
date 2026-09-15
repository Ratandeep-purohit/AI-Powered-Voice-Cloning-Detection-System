import logging

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

from app.db.session import check_database_connection

router = APIRouter(tags=["health"])
logger = logging.getLogger(__name__)


@router.get("/health")
def health() -> JSONResponse:
    database_ok = check_database_connection()
    payload = {
        "status": "healthy" if database_ok else "degraded",
        "service": "api",
        "database": "connected" if database_ok else "unavailable",
    }
    if not database_ok:
        logger.error("Database health check failed")
    return JSONResponse(
        status_code=status.HTTP_200_OK if database_ok else status.HTTP_503_SERVICE_UNAVAILABLE,
        content=payload,
    )
