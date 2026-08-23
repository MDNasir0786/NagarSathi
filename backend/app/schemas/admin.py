"""Admin-only schemas: complaint moderation, evidence and dashboard."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Annotated

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StringConstraints,
    field_validator,
    model_validator,
)

from app.models.enums import (
    ComplaintCategory,
    ComplaintSeverity,
    ComplaintStatus,
    UserRole,
)
from app.schemas.common import ORMModel, _validate_url

NoteStr = Annotated[str, StringConstraints(strip_whitespace=True, max_length=2000)]


class AdminComplaintPatch(BaseModel):
    """Every field an admin can change on a complaint, in one call.

    Only the keys present in the request body are applied, and each change is
    recorded in the complaint's audit trail.
    """

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "status": "in_progress",
                "department_id": "00000000-0000-0000-0000-000000000000",
                "priority_score": 88,
                "resolution_notes": "Repair crew scheduled for tomorrow morning.",
            }
        },
    )

    status: ComplaintStatus | None = None
    category: ComplaintCategory | None = None
    severity: ComplaintSeverity | None = None
    priority_score: Annotated[int, Field(ge=0, le=100)] | None = None
    department_id: uuid.UUID | None = None
    assigned_to_id: uuid.UUID | None = None
    resolution_notes: NoteStr | None = None
    before_image_url: str | None = None
    after_image_url: str | None = None
    duplicate_of_id: uuid.UUID | None = None
    #: Recorded on the timeline but hidden from the citizen-facing view.
    internal_note: NoteStr | None = None
    #: Note attached to the status change and shown to the citizen.
    public_note: NoteStr | None = None

    @field_validator("before_image_url", "after_image_url")
    @classmethod
    def _urls(cls, value: str | None) -> str | None:
        return _validate_url(value)

    @model_validator(mode="after")
    def _at_least_one_change(self) -> AdminComplaintPatch:
        if not self.model_dump(exclude_unset=True):
            raise ValueError("Provide at least one field to update.")
        return self

    def changes(self) -> dict:
        return self.model_dump(exclude_unset=True)


class EvidenceRequest(BaseModel):
    """Attach before/after photographic evidence of the fix."""

    model_config = ConfigDict(extra="forbid")

    before_image_url: str | None = None
    after_image_url: str | None = None
    note: NoteStr | None = None

    @field_validator("before_image_url", "after_image_url")
    @classmethod
    def _urls(cls, value: str | None) -> str | None:
        return _validate_url(value)

    @model_validator(mode="after")
    def _needs_one(self) -> EvidenceRequest:
        if not self.before_image_url and not self.after_image_url:
            raise ValueError("Provide before_image_url and/or after_image_url.")
        return self


class DepartmentCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: Annotated[str, StringConstraints(strip_whitespace=True, min_length=2, max_length=120)]
    code: Annotated[
        str,
        StringConstraints(
            strip_whitespace=True, to_upper=True, min_length=2, max_length=32, pattern=r"^[A-Z0-9_]+$"
        ),
    ]
    description: NoteStr | None = None
    contact_email: str | None = None
    contact_phone: str | None = None
    categories: list[ComplaintCategory] = Field(default_factory=list)
    sla_hours: Annotated[int, Field(ge=1, le=8760)] = 72


class DepartmentUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: Annotated[str, StringConstraints(strip_whitespace=True, min_length=2, max_length=120)] | None = None
    description: NoteStr | None = None
    contact_email: str | None = None
    contact_phone: str | None = None
    categories: list[ComplaintCategory] | None = None
    sla_hours: Annotated[int, Field(ge=1, le=8760)] | None = None
    is_active: bool | None = None

    def changes(self) -> dict:
        return self.model_dump(exclude_unset=True)


class DepartmentOut(ORMModel):
    id: uuid.UUID
    name: str
    code: str
    description: str | None
    contact_email: str | None
    contact_phone: str | None
    categories: list[str]
    sla_hours: int
    is_active: bool
    created_at: datetime


class UserAdminOut(ORMModel):
    id: uuid.UUID
    email: str
    full_name: str | None
    phone: str | None
    ward: str | None
    role: UserRole
    is_active: bool
    department_id: uuid.UUID | None
    created_at: datetime


class StatusCount(BaseModel):
    status: ComplaintStatus
    count: int


class CategoryCount(BaseModel):
    category: ComplaintCategory
    count: int


class SeverityCount(BaseModel):
    severity: ComplaintSeverity
    count: int


class DepartmentLoad(BaseModel):
    department_id: uuid.UUID | None
    department_name: str
    open_count: int
    resolved_count: int
    total_count: int


class DashboardStats(BaseModel):
    """`GET /admin/dashboard` — the numbers that drive the admin home screen."""

    generated_at: datetime
    window_days: int

    total_complaints: int
    open_complaints: int
    resolved_complaints: int
    unassigned_complaints: int
    critical_open: int
    duplicates: int

    new_today: int
    new_this_week: int
    resolved_this_week: int

    resolution_rate: float = Field(description="Resolved / total, 0-1.")
    avg_resolution_hours: float | None
    median_resolution_hours: float | None
    sla_breached_open: int
    avg_priority_score: float

    by_status: list[StatusCount]
    by_category: list[CategoryCount]
    by_severity: list[SeverityCount]
    by_department: list[DepartmentLoad]

    top_wards: list[dict]
    city_health_score: float
    total_citizens: int
    total_confirmations: int
