from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)
from sqlalchemy.orm import Session

from app.core.auth import CurrentUser
from app.core.db_session import get_db
from app.core.permissions import require_roles
from app.models.patient import Patient
from app.services.admission.admission_workflow_service import (
    AdmissionWorkflowService,
)

router = APIRouter(
    prefix="/admission",
    tags=["admission"],
)


def get_patient_or_404(
    db: Session,
    patient_id: UUID,
) -> Patient:

    patient = (
        db.query(Patient)
        .filter(Patient.id == patient_id)
        .first()
    )

    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found",
        )

    return patient


@router.get("/{patient_id}/summary")
def get_admission_summary(
    patient_id: UUID,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(
        require_roles(
            [
                "RN",
                "NP",
                "MD",
                "ADMIN",
                "DPCS",
            ]
        )
    ),
):

    patient = get_patient_or_404(
        db,
        patient_id,
    )

    return AdmissionWorkflowService.get_admission_summary(
        patient=patient,
    )


@router.post("/{patient_id}/status")
def change_admission_status(
    patient_id: UUID,
    new_status: str,
    reason: str | None = None,
    notes: str | None = None,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(
        require_roles(
            [
                "RN",
                "NP",
                "MD",
                "ADMIN",
                "DPCS",
            ]
        )
    ),
):

    patient = get_patient_or_404(
        db,
        patient_id,
    )

    result = (
        AdmissionWorkflowService.change_status(
            db=db,
            patient=patient,
            new_status=new_status,
            changed_by=user.user_id,
            role=user.role,
            reason=reason,
            notes=notes,
        )
    )

    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result,
        )

    return result


@router.post("/{patient_id}/start-soc")
def start_soc(
    patient_id: UUID,
    notes: str | None = None,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(
        require_roles(
            [
                "RN",
                "NP",
                "MD",
                "DPCS",
            ]
        )
    ),
):

    patient = get_patient_or_404(
        db,
        patient_id,
    )

    result = (
        AdmissionWorkflowService.start_soc(
            db=db,
            patient=patient,
            changed_by=user.user_id,
            role=user.role,
            notes=notes,
        )
    )

    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result,
        )

    return result


@router.post("/{patient_id}/complete")
def complete_admission(
    patient_id: UUID,
    notes: str | None = None,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(
        require_roles(
            [
                "RN",
                "NP",
                "MD",
                "DPCS",
            ]
        )
    ),
):

    patient = get_patient_or_404(
        db,
        patient_id,
    )

    result = (
        AdmissionWorkflowService.complete_admission(
            db=db,
            patient=patient,
            changed_by=user.user_id,
            role=user.role,
            notes=notes,
        )
    )

    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result,
        )

    return result


@router.post("/{patient_id}/non-admit")
def mark_non_admit(
    patient_id: UUID,
    reason: str,
    notes: str | None = None,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(
        require_roles(
            [
                "RN",
                "NP",
                "MD",
                "ADMIN",
                "DPCS",
            ]
        )
    ),
):

    patient = get_patient_or_404(
        db,
        patient_id,
    )

    result = (
        AdmissionWorkflowService.mark_non_admit(
            db=db,
            patient=patient,
            changed_by=user.user_id,
            role=user.role,
            reason=reason,
            notes=notes,
        )
    )

    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result,
        )

    return result