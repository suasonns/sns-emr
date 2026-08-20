from __future__ import annotations

from datetime import datetime
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.patient_access import get_authorized_patient
from app.db_tenant_dependency import get_db_tenant
from app.core.security import get_current_user
from app.services.audit_logger import log_event

from app.models.patient import Patient
from app.services.admission.admission_guardrail_service import (
    AdmissionGuardrailService,
    TrainingModeBlockedError,
    AdmissionPrerequisiteError,
)

router = APIRouter(
    prefix="/admissions",
    tags=["admissions"],
)


# =========================================================
# REQUEST MODELS
# =========================================================

class AuthorizeAdmissionRequest(BaseModel):
    election_signed_at: datetime = Field(
        ...,
        json_schema_extra={"example": "2026-05-29T14:00:00Z"},
    )


class RecordsReleaseRequest(BaseModel):
    records_release_signed_at: datetime = Field(
        ...,
        json_schema_extra={"example": "2026-05-29T12:00:00Z"},
    )


# =========================================================
# HELPERS
# =========================================================

def _resolve_user_id(user):
    return (
        getattr(user, "user_id", None)
        or getattr(user, "id", None)
        or getattr(user, "sub", None)
    )


def _resolve_tenant_id(user):
    tenant_id = getattr(user, "tenant_id", None)
    if not tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Missing tenant context",
        )
    return tenant_id


def _get_patient_or_404(
    *,
    db: Session,
    patient_id: uuid.UUID,
    user,
) -> Patient:
    _resolve_tenant_id(user)
    return get_authorized_patient(db, patient_id, user)


# =========================================================
# ROUTES
# =========================================================

@router.post(
    "/{patient_id}/authorize",
    status_code=status.HTTP_200_OK,
)
def authorize(
    patient_id: uuid.UUID,
    payload: AuthorizeAdmissionRequest,
    db: Session = Depends(get_db_tenant),
    user=Depends(get_current_user),
):
    """
    Record election/consent signature.

    IMPORTANT:
    - This does NOT admit the patient.
    - The system should wait for manual SOC datetime before admission.
    """
    actor_user_id = _resolve_user_id(user)

    if not actor_user_id:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authenticated user identity missing",
        )

    patient = _get_patient_or_404(
        db=db,
        patient_id=patient_id,
        user=user,
    )

    try:
        result = AdmissionGuardrailService.record_election_signed(
            db=db,
            patient=patient,
            election_signed_at=payload.election_signed_at,
            actor_user_id=actor_user_id,
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
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    log_event(
        user_id=actor_user_id,
        role=(getattr(user, "role", "") or "").upper(),
        action="AUTHORIZE_ADMISSION",
        entity_type="patient",
        entity_id=str(patient.id),
        db=db,
    )

    return result


@router.post(
    "/{patient_id}/records-release",
    status_code=status.HTTP_200_OK,
)
def records_release(
    patient_id: uuid.UUID,
    payload: RecordsReleaseRequest,
    db: Session = Depends(get_db_tenant),
    user=Depends(get_current_user),
):
    """
    Record records-release signature.

    IMPORTANT:
    - This does NOT admit the patient.
    - The system should wait for manual SOC datetime before admission.
    """
    actor_user_id = _resolve_user_id(user)

    if not actor_user_id:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authenticated user identity missing",
        )

    patient = _get_patient_or_404(
        db=db,
        patient_id=patient_id,
        user=user,
    )

    try:
        result = AdmissionGuardrailService.record_records_release_signed(
            db=db,
            patient=patient,
            signed_at=payload.records_release_signed_at,
            actor_user_id=actor_user_id,
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
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    log_event(
        user_id=actor_user_id,
        role=(getattr(user, "role", "") or "").upper(),
        action="RECORDS_RELEASE_SIGNED",
        entity_type="patient",
        entity_id=str(patient.id),
        db=db,
    )

    return result