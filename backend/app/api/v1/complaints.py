"""Citizen complaint endpoints: file, browse, track and confirm."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Path, Query, status

from app.api.deps import PaginationDep
from app.auth.dependencies import ActiveUser, DbSession
from app.models.enums import ComplaintCategory, ComplaintStatus
from app.schemas.common import ErrorResponse, Page, PaginationMeta
from app.schemas.complaint import (
    ComplaintCreate,
    ComplaintCreateResponse,
    ComplaintDetail,
    ComplaintListItem,
    ComplaintStatusOut,
    ComplaintUpdateByCitizen,
    ConfirmRequest,
    ConfirmResponse,
    NearbyComplaint,
    SimilarComplaint,
)
from app.services import complaint_service
from app.utils.errors import NotFoundError

router = APIRouter(prefix="/complaints", tags=["Complaints"])

_ERRORS = {
    401: {"model": ErrorResponse},
    403: {"model": ErrorResponse},
    404: {"model": ErrorResponse},
    422: {"model": ErrorResponse},
}

ComplaintId = Annotated[uuid.UUID, Path(description="Complaint UUID.")]


@router.post(
    "",
    response_model=ComplaintCreateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="File a civic complaint",
    responses={**_ERRORS, 201: {"description": "Complaint filed and analysed."}},
)
def create_complaint(
    payload: ComplaintCreate, user: ActiveUser, db: DbSession
) -> ComplaintCreateResponse:
    """File a complaint with GPS coordinates and an optional photo URL.

    On submission Claude classifies the report (category, severity, priority
    score, summary, responsible department, suggested action) and checks nearby
    open complaints for duplicates. If the report duplicates an existing one it
    is linked and counted as a confirmation on the original instead.

    If the AI is unavailable a deterministic analyser is used and
    `ai_status` comes back as `fallback` — filing never fails because of it.
    """
    complaint, result, duplicate_of = complaint_service.create_complaint(
        db, user, payload
    )
    detail = complaint_service.to_detail(db, complaint, requester=user)

    if duplicate_of is not None:
        message = (
            f"This looks like the same issue as {duplicate_of.reference_code}, which "
            "is already being tracked. Your report has been added as a confirmation."
        )
    else:
        message = (
            f"Complaint {complaint.reference_code} filed and routed to "
            f"{detail.department.name if detail.department else 'the grievance cell'}."
        )

    return ComplaintCreateResponse(
        complaint=detail,
        is_duplicate=duplicate_of is not None,
        duplicate_of=(
            SimilarComplaint(
                id=duplicate_of.id,
                reference_code=duplicate_of.reference_code,
                title=duplicate_of.title,
                status=duplicate_of.status,
                category=duplicate_of.category,
                confirmation_count=duplicate_of.confirmation_count,
                created_at=duplicate_of.created_at,
            )
            if duplicate_of is not None
            else None
        ),
        ai_status=result.status,
        message=message,
    )


@router.get(
    "",
    response_model=Page[ComplaintListItem],
    summary="List my complaints",
    responses=_ERRORS,
)
def list_my_complaints(
    user: ActiveUser,
    db: DbSession,
    page: PaginationDep,
    status_filter: Annotated[
        list[ComplaintStatus] | None,
        Query(alias="status", description="Filter by one or more statuses."),
    ] = None,
    category: Annotated[
        list[ComplaintCategory] | None, Query(description="Filter by category.")
    ] = None,
    search: Annotated[
        str | None, Query(max_length=120, description="Free-text search.")
    ] = None,
    sort: Annotated[
        str,
        Query(
            description="Sort field, prefix with '-' for descending.",
            pattern=r"^-?(created_at|updated_at|priority_score|confirmation_count|status|severity)$",
        ),
    ] = "-created_at",
) -> Page[ComplaintListItem]:
    """Complaints filed by the signed-in citizen."""
    rows, total = complaint_service.list_complaints(
        db,
        citizen_id=user.id,
        statuses=status_filter,
        categories=category,
        search=search,
        sort=sort,
        limit=page.limit,
        offset=page.offset,
    )
    return Page[ComplaintListItem](
        items=[complaint_service.to_list_item(row) for row in rows],
        pagination=PaginationMeta.build(total, page.limit, page.offset),
    )


@router.get(
    "/nearby",
    response_model=list[NearbyComplaint],
    summary="Find nearby issues already reported",
    responses=_ERRORS,
)
def nearby_complaints(
    user: ActiveUser,
    db: DbSession,
    latitude: Annotated[float, Query(ge=-90, le=90, description="Your latitude.")],
    longitude: Annotated[float, Query(ge=-180, le=180, description="Your longitude.")],
    radius_meters: Annotated[
        int | None, Query(ge=10, le=5000, description="Search radius in metres.")
    ] = None,
    category: Annotated[
        ComplaintCategory | None, Query(description="Restrict to one category.")
    ] = None,
    limit: Annotated[int, Query(ge=1, le=50)] = 10,
) -> list[NearbyComplaint]:
    """Open complaints near a point, so a citizen can confirm instead of duplicating.

    Call this before showing the "file a complaint" form: if something is
    already reported at that spot, offer the confirm action instead.
    """
    return complaint_service.nearby_for_citizen(
        db,
        latitude=latitude,
        longitude=longitude,
        radius_meters=radius_meters,
        category=category,
        requester=user,
        limit=limit,
    )


@router.get(
    "/reference/{reference_code}",
    response_model=ComplaintDetail,
    summary="Look up a complaint by its tracking code",
    responses=_ERRORS,
)
def get_by_reference(
    reference_code: Annotated[str, Path(max_length=32, description="e.g. BCA-2026-4F9A2C")],
    user: ActiveUser,
    db: DbSession,
) -> ComplaintDetail:
    complaint = complaint_service.get_by_reference(db, reference_code)
    if complaint is None:
        raise NotFoundError("No complaint found with that reference code.")
    complaint_service.ensure_can_view(complaint, user)
    return complaint_service.to_detail(db, complaint, requester=user)


@router.get(
    "/{complaint_id}",
    response_model=ComplaintDetail,
    summary="Complaint details",
    responses=_ERRORS,
)
def get_complaint(
    complaint_id: ComplaintId, user: ActiveUser, db: DbSession
) -> ComplaintDetail:
    """Full detail, including the AI analysis and the public timeline.

    Citizens can only read their own complaints; admins can read any.
    """
    complaint = complaint_service.get_complaint_or_404(db, complaint_id)
    complaint_service.ensure_can_view(complaint, user)
    return complaint_service.to_detail(db, complaint, requester=user)


@router.patch(
    "/{complaint_id}",
    response_model=ComplaintDetail,
    summary="Edit my complaint (before it is picked up)",
    responses={**_ERRORS, 409: {"model": ErrorResponse}},
)
def update_complaint(
    complaint_id: ComplaintId,
    payload: ComplaintUpdateByCitizen,
    user: ActiveUser,
    db: DbSession,
) -> ComplaintDetail:
    """Correct wording or add photos while the complaint is still `submitted`."""
    complaint = complaint_service.get_complaint_or_404(db, complaint_id)
    updated = complaint_service.update_own_complaint(db, complaint, user, payload)
    return complaint_service.to_detail(db, updated, requester=user)


@router.get(
    "/{complaint_id}/status",
    response_model=ComplaintStatusOut,
    summary="Track complaint status",
    responses=_ERRORS,
)
def track_status(
    complaint_id: ComplaintId, user: ActiveUser, db: DbSession
) -> ComplaintStatusOut:
    """Compact status view with the SLA clock and the full public timeline."""
    complaint = complaint_service.get_complaint_or_404(db, complaint_id)
    complaint_service.ensure_can_view(complaint, user)
    return complaint_service.to_status(db, complaint, requester=user)


@router.post(
    "/{complaint_id}/confirm",
    response_model=ConfirmResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Confirm an existing nearby issue",
    responses={**_ERRORS, 409: {"model": ErrorResponse}},
)
def confirm_complaint(
    complaint_id: ComplaintId,
    payload: ConfirmRequest,
    user: ActiveUser,
    db: DbSession,
) -> ConfirmResponse:
    """Add a "me too" to an existing complaint.

    Each citizen may confirm a complaint once. Confirmations raise the priority
    score and, past a threshold, escalate severity — so widely-felt problems
    surface without anyone filing duplicates. Confirming a complaint that was
    itself flagged as a duplicate records the confirmation on the original.
    """
    complaint, _ = complaint_service.confirm_complaint(db, complaint_id, user, payload)
    return ConfirmResponse(
        complaint_id=complaint.id,
        reference_code=complaint.reference_code,
        confirmation_count=complaint.confirmation_count,
        priority_score=complaint.priority_score,
        severity=complaint.severity,
        message=(
            f"Thanks — {complaint.confirmation_count} citizen(s) have now confirmed "
            f"{complaint.reference_code}."
        ),
    )
