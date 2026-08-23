"""Profile and auth-facing schemas."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, EmailStr, Field, StringConstraints, field_validator

from app.models.enums import UserRole
from app.schemas.common import ORMModel, PhoneNumber, _validate_url

NameStr = Annotated[str, StringConstraints(strip_whitespace=True, min_length=2, max_length=160)]
WardStr = Annotated[str, StringConstraints(strip_whitespace=True, max_length=80)]


class ProfileUpsert(BaseModel):
    """Citizen-editable profile fields.

    `role`, `is_active` and `department_id` are intentionally absent — those
    are server-controlled and can only change through admin endpoints.
    """

    model_config = ConfigDict(extra="forbid")

    full_name: NameStr | None = None
    phone: PhoneNumber | None = None
    address: Annotated[str, StringConstraints(strip_whitespace=True, max_length=500)] | None = None
    ward: WardStr | None = None
    city: Annotated[str, StringConstraints(strip_whitespace=True, max_length=80)] | None = None
    avatar_url: str | None = None
    language: Annotated[str, StringConstraints(strip_whitespace=True, max_length=8)] | None = None

    @field_validator("avatar_url")
    @classmethod
    def _avatar(cls, value: str | None) -> str | None:
        return _validate_url(value)

    def changes(self) -> dict:
        """Only the fields the client actually sent."""
        return self.model_dump(exclude_unset=True, exclude_none=False)


class DepartmentBrief(ORMModel):
    id: uuid.UUID
    name: str
    code: str


class ProfileOut(ORMModel):
    id: uuid.UUID
    email: EmailStr
    full_name: str | None
    phone: str | None
    address: str | None
    ward: str | None
    city: str
    avatar_url: str | None
    language: str
    role: UserRole
    is_active: bool
    department: DepartmentBrief | None = None
    created_at: datetime
    updated_at: datetime


class ProfileStats(BaseModel):
    total_complaints: int = 0
    open_complaints: int = 0
    resolved_complaints: int = 0
    confirmations_given: int = 0


class MeResponse(BaseModel):
    """`GET /auth/me` — identity plus a small activity summary."""

    profile: ProfileOut
    stats: ProfileStats
    permissions: list[str]


class TokenIntrospection(BaseModel):
    valid: bool
    user_id: uuid.UUID
    email: str | None
    role: UserRole
    expires_at: datetime | None


class RoleUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    role: UserRole = Field(description="Target application role.")
    department_id: uuid.UUID | None = Field(
        default=None, description="Optional department to attach an admin to."
    )


class ActiveUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    is_active: bool
