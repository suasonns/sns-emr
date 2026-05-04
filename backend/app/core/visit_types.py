from fastapi import HTTPException

CANONICAL_VISIT_TYPES = {
    "RN", "LVN", "NP", "MD", "SW", "CHAPLAIN", "CHHA", "VOLUNTEER",
}

VISIT_TYPE_ALIASES = {
    "AIDE": "CHHA",
    "HHA": "CHHA",
    "CNA": "CHHA",
}

def normalize_visit_type(raw_visit_type: str) -> str:
    if not raw_visit_type:
        raise HTTPException(status_code=400, detail="visit_type is required")

    vt = raw_visit_type.strip().upper()
    vt = VISIT_TYPE_ALIASES.get(vt, vt)

    if vt not in CANONICAL_VISIT_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid visit_type '{raw_visit_type}'. Allowed: {sorted(CANONICAL_VISIT_TYPES)}",
        )
    return vt