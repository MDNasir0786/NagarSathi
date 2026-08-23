"""Append-only audit trail / public timeline for a complaint."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import (
    Base,
    TimestampMixin,
    UUIDPrimaryKeyMixin,
    UUIDType,
    enum_column,
)
from app.models.enums import UpdateType, UserRole

if TYPE_CHECKING:  # pragma: no cover
    from app.models.complaint import Complaint
    from app.models.profile import Profile


class ComplaintUpdate(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "complaint_updates"

    complaint_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType,
        ForeignKey("complaints.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    #: Null when the entry was written by the system or the AI analyser.
    actor_id: Mapped[uuid.UUID | None] = mapped_column(
        UUIDType, ForeignKey("profiles.id", ondelete="SET NULL"), index=True
    )
    actor_role: Mapped[UserRole | None] = mapped_column(enum_column(UserRole))
    actor_label: Mapped[str] = mapped_column(String(64), nullable=False, default="system")

    update_type: Mapped[UpdateType] = mapped_column(
        enum_column(UpdateType), nullable=False, index=True
    )
    old_value: Mapped[str | None] = mapped_column(String(255))
    new_value: Mapped[str | None] = mapped_column(String(255))
    note: Mapped[str | None] = mapped_column(Text)

    #: Internal notes stay hidden from the citizen-facing timeline.
    is_public: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    complaint: Mapped[Complaint] = relationship(back_populates="updates")
    actor: Mapped[Profile | None] = relationship()

    def __repr__(self) -> str:  # pragma: no cover
        return f"<ComplaintUpdate {self.update_type.value}>"
