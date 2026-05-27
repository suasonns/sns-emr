import uuid
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db_tenant_dependency import get_db_tenant
from app.core.security import get_current_user
from app.models.patient_assignment import PatientAssignment


router = APIRouter(prefix="/patient-assignments", tags=["patient-assignments"])


class AssignmentCreate(BaseModel):
    patient_id: uuid.UUID
    discipline: str  # RN/MSW/SC
    staff_user_id: uuid.UUID
    service_area: str | None = None
    note: str | None = None


@router.post("/", summary="Assign staff to a patient (no task creation)")
def assign_staff(
    payload: AssignmentCreate,
    db: Session = Depends(get_db_tenant),
    user=Depends(get_current_user),
):
    discipline = payload.discipline.strip().upper()
    if discipline not in {"RN", "MSW", "SC"}:
        raise HTTPException(status_code=400, detail="discipline must be RN, MSW, or SC")

    # Mark any prior active assignment for that discipline as REASSIGNED
    db.query(PatientAssignment).filter(
        PatientAssignment.patient_id == payload.patient_id,
        PatientAssignment.discipline == discipline,
        PatientAssignment.status == "ASSIGNED",
    ).update({"status": "REASSIGNED"})

    assignment = PatientAssignment(
        patient_id=payload.patient_id,
        discipline=discipline,
        staff_user_id=payload.staff_user_id,
        service_area=payload.service_area,
        status="ASSIGNED",
        assigned_by=user.id,
        note=payload.note,
    )

    db.add(assignment)
    db.commit()
    db.refresh(assignment)
    return assignment