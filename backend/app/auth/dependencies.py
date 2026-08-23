"""FastAPI auth dependencies: current user, active user and admin guard."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.auth.jwt import TokenPayload, decode_token
from app.database.session import get_db
from app.models import Profile, UserRole
from app.services import profile_service
from app.utils.errors import AuthenticationError, PermissionDeniedError

#: `auto_error=False` so we can emit our own JSON error envelope.
bearer_scheme = HTTPBearer(
    scheme_name="SupabaseBearer",
    description="Paste the Supabase access token (JWT) — no 'Bearer ' prefix needed.",
    auto_error=False,
)

DbSession = Annotated[Session, Depends(get_db)]


def get_token_payload(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None, Depends(bearer_scheme)
    ],
) -> TokenPayload:
    """Verify the bearer token and return its claims."""
    if credentials is None or not credentials.credentials:
        raise AuthenticationError("Authorization header with a Bearer token is required.")
    if credentials.scheme.lower() != "bearer":
        raise AuthenticationError("Authorization scheme must be Bearer.")
    return decode_token(credentials.credentials)


TokenClaims = Annotated[TokenPayload, Depends(get_token_payload)]


def get_current_user(payload: TokenClaims, db: DbSession) -> Profile:
    """Resolve the verified token to a profile, provisioning on first login."""
    return profile_service.provision_profile(db, payload)


CurrentUser = Annotated[Profile, Depends(get_current_user)]


def get_current_active_user(user: CurrentUser) -> Profile:
    if not user.is_active:
        raise PermissionDeniedError(
            "This account has been deactivated. Contact the municipal helpdesk.",
            code="account_disabled",
        )
    return user


ActiveUser = Annotated[Profile, Depends(get_current_active_user)]


def require_admin(user: ActiveUser) -> Profile:
    """Guard every /admin and AI-briefing route."""
    if user.role is not UserRole.ADMIN:
        raise PermissionDeniedError(
            "Administrator privileges are required for this endpoint.",
            code="admin_required",
        )
    return user


AdminUser = Annotated[Profile, Depends(require_admin)]


def get_optional_user(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None, Depends(bearer_scheme)
    ],
    db: DbSession,
) -> Profile | None:
    """For endpoints that work anonymously but personalise when signed in."""
    if credentials is None or not credentials.credentials:
        return None
    try:
        payload = decode_token(credentials.credentials)
        return profile_service.provision_profile(db, payload)
    except Exception:
        return None


OptionalUser = Annotated[Profile | None, Depends(get_optional_user)]
