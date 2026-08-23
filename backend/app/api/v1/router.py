"""Aggregate router for API v1."""

from fastapi import APIRouter

from app.api.v1 import admin, ai, analytics, auth, complaints, profile

api_router = APIRouter()

api_router.include_router(auth.router)
api_router.include_router(profile.router)
api_router.include_router(complaints.router)
api_router.include_router(admin.router)
api_router.include_router(analytics.router)
api_router.include_router(ai.router)

__all__ = ["api_router"]
