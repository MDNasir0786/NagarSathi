"""Bhopal CivicAI — FastAPI application entry point.

Run locally:
    uvicorn app.main:app --reload --port 8000

Swagger UI: http://localhost:8000/docs
ReDoc:      http://localhost:8000/redoc
OpenAPI:    http://localhost:8000/openapi.json
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from app import __version__
from app.api.v1.router import api_router
from app.database.init_db import init_database
from app.database.session import check_database_connection
from app.schemas.common import HealthResponse, ReadinessResponse
from app.utils.config import settings
from app.utils.errors import register_exception_handlers
from app.utils.logging import (
    RateLimitMiddleware,
    RequestContextMiddleware,
    configure_logging,
)

logger = logging.getLogger(__name__)

DESCRIPTION = """
Backend for **Bhopal CivicAI** — an AI-assisted civic grievance platform for
Bhopal, Madhya Pradesh.

### How authentication works
1. The React client signs users up / in with **Supabase Auth**.
2. It sends the resulting access token as `Authorization: Bearer <token>`.
3. This API verifies the JWT, mirrors the user into `profiles` on first call,
   and authorises using the **role stored in our database** — never a role
   claimed by the token.

**Roles:** `citizen` (default for every signup) and `admin`. The admin role can
never be obtained through signup; it comes from the backend `ADMIN_EMAILS`
allow-list, an existing admin, or the operator CLI.

### Using Swagger
Click **Authorize**, paste a Supabase access token, and every request will
carry it. `GET /api/v1/auth/me` is the quickest way to confirm it worked.

### AI
Complaint triage and the daily briefing run on the Claude API. The API key is
backend-only. If Claude is unreachable, endpoints degrade to a deterministic
analyser and report `status: "fallback"` rather than failing.
"""

TAGS_METADATA = [
    {"name": "Authentication", "description": "Verify Supabase tokens, provision profiles."},
    {"name": "Profile", "description": "Citizen profile management."},
    {"name": "Complaints", "description": "File, browse, track and confirm complaints."},
    {"name": "Admin", "description": "Municipal staff operations. Requires the admin role."},
    {"name": "Analytics", "description": "Hotspots, trends, category and department analytics."},
    {"name": "AI", "description": "Claude-powered analysis and the daily admin briefing."},
    {"name": "System", "description": "Health and readiness probes."},
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Prepare the database on boot and log the effective configuration."""
    configure_logging()
    logger.info(
        "starting %s v%s (env=%s, db=%s)",
        settings.app_name,
        __version__,
        settings.app_env,
        "sqlite" if settings.is_sqlite else "postgres",
    )
    if not settings.auth_configured:
        logger.warning(
            "Supabase auth is NOT configured — set SUPABASE_JWT_SECRET or SUPABASE_URL. "
            "All authenticated endpoints will return 503."
        )
    if not settings.claude_configured:
        logger.warning(
            "Claude is NOT configured (ANTHROPIC_API_KEY missing or AI_ENABLED=false) — "
            "complaint analysis will use the deterministic fallback analyser."
        )
    try:
        init_database()
    except Exception:
        # Don't crash the process: /ready will report the failure and a
        # container orchestrator can restart or hold traffic.
        logger.exception("database initialisation failed")

    yield

    logger.info("shutting down %s", settings.app_name)


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        description=DESCRIPTION,
        version=__version__,
        lifespan=lifespan,
        openapi_tags=TAGS_METADATA,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        swagger_ui_parameters={
            "persistAuthorization": True,
            "displayRequestDuration": True,
            "docExpansion": "none",
        },
        contact={"name": "Bhopal CivicAI", "email": "support@bhopalcivicai.in"},
        license_info={"name": "MIT"},
    )

    # --- middleware (outermost first) -------------------------------------
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PATCH", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
        expose_headers=["X-Request-ID", "X-Response-Time-ms"],
        max_age=600,
    )
    app.add_middleware(GZipMiddleware, minimum_size=1024)
    app.add_middleware(RateLimitMiddleware)
    app.add_middleware(RequestContextMiddleware)

    register_exception_handlers(app)
    app.include_router(api_router, prefix=settings.api_v1_prefix)

    # --- system routes ----------------------------------------------------
    @app.get("/health", response_model=HealthResponse, tags=["System"], summary="Liveness")
    def health() -> HealthResponse:
        """Liveness probe — does not touch the database."""
        return HealthResponse(
            status="ok",
            app=settings.app_name,
            version=__version__,
            environment=settings.app_env,
        )

    @app.get(
        "/ready", response_model=ReadinessResponse, tags=["System"], summary="Readiness"
    )
    def ready() -> ReadinessResponse:
        """Readiness probe — verifies database connectivity and configuration."""
        database_ok = check_database_connection()
        return ReadinessResponse(
            status="ready" if database_ok else "degraded",
            database=database_ok,
            auth_configured=settings.auth_configured,
            ai_configured=settings.claude_configured,
        )

    @app.get("/", include_in_schema=False)
    def root() -> dict:
        return {
            "name": settings.app_name,
            "version": __version__,
            "docs": "/docs",
            "health": "/health",
            "api": settings.api_v1_prefix,
        }

    return app


app = create_app()
