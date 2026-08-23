"""Shared response envelopes and reusable field types."""

from __future__ import annotations

from typing import Annotated, Any, Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_validator

T = TypeVar("T")


def _validate_url(value: str | None) -> str | None:
    if value is None:
        return None
    value = value.strip()
    if not value:
        return None
    if not value.startswith(("http://", "https://")):
        raise ValueError("URL must start with http:// or https://")
    if len(value) > 2000:
        raise ValueError("URL is too long (max 2000 characters)")
    return value


#: A trimmed, non-empty short string.
ShortText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)]
#: Indian mobile / landline, loosely validated (E.164-ish).
PhoneNumber = Annotated[
    str, StringConstraints(strip_whitespace=True, pattern=r"^\+?[0-9][0-9\-\s]{6,19}$")
]


class ORMModel(BaseModel):
    """Base for response models read straight off SQLAlchemy instances."""

    model_config = ConfigDict(from_attributes=True)


class PaginationMeta(BaseModel):
    total: int = Field(description="Total matching records.")
    limit: int
    offset: int
    has_more: bool

    @classmethod
    def build(cls, total: int, limit: int, offset: int) -> PaginationMeta:
        return cls(
            total=total,
            limit=limit,
            offset=offset,
            has_more=(offset + limit) < total,
        )


class Page(BaseModel, Generic[T]):
    """Standard list envelope used by every collection endpoint."""

    items: list[T]
    pagination: PaginationMeta


class MessageResponse(BaseModel):
    message: str
    detail: str | None = None


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: Any | None = None


class ErrorResponse(BaseModel):
    """The single error envelope returned by every failing endpoint."""

    error: ErrorDetail


class HealthResponse(BaseModel):
    status: str
    app: str
    version: str
    environment: str


class ReadinessResponse(BaseModel):
    status: str
    database: bool
    auth_configured: bool
    ai_configured: bool


class UrlPayload(BaseModel):
    url: str

    @field_validator("url")
    @classmethod
    def _check_url(cls, value: str) -> str:
        validated = _validate_url(value)
        if validated is None:
            raise ValueError("A URL is required")
        return validated
