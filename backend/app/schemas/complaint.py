"""Citizen-facing complaint schemas."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_validator

from app.models.enums import (
    AIAnalysisStatus,
    ComplaintCategory,
    ComplaintSeverity,
    ComplaintStatus,
    UpdateType,
    UserRole,
)
from app.schemas.common import ORMModel, _validate_url
from app.schemas.profile import DepartmentBrief

TitleStr = Annotated[str, StringConstraints(strip_whitespace=True, min_length=5, max_length=200)]
DescriptionStr = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=10, max_length=5000)
]
Latitude = Annotated[float, Field(ge=-90, le=90, description="WGS84 latitude.")]
Longitude = Annotated[float, Field(ge=-180, le=180, description="WGS84 longitude.")]


class ComplaintCreate(BaseModel):
    """Payload for filing a new complaint.

    Note that `category`, `severity` and `priority_score` are **not** accepted
    from the client — they are produced by the AI analysis step. A citizen may
    pass `category_hint` to nudge the classifier.
    """

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "title": "Large pothole near Habibganj underbridge",
                "description": (
                    "A deep pothole has opened up in the left lane just after the "
                    "underbridge. Two-wheelers are swerving into traffic to avoid it "
                    "and it floods whenever it rains."
                ),
                "latitude": 23.2331,
                "longitude": 77.4344,
                "address": "Habibganj Underbridge, Bhopal",
                "landmark": "Opposite the bus stop",
                "ward": "Ward 32",
                "image_url": "https://example.supabase.co/storage/v1/object/public/complaints/pothole.jpg",
                "category_hint": "road",
            }
        },
    )

    title: TitleStr
    description: DescriptionStr
    latitude: Latitude
    longitude: Longitude
    address: Annotated[str, StringConstraints(strip_whitespace=True, max_length=500)] | None = None
    landmark: Annotated[str, StringConstraints(strip_whitespace=True, max_length=200)] | None = None
    ward: Annotated[str, StringConstraints(strip_whitespace=True, max_length=80)] | None = None

    image_url: str | None = Field(
        default=None,
        description="Primary photo URL (upload to Supabase Storage first).",
    )
    image_urls: list[str] = Field(
        default_factory=list, max_length=6, description="Additional photo URLs."
    )
    category_hint: ComplaintCategory | None = Field(
        default=None, description="Optional citizen-suggested category."
    )

    @field_validator("image_url")
    @classmethod
    def _primary_image(cls, value: str | None) -> str | None:
        return _validate_url(value)

    @field_validator("image_urls")
    @classmethod
    def _extra_images(cls, value: list[str]) -> list[str]:
        cleaned = [url for url in (_validate_url(item) for item in value) if url]
        return list(dict.fromkeys(cleaned))  # de-duplicate, preserve order


class ComplaintUpdateByCitizen(BaseModel):
    """A citizen may refine their own report while it is still unacknowledged."""

    model_config = ConfigDict(extra="forbid")

    title: TitleStr | None = None
    description: DescriptionStr | None = None
    address: Annotated[str, StringConstraints(strip_whitespace=True, max_length=500)] | None = None
    landmark: Annotated[str, StringConstraints(strip_whitespace=True, max_length=200)] | None = None
    image_url: str | None = None
    image_urls: list[str] | None = Field(default=None, max_length=6)

    @field_validator("image_url")
    @classmethod
    def _primary_image(cls, value: str | None) -> str | None:
        return _validate_url(value)

    @field_validator("image_urls")
    @classmethod
    def _extra_images(cls, value: list[str] | None) -> list[str] | None:
        if value is None:
            return None
        return [url for url in (_validate_url(item) for item in value) if url]


class CitizenBrief(ORMModel):
    id: uuid.UUID
    full_name: str | None
    ward: str | None


class ComplaintListItem(ORMModel):
    """Compact row used in list views and map pins."""

    id: uuid.UUID
    reference_code: str
    title: str
    category: ComplaintCategory
    severity: ComplaintSeverity
    status: ComplaintStatus
    priority_score: int
    latitude: float
    longitude: float
    address: str | None
    ward: str | None
    image_url: str | None
    confirmation_count: int
    ai_summary: str | None
    department: DepartmentBrief | None = None
    created_at: datetime
    updated_at: datetime


class TimelineEntry(ORMModel):
    id: uuid.UUID
    update_type: UpdateType
    actor_label: str
    actor_role: UserRole | None
    old_value: str | None
    new_value: str | None
    note: str | None
    created_at: datetime


class SimilarComplaint(ORMModel):
    """A linked complaint (duplicate original or a related nearby report).

    ORM-enabled because `ComplaintDetail.duplicate_of` is populated straight
    from the `Complaint.duplicate_of` relationship during validation.
    """

    id: uuid.UUID
    reference_code: str
    title: str
    status: ComplaintStatus
    category: ComplaintCategory
    distance_meters: float | None = None
    confirmation_count: int = 0
    created_at: datetime


class AIAnalysisOut(BaseModel):
    """The AI verdict attached to a complaint."""

    status: AIAnalysisStatus
    summary: str | None = None
    suggested_action: str | None = None
    tags: list[str] = Field(default_factory=list)
    confidence: float | None = None
    model: str | None = None
    analyzed_at: datetime | None = None


class ComplaintDetail(ComplaintListItem):
    """Full complaint view, including the timeline and AI output."""

    description: str
    image_urls: list[str] = Field(default_factory=list)
    citizen: CitizenBrief | None = None
    resolution_notes: str | None = None
    before_image_url: str | None = None
    after_image_url: str | None = None
    acknowledged_at: datetime | None = None
    resolved_at: datetime | None = None
    closed_at: datetime | None = None
    resolution_hours: float | None = None
    duplicate_of: SimilarComplaint | None = None
    similar_complaints: list[SimilarComplaint] = Field(default_factory=list)
    ai_analysis: AIAnalysisOut | None = None
    timeline: list[TimelineEntry] = Field(default_factory=list)


class ComplaintStatusOut(BaseModel):
    """Lightweight status-tracking response."""

    id: uuid.UUID
    reference_code: str
    status: ComplaintStatus
    severity: ComplaintSeverity
    priority_score: int
    department: DepartmentBrief | None = None
    is_open: bool
    sla_hours: int | None = None
    sla_due_at: datetime | None = None
    sla_breached: bool = False
    resolution_hours: float | None = None
    last_update: TimelineEntry | None = None
    timeline: list[TimelineEntry] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class NearbyComplaint(BaseModel):
    """Existing issue a citizen can confirm instead of filing a duplicate."""

    id: uuid.UUID
    reference_code: str
    title: str
    category: ComplaintCategory
    severity: ComplaintSeverity
    status: ComplaintStatus
    latitude: float
    longitude: float
    distance_meters: float
    confirmation_count: int
    image_url: str | None
    already_confirmed_by_me: bool = False
    is_mine: bool = False
    created_at: datetime


class ConfirmRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    note: Annotated[str, StringConstraints(strip_whitespace=True, max_length=500)] | None = (
        Field(default=None, description="Optional extra context from the citizen.")
    )
    latitude: Latitude | None = None
    longitude: Longitude | None = None


class ConfirmResponse(BaseModel):
    complaint_id: uuid.UUID
    reference_code: str
    confirmation_count: int
    priority_score: int
    severity: ComplaintSeverity
    message: str


class ComplaintCreateResponse(BaseModel):
    """Creation result — either a new complaint or a pointer to a duplicate."""

    complaint: ComplaintDetail
    is_duplicate: bool = False
    duplicate_of: SimilarComplaint | None = None
    ai_status: AIAnalysisStatus
    message: str
