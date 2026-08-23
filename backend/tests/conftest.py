"""Pytest fixtures: isolated SQLite database, TestClient and signed tokens."""

from __future__ import annotations

import os
import uuid
from collections.abc import Iterator
from datetime import UTC, datetime, timedelta

# Configure the environment before any app module is imported.
TEST_SECRET = "test-only-jwt-secret-please-do-not-use-anywhere-else"
os.environ.update(
    {
        "APP_ENV": "development",
        "DATABASE_URL": "sqlite:///./test_bhopal_civicai.db",
        "SUPABASE_JWT_SECRET": TEST_SECRET,
        "SUPABASE_JWT_ALGORITHMS": "HS256",
        "SUPABASE_JWT_AUDIENCE": "authenticated",
        "SUPABASE_JWT_ISSUER": "https://test.local/auth/v1",
        "SUPABASE_URL": "",
        "ANTHROPIC_API_KEY": "",
        "AI_ENABLED": "true",
        "ADMIN_EMAILS": "admin@bhopalcivicai.in",
        "AUTO_CREATE_TABLES": "true",
        "SEED_DEPARTMENTS": "true",
        "RATE_LIMIT_ENABLED": "false",
        "LOG_LEVEL": "WARNING",
    }
)

import jwt
import pytest
from fastapi.testclient import TestClient

from app.database.base import Base
from app.database.session import SessionLocal, engine
from app.main import app
from app.utils.config import settings

CITIZEN_EMAIL = "citizen@example.com"
OTHER_EMAIL = "neighbour@example.com"
ADMIN_EMAIL = "admin@bhopalcivicai.in"

BHOPAL = (23.2331, 77.4344)
BHOPAL_NEAR = (23.23345, 77.43455)


def make_token(email: str, name: str | None = None, *, hours: int = 2) -> str:
    """Mint a Supabase-shaped HS256 access token for tests."""
    now = datetime.now(UTC)
    claims = {
        "sub": str(uuid.uuid5(uuid.NAMESPACE_URL, f"bhopal-civicai:{email}")),
        "email": email,
        "aud": settings.supabase_jwt_audience,
        "iss": settings.expected_issuer,
        "role": "authenticated",
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(hours=hours)).timestamp()),
        "user_metadata": {"full_name": name or email.split("@")[0]},
    }
    return jwt.encode(claims, TEST_SECRET, algorithm="HS256")


def auth(email: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {make_token(email)}"}


@pytest.fixture(scope="session", autouse=True)
def _fresh_database() -> Iterator[None]:
    """Drop and recreate the schema once per test session."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="session")
def client() -> Iterator[TestClient]:
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def db() -> Iterator[object]:
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def citizen_headers() -> dict[str, str]:
    return auth(CITIZEN_EMAIL)


@pytest.fixture
def other_headers() -> dict[str, str]:
    return auth(OTHER_EMAIL)


@pytest.fixture
def admin_headers() -> dict[str, str]:
    return auth(ADMIN_EMAIL)


@pytest.fixture
def sample_complaint() -> dict:
    return {
        "title": "Large pothole near Habibganj underbridge",
        "description": (
            "A deep pothole has opened up in the left lane just after the underbridge. "
            "Two-wheelers swerve into traffic to avoid it and it floods when it rains."
        ),
        "latitude": BHOPAL[0],
        "longitude": BHOPAL[1],
        "address": "Habibganj Underbridge, Bhopal",
        "ward": "Ward 32",
        "category_hint": "road",
    }
