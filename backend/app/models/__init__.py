"""ORM models. Importing this package registers every table on `Base`."""

from app.database.base import Base
from app.models.complaint import Complaint
from app.models.complaint_confirmation import ComplaintConfirmation
from app.models.complaint_update import ComplaintUpdate
from app.models.department import Department
from app.models.enums import (
    OPEN_STATUSES,
    SEVERITY_WEIGHT,
    TERMINAL_STATUSES,
    AIAnalysisStatus,
    ComplaintCategory,
    ComplaintSeverity,
    ComplaintStatus,
    UpdateType,
    UserRole,
)
from app.models.profile import Profile

__all__ = [
    "OPEN_STATUSES",
    "SEVERITY_WEIGHT",
    "TERMINAL_STATUSES",
    "AIAnalysisStatus",
    "Base",
    "Complaint",
    "ComplaintCategory",
    "ComplaintConfirmation",
    "ComplaintSeverity",
    "ComplaintStatus",
    "ComplaintUpdate",
    "Department",
    "Profile",
    "UpdateType",
    "UserRole",
]
