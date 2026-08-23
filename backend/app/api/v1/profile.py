"""Citizen profile endpoints."""

from __future__ import annotations

from fastapi import APIRouter, status

from app.auth.dependencies import ActiveUser, DbSession
from app.schemas.common import ErrorResponse
from app.schemas.profile import ProfileOut, ProfileStats, ProfileUpsert
from app.services import complaint_service, profile_service

router = APIRouter(prefix="/profile", tags=["Profile"])

_ERRORS = {
    401: {"model": ErrorResponse},
    403: {"model": ErrorResponse},
    422: {"model": ErrorResponse},
}


@router.get("", response_model=ProfileOut, summary="Get my profile", responses=_ERRORS)
def get_profile(user: ActiveUser) -> ProfileOut:
    return ProfileOut.model_validate(user)


@router.post(
    "",
    response_model=ProfileOut,
    status_code=status.HTTP_200_OK,
    summary="Create or replace my profile details",
    responses=_ERRORS,
)
def upsert_profile(
    payload: ProfileUpsert, user: ActiveUser, db: DbSession
) -> ProfileOut:
    """Fill in profile details after signup.

    The profile row itself is created on first authentication, so this is an
    upsert of the editable fields. `role`, `is_active` and `department_id` are
    server-controlled and rejected if sent.
    """
    updated = profile_service.update_profile(db, user, payload.changes())
    return ProfileOut.model_validate(updated)


@router.patch(
    "",
    response_model=ProfileOut,
    summary="Update my profile",
    responses=_ERRORS,
)
def update_profile(
    payload: ProfileUpsert, user: ActiveUser, db: DbSession
) -> ProfileOut:
    """Partial update — only the fields present in the body are changed."""
    updated = profile_service.update_profile(db, user, payload.changes())
    return ProfileOut.model_validate(updated)


@router.get(
    "/stats",
    response_model=ProfileStats,
    summary="My complaint activity summary",
    responses=_ERRORS,
)
def profile_stats(user: ActiveUser, db: DbSession) -> ProfileStats:
    return ProfileStats(**complaint_service.citizen_stats(db, user))
