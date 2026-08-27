from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import AliasChoices, BaseModel, Field
from sqlalchemy.orm import Session

from app.core.capabilities import MANAGE_PATIENT_ASSIGNMENTS, has_capability
from app.core.patient_access import get_authorized_patient
from app.core.security import CurrentUser, get_current_user
from app.db_tenant_dependency import get_db_tenant
from app.models.patient_assignment import PatientAssignment
from app.models.user import User
from app.services.patient_assignment_service import (
    assign_patient_staff,
    deactivate_assignment,
    list_patient_assignments,
    normalize_assignment_discipline,
    serialize_assignment,
)


router = APIRouter(prefix="/patient-assignments", tags=["patient-assignments"])


class AssignmentCreate(BaseModel):
    patient_id: uuid.UUID
    discipline: str
    user_id: uuid.UUID = Field(
        validation_alias=AliasChoices("user_id", "staff_user_id")
    )
    service_area: str | None = None
    note: str | None = None
    is_primary: bool = True


class AssignmentDeactivate(BaseModel):
    note: str | None = None


def _tenant_id_or_403(user: CurrentUser) -> uuid.UUID:
    tenant_id = getattr(user, "tenant_id", None)
    if not tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Missing tenant context",
        )
    return uuid.UUID(str(tenant_id))


def _require_tenant_user(
    user: CurrentUser = Depends(get_current_user),
) -> CurrentUser:
    _tenant_id_or_403(user)
    return user


def _require_assignment_manager(
    user: CurrentUser = Depends(get_current_user),
) -> CurrentUser:
    _tenant_id_or_403(user)
    if not has_capability(user.role, MANAGE_PATIENT_ASSIGNMENTS):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Current role is not allowed to manage patient assignments",
        )
    return user


def _assignment_or_404(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    assignment_id: uuid.UUID,
) -> PatientAssignment:
    assignment = (
        db.query(PatientAssignment)
        .filter(
            PatientAssignment.id == assignment_id,
            PatientAssignment.tenant_id == tenant_id,
        )
        .first()
    )
    if not assignment:
        raise HTTPException(status_code=404, detail="Patient assignment not found")
    return assignment


@router.post("/", status_code=status.HTTP_201_CREATED, summary="Assign staff to a patient")
def assign_staff(
    payload: AssignmentCreate,
    db: Session = Depends(get_db_tenant),
    user: CurrentUser = Depends(_require_assignment_manager),
):
    tenant_id = _tenant_id_or_403(user)
    get_authorized_patient(db, payload.patient_id, user)

    assignment = assign_patient_staff(
        db,
        tenant_id=tenant_id,
        patient_id=payload.patient_id,
        staff_user_id=payload.user_id,
        discipline=normalize_assignment_discipline(payload.discipline),
        assigned_by=user.user_id,
        service_area=payload.service_area,
        note=payload.note,
        is_primary=payload.is_primary,
    )
    return assignment


@router.get("/patient/{patient_id}", summary="List patient staff assignments")
def get_patient_assignments(
    patient_id: uuid.UUID,
    include_inactive: bool = Query(False),
    db: Session = Depends(get_db_tenant),
    user: CurrentUser = Depends(_require_tenant_user),
):
    tenant_id = _tenant_id_or_403(user)
    get_authorized_patient(db, patient_id, user)

    return {
        "patient_id": str(patient_id),
        "include_inactive": include_inactive,
        "assignments": list_patient_assignments(
            db,
            tenant_id=tenant_id,
            patient_id=patient_id,
            include_inactive=include_inactive,
        ),
    }


@router.patch("/{assignment_id}/deactivate", summary="Deactivate a patient staff assignment")
def deactivate_patient_assignment(
    assignment_id: uuid.UUID,
    payload: AssignmentDeactivate,
    db: Session = Depends(get_db_tenant),
    user: CurrentUser = Depends(_require_assignment_manager),
):
    tenant_id = _tenant_id_or_403(user)
    assignment = _assignment_or_404(
        db,
        tenant_id=tenant_id,
        assignment_id=assignment_id,
    )
    get_authorized_patient(db, assignment.patient_id, user)

    staff_user = db.query(User).filter(User.id == assignment.user_id).first()
    assigned_by_user = (
        db.query(User).filter(User.id == assignment.assigned_by).first()
        if assignment.assigned_by
        else None
    )

    if assignment.active:
        assignment = deactivate_assignment(
            db,
            assignment=assignment,
            note=payload.note,
        )
    elif payload.note is not None:
        assignment.note = payload.note
        db.commit()
        db.refresh(assignment)

    return serialize_assignment(
        assignment,
        staff_user=staff_user,
        assigned_by_user=assigned_by_user,
    )
