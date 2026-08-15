from __future__ import annotations

from dataclasses import asdict, is_dataclass
from typing import Any, Generator, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.core.security import get_current_user, CurrentUser
from app.models.admission import Admission
from app.models.patient import Patient
from app.services.audit_logger import log_event
from app.services.admission_cloning_service import clone_previous_admission
from app.services.admission_dx_validation_engine import AdmissionDxValidationEngine

# =========================================================
# ROUTER
# =========================================================

router = APIRouter(
    prefix="/admissions",
    tags=["admission-diagnosis"],
)

# =========================================================
# DB DEPENDENCY
# =========================================================


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# =========================================================
# REQUEST / RESPONSE MODELS
# =========================================================

class PrimaryDiagnosisDecisionRequest(BaseModel):
    primary_diagnosis: str = Field(
        ...,
        description="ICD-10 code selected by RN/clinician for the new admission",
        json_schema_extra={"example": "C78.7"},
    )

    is_same_primary_as_previous: bool = Field(
        ...,
        description="True if the new admission primary diagnosis is the same as the previous admission primary diagnosis",
        json_schema_extra={"example": False},
    )


class CloneContextResponse(BaseModel):
    status: str
    patient_id: str
    admission_id: str
    clone_result: dict[str, Any]
    comparison_snapshot: dict[str, Any]
    request_id: str


class DxComparisonResponse(BaseModel):
    status: str
    patient_id: str
    admission_id: str
    comparison_snapshot: dict[str, Any]
    request_id: str


class PrimaryDiagnosisDecisionResponse(BaseModel):
    success: bool
    status: str
    message: str
    previous_primary: Optional[dict[str, Any]] = None
    new_primary: Optional[dict[str, Any]] = None
    actions: list[str] = Field(default_factory=list)
    admission_id: str
    patient_id: str
    request_id: str


# =========================================================
# HELPERS
# =========================================================

ALLOWED_DECISION_ROLES = {
    "RN",
    "NP",
    "MD",
    "DPCS",
    "ADMIN",
}


def _get_request_id(request: Request, response: Optional[Response] = None) -> str:
    existing = (
        getattr(request.state, "request_id", None)
        or request.headers.get("X-Request-ID")
    )
    request_id = str(existing or UUID(int=0).hex) if existing else str(__import__("uuid").uuid4())
    request.state.request_id = request_id

    if response is not None:
        response.headers["X-Request-ID"] = request_id

    return request_id


def _resolve_user_id(user: CurrentUser) -> UUID:
    candidate = (
        getattr(user, "user_id", None)
        or getattr(user, "id", None)
    )
    if not candidate:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authenticated user identity missing",
        )
    return candidate


def _resolve_tenant_id(user: CurrentUser) -> UUID:
    tenant_id = getattr(user, "tenant_id", None)
    if not tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Missing tenant context",
        )
    return tenant_id


def _set_db_context(
    db: Session,
    *,
    tenant_id: UUID,
    user_id: UUID,
    request_id: str,
) -> None:
    db.info["tenant_id"] = tenant_id
    db.info["user_id"] = user_id
    db.info["request_id"] = request_id


def _safe_log_event(
    *,
    db: Session,
    user_id: UUID,
    action: str,
    entity_type: str,
    entity_id: UUID,
    request_id: str,
    metadata: Optional[dict[str, Any]] = None,
) -> None:
    try:
        log_event(
            db=db,
            user_id=str(user_id),
            role="SYSTEM",
            action=action,
            entity_type=entity_type,
            entity_id=str(entity_id),
            commit=False,
        )
    except Exception:
        # Do not block workflow on audit failure
        pass


def _get_admission_or_404(
    *,
    db: Session,
    admission_id: UUID,
    current_user: CurrentUser,
) -> Admission:
    tenant_id = _resolve_tenant_id(current_user)

    admission = (
        db.query(Admission)
        .filter(
            Admission.id == admission_id,
            Admission.tenant_id == tenant_id,
        )
        .first()
    )

    if not admission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Admission not found",
        )

    return admission


def _get_patient_for_admission_or_404(
    *,
    db: Session,
    admission: Admission,
) -> Patient:
    patient = (
        db.query(Patient)
        .filter(Patient.id == admission.patient_id)
        .first()
    )

    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found for admission",
        )

    return patient


def _normalize_dataclass_result(value: Any) -> dict[str, Any]:
    if is_dataclass(value):
        return asdict(value)
    if isinstance(value, dict):
        return value
    return {"value": value}


# =========================================================
# ROUTES
# =========================================================

@router.post(
    "/{admission_id}/clone-context",
    response_model=CloneContextResponse,
    status_code=status.HTTP_200_OK,
)
def clone_admission_context(
    admission_id: UUID,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """
    Clone previous admission context into the new admission.

    WHAT IT DOES
    ------------
    - copies secondary diagnoses
    - copies comorbidities
    - preserves previous primary as comparison only
    - returns comparison snapshot for RN review
    """
    request_id = _get_request_id(request, response)
    user_id = _resolve_user_id(current_user)

    admission = _get_admission_or_404(
        db=db,
        admission_id=admission_id,
        current_user=current_user,
    )
    patient = _get_patient_for_admission_or_404(
        db=db,
        admission=admission,
    )

    _set_db_context(
        db=db,
        tenant_id=admission.tenant_id,
        user_id=user_id,
        request_id=request_id,
    )

    try:
        clone_result = clone_previous_admission(
            db=db,
            patient_id=patient.id,
            new_admission=admission,
            user_id=user_id,
        )

        comparison_snapshot = AdmissionDxValidationEngine.build_comparison_snapshot(
            db=db,
            patient=patient,
            new_admission=admission,
        )

        _safe_log_event(
            db=db,
            user_id=user_id,
            action="CLONE_ADMISSION_CONTEXT",
            entity_type="admission",
            entity_id=admission.id,
            request_id=request_id,
            metadata={
                "patient_id": str(patient.id),
            },
        )

        db.commit()

    except HTTPException:
        db.rollback()
        raise
    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Admission context clone failed: {exc}",
        )

    return CloneContextResponse(
        status="ok",
        patient_id=str(patient.id),
        admission_id=str(admission.id),
        clone_result=clone_result,
        comparison_snapshot=comparison_snapshot,
        request_id=request_id,
    )


@router.get(
    "/{admission_id}/dx-comparison",
    response_model=DxComparisonResponse,
    status_code=status.HTTP_200_OK,
)
def get_admission_dx_comparison(
    admission_id: UUID,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """
    Return comparison snapshot for the admission.

    WHAT IT RETURNS
    ---------------
    - previous primary diagnosis
    - carried secondary diagnoses
    - carried comorbidities
    - previous labs
    - previous H&P
    - flag indicating RN must still choose primary dx
    """
    request_id = _get_request_id(request, response)
    user_id = _resolve_user_id(current_user)

    admission = _get_admission_or_404(
        db=db,
        admission_id=admission_id,
        current_user=current_user,
    )
    patient = _get_patient_for_admission_or_404(
        db=db,
        admission=admission,
    )

    _set_db_context(
        db=db,
        tenant_id=admission.tenant_id,
        user_id=user_id,
        request_id=request_id,
    )

    try:
        comparison_snapshot = AdmissionDxValidationEngine.build_comparison_snapshot(
            db=db,
            patient=patient,
            new_admission=admission,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Diagnosis comparison load failed: {exc}",
        )

    return DxComparisonResponse(
        status="ok",
        patient_id=str(patient.id),
        admission_id=str(admission.id),
        comparison_snapshot=comparison_snapshot,
        request_id=request_id,
    )


@router.post(
    "/{admission_id}/primary-diagnosis-decision",
    response_model=PrimaryDiagnosisDecisionResponse,
    status_code=status.HTTP_200_OK,
)
def decide_primary_diagnosis(
    admission_id: UUID,
    payload: PrimaryDiagnosisDecisionRequest,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """
    RN/clinician confirms whether the new admission primary diagnosis
    is the same as previous, or changed.

    BEHAVIOR
    --------
    - same primary => confirm previous primary as new primary
    - changed primary => create new primary and move old primary to secondary
    """
    request_id = _get_request_id(request, response)
    user_id = _resolve_user_id(current_user)

    actor_role = str(getattr(current_user, "role", "SYSTEM")).strip().upper()
    if actor_role not in ALLOWED_DECISION_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only clinical or authorized admission roles may decide primary diagnosis.",
        )

    admission = _get_admission_or_404(
        db=db,
        admission_id=admission_id,
        current_user=current_user,
    )
    patient = _get_patient_for_admission_or_404(
        db=db,
        admission=admission,
    )

    _set_db_context(
        db=db,
        tenant_id=admission.tenant_id,
        user_id=user_id,
        request_id=request_id,
    )

    try:
        decision = AdmissionDxValidationEngine.validate_and_apply_primary_decision(
            db=db,
            patient=patient,
            new_admission=admission,
            user_id=user_id,
            primary_diagnosis=payload.primary_diagnosis,
            is_same_primary_as_previous=payload.is_same_primary_as_previous,
        )

        decision_payload = _normalize_dataclass_result(decision)

        _safe_log_event(
            db=db,
            user_id=user_id,
            action="PRIMARY_DIAGNOSIS_DECISION",
            entity_type="admission",
            entity_id=admission.id,
            request_id=request_id,
            metadata={
                "patient_id": str(patient.id),
                "actor_role": actor_role,
                "primary_diagnosis": payload.primary_diagnosis,
                "is_same_primary_as_previous": payload.is_same_primary_as_previous,
                "decision_status": decision_payload.get("status"),
            },
        )

        db.commit()

    except HTTPException:
        db.rollback()
        raise
    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Primary diagnosis decision failed: {exc}",
        )

    return PrimaryDiagnosisDecisionResponse(
        success=bool(decision_payload.get("success")),
        status=str(decision_payload.get("status")),
        message=str(decision_payload.get("message")),
        previous_primary=decision_payload.get("previous_primary"),
        new_primary=decision_payload.get("new_primary"),
        actions=decision_payload.get("actions", []),
        admission_id=str(admission.id),
        patient_id=str(patient.id),
        request_id=request_id,
    )


# =========================================================
# Pydantic model rebuild
# =========================================================

PrimaryDiagnosisDecisionRequest.model_rebuild()
CloneContextResponse.model_rebuild()
DxComparisonResponse.model_rebuild()
PrimaryDiagnosisDecisionResponse.model_rebuild()