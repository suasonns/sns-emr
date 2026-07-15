"""
Enterprise visit type normalizer.

Compliance rule:
Visit types must be normalized to canonical uppercase values.
"""

from __future__ import annotations

from fastapi import HTTPException, status


CANONICAL_VISIT_TYPES = {
    "RN",
    "LVN",
    "LPN",
    "NP",
    "MD",
    "SW",
    "CHAPLAIN",
    "AIDE",
    "ADMINISTRATIVE",
}


VISIT_TYPE_ALIASES = {
    "NURSE": "RN",
    "REGISTERED NURSE": "RN",
    "SKILLED NURSE": "RN",
    "SOCIAL WORK": "SW",
    "SOCIAL WORKER": "SW",
    "CHAP": "CHAPLAIN",
    "SPIRITUAL CARE": "CHAPLAIN",
    "HOME HEALTH AIDE": "AIDE",
    "HHA": "AIDE",
}


def normalize_visit_type(raw_visit_type: str) -> str:
    """
    Normalize visit_type to a canonical value.

    Raises 400 if the visit type is invalid.
    """
    if not raw_visit_type:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="visit_type is required",
        )

    value = raw_visit_type.strip().upper()

    # Apply aliases
    value = VISIT_TYPE_ALIASES.get(value, value)

    if value not in CANONICAL_VISIT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid visit_type '{raw_visit_type}'",
        )

    return value