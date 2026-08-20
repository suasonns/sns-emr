from __future__ import annotations

from uuid import UUID
from datetime import datetime

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.security import CurrentUser
from app.core.db_session import get_db
from app.core.permissions import require_roles
from app.core.patient_access import get_authorized_patient
from app.models.patient import Patient
from app.services.admission.admission_workflow_service import (
    AdmissionWorkflowService,
)
from app.services.admission.admission_guardrail_service import (
    AdmissionGuardrailService,
    TrainingModeBlockedError,
    AdmissionPrerequisiteError,
)

router = APIRouter(
    prefix="/admission",
    tags=["admission"],
)


# =========================================================
# REQUEST MODELS (INLINE ON PURPOSE)
# Self-contained, clean Swagger JSON bodies.
# =========================================================

class ChangeStatusRequest(BaseModel):
    new_status: str = Field(
        ...,
        json_schema_extra={"example": "SOC_IN_PROGRESS"},
    )
    reason: str | None = Field(
        default=None,
        json_schema_extra={"example": "Clinical review completed"},
    )
    notes: str | None = Field(
        default=None,
        json_schema_extra={"example": "Optional internal note"},
    )


class StartSocRequest(BaseModel):
    soc_datetime: datetime = Field(
        ...,
        json_schema_extra={"example": "2026-07-16T10:00:00Z"},
    )
    notes: str | None = Field(
        default=None,
        json_schema_extra={"example": "SOC manually entered after bedside assessment"},
    )


class CompleteAdmissionRequest(BaseModel):
    admit_datetime: datetime | None = Field(
        default=None,
        json_schema_extra={"example": "2026-07-16T11:30:00Z"},
    )
    notes: str | None = Field(
        default=None,
        json_schema_extra={"example": "Admission finalized after SOC"},
    )


class NonAdmitRequest(BaseModel):
    reason: str = Field(
        ...,
        json_schema_extra={"example": "Patient declined hospice services"},
    )
    notes: str | None = Field(
        default=None,
        json_schema_extra={"example": "Discussed with family"},
    )


# =========================================================
# HELPERS
# =========================================================

def _tenant_id_or_403(user: CurrentUser):
    tenant_id = getattr(user, "tenant_id", None)
    if not tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Missing tenant context",
        )
    return tenant_id


def _raise_workflow_http_error(exc: Exception) -> None:
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=str(exc),
    ) from exc


def get_patient_or_404(
    db: Session,
    patient_id: UUID,
    user: CurrentUser,
) -> Patient:
    _tenant_id_or_403(user)
    return get_authorized_patient(db, patient_id, user)


# =========================================================
# ROUTES
# =========================================================

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
        user,
    )

    try:
        return AdmissionWorkflowService.get_admission_summary(
            db=db,
            patient=patient,
        )
    except ValueError as exc:
        _raise_workflow_http_error(exc)


@router.post("/{patient_id}/status")
def change_admission_status(
    patient_id: UUID,
    payload: ChangeStatusRequest,
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
        user,
    )

    try:
        result = AdmissionWorkflowService.change_status(
            db=db,
            patient=patient,
            new_status=payload.new_status,
            changed_by=user.user_id,
            role=user.role,
            reason=payload.reason,
            notes=payload.notes,
        )
    except ValueError as exc:
        _raise_workflow_http_error(exc)

    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result,
        )

    return result


@router.post("/{patient_id}/start-soc")
def start_soc(
    patient_id: UUID,
    payload: StartSocRequest,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(
        require_roles(
            [
                "RN",
                "NP",
                "MD",
                "DPCS",
                "ADMIN",
            ]
        )
    ),
):
    patient = get_patient_or_404(
        db,
        patient_id,
        user,
    )

    try:
        result = AdmissionGuardrailService.set_soc_datetime(
            db=db,
            patient=patient,
            soc_datetime=payload.soc_datetime,
            actor_user_id=user.user_id,
            trigger_source="RN" if user.role in {"RN", "NP", "MD"} else "OFFICE",
            commit=True,
        )
    except TrainingModeBlockedError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except AdmissionPrerequisiteError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except ValueError as exc:
        _raise_workflow_http_error(exc)

    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result,
        )

    return result


@router.post("/{patient_id}/complete")
def complete_admission(
    patient_id: UUID,
    payload: CompleteAdmissionRequest,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(
        require_roles(
            [
                "RN",
                "NP",
                "MD",
                "DPCS",
                "ADMIN",
            ]
        )
    ),
):
    patient = get_patient_or_404(
        db,
        patient_id,
        user,
    )

    try:
        admission = AdmissionGuardrailService.get_latest_admission(
            db=db,
            patient=patient,
        )
        readiness = AdmissionGuardrailService.get_admission_readiness(
            patient=patient,
            admission=admission,
        )
    except TrainingModeBlockedError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except AdmissionPrerequisiteError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    return {
        "success": True,
        "deprecated": True,
        "message": "Admission is now triggered by manual SOC datetime. Use /start-soc with soc_datetime.",
        "patient_id": str(patient.id),
        "admission_id": str(admission.id),
        "status": admission.status,
        "ready_for_admission": readiness.ready,
        "blockers": readiness.blockers,
    }


@router.post("/{patient_id}/non-admit")
def mark_non_admit(
    patient_id: UUID,
    payload: NonAdmitRequest,
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
        user,
    )

    try:
        result = AdmissionWorkflowService.mark_non_admit(
            db=db,
            patient=patient,
            changed_by=user.user_id,
            role=user.role,
            reason=payload.reason,
            notes=payload.notes,
        )
    except ValueError as exc:
        _raise_workflow_http_error(exc)

    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result,
        )

    return result