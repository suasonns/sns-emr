from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.patient_access import get_authorized_patient
from app.core.security import CurrentUser, get_current_user
from app.db_tenant_dependency import get_db_tenant
from app.services.supervisory_scheduling_service import compute_supervisory_schedule

router = APIRouter(prefix="/patients", tags=["supervisory-schedule"])


def _tenant_id_or_403(user: CurrentUser) -> uuid.UUID:
    tenant_id = getattr(user, "tenant_id", None)
    if not tenant_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Missing tenant context")
    return uuid.UUID(str(tenant_id))


@router.get("/{patient_id}/supervisory-schedule")
def get_supervisory_schedule(
    patient_id: uuid.UUID,
    db: Session = Depends(get_db_tenant),
    user: CurrentUser = Depends(get_current_user),
):
    """
    Returns CHHA (14-day) and LVN (28-day) RN-supervisory-visit compliance
    status for a patient: whether each cadence is required (based on active
    CHHA/LVN assignments), and if so its current due_date/status
    (SATISFIED / DUE / OVERDUE / NOT_YET_DUE).
    """
    tenant_id = _tenant_id_or_403(user)
    get_authorized_patient(db, patient_id, user)
    return compute_supervisory_schedule(db, tenant_id=tenant_id, patient_id=patient_id)
