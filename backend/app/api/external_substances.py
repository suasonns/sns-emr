from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(prefix="/external-substances", tags=["External Substances"])


@router.get("/")
def get_external_substances():
    """
    ✅ Placeholder endpoint

    Future use:
    - family-provided meds
    - OTC tracking
    - non-hospice-covered items
    """
    return {
        "message": "external substances module active",
        "status": "placeholder"
    }
