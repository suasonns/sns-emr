"""
SNS Staff & Access -- account-type taxonomy (Phase UM-2A).

Distinguishes human platform staff from non-human platform identities
(service accounts, automation accounts, API clients) on the same `users`
table. Like app.core.departments, this is a validated Python set, not a
database lookup table -- it mirrors PLATFORM_ROLES/PLATFORM_DEPARTMENTS.

This module only defines and validates the *label*. Full first-class
Service Account / API Client management (owner/purpose/scope fields,
dedicated lifecycle) is explicitly deferred to a later phase (UM-5/UM-6
per the approved SNS Staff & Access roadmap) -- do not build that
workflow against this module without re-confirming scope.
"""

from __future__ import annotations

ACCOUNT_TYPES: frozenset[str] = frozenset(
    {
        "HUMAN_STAFF",
        "SERVICE_ACCOUNT",
        "AUTOMATION_ACCOUNT",
        "API_CLIENT",
    }
)

DEFAULT_ACCOUNT_TYPE = "HUMAN_STAFF"


def normalize_account_type(value: str | None) -> str:
    """Uppercases/validates an account-type string. Blank/None defaults to
    HUMAN_STAFF (every SNS Staff & Access account created today is a human
    staff member). Raises ValueError for anything not in ACCOUNT_TYPES so
    callers can turn it into a 422 response."""
    if value is None:
        return DEFAULT_ACCOUNT_TYPE
    normalized = value.strip().upper()
    if not normalized:
        return DEFAULT_ACCOUNT_TYPE
    if normalized not in ACCOUNT_TYPES:
        raise ValueError(f"account_type must be one of {sorted(ACCOUNT_TYPES)}")
    return normalized
