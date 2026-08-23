"""Smart-city analytics endpoints.

Aggregate, non-identifying views are available to any signed-in user (the
citizen app renders the hotspot map from these). Department performance is
admin-only because it evaluates municipal staff.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Query

from app.api.deps import WindowDays
from app.auth.dependencies import ActiveUser, AdminUser, DbSession
from app.models.enums import ComplaintCategory
from app.schemas.analytics import (
    CategoryStatsResponse,
    CityHealthScore,
    DepartmentPerformanceResponse,
    HotspotResponse,
    TrendsResponse,
)
from app.schemas.common import ErrorResponse
from app.services import analytics_service

router = APIRouter(prefix="/analytics", tags=["Analytics"])

_ERRORS = {401: {"model": ErrorResponse}, 403: {"model": ErrorResponse}}


@router.get(
    "/hotspots",
    response_model=HotspotResponse,
    summary="Civic issue hotspots",
    responses=_ERRORS,
)
def hotspots(
    user: ActiveUser,
    db: DbSession,
    window_days: WindowDays = 30,
    grid_meters: Annotated[
        int | None, Query(ge=100, le=5000, description="Cluster cell size in metres.")
    ] = None,
    min_complaints: Annotated[
        int | None, Query(ge=2, le=50, description="Minimum complaints per cluster.")
    ] = None,
    category: Annotated[
        ComplaintCategory | None, Query(description="Restrict to one category.")
    ] = None,
    open_only: Annotated[bool, Query(description="Ignore resolved complaints.")] = False,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
) -> HotspotResponse:
    """Geographic clusters of complaints, ranked by severity-weighted intensity.

    Complaints are snapped to a metre-scale grid, so the response is a set of
    map-ready cells with a dominant category, intensity (0-1) and sample
    complaints — the citizen app draws these as a heat layer.
    """
    return analytics_service.hotspots(
        db,
        window_days=window_days,
        min_complaints=min_complaints,
        grid_meters=grid_meters,
        category=category,
        open_only=open_only,
        limit=limit,
    )


@router.get(
    "/trends",
    response_model=TrendsResponse,
    summary="Trending issues over time",
    responses=_ERRORS,
)
def trends(
    user: ActiveUser,
    db: DbSession,
    window_days: WindowDays = 30,
    granularity: Annotated[
        str, Query(pattern="^(day|week|month)$", description="Bucket size.")
    ] = "day",
) -> TrendsResponse:
    """A time series of complaint volume plus which categories are rising.

    "Trending" compares the most recent third of the window against the third
    before it, so a monsoon spike in drainage complaints shows up as `rising`.
    """
    return analytics_service.trends(
        db, window_days=window_days, granularity=granularity
    )


@router.get(
    "/categories",
    response_model=CategoryStatsResponse,
    summary="Category statistics",
    responses=_ERRORS,
)
def categories(
    user: ActiveUser, db: DbSession, window_days: WindowDays = 30
) -> CategoryStatsResponse:
    """Volume, share, resolution rate and turnaround per civic category."""
    return analytics_service.category_stats(db, window_days=window_days)


@router.get(
    "/departments",
    response_model=DepartmentPerformanceResponse,
    summary="Department performance (admin only)",
    responses=_ERRORS,
)
def departments(
    admin: AdminUser, db: DbSession, window_days: WindowDays = 30
) -> DepartmentPerformanceResponse:
    """Throughput, SLA compliance and a composite score per department."""
    return analytics_service.department_performance(db, window_days=window_days)


@router.get(
    "/city-health",
    response_model=CityHealthScore,
    summary="City health score",
    responses=_ERRORS,
)
def city_health(
    user: ActiveUser, db: DbSession, window_days: WindowDays = 30
) -> CityHealthScore:
    """A single 0-100 civic responsiveness score with its sub-components.

    Weighted from resolution rate (30%), speed (20%), backlog (20%), open
    critical issues (15%) and citizen engagement (15%), and compared against
    the previous equal-length window to derive the trend.
    """
    return analytics_service.city_health(db, window_days=window_days)
