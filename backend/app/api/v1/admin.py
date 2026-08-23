"""Admin endpoints. Every route here requires the `admin` application role."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Path, Query, status

from app.api.deps import PaginationDep, WindowDays
from app.auth.dependencies import AdminUser, DbSession
from app.models.enums import (
    ComplaintCategory,
    ComplaintSeverity,
    ComplaintStatus,
    UserRole,
)
from app.schemas.admin import (
    AdminComplaintPatch,
    DashboardStats,
    DepartmentCreate,
    DepartmentOut,
    DepartmentUpdate,
    EvidenceRequest,
    UserAdminOut,
)
from app.schemas.ai import AnalyzeComplaintResponse
from app.schemas.common import ErrorResponse, Page, PaginationMeta
from app.schemas.complaint import ComplaintDetail, ComplaintListItem
from app.schemas.profile import ActiveUpdateRequest, ProfileOut, RoleUpdateRequest
from app.services import admin_service, complaint_service, profile_service
from app.services.claude_service import DEPARTMENT_BY_CATEGORY, claude_service
from app.utils.config import settings

router = APIRouter(prefix="/admin", tags=["Admin"])

_ERRORS = {
    401: {"model": ErrorResponse},
    403: {"model": ErrorResponse, "description": "Administrator role required."},
    404: {"model": ErrorResponse},
    422: {"model": ErrorResponse},
}

ComplaintId = Annotated[uuid.UUID, Path(description="Complaint UUID.")]


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------


@router.get(
    "/dashboard",
    response_model=DashboardStats,
    summary="Admin dashboard statistics",
    responses=_ERRORS,
)
def dashboard(
    admin: AdminUser, db: DbSession, window_days: WindowDays = 30
) -> DashboardStats:
    """Every counter the admin home screen needs, in one request.

    Includes totals by status/category/severity, department load, SLA breaches,
    resolution times, ward hotspots and the composite city-health score.
    """
    return admin_service.dashboard(db, window_days=window_days)


# ---------------------------------------------------------------------------
# Complaints
# ---------------------------------------------------------------------------


@router.get(
    "/complaints",
    response_model=Page[ComplaintListItem],
    summary="Search and filter all complaints",
    responses=_ERRORS,
)
def list_all_complaints(
    admin: AdminUser,
    db: DbSession,
    page: PaginationDep,
    status_filter: Annotated[
        list[ComplaintStatus] | None, Query(alias="status", description="Filter by status.")
    ] = None,
    category: Annotated[
        list[ComplaintCategory] | None, Query(description="Filter by category.")
    ] = None,
    severity: Annotated[
        list[ComplaintSeverity] | None, Query(description="Filter by severity.")
    ] = None,
    department_id: Annotated[uuid.UUID | None, Query(description="Filter by department.")] = None,
    assigned_to_id: Annotated[uuid.UUID | None, Query(description="Filter by assignee.")] = None,
    ward: Annotated[str | None, Query(max_length=80)] = None,
    search: Annotated[
        str | None,
        Query(max_length=120, description="Matches title, description, code, address, ward."),
    ] = None,
    unassigned_only: Annotated[
        bool, Query(description="Only complaints with no department.")
    ] = False,
    created_after: Annotated[datetime | None, Query(description="ISO 8601 lower bound.")] = None,
    created_before: Annotated[datetime | None, Query(description="ISO 8601 upper bound.")] = None,
    sort: Annotated[
        str,
        Query(
            description="Sort field, '-' prefix for descending.",
            pattern=r"^-?(created_at|updated_at|priority_score|confirmation_count|status|severity)$",
        ),
    ] = "-priority_score",
) -> Page[ComplaintListItem]:
    """The municipal work queue — defaults to highest priority first."""
    rows, total = complaint_service.list_complaints(
        db,
        statuses=status_filter,
        categories=category,
        severities=severity,
        department_id=department_id,
        assigned_to_id=assigned_to_id,
        ward=ward,
        search=search,
        unassigned_only=unassigned_only,
        created_after=created_after,
        created_before=created_before,
        sort=sort,
        limit=page.limit,
        offset=page.offset,
    )
    return Page[ComplaintListItem](
        items=[complaint_service.to_list_item(row) for row in rows],
        pagination=PaginationMeta.build(total, page.limit, page.offset),
    )


@router.get(
    "/complaints/{complaint_id}",
    response_model=ComplaintDetail,
    summary="Complaint details (admin view)",
    responses=_ERRORS,
)
def get_complaint(
    complaint_id: ComplaintId, admin: AdminUser, db: DbSession
) -> ComplaintDetail:
    """Full detail including internal-only timeline entries."""
    complaint = complaint_service.get_complaint_or_404(db, complaint_id)
    return complaint_service.to_detail(db, complaint, requester=admin)


@router.patch(
    "/complaints/{complaint_id}",
    response_model=ComplaintDetail,
    summary="Update status, department, priority or resolution",
    responses={**_ERRORS, 409: {"model": ErrorResponse}},
)
def update_complaint(
    complaint_id: ComplaintId,
    payload: AdminComplaintPatch,
    admin: AdminUser,
    db: DbSession,
) -> ComplaintDetail:
    """Apply one or more administrative changes to a complaint.

    Each changed field is recorded as a separate timeline entry naming the
    admin who made it. Setting status to `resolved` or `rejected` requires a
    resolution note (either already stored or supplied in the same call).
    Assigning a department on a freshly submitted complaint also moves it to
    `assigned`.
    """
    complaint = complaint_service.get_complaint_or_404(db, complaint_id)
    updated = admin_service.patch_complaint(db, complaint, admin, payload)
    return complaint_service.to_detail(db, updated, requester=admin)


@router.post(
    "/complaints/{complaint_id}/evidence",
    response_model=ComplaintDetail,
    summary="Attach before/after evidence",
    responses=_ERRORS,
)
def add_evidence(
    complaint_id: ComplaintId,
    payload: EvidenceRequest,
    admin: AdminUser,
    db: DbSession,
) -> ComplaintDetail:
    """Attach photographic proof of the work done (upload to storage first)."""
    complaint = complaint_service.get_complaint_or_404(db, complaint_id)
    updated = admin_service.add_evidence(db, complaint, admin, payload)
    return complaint_service.to_detail(db, updated, requester=admin)


@router.post(
    "/complaints/{complaint_id}/reanalyze",
    response_model=AnalyzeComplaintResponse,
    summary="Re-run AI analysis on a complaint",
    responses=_ERRORS,
)
def reanalyze_complaint(
    complaint_id: ComplaintId,
    admin: AdminUser,
    db: DbSession,
    apply: Annotated[
        bool, Query(description="Persist the new classification over the old one.")
    ] = True,
) -> AnalyzeComplaintResponse:
    """Ask Claude to re-classify a complaint (e.g. after the text was edited)."""
    complaint = complaint_service.get_complaint_or_404(db, complaint_id)
    if apply:
        result = complaint_service.analyze_and_apply(db, complaint, actor=admin)
        db.commit()
        db.refresh(complaint)
        department_id = complaint.department_id
        department_name = complaint.department.name if complaint.department else None
    else:
        nearby = complaint_service.find_nearby(
            db,
            latitude=complaint.latitude,
            longitude=complaint.longitude,
            radius_meters=settings.duplicate_radius_meters,
            exclude_id=complaint.id,
            limit=8,
        )
        result = claude_service.analyze_complaint(
            title=complaint.title,
            description=complaint.description,
            latitude=complaint.latitude,
            longitude=complaint.longitude,
            address=complaint.address,
            ward=complaint.ward,
            image_url=complaint.image_url,
            candidates=complaint_service.build_duplicate_candidates(nearby),
            confirmation_count=complaint.confirmation_count,
        )
        department_id = None
        department_name = DEPARTMENT_BY_CATEGORY[result.analysis.category]

    return AnalyzeComplaintResponse(
        analysis=result.analysis,
        status=result.status,
        model=result.model,
        department_id=department_id,
        department_name=department_name,
        duplicate_candidates_considered=result.candidates_considered,
        latency_ms=round(result.latency_ms, 1),
    )


# ---------------------------------------------------------------------------
# Departments
# ---------------------------------------------------------------------------


@router.get(
    "/departments",
    response_model=list[DepartmentOut],
    summary="List departments",
    responses=_ERRORS,
)
def list_departments(
    admin: AdminUser,
    db: DbSession,
    include_inactive: Annotated[bool, Query()] = False,
) -> list[DepartmentOut]:
    return [
        DepartmentOut.model_validate(department)
        for department in admin_service.list_departments(
            db, include_inactive=include_inactive
        )
    ]


@router.post(
    "/departments",
    response_model=DepartmentOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create a department",
    responses={**_ERRORS, 409: {"model": ErrorResponse}},
)
def create_department(
    payload: DepartmentCreate, admin: AdminUser, db: DbSession
) -> DepartmentOut:
    return DepartmentOut.model_validate(admin_service.create_department(db, payload))


@router.patch(
    "/departments/{department_id}",
    response_model=DepartmentOut,
    summary="Update a department",
    responses=_ERRORS,
)
def update_department(
    department_id: Annotated[uuid.UUID, Path()],
    payload: DepartmentUpdate,
    admin: AdminUser,
    db: DbSession,
) -> DepartmentOut:
    return DepartmentOut.model_validate(
        admin_service.update_department(db, department_id, payload)
    )


# ---------------------------------------------------------------------------
# Users and roles
# ---------------------------------------------------------------------------


@router.get(
    "/users",
    response_model=Page[UserAdminOut],
    summary="List platform users",
    responses=_ERRORS,
)
def list_users(
    admin: AdminUser,
    db: DbSession,
    page: PaginationDep,
    role: Annotated[UserRole | None, Query(description="Filter by role.")] = None,
    search: Annotated[str | None, Query(max_length=120, description="Email or name.")] = None,
) -> Page[UserAdminOut]:
    rows, total = profile_service.list_profiles(
        db, role=role, search=search, limit=page.limit, offset=page.offset
    )
    return Page[UserAdminOut](
        items=[UserAdminOut.model_validate(row) for row in rows],
        pagination=PaginationMeta.build(total, page.limit, page.offset),
    )


@router.post(
    "/users/{user_id}/role",
    response_model=ProfileOut,
    summary="Grant or revoke the admin role",
    responses={**_ERRORS, 409: {"model": ErrorResponse}},
)
def set_user_role(
    user_id: Annotated[uuid.UUID, Path(description="Target user id.")],
    payload: RoleUpdateRequest,
    admin: AdminUser,
    db: DbSession,
) -> ProfileOut:
    """The only in-app path to the admin role.

    Signup can never produce an admin. Guards prevent self-demotion and
    removing the last remaining admin.
    """
    updated = profile_service.set_role(
        db,
        actor=admin,
        target_user_id=user_id,
        role=payload.role,
        department_id=payload.department_id,
    )
    return ProfileOut.model_validate(updated)


@router.post(
    "/users/{user_id}/active",
    response_model=ProfileOut,
    summary="Activate or deactivate a user",
    responses={**_ERRORS, 409: {"model": ErrorResponse}},
)
def set_user_active(
    user_id: Annotated[uuid.UUID, Path()],
    payload: ActiveUpdateRequest,
    admin: AdminUser,
    db: DbSession,
) -> ProfileOut:
    updated = profile_service.set_active(
        db, actor=admin, target_user_id=user_id, is_active=payload.is_active
    )
    return ProfileOut.model_validate(updated)
