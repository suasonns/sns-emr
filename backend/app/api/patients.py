# =========================================================
# ENTERPRISE PATIENTS ROUTER (FULL PRESERVED + FIXED)
# =========================================================

from __future__ import annotations

import uuid
import re
from datetime import date, datetime, timedelta, timezone
from typing import Generator

from fastapi import APIRouter, Depends, HTTPException, Request, status, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func, text

from app.core.security import get_current_user
from app.db_tenant_dependency import get_db_tenant

from app.models.patient import Patient
from app.models.user import User
from app.models.patient_assignment import PatientAssignment
from app.models.patient_facesheet import PatientFaceSheet
from app.models.task import Task
from app.models.visit import Visit
from app.models.patient_diagnosis import PatientDiagnosis

from app.models.enums import (
    DiagnosisType,
    DiagnosisStatus,
    DiagnosisSource,
)
from app.models.enums import (
    TaskStatus,
    TaskOrigin,
    TaskType,
    TaskDiscipline,
    TaskRegulatoryBasis,
)

from app.services.icd10_resolver_service import (
    ICD10ResolutionError,
    resolve_icd10_diagnosis_for_use,
)
from app.services.diagnosis_sync_service import (
    sync_official_primary_diagnosis,
)
from enum import Enum


class PatientCategory(str, Enum):
    ACTIVE = "ACTIVE"
    PENDING = "PENDING"
    PROSPECTIVE = "PROSPECTIVE"
    NON_ADMITS = "NON_ADMITS"
    DISCHARGED_30 = "DISCHARGED_30"
    DISCHARGED_ALL = "DISCHARGED_ALL"
    ALL = "ALL"


# =========================================================
# DB WRAPPER
# =========================================================

def get_db_with_request_state(
    request: Request,
    db: Session = Depends(get_db_tenant),
) -> Generator[Session, None, None]:
    request.state.db = db
    yield db


# =========================================================
# AUTH
# =========================================================

def require_tenant_user(user=Depends(get_current_user)):
    if getattr(user, "is_superuser", False) or getattr(user, "is_management", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tenant-scoped endpoint not allowed for system accounts",
        )
    return user


def _tenant_id_uuid(user) -> uuid.UUID:
    if not getattr(user, "tenant_id", None):
        raise HTTPException(401, "Missing tenant")
    return uuid.UUID(str(user.tenant_id))


# =========================================================
# ROUTER
# =========================================================

router = APIRouter(prefix="/patients", tags=["patients"])


# =========================================================
# SCHEMAS ✅ FIXED (MRN REMOVED)
# =========================================================

class PatientCreate(BaseModel):
    first_name: str
    middle_name: str | None = None
    last_name: str
    date_of_birth: date
    primary_diagnosis: str


class PatientUpdate(BaseModel):
    full_name: str | None = None
    primary_diagnosis: str | None = None
    status: str | None = None

    admission_status: str | None = None

    discharge_reason: str | None = None
    discharge_initiated_by: str | None = None
    discharge_plan_reviewed: bool | None = None

    discharge_notified: bool | None = None
    discharge_explained: bool | None = None
    discharge_readmission_explained: bool | None = None
    discharge_medication_instruction: bool | None = None
    discharge_contact_provided: bool | None = None
    discharge_referral_provided: bool | None = None


# =========================================================
# LIST PATIENTS ✅ UNCHANGED
# =========================================================

@router.get("/")
def list_patients(
    category: PatientCategory = Query(PatientCategory.ACTIVE),
    db: Session = Depends(get_db_with_request_state),
    user=Depends(require_tenant_user),
):
    tenant_id = _tenant_id_uuid(user)

    db_user = db.query(User).filter(User.id == user.user_id).first()
    if not db_user or not db_user.active:
        raise HTTPException(403, "Inactive or missing user")

    access_level = db_user.access_level or "ROLE_BASED"
    
    # -----------------------------------------------------
    # Discipline-restricted roles
    # -----------------------------------------------------
    # CHHA and Volunteer users must not enumerate
    # patient lists from the patient registry endpoint.
    # They must access patient information through
    # assigned workflow-specific routes only.
    if user.role in {
        "CHHA",
        "VOLUNTEER",
    }:
        raise HTTPException(
            status_code=403,
            detail="User is not authorized to list patients",
        )
    
    query = db.query(Patient).filter(
        Patient.tenant_id == tenant_id
    )

    FULL_ACCESS_ROLES = {"ADMIN", "DPCS", "MD"}

    if not (
        user.role in FULL_ACCESS_ROLES
        or access_level == "FULL_ACCESS"
    ):
        query = (
            query.join(
                PatientAssignment,
                Patient.id == PatientAssignment.patient_id
            )
            .filter(
                PatientAssignment.tenant_id == tenant_id,
                PatientAssignment.user_id == user.user_id,
            )
            .distinct()
        )

    if category == "ACTIVE":
        query = query.filter(
            Patient.admission_status == "ADMITTED"
        )

    elif category == "PENDING":
        query = query.filter(
            Patient.admission_status == "PENDING"
        )

    elif category == "PROSPECTIVE":
        query = query.filter(
            Patient.admission_status.in_(["PRE_REFERRAL", "PROSPECT"])
        )

    elif category == "NON_ADMITS":
        query = query.filter(
            Patient.not_admitted_at.isnot(None)
        )

    elif category == "DISCHARGED_30":
        query = query.filter(
            Patient.discharge_date.isnot(None),
            Patient.discharge_date >= func.current_date() - text("INTERVAL '30 days'")
        )

    elif category == "DISCHARGED_ALL":
        query = query.filter(
            Patient.discharge_date.isnot(None)
        )

    elif category == "ALL":
        pass

    else:
        raise HTTPException(400, f"Invalid category: {category}")

    return query.order_by(Patient.full_name).all()

def _clean_name_part(value: str | None) -> str | None:
    if value is None:
        return None

    cleaned = str(value).strip()

    if not cleaned:
        return None

    return cleaned


def _compose_full_name_for_patient(
    *,
    first_name: str,
    middle_name: str | None,
    last_name: str,
) -> tuple[str, str | None, str, str]:
    """
    Build Patient.full_name from structured name fields.

    Database compatibility:
    - patients table still stores full_name
    - patient_facesheet stores first_name / middle_name / last_name

    API governance:
    - New patient creation must accept structured names
    - full_name becomes an internal compatibility field only
    """

    cleaned_first = _clean_name_part(first_name)
    cleaned_middle = _clean_name_part(middle_name)
    cleaned_last = _clean_name_part(last_name)

    if not cleaned_first:
        raise HTTPException(
            status_code=400,
            detail="first_name is required",
        )

    if not cleaned_last:
        raise HTTPException(
            status_code=400,
            detail="last_name is required",
        )

    parts = [
        cleaned_first,
        cleaned_middle,
        cleaned_last,
    ]

    full_name = " ".join(
        part for part in parts if part
    )

    return cleaned_first, cleaned_middle, cleaned_last, full_name

def _parse_primary_diagnosis_input(
    db: Session,
    value: str,
) -> tuple[str, str, str]:
    """
    Resolve referral primary diagnosis through ICD10 SSOT.

    Accepts:
        I50.84
        End stage heart failure
        End stage heart failure (I50.84)

    Uses:
        icd10_master
        icd10_hospice_policy

    Returns:
        icd10_code
        diagnosis_description
        display_name
    """

    try:
        resolved = resolve_icd10_diagnosis_for_use(
            db,
            diagnosis_input=value,
            diagnosis_role="PRIMARY",
            workflow_context="REFERRAL",
        )

    except ICD10ResolutionError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    return (
        resolved.icd10_code,
        resolved.diagnosis_description,
        resolved.display_name,
    )

def _enum_value(value):
    if value is None:
        return None

    if hasattr(value, "value"):
        return value.value

    return str(value)

def _diagnosis_to_payload(
    diagnosis: PatientDiagnosis | None,
) -> dict | None:
    if diagnosis is None:
        return None

    return {
        "id": str(diagnosis.id),
        "diagnosis_type": _enum_value(diagnosis.diagnosis_type),
        "status": _enum_value(diagnosis.status),
        "source": _enum_value(diagnosis.source),
        "icd10_code": diagnosis.icd10_code,
        "diagnosis_description": diagnosis.diagnosis_description,
        "display_name": diagnosis.display_name,
        "active": diagnosis.active,
        "is_terminal": diagnosis.is_terminal,
        "is_related_to_terminal": diagnosis.is_related_to_terminal,
        "effective_date": diagnosis.effective_date,
        "resolved_date": diagnosis.resolved_date,
        "effective_benefit_period_number": (
            diagnosis.effective_benefit_period_number
        ),
        "resolved_benefit_period_number": (
            diagnosis.resolved_benefit_period_number
        ),
        "idg_discussion_required": (
            diagnosis.idg_discussion_required
        ),
        "idg_discussed": diagnosis.idg_discussed,
        "idg_discussed_at": diagnosis.idg_discussed_at,
        "idg_meeting_id": (
            str(diagnosis.idg_meeting_id)
            if diagnosis.idg_meeting_id
            else None
        ),
        "idg_summary": diagnosis.idg_summary,
        "hospital_records_reviewed": (
            diagnosis.hospital_records_reviewed
        ),
        "diagnostic_results_reviewed": (
            diagnosis.diagnostic_results_reviewed
        ),
        "specialist_documentation_reviewed": (
            diagnosis.specialist_documentation_reviewed
        ),
        "specialist_name": diagnosis.specialist_name,
        "specialist_documentation_date": (
            diagnosis.specialist_documentation_date
        ),
        "prior_specialist_certification_present": (
            diagnosis.prior_specialist_certification_present
        ),
        "supporting_evidence_summary": (
            diagnosis.supporting_evidence_summary
        ),
        "physician_signed_document_type": (
            diagnosis.physician_signed_document_type
        ),
        "physician_signed_document_id": (
            str(diagnosis.physician_signed_document_id)
            if diagnosis.physician_signed_document_id
            else None
        ),
        "physician_signed_at": diagnosis.physician_signed_at,
        "physician_signature_notes": (
            diagnosis.physician_signature_notes
        ),
        "change_reason": diagnosis.change_reason,
        "rejected_reason": diagnosis.rejected_reason,
        "notes": diagnosis.notes,
        "created_at": diagnosis.created_at,
        "updated_at": diagnosis.updated_at,
    }


def _get_active_primary_diagnosis(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    patient_id: uuid.UUID,
) -> PatientDiagnosis | None:
    return (
        db.query(PatientDiagnosis)
        .filter(
            PatientDiagnosis.tenant_id == tenant_id,
            PatientDiagnosis.patient_id == patient_id,
            PatientDiagnosis.diagnosis_type == DiagnosisType.PRIMARY,
            PatientDiagnosis.status == DiagnosisStatus.ACTIVE,
            PatientDiagnosis.active.is_(True),
            PatientDiagnosis.resolved_date.is_(None),
        )
        .order_by(PatientDiagnosis.created_at.desc())
        .first()
    )


def _get_active_diagnoses_by_type(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    patient_id: uuid.UUID,
    diagnosis_type: DiagnosisType,
) -> list[PatientDiagnosis]:
    return (
        db.query(PatientDiagnosis)
        .filter(
            PatientDiagnosis.tenant_id == tenant_id,
            PatientDiagnosis.patient_id == patient_id,
            PatientDiagnosis.diagnosis_type == diagnosis_type,
            PatientDiagnosis.status == DiagnosisStatus.ACTIVE,
            PatientDiagnosis.active.is_(True),
            PatientDiagnosis.resolved_date.is_(None),
        )
        .order_by(PatientDiagnosis.created_at.asc())
        .all()
    )


def _get_diagnosis_summary_payload(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    patient_id: uuid.UUID,
) -> dict:
    active_primary = _get_active_primary_diagnosis(
        db,
        tenant_id=tenant_id,
        patient_id=patient_id,
    )

    active_secondary = _get_active_diagnoses_by_type(
        db,
        tenant_id=tenant_id,
        patient_id=patient_id,
        diagnosis_type=DiagnosisType.SECONDARY,
    )

    active_comorbidities = _get_active_diagnoses_by_type(
        db,
        tenant_id=tenant_id,
        patient_id=patient_id,
        diagnosis_type=DiagnosisType.COMORBIDITY,
    )

    return {
        "primary": _diagnosis_to_payload(
            active_primary
        ),
        "secondary": [
            _diagnosis_to_payload(diagnosis)
            for diagnosis in active_secondary
        ],
        "comorbidities": [
            _diagnosis_to_payload(diagnosis)
            for diagnosis in active_comorbidities
        ],
    }
    
# =========================================================
# CREATE PATIENT ✅ FIXED (AUTO MRN)
# =========================================================

@router.post("/")
def create_patient(
    payload: PatientCreate,
    db: Session = Depends(get_db_with_request_state),
    user=Depends(require_tenant_user),
):
    tenant_id = _tenant_id_uuid(user)

    first_name, middle_name, last_name, full_name = (
        _compose_full_name_for_patient(
            first_name=payload.first_name,
            middle_name=payload.middle_name,
            last_name=payload.last_name,
        )
    )

    primary_icd10_code, primary_diagnosis_description, primary_display_name = (
        _parse_primary_diagnosis_input(
            db,
            payload.primary_diagnosis,
        )
    )

    user_id = getattr(user, "user_id", None)

    if not user_id:
        raise HTTPException(
            status_code=500,
            detail="Invalid user identity (created_by required)",
        )

    count = db.query(
        func.count(Patient.id)
    ).scalar() or 0

    mrn_value = (
        "LFH-"
        + str(count + 1).zfill(6)
    )

    patient_id = uuid.uuid4()
    now = datetime.now(timezone.utc)

    patient = Patient(
        id=patient_id,
        tenant_id=tenant_id,
        mrn=mrn_value,
        full_name=full_name,
        date_of_birth=payload.date_of_birth,
        primary_diagnosis=primary_display_name,
        status="ACTIVE",
        admission_status="PRE_REFERRAL",
        acuity_state="ROUTINE",
        created_by=user_id,
    )

    facesheet = PatientFaceSheet(
        patient_id=patient_id,
        first_name=first_name,
        middle_name=middle_name,
        last_name=last_name,
        dob=payload.date_of_birth,
        primary_diagnosis=primary_display_name,
        created_by=user_id,
        updated_by=user_id,
        updated_at=now,
    )

    diagnosis = PatientDiagnosis(
        tenant_id=tenant_id,
        patient_id=patient_id,
        diagnosis_type=DiagnosisType.PRIMARY,
        status=DiagnosisStatus.ACTIVE,
        source=DiagnosisSource.REFERRAL,
        icd10_code=primary_icd10_code,
        diagnosis_description=primary_diagnosis_description,
        display_name=primary_display_name,
        active=True,
        is_terminal=True,
        is_related_to_terminal=True,
        effective_date=date.today(),
        created_by=user_id,
    )

    db.add(patient)
    db.add(facesheet)
    db.add(diagnosis)

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise

    db.refresh(patient)

    created_by_name = (
        db.query(
            func.coalesce(
                User.display_name,
                User.full_name,
                User.email,
            )
        )
        .filter(
            User.id == patient.created_by
        )
        .scalar()
    )

    return {
        "id": str(patient.id),
        "mrn": patient.mrn,
        "first_name": first_name,
        "middle_name": middle_name,
        "last_name": last_name,
        "full_name": patient.full_name,
        "date_of_birth": patient.date_of_birth,
        "primary_diagnosis": patient.primary_diagnosis,
        "status": patient.status,
        "admission_status": patient.admission_status,
        "acuity_state": patient.acuity_state,
        "created_by": str(patient.created_by),
        "created_by_name": created_by_name,
        "created_at": patient.created_at,
        "facesheet_created": True,
    }
# =========================================================
# FACE SHEET SCHEMA
# =========================================================

class FaceSheetCreate(BaseModel):

    # ==================================================
    # ✅ PATIENT IDENTITY
    # ==================================================

    first_name: str
    middle_name: str | None = None
    last_name: str

    ssn: str | None = None

    dob: date | None = None

    gender: str | None = None
    race: str | None = None
    ethnicity: str | None = None

    language: str | None = None
    religion: str | None = None
    marital_status: str | None = None

    phone: str | None = None

    address: str | None = None
    city: str | None = None
    state: str | None = None
    zip: str | None = None

    # ==================================================
    # ✅ CURRENT PLACE OF SERVICE (POS)
    # Where patient physically resides NOW
    # ==================================================

    current_pos_type: str | None = None

    # HOME
    # ASSISTED_LIVING
    # MEMORY_CARE
    # BOARD_AND_CARE
    # RCFE
    # SNF
    # LONG_TERM_CARE
    # HOSPITAL
    # VA_FACILITY
    # CORRECTIONAL_FACILITY
    # OTHER

    current_pos_name: str | None = None

    current_pos_address: str | None = None

    room_number: str | None = None

    pos_start_date: date | None = None

    pos_end_date: date | None = None

    # ==================================================
    # ✅ CURRENT LEVEL OF CARE (LOC)
    # Hospice level of care
    # ==================================================

    current_level_of_care: str | None = None

    # ROUTINE_HOME_CARE
    # CONTINUOUS_HOME_CARE
    # GENERAL_INPATIENT
    # INPATIENT_RESPITE

    loc_effective_date: date | None = None

    # ==================================================
    # ✅ PRIMARY COVERAGE
    # ==================================================

    primary_payer: str | None = None

    primary_policy_number: str | None = None

    mbi_number: str | None = None

    # ==================================================
    # ✅ SECONDARY COVERAGE
    # ==================================================

    secondary_payer: str | None = None

    secondary_policy_number: str | None = None

    # ==================================================
    # ✅ AUTHORIZATION TRACKING
    # ==================================================

    requires_prior_authorization: bool | None = None

    authorization_required_for: str | None = None

    # HOSPICE
    # RESPITE
    # GIP
    # DME
    # OTHER

    authorization_number: str | None = None

    authorization_status: str | None = None

    # NOT_REQUIRED
    # PENDING
    # APPROVED
    # DENIED
    # EXPIRED

    authorization_start_date: date | None = None

    authorization_end_date: date | None = None

    # ==================================================
    # ✅ DIAGNOSIS / CLINICAL
    # ==================================================

    primary_diagnosis: str | None = None

    secondary_diagnoses: str | None = None

    has_allergies: bool | None = None

    allergies: str | None = None

    # ==================================================
    # ✅ HOSPICE DATES
    # ==================================================

    ref_date: date | None = None

    soc_date: date | None = None

    recert_date: date | None = None

    # ==================================================
    # ✅ RESPONSIBLE PARTY
    # ==================================================

    responsible_party_name: str | None = None

    responsible_party_relationship: str | None = None

    responsible_party_phone: str | None = None

    # ==================================================
    # ✅ EMERGENCY CONTACT
    # ==================================================

    emergency_contact_name: str | None = None

    emergency_contact_relationship: str | None = None

    emergency_contact_phone: str | None = None

    # ==================================================
    # ✅ ATTENDING PHYSICIAN
    # ==================================================

    attending_physician_name: str | None = None

    attending_physician_npi: str | None = None

    attending_physician_following: bool | None = None

    # ==================================================
    # ✅ HOSPICE MEDICAL DIRECTOR
    # ==================================================

    medical_director_name: str | None = None

    medical_director_npi: str | None = None

    medical_director_designee_name: str | None = None

    medical_director_designee_npi: str | None = None

    associate_medical_director_name: str | None = None

    associate_medical_director_npi: str | None = None

    # ==================================================
    # ✅ PHARMACY
    # ==================================================

    pharmacy_name: str | None = None

    pharmacy_phone: str | None = None

    pharmacy_fax: str | None = None

    # ==================================================
    # ✅ DME
    # ==================================================

    dme_vendor_name: str | None = None

    dme_vendor_phone: str | None = None

    # ==================================================
    # ✅ MORTUARY
    # ==================================================

    mortuary_name: str | None = None

    mortuary_phone: str | None = None

    # ==================================================
    # ✅ SPECIAL INSTRUCTIONS
    # ==================================================

    special_instructions: str | None = None

# =========================================================
# SAVE / UPDATE FACE SHEET
# =========================================================

@router.post("/{patient_id}/facesheet")
def save_facesheet(
    patient_id: uuid.UUID,
    payload: FaceSheetCreate,
    db: Session = Depends(get_db_with_request_state),
    user=Depends(require_tenant_user),
):
    tenant_id = _tenant_id_uuid(user)

    patient = db.query(Patient).filter(
        Patient.id == patient_id,
        Patient.tenant_id == tenant_id
    ).first()

    if not patient:
        raise HTTPException(404, "Patient not found")

    user_id = getattr(user, "user_id", None)

    if not user_id:
        raise HTTPException(500, "Invalid user identity")

    facesheet = (
        db.query(PatientFaceSheet)
        .filter(
            PatientFaceSheet.patient_id == patient.id
        )
        .first()
    )

    if not facesheet:
        facesheet = PatientFaceSheet(
            patient_id=patient.id,
            created_by=str(user_id),
        )
        db.add(facesheet)

    data = payload.model_dump(exclude_unset=True)

    if "primary_diagnosis" in data:
        primary_diagnosis_value = data.get("primary_diagnosis")

        if primary_diagnosis_value is None or not str(primary_diagnosis_value).strip():
            raise HTTPException(
                status_code=400,
                detail="Primary diagnosis cannot be blank",
            )

        sync_result = sync_official_primary_diagnosis(
            db,
            tenant_id=tenant_id,
            patient_id=patient.id,
            primary_diagnosis=primary_diagnosis_value,
            source="REFERRAL",
            updated_by=user_id,
        )

        if not sync_result.get("synced"):
            reason = sync_result.get("reason")
            detail = sync_result.get("detail") or reason or "Primary diagnosis sync failed"

            if reason == "PATIENT_NOT_FOUND":
                raise HTTPException(
                    status_code=404,
                    detail=detail,
                )

            if reason == "MISSING_ACTOR_FOR_AUDIT_FIELDS":
                raise HTTPException(
                    status_code=500,
                    detail=detail,
                )

            raise HTTPException(
                status_code=400,
                detail=detail,
            )

        data["primary_diagnosis"] = sync_result["primary_diagnosis"]

    for field, value in data.items():
        if hasattr(facesheet, field):
            setattr(facesheet, field, value)

    facesheet.updated_by = str(user_id)
    facesheet.updated_at = datetime.now(timezone.utc)

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise

    db.refresh(facesheet)

    return {
        "status": "facesheet saved",
        "facesheet_id": str(facesheet.id),
        "patient_id": str(patient.id),
    }

# =========================================================
# GET FACE SHEET
# =========================================================

@router.get("/{patient_id}/facesheet")
def get_facesheet(
    patient_id: uuid.UUID,
    db: Session = Depends(get_db_with_request_state),
    user=Depends(require_tenant_user),
):
    tenant_id = _tenant_id_uuid(user)

    patient = db.query(Patient).filter(
        Patient.id == patient_id,
        Patient.tenant_id == tenant_id
    ).first()

    if not patient:
        raise HTTPException(404, "Patient not found")

    facesheet = (
    db.query(PatientFaceSheet)
    .filter(
        PatientFaceSheet.patient_id == patient.id
    )
    .first()
)

    if not facesheet:
        raise HTTPException(
            status_code=404,
            detail="Facesheet not found"
        )
    
    diagnosis_summary = _get_diagnosis_summary_payload(
        db,
        tenant_id=tenant_id,
        patient_id=patient.id,
    )
    
    return {
        "mrn": patient.mrn,
        "full_name": patient.full_name,

        # --------------------------------------------------
        # PERSONAL
        # --------------------------------------------------
        "first_name": facesheet.first_name,
        "middle_name": facesheet.middle_name,
        "last_name": facesheet.last_name,

        "ssn": facesheet.ssn,

        "address": facesheet.address,
        "city": facesheet.city,
        "state": facesheet.state,
        "zip": facesheet.zip,

        "phone": facesheet.phone,
        "dob": facesheet.dob,

        "gender": facesheet.gender,
        "race": facesheet.race,
        "ethnicity": facesheet.ethnicity,

        "language": facesheet.language,
        "religion": facesheet.religion,
        "marital_status": facesheet.marital_status,

        # --------------------------------------------------
        # INSURANCE
        # --------------------------------------------------
        "primary_payer": facesheet.primary_payer,
        "primary_policy_number": facesheet.primary_policy_number,

        "mbi_number": facesheet.mbi_number,

        "secondary_payer": facesheet.secondary_payer,
        "secondary_policy_number": facesheet.secondary_policy_number,

        # --------------------------------------------------
        # AUTHORIZATION
        # --------------------------------------------------
        "requires_prior_authorization":
            facesheet.requires_prior_authorization,

        "authorization_required_for":
            facesheet.authorization_required_for,

        "authorization_number":
            facesheet.authorization_number,

        "authorization_status":
            facesheet.authorization_status,

        "authorization_start_date":
            facesheet.authorization_start_date,

        "authorization_end_date":
            facesheet.authorization_end_date,

        # --------------------------------------------------
        # CLINICAL
        # --------------------------------------------------
        "primary_diagnosis": facesheet.primary_diagnosis,

        "secondary_diagnoses":
            facesheet.secondary_diagnoses,

        "diagnoses":
            diagnosis_summary,

        "active_primary_diagnosis":
            diagnosis_summary["primary"],

        "active_secondary_diagnoses":
            diagnosis_summary["secondary"],

        "active_comorbidities":
            diagnosis_summary["comorbidities"],

        "has_allergies":
            facesheet.has_allergies,

        "allergies":
            facesheet.allergies,

        # --------------------------------------------------
        # LEVEL OF CARE
        # --------------------------------------------------
        "current_level_of_care":
            facesheet.current_level_of_care,

        "loc_effective_date":
            facesheet.loc_effective_date,

        # --------------------------------------------------
        # POS
        # --------------------------------------------------
        "current_pos_type":
            facesheet.current_pos_type,

        "current_pos_name":
            facesheet.current_pos_name,

        "current_pos_address":
            facesheet.current_pos_address,

        "room_number":
            facesheet.room_number,

        "pos_start_date":
            facesheet.pos_start_date,

        "pos_end_date":
            facesheet.pos_end_date,

        # --------------------------------------------------
        # RESPONSIBLE PARTY
        # --------------------------------------------------
        "responsible_party_name":
            facesheet.responsible_party_name,

        "responsible_party_relationship":
            facesheet.responsible_party_relationship,

        "responsible_party_phone":
            facesheet.responsible_party_phone,

        # --------------------------------------------------
        # EMERGENCY CONTACT
        # --------------------------------------------------
        "emergency_contact_name":
            facesheet.emergency_contact_name,

        "emergency_contact_relationship":
            facesheet.emergency_contact_relationship,

        "emergency_contact_phone":
            facesheet.emergency_contact_phone,

        # --------------------------------------------------
        # PHYSICIANS
        # --------------------------------------------------
        "attending_physician_name":
            facesheet.attending_physician_name,

        "attending_physician_npi":
            facesheet.attending_physician_npi,

        "attending_physician_following":
            facesheet.attending_physician_following,

        "medical_director_name":
            facesheet.medical_director_name,

        "medical_director_npi":
            facesheet.medical_director_npi,

        "medical_director_designee_name":
            facesheet.medical_director_designee_name,

        "medical_director_designee_npi":
            facesheet.medical_director_designee_npi,

        "associate_medical_director_name":
            facesheet.associate_medical_director_name,

        "associate_medical_director_npi":
            facesheet.associate_medical_director_npi,

        # --------------------------------------------------
        # VENDORS
        # --------------------------------------------------
        "pharmacy_name":
            facesheet.pharmacy_name,

        "pharmacy_phone":
            facesheet.pharmacy_phone,

        "pharmacy_fax":
            facesheet.pharmacy_fax,

        "dme_vendor_name":
            facesheet.dme_vendor_name,

        "dme_vendor_phone":
            facesheet.dme_vendor_phone,

        # --------------------------------------------------
        # MORTUARY
        # --------------------------------------------------
        "mortuary_name":
            facesheet.mortuary_name,

        "mortuary_phone":
            facesheet.mortuary_phone,

        # --------------------------------------------------
        # SERVICE DATES
        # --------------------------------------------------
        "soc_date":
            facesheet.soc_date,

        "ref_date":
            facesheet.ref_date,

        "recert_date":
            facesheet.recert_date,

        # --------------------------------------------------
        # NOTES
        # --------------------------------------------------
        "special_instructions":
            facesheet.special_instructions,
    }
    
# =========================================================
# UPDATE PATIENT ✅ RESTORED
# =========================================================

@router.put("/{patient_id}")
def update_patient(
    patient_id: uuid.UUID,
    payload: PatientUpdate,
    db: Session = Depends(get_db_with_request_state),
    user=Depends(require_tenant_user),
):
    tenant_id = _tenant_id_uuid(user)

    patient = db.query(Patient).filter(
        Patient.id == patient_id,
        Patient.tenant_id == tenant_id
    ).first()

    if not patient:
        raise HTTPException(
            status_code=404,
            detail="Patient not found",
        )

    data = payload.model_dump(exclude_unset=True)

    if not data:
        raise HTTPException(
            status_code=400,
            detail="No fields provided for update",
        )

    user_id = (
        getattr(user, "id", None)
        or getattr(user, "user_id", None)
        or getattr(user, "sub", None)
    )

    if not user_id:
        raise HTTPException(
            status_code=500,
            detail="Invalid user identity",
        )

    final_status = data.get(
        "admission_status",
        patient.admission_status,
    )

    final_discharge_reason = data.get(
        "discharge_reason",
        patient.discharge_reason,
    )

    final_initiated_by = data.get(
        "discharge_initiated_by",
        patient.discharge_initiated_by,
    )

    final_plan_reviewed = data.get(
        "discharge_plan_reviewed",
        patient.discharge_plan_reviewed,
    )

    if final_status == "DISCHARGED":
        if not final_discharge_reason:
            raise HTTPException(
                status_code=400,
                detail="discharge_reason is required",
            )

        if not final_initiated_by:
            raise HTTPException(
                status_code=400,
                detail="discharge_initiated_by is required",
            )

        if final_plan_reviewed is None:
            raise HTTPException(
                status_code=400,
                detail="discharge_plan_reviewed is required",
            )

    if "primary_diagnosis" in data:
        primary_diagnosis_value = data.get("primary_diagnosis")

        if primary_diagnosis_value is None or not str(primary_diagnosis_value).strip():
            raise HTTPException(
                status_code=400,
                detail="Primary diagnosis cannot be blank",
            )

        sync_result = sync_official_primary_diagnosis(
            db,
            tenant_id=tenant_id,
            patient_id=patient.id,
            primary_diagnosis=primary_diagnosis_value,
            source="RN_ICA",
            updated_by=user_id,
        )

        if not sync_result.get("synced"):
            reason = sync_result.get("reason")
            detail = sync_result.get("detail") or reason or "Primary diagnosis sync failed"

            if reason == "PATIENT_NOT_FOUND":
                raise HTTPException(
                    status_code=404,
                    detail=detail,
                )

            if reason == "MISSING_ACTOR_FOR_AUDIT_FIELDS":
                raise HTTPException(
                    status_code=500,
                    detail=detail,
                )

            raise HTTPException(
                status_code=400,
                detail=detail,
            )

        data["primary_diagnosis"] = sync_result["primary_diagnosis"]

    for field, value in data.items():
        setattr(patient, field, value)

    patient.updated_by = user_id
    patient.updated_at = datetime.now(timezone.utc)

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise

    db.refresh(patient)

    return patient

# ---------------------------------------------------------
# ✅ VALIDATION HELPERS
# ---------------------------------------------------------

def validate_name_fields(facesheet):
    if not facesheet.first_name:
        raise HTTPException(400, "First name is required")

    if not facesheet.last_name:
        raise HTTPException(400, "Last name is required")

    # ✅ Conditional middle name rule
    if facesheet.middle_name is not None and facesheet.middle_name == "":
        raise HTTPException(400, "Middle name cannot be empty if provided")

def validate_name_for_eligibility(patient):
    if not getattr(patient, "first_name", None):
        raise HTTPException(400, "First name required for eligibility")

    if not getattr(patient, "last_name", None):
        raise HTTPException(400, "Last name required for eligibility")

    mbi = getattr(patient, "mbi_number", None)
    dob = getattr(patient, "dob", None)

    if not mbi:
        raise HTTPException(400, "MBI required for eligibility")

    if not dob:
        raise HTTPException(400, "Date of birth required for eligibility")

    # ✅ KEY RULE (this prevents your real-world issue)
    if getattr(patient, "middle_name", None) is None:
        # allow initial attempt
        return

    if getattr(patient, "middle_name") == "":
        raise HTTPException(
            400,
            "Middle name must match Medicare card if patient has one"
        )

def build_name_variants(patient):
    first = getattr(patient, "first_name", "").strip()
    middle = getattr(patient, "middle_name", None)
    last = getattr(patient, "last_name", "").strip()

    variants = []

    # ✅ 1. FULL NAME (highest accuracy)
    if middle:
        variants.append({
            "first_name": first,
            "middle_name": middle,
            "last_name": last
        })

        # ✅ 2. MIDDLE INITIAL
        variants.append({
            "first_name": first,
            "middle_name": middle[0],  # initial only
            "last_name": last
        })

    # ✅ 3. NO MIDDLE
    variants.append({
        "first_name": first,
        "middle_name": None,
        "last_name": last
    })

    return variants

def run_eligibility_with_retry(patient, eligibility_client):
    variants = build_name_variants(patient)

    for variant in variants:
        try:
            response = eligibility_client.check(
                first_name=variant["first_name"],
                middle_name=variant["middle_name"],
                last_name=variant["last_name"],
                dob=patient.dob,
                mbi=patient.mbi_number
            )

            if response and response.get("eligible"):
                return {
                    "status": "SUCCESS",
                    "matched_variant": variant
                }

        except Exception:
            continue

    raise HTTPException(
        status_code=400,
        detail="Eligibility failed: verify patient name matches Medicare card"
    )
    
# =========================================================
# ADMIT PATIENT
# =========================================================

@router.post("/{patient_id}/admit")
def admit_patient(
    patient_id: uuid.UUID,
    db: Session = Depends(get_db_with_request_state),
    user=Depends(require_tenant_user),
):
    tenant_id = _tenant_id_uuid(user)

    patient = db.query(Patient).filter(
        Patient.id == patient_id,
        Patient.tenant_id == tenant_id
    ).first()

    if not patient:
        raise HTTPException(404, "Patient not found")

    now = datetime.now(timezone.utc)

    # --------------------------------------------------
    # ✅ VALIDATION: READY FOR ADMISSION
    # --------------------------------------------------
    if not patient.primary_diagnosis:
        raise HTTPException(400, "Primary diagnosis required for admission")

    if not patient.election_signed_at:
        raise HTTPException(400, "Election must be signed before admission")

    if not patient.records_release_signed_at:
        raise HTTPException(400, "Records release must be signed")

    # --------------------------------------------------
    # ✅ AUTHORIZE ADMISSION
    # --------------------------------------------------
    user_id = getattr(user, "id", None) \
        or getattr(user, "user_id", None) \
        or getattr(user, "sub", None)

    if not user_id:
        raise HTTPException(500, "Invalid user identity")

    patient.admission_authorized_at = now
    patient.admission_authorized_by = user_id

    # --------------------------------------------------
    # ✅ SET SOC (START OF CARE)
    # --------------------------------------------------
    if not patient.soc_date:
        patient.soc_date = now

    # --------------------------------------------------
    # ✅ FINAL TRANSITION
    # --------------------------------------------------
    patient.admission_status = "ADMITTED"
    patient.on_service_at = now

    # --------------------------------------------------
    # ✅ TASK CREATOR (FIXED FOR YOUR DB SCHEMA)
    # --------------------------------------------------
    def create_task(
        task_type,
        alert_reason,
        due_hours,
        discipline,
        regulatory_basis
    ):
        return Task(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            patient_id=patient.id,
            task_type=task_type,
            alert_reason=alert_reason,
            status=TaskStatus.PENDING,
            origin=TaskOrigin.SYSTEM,
            discipline=discipline,
            regulatory_basis=regulatory_basis,
            created_at=now,
            due_at=now + timedelta(hours=due_hours),
            created_by=str(user_id),
        )

    # --------------------------------------------------
    # ✅ CREATE ADMISSION TASKS (ENUM-VALID)
    # --------------------------------------------------
    tasks = [

        create_task(
            TaskType.CERTIFICATION,
            "Physician Hospice Certification",
            48,
            TaskDiscipline.MD,
            TaskRegulatoryBasis.CERTIFICATION
        ),

        create_task(
            TaskType.POC_REVIEW_REQUIRED,
            "Establish Plan of Care",
            24,
            TaskDiscipline.RN,
            TaskRegulatoryBasis.POC_UPDATE
        ),

        create_task(
            TaskType.CLINICAL_REVIEW_REQUIRED,
            "Admission Clinical Review",
            24,
            TaskDiscipline.RN,
            TaskRegulatoryBasis.CONDITION_TRIGGER
        ),
    ]

    for t in tasks:
        db.add(t)

    # --------------------------------------------------
    # ✅ SAVE
    # --------------------------------------------------
    db.commit()
    db.refresh(patient)

    return {
        "status": "ADMITTED",
        "soc_date": patient.soc_date
    }

@router.post("/{patient_id}/authorize-admission")
def authorize_admission(
    patient_id: uuid.UUID,
    db: Session = Depends(get_db_with_request_state),
    user=Depends(require_tenant_user),
):
    tenant_id = _tenant_id_uuid(user)

    patient = db.query(Patient).filter(
        Patient.id == patient_id,
        Patient.tenant_id == tenant_id
    ).first()

    if not patient:
        raise HTTPException(404, "Patient not found")

    now = datetime.now(timezone.utc)

    user_id = getattr(user, "id", None) \
        or getattr(user, "user_id", None) \
        or getattr(user, "sub", None)

    if not user_id:
        raise HTTPException(500, "Invalid user identity")

    patient.admission_authorized_at = now
    patient.admission_authorized_by = user_id

    db.commit()

    return {"status": "AUTHORIZED"}

# =========================================================
# NON ADMIT
# =========================================================

@router.post("/{patient_id}/non-admit")
def non_admit_patient(
    patient_id: uuid.UUID,
    db: Session = Depends(get_db_with_request_state),
    user=Depends(require_tenant_user),
):
    tenant_id = _tenant_id_uuid(user)

    patient = db.query(Patient).filter(
        Patient.id == patient_id,
        Patient.tenant_id == tenant_id
    ).first()

    if not patient:
        raise HTTPException(404, "Patient not found")

    patient.admission_status = "NON_ADMIT"
    patient.not_admitted_at = datetime.now(timezone.utc)

    db.commit()
    return {"status": "NON_ADMIT"}

@router.post("/tasks/{task_id}/complete")
def complete_task(
    task_id: uuid.UUID,
    db: Session = Depends(get_db_with_request_state),
    user=Depends(require_tenant_user),
):
    tenant_id = _tenant_id_uuid(user)

    task = db.query(Task).filter(
        Task.id == task_id,
        Task.tenant_id == tenant_id
    ).first()

    if not task:
        raise HTTPException(404, "Task not found")
    
    # --------------------------------------------------
    # ✅ COMPLETION VALIDATION (CRITICAL)
    # --------------------------------------------------

    # ✅ RN SOC VISIT MUST HAVE VISIT RECORD
    if task.task_type == TaskType.INITIAL_RN_ICA:
        visit_exists = db.query(Visit).filter(
            Visit.patient_id == task.patient_id,
            Visit.tenant_id == tenant_id
        ).first()

        if not visit_exists:
            raise HTTPException(
                400,
                "RN visit must be completed before closing task"
            )


    # ✅ CERTIFICATION MUST HAVE APPROVAL (placeholder logic)
    if task.task_type == TaskType.CERTIFICATION:
        # You will later check physician certification table
        if not task.completed_at:
            raise HTTPException(
                400,
                "Certification documentation required"
            )


    # ✅ PLAN OF CARE
    if task.task_type == TaskType.POC_REVIEW_REQUIRED:
        # placeholder validation — expand later
        if not task.completed_at:
            raise HTTPException(
                400,
                "Plan of care must be established"
            )


    # ✅ CLINICAL REVIEW
    if task.task_type == TaskType.CLINICAL_REVIEW_REQUIRED:
        # placeholder — check for clinical note later
        if not task.completed_at:
            raise HTTPException(
                400,
                "Clinical review required before completion"
            )
    
    # --------------------------------------------------
    # ✅ COMPLETE TASK
    # --------------------------------------------------

    now = datetime.now(timezone.utc)

    user_id = getattr(user, "id", None) \
        or getattr(user, "user_id", None) \
        or getattr(user, "sub", None)

    task.status = TaskStatus.COMPLETED
    task.completed_at = now
    task.completion_reference_type = "NOTE"  # placeholder
    task.completion_reference_id = str(user_id)

    db.commit()

    return {"status": "COMPLETED"}
# =========================================================
# CHART SUMMARY ✅ REQUIRED (FIXES YOUR IMPORT ERROR)
# =========================================================

@router.get("/{patient_id}/chart-summary")
def patient_chart_summary(
    patient_id: uuid.UUID,
    db: Session = Depends(get_db_with_request_state),
    user=Depends(require_tenant_user),
):
    tenant_id = _tenant_id_uuid(user)

    patient = db.query(Patient).filter(
        Patient.id == patient_id,
        Patient.tenant_id == tenant_id
    ).first()

    if not patient:
        raise HTTPException(404, "Patient not found")
    
    facesheet = (
        db.query(PatientFaceSheet)
        .filter(
            PatientFaceSheet.patient_id == patient.id
        )
        .first()
    )
    
    diagnosis_summary = _get_diagnosis_summary_payload(
        db,
        tenant_id=tenant_id,
        patient_id=patient.id,
    )
    
    visits = db.query(Visit).filter(
        Visit.patient_id == patient_id,
        Visit.tenant_id == tenant_id
    ).order_by(Visit.visit_datetime.desc()).all()

    return {
        "patient": patient,

        "diagnoses": diagnosis_summary,

        "facesheet": {
            # -----------------------------------------
            # COVERAGE
            # -----------------------------------------
            "primary_payer": getattr(facesheet, "primary_payer", None),
            "primary_policy_number": getattr(facesheet, "primary_policy_number", None),
            "secondary_payer": getattr(facesheet, "secondary_payer", None),
            "secondary_policy_number": getattr(facesheet, "secondary_policy_number", None),
            "mbi_number": getattr(facesheet, "mbi_number", None),

            # -----------------------------------------
            # AUTHORIZATION
            # -----------------------------------------
            "requires_prior_authorization": getattr(
                facesheet,
                "requires_prior_authorization",
                None
            ),
            "authorization_status": getattr(
                facesheet,
                "authorization_status",
                None
            ),

            # -----------------------------------------
            # CLINICAL
            # -----------------------------------------
            "primary_diagnosis": getattr(
                facesheet,
                "primary_diagnosis",
                None
            ),
            
            "active_primary_diagnosis":
                diagnosis_summary["primary"],

            "active_secondary_diagnoses":
                diagnosis_summary["secondary"],

            "active_comorbidities":
                diagnosis_summary["comorbidities"],
            
            "has_allergies": getattr(
                facesheet,
                "has_allergies",
                None
            ),

            # -----------------------------------------
            # LOC
            # -----------------------------------------
            "current_level_of_care": getattr(
                facesheet,
                "current_level_of_care",
                None
            ),

            "loc_effective_date": getattr(
                facesheet,
                "loc_effective_date",
                None
            ),

            # -----------------------------------------
            # POS
            # -----------------------------------------
            "current_pos_type": getattr(
                facesheet,
                "current_pos_type",
                None
            ),

            "current_pos_name": getattr(
                facesheet,
                "current_pos_name",
                None
            ),

            "room_number": getattr(
                facesheet,
                "room_number",
                None
            ),

            # -----------------------------------------
            # RESPONSIBLE PARTY
            # -----------------------------------------
            "responsible_party_name": getattr(
                facesheet,
                "responsible_party_name",
                None
            ),

            "responsible_party_phone": getattr(
                facesheet,
                "responsible_party_phone",
                None
            ),

            # -----------------------------------------
            # EMERGENCY CONTACT
            # -----------------------------------------
            "emergency_contact_name": getattr(
                facesheet,
                "emergency_contact_name",
                None
            ),

            "emergency_contact_phone": getattr(
                facesheet,
                "emergency_contact_phone",
                None
            ),

            # -----------------------------------------
            # PHYSICIANS
            # -----------------------------------------
            "attending_physician_name": getattr(
                facesheet,
                "attending_physician_name",
                None
            ),

            "medical_director_name": getattr(
                facesheet,
                "medical_director_name",
                None
            ),

            "medical_director_designee_name": getattr(
                facesheet,
                "medical_director_designee_name",
                None
            ),

            "associate_medical_director_name": getattr(
                facesheet,
                "associate_medical_director_name",
                None
            ),
        } if facesheet else None,

        "visits": visits,
    }