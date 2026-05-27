# app/domain/visits.py

VISIT_TYPE_ALIASES = {
    "AIDE": "CHHA",
    "CHHA": "CHHA",
}

ALLOWED_VISIT_TYPES = {
    "RN",
    "LVN",
    "NP",
    "MD",
    "SW",
    "CHAPLAIN",
    "CHHA",
    "VOLUNTEER",
}


def normalize_visit_type(value: str) -> str:
    """
    Normalize and validate visit_type.

    - Uppercase normalization
    - Alias mapping (AIDE -> CHHA)
    - Allowed set enforcement
    """
    if not value:
        raise ValueError("visit_type is required")

    normalized = value.strip().upper()
    normalized = VISIT_TYPE_ALIASES.get(normalized, normalized)

    if normalized not in ALLOWED_VISIT_TYPES:
        raise ValueError(f"Invalid visit_type: {value}")

    return normalized