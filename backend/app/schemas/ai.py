"""Schemas for the AI endpoints.

`ComplaintAnalysis` is the structured output contract handed to Claude, so it
must stay inside the subset of JSON Schema that structured outputs support:
no numeric bounds, no string length constraints. Ranges are clamped in
`app.services.claude_service` instead.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_validator

from app.models.enums import (
    AIAnalysisStatus,
    ComplaintCategory,
    ComplaintSeverity,
)
from app.schemas.common import _validate_url


class DuplicateCandidate(BaseModel):
    """A nearby open complaint offered to Claude for duplicate detection."""

    reference_code: str
    title: str
    description: str
    category: ComplaintCategory
    status: str
    distance_meters: float
    age_hours: float


class ComplaintAnalysis(BaseModel):
    """Claude's structured verdict on a complaint. Also the API response body."""

    model_config = ConfigDict(extra="forbid")

    category: ComplaintCategory = Field(
        description="Best-fit civic category for this complaint."
    )
    severity: ComplaintSeverity = Field(
        description="How dangerous or disruptive the issue is right now."
    )
    priority_score: int = Field(
        description=(
            "Integer 0-100. Higher means it should be fixed sooner. Weigh public "
            "safety risk, number of people affected, and how fast it will worsen."
        )
    )
    summary: str = Field(
        description="One or two neutral sentences an official can act on."
    )
    department: str = Field(
        description=(
            "Department code that owns the fix. One of: PWD, SWM, ELEC, WATER, "
            "TRAFFIC, DRAIN, GENERAL."
        )
    )
    suggested_action: str = Field(
        description="The concrete next step the department should take."
    )
    tags: list[str] = Field(
        default_factory=list,
        description="Up to five short lowercase keywords for search and analytics.",
    )
    duplicate_of: str | None = Field(
        default=None,
        description=(
            "reference_code of an existing complaint describing the SAME physical "
            "issue at the same spot, or null. Only use codes from the supplied "
            "candidate list."
        ),
    )
    similar_references: list[str] = Field(
        default_factory=list,
        description=(
            "reference_codes of related-but-distinct nearby complaints, from the "
            "candidate list only."
        ),
    )
    confidence: float = Field(
        description="Your confidence in this classification, 0.0 to 1.0."
    )
    reasoning: str | None = Field(
        default=None, description="Short justification for the severity and priority."
    )

    @field_validator("priority_score")
    @classmethod
    def _clamp_priority(cls, value: int) -> int:
        return max(0, min(100, int(value)))

    @field_validator("confidence")
    @classmethod
    def _clamp_confidence(cls, value: float) -> float:
        return max(0.0, min(1.0, float(value)))

    @field_validator("tags")
    @classmethod
    def _tidy_tags(cls, value: list[str]) -> list[str]:
        tags = [tag.strip().lower()[:32] for tag in value if tag and tag.strip()]
        return list(dict.fromkeys(tags))[:5]


class AnalyzeComplaintRequest(BaseModel):
    """Analyse free text without persisting anything (preview before submit)."""

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "title": "Overflowing garbage bin attracting stray dogs",
                "description": (
                    "The community bin next to the park gate has not been emptied for "
                    "four days. Waste is spilling onto the footpath and stray dogs are "
                    "scattering it across the road."
                ),
                "latitude": 23.2599,
                "longitude": 77.4126,
                "check_duplicates": True,
            }
        },
    )

    title: Annotated[str, StringConstraints(strip_whitespace=True, min_length=5, max_length=200)]
    description: Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=10, max_length=5000)
    ]
    latitude: Annotated[float, Field(ge=-90, le=90)] | None = None
    longitude: Annotated[float, Field(ge=-180, le=180)] | None = None
    address: Annotated[str, StringConstraints(strip_whitespace=True, max_length=500)] | None = None
    image_url: str | None = None
    category_hint: ComplaintCategory | None = None
    check_duplicates: bool = Field(
        default=True,
        description="Include nearby-duplicate detection (requires coordinates).",
    )

    @field_validator("image_url")
    @classmethod
    def _image(cls, value: str | None) -> str | None:
        return _validate_url(value)


class AnalyzeComplaintResponse(BaseModel):
    analysis: ComplaintAnalysis
    status: AIAnalysisStatus = Field(
        description="completed = produced by Claude; fallback = deterministic analyser."
    )
    model: str | None = None
    department_id: uuid.UUID | None = None
    department_name: str | None = None
    duplicate_candidates_considered: int = 0
    latency_ms: float | None = None


class ReanalyzeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    complaint_id: uuid.UUID
    apply: bool = Field(
        default=False,
        description="When true, overwrite the stored classification with the new one.",
    )


class BriefingSection(BaseModel):
    heading: str
    body: str


class AdminBriefingResponse(BaseModel):
    """`GET /ai/admin-briefing` — the daily narrative for city officials."""

    generated_at: datetime
    window_hours: int
    headline: str
    briefing: str = Field(description="Markdown briefing for the admin dashboard.")
    priorities: list[str] = Field(
        default_factory=list, description="Ranked actions for today."
    )
    watchlist: list[str] = Field(
        default_factory=list, description="Emerging risks worth monitoring."
    )
    city_health_score: float
    status: AIAnalysisStatus
    model: str | None = None
    metrics_snapshot: dict = Field(default_factory=dict)
