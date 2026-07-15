from __future__ import annotations

from typing import Optional


# =========================================================
# VISIT TYPE NORMALIZATION
# =========================================================

# Canonical alias mapping (input -> normalized output)
VISIT_TYPE_ALIASES = {
    "AIDE": "CHHA",
    "CNA": "CHHA",
    "HOME HEALTH AIDE": "CHHA",
}

# System-approved canonical visit types
#
# IMPORTANT:
# Must remain aligned with app/api/visits.py
# and any visit validation paths.
ALLOWED_VISIT_TYPES = {
    "RN",
    "LVN",
    "NP",
    "PA",
    "MD",
    "SW",
    "CHAPLAIN",
    "CHHA",
    "VOLUNTEER",
    "ADMINISTRATIVE",
}


# =========================================================
# NORMALIZATION HELPERS
# =========================================================

def _normalize_raw(value: str) -> str:
    """
    Normalize raw string input into a comparable canonical form.

    - strips whitespace
    - uppercases
    - collapses internal spacing

    Raises:
        ValueError: if value is empty or invalid type
    """
    if not isinstance(value, str):
        raise ValueError("visit_type must be a string")

    normalized = value.strip().upper()

    if not normalized:
        raise ValueError("visit_type is required")

    normalized = " ".join(normalized.split())

    return normalized


def _apply_alias(normalized: str) -> str:
    """
    Apply alias mapping to normalized value.

    Ensures real-world inputs map correctly to canonical system types.
    """
    return VISIT_TYPE_ALIASES.get(normalized, normalized)


def _validate_allowed(normalized: str) -> str:
    """
    Validate normalized visit type against allowed set.

    Raises:
        ValueError: if value not part of allowed canonical types
    """
    if normalized not in ALLOWED_VISIT_TYPES:
        raise ValueError(f"Invalid visit_type: {normalized}")

    return normalized


# =========================================================
# PUBLIC API
# =========================================================

def normalize_visit_type(value: str) -> str:
    """
    Normalize and validate visit_type for enterprise use.

    Guarantees:
    - strict canonical values
    - alias resolution
    - deterministic output for downstream rule systems

    This function is the SINGLE SOURCE OF TRUTH
    for visit_type normalization.
    """
    normalized = _normalize_raw(value)
    normalized = _apply_alias(normalized)
    normalized = _validate_allowed(normalized)

    return normalized


def safe_normalize_visit_type(
    value: Optional[str],
    default: str = "RN",
) -> str:
    """
    Safe normalization wrapper.

    Returns:
        normalized value when valid

    Falls back to default when invalid.
    """
    if not value:
        return default

    try:
        return normalize_visit_type(value)
    except ValueError:
        return default


def is_rn_visit(value: Optional[str]) -> bool:
    """
    Utility helper for RN detection.

    Returns:
        True if visit resolves to RN.
    """
    try:
        return normalize_visit_type(value) == "RN"
    except ValueError:
        return False