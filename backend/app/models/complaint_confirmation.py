""""Me too" confirmations — one per citizen per complaint."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Float, ForeignKey, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin, UUIDPrimaryKeyMixin, UUIDType

if TYPE_CHECKING:  # pragma: no cover
    from app.models.complaint import Complaint
    from app.models.profile import Profile


class ComplaintConfirmation(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "complaint_confirmations"
    __table_args__ = (
        UniqueConstraint(
            "complaint_id", "citizen_id", name="uq_confirmation_complaint_citizen"
        ),
    )

    complaint_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType,
        ForeignKey("complaints.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    citizen_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False, index=True
    )

    note: Mapped[str | None] = mapped_column(Text)

    #: Where the confirming citizen was standing, for hotspot precision.
    latitude: Mapped[float | None] = mapped_column(Float)
    longitude: Mapped[float | None] = mapped_column(Float)
    distance_meters: Mapped[float | None] = mapped_column(Float)

    complaint: Mapped[Complaint] = relationship(back_populates="confirmations")
    citizen: Mapped[Profile] = relationship()

    def __repr__(self) -> str:  # pragma: no cover
        return f"<ComplaintConfirmation {self.complaint_id}>"
