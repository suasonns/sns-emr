from typing import Optional


# ==========================================================
# VISIT TYPE NORMALIZATION (API-facing classification)
# ==========================================================

CANONICAL_VISIT_TYPES = {
    "RN",
    "LVN",
    "NP",
    "MD",
    "SW",
    "CHAPLAIN",
    "CHHA",
    "VOLUNTEER",
}

VISIT_TYPE_ALIASES = {
    "AIDE": "CHHA",
    "HHA": "CHHA",
    "CNA": "CHHA",
}


def normalize_visit_type(raw_visit_type: Optional[str]) -> str:
    """
    Normalize visit_type to canonical uppercase value.

    Core-layer rule:
      - Raise ValueError only (API layer maps to HTTP errors)
    """
    if not raw_visit_type:
        raise ValueError("visit_type is required")

    vt = raw_visit_type.strip().upper()
    vt = VISIT_TYPE_ALIASES.get(vt, vt)

    if vt not in CANONICAL_VISIT_TYPES:
        raise ValueError(
            f"Invalid visit_type '{raw_visit_type}'. "
            f"Allowed: {sorted(CANONICAL_VISIT_TYPES)}"
        )

    return vt


# ==========================================================
# VISIT SERVICE / DISCIPLINE NORMALIZATION
# ==========================================================

ALLOWED_VISIT_SERVICES = {
    "RN",
    "LVN",
    "LPN",
    "NP",
    "MD",
    "PA",
    "SW",
    "CHAPLAIN",
    "AIDE",
    "HHA",
    "PT",
    "OT",
    "ST",
}

_VISIT_SERVICE_ALIASES = {
    "NURSE": "RN",
    "REGISTERED NURSE": "RN",
    "SKILLED NURSE": "RN",
    "SN": "RN",
    "L.V.N": "LVN",
    "LPN": "LPN",
    "HHA": "HHA",
    "HOME HEALTH AIDE": "HHA",
    "HOMEHEALTHAIDE": "HHA",
    "AID": "AIDE",
    "AIDE": "AIDE",
    "SOCIAL WORK": "SW",
    "SOCIAL WORKER": "SW",
    "MSW": "SW",
    "CHAP": "CHAPLAIN",
    "SPIRITUAL CARE": "CHAPLAIN",
    "PHYSICIAN": "MD",
    "DOCTOR": "MD",
    "NURSE PRACTITIONER": "NP",
    "PHYSICIAN ASSISTANT": "PA",
}


def normalize_visit_service(value: Optional[str]) -> str:
    """
    Normalize visit service / discipline to canonical value.

    Core-layer rule:
      - Raise ValueError only
      - Deterministic normalization
    """
    if not value:
        raise ValueError("visit service is required")

    raw = str(value).strip()
    if not raw:
        raise ValueError("visit service is required")

    upper = raw.upper().replace("-", " ").replace("_", " ").strip()
    upper = " ".join(upper.split())

    canonical = _VISIT_SERVICE_ALIASES.get(upper, upper)

    if canonical not in ALLOWED_VISIT_SERVICES:
        raise ValueError(f"unsupported visit service: {raw}")

    return canonical


# ==========================================================
# BACKWARDS-COMPATIBILITY ALIAS (MUST BE LAST)
# ==========================================================

normalize_visit_discipline = normalize_visit_service
