"""Schema creation and reference-data seeding."""

from __future__ import annotations

import logging

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.base import Base
from app.database.session import SessionLocal, engine
from app.models import Department
from app.models.enums import ComplaintCategory
from app.utils.config import settings

logger = logging.getLogger(__name__)

#: Default Bhopal Municipal Corporation departments and the categories they own.
DEFAULT_DEPARTMENTS: list[dict] = [
    {
        "name": "Public Works Department",
        "code": "PWD",
        "description": "Roads, footpaths, potholes and civil infrastructure.",
        "categories": [ComplaintCategory.ROAD.value],
        "contact_email": "pwd@bhopalcivicai.in",
        "sla_hours": 96,
    },
    {
        "name": "Solid Waste Management",
        "code": "SWM",
        "description": "Garbage collection, dumping points and street sweeping.",
        "categories": [ComplaintCategory.GARBAGE.value],
        "contact_email": "swm@bhopalcivicai.in",
        "sla_hours": 24,
    },
    {
        "name": "Electrical & Street Lighting",
        "code": "ELEC",
        "description": "Street lights, poles and public electrical faults.",
        "categories": [ComplaintCategory.STREETLIGHT.value],
        "contact_email": "electrical@bhopalcivicai.in",
        "sla_hours": 48,
    },
    {
        "name": "Water Supply",
        "code": "WATER",
        "description": "Pipelines, leakages, supply interruptions and water quality.",
        "categories": [ComplaintCategory.WATER.value],
        "contact_email": "water@bhopalcivicai.in",
        "sla_hours": 24,
    },
    {
        "name": "Traffic Police & Management",
        "code": "TRAFFIC",
        "description": "Signals, signage, encroachment and traffic congestion.",
        "categories": [ComplaintCategory.TRAFFIC.value],
        "contact_email": "traffic@bhopalcivicai.in",
        "sla_hours": 48,
    },
    {
        "name": "Drainage & Sewerage",
        "code": "DRAIN",
        "description": "Storm drains, sewer overflow and waterlogging.",
        "categories": [ComplaintCategory.DRAINAGE.value],
        "contact_email": "drainage@bhopalcivicai.in",
        "sla_hours": 48,
    },
    {
        "name": "General Grievance Cell",
        "code": "GENERAL",
        "description": "Fallback department for uncategorised civic issues.",
        "categories": [ComplaintCategory.OTHER.value],
        "contact_email": "grievance@bhopalcivicai.in",
        "sla_hours": 120,
    },
]


def create_tables() -> None:
    """Create any missing tables.

    Convenient for local development. In production run
    `migrations/001_init.sql` against Supabase and set
    AUTO_CREATE_TABLES=false — this call never alters existing columns.
    """
    Base.metadata.create_all(bind=engine)
    logger.info("database schema ensured (%d tables)", len(Base.metadata.tables))


def seed_departments(db: Session | None = None) -> int:
    """Insert the default departments that do not already exist."""
    owns_session = db is None
    session = db or SessionLocal()
    created = 0
    try:
        existing = set(session.scalars(select(Department.code)).all())
        for payload in DEFAULT_DEPARTMENTS:
            if payload["code"] in existing:
                continue
            session.add(Department(**payload))
            created += 1
        if created:
            session.commit()
            logger.info("seeded %d departments", created)
        return created
    except Exception:
        session.rollback()
        raise
    finally:
        if owns_session:
            session.close()


def init_database() -> None:
    """Boot-time database preparation, driven by configuration flags."""
    if settings.auto_create_tables:
        create_tables()
    if settings.seed_departments:
        seed_departments()
