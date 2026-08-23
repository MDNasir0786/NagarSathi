"""Admin operations: dashboard aggregation, complaint moderation, departments."""

from __future__ import annotations

import logging
import statistics
import uuid
from collections import Counter
from datetime import timedelta

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
    UpdateType,
    UserRole,
)
from app.schemas.admin import (
    AdminComplaintPatch,
    CategoryCount,
    DashboardStats,
    DepartmentCreate,
    DepartmentLoad,
    DepartmentUpdate,
    EvidenceRequest,
    SeverityCount,
    StatusCount,
)
from app.services import analytics_service
from app.services.complaint_service import record_update
from app.utils.errors import ConflictError, NotFoundError, ValidationError

logger = logging.getLogger(__name__)

#: Statuses that require a resolution note before they can be set.
_REQUIRES_NOTE = {ComplaintStatus.RESOLVED, ComplaintStatus.REJECTED}


# ---------------------------------------------------------------------------
# Complaint moderation
# ---------------------------------------------------------------------------


def _apply_status_change(
    db: Session,
    complaint: Complaint,
    new_status: ComplaintStatus,
    *,
    admin: Profile,
    note: str | None,
    has_resolution_note: bool,
) -> None:
    old_status = complaint.status
    if old_status is new_status:
        return

    if new_status in _REQUIRES_NOTE and not (
        has_resolution_note or complaint.resolution_notes
    ):
        raise ValidationError(
            f"A resolution note is required when marking a complaint {new_status.value}.",
            code="resolution_note_required",
        )

    now = utcnow()
    complaint.status = new_status

    if new_status is ComplaintStatus.ACKNOWLEDGED and not complaint.acknowledged_at:
        complaint.acknowledged_at = now
    elif new_status is ComplaintStatus.RESOLVED:
        complaint.resolved_at = now
        complaint.acknowledged_at = complaint.acknowledged_at or now
    elif new_status is ComplaintStatus.CLOSED:
        complaint.closed_at = now
    elif new_status in OPEN_STATUSES:
        # Reopening: clear terminal timestamps so SLA maths stays truthful.
        complaint.resolved_at = None
        complaint.closed_at = None

    record_update(
        db,
        complaint,
        update_type=UpdateType.STATUS_CHANGE,
        actor=admin,
        old_value=old_status.value,
        new_value=new_status.value,
        note=note,
    )


def patch_complaint(
    db: Session,
    complaint: Complaint,
    admin: Profile,
    payload: AdminComplaintPatch,
) -> Complaint:
    """Apply an admin's changes, writing one audit entry per changed field."""
    changes = payload.changes()
    public_note = changes.pop("public_note", None)
    internal_note = changes.pop("internal_note", None)
    new_status = changes.pop("status", None)

    if "department_id" in changes:
        department_id = changes.pop("department_id")
        department = db.get(Department, department_id) if department_id else None
        if department_id and department is None:
            raise NotFoundError("Department not found.")
        old = complaint.department.code if complaint.department else None
        complaint.department_id = department_id
        record_update(
            db,
            complaint,
            update_type=UpdateType.DEPARTMENT_ASSIGNED,
            actor=admin,
            old_value=old,
            new_value=department.code if department else None,
            note=f"Routed to {department.name}." if department else "Department cleared.",
        )
        # Assignment implies work has started moving.
        if department is not None and complaint.status is ComplaintStatus.SUBMITTED and not new_status:
            new_status = ComplaintStatus.ASSIGNED

    if "assigned_to_id" in changes:
        assignee_id = changes.pop("assigned_to_id")
        assignee = db.get(Profile, assignee_id) if assignee_id else None
        if assignee_id:
            if assignee is None:
                raise NotFoundError("Assignee not found.")
            if assignee.role is not UserRole.ADMIN:
                raise ValidationError(
                    "Complaints can only be assigned to municipal staff (admins).",
                    code="invalid_assignee",
                )
        complaint.assigned_to_id = assignee_id
        record_update(
            db,
            complaint,
            update_type=UpdateType.ASSIGNEE_CHANGE,
            actor=admin,
            new_value=assignee.email if assignee else None,
        )

    if "priority_score" in changes:
        value = changes.pop("priority_score")
        old = complaint.priority_score
        complaint.priority_score = value
        record_update(
            db,
            complaint,
            update_type=UpdateType.PRIORITY_CHANGE,
            actor=admin,
            old_value=old,
            new_value=value,
            note="Priority adjusted by municipal staff.",
        )

    if "severity" in changes:
        value = changes.pop("severity")
        old = complaint.severity
        complaint.severity = value
        record_update(
            db,
            complaint,
            update_type=UpdateType.SEVERITY_CHANGE,
            actor=admin,
            old_value=old.value,
            new_value=value.value,
        )

    if "category" in changes:
        value = changes.pop("category")
        old = complaint.category
        complaint.category = value
        record_update(
            db,
            complaint,
            update_type=UpdateType.CATEGORY_CHANGE,
            actor=admin,
            old_value=old.value,
            new_value=value.value,
            note="Category corrected by municipal staff.",
        )

    if "duplicate_of_id" in changes:
        duplicate_of_id = changes.pop("duplicate_of_id")
        if duplicate_of_id:
            if duplicate_of_id == complaint.id:
                raise ValidationError(
                    "A complaint cannot be a duplicate of itself.",
                    code="self_duplicate",
                )
            original = db.get(Complaint, duplicate_of_id)
            if original is None:
                raise NotFoundError("The original complaint was not found.")
            complaint.duplicate_of_id = original.id
            if not new_status:
                new_status = ComplaintStatus.DUPLICATE
            record_update(
                db,
                complaint,
                update_type=UpdateType.DUPLICATE_LINKED,
                actor=admin,
                new_value=original.reference_code,
                note=f"Marked as duplicate of {original.reference_code}.",
            )
        else:
            complaint.duplicate_of_id = None

    has_resolution_note = False
    if "resolution_notes" in changes:
        value = changes.pop("resolution_notes")
        complaint.resolution_notes = value
        has_resolution_note = bool(value)
        record_update(
            db,
            complaint,
            update_type=UpdateType.RESOLUTION_NOTE,
            actor=admin,
            note=value,
        )

    evidence_fields = {
        key: changes.pop(key)
        for key in ("before_image_url", "after_image_url")
        if key in changes
    }
    if evidence_fields:
        for key, value in evidence_fields.items():
            setattr(complaint, key, value)
        record_update(
            db,
            complaint,
            update_type=UpdateType.EVIDENCE_ADDED,
            actor=admin,
            new_value=", ".join(sorted(evidence_fields)),
            note="Photographic evidence attached.",
        )

    # Anything left is an unexpected field; the schema forbids extras, so this
    # only guards against future drift.
    if changes:
        raise ValidationError(
            f"Unsupported fields: {', '.join(sorted(changes))}", code="unsupported_field"
        )

    if new_status is not None:
        _apply_status_change(
            db,
            complaint,
            new_status,
            admin=admin,
            note=public_note,
            has_resolution_note=has_resolution_note,
        )
    elif public_note:
        record_update(
            db,
            complaint,
            update_type=UpdateType.COMMENT,
            actor=admin,
            note=public_note,
        )

    if internal_note:
        record_update(
            db,
            complaint,
            update_type=UpdateType.COMMENT,
            actor=admin,
            note=internal_note,
            is_public=False,
        )

    db.commit()
    db.refresh(complaint)
    logger.info(
        "complaint %s updated by admin %s", complaint.reference_code, admin.email
    )
    return complaint


def add_evidence(
    db: Session, complaint: Complaint, admin: Profile, payload: EvidenceRequest
) -> Complaint:
    """Attach before/after photos documenting the fix."""
    added: list[str] = []
    if payload.before_image_url:
        complaint.before_image_url = payload.before_image_url
        added.append("before")
    if payload.after_image_url:
        complaint.after_image_url = payload.after_image_url
        added.append("after")

    record_update(
        db,
        complaint,
        update_type=UpdateType.EVIDENCE_ADDED,
        actor=admin,
        new_value=", ".join(added),
        note=payload.note or f"{' and '.join(added)} evidence uploaded.",
    )
    db.commit()
    db.refresh(complaint)
    return complaint


# ---------------------------------------------------------------------------
# Departments
# ---------------------------------------------------------------------------


def create_department(db: Session, payload: DepartmentCreate) -> Department:
    existing = db.scalar(
        select(Department).where(
            (Department.code == payload.code) | (Department.name == payload.name)
        )
    )
    if existing is not None:
        raise ConflictError(
            "A department with that name or code already exists.",
            code="department_exists",
        )
    department = Department(
        name=payload.name,
        code=payload.code,
        description=payload.description,
        contact_email=payload.contact_email,
        contact_phone=payload.contact_phone,
        categories=[category.value for category in payload.categories],
        sla_hours=payload.sla_hours,
    )
    db.add(department)
    db.commit()
    db.refresh(department)
    return department


def update_department(
    db: Session, department_id: uuid.UUID, payload: DepartmentUpdate
) -> Department:
    department = db.get(Department, department_id)
    if department is None:
        raise NotFoundError("Department not found.")
    changes = payload.changes()
    if not changes:
        raise ValidationError("Provide at least one field to update.")
    if "categories" in changes and changes["categories"] is not None:
        changes["categories"] = [
            item.value if isinstance(item, ComplaintCategory) else str(item)
            for item in changes["categories"]
        ]
    for field_name, value in changes.items():
        setattr(department, field_name, value)
    db.commit()
    db.refresh(department)
    return department


def list_departments(db: Session, *, include_inactive: bool = False) -> list[Department]:
    stmt = select(Department).order_by(Department.name)
    if not include_inactive:
        stmt = stmt.where(Department.is_active.is_(True))
    return list(db.scalars(stmt).all())


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------


def dashboard(db: Session, *, window_days: int = 30) -> DashboardStats:
    """Aggregate everything the admin home screen needs in one round trip.

    Counters (`total_complaints`, `open_complaints`, `by_status`, …) are
    all-time, which is what a work-queue dashboard needs. `window_days` scopes
    the trend-sensitive figures — the city-health score and its comparison
    against the preceding window — while `new_today` / `new_this_week` /
    `resolved_this_week` cover recency.
    """
    now = utcnow()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = now - timedelta(days=7)

    all_complaints = list(db.scalars(select(Complaint)).all())
    departments = {
        str(department.id): department
        for department in db.scalars(select(Department)).all()
    }

    def created_at(complaint: Complaint):
        return analytics_service._aware(complaint.created_at) or now

    total = len(all_complaints)
    open_members = [c for c in all_complaints if c.status in OPEN_STATUSES]
    resolved_members = [
        c for c in all_complaints if c.status is ComplaintStatus.RESOLVED
    ]

    durations: list[float] = []
    for complaint in resolved_members:
        hours = analytics_service._resolution_hours(complaint)
        if hours is not None:
            durations.append(hours)

    sla_breached = 0
    for complaint in open_members:
        department = (
            departments.get(str(complaint.department_id))
            if complaint.department_id
            else None
        )
        if department and (now - created_at(complaint)).total_seconds() / 3600 > department.sla_hours:
            sla_breached += 1

    status_counter = Counter(c.status for c in all_complaints)
    category_counter = Counter(c.category for c in all_complaints)
    severity_counter = Counter(c.severity for c in all_complaints)
    ward_counter = Counter(c.ward for c in all_complaints if c.ward)

    department_loads: list[DepartmentLoad] = []
    for key, department in departments.items():
        members = [c for c in all_complaints if str(c.department_id) == key]
        if not members:
            continue
        department_loads.append(
            DepartmentLoad(
                department_id=department.id,
                department_name=department.name,
                open_count=sum(1 for c in members if c.status in OPEN_STATUSES),
                resolved_count=sum(
                    1 for c in members if c.status is ComplaintStatus.RESOLVED
                ),
                total_count=len(members),
            )
        )
    unrouted = [c for c in all_complaints if c.department_id is None]
    if unrouted:
        department_loads.append(
            DepartmentLoad(
                department_id=None,
                department_name="Unassigned",
                open_count=sum(1 for c in unrouted if c.status in OPEN_STATUSES),
                resolved_count=0,
                total_count=len(unrouted),
            )
        )
    department_loads.sort(key=lambda item: item.open_count, reverse=True)

    health = analytics_service.city_health(db, window_days=window_days)

    return DashboardStats(
        generated_at=now,
        window_days=window_days,
        total_complaints=total,
        open_complaints=len(open_members),
        resolved_complaints=len(resolved_members),
        unassigned_complaints=sum(1 for c in open_members if c.department_id is None),
        critical_open=sum(
            1 for c in open_members if c.severity is ComplaintSeverity.CRITICAL
        ),
        duplicates=status_counter.get(ComplaintStatus.DUPLICATE, 0),
        new_today=sum(1 for c in all_complaints if created_at(c) >= today_start),
        new_this_week=sum(1 for c in all_complaints if created_at(c) >= week_start),
        resolved_this_week=sum(
            1
            for c in resolved_members
            if (analytics_service._aware(c.resolved_at) or now) >= week_start
        ),
        resolution_rate=round(len(resolved_members) / total, 4) if total else 0.0,
        avg_resolution_hours=(
            round(sum(durations) / len(durations), 1) if durations else None
        ),
        median_resolution_hours=(
            round(statistics.median(durations), 1) if durations else None
        ),
        sla_breached_open=sla_breached,
        avg_priority_score=(
            round(sum(c.priority_score or 0 for c in all_complaints) / total, 1)
            if total
            else 0.0
        ),
        by_status=[
            StatusCount(status=status, count=status_counter.get(status, 0))
            for status in ComplaintStatus
        ],
        by_category=[
            CategoryCount(category=category, count=category_counter.get(category, 0))
            for category in ComplaintCategory
        ],
        by_severity=[
            SeverityCount(severity=severity, count=severity_counter.get(severity, 0))
            for severity in ComplaintSeverity
        ],
        by_department=department_loads,
        top_wards=[
            {"ward": ward, "count": count} for ward, count in ward_counter.most_common(5)
        ],
        city_health_score=health.score,
        total_citizens=db.scalar(
            select(func.count())
            .select_from(Profile)
            .where(Profile.role == UserRole.CITIZEN)
        )
        or 0,
        total_confirmations=db.scalar(
            select(func.count()).select_from(ComplaintConfirmation)
        )
        or 0,
    )
