"""Smart-city analytics: hotspots, category stats, department performance,
trends and the composite city-health score.

All aggregation is portable SQL plus in-Python post-processing, so the same
code runs on Supabase Postgres and on SQLite without PostGIS.
"""

from __future__ import annotations

import logging
import statistics
from collections import Counter, defaultdict
from datetime import UTC, date, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database.base import utcnow
from app.models import (
    OPEN_STATUSES,
    Complaint,
    ComplaintCategory,
    ComplaintConfirmation,
    ComplaintSeverity,
    ComplaintStatus,
    Department,
    Profile,
    UserRole,
)
from app.schemas.analytics import (
    CategoryStat,
    CategoryStatsResponse,
    CityHealthScore,
    DepartmentPerformance,
    DepartmentPerformanceResponse,
    Hotspot,
    HotspotComplaintBrief,
    HotspotResponse,
    TrendingIssue,
    TrendPoint,
    TrendsResponse,
)
from app.utils.config import settings
from app.utils.geo import grid_cell, grid_cell_center

logger = logging.getLogger(__name__)

SEVERITY_INTENSITY = {
    ComplaintSeverity.LOW: 1.0,
    ComplaintSeverity.MEDIUM: 2.0,
    ComplaintSeverity.HIGH: 3.5,
    ComplaintSeverity.CRITICAL: 5.0,
}
_SEVERITY_RANK = {
    ComplaintSeverity.LOW: 0,
    ComplaintSeverity.MEDIUM: 1,
    ComplaintSeverity.HIGH: 2,
    ComplaintSeverity.CRITICAL: 3,
}

#: Target turnaround used to normalise the "speed" health component.
SPEED_TARGET_HOURS = 72.0
SPEED_WORST_HOURS = 336.0  # two weeks


def _aware(value: datetime | None) -> datetime | None:
    """SQLite hands back naive datetimes; normalise everything to UTC."""
    if value is None:
        return None
    return value if value.tzinfo else value.replace(tzinfo=UTC)


def _window_start(days: int) -> datetime:
    return utcnow() - timedelta(days=days)


def _grade(score: float) -> str:
    if score >= 90:
        return "A+"
    if score >= 80:
        return "A"
    if score >= 70:
        return "B"
    if score >= 60:
        return "C"
    if score >= 50:
        return "D"
    return "E"


def _resolution_hours(complaint: Complaint) -> float | None:
    resolved = _aware(complaint.resolved_at)
    created = _aware(complaint.created_at)
    if resolved is None or created is None:
        return None
    return (resolved - created).total_seconds() / 3600


def _fetch_window(
    db: Session, window_days: int, *, category: ComplaintCategory | None = None
) -> list[Complaint]:
    stmt = select(Complaint).where(Complaint.created_at >= _window_start(window_days))
    if category is not None:
        stmt = stmt.where(Complaint.category == category)
    return list(db.scalars(stmt).all())


# ---------------------------------------------------------------------------
# Hotspots
# ---------------------------------------------------------------------------


def hotspots(
    db: Session,
    *,
    window_days: int = 30,
    min_complaints: int | None = None,
    grid_meters: int | None = None,
    category: ComplaintCategory | None = None,
    open_only: bool = False,
    limit: int = 50,
) -> HotspotResponse:
    """Cluster complaints onto a metre-scale grid and rank by intensity."""
    cell_size = grid_meters or settings.hotspot_grid_meters
    threshold = min_complaints or settings.hotspot_min_complaints

    complaints = _fetch_window(db, window_days, category=category)
    if open_only:
        complaints = [c for c in complaints if c.status in OPEN_STATUSES]

    buckets: dict[tuple[int, int], list[Complaint]] = defaultdict(list)
    for complaint in complaints:
        buckets[grid_cell(complaint.latitude, complaint.longitude, cell_size)].append(
            complaint
        )

    raw: list[tuple[float, Hotspot]] = []
    for cell, members in buckets.items():
        if len(members) < threshold:
            continue

        weighted = sum(SEVERITY_INTENSITY[member.severity] for member in members)
        confirmations = sum(member.confirmation_count or 0 for member in members)
        category_counter = Counter(member.category.value for member in members)
        dominant = ComplaintCategory(category_counter.most_common(1)[0][0])
        max_severity = max(members, key=lambda m: _SEVERITY_RANK[m.severity]).severity
        created = [_aware(m.created_at) for m in members]
        wards = sorted({m.ward for m in members if m.ward})
        center_lat, center_lon = grid_cell_center(
            cell, cell_size, reference_lat=members[0].latitude
        )
        top = sorted(members, key=lambda m: m.priority_score or 0, reverse=True)[:3]

        hotspot = Hotspot(
            cluster_id=f"{cell[0]}:{cell[1]}:{cell_size}",
            center_latitude=center_lat,
            center_longitude=center_lon,
            radius_meters=float(cell_size) / 2,
            complaint_count=len(members),
            open_count=sum(1 for m in members if m.status in OPEN_STATUSES),
            resolved_count=sum(
                1 for m in members if m.status is ComplaintStatus.RESOLVED
            ),
            confirmation_count=confirmations,
            intensity=0.0,  # normalised below
            dominant_category=dominant,
            categories=dict(category_counter),
            max_severity=max_severity,
            avg_priority_score=round(
                sum(m.priority_score or 0 for m in members) / len(members), 1
            ),
            wards=wards,
            sample_complaints=[
                HotspotComplaintBrief(
                    id=m.id,
                    reference_code=m.reference_code,
                    title=m.title,
                    category=m.category,
                    severity=m.severity,
                )
                for m in top
            ],
            first_reported_at=min(created),  # type: ignore[arg-type]
            last_reported_at=max(created),  # type: ignore[arg-type]
        )
        raw.append((weighted + confirmations * 0.5, hotspot))

    if raw:
        peak = max(score for score, _ in raw) or 1.0
        for score, hotspot in raw:
            hotspot.intensity = round(min(score / peak, 1.0), 3)

    raw.sort(key=lambda pair: pair[0], reverse=True)
    ranked = [hotspot for _, hotspot in raw[:limit]]

    return HotspotResponse(
        generated_at=utcnow(),
        window_days=window_days,
        grid_meters=cell_size,
        min_complaints=threshold,
        total_hotspots=len(raw),
        hotspots=ranked,
    )


# ---------------------------------------------------------------------------
# Category statistics
# ---------------------------------------------------------------------------


def category_stats(db: Session, *, window_days: int = 30) -> CategoryStatsResponse:
    current = _fetch_window(db, window_days)
    previous_start = _window_start(window_days * 2)
    previous_end = _window_start(window_days)
    previous = list(
        db.scalars(
            select(Complaint).where(
                Complaint.created_at >= previous_start,
                Complaint.created_at < previous_end,
            )
        ).all()
    )

    total = len(current)
    previous_counts = Counter(item.category for item in previous)
    grouped: dict[ComplaintCategory, list[Complaint]] = defaultdict(list)
    for complaint in current:
        grouped[complaint.category].append(complaint)

    stats: list[CategoryStat] = []
    for category in ComplaintCategory:
        members = grouped.get(category, [])
        count = len(members)
        resolved = [m for m in members if m.status is ComplaintStatus.RESOLVED]
        durations = [h for h in (_resolution_hours(m) for m in resolved) if h is not None]
        before = previous_counts.get(category, 0)
        # No prior baseline: report +100% when the category appeared, else flat.
        trend = ((count - before) / before) * 100 if before else (100.0 if count else 0.0)

        stats.append(
            CategoryStat(
                category=category,
                total=count,
                open_count=sum(1 for m in members if m.status in OPEN_STATUSES),
                resolved_count=len(resolved),
                share=round(count / total, 4) if total else 0.0,
                avg_priority_score=(
                    round(sum(m.priority_score or 0 for m in members) / count, 1)
                    if count
                    else 0.0
                ),
                avg_resolution_hours=(
                    round(sum(durations) / len(durations), 1) if durations else None
                ),
                resolution_rate=round(len(resolved) / count, 4) if count else 0.0,
                trend_pct=round(trend, 1),
            )
        )

    stats.sort(key=lambda item: item.total, reverse=True)
    return CategoryStatsResponse(
        generated_at=utcnow(),
        window_days=window_days,
        total_complaints=total,
        categories=stats,
    )


# ---------------------------------------------------------------------------
# Department performance
# ---------------------------------------------------------------------------


def department_performance(
    db: Session, *, window_days: int = 30
) -> DepartmentPerformanceResponse:
    departments = list(db.scalars(select(Department)).all())
    complaints = _fetch_window(db, window_days)

    by_department: dict[str | None, list[Complaint]] = defaultdict(list)
    for complaint in complaints:
        by_department[str(complaint.department_id) if complaint.department_id else None].append(
            complaint
        )

    now = utcnow()
    rows: list[DepartmentPerformance] = []

    def build(
        key: str | None,
        name: str,
        code: str | None,
        sla_hours: int | None,
        members: list[Complaint],
    ) -> DepartmentPerformance:
        resolved = [m for m in members if m.status is ComplaintStatus.RESOLVED]
        durations = [h for h in (_resolution_hours(m) for m in resolved) if h is not None]
        open_members = [m for m in members if m.status in OPEN_STATUSES]
        overdue = 0
        if sla_hours:
            for member in open_members:
                created = _aware(member.created_at)
                if created and (now - created).total_seconds() / 3600 > sla_hours:
                    overdue += 1
        within_sla = (
            sum(1 for h in durations if sla_hours and h <= sla_hours) if sla_hours else 0
        )
        compliance = (within_sla / len(durations)) if durations and sla_hours else 0.0
        resolution_rate = (len(resolved) / len(members)) if members else 0.0
        avg_hours = (sum(durations) / len(durations)) if durations else None

        # Composite: 50% throughput, 30% SLA compliance, 20% speed.
        speed_component = 0.0
        if avg_hours is not None:
            speed_component = max(
                0.0, min(1.0, 1 - (avg_hours - SPEED_TARGET_HOURS) / SPEED_WORST_HOURS)
            )
        score = 100 * (0.5 * resolution_rate + 0.3 * compliance + 0.2 * speed_component)
        if not members:
            score = 0.0

        return DepartmentPerformance(
            department_id=members[0].department_id if key and members else None,
            department_name=name,
            department_code=code,
            assigned=len(members),
            resolved=len(resolved),
            open_count=len(open_members),
            overdue=overdue,
            resolution_rate=round(resolution_rate, 4),
            avg_resolution_hours=round(avg_hours, 1) if avg_hours is not None else None,
            sla_hours=sla_hours,
            sla_compliance=round(compliance, 4),
            performance_score=round(score, 1),
            grade=_grade(score),
        )

    for department in departments:
        members = by_department.get(str(department.id), [])
        rows.append(
            build(
                str(department.id),
                department.name,
                department.code,
                department.sla_hours,
                members,
            )
        )

    unassigned = by_department.get(None, [])
    if unassigned:
        rows.append(build(None, "Unassigned", None, None, unassigned))

    rows.sort(key=lambda row: (row.performance_score, row.resolved), reverse=True)
    return DepartmentPerformanceResponse(
        generated_at=utcnow(), window_days=window_days, departments=rows
    )


# ---------------------------------------------------------------------------
# Trends
# ---------------------------------------------------------------------------


def _bucket_key(moment: datetime, granularity: str) -> date:
    aware = _aware(moment)
    assert aware is not None
    if granularity == "week":
        return (aware - timedelta(days=aware.weekday())).date()
    if granularity == "month":
        return aware.date().replace(day=1)
    return aware.date()


def trends(
    db: Session, *, window_days: int = 30, granularity: str = "day"
) -> TrendsResponse:
    if granularity not in {"day", "week", "month"}:
        granularity = "day"

    complaints = _fetch_window(db, window_days)
    series_map: dict[date, dict] = defaultdict(
        lambda: {"total": 0, "resolved": 0, "by_category": Counter()}
    )
    for complaint in complaints:
        bucket = series_map[_bucket_key(complaint.created_at, granularity)]
        bucket["total"] += 1
        bucket["by_category"][complaint.category.value] += 1
        if complaint.status is ComplaintStatus.RESOLVED:
            bucket["resolved"] += 1

    series = [
        TrendPoint(
            bucket=bucket,
            total=values["total"],
            resolved=values["resolved"],
            by_category=dict(values["by_category"]),
        )
        for bucket, values in sorted(series_map.items())
    ]

    # Trending: last third of the window vs the third before it.
    split_days = max(1, window_days // 3)
    recent_cutoff = utcnow() - timedelta(days=split_days)
    previous_cutoff = utcnow() - timedelta(days=split_days * 2)

    recent = [c for c in complaints if (_aware(c.created_at) or utcnow()) >= recent_cutoff]
    previous = [
        c
        for c in complaints
        if previous_cutoff <= (_aware(c.created_at) or utcnow()) < recent_cutoff
    ]
    recent_counts = Counter(c.category for c in recent)
    previous_counts = Counter(c.category for c in previous)

    trending: list[TrendingIssue] = []
    for category in ComplaintCategory:
        recent_count = recent_counts.get(category, 0)
        previous_count = previous_counts.get(category, 0)
        if not recent_count and not previous_count:
            continue
        if previous_count:
            change = ((recent_count - previous_count) / previous_count) * 100
        else:
            change = 100.0 * recent_count
        if change > 20:
            direction = "rising"
        elif change < -20:
            direction = "falling"
        else:
            direction = "stable"
        wards = Counter(c.ward for c in recent if c.category is category and c.ward)
        trending.append(
            TrendingIssue(
                category=category,
                recent_count=recent_count,
                previous_count=previous_count,
                change_pct=round(change, 1),
                direction=direction,
                sample_titles=[
                    c.title for c in recent if c.category is category
                ][:3],
                top_ward=wards.most_common(1)[0][0] if wards else None,
            )
        )

    trending.sort(key=lambda item: (item.recent_count, item.change_pct), reverse=True)
    busiest = max(series, key=lambda point: point.total).bucket if series else None

    return TrendsResponse(
        generated_at=utcnow(),
        window_days=window_days,
        granularity=granularity,
        series=series,
        trending=trending,
        busiest_day=busiest,
        total_in_window=len(complaints),
    )


# ---------------------------------------------------------------------------
# City health score
# ---------------------------------------------------------------------------


def _score_for(complaints: list[Complaint], confirmations: int) -> tuple[float, dict]:
    total = len(complaints)
    if not total:
        return 0.0, {
            "resolution": 0.0,
            "speed": 0.0,
            "backlog": 0.0,
            "severity": 0.0,
            "engagement": 0.0,
        }

    resolved = [c for c in complaints if c.status is ComplaintStatus.RESOLVED]
    open_members = [c for c in complaints if c.status in OPEN_STATUSES]
    durations = [h for h in (_resolution_hours(c) for c in resolved) if h is not None]
    critical_open = sum(
        1 for c in open_members if c.severity is ComplaintSeverity.CRITICAL
    )

    resolution = len(resolved) / total
    if durations:
        avg_hours = sum(durations) / len(durations)
        speed = max(
            0.0, min(1.0, 1 - (avg_hours - SPEED_TARGET_HOURS) / SPEED_WORST_HOURS)
        )
    else:
        speed = 0.35  # nothing resolved yet: neutral-low, not zero
    backlog = 1 - (len(open_members) / total)
    severity = max(0.0, 1 - (critical_open / max(total, 1)) * 4)
    engagement = min(1.0, confirmations / total) if total else 0.0

    components = {
        "resolution": round(resolution * 100, 1),
        "speed": round(speed * 100, 1),
        "backlog": round(backlog * 100, 1),
        "severity": round(severity * 100, 1),
        "engagement": round(engagement * 100, 1),
    }
    score = (
        0.30 * resolution
        + 0.20 * speed
        + 0.20 * backlog
        + 0.15 * severity
        + 0.15 * engagement
    ) * 100
    return round(score, 1), components


def city_health(db: Session, *, window_days: int = 30) -> CityHealthScore:
    current = _fetch_window(db, window_days)
    confirmations = db.scalar(
        select(func.count())
        .select_from(ComplaintConfirmation)
        .where(ComplaintConfirmation.created_at >= _window_start(window_days))
    ) or 0
    score, components = _score_for(current, confirmations)

    previous = list(
        db.scalars(
            select(Complaint).where(
                Complaint.created_at >= _window_start(window_days * 2),
                Complaint.created_at < _window_start(window_days),
            )
        ).all()
    )
    previous_confirmations = db.scalar(
        select(func.count())
        .select_from(ComplaintConfirmation)
        .where(
            ComplaintConfirmation.created_at >= _window_start(window_days * 2),
            ComplaintConfirmation.created_at < _window_start(window_days),
        )
    ) or 0
    previous_score, _ = _score_for(previous, previous_confirmations)

    delta = score - previous_score
    if not previous:
        trend = "stable"
    elif delta > 3:
        trend = "improving"
    elif delta < -3:
        trend = "worsening"
    else:
        trend = "stable"

    resolved = [c for c in current if c.status is ComplaintStatus.RESOLVED]
    open_members = [c for c in current if c.status in OPEN_STATUSES]
    durations = [h for h in (_resolution_hours(c) for c in resolved) if h is not None]

    category_rates: dict[ComplaintCategory, float] = {}
    grouped: dict[ComplaintCategory, list[Complaint]] = defaultdict(list)
    for complaint in current:
        grouped[complaint.category].append(complaint)
    for category, members in grouped.items():
        if len(members) >= 3:
            category_rates[category] = sum(
                1 for m in members if m.status is ComplaintStatus.RESOLVED
            ) / len(members)

    worst = min(category_rates, key=category_rates.get) if category_rates else None  # type: ignore[arg-type]
    best = max(category_rates, key=category_rates.get) if category_rates else None  # type: ignore[arg-type]

    critical_open = sum(
        1 for c in open_members if c.severity is ComplaintSeverity.CRITICAL
    )
    headline = (
        f"{settings.city_name} civic health is {_grade(score)} ({score}/100), "
        f"{trend} versus the previous {window_days} days — "
        f"{len(open_members)} open of {len(current)} reported."
    )

    return CityHealthScore(
        generated_at=utcnow(),
        window_days=window_days,
        score=score,
        grade=_grade(score),
        trend=trend,
        components=components,
        open_complaints=len(open_members),
        resolved_complaints=len(resolved),
        avg_resolution_hours=(
            round(sum(durations) / len(durations), 1) if durations else None
        ),
        critical_open=critical_open,
        worst_category=worst,
        best_category=best,
        headline=headline,
    )


# ---------------------------------------------------------------------------
# Metrics snapshot for the AI briefing
# ---------------------------------------------------------------------------


def briefing_metrics(db: Session, *, window_hours: int = 24) -> dict:
    """Compact, JSON-serialisable metrics snapshot handed to Claude."""
    window_start = utcnow() - timedelta(hours=window_hours)
    previous_start = utcnow() - timedelta(hours=window_hours * 2)

    new_complaints = list(
        db.scalars(select(Complaint).where(Complaint.created_at >= window_start)).all()
    )
    previous_complaints = list(
        db.scalars(
            select(Complaint).where(
                Complaint.created_at >= previous_start,
                Complaint.created_at < window_start,
            )
        ).all()
    )
    all_open = list(
        db.scalars(
            select(Complaint).where(Complaint.status.in_(list(OPEN_STATUSES)))
        ).all()
    )
    resolved_in_window = db.scalar(
        select(func.count())
        .select_from(Complaint)
        .where(
            Complaint.status == ComplaintStatus.RESOLVED,
            Complaint.resolved_at >= window_start,
        )
    ) or 0

    category_counter = Counter(c.category.value for c in new_complaints)
    previous_categories = Counter(c.category.value for c in previous_complaints)
    ward_counter = Counter(c.ward for c in new_complaints if c.ward)

    departments = {
        str(department.id): department
        for department in db.scalars(select(Department)).all()
    }
    department_backlog: Counter[str] = Counter()
    overdue = 0
    now = utcnow()
    for complaint in all_open:
        key = (
            departments[str(complaint.department_id)].code
            if complaint.department_id and str(complaint.department_id) in departments
            else "UNASSIGNED"
        )
        department_backlog[key] += 1
        sla = (
            departments[str(complaint.department_id)].sla_hours
            if complaint.department_id and str(complaint.department_id) in departments
            else None
        )
        created = _aware(complaint.created_at)
        if sla and created and (now - created).total_seconds() / 3600 > sla:
            overdue += 1

    health = city_health(db, window_days=max(1, window_hours // 24 or 1) * 7)

    durations: list[float] = []
    for complaint in db.scalars(
        select(Complaint).where(Complaint.resolved_at.is_not(None))
    ).all():
        hours = _resolution_hours(complaint)
        if hours is not None:
            durations.append(hours)

    return {
        "city": settings.city_name,
        "window_hours": window_hours,
        "new_complaints": len(new_complaints),
        "new_complaints_previous_window": len(previous_complaints),
        "resolved_in_window": resolved_in_window,
        "open_complaints": len(all_open),
        "critical_open": sum(
            1 for c in all_open if c.severity is ComplaintSeverity.CRITICAL
        ),
        "high_open": sum(1 for c in all_open if c.severity is ComplaintSeverity.HIGH),
        "unassigned_complaints": sum(1 for c in all_open if c.department_id is None),
        "sla_breached_open": overdue,
        "new_by_category": dict(category_counter),
        "previous_by_category": dict(previous_categories),
        "top_category": (
            category_counter.most_common(1)[0][0] if category_counter else None
        ),
        "top_wards": ward_counter.most_common(5),
        "open_backlog_by_department": dict(department_backlog),
        "avg_resolution_hours_all_time": (
            round(sum(durations) / len(durations), 1) if durations else None
        ),
        "median_resolution_hours_all_time": (
            round(statistics.median(durations), 1) if durations else None
        ),
        "city_health_score": health.score,
        "city_health_grade": health.grade,
        "city_health_trend": health.trend,
        "city_health_components": health.components,
        "worst_performing_category": (
            health.worst_category.value if health.worst_category else None
        ),
        "total_citizens": db.scalar(
            select(func.count())
            .select_from(Profile)
            .where(Profile.role == UserRole.CITIZEN)
        )
        or 0,
    }
