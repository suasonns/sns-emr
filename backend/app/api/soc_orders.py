# app/api/soc_orders.py
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db_tenant_dependency import get_db_tenant
from app.models.patient import Patient
from app.models.task import Task
from app.models.enums import TaskType, TaskOrigin, TaskDiscipline, TaskStatus
from app.tenancy.registry import assert_known_tenant


router = APIRouter(prefix="/soc-orders", tags=["soc-orders"])


class RNAdmissionOrder(BaseModel):
    # RN is always required for admission workflow
    order_rn: bool = True


def _require_tenant(user) -> str:
    tenant_id = getattr(user, "tenant_id", None)
    if tenant_id is None and isinstance(user, dict):
        tenant_id = user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=401, detail="Missing tenant context")

    assert_known_tenant(str(tenant_id))
    return str(tenant_id)


@router.post(
    "/patients/{patient_id}/rn-admission",
    summary="Finalize RN admission order and create ICA tasks",
)
def finalize_rn_admission_order(
    patient_id: uuid.UUID,
    payload: RNAdmissionOrder,
    db: Session = Depends(get_db_tenant),
    user=Depends(get_current_user),
):
    tenant_id = _require_tenant(user)

    patient = (
        db.query(Patient)
        .filter(Patient.id == patient_id, Patient.tenant_id == tenant_id)
        .first()
    )
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    if not payload.order_rn:
        raise HTTPException(status_code=400, detail="RN admission order cannot be false")

    soc_date = datetime.now(timezone.utc).date()

    ica_specs = [
        (TaskType.INITIAL_RN_ICA, TaskDiscipline.RN, soc_date + timedelta(days=2)),
        (TaskType.INITIAL_MSW_ICA, TaskDiscipline.SW, soc_date + timedelta(days=5)),
        (TaskType.INITIAL_SC_ICA, TaskDiscipline.CHAPLAIN, soc_date + timedelta(days=5)),
        (TaskType.INITIAL_BEREAVEMENT, TaskDiscipline.SW, soc_date + timedelta(days=5)),
    ]

    created = []
    for task_type, discipline, due_date in ica_specs:
        db.add(
            Task(
                id=uuid.uuid4(),
                tenant_id=tenant_id,
                patient_id=patient.id,
                task_type=task_type,
                origin=TaskOrigin.ADMISSION,
                discipline=discipline,
                status=TaskStatus.PENDING,  # ✅ enum-safe
                due_date=due_date,
                created_by=getattr(user, "id", None),
            )
        )
        created.append(task_type.value)

    db.commit()

    return {
        "status": "rn_admission_finalized",
        "patient_id": str(patient_id),
        "ica_tasks_created": created,
    }