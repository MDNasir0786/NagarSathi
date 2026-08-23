"""Smart-city analytics schemas."""

from __future__ import annotations

import uuid
from datetime import date, datetime

from pydantic import BaseModel, Field

from app.models.enums import ComplaintCategory, ComplaintSeverity


class HotspotComplaintBrief(BaseModel):
    id: uuid.UUID
    reference_code: str
    title: str
    category: ComplaintCategory
    severity: ComplaintSeverity


class Hotspot(BaseModel):
    """A geographic cluster of civic issues."""

    cluster_id: str = Field(description="Stable id for the grid cell.")
    center_latitude: float
    center_longitude: float
    radius_meters: float
    complaint_count: int
    open_count: int
    resolved_count: int
    confirmation_count: int
    intensity: float = Field(description="Normalised 0-1 severity-weighted density.")
    dominant_category: ComplaintCategory
    categories: dict[str, int]
    max_severity: ComplaintSeverity
    avg_priority_score: float
    wards: list[str] = Field(default_factory=list)
    sample_complaints: list[HotspotComplaintBrief] = Field(default_factory=list)
    first_reported_at: datetime
    last_reported_at: datetime


class HotspotResponse(BaseModel):
    generated_at: datetime
    window_days: int
    grid_meters: int
    min_complaints: int
    total_hotspots: int
    hotspots: list[Hotspot]


class CategoryStat(BaseModel):
    category: ComplaintCategory
    total: int
    open_count: int
    resolved_count: int
    share: float = Field(description="Share of all complaints in the window, 0-1.")
    avg_priority_score: float
    avg_resolution_hours: float | None
    resolution_rate: float
    trend_pct: float = Field(
        description="Change vs the previous equal-length window, in percent."
    )


class CategoryStatsResponse(BaseModel):
    generated_at: datetime
    window_days: int
    total_complaints: int
    categories: list[CategoryStat]


class DepartmentPerformance(BaseModel):
    department_id: uuid.UUID | None
    department_name: str
    department_code: str | None
    assigned: int
    resolved: int
    open_count: int
    overdue: int = Field(description="Open complaints past their SLA.")
    resolution_rate: float
    avg_resolution_hours: float | None
    sla_hours: int | None
    sla_compliance: float = Field(description="Resolved within SLA / resolved, 0-1.")
    performance_score: float = Field(description="Composite 0-100 score.")
    grade: str


class DepartmentPerformanceResponse(BaseModel):
    generated_at: datetime
    window_days: int
    departments: list[DepartmentPerformance]


class TrendPoint(BaseModel):
    bucket: date
    total: int
    resolved: int
    by_category: dict[str, int] = Field(default_factory=dict)


class TrendingIssue(BaseModel):
    category: ComplaintCategory
    recent_count: int
    previous_count: int
    change_pct: float
    direction: str = Field(description="rising | falling | stable")
    sample_titles: list[str] = Field(default_factory=list)
    top_ward: str | None = None


class TrendsResponse(BaseModel):
    generated_at: datetime
    window_days: int
    granularity: str
    series: list[TrendPoint]
    trending: list[TrendingIssue]
    busiest_day: date | None = None
    total_in_window: int = 0


class CityHealthScore(BaseModel):
    """A single composite indicator of civic responsiveness."""

    generated_at: datetime
    window_days: int
    score: float = Field(description="0-100, higher is healthier.")
    grade: str
    trend: str = Field(description="improving | worsening | stable")
    components: dict[str, float] = Field(
        description="Sub-scores: resolution, speed, backlog, severity, engagement."
    )
    open_complaints: int
    resolved_complaints: int
    avg_resolution_hours: float | None
    critical_open: int
    worst_category: ComplaintCategory | None = None
    best_category: ComplaintCategory | None = None
    headline: str
