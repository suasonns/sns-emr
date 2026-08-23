# app/api/routes/plan_of_care.py

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.patient_access import get_authorized_patient
from app.core.security import get_current_user
from app.db_tenant_dependency import get_db_tenant
from app.models.plan_of_care import PlanOfCare
from app.models.plan_of_care_version import PlanOfCareVersion
from app.services.poc_service import (
    create_plan_of_care as create_plan_of_care_service,
    create_new_version as create_new_poc_version_service,
    get_active_plan_of_care_version,
    get_current_plan_of_care_version_for_patient,
)

router = APIRouter(
    prefix="/plan-of-care",
    tags=["plan-of-care"],
)


# =========================================================
# DEPENDENCY WRAPPERS
# =========================================================

def get_db_with_request_state(
    db: Session = Depends(get_db_tenant),
):
    yield db


def require_tenant_user(user=Depends(get_current_user)):
    from app.core.roles import is_platform_role

    if (
        is_platform_role(getattr(user, "role", None))
        or getattr(user, "is_superuser", False)
        or getattr(user, "is_management", False)
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tenant-scoped endpoint not allowed for system accounts",
        )
    return user


def _tenant_id_uuid(user) -> uuid.UUID:
    if not getattr(user, "tenant_id", None):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing tenant",
        )
    return uuid.UUID(str(user.tenant_id))


def _user_id_uuid(user) -> uuid.UUID:
    raw_user_id = (
        getattr(user, "user_id", None)
        or getattr(user, "id", None)
        or getattr(user, "sub", None)
    )
    if not raw_user_id:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Invalid user identity",
        )
    return uuid.UUID(str(raw_user_id))


# =========================================================
# V2 REQUEST / RESPONSE MODELS
# =========================================================

class POCInterventionIn(BaseModel):
    discipline: str
    intervention_text: str
    frequency: Optional[str] = None
    instructions: Optional[str] = None
    source_kind: str = "RULE_GENERATED"
    status: str = "ACTIVE"
    sort_order: Optional[int] = None


class POCGoalIn(BaseModel):
    goal_text: str
    measurable_outcome: Optional[str] = None
    target_timeframe: Optional[str] = None
    source_kind: str = "RULE_GENERATED"
    status: str = "ACTIVE"
    sort_order: Optional[int] = None
    interventions: list[POCInterventionIn] = Field(default_factory=list)


class POCProblemIn(BaseModel):
    problem_code: str
    label: str
    description: Optional[str] = None
    severity: str = "UNKNOWN"
    source_diagnosis_code: Optional[str] = None
    source_condition: Optional[str] = None
    diagnosis_context: str = "MANUAL"
    rule_key: Optional[str] = None
    source_kind: str = "RULE_GENERATED"
    status: str = "ACTIVE"
    sort_order: Optional[int] = None
    goals: list[POCGoalIn] = Field(default_factory=list)


class POCContentIn(BaseModel):
    problems: list[POCProblemIn] = Field(default_factory=list)


class CreatePlanOfCareV2Request(BaseModel):
    admission_id: UUID
    patient_id: UUID
    source_kind: str = "ICA"
    change_reason: Optional[str] = "Initial POC creation"
    generated_from: Optional[dict[str, Any]] = None
    create_physician_attestation: bool = False
    poc_content: POCContentIn


class UpdatePlanOfCareV2Request(BaseModel):
    source_kind: str
    change_reason: Optional[str] = None
    generated_from: Optional[dict[str, Any]] = None
    reviewed_in_idg: bool = False
    idg_review_id: Optional[UUID] = None
    create_physician_attestation: bool = False
    poc_content: POCContentIn


class CreatePlanOfCareResponse(BaseModel):
    status: str
    plan_of_care_id: UUID


class UpdatePlanOfCareV2Response(BaseModel):
    status: str
    plan_of_care_id: UUID
    version_id: UUID
    version_number: int


class CurrentPlanOfCareVersionResponse(BaseModel):
    version_id: UUID
    version_number: int
    status: str
    source_kind: str
    change_reason: Optional[str] = None
    generated_from: Optional[dict[str, Any]] = None
    reviewed_in_idg: bool
    idg_review_id: Optional[UUID] = None
    poc_content: POCContentIn


class CurrentPlanOfCareResponse(BaseModel):
    plan_of_care_id: UUID
    patient_id: UUID
    admission_id: UUID
    tenant_id: UUID
    status: str
    current_version_id: UUID
    current_version: CurrentPlanOfCareVersionResponse


class PlanOfCareVersionSummaryResponse(BaseModel):
    version_id: UUID
    version_number: int
    status: str
    source_kind: str
    change_reason: Optional[str] = None
    based_on_version_id: Optional[UUID] = None
    reviewed_in_idg: bool
    idg_review_id: Optional[UUID] = None
    created_at: Optional[datetime] = None


# =========================================================
# INTERNAL HELPERS
# =========================================================

def _create_poc_or_raise_http(
    *,
    db: Session,
    tenant_id: UUID,
    patient_id: UUID,
    admission_id: UUID,
    created_by_user_id: UUID,
    poc_content: dict[str, Any],
    source_kind: str = "ICA",
    change_reason: Optional[str] = "Initial POC creation",
    generated_from: Optional[dict[str, Any]] = None,
    create_physician_attestation: bool = False,
):
    try:
        return create_plan_of_care_service(
            db=db,
            tenant_id=tenant_id,
            patient_id=patient_id,
            admission_id=admission_id,
            created_by_user_id=created_by_user_id,
            poc_content=poc_content,
            source_kind=source_kind,
            change_reason=change_reason,
            generated_from=generated_from,
            create_physician_attestation=create_physician_attestation,
        )
    except ValueError as e:
        message = str(e)

        if message == "Plan of Care already exists for this admission in this tenant":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=message,
            )

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message,
        )
    except IntegrityError as e:
        raw_message = str(e.orig)

        if "fk_poc_admission" in raw_message:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid admission_id: admission does not exist",
            )

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Database integrity error while creating Plan of Care",
        )


def _create_poc_version_or_raise_http(
    *,
    db: Session,
    plan_of_care_id: UUID,
    tenant_id: UUID,
    user_id: UUID,
    updated_content: dict[str, Any],
    source_kind: str,
    change_reason: Optional[str] = None,
    generated_from: Optional[dict[str, Any]] = None,
    reviewed_in_idg: bool = False,
    idg_review_id: Optional[UUID] = None,
    create_physician_attestation: bool = False,
):
    try:
        return create_new_poc_version_service(
            db=db,
            plan_of_care_id=plan_of_care_id,
            tenant_id=tenant_id,
            updated_content=updated_content,
            user_id=user_id,
            source_kind=source_kind,
            change_reason=change_reason,
            generated_from=generated_from,
            reviewed_in_idg=reviewed_in_idg,
            idg_review_id=idg_review_id,
            create_physician_attestation=create_physician_attestation,
        )
    except ValueError as e:
        message = str(e)

        if message == "Plan of Care not found in tenant":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=message,
            )

        if message == "Current version not found":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=message,
            )

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message,
        )


# =========================================================
# V2 CREATE ENDPOINT
# =========================================================

@router.post(
    "/",
    response_model=CreatePlanOfCareResponse,
    status_code=status.HTTP_200_OK,
)
def create_plan_of_care_v2(
    payload: CreatePlanOfCareV2Request,
    db: Session = Depends(get_db_with_request_state),
    user=Depends(require_tenant_user),
) -> CreatePlanOfCareResponse:
    """
    Clean v2 endpoint:
    - one request body
    - one source of truth
    - nested poc_content only
    """
    tenant_id = _tenant_id_uuid(user)
    user_id = _user_id_uuid(user)
    get_authorized_patient(db, payload.patient_id, user)

    poc = _create_poc_or_raise_http(
        db=db,
        tenant_id=tenant_id,
        patient_id=payload.patient_id,
        admission_id=payload.admission_id,
        created_by_user_id=user_id,
        poc_content=payload.poc_content.model_dump(exclude_none=True),
        source_kind=payload.source_kind,
        change_reason=payload.change_reason,
        generated_from=payload.generated_from,
        create_physician_attestation=payload.create_physician_attestation,
    )

    return CreatePlanOfCareResponse(
        status="success",
        plan_of_care_id=poc.id,
    )


# =========================================================
# V2 VERSION CREATE ENDPOINT
# =========================================================

@router.post(
    "/{plan_of_care_id}/versions/",
    response_model=UpdatePlanOfCareV2Response,
    status_code=status.HTTP_200_OK,
)
def create_plan_of_care_version_v2(
    plan_of_care_id: UUID,
    payload: UpdatePlanOfCareV2Request,
    db: Session = Depends(get_db_with_request_state),
    user=Depends(require_tenant_user),
) -> UpdatePlanOfCareV2Response:
    """
    Create a new Plan of Care version under an existing root PlanOfCare.
    """
    tenant_id = _tenant_id_uuid(user)
    user_id = _user_id_uuid(user)
    poc = (
        db.query(PlanOfCare)
        .filter(
            PlanOfCare.id == plan_of_care_id,
            PlanOfCare.tenant_id == tenant_id,
        )
        .first()
    )
    if not poc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Plan of Care not found in tenant",
        )
    get_authorized_patient(db, poc.patient_id, user)

    version = _create_poc_version_or_raise_http(
        db=db,
        plan_of_care_id=plan_of_care_id,
        tenant_id=tenant_id,
        user_id=user_id,
        updated_content=payload.poc_content.model_dump(exclude_none=True),
        source_kind=payload.source_kind,
        change_reason=payload.change_reason,
        generated_from=payload.generated_from,
        reviewed_in_idg=payload.reviewed_in_idg,
        idg_review_id=payload.idg_review_id,
        create_physician_attestation=payload.create_physician_attestation,
    )

    return UpdatePlanOfCareV2Response(
        status="success",
        plan_of_care_id=version.plan_of_care_id,
        version_id=version.id,
        version_number=version.version_number,
    )


# =========================================================
# GET CURRENT POC WITH NESTED STRUCTURE
# =========================================================

@router.get(
    "/{plan_of_care_id}/current/",
    response_model=CurrentPlanOfCareResponse,
    status_code=status.HTTP_200_OK,
)
def get_current_plan_of_care_v2(
    plan_of_care_id: UUID,
    db: Session = Depends(get_db_with_request_state),
    user=Depends(require_tenant_user),
) -> CurrentPlanOfCareResponse:
    """
    Return the current active PlanOfCare version and its nested poc_content snapshot.
    """
    tenant_id = _tenant_id_uuid(user)

    poc = (
        db.query(PlanOfCare)
        .filter(
            PlanOfCare.id == plan_of_care_id,
            PlanOfCare.tenant_id == tenant_id,
        )
        .first()
    )

    if not poc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Plan of Care not found in tenant",
        )

    get_authorized_patient(db, poc.patient_id, user)

    version = get_active_plan_of_care_version(
        db,
        tenant_id=tenant_id,
        plan_of_care_id=poc.id,
    )

    if not version:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Current Plan of Care version not found",
        )

    snapshot = version.snapshot_json or {}
    if not isinstance(snapshot, dict):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Current Plan of Care snapshot is invalid",
        )

    return CurrentPlanOfCareResponse(
        plan_of_care_id=poc.id,
        patient_id=poc.patient_id,
        admission_id=poc.admission_id,
        tenant_id=poc.tenant_id,
        status=poc.status,
        current_version_id=version.id,
        current_version=CurrentPlanOfCareVersionResponse(
            version_id=version.id,
            version_number=version.version_number,
            status=version.status,
            source_kind=version.source_kind,
            change_reason=version.change_reason,
            generated_from=version.generated_from,
            reviewed_in_idg=version.reviewed_in_idg,
            idg_review_id=version.idg_review_id,
            poc_content=POCContentIn.model_validate(snapshot),
        ),
    )



# =========================================================
# GET CURRENT POC BY PATIENT (convenience lookup — no plan_of_care_id needed)
# =========================================================

@router.get(
    "/by-patient/{patient_id}/current/",
    response_model=CurrentPlanOfCareResponse,
    status_code=status.HTTP_200_OK,
)
def get_current_plan_of_care_by_patient_v2(
    patient_id: UUID,
    db: Session = Depends(get_db_with_request_state),
    user=Depends(require_tenant_user),
) -> CurrentPlanOfCareResponse:
    """
    Convenience lookup so the frontend can resolve a patient's active
    Plan of Care and current version without already knowing the
    plan_of_care_id (e.g. from RN ICA or the patient chart).
    """
    tenant_id = _tenant_id_uuid(user)
    get_authorized_patient(db, patient_id, user)

    poc = (
        db.query(PlanOfCare)
        .filter(
            PlanOfCare.tenant_id == tenant_id,
            PlanOfCare.patient_id == patient_id,
        )
        .order_by(PlanOfCare.created_at.desc())
        .first()
    )

    if not poc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No Plan of Care found for this patient",
        )

    version = get_active_plan_of_care_version(
        db,
        tenant_id=tenant_id,
        plan_of_care_id=poc.id,
    )

    if not version:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Current Plan of Care version not found",
        )

    snapshot = version.snapshot_json or {}
    if not isinstance(snapshot, dict):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Current Plan of Care snapshot is invalid",
        )

    return CurrentPlanOfCareResponse(
        plan_of_care_id=poc.id,
        patient_id=poc.patient_id,
        admission_id=poc.admission_id,
        tenant_id=poc.tenant_id,
        status=poc.status,
        current_version_id=version.id,
        current_version=CurrentPlanOfCareVersionResponse(
            version_id=version.id,
            version_number=version.version_number,
            status=version.status,
            source_kind=version.source_kind,
            change_reason=version.change_reason,
            generated_from=version.generated_from,
            reviewed_in_idg=version.reviewed_in_idg,
            idg_review_id=version.idg_review_id,
            poc_content=POCContentIn.model_validate(snapshot),
        ),
    )


# =========================================================
# GET MASTER POC REVIEW BY PATIENT (IDG-facing synchronized
# read view of every RN-ICA-sourced problem, any originating
# section, for the patient's current active Plan of Care
# version — moved here from RN ICA finalization per product
# direction: "Master POC Review belongs in IDG, not RN ICA".)
# =========================================================

@router.get(
    "/by-patient/{patient_id}/problems/",
    status_code=status.HTTP_200_OK,
)
def get_master_poc_review_by_patient(
    patient_id: UUID,
    db: Session = Depends(get_db_with_request_state),
    user=Depends(require_tenant_user),
):
    from app.services import rnica_poc_adapter

    tenant_id = _tenant_id_uuid(user)
    get_authorized_patient(db, patient_id, user)

    problems = rnica_poc_adapter.list_all_problems(
        db,
        tenant_id=tenant_id,
        patient_id=patient_id,
    )
    return {"patientId": str(patient_id), "problems": problems}


# =========================================================
# GET VERSION HISTORY
# =========================================================

@router.get(
    "/{plan_of_care_id}/versions/",
    response_model=list[PlanOfCareVersionSummaryResponse],
    status_code=status.HTTP_200_OK,
)
def get_plan_of_care_versions_v2(
    plan_of_care_id: UUID,
    db: Session = Depends(get_db_with_request_state),
    user=Depends(require_tenant_user),
) -> list[PlanOfCareVersionSummaryResponse]:
    """
    Return all PlanOfCare versions in ascending version order.
    """

    # ✅ FIX: correct tenant extraction
    tenant_id = _tenant_id_uuid(user)

    # ✅ Validate POC exists in tenant
    poc = (
        db.query(PlanOfCare)
        .filter(
            PlanOfCare.id == plan_of_care_id,
            PlanOfCare.tenant_id == tenant_id,
        )
        .first()
    )

    if not poc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Plan of Care not found in tenant",
        )

    get_authorized_patient(db, poc.patient_id, user)

    # ✅ Fetch versions
    versions = (
        db.query(PlanOfCareVersion)
        .filter(
            PlanOfCareVersion.plan_of_care_id == plan_of_care_id,
            PlanOfCareVersion.tenant_id == tenant_id,
        )
        .order_by(PlanOfCareVersion.version_number.asc())
        .all()
    )

    # ✅ Return response
    return [
        PlanOfCareVersionSummaryResponse(
            version_id=v.id,
            version_number=v.version_number,
            status=v.status,
            source_kind=v.source_kind,
            change_reason=v.change_reason,
            based_on_version_id=v.based_on_version_id,
            reviewed_in_idg=v.reviewed_in_idg,
            idg_review_id=v.idg_review_id,
            created_at=v.created_at,
        )
        for v in versions
    ]


# =========================================================
# GET SPECIFIC VERSION
# =========================================================

@router.get(
    "/{plan_of_care_id}/versions/{version_id}",
    response_model=CurrentPlanOfCareVersionResponse,
    status_code=status.HTTP_200_OK,
)
def get_plan_of_care_version_by_id_v2(
    plan_of_care_id: UUID,
    version_id: UUID,
    db: Session = Depends(get_db_with_request_state),
    user=Depends(require_tenant_user),
) -> CurrentPlanOfCareVersionResponse:
    """
    Return a specific PlanOfCare version snapshot.
    """
    tenant_id = _tenant_id_uuid(user)

    version = (
        db.query(PlanOfCareVersion)
        .filter(
            PlanOfCareVersion.id == version_id,
            PlanOfCareVersion.plan_of_care_id == plan_of_care_id,
            PlanOfCareVersion.tenant_id == tenant_id,
        )
        .first()
    )

    if not version:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Plan of Care version not found",
        )

    poc = (
        db.query(PlanOfCare)
        .filter(
            PlanOfCare.id == plan_of_care_id,
            PlanOfCare.tenant_id == tenant_id,
        )
        .first()
    )
    if not poc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Plan of Care not found in tenant",
        )
    get_authorized_patient(db, poc.patient_id, user)

    snapshot = version.snapshot_json or {}
    if not isinstance(snapshot, dict):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Plan of Care version snapshot is invalid",
        )

    return CurrentPlanOfCareVersionResponse(
        version_id=version.id,
        version_number=version.version_number,
        status=version.status,
        source_kind=version.source_kind,
        change_reason=version.change_reason,
        generated_from=version.generated_from,
        reviewed_in_idg=version.reviewed_in_idg,
        idg_review_id=version.idg_review_id,
        poc_content=POCContentIn.model_validate(snapshot),
    )