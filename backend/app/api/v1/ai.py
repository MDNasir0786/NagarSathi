"""AI endpoints backed by Claude.

The Claude API key lives only in this backend's environment; it is never
returned in a response and never reaches the React client.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Query
from sqlalchemy import select

from app.auth.dependencies import ActiveUser, AdminUser, DbSession
from app.database.base import utcnow
from app.models import Department
from app.schemas.ai import (
    AdminBriefingResponse,
    AnalyzeComplaintRequest,
    AnalyzeComplaintResponse,
)
from app.schemas.common import ErrorResponse
from app.services import analytics_service, complaint_service
from app.services.claude_service import DEPARTMENT_BY_CATEGORY, claude_service
from app.utils.config import settings

router = APIRouter(prefix="/ai", tags=["AI"])

_ERRORS = {
    401: {"model": ErrorResponse},
    403: {"model": ErrorResponse},
    422: {"model": ErrorResponse},
    429: {"model": ErrorResponse, "description": "AI rate limit exceeded."},
}


@router.post(
    "/analyze-complaint",
    response_model=AnalyzeComplaintResponse,
    summary="Analyse complaint text (no data is stored)",
    responses=_ERRORS,
)
def analyze_complaint(
    payload: AnalyzeComplaintRequest, user: ActiveUser, db: DbSession
) -> AnalyzeComplaintResponse:
    """Preview the AI classification before filing.

    Returns the category, severity, priority score, summary, responsible
    department and suggested action, plus duplicate detection against nearby
    open complaints when coordinates are supplied. Nothing is persisted, so the
    citizen app can call this while the user is still typing the form.

    `status` is `completed` when Claude produced the verdict and `fallback`
    when the deterministic analyser was used instead.
    """
    candidates = []
    if (
        payload.check_duplicates
        and payload.latitude is not None
        and payload.longitude is not None
    ):
        nearby = complaint_service.find_nearby(
            db,
            latitude=payload.latitude,
            longitude=payload.longitude,
            radius_meters=settings.duplicate_radius_meters,
            only_open=True,
            limit=8,
        )
        candidates = complaint_service.build_duplicate_candidates(nearby)

    result = claude_service.analyze_complaint(
        title=payload.title,
        description=payload.description,
        latitude=payload.latitude,
        longitude=payload.longitude,
        address=payload.address,
        image_url=payload.image_url,
        category_hint=payload.category_hint,
        candidates=candidates,
    )

    department = None
    if result.analysis.department:
        department = db.scalar(
            select(Department).where(Department.code == result.analysis.department)
        )

    return AnalyzeComplaintResponse(
        analysis=result.analysis,
        status=result.status,
        model=result.model,
        department_id=department.id if department else None,
        department_name=(
            department.name
            if department
            else DEPARTMENT_BY_CATEGORY[result.analysis.category]
        ),
        duplicate_candidates_considered=result.candidates_considered,
        latency_ms=round(result.latency_ms, 1),
    )


@router.get(
    "/admin-briefing",
    response_model=AdminBriefingResponse,
    summary="AI-generated daily briefing (admin only)",
    responses=_ERRORS,
)
def admin_briefing(
    admin: AdminUser,
    db: DbSession,
    window_hours: Annotated[
        int, Query(ge=1, le=168, description="Reporting window in hours.")
    ] = 24,
) -> AdminBriefingResponse:
    """The morning operations briefing for city officials.

    A metrics snapshot (new vs resolved, backlog by department, SLA breaches,
    rising categories, ward concentrations, city-health components) is computed
    from the database and handed to Claude, which returns a markdown briefing
    plus ranked priorities and a watchlist. If Claude is unavailable, a
    deterministic data-only briefing is returned with `status: fallback`.
    """
    metrics = analytics_service.briefing_metrics(db, window_hours=window_hours)
    result = claude_service.generate_admin_briefing(metrics, window_hours=window_hours)

    return AdminBriefingResponse(
        generated_at=utcnow(),
        window_hours=window_hours,
        headline=result.headline,
        briefing=result.briefing,
        priorities=result.priorities,
        watchlist=result.watchlist,
        city_health_score=metrics.get("city_health_score", 0.0),
        status=result.status,
        model=result.model,
        metrics_snapshot=metrics,
    )
