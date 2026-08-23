"""User profile — mirrors a Supabase `auth.users` row.

`profiles.id` is the Supabase auth user id, so the JWT `sub` claim maps
straight onto the primary key.
"""

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
from app.models.enums import UserRole

if TYPE_CHECKING:  # pragma: no cover
    from app.models.complaint import Complaint
    from app.models.department import Department


class Profile(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "profiles"

    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    full_name: Mapped[str | None] = mapped_column(String(160))
    phone: Mapped[str | None] = mapped_column(String(32))
    address: Mapped[str | None] = mapped_column(Text)
    ward: Mapped[str | None] = mapped_column(String(80), index=True)
    city: Mapped[str] = mapped_column(String(80), nullable=False, default="Bhopal")
    avatar_url: Mapped[str | None] = mapped_column(Text)
    language: Mapped[str] = mapped_column(String(8), nullable=False, default="en")

    # Role is server-controlled: signup always yields `citizen`. See
    # app.services.profile_service for the only paths that can set `admin`.
    role: Mapped[UserRole] = mapped_column(
        enum_column(UserRole), nullable=False, default=UserRole.CITIZEN, index=True
    )
    department_id: Mapped[uuid.UUID | None] = mapped_column(
        UUIDType, ForeignKey("departments.id", ondelete="SET NULL"), index=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    department: Mapped[Department | None] = relationship(back_populates="staff")
    complaints: Mapped[list[Complaint]] = relationship(
        back_populates="citizen",
        foreign_keys="Complaint.citizen_id",
        cascade="all, delete-orphan",
    )

    @property
    def is_admin(self) -> bool:
        return self.role is UserRole.ADMIN

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Profile {self.email} role={self.role.value}>"
