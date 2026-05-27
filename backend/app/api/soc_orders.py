import uuid
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db_tenant_dependency import get_db_tenant
from app.core.security import get_current_user
from app.models.task import Task

# you will create this model below
from app.models.patient_assignment import PatientAssignment


router = APIRouter(prefix="/soc-orders", tags=["soc-orders"])


class RNAdmissionOrder(BaseModel):
    # RN is always required for admission workflow
    order_rn: bool = True

    # optional, based on hospice practice and case needs
    order_msw: bool = False
    order_sc: bool = False

    # if you want to allow RN to document “MSW declined”
    msw_declined: bool = False
    sc_declined: bool = False


def _due(dt: datetime, days: int) -> datetime:
    return dt + timedelta(days=days)


@router.post("/patients/{patient_id}/rn-admission", summary="Finalize RN admission order and create SOC tasks")
def finalize_rn_admission_order(
    patient_id: uuid.UUID,
    payload: RNAdmissionOrder,
    db: Session = Depends(get_db_tenant),
    user=Depends(get_current_user),
):
    now = datetime.utcnow()

    # Determine required disciplines for tasks
    disciplines = ["RN"]
    if payload.order_msw and not payload.msw_declined:
        disciplines.append("MSW")
    if payload.order_sc and not payload.sc_declined:
        disciplines.append("SC")

    # Pull active assignments for those disciplines (optional but recommended)
    assignments = (
        db.query(PatientAssignment)
        .filter(PatientAssignment.patient_id == patient_id)
        .filter(PatientAssignment.status == "ASSIGNED")
        .all()
    )
    assignment_map = {a.discipline.upper(): a for a in assignments}

    # If RN not assigned, block (RN must be assigned in real ops)
    if "RN" not in assignment_map:
        raise HTTPException(status_code=400, detail="RN not assigned. Assign RN before finalizing admission order.")

    created = []

    for d in disciplines:
        assignee = assignment_map.get(d)

        # If MSW/SC ordered but not assigned yet -> still create task, unassigned
        assigned_user_id = assignee.staff_user_id if assignee else None

        # Due logic (compliance-first but practice-aligned):
        # RN: due in 2 days (48h)
        # MSW/SC: due in 5 days
        if d == "RN":
            due_date = _due(now, 2)
            task_type = "RN_SOC"
        elif d == "MSW":
            due_date = _due(now, 5)
            task_type = "MSW_ICA"
        else:
            due_date = _due(now, 5)
            task_type = "SC_ICA"

        task = Task(
            id=uuid.uuid4(),
            patient_id=patient_id,
            task_type=task_type,
            status="OPEN",
            due_date=due_date,
            assigned_user_id=assigned_user_id,
            schedule_status="NEEDS_SCHEDULING",
        )
        db.add(task)
        created.append(task)

    db.commit()

    return {
        "patient_id": str(patient_id),
        "created_task_count": len(created),
        "task_types": [t.task_type for t in created],
        "schedule_status": "NEEDS_SCHEDULING",
    }
