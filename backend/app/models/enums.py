"""Domain enumerations shared by models, schemas and services."""

from __future__ import annotations

from enum import Enum


class UserRole(str, Enum):
    CITIZEN = "citizen"
    ADMIN = "admin"


class ComplaintCategory(str, Enum):
    ROAD = "road"
    GARBAGE = "garbage"
    STREETLIGHT = "streetlight"
    WATER = "water"
    TRAFFIC = "traffic"
    DRAINAGE = "drainage"
    OTHER = "other"


class ComplaintSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ComplaintStatus(str, Enum):
    SUBMITTED = "submitted"
    ACKNOWLEDGED = "acknowledged"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    REJECTED = "rejected"
    DUPLICATE = "duplicate"
    CLOSED = "closed"


#: Statuses that mean no further field work is expected.
TERMINAL_STATUSES: frozenset[ComplaintStatus] = frozenset(
    {
        ComplaintStatus.RESOLVED,
        ComplaintStatus.REJECTED,
        ComplaintStatus.DUPLICATE,
        ComplaintStatus.CLOSED,
    }
)

#: Statuses counted as "open" in dashboards and hotspot analysis.
OPEN_STATUSES: frozenset[ComplaintStatus] = frozenset(
    {
        ComplaintStatus.SUBMITTED,
        ComplaintStatus.ACKNOWLEDGED,
        ComplaintStatus.ASSIGNED,
        ComplaintStatus.IN_PROGRESS,
    }
)


class AIAnalysisStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"       # Claude produced the analysis
    FALLBACK = "fallback"         # deterministic analyser was used instead
    FAILED = "failed"
    SKIPPED = "skipped"           # AI disabled by configuration


class UpdateType(str, Enum):
    CREATED = "created"
    AI_ANALYSIS = "ai_analysis"
    STATUS_CHANGE = "status_change"
    DEPARTMENT_ASSIGNED = "department_assigned"
    PRIORITY_CHANGE = "priority_change"
    SEVERITY_CHANGE = "severity_change"
    CATEGORY_CHANGE = "category_change"
    ASSIGNEE_CHANGE = "assignee_change"
    RESOLUTION_NOTE = "resolution_note"
    EVIDENCE_ADDED = "evidence_added"
    CONFIRMATION = "confirmation"
    DUPLICATE_LINKED = "duplicate_linked"
    COMMENT = "comment"


#: Weight used when folding severity into the deterministic priority score.
SEVERITY_WEIGHT: dict[ComplaintSeverity, int] = {
    ComplaintSeverity.LOW: 20,
    ComplaintSeverity.MEDIUM: 45,
    ComplaintSeverity.HIGH: 70,
    ComplaintSeverity.CRITICAL: 90,
}
