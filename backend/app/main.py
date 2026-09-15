"""FastAPI application entry point."""

from __future__ import annotations

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.api.v1.auth import router as auth_router
from app.api.v1.health import router as health_router
from app.api.v1.register import router as register_router
from app.api.v1.users import router as users_router
from app.config import get_settings
from app.core.exceptions import unhandled_exception_handler
from app.core.logging import configure_logging

settings = get_settings()
configure_logging(settings.log_level)
logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    limiter = Limiter(key_func=get_remote_address)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
        logger.info("Application starting up | env=%s | host=%s | port=%d", settings.app_env, settings.app_host, settings.app_port)
        logger.info("Database: %s", settings.safe_database_url())
        yield
        logger.info("Application shutting down.")

    _app = FastAPI(
        title="AI-Powered Voice Cloning Detection & Prevention System",
        description="Real-time detection and prevention of voice cloning impersonation attacks.",
        version="0.2.0",
        lifespan=lifespan,
        docs_url="/api/docs" if settings.is_development else None,
        redoc_url="/api/redoc" if settings.is_development else None,
        openapi_url="/api/openapi.json" if settings.is_development else None,
    )
    _app.state.limiter = limiter
    _app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    _app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://localhost:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    _app.add_exception_handler(Exception, unhandled_exception_handler)
    _app.include_router(health_router, prefix="/api/v1")
    _app.include_router(auth_router, prefix="/api/v1")
    _app.include_router(register_router, prefix="/api/v1")
    _app.include_router(users_router, prefix="/api/v1")
    return _app


app = create_app()
