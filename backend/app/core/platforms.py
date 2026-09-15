# app/core/platforms.py
"""SNS Platform assignment -- the highest level of the SNS Staff & Access
organizational hierarchy (Platform > Department > Job Title > Platform
Role > Access Level).

Only "SNS Hospice Solutions" is live today (staffed, owned, secured).
"SNS Home Health Solutions" and "SNS Scribe" are listed as known future
SNS platforms so the Platform field is selectable now without a later
User Management redesign -- but they have no staff, roles, ownership, or
service accounts of their own yet. Do not build separate platform
infrastructure for them until a future phase explicitly authorizes it.
"""

DEFAULT_PLATFORM = "SNS Hospice Solutions"

AVAILABLE_PLATFORMS = [
    "SNS Hospice Solutions",
    "SNS Home Health Solutions",
    "SNS Scribe",
]


def normalize_platform(value: str | None) -> str:
    """Returns the canonical platform name, defaulting to SNS Hospice
    Solutions when unset. Raises ValueError if the value is not a known
    SNS platform."""
    if not value or not value.strip():
        return DEFAULT_PLATFORM
    normalized = value.strip()
    for known in AVAILABLE_PLATFORMS:
        if known.lower() == normalized.lower():
            return known
    raise ValueError(f"platform must be one of: {AVAILABLE_PLATFORMS}")
