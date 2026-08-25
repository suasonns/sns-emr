# =========================================================
# ENTERPRISE PATIENTS ROUTER (FULL PRESERVED + FIXED)
# =========================================================

from __future__ import annotations

import uuid
import re
import logging
from datetime import date, datetime, timedelta, timezone
from typing import Generator

from fastapi import APIRouter, Depends, HTTPException, Request, status, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func, text

from app.core.security import get_current_user
from app.core.patient_access import get_authorized_patient
from app.core.capabilities import VIEW_ALL_TENANT_PATIENTS, has_capability
from app.db_tenant_dependency import get_db_tenant

from app.models.patient import Patient
from app.models.user import User
from app.models.admission import Admission
from app.models.patient_assignment import PatientAssignment
from app.models.patient_facesheet import PatientFaceSheet
from app.models.task import Task
from app.models.visit import Visit
from app.models.patient_diagnosis import PatientDiagnosis
from app.billing.models.patient_pos import PatientPOS
from app.models.patient_payer import PatientPayer
from app.models.rnica_assessment import RnicaAssessment
from app.models.rn_recert_assessment import RNRecertAssessment

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
)
from app.services.icd10_resolver_service import (
    ICD10ResolutionError,
    resolve_icd10_diagnosis_for_use,
)
from app.services.diagnosis_sync_service import (
    sync_official_primary_diagnosis,
)
from app.services.code_status_sync_service import (
    CODE_STATUS_DISPLAY_LABELS,
    get_current_code_status,
)
from app.services.physician_sync_service import (
    ASSOCIATE_MEDICAL_DIRECTOR,
    ATTENDING,
    MEDICAL_DIRECTOR,
    get_physician_assignments,
)
from app.services.contact_sync_service import (
    EMERGENCY_CONTACT,
    RESPONSIBLE_PARTY,
    get_patient_contacts,
)
from app.services.hnp_parser_service import build_hnp_summary
from app.services.assessment_history_service import (
    AssessmentHistoryFilters,
    list_patient_assessment_history,
)
from enum import Enum

from datetime import datetime

logger = logging.getLogger(__name__)

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
        raise HTTPException(401, "Missing tenant")
    return uuid.UUID(str(user.tenant_id))

def _get_latest_admission(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    patient_id: uuid.UUID,
) -> Admission | None:
    return (
        db.query(Admission)
        .filter(
            Admission.tenant_id == tenant_id,
            Admission.patient_id == patient_id,
        )
        .order_by(Admission.created_at.desc())
        .first()
    )


def _get_active_admission(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    patient_id: uuid.UUID,
) -> Admission | None:
    return (
        db.query(Admission)
        .filter(
            Admission.tenant_id == tenant_id,
            Admission.patient_id == patient_id,
            Admission.status == "ADMITTED",
            Admission.discharged_at.is_(None),
        )
        .order_by(Admission.created_at.desc())
        .first()
    )

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
    first_name: str | None = None
    middle_name: str | None = None
    last_name: str | None = None
    
    primary_diagnosis: str | None = None
    status: str | None = None

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
    if user.role in {"CHHA", "VOLUNTEER"}:
        raise HTTPException(
            status_code=403,
            detail="User is not authorized to list patients",
        )

    # -----------------------------------------------------
    # Latest admission per patient (tenant-scoped)
    # -----------------------------------------------------
    latest_admission_sq = (
        db.query(
            Admission.patient_id.label("patient_id"),
            func.max(Admission.created_at).label("max_created_at"),
        )
        .filter(Admission.tenant_id == tenant_id)
        .group_by(Admission.patient_id)
        .subquery()
    )

    # -----------------------------------------------------
    # Base query:
    # Pull Patient + latest Admission + FaceSheet identity
    # -----------------------------------------------------
    query = (
        db.query(
            Patient,
            Admission,
            PatientFaceSheet.first_name.label("first_name"),
            PatientFaceSheet.middle_name.label("middle_name"),
            PatientFaceSheet.last_name.label("last_name"),
        )
        .outerjoin(
            PatientFaceSheet,
            PatientFaceSheet.patient_id == Patient.id,
        )
        .outerjoin(
            latest_admission_sq,
            latest_admission_sq.c.patient_id == Patient.id,
        )
        .outerjoin(
            Admission,
            (Admission.patient_id == Patient.id)
            & (Admission.tenant_id == tenant_id)
            & (Admission.created_at == latest_admission_sq.c.max_created_at),
        )
        .filter(
            Patient.tenant_id == tenant_id
        )
    )

    # -----------------------------------------------------
    # Access scoping
    # Use EXISTS instead of JOIN to avoid duplicate rows
    #
    # Single clinical-admin access group (ADMINISTRATOR/DPCS/
    # DPCS_ADMINISTRATOR) + verified tenant-wide physician oversight
    # (MEDICAL_DIRECTOR) see every same-tenant patient. Everyone else
    # (RN, CASE_MANAGER, ATTENDING_PHYSICIAN, etc.) only sees patients
    # they are ACTIVELY assigned to.
    # -----------------------------------------------------
    if not (
        has_capability(user.role, VIEW_ALL_TENANT_PATIENTS)
        or access_level == "FULL_ACCESS"
    ):
        assignment_exists = (
            db.query(PatientAssignment.id)
            .filter(
                PatientAssignment.patient_id == Patient.id,
                PatientAssignment.tenant_id == tenant_id,
                PatientAssignment.user_id == user.user_id,
                PatientAssignment.active.is_(True),
            )
            .exists()
        )

        query = query.filter(assignment_exists)

    # -----------------------------------------------------
    # Category filters
    # -----------------------------------------------------
    if category == PatientCategory.ACTIVE:
        query = query.filter(
            Admission.status == "ADMITTED",
            Admission.discharged_at.is_(None),
        )

    elif category == PatientCategory.PENDING:
        query = query.filter(
            (Admission.status == "PENDING") |
            (Admission.id.is_(None))
        )

    elif category == PatientCategory.PROSPECTIVE:
        query = query.filter(
            Admission.status.in_(["PRE_REFERRAL", "PROSPECT"])
        )

    elif category == PatientCategory.NON_ADMITS:
        query = query.filter(
            Admission.status == "NON_ADMIT"
        )

    elif category == PatientCategory.DISCHARGED_30:
        query = query.filter(
            Admission.discharged_at.isnot(None),
            Admission.discharged_at >= func.now() - text("INTERVAL '30 days'")
        )

    elif category == PatientCategory.DISCHARGED_ALL:
        query = query.filter(
            Admission.discharged_at.isnot(None)
        )

    elif category == PatientCategory.ALL:
        pass

    else:
        raise HTTPException(400, f"Invalid category: {category}")

    # -----------------------------------------------------
    # Ordered rows
    # IMPORTANT:
    # - no .distinct(Patient.id)
    # - stable sort
    # -----------------------------------------------------
    rows = query.order_by(
        func.coalesce(PatientFaceSheet.last_name, ""),
        func.coalesce(PatientFaceSheet.first_name, ""),
        Patient.mrn,
        Patient.id,
    ).all()

    if not rows:
        return []

    # -----------------------------------------------------
    # Collect patient ids for one diagnosis batch query
    # -----------------------------------------------------
    patient_ids = [patient.id for patient, _, _, _, _ in rows]

    active_dx_rows = (
        db.query(PatientDiagnosis)
        .filter(
            PatientDiagnosis.tenant_id == tenant_id,
            PatientDiagnosis.patient_id.in_(patient_ids),
            PatientDiagnosis.status == DiagnosisStatus.ACTIVE,
            PatientDiagnosis.active.is_(True),
            PatientDiagnosis.resolved_date.is_(None),
        )
        .order_by(
            PatientDiagnosis.patient_id.asc(),
            PatientDiagnosis.created_at.asc(),
        )
        .all()
    )

    # -----------------------------------------------------
    # Build compact diagnosis summary map
    # -----------------------------------------------------
    diagnosis_map: dict[str, dict] = {}

    for dx in active_dx_rows:
        pid = str(dx.patient_id)

        if pid not in diagnosis_map:
            diagnosis_map[pid] = {
                "primary": None,
                "secondary_count": 0,
                "comorbidity_count": 0,
                "has_terminal_primary": False,
                "has_related_secondary": False,
                "has_related_comorbidity": False,
            }

        dx_type = _enum_value(dx.diagnosis_type)

        if dx_type == DiagnosisType.PRIMARY.value:
            diagnosis_map[pid]["primary"] = {
                "id": str(dx.id),
                "display_name": f"{dx.display_name} ({dx.icd10_code})" if dx.icd10_code else dx.display_name,
                "diagnosis_description": dx.diagnosis_description,
                "source": _enum_value(dx.source),
                "is_terminal": dx.is_terminal,
                "is_related_to_terminal": dx.is_related_to_terminal,
                "effective_date": dx.effective_date,
            }
            diagnosis_map[pid]["has_terminal_primary"] = bool(dx.is_terminal)

        elif dx_type == DiagnosisType.SECONDARY.value:
            diagnosis_map[pid]["secondary_count"] += 1
            if dx.is_related_to_terminal:
                diagnosis_map[pid]["has_related_secondary"] = True

        elif dx_type == DiagnosisType.COMORBIDITY.value:
            diagnosis_map[pid]["comorbidity_count"] += 1
            if dx.is_related_to_terminal:
                diagnosis_map[pid]["has_related_comorbidity"] = True

    # -----------------------------------------------------
    # Explicit response payload
    # -----------------------------------------------------
    results = []

    for patient, admission, first_name, middle_name, last_name in rows:
        pid = str(patient.id)

        dx_summary = diagnosis_map.get(pid, {
            "primary": None,
            "secondary_count": 0,
            "comorbidity_count": 0,
            "has_terminal_primary": False,
            "has_related_secondary": False,
            "has_related_comorbidity": False,
        })

        results.append({
            "id": pid,
            "mrn": patient.mrn,
            "first_name": first_name,
            "middle_name": middle_name or None,
            "last_name": last_name,
            "date_of_birth": patient.date_of_birth,
            "status": patient.status,
            "primary_diagnosis": patient.primary_diagnosis,
            "admission_status": admission.status if admission else "PENDING",
            "acuity_state": patient.acuity_state,
            "hospice_election_date": admission.effective_date if admission else patient.hospice_election_date,
            "created_at": patient.created_at,
            "updated_at": patient.updated_at,
            "created_by": str(patient.created_by) if patient.created_by else None,
            "updated_by": str(patient.updated_by) if patient.updated_by else None,
            "patient_type": patient.patient_type,
            "diagnosis_summary": dx_summary,
        })

    return results

def _clean_name_part(value: str | None) -> str | None:
    if value is None:
        return None

    cleaned = str(value).strip()

    if not cleaned:
        return None

    return cleaned


def _normalize_name_parts(
    *,
    first_name: str,
    middle_name: str | None,
    last_name: str,
) -> tuple[str, str | None, str]:

    cleaned_first = _clean_name_part(first_name)
    cleaned_middle = _clean_name_part(middle_name)
    cleaned_last = _clean_name_part(last_name)

    if not cleaned_first:
        raise HTTPException(400, "first_name is required")

    if not cleaned_last:
        raise HTTPException(400, "last_name is required")

    return cleaned_first, cleaned_middle, cleaned_last

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
# CARE TEAM — AUTO-POPULATED FROM SHARED ASSIGNMENT SYSTEM
# =========================================================
#
# Facesheet must NOT be the source of truth for who is on a patient's
# care team. app.models.patient_assignment.PatientAssignment (assigned
# via RNICA / scheduling) is the shared source of truth. This helper
# reads the current active assignments and maps them onto the roles the
# Facesheet Hospice Snapshot / Care Team card displays.
#
# NOTE: "Volunteer" has no Discipline enum value yet in this codebase,
# so it cannot be auto-populated from PatientAssignment today; it
# remains a manually-maintained facesheet field until a VOLUNTEER
# discipline is added to app.models.enums.Discipline.
# =========================================================

_CARE_TEAM_DISCIPLINE_MAP: dict[str, tuple[str, ...]] = {
    "primary_rn_name": ("RN",),
    "lvn_name": ("LVN", "LPN"),
    "social_worker_name": ("MSW", "SW", "LCSW", "BSW"),
    "chaplain_name": ("CHAPLAIN",),
    "chha_name": ("CHHA", "AIDE"),
    "clinical_manager_name": ("CASE_MANAGER",),
}


def _get_care_team_assignments(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    patient_id: uuid.UUID,
) -> dict:
    rows = (
        db.query(PatientAssignment, User)
        .join(User, User.id == PatientAssignment.user_id)
        .filter(
            PatientAssignment.tenant_id == tenant_id,
            PatientAssignment.patient_id == patient_id,
            PatientAssignment.active.is_(True),
        )
        .order_by(
            PatientAssignment.is_primary.desc(),
            PatientAssignment.assigned_at.desc(),
        )
        .all()
    )

    by_discipline: dict[str, tuple[str, str]] = {}
    for assignment, assigned_user in rows:
        discipline_value = getattr(assignment.discipline, "value", assignment.discipline)
        if discipline_value in by_discipline:
            continue
        name = assigned_user.display_name or assigned_user.full_name or assigned_user.email
        by_discipline[discipline_value] = (name, str(assigned_user.id))

    result: dict[str, dict | None] = {}
    for field, disciplines in _CARE_TEAM_DISCIPLINE_MAP.items():
        match = None
        for discipline in disciplines:
            if discipline in by_discipline:
                match = by_discipline[discipline]
                break
        result[field] = (
            {"name": match[0], "user_id": match[1], "source": "ASSIGNMENT"}
            if match
            else None
        )

    return result


# =========================================================
# BENEFIT PERIOD — SYSTEM-CALCULATED SCHEDULE
# =========================================================
#
# Hospice benefit periods (per CMS): the first two benefit periods are
# 90 days each; every subsequent benefit period is 60 days, and periods
# continue indefinitely as long as the patient remains eligible. This
# schedule is derived from the election date and should be the primary,
# auto-calculated source for the Facesheet's Benefit Period fields —
# manual entry is a fallback/override only when no election date is on
# file yet (e.g. still in referral).
# =========================================================

def _compute_benefit_period_schedule(
    election_date: date | None,
    *,
    today: date | None = None,
) -> dict:
    if not election_date:
        return {
            "available": False,
            "reason": "NO_ELECTION_DATE",
            "benefit_period_number": None,
            "benefit_period_start": None,
            "benefit_period_end": None,
            "days_remaining": None,
            "recert_due_date": None,
            "face_to_face_due_date": None,
        }

    today = today or date.today()

    period_number = 1
    period_start = election_date
    period_length = 90

    # Walk forward through the BP schedule until we find the period
    # containing "today" (or the next upcoming period if today is
    # before election, or the most recent period if the patient has
    # somehow lapsed past all computed periods).
    while True:
        period_end = period_start + timedelta(days=period_length)

        if today < period_end or period_number >= 60:
            break

        period_number += 1
        period_start = period_end
        period_length = 90 if period_number <= 2 else 60

    days_remaining = (period_end - today).days

    # Operational buffer: recert paperwork should be completed before
    # the benefit period ends; flag 15 days ahead as the internal due
    # date so staff aren't scrambling on the last day.
    recert_due_date = period_end - timedelta(days=15)

    # CMS requires a face-to-face encounter within the 30 days prior to
    # the start of the 3rd benefit period and every period thereafter.
    face_to_face_due_date = period_start if period_number >= 3 else None

    return {
        "available": True,
        "reason": None,
        "benefit_period_number": period_number,
        "benefit_period_start": period_start,
        "benefit_period_end": period_end,
        "days_remaining": days_remaining,
        "recert_due_date": recert_due_date,
        "face_to_face_due_date": face_to_face_due_date,
    }


def _generate_mrn_for_tenant(
    db: Session,
    *,
    tenant_id: uuid.UUID,
) -> str:
    count = (
        db.query(func.count(Patient.id))
        .filter(Patient.tenant_id == tenant_id)
        .scalar()
        or 0
    )

    return "LFH-" + str(count + 1).zfill(6)
    
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

    first_name, middle_name, last_name = _normalize_name_parts(
        first_name=payload.first_name,
        middle_name=payload.middle_name,
        last_name=payload.last_name,
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

    db_user = (
        db.query(User)
        .filter(User.id == user_id)
        .first()
    )

    if not db_user or not db_user.active:
        raise HTTPException(
            status_code=403,
            detail="Inactive or missing user",
        )

    mrn_value = _generate_mrn_for_tenant(
        db,
        tenant_id=tenant_id,
    )

    patient_id = uuid.uuid4()
    now = datetime.now(timezone.utc)

    patient = Patient(
        id=patient_id,
        tenant_id=tenant_id,
        mrn=mrn_value,
        date_of_birth=payload.date_of_birth,

        # ✅ CLINICAL WORKFLOW SOURCE OF TRUTH
        admission_status="REFERRAL",

        # ✅ KEEP ONLY IF USED ELSEWHERE (NON-WORKFLOW UI / LEGACY)
        status="PENDING",
        
        # ✅ REQUIRED FIELDS
        primary_diagnosis=primary_display_name,
        acuity_state="ROUTINE",

        created_by=user_id,
        created_at=now,
    )

    facesheet = PatientFaceSheet(
        tenant_id=tenant_id,
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

    admission = Admission(
        tenant_id=tenant_id,
        patient_id=patient_id,
        status="PENDING",
        admission_date=now.replace(tzinfo=None),
        created_at=now.replace(tzinfo=None),
        created_by=user_id,
    )

    db.add(patient)
    db.add(facesheet)
    db.add(diagnosis)
    db.add(admission)

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise

    # ✅ refresh after commit
    db.refresh(patient)
    db.refresh(admission)

    # ✅ ✅ ENFORCEMENT CHECK (ADD THIS BLOCK)
    fs_check = db.query(PatientFaceSheet).filter(
        PatientFaceSheet.patient_id == patient.id,
        PatientFaceSheet.tenant_id == tenant_id,
    ).first()

    if not fs_check:
        raise HTTPException(
            status_code=500,
            detail="CRITICAL: Facesheet missing — invalid patient record"
        )

    created_by_name = (
        db.query(
            func.coalesce(
                User.display_name,
                User.email,
            )
        )
        .filter(User.id == patient.created_by)
        .scalar()
    )

    patient_name = " ".join(
        part for part in [first_name, middle_name, last_name] if part
    )

    return {
        "id": str(patient.id),
        "mrn": patient.mrn,
        "first_name": first_name,
        "middle_name": middle_name or None,
        "last_name": last_name,
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
# REFERRAL IMPORT / FACE SHEET AUTOFILL
# =========================================================

class ReferralFaceSheetCreate(BaseModel):
    first_name: str
    last_name: str
    middle_name: str | None = None
    date_of_birth: date
    phone: str | None = None
    address: str | None = None
    city: str | None = None
    state: str | None = None
    zip: str | None = None
    gender: str | None = None
    language: str | None = None
    religion: str | None = None
    marital_status: str | None = None
    primary_payer: str | None = None
    primary_policy_number: str | None = None
    authorization_status: str | None = None
    current_level_of_care: str | None = None
    primary_diagnosis: str | None = None
    secondary_diagnoses: str | None = None
    attending_physician_name: str | None = None
    attending_physician_npi: str | None = None
    responsible_party_name: str | None = None
    responsible_party_relationship: str | None = None
    responsible_party_phone: str | None = None
    emergency_contact_name: str | None = None
    emergency_contact_relationship: str | None = None
    emergency_contact_phone: str | None = None
    referral_source: str | None = None
    referral_date: date | None = None
    special_instructions: str | None = None


@router.post("/from-referral")
def create_patient_from_referral(
    payload: ReferralFaceSheetCreate,
    db: Session = Depends(get_db_with_request_state),
    user=Depends(require_tenant_user),
):
    tenant_id = _tenant_id_uuid(user)
    user_id = getattr(user, "user_id", None)

    if not user_id:
        raise HTTPException(500, "Invalid user identity")

    first_name, middle_name, last_name = _normalize_name_parts(
        first_name=payload.first_name,
        middle_name=payload.middle_name,
        last_name=payload.last_name,
    )

    diagnosis_label = payload.primary_diagnosis.strip() if payload.primary_diagnosis else "Diagnosis pending"
    if payload.primary_diagnosis and payload.primary_diagnosis.strip():
        try:
            primary_icd10_code, primary_diagnosis_description, primary_display_name = _parse_primary_diagnosis_input(
                db,
                payload.primary_diagnosis,
            )
        except HTTPException:
            primary_icd10_code = "N/A"
            primary_diagnosis_description = payload.primary_diagnosis.strip()
            primary_display_name = payload.primary_diagnosis.strip()
    else:
        primary_icd10_code = "N/A"
        primary_diagnosis_description = "Diagnosis pending"
        primary_display_name = "Diagnosis pending"

    mrn_value = _generate_mrn_for_tenant(db, tenant_id=tenant_id)
    patient_id = uuid.uuid4()
    now = datetime.now(timezone.utc)

    patient = Patient(
        id=patient_id,
        tenant_id=tenant_id,
        mrn=mrn_value,
        date_of_birth=payload.date_of_birth,
        primary_diagnosis=primary_display_name,
        admission_status="REFERRAL",
        status="PENDING",
        acuity_state="ROUTINE",
        created_by=user_id,
        created_at=now,
    )

    facesheet = PatientFaceSheet(
        tenant_id=tenant_id,
        patient_id=patient_id,
        first_name=first_name,
        middle_name=middle_name,
        last_name=last_name,
        dob=payload.date_of_birth,
        phone=payload.phone,
        address=payload.address,
        city=payload.city,
        state=payload.state,
        zip=payload.zip,
        gender=payload.gender,
        language=payload.language,
        religion=payload.religion,
        marital_status=payload.marital_status,
        primary_payer=payload.primary_payer,
        primary_policy_number=payload.primary_policy_number,
        authorization_status=payload.authorization_status,
        current_level_of_care=payload.current_level_of_care,
        primary_diagnosis=primary_display_name,
        secondary_diagnoses=payload.secondary_diagnoses,
        ref_date=payload.referral_date,
        special_instructions=payload.special_instructions,
        responsible_party_name=payload.responsible_party_name,
        responsible_party_relationship=payload.responsible_party_relationship,
        responsible_party_phone=payload.responsible_party_phone,
        emergency_contact_name=payload.emergency_contact_name,
        emergency_contact_relationship=payload.emergency_contact_relationship,
        emergency_contact_phone=payload.emergency_contact_phone,
        attending_physician_name=payload.attending_physician_name,
        attending_physician_npi=payload.attending_physician_npi,
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

    admission = Admission(
        tenant_id=tenant_id,
        patient_id=patient_id,
        status="PENDING",
        admission_date=now.replace(tzinfo=None),
        created_at=now.replace(tzinfo=None),
        created_by=user_id,
    )

    db.add(patient)
    db.add(facesheet)
    db.add(diagnosis)
    db.add(admission)

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise

    db.refresh(patient)
    db.refresh(facesheet)

    return {
        "id": str(patient.id),
        "mrn": patient.mrn,
        "first_name": first_name,
        "middle_name": middle_name,
        "last_name": last_name,
        "date_of_birth": patient.date_of_birth,
        "primary_diagnosis": primary_display_name,
        "status": patient.status,
        "admission_status": patient.admission_status,
        "facesheet_created": True,
        "facesheet_id": str(facesheet.id),
        "referral_source": payload.referral_source,
        "referral_date": payload.referral_date,
    }


class HnpImportRequest(BaseModel):
    raw_text: str
    patient_id: str | None = None
    source_name: str | None = None


@router.post("/from-hnp")
def create_patient_from_hnp(
    payload: HnpImportRequest,
    db: Session = Depends(get_db_with_request_state),
    user=Depends(require_tenant_user),
):
    tenant_id = _tenant_id_uuid(user)
    user_id = getattr(user, "user_id", None)

    if not payload.raw_text or not payload.raw_text.strip():
        raise HTTPException(400, "raw_text is required")

    try:
        summary = build_hnp_summary(payload.raw_text)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc

    if payload.patient_id:
        patient = (
            db.query(Patient)
            .filter(Patient.id == uuid.UUID(str(payload.patient_id)), Patient.tenant_id == tenant_id)
            .first()
        )
    else:
        patient = (
            db.query(Patient)
            .filter(
                Patient.tenant_id == tenant_id,
                Patient.date_of_birth == date.fromisoformat(summary["date_of_birth"]),
            )
            .filter(
                (Patient.mrn == summary["mrn"]) |
                (
                    Patient.id.in_(
                        db.query(PatientFaceSheet.patient_id)
                        .filter(
                            PatientFaceSheet.tenant_id == tenant_id,
                            PatientFaceSheet.first_name.ilike(summary["first_name"]),
                            PatientFaceSheet.last_name.ilike(summary["last_name"]),
                        )
                    )
                )
            )
            .first()
        )

    if patient is None:
        patient_id = uuid.uuid4()
        now = datetime.now(timezone.utc)
        patient = Patient(
            id=patient_id,
            tenant_id=tenant_id,
            mrn=summary["mrn"],
            date_of_birth=date.fromisoformat(summary["date_of_birth"]),
            primary_diagnosis=summary["primary_diagnosis"] or "Diagnosis pending",
            admission_status="REFERRAL",
            status="PENDING",
            acuity_state="ROUTINE",
            created_by=user_id,
            created_at=now,
        )
        db.add(patient)

        facesheet = PatientFaceSheet(
            tenant_id=tenant_id,
            patient_id=patient_id,
            first_name=summary["first_name"],
            middle_name=None,
            last_name=summary["last_name"],
            dob=date.fromisoformat(summary["date_of_birth"]),
            phone=summary.get("phone"),
            address=summary.get("address"),
            gender=summary.get("sex"),
            primary_diagnosis=summary["primary_diagnosis"] or "Diagnosis pending",
            created_by=user_id,
            updated_by=user_id,
            updated_at=now,
        )
        db.add(facesheet)

        diagnosis = PatientDiagnosis(
            tenant_id=tenant_id,
            patient_id=patient_id,
            diagnosis_type=DiagnosisType.PRIMARY,
            status=DiagnosisStatus.ACTIVE,
            source=DiagnosisSource.REFERRAL,
            icd10_code="N/A",
            diagnosis_description=summary["primary_diagnosis"] or "Diagnosis pending",
            display_name=summary["primary_diagnosis"] or "Diagnosis pending",
            active=True,
            is_terminal=True,
            is_related_to_terminal=True,
            effective_date=date.today(),
            created_by=user_id,
        )
        db.add(diagnosis)

        admission = Admission(
            tenant_id=tenant_id,
            patient_id=patient_id,
            status="PENDING",
            admission_date=now.replace(tzinfo=None),
            created_at=now.replace(tzinfo=None),
            created_by=user_id,
        )
        db.add(admission)

    else:
        patient.primary_diagnosis = summary["primary_diagnosis"] or patient.primary_diagnosis
        patient.date_of_birth = date.fromisoformat(summary["date_of_birth"])
        if not patient.mrn:
            patient.mrn = summary["mrn"]
        patient.updated_at = datetime.now(timezone.utc)

        facesheet = (
            db.query(PatientFaceSheet)
            .filter(
                PatientFaceSheet.patient_id == patient.id,
                PatientFaceSheet.tenant_id == tenant_id,
            )
            .first()
        )
        if facesheet is None:
            facesheet = PatientFaceSheet(
                tenant_id=tenant_id,
                patient_id=patient.id,
                first_name=summary["first_name"],
                last_name=summary["last_name"],
                dob=date.fromisoformat(summary["date_of_birth"]),
                phone=summary.get("phone"),
                address=summary.get("address"),
                gender=summary.get("sex"),
                primary_diagnosis=summary["primary_diagnosis"] or patient.primary_diagnosis,
                created_by=user_id,
                updated_by=user_id,
                updated_at=datetime.now(timezone.utc),
            )
            db.add(facesheet)
        else:
            facesheet.first_name = summary["first_name"] or facesheet.first_name
            facesheet.last_name = summary["last_name"] or facesheet.last_name
            facesheet.dob = date.fromisoformat(summary["date_of_birth"])
            facesheet.phone = summary.get("phone") or facesheet.phone
            facesheet.address = summary.get("address") or facesheet.address
            facesheet.gender = summary.get("sex") or facesheet.gender
            facesheet.primary_diagnosis = summary["primary_diagnosis"] or facesheet.primary_diagnosis
            facesheet.updated_by = user_id
            facesheet.updated_at = datetime.now(timezone.utc)

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise

    return {
        "id": str(patient.id),
        "mrn": patient.mrn,
        "first_name": summary["first_name"],
        "last_name": summary["last_name"],
        "date_of_birth": patient.date_of_birth,
        "primary_diagnosis": patient.primary_diagnosis,
        "source": payload.source_name or "HNP",
        "updated_from_hnp": True,
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

    # HOPE A1400 payer source category (Medicare / Medicare Advantage /
    # Medicaid-Medi-Cal / Medicaid-Medi-Cal Managed Care / Private-Managed
    # Care / Other Government / Self Pay / No Payer Source). Distinct from
    # the free-text payer name; see PAYER_SOURCE_TYPES for allowed values.
    primary_payer_type: str | None = None

    primary_policy_number: str | None = None

    mbi_number: str | None = None

    # ==================================================
    # ✅ SECONDARY COVERAGE
    # ==================================================

    secondary_payer: str | None = None

    secondary_payer_type: str | None = None

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

    diagnosis_entries: list[dict] | None = None

    has_allergies: bool | None = None

    allergies: str | None = None

    # ==================================================
    # ✅ HOSPICE DATES
    # ==================================================

    ref_date: date | None = None

    recert_date: date | None = None

    election_date: date | None = None

    face_to_face_due_date: date | None = None

    # ==================================================
    # ✅ BENEFIT PERIOD
    # ==================================================

    benefit_period_number: str | None = None

    benefit_period_start: date | None = None

    benefit_period_end: date | None = None

    # ==================================================
    # ✅ HOSPICE SNAPSHOT
    # ==================================================

    pps_score: str | None = None

    kps_score: str | None = None

    fast_stage: str | None = None

    code_status: str | None = None

    cti_status: str | None = None

    noe_status: str | None = None

    primary_rn_name: str | None = None

    social_worker_name: str | None = None

    # ==================================================
    # ✅ CARE TEAM
    # ==================================================

    lvn_name: str | None = None

    chaplain_name: str | None = None

    chha_name: str | None = None

    volunteer_name: str | None = None

    clinical_manager_name: str | None = None

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

    attending_physician_address: str | None = None

    attending_physician_phone: str | None = None

    attending_physician_fax: str | None = None

    attending_physician_npi: str | None = None

    attending_physician_following: bool | None = None

    # ==================================================
    # ✅ HOSPICE MEDICAL DIRECTOR
    # ==================================================

    medical_director_name: str | None = None

    medical_director_address: str | None = None

    medical_director_phone: str | None = None

    medical_director_fax: str | None = None

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
    # ✅ OXYGEN
    # ==================================================

    oxygen_vendor_name: str | None = None

    oxygen_vendor_phone: str | None = None

    oxygen_vendor_emergency_phone: str | None = None

    # ==================================================
    # ✅ MORTUARY
    # ==================================================

    mortuary_name: str | None = None

    mortuary_phone: str | None = None

    mortuary_prearranged: bool | None = None

    mortuary_contact_name: str | None = None

    mortuary_contact_phone: str | None = None

    mortuary_notes: str | None = None

    # ==================================================
    # ✅ SPECIAL INSTRUCTIONS
    # ==================================================

    special_instructions: str | None = None


class PosHistoryCreate(BaseModel):
    pos_type: str
    pos_name: str | None = None
    pos_address: str | None = None
    room_number: str | None = None
    start_date: date
    end_date: date | None = None
    reason: str | None = None


class PosHistoryUpdate(BaseModel):
    pos_type: str | None = None
    pos_name: str | None = None
    pos_address: str | None = None
    room_number: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    reason: str | None = None


def _serialize_pos_history_entry(
    entry: PatientPOS,
    *,
    today: date | None = None,
) -> dict:
    reference_day = today or date.today()
    is_current = (
        entry.effective_date is not None
        and entry.effective_date <= reference_day
        and (entry.end_date is None or entry.end_date >= reference_day)
    )

    return {
        "id": str(entry.id),
        "pos_type": entry.pos_type,
        "pos_name": entry.facility_name,
        "pos_address": entry.pos_address,
        "room_number": entry.room_number,
        "start_date": entry.effective_date,
        "end_date": entry.end_date,
        "reason": entry.notes,
        "status": entry.status,
        "is_current": is_current,
        "created_at": entry.created_at,
        "updated_at": entry.updated_at,
    }


def _get_current_pos_history_entry(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    patient_id: uuid.UUID,
    today: date | None = None,
) -> PatientPOS | None:
    reference_day = today or date.today()
    return (
        db.query(PatientPOS)
        .filter(
            PatientPOS.tenant_id == tenant_id,
            PatientPOS.patient_id == patient_id,
            PatientPOS.effective_date <= reference_day,
            (PatientPOS.end_date.is_(None)) | (PatientPOS.end_date >= reference_day),
        )
        .order_by(
            PatientPOS.effective_date.desc(),
            PatientPOS.created_at.desc(),
        )
        .first()
    )


def _sync_facesheet_current_pos_from_history(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    patient_id: uuid.UUID,
    actor_id: uuid.UUID | None = None,
) -> None:
    facesheet = (
        db.query(PatientFaceSheet)
        .filter(
            PatientFaceSheet.patient_id == patient_id,
            PatientFaceSheet.tenant_id == tenant_id,
        )
        .first()
    )

    if not facesheet:
        return

    current_entry = _get_current_pos_history_entry(
        db,
        tenant_id=tenant_id,
        patient_id=patient_id,
    )

    if current_entry:
        facesheet.current_pos_type = current_entry.pos_type
        facesheet.current_pos_name = current_entry.facility_name
        facesheet.current_pos_address = current_entry.pos_address
        facesheet.room_number = current_entry.room_number
        facesheet.pos_start_date = current_entry.effective_date
        facesheet.pos_end_date = current_entry.end_date
    else:
        facesheet.current_pos_type = None
        facesheet.current_pos_name = None
        facesheet.current_pos_address = None
        facesheet.room_number = None
        facesheet.pos_start_date = None
        facesheet.pos_end_date = None

    facesheet.updated_at = datetime.now(timezone.utc)
    if actor_id is not None:
        facesheet.updated_by = actor_id

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

    patient = get_authorized_patient(db, patient_id, user)

    user_id = getattr(user, "user_id", None)

    if not user_id:
        raise HTTPException(500, "Invalid user identity")

    facesheet = (
        db.query(PatientFaceSheet)
        .filter(
            PatientFaceSheet.patient_id == patient.id,
            PatientFaceSheet.tenant_id == tenant_id
        )
        .first()
    )

    data = payload.model_dump(exclude_unset=True)
    
    if facesheet:
        if "first_name" in data:
            facesheet.first_name = data["first_name"]
        if "middle_name" in data:
            facesheet.middle_name = data["middle_name"]
        if "last_name" in data:
            facesheet.last_name = data["last_name"]
        facesheet.updated_by = user_id
        facesheet.updated_at = datetime.now(timezone.utc)

    if not facesheet:
        facesheet = PatientFaceSheet(
            patient_id=patient.id,
            tenant_id=tenant_id,
            created_by=str(user_id),
        )
        db.add(facesheet)

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

    facesheet.updated_by = user_id
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
    # --------------------------------------------------
    # ✅ TENANT CONTEXT
    # --------------------------------------------------
    tenant_id = _tenant_id_uuid(user)
    patient = get_authorized_patient(db, patient_id, user)

    # --------------------------------------------------
    # ✅ LOAD FACE SHEET (STRICT TENANT ISOLATION)
    # --------------------------------------------------
    facesheet = (
        db.query(PatientFaceSheet)
        .filter(
            PatientFaceSheet.patient_id == patient.id,
            PatientFaceSheet.tenant_id == tenant_id
        )
        .first()
    )

    # --------------------------------------------------
    # ✅ HARD DATA INTEGRITY ENFORCEMENT
    # --------------------------------------------------
    if not facesheet:
        raise HTTPException(
            status_code=500,
            detail="Facesheet integrity error: record missing",
        )

    # --------------------------------------------------
    # ✅ SHARED CODE STATUS (authoritative, cross-module)
    # --------------------------------------------------
    current_code_status_row = get_current_code_status(db, patient_id=patient.id, tenant_id=tenant_id)
    current_code_status = (
        {
            "code_status_id": str(current_code_status_row.id),
            "code_status": current_code_status_row.code_status,
            "display_label": CODE_STATUS_DISPLAY_LABELS.get(
                current_code_status_row.code_status, current_code_status_row.code_status
            ),
            "effective_date": (
                current_code_status_row.effective_date.isoformat()
                if current_code_status_row.effective_date
                else None
            ),
            "source": current_code_status_row.source,
            "notes": current_code_status_row.notes,
            "created_at": (
                current_code_status_row.created_at.isoformat()
                if current_code_status_row.created_at
                else None
            ),
        }
        if current_code_status_row
        else None
    )

    # --------------------------------------------------
    # ✅ SHARED PHYSICIAN ASSIGNMENTS (authoritative, cross-module)
    # --------------------------------------------------
    physician_assignments = get_physician_assignments(db, patient_id=patient.id, tenant_id=tenant_id)

    def _physician_dict(role: str, legacy_name, legacy_address=None, legacy_phone=None, legacy_fax=None, legacy_npi=None, legacy_following=None):
        row = physician_assignments.get(role)
        if row is not None:
            return {
                "name": row.name if row.name is not None else legacy_name,
                "address": row.address if row.address is not None else legacy_address,
                "phone": row.phone if row.phone is not None else legacy_phone,
                "fax": row.fax if row.fax is not None else legacy_fax,
                "npi": row.npi if row.npi is not None else legacy_npi,
                "following": row.will_follow_in_hospice if row.will_follow_in_hospice is not None else legacy_following,
                "source": row.source,
                "updated_at": row.updated_at.isoformat() if row.updated_at else None,
            }
        # No shared row yet - fall back to legacy facesheet-only values.
        return {
            "name": legacy_name,
            "address": legacy_address,
            "phone": legacy_phone,
            "fax": legacy_fax,
            "npi": legacy_npi,
            "following": legacy_following,
            "source": None,
            "updated_at": None,
        }

    # --------------------------------------------------
    # ✅ SHARED CAREGIVER / DECISION-MAKER CONTACTS (authoritative, cross-module)
    # --------------------------------------------------
    patient_contacts = get_patient_contacts(db, patient_id=patient.id, tenant_id=tenant_id)

    def _contact_dict(role: str, legacy_name=None, legacy_relationship=None, legacy_phone=None):
        row = patient_contacts.get(role)
        if row is not None:
            return {
                "name": row.name if row.name is not None else legacy_name,
                "relationship": row.relationship_to_patient if row.relationship_to_patient is not None else legacy_relationship,
                "phone": row.phone if row.phone is not None else legacy_phone,
                "source": row.source,
                "updated_at": row.updated_at.isoformat() if row.updated_at else None,
            }
        # No shared row yet - fall back to legacy facesheet-only values.
        return {
            "name": legacy_name,
            "relationship": legacy_relationship,
            "phone": legacy_phone,
            "source": None,
            "updated_at": None,
        }

    # --------------------------------------------------
    # ✅ DIAGNOSIS SUMMARY
    # --------------------------------------------------
    diagnosis_summary = _get_diagnosis_summary_payload(
        db,
        tenant_id=tenant_id,
        patient_id=patient.id,
    )
    
    active_admission = _get_active_admission(
        db,
        tenant_id=tenant_id,
        patient_id=patient.id,
    )

    care_team_assignments = _get_care_team_assignments(
        db,
        tenant_id=tenant_id,
        patient_id=patient.id,
    )

    benefit_period_schedule = _compute_benefit_period_schedule(
        facesheet.election_date
    )

    # --------------------------------------------------
    # ✅ CANONICAL PATIENT NAME (REQUIRED)
    # --------------------------------------------------
    patient_name = " ".join(
        part for part in [
            facesheet.first_name,
            facesheet.middle_name,
            facesheet.last_name,
        ] if part
    )

    if not patient_name:
        patient_name = "IDENTITY_MISSING"

    # --------------------------------------------------
    # ✅ STRUCTURED RESPONSE (ENTERPRISE CONTRACT)
    # --------------------------------------------------
    return {
        "patient_id": str(patient.id),
        "mrn": patient.mrn,
        
        "identity": {
            "first_name": facesheet.first_name,
            "middle_name": facesheet.middle_name or None,
            "last_name": facesheet.last_name,
            "dob": facesheet.dob,
            "ssn": facesheet.ssn,
            "gender": facesheet.gender,
            "race": facesheet.race,
            "ethnicity": facesheet.ethnicity,
            "language": facesheet.language,
            "religion": facesheet.religion,
            "marital_status": facesheet.marital_status,
            "phone": facesheet.phone,
        },

        "address": {
            "address": facesheet.address,
            "city": facesheet.city,
            "state": facesheet.state,
            "zip": facesheet.zip,
        },

        "insurance": {
            "primary_payer": facesheet.primary_payer,
            "primary_payer_type": facesheet.primary_payer_type,
            "primary_policy_number": facesheet.primary_policy_number,
            "mbi_number": facesheet.mbi_number,
            "secondary_payer": facesheet.secondary_payer,
            "secondary_payer_type": facesheet.secondary_payer_type,
            "secondary_policy_number": facesheet.secondary_policy_number,
        },

        "authorization": {
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
        },

        "clinical": {
            "primary_diagnosis": facesheet.primary_diagnosis,
            "secondary_diagnoses": facesheet.secondary_diagnoses,
            "diagnosis_entries": facesheet.diagnosis_entries,
            "diagnoses": diagnosis_summary,
            "active_primary_diagnosis":
                diagnosis_summary["primary"],
            "active_secondary_diagnoses":
                diagnosis_summary["secondary"],
            "active_comorbidities":
                diagnosis_summary["comorbidities"],
            "has_allergies": facesheet.has_allergies,
            "allergies": facesheet.allergies,
        },

        "level_of_care": {
            "current_level_of_care":
                facesheet.current_level_of_care,
            "loc_effective_date":
                facesheet.loc_effective_date,
        },

        "place_of_service": {
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
        },

        "contacts": {
            "responsible_party": _contact_dict(
                RESPONSIBLE_PARTY,
                facesheet.responsible_party_name,
                facesheet.responsible_party_relationship,
                facesheet.responsible_party_phone,
            ),
            "emergency_contact": _contact_dict(
                EMERGENCY_CONTACT,
                facesheet.emergency_contact_name,
                facesheet.emergency_contact_relationship,
                facesheet.emergency_contact_phone,
            ),
            "primary_caregiver": _contact_dict("PRIMARY_CAREGIVER"),
            "dpoa": _contact_dict("DPOA"),
            "healthcare_agent": _contact_dict("HEALTHCARE_AGENT"),
            "decision_maker": _contact_dict("DECISION_MAKER"),
        },

        "physicians": {
            "attending": _physician_dict(
                ATTENDING,
                facesheet.attending_physician_name,
                facesheet.attending_physician_address,
                facesheet.attending_physician_phone,
                facesheet.attending_physician_fax,
                facesheet.attending_physician_npi,
                facesheet.attending_physician_following,
            ),
            "medical_director": _physician_dict(
                MEDICAL_DIRECTOR,
                facesheet.medical_director_name,
                facesheet.medical_director_address,
                facesheet.medical_director_phone,
                facesheet.medical_director_fax,
                facesheet.medical_director_npi,
            ),
            "medical_director_designee": {
                "name":
                    facesheet.medical_director_designee_name,
                "npi":
                    facesheet.medical_director_designee_npi,
            },
            "associate_medical_director": _physician_dict(
                ASSOCIATE_MEDICAL_DIRECTOR,
                facesheet.associate_medical_director_name,
                legacy_npi=facesheet.associate_medical_director_npi,
            ),
        },

        "vendors": {
            "pharmacy": {
                "name": facesheet.pharmacy_name,
                "phone": facesheet.pharmacy_phone,
                "fax": facesheet.pharmacy_fax,
            },
            "dme": {
                "name": facesheet.dme_vendor_name,
                "phone": facesheet.dme_vendor_phone,
            },
            "oxygen": {
                "name": facesheet.oxygen_vendor_name,
                "phone": facesheet.oxygen_vendor_phone,
                "emergency_phone": facesheet.oxygen_vendor_emergency_phone,
            },
            "mortuary": {
                "name": facesheet.mortuary_name,
                "phone": facesheet.mortuary_phone,
                "prearranged": facesheet.mortuary_prearranged,
                "contact_name": facesheet.mortuary_contact_name,
                "contact_phone": facesheet.mortuary_contact_phone,
                "notes": facesheet.mortuary_notes,
            },
        },

        "service_dates": {
            "admission_status": active_admission.status if active_admission else "PENDING",
            "soc_date": active_admission.soc_date if active_admission else None,
            "effective_date": active_admission.effective_date if active_admission else None,
            "admission_date": active_admission.admission_date if active_admission else None,
            "ref_date": facesheet.ref_date,
            "recert_date": facesheet.recert_date,
            "election_date": facesheet.election_date,
            "face_to_face_due_date": facesheet.face_to_face_due_date,
        },

        "benefit_period": {
            "benefit_period_number": facesheet.benefit_period_number,
            "benefit_period_start": facesheet.benefit_period_start,
            "benefit_period_end": facesheet.benefit_period_end,
            "auto_calculated": benefit_period_schedule,
        },

        "hospice_snapshot": {
            "pps_score": facesheet.pps_score,
            "kps_score": facesheet.kps_score,
            "fast_stage": facesheet.fast_stage,
            "code_status": (
                current_code_status["display_label"]
                if current_code_status
                else facesheet.code_status
            ),
            "code_status_detail": current_code_status,
            "cti_status": facesheet.cti_status,
            "noe_status": facesheet.noe_status,
        },

        "care_team": {
            "primary_rn_name": facesheet.primary_rn_name,
            "lvn_name": facesheet.lvn_name,
            "social_worker_name": facesheet.social_worker_name,
            "chaplain_name": facesheet.chaplain_name,
            "chha_name": facesheet.chha_name,
            "volunteer_name": facesheet.volunteer_name,
            "clinical_manager_name": facesheet.clinical_manager_name,
            "assignments": care_team_assignments,
        },

        "notes": {
            "special_instructions":
                facesheet.special_instructions,
        },
    }


@router.get("/{patient_id}/pos-history")
def get_patient_pos_history(
    patient_id: uuid.UUID,
    db: Session = Depends(get_db_with_request_state),
    user=Depends(require_tenant_user),
):
    tenant_id = _tenant_id_uuid(user)

    patient = get_authorized_patient(db, patient_id, user)

    entries = (
        db.query(PatientPOS)
        .filter(
            PatientPOS.patient_id == patient.id,
            PatientPOS.tenant_id == tenant_id,
        )
        .order_by(
            PatientPOS.effective_date.desc(),
            PatientPOS.created_at.desc(),
        )
        .all()
    )

    current_entry = _get_current_pos_history_entry(
        db,
        tenant_id=tenant_id,
        patient_id=patient.id,
    )

    return {
        "patient_id": str(patient.id),
        "current_entry": (
            _serialize_pos_history_entry(current_entry)
            if current_entry
            else None
        ),
        "entries": [
            _serialize_pos_history_entry(entry)
            for entry in entries
        ],
    }


@router.post("/{patient_id}/pos-history")
def create_patient_pos_history(
    patient_id: uuid.UUID,
    payload: PosHistoryCreate,
    db: Session = Depends(get_db_with_request_state),
    user=Depends(require_tenant_user),
):
    tenant_id = _tenant_id_uuid(user)

    patient = get_authorized_patient(db, patient_id, user)

    if payload.end_date and payload.end_date < payload.start_date:
        raise HTTPException(
            status_code=422,
            detail="end_date must be on or after start_date",
        )

    actor_uuid = uuid.UUID(str(user.user_id)) if getattr(user, "user_id", None) else None
    now = datetime.now(timezone.utc)
    today = date.today()
    computed_status = (
        "DISCHARGED"
        if payload.end_date and payload.end_date < today
        else "ACTIVE"
    )

    entry = PatientPOS(
        tenant_id=tenant_id,
        patient_id=patient.id,
        pos_type=payload.pos_type,
        facility_name=payload.pos_name,
        pos_address=payload.pos_address,
        room_number=payload.room_number,
        effective_date=payload.start_date,
        end_date=payload.end_date,
        notes=payload.reason,
        status=computed_status,
        created_by=str(user.user_id),
        updated_by=str(user.user_id),
        updated_at=now,
    )
    db.add(entry)
    db.flush()
    _sync_facesheet_current_pos_from_history(
        db,
        tenant_id=tenant_id,
        patient_id=patient.id,
        actor_id=actor_uuid,
    )
    db.commit()
    db.refresh(entry)

    return _serialize_pos_history_entry(entry)


@router.put("/{patient_id}/pos-history/{entry_id}")
def update_patient_pos_history(
    patient_id: uuid.UUID,
    entry_id: uuid.UUID,
    payload: PosHistoryUpdate,
    db: Session = Depends(get_db_with_request_state),
    user=Depends(require_tenant_user),
):
    tenant_id = _tenant_id_uuid(user)

    patient = get_authorized_patient(db, patient_id, user)

    entry = (
        db.query(PatientPOS)
        .filter(
            PatientPOS.id == entry_id,
            PatientPOS.patient_id == patient.id,
            PatientPOS.tenant_id == tenant_id,
        )
        .first()
    )

    if not entry:
        raise HTTPException(status_code=404, detail="POS history entry not found")

    data = payload.model_dump(exclude_unset=True)

    start_date_value = data.get("start_date", entry.effective_date)
    end_date_value = data.get("end_date", entry.end_date)

    if end_date_value and start_date_value and end_date_value < start_date_value:
        raise HTTPException(
            status_code=422,
            detail="end_date must be on or after start_date",
        )

    if "pos_type" in data:
        entry.pos_type = data["pos_type"]
    if "pos_name" in data:
        entry.facility_name = data["pos_name"]
    if "pos_address" in data:
        entry.pos_address = data["pos_address"]
    if "room_number" in data:
        entry.room_number = data["room_number"]
    if "start_date" in data:
        entry.effective_date = data["start_date"]
    if "end_date" in data:
        entry.end_date = data["end_date"]
    if "reason" in data:
        entry.notes = data["reason"]

    today = date.today()
    entry.status = (
        "DISCHARGED"
        if entry.end_date and entry.end_date < today
        else "ACTIVE"
    )
    entry.updated_at = datetime.now(timezone.utc)
    entry.updated_by = str(user.user_id)

    actor_uuid = uuid.UUID(str(user.user_id)) if getattr(user, "user_id", None) else None
    _sync_facesheet_current_pos_from_history(
        db,
        tenant_id=tenant_id,
        patient_id=patient.id,
        actor_id=actor_uuid,
    )
    db.commit()
    db.refresh(entry)

    return _serialize_pos_history_entry(entry)


# =========================================================
# PATIENT PAYER / INSURANCE (REAL — previously no write path existed
# anywhere in the app; billing engine depends on this table)
# =========================================================

class PatientPayerCreate(BaseModel):
    payer_name: str
    payer_type: str
    subscriber_id: str | None = None
    subscriber_id_type: str | None = None
    facility_name: str | None = None
    effective_start_date: date | None = None
    end_date: date | None = None
    is_primary: bool = True


class PatientPayerUpdate(BaseModel):
    payer_name: str | None = None
    payer_type: str | None = None
    subscriber_id: str | None = None
    subscriber_id_type: str | None = None
    facility_name: str | None = None
    effective_start_date: date | None = None
    end_date: date | None = None
    is_primary: bool | None = None


def _serialize_patient_payer(entry: PatientPayer) -> dict:
    return {
        "id": str(entry.id),
        "patient_id": str(entry.patient_id),
        "payer_name": entry.payer_name,
        "payer_type": entry.payer_type,
        "subscriber_id": entry.subscriber_id,
        "subscriber_id_type": entry.subscriber_id_type,
        "facility_name": entry.facility_name,
        "effective_start_date": str(entry.effective_start_date) if entry.effective_start_date else None,
        "end_date": str(entry.end_date) if entry.end_date else None,
        "is_primary": entry.is_primary,
        "created_at": entry.created_at.isoformat() if entry.created_at else None,
    }


@router.get("/{patient_id}/payers")
def list_patient_payers(
    patient_id: uuid.UUID,
    db: Session = Depends(get_db_with_request_state),
    user=Depends(require_tenant_user),
):
    patient = get_authorized_patient(db, patient_id, user)

    entries = (
        db.query(PatientPayer)
        .filter(PatientPayer.patient_id == patient.id)
        .order_by(
            PatientPayer.is_primary.desc().nullslast(),
            PatientPayer.effective_start_date.desc(),
        )
        .all()
    )

    return [_serialize_patient_payer(entry) for entry in entries]


@router.post("/{patient_id}/payers")
def create_patient_payer(
    patient_id: uuid.UUID,
    payload: PatientPayerCreate,
    db: Session = Depends(get_db_with_request_state),
    user=Depends(require_tenant_user),
):
    patient = get_authorized_patient(db, patient_id, user)

    if (
        payload.end_date
        and payload.effective_start_date
        and payload.end_date < payload.effective_start_date
    ):
        raise HTTPException(
            status_code=422,
            detail="end_date must be on or after effective_start_date",
        )

    actor_uuid = uuid.UUID(str(user.user_id)) if getattr(user, "user_id", None) else None

    if payload.is_primary:
        # Only one primary payer per patient at a time — mirrors real
        # coordination-of-benefits behavior, avoids ambiguous claims.
        db.query(PatientPayer).filter(
            PatientPayer.patient_id == patient.id,
            PatientPayer.is_primary.is_(True),
        ).update({"is_primary": False}, synchronize_session=False)

    entry = PatientPayer(
        id=uuid.uuid4(),
        patient_id=patient.id,
        payer_name=payload.payer_name,
        payer_type=payload.payer_type,
        subscriber_id=payload.subscriber_id,
        subscriber_id_type=payload.subscriber_id_type,
        facility_name=payload.facility_name,
        effective_start_date=payload.effective_start_date,
        end_date=payload.end_date,
        is_primary=payload.is_primary,
        created_by=actor_uuid,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)

    return _serialize_patient_payer(entry)


@router.put("/{patient_id}/payers/{payer_id}")
def update_patient_payer(
    patient_id: uuid.UUID,
    payer_id: uuid.UUID,
    payload: PatientPayerUpdate,
    db: Session = Depends(get_db_with_request_state),
    user=Depends(require_tenant_user),
):
    patient = get_authorized_patient(db, patient_id, user)

    entry = (
        db.query(PatientPayer)
        .filter(
            PatientPayer.id == payer_id,
            PatientPayer.patient_id == patient.id,
        )
        .first()
    )

    if not entry:
        raise HTTPException(status_code=404, detail="Payer not found")

    data = payload.model_dump(exclude_unset=True)

    start_date_value = data.get("effective_start_date", entry.effective_start_date)
    end_date_value = data.get("end_date", entry.end_date)

    if end_date_value and start_date_value and end_date_value < start_date_value:
        raise HTTPException(
            status_code=422,
            detail="end_date must be on or after effective_start_date",
        )

    if data.get("is_primary"):
        db.query(PatientPayer).filter(
            PatientPayer.patient_id == patient.id,
            PatientPayer.id != entry.id,
            PatientPayer.is_primary.is_(True),
        ).update({"is_primary": False}, synchronize_session=False)

    for field in (
        "payer_name",
        "payer_type",
        "subscriber_id",
        "subscriber_id_type",
        "facility_name",
        "effective_start_date",
        "end_date",
        "is_primary",
    ):
        if field in data:
            setattr(entry, field, data[field])

    entry.updated_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(entry)

    return _serialize_patient_payer(entry)


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

    patient = get_authorized_patient(db, patient_id, user)

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

    latest_admission = _get_latest_admission(
        db,
        tenant_id=tenant_id,
        patient_id=patient.id,
    )

    return {
        "id": str(patient.id),
        "mrn": patient.mrn,
        "date_of_birth": patient.date_of_birth,
        "primary_diagnosis": patient.primary_diagnosis,
        "status": patient.status,
        "admission_status": latest_admission.status if latest_admission else "PENDING",
        "created_at": patient.created_at,
        "updated_at": patient.updated_at,
    }

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
# Retired. Admission is owned by app/api/admissions.py, which enforces the
# RN primary-diagnosis and diagnosis-discrepancy gates before admitting.

# =========================================================
# NON ADMIT
# =========================================================
# Retired. Non-admit is owned by app/api/admission.py, which requires a
# reason and records the transition through AdmissionWorkflowService.

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

    if task.patient_id:
        get_authorized_patient(db, task.patient_id, user)
    
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

    patient = get_authorized_patient(db, patient_id, user)
    
    facesheet = (
        db.query(PatientFaceSheet)
        .filter(
            PatientFaceSheet.patient_id == patient.id,
            PatientFaceSheet.tenant_id == tenant_id
        )
        .first()
    )
    
    diagnosis_summary = _get_diagnosis_summary_payload(
        db,
        tenant_id=tenant_id,
        patient_id=patient.id,
    )
    
    active_admission = _get_active_admission(
        db,
        tenant_id=tenant_id,
        patient_id=patient.id,
    )
        
    visits = db.query(Visit).filter(
        Visit.patient_id == patient_id,
        Visit.tenant_id == tenant_id
    ).order_by(Visit.visit_datetime.desc()).all()

    return {
            "patient": {
            "id": str(patient.id),
            "mrn": patient.mrn,
            "date_of_birth": patient.date_of_birth,
            "primary_diagnosis": patient.primary_diagnosis,
            "status": patient.status,
            "admission_status": active_admission.status if active_admission else "PENDING",
            "soc_date": active_admission.soc_date if active_admission else None,
            "effective_date": active_admission.effective_date if active_admission else None,
            "admission_date": active_admission.admission_date if active_admission else None,
            "created_at": patient.created_at,
            "updated_at": patient.updated_at,
        },

        "diagnoses": diagnosis_summary,

        "facesheet": {
            # -----------------------------------------
            # COVERAGE
            # -----------------------------------------
            "primary_payer": getattr(facesheet, "primary_payer", None),
            "primary_payer_type": getattr(facesheet, "primary_payer_type", None),
            "primary_policy_number": getattr(facesheet, "primary_policy_number", None),
            "secondary_payer": getattr(facesheet, "secondary_payer", None),
            "secondary_payer_type": getattr(facesheet, "secondary_payer_type", None),
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


def _num(value):
    """Best-effort numeric coercion; returns None for blank/non-numeric values."""
    if value is None or value == "":
        return None
    if isinstance(value, str):
        cleaned = value.strip().replace(",", "")
        if cleaned.endswith("%"):
            cleaned = cleaned[:-1].strip()
        value = cleaned
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _adl_summary(form_data):
    adl = ((form_data.get("musculoskeletal") or {}).get("adl")) or {}
    adl_scores = [_num(v) for v in adl.values()]
    adl_scores = [v for v in adl_scores if v is not None]
    return {
        "adl_scores": adl_scores,
        "adl_score": sum(adl_scores) if adl_scores else None,
        "adl_dependency_count": sum(1 for v in adl_scores if v >= 3) if adl_scores else None,
    }


def _calculate_bmi(vitals):
    saved_bmi = _num((vitals or {}).get("bmi"))
    if saved_bmi is not None:
        return saved_bmi
    height = _num((vitals or {}).get("height"))
    weight = _num((vitals or {}).get("weight"))
    if height is None or weight is None or height <= 0:
        return None
    return round((703 * weight / (height * height)), 1)


def _nyha_numeric(value):
    mapping = {"I": 1, "II": 2, "III": 3, "IV": 4}
    return mapping.get(str(value or "").strip().upper())


def _fast_numeric(value):
    raw = str(value or "").strip().lower()
    if not raw:
        return None
    scale = {
        "1": 1.0,
        "2": 2.0,
        "3": 3.0,
        "4": 4.0,
        "5": 5.0,
        "6a": 6.1,
        "6b": 6.2,
        "6c": 6.3,
        "6d": 6.4,
        "6e": 6.5,
        "7a": 7.1,
        "7b": 7.2,
        "7c": 7.3,
        "7d": 7.4,
        "7e": 7.5,
        "7f": 7.6,
    }
    return scale.get(raw)


def _rnica_trend_point(row: RnicaAssessment) -> dict:
    fd = row.form_data or {}
    perf = fd.get("performanceStatus") or {}
    vitals = fd.get("vitals") or {}
    pain = fd.get("pain") or {}
    adl_summary = _adl_summary(fd)
    visit_meta = fd.get("visitMeta") or {}
    visit_date = str(visit_meta.get("visitDate") or "").strip()
    plotted_date = row.locked_at or row.updated_at or row.created_at
    if visit_date:
        try:
            plotted_date = datetime.fromisoformat(f"{visit_date[:10]}T00:00:00+00:00")
        except ValueError:
            pass
    return {
        "id": str(row.id),
        "assessment_type": "ADMISSION" if (row.assessment_type or "RNICA") == "RNICA" else (row.assessment_type or "RNICA"),
        "status": row.status,
        "date": plotted_date,
        "pps": _num(perf.get("pps")),
        "kps": _num(perf.get("kps")),
        "pain_level": _num((pain.get("painIntensity") or {}).get("current")) or _num(pain.get("painSeverityCategory")),
        "adl_score": adl_summary["adl_score"],
        "adl_dependency_count": adl_summary["adl_dependency_count"],
        "bmi": _calculate_bmi(vitals),
        "mac": _num(vitals.get("mac")),
        "nyha": _nyha_numeric(perf.get("nyha")),
        "nyha_label": perf.get("nyha") or None,
        "fast": _fast_numeric(perf.get("fast")),
        "fast_label": perf.get("fast") or None,
    }


@router.get("/{patient_id}/performance-history")
def get_patient_performance_history(
    patient_id: uuid.UUID,
    db: Session = Depends(get_db_with_request_state),
    user=Depends(require_tenant_user),
):
    """Chronological PPS/KPS/FAST/weight/ADL history across RNICA + RN recert
    assessments, used to compute decline trends for hospice eligibility
    documentation (e.g. the Performance Status card's "change since last
    assessment" panel)."""
    patient = get_authorized_patient(db, patient_id, user)

    history = []

    tenant_id = getattr(patient, "tenant_id", None)

    rnica_rows = (
        db.query(RnicaAssessment)
        .filter(
            RnicaAssessment.patient_id == patient.id,
            (RnicaAssessment.tenant_id == tenant_id) | (RnicaAssessment.tenant_id.is_(None)),
        )
        .order_by(RnicaAssessment.created_at.asc())
        .all()
    )
    for row in rnica_rows:
        fd = row.form_data or {}
        perf = fd.get("performanceStatus") or {}
        adl_summary = _adl_summary(fd)
        history.append({
            "id": str(row.id),
            "source": row.assessment_type or "RNICA",
            "status": row.status,
            "date": row.locked_at or row.updated_at or row.created_at,
            "pps": _num(perf.get("pps")),
            "kps": _num(perf.get("kps")),
            "fast_stage": perf.get("fast") or None,
            "weight": _num((fd.get("vitals") or {}).get("weight")),
            "adl_dependency_count": adl_summary["adl_dependency_count"],
        })

    recert_rows = (
        db.query(RNRecertAssessment)
        .filter(
            RNRecertAssessment.patient_id == patient.id,
            (RNRecertAssessment.tenant_id == tenant_id) | (RNRecertAssessment.tenant_id.is_(None)),
        )
        .order_by(RNRecertAssessment.created_at.asc())
        .all()
    )
    for row in recert_rows:
        history.append({
            "id": str(row.id),
            "source": "RECERT",
            "status": row.status,
            "date": row.finalized_at or row.updated_at or row.created_at,
            "pps": _num(row.pps_score),
            "kps": _num(row.kps_score),
            "fast_stage": row.fast_stage,
            "weight": None,
            "adl_dependency_count": row.adl_dependency_count,
        })

    history.sort(key=lambda h: h["date"] or datetime.min)
    return {"history": history}


@router.get("/{patient_id}/decline-of-status-trend")
def get_patient_decline_of_status_trend(
    patient_id: uuid.UUID,
    from_date: date | None = Query(default=None),
    to_date: date | None = Query(default=None),
    db: Session = Depends(get_db_with_request_state),
    user=Depends(require_tenant_user),
):
    if from_date and to_date and from_date > to_date:
        raise HTTPException(status_code=422, detail="from_date must be on or before to_date")
    patient = get_authorized_patient(db, patient_id, user)
    tenant_id = getattr(patient, "tenant_id", None)
    rows = (
        db.query(RnicaAssessment)
        .filter(
            RnicaAssessment.patient_id == patient.id,
            (RnicaAssessment.tenant_id == tenant_id) | (RnicaAssessment.tenant_id.is_(None)),
            RnicaAssessment.locked.is_(True),
            RnicaAssessment.assessment_type.in_(["RNICA", "UPDATE"]),
        )
        .order_by(RnicaAssessment.locked_at.asc(), RnicaAssessment.created_at.asc())
        .all()
    )
    trend = [_rnica_trend_point(row) for row in rows]
    trend.sort(key=lambda item: item["date"] or datetime.min)
    available_dates = [item["date"].date().isoformat() for item in trend if item.get("date")]
    if from_date or to_date:
        filtered_trend = []
        for item in trend:
            item_date = item.get("date")
            if item_date is None:
                continue
            point_date = item_date.date() if hasattr(item_date, "date") else None
            if point_date is None:
                continue
            if from_date and point_date < from_date:
                continue
            if to_date and point_date > to_date:
                continue
            filtered_trend.append(item)
        trend = filtered_trend

    return {
        "trend": trend,
        "applied_from_date": from_date.isoformat() if from_date else None,
        "applied_to_date": to_date.isoformat() if to_date else None,
        "available_from_date": min(available_dates) if available_dates else None,
        "available_to_date": max(available_dates) if available_dates else None,
    }


@router.get("/{patient_id}/assessment-history")
def get_patient_assessment_history(
    patient_id: uuid.UUID,
    discipline: str | None = Query(default=None),
    assessment_type: str | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    from_date: date | None = Query(default=None),
    to_date: date | None = Query(default=None),
    limit: int = Query(default=200, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    sort_order: str = Query(default="asc", pattern="^(asc|desc)$"),
    db: Session = Depends(get_db_with_request_state),
    user=Depends(require_tenant_user),
):
    if from_date and to_date and from_date > to_date:
        raise HTTPException(status_code=422, detail="from_date must be on or before to_date")
    patient = get_authorized_patient(db, patient_id, user)
    tenant_id = getattr(patient, "tenant_id", None)
    return {
        "patient_id": str(patient.id),
        **list_patient_assessment_history(
            db,
            patient_id=patient.id,
            tenant_id=tenant_id,
            filters=AssessmentHistoryFilters(
                discipline=discipline,
                assessment_type=assessment_type,
                status=status_filter,
                from_date=from_date,
                to_date=to_date,
                limit=limit,
                offset=offset,
                sort_order=sort_order,
            ),
        ),
    }
