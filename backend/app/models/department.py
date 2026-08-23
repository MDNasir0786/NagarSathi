"""Municipal department responsible for handling complaint categories."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, JSONType, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:  # pragma: no cover
    from app.models.complaint import Complaint
    from app.models.profile import Profile


class Department(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "departments"

    name: Mapped[str] = mapped_column(String(120), nullable=False, unique=True)
    code: Mapped[str] = mapped_column(String(32), nullable=False, unique=True, index=True)
    description: Mapped[str | None] = mapped_column(Text)
    contact_email: Mapped[str | None] = mapped_column(String(255))
    contact_phone: Mapped[str | None] = mapped_column(String(32))

    #: Complaint categories this department owns, e.g. ["road", "drainage"].
    categories: Mapped[list[str]] = mapped_column(
        JSONType, nullable=False, default=list
    )

    #: Target turnaround used by department-performance analytics.
    sla_hours: Mapped[int] = mapped_column(nullable=False, default=72)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    complaints: Mapped[list[Complaint]] = relationship(
        back_populates="department", foreign_keys="Complaint.department_id"
    )
    staff: Mapped[list[Profile]] = relationship(back_populates="department")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Department {self.code}>"
