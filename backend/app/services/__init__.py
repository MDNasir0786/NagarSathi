"""Business logic. Routers stay thin; all rules live here.

Submodules are deliberately **not** imported here: `auth.dependencies` needs
`profile_service`, and `profile_service` needs `auth.jwt`, so eager re-exports
would create an import cycle. Import the module you need directly, e.g.
``from app.services import complaint_service``.
"""

__all__ = [
    "admin_service",
    "analytics_service",
    "claude_service",
    "complaint_service",
    "profile_service",
]
