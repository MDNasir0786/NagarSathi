"""Complaint lifecycle: filing, AI enrichment, tracking and confirmations."""

from __future__ import annotations

import logging
import secrets
import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.database.base import utcnow
from app.models import (
    OPEN_STATUSES,
    AIAnalysisStatus,
    Complaint,
    ComplaintCategory,
    ComplaintConfirmation,
    ComplaintSeverity,
    ComplaintStatus,
    ComplaintUpdate,
    Department,
    Profile,
    UpdateType,
    UserRole,
)
from app.schemas.ai import DuplicateCandidate
from app.schemas.complaint import (
    AIAnalysisOut,
    ComplaintCreate,
    ComplaintDetail,
    ComplaintListItem,
    ComplaintStatusOut,
    ComplaintUpdateByCitizen,
    ConfirmRequest,
    NearbyComplaint,
    SimilarComplaint,
    TimelineEntry,
)
from app.services.claude_service import (
    DEPARTMENT_BY_CATEGORY,
    AnalysisResult,
    ClaudeService,
    claude_service,
)
from app.utils.config import settings
from app.utils.errors import (
    ConflictError,
    NotFoundError,
    PermissionDeniedError,
    ValidationError,
)
from app.utils.geo import bounding_box, haversine_meters, is_within_city

logger = logging.getLogger(__name__)

#: Confirmations needed before the platform nudges severity upward.
SEVERITY_ESCALATION_THRESHOLD = 5
_SEVERITY_ORDER = [
    ComplaintSeverity.LOW,
    ComplaintSeverity.MEDIUM,
    ComplaintSeverity.HIGH,
    ComplaintSeverity.CRITICAL,
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def generate_reference_code(db: Session) -> str:
    """Human-quotable tracking code, e.g. ``BCA-2026-4F9A2C``."""
    year = datetime.now(UTC).year
    for _ in range(8):
        candidate = f"BCA-{year}-{secrets.token_hex(3).upper()}"
        exists = db.scalar(
            select(func.count()).select_from(Complaint).where(
                Complaint.reference_code == candidate
            )
        )
        if not exists:
            return candidate
    # Astronomically unlikely; fall back to a longer code.
    return f"BCA-{year}-{uuid.uuid4().hex[:10].upper()}"


def validate_location(latitude: float, longitude: float) -> None:
    if not is_within_city(
        latitude,
        longitude,
        settings.city_center_lat,
        settings.city_center_lon,
        settings.city_radius_km,
    ):
        raise ValidationError(
            f"Location is outside the {settings.city_name} service area "
            f"({settings.city_radius_km:g} km radius).",
            code="outside_service_area",
        )


def record_update(
    db: Session,
    complaint: Complaint,
    *,
    update_type: UpdateType,
    actor: Profile | None = None,
    actor_label: str | None = None,
    old_value: str | None = None,
    new_value: str | None = None,
    note: str | None = None,
    is_public: bool = True,
) -> ComplaintUpdate:
    """Append an entry to the complaint's audit trail / public timeline."""
    entry = ComplaintUpdate(
        complaint_id=complaint.id,
        actor_id=actor.id if actor else None,
        actor_role=actor.role if actor else None,
        actor_label=actor_label
        or (actor.full_name or actor.email if actor else "system"),
        update_type=update_type,
        old_value=str(old_value)[:255] if old_value is not None else None,
        new_value=str(new_value)[:255] if new_value is not None else None,
        note=note,
        is_public=is_public,
    )
    db.add(entry)
    return entry


def _department_by_code(db: Session, code: str | None) -> Department | None:
    if not code:
        return None
    return db.scalar(select(Department).where(Department.code == code.upper()))


def _complaint_query():
    """Base query with the relationships every serialiser needs."""
    return select(Complaint).options(
        selectinload(Complaint.department),
        selectinload(Complaint.citizen),
    )


def get_complaint_or_404(db: Session, complaint_id: uuid.UUID) -> Complaint:
    complaint = db.scalar(_complaint_query().where(Complaint.id == complaint_id))
    if complaint is None:
        raise NotFoundError("Complaint not found.")
    return complaint


def get_by_reference(db: Session, reference_code: str) -> Complaint | None:
    return db.scalar(
        _complaint_query().where(
            func.upper(Complaint.reference_code) == reference_code.upper()
        )
    )


def ensure_can_view(complaint: Complaint, requester: Profile) -> None:
    if requester.role is UserRole.ADMIN or complaint.citizen_id == requester.id:
        return
    raise PermissionDeniedError("You can only view complaints you filed.")


# ---------------------------------------------------------------------------
# Nearby / duplicate detection
# ---------------------------------------------------------------------------


def find_nearby(
    db: Session,
    *,
    latitude: float,
    longitude: float,
    radius_meters: float,
    categories: list[ComplaintCategory] | None = None,
    only_open: bool = True,
    exclude_id: uuid.UUID | None = None,
    max_age_days: int | None = 90,
    limit: int = 20,
) -> list[tuple[Complaint, float]]:
    """Complaints within `radius_meters`, nearest first.

    A cheap indexed bounding-box filter runs in SQL; the exact great-circle
    distance is then applied in Python. This keeps the query portable (no
    PostGIS extension required on Supabase).
    """
    box = bounding_box(latitude, longitude, radius_meters)
    stmt = _complaint_query().where(
        Complaint.latitude.between(box.min_lat, box.max_lat),
        Complaint.longitude.between(box.min_lon, box.max_lon),
    )
    if only_open:
        stmt = stmt.where(Complaint.status.in_(list(OPEN_STATUSES)))
    if categories:
        stmt = stmt.where(Complaint.category.in_(categories))
    if exclude_id is not None:
        stmt = stmt.where(Complaint.id != exclude_id)
    if max_age_days:
        cutoff = utcnow() - timedelta(days=max_age_days)
        stmt = stmt.where(Complaint.created_at >= cutoff)

    # Bounded to keep the in-Python distance pass cheap on dense wards.
    rows = db.scalars(stmt.order_by(Complaint.created_at.desc()).limit(200)).all()

    scored: list[tuple[Complaint, float]] = []
    for complaint in rows:
        distance = haversine_meters(
            latitude, longitude, complaint.latitude, complaint.longitude
        )
        if distance <= radius_meters:
            scored.append((complaint, distance))

    scored.sort(key=lambda pair: pair[1])
    return scored[:limit]


def build_duplicate_candidates(
    nearby: list[tuple[Complaint, float]], *, limit: int = 8
) -> list[DuplicateCandidate]:
    now = utcnow()
    candidates: list[DuplicateCandidate] = []
    for complaint, distance in nearby[:limit]:
        created = complaint.created_at
        if created.tzinfo is None:  # SQLite returns naive datetimes
            created = created.replace(tzinfo=UTC)
        candidates.append(
            DuplicateCandidate(
                reference_code=complaint.reference_code,
                title=complaint.title,
                description=complaint.description,
                category=complaint.category,
                status=complaint.status.value,
                distance_meters=distance,
                age_hours=(now - created).total_seconds() / 3600,
            )
        )
    return candidates


def nearby_for_citizen(
    db: Session,
    *,
    latitude: float,
    longitude: float,
    radius_meters: float | None,
    category: ComplaintCategory | None,
    requester: Profile,
    limit: int = 10,
) -> list[NearbyComplaint]:
    """Open issues a citizen can confirm instead of filing a duplicate."""
    validate_location(latitude, longitude)
    radius = radius_meters or settings.nearby_radius_meters
    nearby = find_nearby(
        db,
        latitude=latitude,
        longitude=longitude,
        radius_meters=radius,
        categories=[category] if category else None,
        only_open=True,
        limit=limit,
    )
    if not nearby:
        return []

    ids = [complaint.id for complaint, _ in nearby]
    already = set(
        db.scalars(
            select(ComplaintConfirmation.complaint_id).where(
                ComplaintConfirmation.complaint_id.in_(ids),
                ComplaintConfirmation.citizen_id == requester.id,
            )
        ).all()
    )

    return [
        NearbyComplaint(
            id=complaint.id,
            reference_code=complaint.reference_code,
            title=complaint.title,
            category=complaint.category,
            severity=complaint.severity,
            status=complaint.status,
            latitude=complaint.latitude,
            longitude=complaint.longitude,
            distance_meters=round(distance, 1),
            confirmation_count=complaint.confirmation_count,
            image_url=complaint.image_url,
            already_confirmed_by_me=complaint.id in already,
            is_mine=complaint.citizen_id == requester.id,
            created_at=complaint.created_at,
        )
        for complaint, distance in nearby
    ]


# ---------------------------------------------------------------------------
# AI enrichment
# ---------------------------------------------------------------------------


def apply_analysis(
    db: Session,
    complaint: Complaint,
    result: AnalysisResult,
    *,
    actor: Profile | None = None,
    link_duplicates: bool = True,
) -> Complaint:
    """Write an AI verdict onto a complaint and record it on the timeline."""
    analysis = result.analysis

    complaint.category = analysis.category
    complaint.severity = analysis.severity
    complaint.priority_score = analysis.priority_score
    complaint.ai_summary = analysis.summary
    complaint.ai_suggested_action = analysis.suggested_action
    complaint.ai_tags = analysis.tags
    complaint.ai_confidence = analysis.confidence
    complaint.ai_model = result.model
    complaint.ai_analysis_status = result.status
    complaint.ai_analyzed_at = utcnow()

    department = _department_by_code(db, analysis.department) or _department_by_code(
        db, DEPARTMENT_BY_CATEGORY[analysis.category]
    )
    if department is not None:
        complaint.department_id = department.id

    if link_duplicates:
        if analysis.duplicate_of:
            original = get_by_reference(db, analysis.duplicate_of)
            if original is not None and original.id != complaint.id:
                complaint.duplicate_of_id = original.id
        if analysis.similar_references:
            similar_ids = [
                str(found.id)
                for code in analysis.similar_references
                if (found := get_by_reference(db, code)) is not None
                and found.id != complaint.id
            ]
            complaint.similar_complaint_ids = similar_ids

    record_update(
        db,
        complaint,
        update_type=UpdateType.AI_ANALYSIS,
        actor=actor,
        actor_label="Claude AI" if result.status is AIAnalysisStatus.COMPLETED else "system",
        new_value=f"{analysis.category.value}/{analysis.severity.value}/p{analysis.priority_score}",
        note=analysis.summary,
        is_public=True,
    )
    return complaint


def analyze_and_apply(
    db: Session,
    complaint: Complaint,
    *,
    service: ClaudeService | None = None,
    actor: Profile | None = None,
    category_hint: ComplaintCategory | None = None,
) -> AnalysisResult:
    """Run duplicate-aware analysis for an existing complaint row."""
    engine = service or claude_service
    nearby = find_nearby(
        db,
        latitude=complaint.latitude,
        longitude=complaint.longitude,
        radius_meters=settings.duplicate_radius_meters,
        only_open=True,
        exclude_id=complaint.id,
        limit=8,
    )
    result = engine.analyze_complaint(
        title=complaint.title,
        description=complaint.description,
        latitude=complaint.latitude,
        longitude=complaint.longitude,
        address=complaint.address,
        ward=complaint.ward,
        image_url=complaint.image_url,
        category_hint=category_hint,
        candidates=build_duplicate_candidates(nearby),
        confirmation_count=complaint.confirmation_count,
    )
    apply_analysis(db, complaint, result, actor=actor)
    return result


# ---------------------------------------------------------------------------
# Create / update
# ---------------------------------------------------------------------------


def create_complaint(
    db: Session,
    citizen: Profile,
    payload: ComplaintCreate,
    *,
    service: ClaudeService | None = None,
) -> tuple[Complaint, AnalysisResult, Complaint | None]:
    """File a complaint and enrich it with AI analysis.

    Returns the complaint, the analysis result, and the original complaint if
    the AI flagged this report as a duplicate.
    """
    validate_location(payload.latitude, payload.longitude)

    complaint = Complaint(
        reference_code=generate_reference_code(db),
        citizen_id=citizen.id,
        title=payload.title,
        description=payload.description,
        image_url=payload.image_url,
        image_urls=payload.image_urls,
        latitude=payload.latitude,
        longitude=payload.longitude,
        address=payload.address,
        landmark=payload.landmark,
        ward=payload.ward or citizen.ward,
        category=payload.category_hint or ComplaintCategory.OTHER,
        status=ComplaintStatus.SUBMITTED,
        ai_analysis_status=AIAnalysisStatus.PENDING,
    )
    db.add(complaint)
    db.flush()  # assign the primary key before writing timeline rows

    record_update(
        db,
        complaint,
        update_type=UpdateType.CREATED,
        actor=citizen,
        new_value=ComplaintStatus.SUBMITTED.value,
        note="Complaint filed by citizen.",
    )

    result = analyze_and_apply(
        db, complaint, service=service, category_hint=payload.category_hint
    )

    duplicate_of: Complaint | None = None
    if complaint.duplicate_of_id:
        duplicate_of = db.get(Complaint, complaint.duplicate_of_id)
        if duplicate_of is not None:
            complaint.status = ComplaintStatus.DUPLICATE
            record_update(
                db,
                complaint,
                update_type=UpdateType.DUPLICATE_LINKED,
                actor_label="Claude AI",
                new_value=duplicate_of.reference_code,
                note=(
                    "Detected as a duplicate of an existing report; the original "
                    "has been given an extra confirmation."
                ),
            )
            # Roll the citizen's report into the original as a confirmation.
            _register_confirmation(
                db,
                original=duplicate_of,
                citizen=citizen,
                note=f"Auto-confirmed via duplicate report {complaint.reference_code}.",
                latitude=payload.latitude,
                longitude=payload.longitude,
            )

    db.commit()
    db.refresh(complaint)
    logger.info(
        "complaint %s filed by %s (%s/%s, ai=%s)",
        complaint.reference_code,
        citizen.email,
        complaint.category.value,
        complaint.severity.value,
        result.status.value,
    )
    return complaint, result, duplicate_of


def update_own_complaint(
    db: Session,
    complaint: Complaint,
    citizen: Profile,
    payload: ComplaintUpdateByCitizen,
) -> Complaint:
    """Let a citizen correct their report while it is still unacknowledged."""
    if complaint.citizen_id != citizen.id:
        raise PermissionDeniedError("You can only edit complaints you filed.")
    if complaint.status is not ComplaintStatus.SUBMITTED:
        raise ConflictError(
            "This complaint has already been picked up by the municipal team and "
            "can no longer be edited.",
            code="complaint_locked",
        )

    changes = payload.model_dump(exclude_unset=True)
    if not changes:
        raise ValidationError("Provide at least one field to update.")

    for field_name, value in changes.items():
        setattr(complaint, field_name, value)

    record_update(
        db,
        complaint,
        update_type=UpdateType.COMMENT,
        actor=citizen,
        note=f"Citizen updated: {', '.join(sorted(changes))}.",
    )
    db.commit()
    db.refresh(complaint)
    return complaint


# ---------------------------------------------------------------------------
# Confirmations
# ---------------------------------------------------------------------------


def _register_confirmation(
    db: Session,
    *,
    original: Complaint,
    citizen: Profile,
    note: str | None,
    latitude: float | None,
    longitude: float | None,
) -> ComplaintConfirmation | None:
    """Idempotently add a confirmation and re-weight the original complaint."""
    existing = db.scalar(
        select(ComplaintConfirmation).where(
            ComplaintConfirmation.complaint_id == original.id,
            ComplaintConfirmation.citizen_id == citizen.id,
        )
    )
    if existing is not None:
        return None

    distance = None
    if latitude is not None and longitude is not None:
        distance = haversine_meters(
            latitude, longitude, original.latitude, original.longitude
        )

    confirmation = ComplaintConfirmation(
        complaint_id=original.id,
        citizen_id=citizen.id,
        note=note,
        latitude=latitude,
        longitude=longitude,
        distance_meters=distance,
    )
    db.add(confirmation)

    original.confirmation_count = (original.confirmation_count or 0) + 1
    # Community weight nudges priority; severity escalates only at a threshold.
    original.priority_score = min(100, (original.priority_score or 50) + 2)
    if (
        original.confirmation_count >= SEVERITY_ESCALATION_THRESHOLD
        and original.severity is not ComplaintSeverity.CRITICAL
    ):
        current_index = _SEVERITY_ORDER.index(original.severity)
        escalated = _SEVERITY_ORDER[min(current_index + 1, len(_SEVERITY_ORDER) - 1)]
        if escalated is not original.severity:
            record_update(
                db,
                original,
                update_type=UpdateType.SEVERITY_CHANGE,
                actor_label="system",
                old_value=original.severity.value,
                new_value=escalated.value,
                note=(
                    f"Escalated automatically after {original.confirmation_count} "
                    "citizen confirmations."
                ),
            )
            original.severity = escalated

    record_update(
        db,
        original,
        update_type=UpdateType.CONFIRMATION,
        actor=citizen,
        new_value=str(original.confirmation_count),
        note=note or "Another citizen confirmed this issue.",
    )
    return confirmation


def confirm_complaint(
    db: Session,
    complaint_id: uuid.UUID,
    citizen: Profile,
    payload: ConfirmRequest,
) -> tuple[Complaint, bool]:
    """Confirm an existing nearby issue ("me too")."""
    complaint = get_complaint_or_404(db, complaint_id)

    # Confirmations always land on the canonical report.
    if complaint.duplicate_of_id:
        canonical = db.get(Complaint, complaint.duplicate_of_id)
        if canonical is not None:
            complaint = canonical

    if complaint.citizen_id == citizen.id:
        raise ConflictError(
            "You filed this complaint, so it is already counted.",
            code="own_complaint",
        )
    if complaint.status not in OPEN_STATUSES:
        raise ConflictError(
            f"This complaint is already {complaint.status.value} and cannot be confirmed.",
            code="complaint_closed",
        )

    if payload.latitude is not None and payload.longitude is not None:
        distance = haversine_meters(
            payload.latitude, payload.longitude, complaint.latitude, complaint.longitude
        )
        max_distance = settings.nearby_radius_meters * 2
        if distance > max_distance:
            raise ValidationError(
                f"You appear to be {distance / 1000:.1f} km from this issue. "
                "Confirmations must be made near the reported location.",
                code="too_far_to_confirm",
            )

    confirmation = _register_confirmation(
        db,
        original=complaint,
        citizen=citizen,
        note=payload.note,
        latitude=payload.latitude,
        longitude=payload.longitude,
    )
    if confirmation is None:
        db.rollback()
        raise ConflictError(
            "You have already confirmed this complaint.", code="already_confirmed"
        )

    db.commit()
    db.refresh(complaint)
    return complaint, True


# ---------------------------------------------------------------------------
# Reads
# ---------------------------------------------------------------------------


def list_complaints(
    db: Session,
    *,
    citizen_id: uuid.UUID | None = None,
    statuses: list[ComplaintStatus] | None = None,
    categories: list[ComplaintCategory] | None = None,
    severities: list[ComplaintSeverity] | None = None,
    department_id: uuid.UUID | None = None,
    assigned_to_id: uuid.UUID | None = None,
    ward: str | None = None,
    search: str | None = None,
    created_after: datetime | None = None,
    created_before: datetime | None = None,
    unassigned_only: bool = False,
    sort: str = "-created_at",
    limit: int = 20,
    offset: int = 0,
) -> tuple[list[Complaint], int]:
    """Shared filtered/sorted/paginated query for citizen and admin lists."""
    stmt = _complaint_query()
    filters = []

    if citizen_id is not None:
        filters.append(Complaint.citizen_id == citizen_id)
    if statuses:
        filters.append(Complaint.status.in_(statuses))
    if categories:
        filters.append(Complaint.category.in_(categories))
    if severities:
        filters.append(Complaint.severity.in_(severities))
    if department_id is not None:
        filters.append(Complaint.department_id == department_id)
    if assigned_to_id is not None:
        filters.append(Complaint.assigned_to_id == assigned_to_id)
    if unassigned_only:
        filters.append(Complaint.department_id.is_(None))
    if ward:
        filters.append(func.lower(Complaint.ward) == ward.lower())
    if created_after is not None:
        filters.append(Complaint.created_at >= created_after)
    if created_before is not None:
        filters.append(Complaint.created_at <= created_before)
    if search:
        pattern = f"%{search.lower().strip()}%"
        filters.append(
            or_(
                func.lower(Complaint.title).like(pattern),
                func.lower(Complaint.description).like(pattern),
                func.lower(Complaint.reference_code).like(pattern),
                func.lower(func.coalesce(Complaint.address, "")).like(pattern),
                func.lower(func.coalesce(Complaint.ward, "")).like(pattern),
            )
        )

    if filters:
        stmt = stmt.where(*filters)

    total = db.scalar(
        select(func.count()).select_from(Complaint).where(*filters)
        if filters
        else select(func.count()).select_from(Complaint)
    ) or 0

    sort_map = {
        "created_at": Complaint.created_at,
        "updated_at": Complaint.updated_at,
        "priority_score": Complaint.priority_score,
        "confirmation_count": Complaint.confirmation_count,
        "severity": Complaint.severity,
        "status": Complaint.status,
    }
    descending = sort.startswith("-")
    column = sort_map.get(sort.lstrip("-"), Complaint.created_at)
    stmt = stmt.order_by(column.desc() if descending else column.asc())

    rows = list(db.scalars(stmt.limit(limit).offset(offset)).all())
    return rows, total


def get_timeline(
    db: Session, complaint: Complaint, *, include_internal: bool
) -> list[ComplaintUpdate]:
    stmt = (
        select(ComplaintUpdate)
        .where(ComplaintUpdate.complaint_id == complaint.id)
        .order_by(ComplaintUpdate.created_at.asc())
    )
    if not include_internal:
        stmt = stmt.where(ComplaintUpdate.is_public.is_(True))
    return list(db.scalars(stmt).all())


def _to_similar(complaint: Complaint, distance: float | None = None) -> SimilarComplaint:
    return SimilarComplaint(
        id=complaint.id,
        reference_code=complaint.reference_code,
        title=complaint.title,
        status=complaint.status,
        category=complaint.category,
        distance_meters=round(distance, 1) if distance is not None else None,
        confirmation_count=complaint.confirmation_count,
        created_at=complaint.created_at,
    )


def to_list_item(complaint: Complaint) -> ComplaintListItem:
    return ComplaintListItem.model_validate(complaint)


def to_detail(
    db: Session, complaint: Complaint, *, requester: Profile
) -> ComplaintDetail:
    """Serialise a complaint with its timeline, AI verdict and linked reports."""
    is_admin = requester.role is UserRole.ADMIN
    timeline = get_timeline(db, complaint, include_internal=is_admin)

    duplicate_of = None
    if complaint.duplicate_of_id:
        original = db.get(Complaint, complaint.duplicate_of_id)
        if original is not None:
            duplicate_of = _to_similar(original)

    similar: list[SimilarComplaint] = []
    if complaint.similar_complaint_ids:
        ids = []
        for raw in complaint.similar_complaint_ids:
            try:
                ids.append(uuid.UUID(str(raw)))
            except (ValueError, TypeError):
                continue
        if ids:
            found = db.scalars(select(Complaint).where(Complaint.id.in_(ids))).all()
            similar = [_to_similar(item) for item in found]

    detail = ComplaintDetail.model_validate(complaint)
    detail.timeline = [TimelineEntry.model_validate(entry) for entry in timeline]
    detail.duplicate_of = duplicate_of
    detail.similar_complaints = similar
    detail.resolution_hours = (
        round(complaint.resolution_hours, 2) if complaint.resolution_hours else None
    )
    detail.ai_analysis = AIAnalysisOut(
        status=complaint.ai_analysis_status,
        summary=complaint.ai_summary,
        suggested_action=complaint.ai_suggested_action,
        tags=complaint.ai_tags or [],
        confidence=complaint.ai_confidence,
        model=complaint.ai_model,
        analyzed_at=complaint.ai_analyzed_at,
    )
    # A citizen never sees another citizen's identity.
    if not is_admin and complaint.citizen_id != requester.id:
        detail.citizen = None
    return detail


def to_status(db: Session, complaint: Complaint, *, requester: Profile) -> ComplaintStatusOut:
    """Compact tracking view with SLA state."""
    is_admin = requester.role is UserRole.ADMIN
    timeline = [
        TimelineEntry.model_validate(entry)
        for entry in get_timeline(db, complaint, include_internal=is_admin)
    ]

    sla_hours = complaint.department.sla_hours if complaint.department else None
    sla_due_at = None
    sla_breached = False
    if sla_hours:
        created = complaint.created_at
        if created.tzinfo is None:
            created = created.replace(tzinfo=UTC)
        sla_due_at = created + timedelta(hours=sla_hours)
        reference = complaint.resolved_at or utcnow()
        if reference.tzinfo is None:
            reference = reference.replace(tzinfo=UTC)
        sla_breached = reference > sla_due_at and complaint.status in OPEN_STATUSES

    return ComplaintStatusOut(
        id=complaint.id,
        reference_code=complaint.reference_code,
        status=complaint.status,
        severity=complaint.severity,
        priority_score=complaint.priority_score,
        department=complaint.department,  # type: ignore[arg-type]
        is_open=complaint.is_open,
        sla_hours=sla_hours,
        sla_due_at=sla_due_at,
        sla_breached=sla_breached,
        resolution_hours=(
            round(complaint.resolution_hours, 2) if complaint.resolution_hours else None
        ),
        last_update=timeline[-1] if timeline else None,
        timeline=timeline,
        created_at=complaint.created_at,
        updated_at=complaint.updated_at,
    )


def citizen_stats(db: Session, citizen: Profile) -> dict[str, int]:
    total = db.scalar(
        select(func.count()).select_from(Complaint).where(Complaint.citizen_id == citizen.id)
    ) or 0
    open_count = db.scalar(
        select(func.count())
        .select_from(Complaint)
        .where(
            Complaint.citizen_id == citizen.id,
            Complaint.status.in_(list(OPEN_STATUSES)),
        )
    ) or 0
    resolved = db.scalar(
        select(func.count())
        .select_from(Complaint)
        .where(
            Complaint.citizen_id == citizen.id,
            Complaint.status == ComplaintStatus.RESOLVED,
        )
    ) or 0
    confirmations = db.scalar(
        select(func.count())
        .select_from(ComplaintConfirmation)
        .where(ComplaintConfirmation.citizen_id == citizen.id)
    ) or 0
    return {
        "total_complaints": total,
        "open_complaints": open_count,
        "resolved_complaints": resolved,
        "confirmations_given": confirmations,
    }
