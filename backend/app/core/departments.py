"""
SNS Staff & Access -- department taxonomy (Phase UM-2).

Department is a presentational/organizational classification only -- it
grants NO permissions. Authorization always flows through
app.core.roles.role_can() / PLATFORM_PERMISSION_MATRIX, never through this
module. This mirrors how PLATFORM_ROLES itself is a validated Python set
rather than a database table: adding a department here requires no
migration, matching the existing role-handling convention in this codebase.
"""

from __future__ import annotations

PLATFORM_DEPARTMENTS: frozenset[str] = frozenset(
    {
        "EXECUTIVE",
        "PLATFORM_ADMINISTRATION",
        "CUSTOMER_SUPPORT",
        "CUSTOMER_SERVICE",
        "DEVELOPMENT",
        "DEVOPS",
        "SECURITY",
        "COMPLIANCE",
        "BILLING_AND_LICENSING",
        "AI_OPERATIONS",
        "QUALITY_ASSURANCE",
        "IMPLEMENTATION",
    }
)


def normalize_department(value: str | None) -> str | None:
    """Uppercases/validates a department string; returns None for blank
    input. Raises ValueError for anything not in PLATFORM_DEPARTMENTS so
    callers can turn it into a 400 response."""
    if value is None:
        return None
    normalized = value.strip().upper()
    if not normalized:
        return None
    if normalized not in PLATFORM_DEPARTMENTS:
        raise ValueError(f"department must be one of {sorted(PLATFORM_DEPARTMENTS)}")
    return normalized
