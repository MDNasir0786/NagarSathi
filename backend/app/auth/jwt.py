"""Supabase JWT verification.

Two verification modes are supported:

* **Shared secret (HS256)** — set ``SUPABASE_JWT_SECRET``.
* **Asymmetric (ES256/RS256)** — leave the secret blank and set
  ``SUPABASE_URL``; signing keys are fetched and cached from the project's
  JWKS endpoint.

The token is never trusted for authorisation data: the role that matters is
the one stored on the ``profiles`` row in our own database.
"""

from __future__ import annotations

import logging
from functools import lru_cache
from typing import Any
from uuid import UUID

import jwt
from jwt import PyJWKClient
from pydantic import BaseModel, Field

from app.utils.config import settings
from app.utils.errors import AuthenticationError, ServiceUnavailableError

logger = logging.getLogger(__name__)


class TokenPayload(BaseModel):
    """The subset of Supabase access-token claims this API relies on."""

    sub: UUID
    email: str | None = None
    phone: str | None = None
    aud: str | None = None
    exp: int | None = None
    iat: int | None = None
    iss: str | None = None
    session_id: str | None = None
    #: Supabase's own claim ("authenticated"/"anon") — NOT our application role.
    token_role: str | None = Field(default=None, alias="role")
    app_metadata: dict[str, Any] = Field(default_factory=dict)
    user_metadata: dict[str, Any] = Field(default_factory=dict)

    model_config = {"populate_by_name": True, "extra": "ignore"}

    @property
    def user_id(self) -> UUID:
        return self.sub

    @property
    def display_name(self) -> str | None:
        for key in ("full_name", "name", "display_name"):
            value = self.user_metadata.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
        return None

    @property
    def avatar_url(self) -> str | None:
        for key in ("avatar_url", "picture"):
            value = self.user_metadata.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
        return None


@lru_cache(maxsize=1)
def _jwk_client() -> PyJWKClient:
    if not settings.jwks_url:  # pragma: no cover - guarded by callers
        raise ServiceUnavailableError("Supabase JWKS endpoint is not configured.")
    return PyJWKClient(
        settings.jwks_url,
        cache_keys=True,
        max_cached_keys=8,
        lifespan=settings.jwks_cache_seconds,
    )


def _resolve_key(token: str) -> tuple[Any, list[str]]:
    """Return the verification key and the algorithms allowed for it."""
    algorithms = settings.jwt_algorithm_list
    symmetric = [alg for alg in algorithms if alg.startswith("HS")]

    if settings.supabase_jwt_secret and symmetric:
        return settings.supabase_jwt_secret, symmetric

    if settings.jwks_url:
        asymmetric = [alg for alg in algorithms if not alg.startswith("HS")] or [
            "ES256",
            "RS256",
        ]
        try:
            signing_key = _jwk_client().get_signing_key_from_jwt(token)
        except jwt.PyJWKClientError as exc:
            logger.warning("JWKS key lookup failed: %s", exc)
            raise AuthenticationError("Token signing key could not be verified.") from exc
        except Exception as exc:  # network/JWKS outage
            logger.exception("JWKS endpoint unreachable")
            raise ServiceUnavailableError(
                "Unable to reach the identity provider. Please retry."
            ) from exc
        return signing_key.key, asymmetric

    raise ServiceUnavailableError(
        "Authentication is not configured: set SUPABASE_JWT_SECRET or SUPABASE_URL."
    )


def decode_token(token: str) -> TokenPayload:
    """Verify a Supabase access token and return its claims.

    Raises:
        AuthenticationError: the token is missing, malformed, expired or the
            signature/audience/issuer does not match.
        ServiceUnavailableError: auth is unconfigured or the JWKS endpoint is
            unreachable.
    """
    if not token or not token.strip():
        raise AuthenticationError("Authorization token is missing.")

    key, algorithms = _resolve_key(token)

    options: dict[str, Any] = {
        "require": ["exp", "sub"],
        "verify_aud": bool(settings.supabase_jwt_audience),
        "verify_iss": bool(settings.expected_issuer),
    }

    try:
        claims = jwt.decode(
            token,
            key,
            algorithms=algorithms,
            audience=settings.supabase_jwt_audience or None,
            issuer=settings.expected_issuer or None,
            options=options,
            leeway=10,  # tolerate small clock skew
        )
    except jwt.ExpiredSignatureError as exc:
        raise AuthenticationError(
            "Session has expired. Please sign in again.", code="token_expired"
        ) from exc
    except jwt.InvalidAudienceError as exc:
        raise AuthenticationError(
            "Token audience is invalid.", code="invalid_audience"
        ) from exc
    except jwt.InvalidIssuerError as exc:
        raise AuthenticationError(
            "Token issuer is invalid.", code="invalid_issuer"
        ) from exc
    except jwt.InvalidSignatureError as exc:
        raise AuthenticationError(
            "Token signature is invalid.", code="invalid_signature"
        ) from exc
    except jwt.MissingRequiredClaimError as exc:
        raise AuthenticationError(
            f"Token is missing the required claim '{exc.claim}'.",
            code="invalid_token",
        ) from exc
    except jwt.InvalidTokenError as exc:
        raise AuthenticationError(
            "Authorization token is invalid.", code="invalid_token"
        ) from exc

    try:
        return TokenPayload.model_validate(claims)
    except Exception as exc:
        logger.warning("token claims failed validation: %s", exc)
        raise AuthenticationError(
            "Token claims are malformed.", code="invalid_token"
        ) from exc
