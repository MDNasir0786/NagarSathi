"""Profile provisioning and role management.

Role rules enforced here:

* A profile created through normal signup is **always** a ``citizen``.
  The client cannot influence this — `role` is never read from request bodies.
* The admin role can only be granted by
  (a) the ``ADMIN_EMAILS`` allow-list in the backend environment,
  (b) an existing admin calling ``POST /api/v1/admin/users/{id}/role``, or
  (c) the operator-run ``scripts/create_admin.py``.
"""

from __future__ import annotations

import logging
import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.auth.jwt import TokenPayload
from app.models import Complaint, Department, Profile, UserRole
from app.utils.config import settings
from app.utils.errors import ConflictError, NotFoundError, ValidationError

logger = logging.getLogger(__name__)


def resolve_initial_role(email: str | None) -> UserRole:
    """Decide the role for a brand-new profile from backend config only."""
    if email and email.lower() in settings.admin_email_list:
        return UserRole.ADMIN
    return UserRole.CITIZEN


def get_profile(db: Session, user_id: uuid.UUID) -> Profile | None:
    return db.get(Profile, user_id)


def get_profile_by_email(db: Session, email: str) -> Profile | None:
    return db.scalar(select(Profile).where(func.lower(Profile.email) == email.lower()))


def provision_profile(db: Session, payload: TokenPayload) -> Profile:
    """Return the profile for a verified token, creating it on first sight.

    Supabase owns authentication, so the first authenticated request from a
    new user is what materialises the application-side profile row.
    """
    profile = db.get(Profile, payload.user_id)
    email = (payload.email or "").strip().lower()

    if profile is not None:
        # Keep the mirrored email in sync if the user changed it in Supabase.
        if email and profile.email.lower() != email:
            profile.email = email
            db.commit()
            db.refresh(profile)
        return profile

    if not email:
        raise ValidationError(
            "The access token has no email claim, so a profile cannot be created.",
            code="missing_email_claim",
        )

    # An operator may have pre-seeded this admin by email before the person
    # signed up. Adopt that row's role, then re-key it to the real auth id.
    placeholder = get_profile_by_email(db, email)
    inherited_role: UserRole | None = None
    inherited_department: uuid.UUID | None = None
    if placeholder is not None:
        in_use = db.scalar(
            select(func.count())
            .select_from(Complaint)
            .where(Complaint.citizen_id == placeholder.id)
        )
        if in_use:
            raise ConflictError(
                "A different account already owns this email address.",
                code="email_already_linked",
            )
        inherited_role = placeholder.role
        inherited_department = placeholder.department_id
        db.delete(placeholder)
        db.flush()

    profile = Profile(
        id=payload.user_id,
        email=email,
        full_name=payload.display_name,
        avatar_url=payload.avatar_url,
        phone=payload.phone,
        city=settings.city_name,
        role=inherited_role or resolve_initial_role(email),
        department_id=inherited_department,
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)
    logger.info(
        "provisioned profile %s role=%s", profile.email, profile.role.value
    )
    return profile


def update_profile(db: Session, profile: Profile, changes: dict) -> Profile:
    """Apply a citizen-editable subset of profile fields."""
    editable = {
        "full_name",
        "phone",
        "address",
        "ward",
        "city",
        "avatar_url",
        "language",
    }
    unknown = set(changes) - editable
    if unknown:
        # Defence in depth: `role`/`is_active`/`department_id` must never be
        # settable by the profile owner.
        raise ValidationError(
            f"These fields cannot be updated here: {', '.join(sorted(unknown))}",
            code="field_not_editable",
        )

    for field, value in changes.items():
        setattr(profile, field, value)
    db.commit()
    db.refresh(profile)
    return profile


def set_role(
    db: Session,
    *,
    actor: Profile,
    target_user_id: uuid.UUID,
    role: UserRole,
    department_id: uuid.UUID | None = None,
) -> Profile:
    """Admin-only role change. Guards against removing the last admin."""
    target = db.get(Profile, target_user_id)
    if target is None:
        raise NotFoundError("User not found.")

    if target.id == actor.id and role is not UserRole.ADMIN:
        raise ConflictError(
            "You cannot remove your own admin role.", code="self_demotion"
        )

    if target.role is UserRole.ADMIN and role is not UserRole.ADMIN:
        remaining = db.scalar(
            select(func.count())
            .select_from(Profile)
            .where(Profile.role == UserRole.ADMIN, Profile.id != target.id)
        )
        if not remaining:
            raise ConflictError(
                "At least one admin must remain.", code="last_admin"
            )

    if department_id is not None:
        if db.get(Department, department_id) is None:
            raise NotFoundError("Department not found.")
        target.department_id = department_id

    target.role = role
    db.commit()
    db.refresh(target)
    logger.info(
        "role change: %s -> %s by %s", target.email, role.value, actor.email
    )
    return target


def set_active(
    db: Session, *, actor: Profile, target_user_id: uuid.UUID, is_active: bool
) -> Profile:
    target = db.get(Profile, target_user_id)
    if target is None:
        raise NotFoundError("User not found.")
    if target.id == actor.id and not is_active:
        raise ConflictError(
            "You cannot deactivate your own account.", code="self_deactivation"
        )
    target.is_active = is_active
    db.commit()
    db.refresh(target)
    return target


def list_profiles(
    db: Session,
    *,
    role: UserRole | None = None,
    search: str | None = None,
    limit: int = 20,
    offset: int = 0,
) -> tuple[list[Profile], int]:
    stmt = select(Profile)
    count_stmt = select(func.count()).select_from(Profile)

    if role is not None:
        stmt = stmt.where(Profile.role == role)
        count_stmt = count_stmt.where(Profile.role == role)
    if search:
        pattern = f"%{search.lower()}%"
        condition = func.lower(Profile.email).like(pattern) | func.lower(
            func.coalesce(Profile.full_name, "")
        ).like(pattern)
        stmt = stmt.where(condition)
        count_stmt = count_stmt.where(condition)

    total = db.scalar(count_stmt) or 0
    rows = list(
        db.scalars(
            stmt.order_by(Profile.created_at.desc()).limit(limit).offset(offset)
        ).all()
    )
    return rows, total
