"""Civic complaint — the central entity of the platform."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import (
    Base,
    JSONType,
    TimestampMixin,
    UUIDPrimaryKeyMixin,
    UUIDType,
    enum_column,
)
from app.models.enums import (
    AIAnalysisStatus,
    ComplaintCategory,
    ComplaintSeverity,
    ComplaintStatus,
)

if TYPE_CHECKING:  # pragma: no cover
    from app.models.complaint_confirmation import ComplaintConfirmation
    from app.models.complaint_update import ComplaintUpdate
    from app.models.department import Department
    from app.models.profile import Profile


class Complaint(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "complaints"
    __table_args__ = (
        CheckConstraint("latitude >= -90 AND latitude <= 90", name="ck_complaints_lat"),
        CheckConstraint(
            "longitude >= -180 AND longitude <= 180", name="ck_complaints_lon"
        ),
        CheckConstraint(
            "priority_score >= 0 AND priority_score <= 100",
            name="ck_complaints_priority",
        ),
        # Bounding-box prefilter for nearby/duplicate lookups.
        Index("ix_complaints_lat_lon", "latitude", "longitude"),
        Index("ix_complaints_status_category", "status", "category"),
        Index("ix_complaints_citizen_created", "citizen_id", "created_at"),
    )

    #: Human-facing tracking id, e.g. "BCA-2026-0001A7".
    reference_code: Mapped[str] = mapped_column(
        String(32), nullable=False, unique=True, index=True
    )

    citizen_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # ----- Citizen-supplied content ---------------------------------------
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    image_url: Mapped[str | None] = mapped_column(Text)
    image_urls: Mapped[list[str]] = mapped_column(JSONType, nullable=False, default=list)

    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    address: Mapped[str | None] = mapped_column(Text)
    landmark: Mapped[str | None] = mapped_column(String(200))
    ward: Mapped[str | None] = mapped_column(String(80), index=True)

    # ----- Classification (AI-assisted, admin-overridable) ----------------
    category: Mapped[ComplaintCategory] = mapped_column(
        enum_column(ComplaintCategory),
        nullable=False,
        default=ComplaintCategory.OTHER,
        index=True,
    )
    severity: Mapped[ComplaintSeverity] = mapped_column(
        enum_column(ComplaintSeverity),
        nullable=False,
        default=ComplaintSeverity.MEDIUM,
        index=True,
    )
    priority_score: Mapped[int] = mapped_column(Integer, nullable=False, default=50, index=True)
    status: Mapped[ComplaintStatus] = mapped_column(
        enum_column(ComplaintStatus),
        nullable=False,
        default=ComplaintStatus.SUBMITTED,
        index=True,
    )

    # ----- AI analysis output ---------------------------------------------
    ai_summary: Mapped[str | None] = mapped_column(Text)
    ai_suggested_action: Mapped[str | None] = mapped_column(Text)
    ai_tags: Mapped[list[str]] = mapped_column(JSONType, nullable=False, default=list)
    ai_confidence: Mapped[float | None] = mapped_column(Float)
    ai_model: Mapped[str | None] = mapped_column(String(64))
    ai_analysis_status: Mapped[AIAnalysisStatus] = mapped_column(
        enum_column(AIAnalysisStatus), nullable=False, default=AIAnalysisStatus.PENDING
    )
    ai_analyzed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # ----- Routing / workflow ---------------------------------------------
    department_id: Mapped[uuid.UUID | None] = mapped_column(
        UUIDType, ForeignKey("departments.id", ondelete="SET NULL"), index=True
    )
    assigned_to_id: Mapped[uuid.UUID | None] = mapped_column(
        UUIDType, ForeignKey("profiles.id", ondelete="SET NULL"), index=True
    )

    # ----- Duplicate / similarity linkage ---------------------------------
    duplicate_of_id: Mapped[uuid.UUID | None] = mapped_column(
        UUIDType, ForeignKey("complaints.id", ondelete="SET NULL"), index=True
    )
    similar_complaint_ids: Mapped[list[str]] = mapped_column(
        JSONType, nullable=False, default=list
    )

    #: Number of distinct citizens who confirmed the same issue.
    confirmation_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # ----- Resolution -----------------------------------------------------
    resolution_notes: Mapped[str | None] = mapped_column(Text)
    before_image_url: Mapped[str | None] = mapped_column(Text)
    after_image_url: Mapped[str | None] = mapped_column(Text)
    acknowledged_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # ----- Relationships --------------------------------------------------
    citizen: Mapped[Profile] = relationship(
        back_populates="complaints", foreign_keys=[citizen_id]
    )
    assignee: Mapped[Profile | None] = relationship(foreign_keys=[assigned_to_id])
    department: Mapped[Department | None] = relationship(
        back_populates="complaints", foreign_keys=[department_id]
    )
    duplicate_of: Mapped[Complaint | None] = relationship(
        remote_side="Complaint.id", foreign_keys=[duplicate_of_id]
    )
    confirmations: Mapped[list[ComplaintConfirmation]] = relationship(
        back_populates="complaint", cascade="all, delete-orphan"
    )
    updates: Mapped[list[ComplaintUpdate]] = relationship(
        back_populates="complaint",
        cascade="all, delete-orphan",
        order_by="ComplaintUpdate.created_at",
    )

    @property
    def is_open(self) -> bool:
        from app.models.enums import OPEN_STATUSES

        return self.status in OPEN_STATUSES

    @property
    def resolution_hours(self) -> float | None:
        if not self.resolved_at:
            return None
        return (self.resolved_at - self.created_at).total_seconds() / 3600

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Complaint {self.reference_code} {self.status.value}>"
