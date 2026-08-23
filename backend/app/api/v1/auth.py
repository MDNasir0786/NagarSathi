"""Authentication endpoints.

Sign-up and sign-in happen in Supabase (from the React client). This API only
*verifies* the resulting access token, mirrors the user into `profiles`, and
reports the application role.
"""

from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter, status

from app.auth.dependencies import ActiveUser, CurrentUser, DbSession, TokenClaims
from app.models import UserRole
from app.schemas.common import ErrorResponse
from app.schemas.profile import (
    MeResponse,
    ProfileOut,
    ProfileStats,
    TokenIntrospection,
)
from app.services import complaint_service

router = APIRouter(prefix="/auth", tags=["Authentication"])

CITIZEN_PERMISSIONS = [
    "complaint:create",
    "complaint:read:own",
    "complaint:confirm",
    "profile:manage:own",
    "analytics:read:public",
]
ADMIN_PERMISSIONS = [
    *CITIZEN_PERMISSIONS,
    "complaint:read:all",
    "complaint:update",
    "complaint:assign",
    "department:manage",
    "user:manage",
    "analytics:read:all",
    "ai:briefing",
]


@router.get(
    "/me",
    response_model=MeResponse,
    summary="Current user",
    responses={401: {"model": ErrorResponse}},
)
def read_me(user: ActiveUser, db: DbSession) -> MeResponse:
    """Return the signed-in user's profile, activity summary and permissions.

    The profile row is created automatically on the first authenticated call,
    so a freshly signed-up Supabase user can hit this immediately.
    """
    stats = complaint_service.citizen_stats(db, user)
    return MeResponse(
        profile=ProfileOut.model_validate(user),
        stats=ProfileStats(**stats),
        permissions=(
            ADMIN_PERMISSIONS if user.role is UserRole.ADMIN else CITIZEN_PERMISSIONS
        ),
    )


@router.post(
    "/sync",
    response_model=ProfileOut,
    status_code=status.HTTP_200_OK,
    summary="Provision or refresh the local profile",
    responses={401: {"model": ErrorResponse}, 422: {"model": ErrorResponse}},
)
def sync_profile(user: CurrentUser) -> ProfileOut:
    """Idempotently mirror the Supabase user into `profiles`.

    Call this right after signup/login in the React app. Repeat calls are
    harmless. The role is always assigned by the backend — a client cannot
    request one.
    """
    return ProfileOut.model_validate(user)


@router.get(
    "/verify",
    response_model=TokenIntrospection,
    summary="Verify the access token",
    responses={401: {"model": ErrorResponse}},
)
def verify_token(claims: TokenClaims, user: ActiveUser) -> TokenIntrospection:
    """Cheap token check for the frontend's route guards."""
    return TokenIntrospection(
        valid=True,
        user_id=user.id,
        email=user.email,
        role=user.role,
        expires_at=(
            datetime.fromtimestamp(claims.exp, tz=UTC) if claims.exp else None
        ),
    )
