"""Declarative base and shared column types/mixins."""

from __future__ import annotations

import enum
import uuid
from datetime import UTC, datetime

from sqlalchemy import JSON, DateTime, Uuid, func
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

# JSONB on Postgres (indexable), plain JSON elsewhere (e.g. SQLite in dev).
JSONType = JSON().with_variant(JSONB(), "postgresql")

# Native uuid on Postgres, CHAR(32) elsewhere.
UUIDType = Uuid(as_uuid=True)


def enum_column(enum_cls: type[enum.Enum]) -> SAEnum:
    """A VARCHAR-backed enum column storing the enum *value*.

    `native_enum=False` keeps the schema portable (no Postgres ENUM types to
    migrate when a member is added) while still emitting a CHECK constraint.
    """
    return SAEnum(
        enum_cls,
        native_enum=False,
        length=32,
        validate_strings=True,
        values_callable=lambda cls: [member.value for member in cls],
    )


def utcnow() -> datetime:
    return datetime.now(UTC)


class Base(DeclarativeBase):
    """Base class for all ORM models."""


class UUIDPrimaryKeyMixin:
    id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, primary_key=True, default=uuid.uuid4
    )


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utcnow,
        server_default=func.now(),
        index=True,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utcnow,
        onupdate=utcnow,
        server_default=func.now(),
    )
