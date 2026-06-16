# app/api/idg/router.py

from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db_request_dependency import get_db_tenant_with_request_state

from app.services.idg_engine import enforce_idg_readiness

router = APIRouter(prefix="/idg", tags=["IDG"])


# =========================================================
# ✅ IDG READINESS CHECK
# =========================================================

@router.get("/{patient_id}/check")
def check_idg_status(
    patient_id: UUID,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db_tenant_with_request_state),
):
    """
    Check if patient is ready for IDG review.
    """

    result = enforce_idg_readiness(
        db=db,
        patient_id=patient_id,
        tenant_id=current_user.tenant_id,
    )

    return {
        "blocked": result.blocked,
        "reasons": result.reasons,
    }
