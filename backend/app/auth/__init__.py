"""Authentication: Supabase JWT verification and role-based dependencies."""

from app.auth.dependencies import (
    ActiveUser,
    AdminUser,
    CurrentUser,
    DbSession,
    OptionalUser,
    TokenClaims,
    bearer_scheme,
    get_current_active_user,
    get_current_user,
    get_optional_user,
    get_token_payload,
    require_admin,
)
from app.auth.jwt import TokenPayload, decode_token

__all__ = [
    "ActiveUser",
    "AdminUser",
    "CurrentUser",
    "DbSession",
    "OptionalUser",
    "TokenClaims",
    "TokenPayload",
    "bearer_scheme",
    "decode_token",
    "get_current_active_user",
    "get_current_user",
    "get_optional_user",
    "get_token_payload",
    "require_admin",
]
