"""Engine, session factory and the FastAPI `get_db` dependency."""

from __future__ import annotations

import logging
from collections.abc import Generator
from typing import Any

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.utils.config import settings

logger = logging.getLogger(__name__)


def _engine_kwargs() -> dict[str, Any]:
    kwargs: dict[str, Any] = {
        "echo": settings.db_echo,
        "pool_pre_ping": True,  # drop dead connections (Supabase pooler recycles them)
        "future": True,
    }
    if settings.is_sqlite:
        # SQLite is only for local dev / tests; FastAPI runs handlers in a
        # threadpool so the same connection can be seen from another thread.
        kwargs["connect_args"] = {"check_same_thread": False}
    else:
        kwargs.update(
            pool_size=settings.db_pool_size,
            max_overflow=settings.db_max_overflow,
            pool_recycle=1800,
            connect_args={
                "application_name": "bhopal-civicai-api",
                "connect_timeout": 10,
            },
        )
    return kwargs


engine: Engine = create_engine(settings.database_url, **_engine_kwargs())

SessionLocal = sessionmaker(
    bind=engine, autocommit=False, autoflush=False, expire_on_commit=False
)


def get_db() -> Generator[Session, None, None]:
    """Yield a session, rolling back on failure and always closing."""
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def check_database_connection() -> bool:
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:  # pragma: no cover - surfaced via /ready
        logger.exception("database connectivity check failed")
        return False
