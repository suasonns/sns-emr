# app/api/visits.py

from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Set, Generator, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, Request, Response, Security, status
from pydantic import (
    BaseModel,
    Field,
    field_validator,
    ValidationInfo,
)
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.core.security import get_current_user, CurrentUser
from app.core.visit_type_normalizer import normalize_visit_type

from app.models.enums import (
    TaskStatus,
    TaskType,
    VisitFormType,
    CompletionReferenceType,
    TaskOrigin,
    TaskRegulatoryBasis,
)
from app.models.clinical_note import ClinicalNote
from app.models.patient import Patient
from app.models.task import Task
from app.models.visit import Visit
from app.models.med_reconciliation import MedReconciliationItem
from app.models.sfv_requirement import SFVRequirement
from app.models.admission import Admission

from app.services.chha_outcome_service import upsert_chha_outcome
from app.services.diagnosis_sync_service import sync_official_primary_diagnosis
from app.services.audit_logger import log_event
from app.services.bereavement_aggregation_engine import (
    BereavementAggregationEngine,
    BereavementNoteInput,
)
from app.services.dynamic_condition_detection_engine import (
    DynamicConditionDetectionEngine,
    NoteInput,
)
from app.services.refusal_engine import record_refusal
from app.services.task_completion import auto_complete_tasks_for_visit
from app.domain.forms.form_resolution_service import resolve_form_package
from app.services.visit_compliance_guards import (
    enforce_commlog_for_visit_status_change,
)
from app.services.hope_phase_b_engine import (
    complete_sfv_requirement_from_visit,
    process_huv_finalize,
    process_initial_rn_ica_finalize,
)
from app.services.clinical_reasoning_engine import ClinicalReasoningEngine
from app.services.reasoning_result_to_recommendation_service import (
    ReasoningResultToRecommendationService,
)
from app.services.clinical_note_validation_engine import (
    validate_and_trigger_incident,
)

logger = logging.getLogger(__name__)


# =========================================================
# ROUTER
# =========================================================

router = APIRouter(prefix="/visits", tags=["visits"])

# =========================================================
# CONSTANTS
# =========================================================

ALLOWED_VISIT_TYPES: Set[str] = {
    "RN",
    "LVN",
    "NP",
    "PA",
    "MD",
    "SW",
    "CHAPLAIN",
    "AIDE",
    "ADMINISTRATIVE",
}

ALLOWED_STATUS_CHANGES: Set[str] = {
    "MISSED",
    "RESCHEDULED",
}

TELEPHONE_MODES: Set[str] = {
    "TELEPHONE",
    "PHONE",
    "TEL",
    "CALL",
}

VISIT_CORRECTION_WINDOW_HOURS = 72
ALLOWED_REOPEN_ROLES = {"ADMIN", "SUPERVISOR", "DON", "QA", "SYSTEM"}

VISIT_TYPE_ALIASES: dict[str, str] = {
    "SN": "RN",
    "MSW": "SW",
    "BSW": "SW",
    "LCSW": "SW",
    "SC": "CHAPLAIN",
    "CHHA": "AIDE",
}

ISSUE_EVENT_TYPES: Set[str] = {
    "CHANGE_OF_CONDITION",
    "NEW_ORDER",
    "UPDATE_ASSESSMENT",
    "RECERT",
}

GENERIC_NOTE_TYPES: Set[str] = {
    "VISIT",
    "NOTE",
    "FORM",
    "CLINICAL_NOTE",
}

ASSESSMENT_EVENT_FORM_TYPES: Set[str] = {
    VisitFormType.ASSESS.value,
}

MODERATE_OR_SEVERE: Set[str] = {"MODERATE", "SEVERE"}

# =========================================================
# ENGINE SINGLETONS
# =========================================================

condition_engine = DynamicConditionDetectionEngine()
bereavement_engine = BereavementAggregationEngine()
clinical_reasoning_engine = ClinicalReasoningEngine()
reasoning_recommendation_service = ReasoningResultToRecommendationService()

# =========================================================
# DB DEPENDENCY
# =========================================================


def get_db(request: Request) -> Generator[Session, None, None]:
    db = SessionLocal()
    request.state.db = db
    try:
        yield db
    finally:
        db.close()


# =========================================================
# REQUEST / RESPONSE SCHEMAS
# =========================================================

class VisitStatusUpdate(BaseModel):
    status: str = Field(
        ...,
        description="Allowed: MISSED, RESCHEDULED",
    )

    communications_log_id: Optional[uuid.UUID] = Field(
        None,
        description="Required when status is MISSED or RESCHEDULED",
    )

class VisitCreateRequest(BaseModel):
    """
    Enterprise-grade Visit Create Request

    Key Design:
    - service_type = WHAT (SN, MSW, CHAPLAIN)
    - visit_type = WHO (RN, LVN, SW, etc.)
    """

    # =========================================================
    # REQUIRED CORE
    # =========================================================
    patient_id: uuid.UUID = Field(
        ...,
        description="Patient identifier",
    )

    # ✅ WHO performed the visit
    visit_type: str = Field(
        ...,
        description="Discipline: RN, LVN, SW, CHAPLAIN, AIDE, MD, NP, PA, ADMINISTRATIVE",
    )

    # ✅ WHAT service category (CRITICAL FIX)
    service_type: Optional[str] = Field(
        default="SN",
        description="Service classification: SN (Skilled Nursing), MSW, CHAPLAIN, AIDE",
    )

    # =========================================================
    # WORKFLOW / FORM ENGINE
    # =========================================================
    form_type: Optional[str] = Field(
        None,
        description=(
            "Workflow selector: "
            "ASSESS, PRE_ADMIT_EVAL, SHORT_FORM, SUPV_VISIT_ONLY, "
            "ON_CALL_TRIAGE, MISSED_VISIT, DECLINED_VISIT, "
            "ANCILLARY_SUPPORT, VOLUNTEER_SUPPORT, RESPITE_RELIEF, "
            "BEREAVEMENT_VISIT, DEATH_VISIT, AFTER_DEATH, "
            "AFTER_HOURS, OFFICE_HOURS, WEEKENDS, ROUTINE_VISIT"
        ),
    )

    # =========================================================
    # CLINICAL CONTEXT
    # =========================================================
    level_of_care: Optional[str] = Field(
        None,
        description="Hospice LOC: RC, CC, IP, RSP (accepts CMS strings via normalization)",
    )

    visit_schedule_type: Optional[str] = Field(
        None,
        description="SCHEDULED or UNSCHEDULED",
    )

    event_type: Optional[str] = Field(
        None,
        description=(
            "Optional event trigger: "
            "CHANGE_OF_CONDITION, NEW_ORDER, UPDATE_ASSESSMENT, RECERT"
        ),
    )

    clinical_note: Optional[dict[str, Any]] = Field(
        default=None,
        description="Full ROS assessment structure including issues and POC",
    )

    # =========================================================
    # ✅ VALIDATIONS (ENTERPRISE CRITICAL)
    # =========================================================

    @field_validator("visit_type", mode="before")
    @classmethod
    def normalize_visit_type(cls, value: str) -> str:
        if not value:
            raise ValueError("visit_type is required")

        v = value.strip().upper()

        mapping = {
            "SN": "RN",   # ⚠️ fallback only — will be validated below
            "NURSE": "RN",
            "REGISTERED_NURSE": "RN",

            "MSW": "SW",
            "LCSW": "SW",
            "BSW": "SW",

            "SC": "CHAPLAIN",
            "CHHA": "AIDE",
        }

        return mapping.get(v, v)

    @field_validator("service_type", mode="before")
    @classmethod
    def normalize_service_type(cls, value: Optional[str]) -> str:
        if not value:
            return "SN"

        v = value.strip().upper()

        mapping = {
            "SKILLED_NURSING": "SN",
            "NURSING": "SN",
            "SOCIAL_WORK": "MSW",
            "SPIRITUAL": "CHAPLAIN",
        }

        return mapping.get(v, v)

    @field_validator("level_of_care", mode="before")
    @classmethod
    def normalize_level_of_care(cls, value: Optional[str]) -> Optional[str]:
        if not value:
            return None

        v = value.strip().upper()

        mapping = {
            "ROUTINE_HOME_CARE": "RC",
            "CONTINUOUS_HOME_CARE": "CC",
            "GENERAL_INPATIENT": "IP",
            "INPATIENT_RESPITE": "RSP",
        }

        return mapping.get(v, v)

    @field_validator("visit_schedule_type", mode="before")
    @classmethod
    def normalize_schedule(cls, value: Optional[str]) -> Optional[str]:
        if not value:
            return None

        v = value.strip().upper()
        if v not in {"SCHEDULED", "UNSCHEDULED"}:
            raise ValueError(f"Invalid visit_schedule_type {value}")

        return v

    @field_validator("service_type")
    @classmethod
    def validate_service_vs_discipline(
        cls,
        value: str,
        info: ValidationInfo,
    ) -> str:
        discipline = info.data.get("visit_type")

        if value == "SN" and discipline not in {"RN", "LVN"}:
            raise ValueError(
                "Skilled Nursing (SN) visits must be RN or LVN"
            )

        return value

class CHHATaskResultItem(BaseModel):
    section_code: str
    task_code: str
    was_assigned: bool = True
    completed: bool = False
    refused: bool = False
    not_done: bool = False
    observation_code: Optional[str] = None
    result_note: Optional[str] = None


class CHHAOutcomeUpsertRequest(BaseModel):
    poc_reference_id: Optional[uuid.UUID] = None
    tolerance_to_care: str
    condition_during_visit: str
    skin_outcome: str

    pain_or_change_observed: bool = False
    rn_notification_required: bool = False
    rn_notified: bool = False
    rn_notified_name: Optional[str] = None

    caregiver_instruction_provided: bool = False
    caregiver_understanding_confirmed: bool = False

    exception_narrative: Optional[str] = None
    task_results: List[CHHATaskResultItem] = Field(default_factory=list)


class RefusalRequest(BaseModel):
    discipline: str = Field(
        ...,
        description="LVN, CHHA, MSW, SC, RN, MD, NP, PA",
    )

    reason: Optional[str] = Field(
        None,
        description="Optional free-text refusal reason",
    )


class VisitMutationResponse(BaseModel):
    status: str
    visit_id: str
    request_id: str

    completed_task_types: list[str] = Field(
        default_factory=list,
        description="Tasks completed as a result of this action",
    )

    new_status: Optional[str] = None
    communications_log_id: Optional[str] = None


class VisitReopenRequest(BaseModel):
    reason: str = Field(
        ...,
        min_length=5,
        max_length=2000,
        description="Reason for reopening visit",
    )


class VisitCreateResponse(BaseModel):
    visit_id: str
    visit_type: str
    form_type: Optional[str] = None

    form_family: Optional[str] = Field(
        None,
        description="CLINICAL, PSYCHOSOCIAL, SPIRITUAL, SUPPORT, ADMIN",
    )

    primary_form: Optional[str] = None

    attached_forms: List[str] = Field(
        default_factory=list,
        description="Auto-attached forms generated by form engine",
    )

    modules: List[str] = Field(
        default_factory=list,
        description="UI modules required for rendering this form",
    )

    resolved_by: Optional[str] = Field(
        None,
        description="Resolution source: db_engine, event_override, cc_override",
    )

    is_supervisory: bool = False
    supervisory_targets: List[str] = Field(default_factory=list)

    request_id: str


class RefusalResponse(BaseModel):
    status: str
    patient_id: str
    discipline: str

    reason: Optional[str] = None
    refused_at: Optional[str] = None

    request_id: str


# =========================================================
# INTERNAL HELPERS
# =========================================================

def _normalize_and_validate_form_type(raw: Optional[str]) -> str:
    if not raw:
        return VisitFormType.SHORT_FORM.value

    normalized = str(raw).strip().upper()

    try:
        return VisitFormType(normalized).value
    except ValueError:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid form_type '{raw}'. Allowed: {[e.value for e in VisitFormType]}",
        )


def _normalize_schedule_type(raw: Optional[str]) -> Optional[str]:
    if not raw:
        return None
    value = str(raw).strip().upper()
    allowed = {"SCHEDULED", "UNSCHEDULED"}
    if value not in allowed:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid visit_schedule_type '{raw}'. Allowed: {sorted(allowed)}",
        )
    return value


def _normalize_event_type_for_form(
    form_type: str,
    raw: Optional[str],
) -> Optional[str]:

    if not raw:
        return None

    value = str(raw).strip().upper()

    from app.models.enums import VisitEventType

    try:
        return VisitEventType(value).value
    except ValueError:
        raise HTTPException(
            status_code=422,
            detail=(
                f"Invalid event_type '{raw}'. "
                f"Allowed: {[e.value for e in VisitEventType]}"
            ),
        )

    return value

def _normalize_and_validate_visit_type(raw: str) -> str:
    normalized = normalize_visit_type(raw or "")
    if normalized not in ALLOWED_VISIT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid visit_type '{raw}'. Allowed: {sorted(ALLOWED_VISIT_TYPES)}",
        )
    return normalized


def _canonicalize_discipline(raw: str) -> str:
    candidate = str(raw or "").strip().upper()
    candidate = VISIT_TYPE_ALIASES.get(candidate, candidate)
    normalized = normalize_visit_type(candidate)
    normalized = VISIT_TYPE_ALIASES.get(normalized, normalized)
    if normalized not in ALLOWED_VISIT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                f"Invalid visit_type '{raw}'. Allowed: "
                f"{sorted(ALLOWED_VISIT_TYPES | set(VISIT_TYPE_ALIASES.keys()))}"
            ),
        )
    return normalized


def _guard_against_generic_note_type(note_type: Optional[str], request_id: str) -> str:
    value = (note_type or "").strip().upper()
    if not value or value in GENERIC_NOTE_TYPES:
        logger.critical(
            "FORM_ENGINE_RETURNED_GENERIC_NOTE_TYPE",
            extra={
                "note_type": note_type,
                "request_id": request_id,
            },
        )
        raise HTTPException(
            status_code=500,
            detail="Form engine returned a generic note type; registry must be corrected.",
        )
    return value


def _enforce_form_selection_rules(
    *,
    discipline: str,
    form_type: str,
    visit_schedule_type: Optional[str],
    event_type: Optional[str],
) -> None:
    """
    Enforce SNS hospice workflow reality.

    Clinical rules:
    - SW/MSW/BSW/LCSW -> always ROUTINE_VISIT (psychosocial routine form package)
    - RN/LVN SHORT_FORM -> PRN/UNSCHEDULED false alarm only (no issue/event)
    - RN + issue -> ASSESS + UPDATE_ASSESSMENT
    - LVN + issue -> ROUTINE_VISIT (routine SN), never SHORT_FORM
    - LVN change of condition must be escalated operationally (captured later in workflow)
    """
    discipline = _canonicalize_discipline(discipline)
    form_type = _normalize_and_validate_form_type(form_type)
    schedule = _normalize_schedule_type(visit_schedule_type)
    event = event_type

    issue_present = event in ISSUE_EVENT_TYPES
    is_prn = schedule == "UNSCHEDULED"

    if discipline == "SW":
        if form_type != VisitFormType.ROUTINE_VISIT.value:
            raise HTTPException(
                status_code=422,
                detail=(
                    "SW/MSW/BSW/LCSW must use ROUTINE_VISIT. "
                    "The form engine will resolve ROUTINE_VISIT to the psychosocial routine SW form."
                ),
            )
        if issue_present:
            raise HTTPException(
                status_code=422,
                detail=(
                    "SW psychosocial visits should not use nursing issue event types. "
                    "Keep ROUTINE_VISIT and document psychosocial findings in the SW routine form."
                ),
            )
        return

    if form_type == VisitFormType.SHORT_FORM.value:

        if not is_prn:
            raise HTTPException(
                status_code=422,
                detail="SHORT_FORM is only allowed for unscheduled (PRN) visits.",
            )

        # ✅ CRITICAL FIX: AUTO-SWITCH BASED ON DISCIPLINE

        if issue_present:
            if discipline == "RN":
                # ✅ RN → COMPREHENSIVE ASSESSMENT
                return  # let resolver switch to RN_ASSESS
            elif discipline == "LVN":
                # ✅ LVN → ROUTINE VISIT
                return  # let resolver switch to LVN_ROUTINE

        return

    if discipline == "RN":
        if issue_present:

            # ✅ DO NOT BLOCK SHORT_FORM — resolver will convert it
            if form_type == VisitFormType.SHORT_FORM.value:
                return

            if form_type != VisitFormType.ASSESS.value:
                raise HTTPException(
                    status_code=422,
                    detail=(
                        "RN must use ASSESS when issues are present."
                    ),
                )

            if event != "UPDATE_ASSESSMENT":
                raise HTTPException(
                    status_code=422,
                    detail=(
                        "RN issue-driven reassessment must use event_type=UPDATE_ASSESSMENT "
                        "so the plan of care update path is traceable."
                    ),
                )
            return
        return

    if discipline == "LVN":
        if issue_present:

            # ✅ allow SHORT_FORM → resolver converts
            if form_type == VisitFormType.SHORT_FORM.value:
                return

            if form_type != VisitFormType.ROUTINE_VISIT.value:
                raise HTTPException(
                    status_code=422,
                    detail=(
                        "LVN with issues must use ROUTINE_VISIT."
                    ),
                )
            return
        return


def _get_request_id(request: Request, response: Optional[Response] = None) -> str:
    existing = (
        getattr(request.state, "request_id", None)
        or request.headers.get("X-Request-ID")
    )
    request_id = str(existing or uuid.uuid4())
    request.state.request_id = request_id

    if response is not None:
        response.headers["X-Request-ID"] = request_id

    return request_id


def _extract_user_id_from_request(request: Request) -> Optional[uuid.UUID]:
    candidate_values = [
        getattr(request.state, "user_id", None),
        getattr(getattr(request.state, "user", None), "id", None),
        request.headers.get("X-User-Id"),
    ]

    for candidate in candidate_values:
        if not candidate:
            continue
        try:
            return candidate if isinstance(candidate, uuid.UUID) else uuid.UUID(str(candidate))
        except (TypeError, ValueError):
            continue

    return None


def _resolve_actor_user_id(db: Session, request: Request) -> uuid.UUID:
    authenticated_user_id = _extract_user_id_from_request(request)

    if authenticated_user_id:
        return authenticated_user_id

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authenticated user context is required",
    )

def _set_db_context(
    db: Session,
    tenant_id: uuid.UUID,
    user_id: uuid.UUID,
    request_id: str,
) -> None:
    db.info["tenant_id"] = tenant_id
    db.info["user_id"] = user_id
    db.info["request_id"] = request_id


def _normalized_mode_from_visit(visit: Visit) -> str:
    raw_mode = None
    for attr in ("visit_mode", "mode", "encounter_mode", "contact_mode"):
        if hasattr(visit, attr):
            raw_mode = getattr(visit, attr)
            if raw_mode is not None:
                break
    return (str(raw_mode) if raw_mode else "").upper()


def _resolve_actor_role(request: Request) -> str:
    candidate_values = [
        getattr(request.state, "role", None),
        getattr(getattr(request.state, "user", None), "role", None),
        request.headers.get("X-User-Role"),
    ]

    for candidate in candidate_values:
        if candidate:
            return str(candidate).strip().upper()

    return "SYSTEM"


def _visit_has_early_lock(visit: Visit) -> tuple[bool, Optional[str]]:
    for attr in ("signed_at", "reviewed_at", "approved_at", "cosigned_at", "locked_at"):
        if getattr(visit, attr, None) is not None:
            return True, attr
    return False, None


def _visit_is_within_correction_window(visit: Visit, now: datetime) -> bool:
    finalized_at = getattr(visit, "finalized_at", None)
    if finalized_at is None:
        return False

    if finalized_at.tzinfo is None:
        finalized_at = finalized_at.replace(tzinfo=timezone.utc)

    return now <= finalized_at + timedelta(hours=VISIT_CORRECTION_WINDOW_HOURS)


def _apply_reopen_metadata(
    *,
    visit: Visit,
    user_id: uuid.UUID,
    reason: str,
    now: datetime,
) -> None:
    if hasattr(visit, "updated_at"):
        visit.updated_at = now

    if hasattr(visit, "updated_by"):
        visit.updated_by = user_id

    if hasattr(visit, "status"):
        visit.status = "REOPENED"

    if hasattr(visit, "details"):
        details = getattr(visit, "details") or {}
        if not isinstance(details, dict):
            details = {}
        details["reopened_at"] = now.isoformat()
        details["reopened_by"] = str(user_id)
        details["reopen_reason"] = reason
        details["superseded_finalized_at"] = (
            getattr(visit, "finalized_at", None).isoformat()
            if getattr(visit, "finalized_at", None) is not None
            else None
        )
        visit.details = details


def _safe_log_event(
    db: Session,
    user_id: uuid.UUID,
    action: str,
    entity_type: str,
    entity_id: uuid.UUID,
    request_id: Optional[str] = None,
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
        logger.exception(
            "Audit log failed",
            extra={
                "action": action,
                "entity_type": entity_type,
                "entity_id": str(entity_id),
                "request_id": request_id,
                **(metadata or {}),
            },
        )


def _load_visit_for_update(db: Session, visit_id: uuid.UUID) -> Visit:
    visit = (
        db.query(Visit)
        .execution_options(skip_tenant_filter=True)
        .with_for_update()
        .filter(Visit.id == visit_id)
        .first()
    )
    if not visit:
        raise HTTPException(status_code=404, detail="Visit not found")
    return visit


def _load_patient_for_update(db: Session, patient_id: uuid.UUID) -> Patient:
    patient = (
        db.query(Patient)
        .execution_options(skip_tenant_filter=True)
        .with_for_update()
        .filter(Patient.id == patient_id)
        .first()
    )
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return patient

def _normalize_level_of_care(raw: Optional[str]) -> Optional[str]:
    if not raw:
        return None

    value = raw.strip().upper()

    mapping = {
        "ROUTINE_HOME_CARE": "RC",
        "CONTINUOUS_HOME_CARE": "CC",
        "GENERAL_INPATIENT": "IP",
        "INPATIENT_RESPITE": "RSP",
    }

    return mapping.get(value, value)

# =========================================================
# SUPERVISORY LOGIC HELPERS
# =========================================================

def _get_patient_refusal_flag(patient: Patient, service_key: str) -> bool:
    key = service_key.strip().upper()

    if key == "CHHA":
        return bool(
            getattr(patient, "chha_refused", False)
            or getattr(patient, "aide_refused", False)
        )

    if key == "LVN":
        return bool(getattr(patient, "lvn_refused", False))

    return False


def _patient_has_active_staff(patient: Patient, service_key: str) -> bool:
    key = service_key.strip().upper()

    if key == "CHHA":
        return bool(getattr(patient, "has_chha", False))

    if key == "LVN":
        return bool(getattr(patient, "has_lvn", False))

    return False


def _read_supervisory_targets_from_visit(visit: Visit) -> list[str]:
    """
    Extract supervisory target disciplines from visit.details.

    Returns:
        List[str] of normalized uppercase targets (e.g. ["LVN", "CHHA"]).

    Rules:
    - details must be a dict
    - supervisory_targets must be a list
    - values normalized to uppercase strings
    - empty/invalid values filtered out
    """

    details = getattr(visit, "details", None)

    if not isinstance(details, dict):
        return []

    targets = details.get("supervisory_targets")

    if not isinstance(targets, list):
        return []

    return [
        str(t).strip().upper()
        for t in targets
        if str(t).strip()
    ]


def _last_rn_supervisory_visit_for_target(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    patient_id: uuid.UUID,
    target: str,
) -> Optional[Visit]:
    target = target.strip().upper()

    visits = (
        db.query(Visit)
        .execution_options(skip_tenant_filter=True)
        .filter(
            Visit.tenant_id == tenant_id,
            Visit.patient_id == patient_id,
            Visit.visit_discipline == "RN",
        )
        .order_by(Visit.created_at.desc())
        .all()
    )

    for visit in visits:
        if not bool(getattr(visit, "is_supervisory", False)):
            continue

        if (getattr(visit, "status", "") or "").upper() != "FINALIZED":
            continue

        targets = _read_supervisory_targets_from_visit(visit)
        if target in targets:
            return visit

    return None


def _is_chha_supervision_due(
    db: Session,
    *,
    patient: Patient,
    now: datetime,
) -> bool:
    if not _patient_has_active_staff(patient, "CHHA"):
        return False

    if _get_patient_refusal_flag(patient, "CHHA"):
        return False

    last_visit = _last_rn_supervisory_visit_for_target(
        db,
        tenant_id=patient.tenant_id,
        patient_id=patient.id,
        target="CHHA",
    )

    if last_visit is None:
        return True

    last_finalized_at = (
        getattr(last_visit, "finalized_at", None)
        or getattr(last_visit, "created_at", None)
    )
    if last_finalized_at is None:
        return True

    if last_finalized_at.tzinfo is None:
        last_finalized_at = last_finalized_at.replace(tzinfo=timezone.utc)

    return now >= (last_finalized_at + timedelta(days=14))


def _is_lvn_supervision_due(
    db: Session,
    *,
    patient: Patient,
    now: datetime,
) -> bool:
    if not _patient_has_active_staff(patient, "LVN"):
        return False

    if _get_patient_refusal_flag(patient, "LVN"):
        return False

    last_visit = _last_rn_supervisory_visit_for_target(
        db,
        tenant_id=patient.tenant_id,
        patient_id=patient.id,
        target="LVN",
    )

    if last_visit is None:
        return True

    last_finalized_at = (
        getattr(last_visit, "finalized_at", None)
        or getattr(last_visit, "created_at", None)
    )
    if last_finalized_at is None:
        return True

    if last_finalized_at.tzinfo is None:
        last_finalized_at = last_finalized_at.replace(tzinfo=timezone.utc)

    return (
        last_finalized_at.year != now.year
        or last_finalized_at.month != now.month
    )


def _determine_supervisory_context(
    db: Session,
    *,
    patient: Patient,
    normalized_visit_type: str,
    validated_form_type: str,
    now: datetime,
) -> tuple[bool, list[str]]:
    if normalized_visit_type != "RN":
        return False, []

    if validated_form_type != VisitFormType.ROUTINE_VISIT.value:
        return False, []

    targets: list[str] = []

    if _is_chha_supervision_due(
        db,
        patient=patient,
        now=now,
    ):
        targets.append("CHHA")

    if _is_lvn_supervision_due(
        db,
        patient=patient,
        now=now,
    ):
        targets.append("LVN")

    return (len(targets) > 0), targets


def _apply_supervisory_context_to_visit(
    *,
    visit: Visit,
    is_supervisory: bool,
    supervisory_targets: list[str],
) -> None:
    if hasattr(visit, "is_supervisory"):
        visit.is_supervisory = is_supervisory

    if hasattr(visit, "details"):
        details = getattr(visit, "details") or {}
        if not isinstance(details, dict):
            details = {}

        details["is_supervisory"] = is_supervisory
        details["supervisory_targets"] = supervisory_targets

        visit.details = details


# =========================================================
# TASK COMPLETION HELPERS
# =========================================================

def _complete_task_with_visit(task: Task, visit: Visit, now: datetime) -> None:
    if not getattr(task, "tenant_id", None):
        raise ValueError("Task missing tenant_id")

    if not getattr(visit, "id", None):
        raise ValueError("Visit missing id")

    if task.status == TaskStatus.COMPLETED:
        return

    task.status = TaskStatus.COMPLETED
    task.completed_at = now

    task.completion_reference_type = (
        CompletionReferenceType.VISIT
        if hasattr(CompletionReferenceType, "VISIT")
        else "VISIT"
    )

    task.completion_reference_id = visit.id

    if hasattr(task, "updated_at"):
        task.updated_at = now

    if hasattr(task, "updated_by"):
        task.updated_by = (
            getattr(visit, "finalized_by", None)
            or getattr(visit, "provider_id", None)
        )


def _complete_initial_task_for_visit(
    db: Session,
    visit: Visit,
) -> list[str]:
    if not getattr(visit, "tenant_id", None):
        raise ValueError("Visit missing tenant_id")

    visit_type = _normalize_and_validate_visit_type(
        getattr(visit, "visit_type", "") or ""
    )

    discipline = normalize_visit_type(
        getattr(visit, "visit_discipline", "") or ""
    ).upper()

    target_task_type = None

    if visit_type == "RN" or discipline == "RN":
        target_task_type = TaskType.INITIAL_RN_ICA
    elif visit_type == "SW" or discipline == "SW":
        target_task_type = TaskType.INITIAL_MSW_ICA
    elif visit_type == "CHAPLAIN" or discipline == "CHAPLAIN":
        target_task_type = TaskType.INITIAL_SC_ICA

    if not target_task_type:
        return []

    # =====================================================
    # OPEN TASK
    # =====================================================

    task = (
        db.query(Task)
        .execution_options(skip_tenant_filter=True)
        .with_for_update()
        .filter(
            Task.tenant_id == visit.tenant_id,
            Task.patient_id == visit.patient_id,
            Task.task_type == target_task_type,
            Task.status.in_([
                TaskStatus.PENDING,
                TaskStatus.IN_PROGRESS,
                TaskStatus.OVERDUE,
            ]),
        )
        .first()
    )

    if task:
        now = datetime.now(timezone.utc)

        _complete_task_with_visit(
            task,
            visit,
            now,
        )

        logger.info(
            "Completed initial task task_type=%s patient_id=%s via visit_id=%s",
            target_task_type.value,
            str(getattr(visit, "patient_id", None)),
            str(getattr(visit, "id", None)),
        )

        return [target_task_type.value]

    # =====================================================
    # ALREADY COMPLETED BY AUTO ENGINE
    # =====================================================

    completed_task = (
        db.query(Task)
        .execution_options(skip_tenant_filter=True)
        .filter(
            Task.tenant_id == visit.tenant_id,
            Task.patient_id == visit.patient_id,
            Task.task_type == target_task_type,
            Task.status == TaskStatus.COMPLETED,
            Task.completion_reference_id == visit.id,
        )
        .first()
    )

    if completed_task:
        logger.info(
            "Initial task already completed by automation task_type=%s visit_id=%s",
            target_task_type.value,
            str(visit.id),
        )

        return [target_task_type.value]

    return []


def _get_task_type_member(task_type_name: str):
    return getattr(TaskType, task_type_name, None)


def _create_condition_trigger_task_if_missing(
    db: Session,
    patient: Patient,
    user_id: uuid.UUID,
    now: datetime,
    task_type_name: str,
    discipline_value: str,
) -> bool:
    if not getattr(patient, "tenant_id", None):
        raise ValueError("Patient missing tenant_id")

    task_type_member = _get_task_type_member(task_type_name)
    if task_type_member is None:
        logger.warning("Missing TaskType enum member: %s", task_type_name)
        return False

    existing = (
        db.query(Task)
        .execution_options(skip_tenant_filter=True)
        .with_for_update()
        .filter(
            Task.tenant_id == patient.tenant_id,
            Task.patient_id == patient.id,
            Task.task_type == task_type_member,
            Task.status.in_([
                TaskStatus.PENDING,
                TaskStatus.IN_PROGRESS,
                TaskStatus.OVERDUE,
            ]),
        )
        .first()
    )

    if existing:
        return False

    task = Task(
        id=uuid.uuid4(),
        tenant_id=patient.tenant_id,
        patient_id=patient.id,
        task_type=task_type_member,
        status=TaskStatus.PENDING,
        created_at=now,
        updated_at=now,
        created_by=user_id,
    )

    if hasattr(task, "due_date"):
        task.due_date = now.date()

    if hasattr(task, "due_at"):
        task.due_at = now

    if hasattr(task, "origin"):
        task.origin = (
            TaskOrigin.SYSTEM
            if hasattr(TaskOrigin, "SYSTEM")
            else "SYSTEM"
        )

    if hasattr(task, "discipline"):
        task.discipline = discipline_value

    if hasattr(task, "regulatory_basis"):
        task.regulatory_basis = (
            TaskRegulatoryBasis.CONDITION_TRIGGER
            if hasattr(TaskRegulatoryBasis, "CONDITION_TRIGGER")
            else "CONDITION_TRIGGER"
        )

    if hasattr(task, "alert_reason"):
        task.alert_reason = task_type_name

    db.add(task)

    logger.info(
        "Created condition-trigger task task_type=%s patient_id=%s",
        task_type_name,
        str(patient.id),
    )

    return True


def _fetch_visit_related_notes(db: Session, visit: Visit) -> list[Any]:
    candidate_models: list[tuple[str, str]] = [
        ("app.models.note", "Note"),
        ("app.models.visit_note", "VisitNote"),
        ("app.models.clinical_note", "ClinicalNote"),
    ]

    for module_name, class_name in candidate_models:
        try:
            module = __import__(module_name, fromlist=[class_name])
            note_model = getattr(module, class_name, None)
            if note_model is None:
                continue

            query = db.query(note_model).execution_options(skip_tenant_filter=True)

            if hasattr(note_model, "tenant_id"):
                query = query.filter(note_model.tenant_id == visit.tenant_id)

            if hasattr(note_model, "visit_id"):
                query = query.filter(note_model.visit_id == visit.id)
            elif hasattr(note_model, "patient_id"):
                query = query.filter(note_model.patient_id == visit.patient_id)
            else:
                continue

            return query.all()

        except Exception:
            logger.debug(
                "Note model unavailable or query failed for %s.%s",
                module_name,
                class_name,
                exc_info=True,
            )

    return []


def _run_condition_detection_non_blocking(
    db: Session,
    visit: Visit,
    patient: Patient,
    user_id: uuid.UUID,
    now: datetime,
    request_id: str,
) -> None:
    try:
        notes = _fetch_visit_related_notes(db, visit)

        note_inputs = [
            NoteInput(
                patient_id=patient.id,
                author_discipline=getattr(n, "discipline", ""),
                text=getattr(n, "text", "") or getattr(n, "note_text", ""),
                structured_flags=None,
            )
            for n in notes
        ]

        condition_result = condition_engine.detect(
            notes=note_inputs,
            assessments=None,
        )

        if condition_result.has_wounds and not getattr(patient, "has_wounds", False):
            setattr(patient, "has_wounds", True)
            if hasattr(patient, "updated_at"):
                patient.updated_at = now

        if condition_result.psychosocial_issue:
            _create_condition_trigger_task_if_missing(
                db=db,
                patient=patient,
                user_id=user_id,
                now=now,
                task_type_name="MSW_REOFFER",
                discipline_value="SW",
            )

        if condition_result.spiritual_distress:
            _create_condition_trigger_task_if_missing(
                db=db,
                patient=patient,
                user_id=user_id,
                now=now,
                task_type_name="CHAPLAIN_REOFFER",
                discipline_value="CHAPLAIN",
            )

        _safe_log_event(
            db=db,
            user_id=user_id,
            action="CONDITION_ENGINE_EVALUATED",
            entity_type="visit",
            entity_id=visit.id,
            request_id=request_id,
        )

    except Exception:
        logger.exception(
            "Condition detection failed",
            extra={
                "visit_id": str(visit.id),
                "patient_id": str(patient.id),
                "request_id": request_id,
            },
        )


def _run_bereavement_aggregation_non_blocking(
    db: Session,
    visit: Visit,
    patient: Patient,
    user_id: uuid.UUID,
    request_id: str,
) -> None:
    try:
        notes = _fetch_visit_related_notes(db, visit)

        bereavement_inputs = [
            BereavementNoteInput(
                patient_id=patient.id,
                note_id=getattr(n, "id", None),
                discipline=getattr(n, "discipline", ""),
                text=getattr(n, "text", "") or getattr(n, "note_text", ""),
            )
            for n in notes
            if getattr(n, "id", None) is not None
        ]

        result = bereavement_engine.detect(bereavement_inputs)

        if result.source_notes:
            _safe_log_event(
                db=db,
                user_id=user_id,
                action="BEREAVEMENT_AGGREGATED",
                entity_type="patient",
                entity_id=patient.id,
                request_id=request_id,
            )

    except Exception:
        logger.exception(
            "Bereavement aggregation failed",
            extra={
                "visit_id": str(visit.id),
                "patient_id": str(patient.id),
                "request_id": request_id,
            },
        )


def _enforce_rn_supervisory_requirement(
    visit: Visit,
    patient: Patient,
    is_rn: bool,
) -> None:
    if not is_rn:
        return

    if not getattr(visit, "is_supervisory", False):
        return

    details = getattr(visit, "details", None) or {}
    if not isinstance(details, dict):
        details = {}

    targets = details.get("supervisory_targets", [])
    if not isinstance(targets, list) or not targets:
        raise HTTPException(
            status_code=422,
            detail="Supervisory RN visit is missing supervisory_targets context",
        )


# =========================================================
# PHASE B / HOPE HELPERS
# =========================================================

def _severity_rank(value: Optional[str]) -> int:
    if not value:
        return 0
    code = str(value).strip().upper()
    if code == "SEVERE":
        return 3
    if code == "MODERATE":
        return 2
    if code == "MILD":
        return 1
    return 0


def _extract_j2051_impacts_from_notes(
    *,
    notes: list[ClinicalNote],
    visit_id: uuid.UUID,
    request_id: str,
) -> tuple[Optional[str], Optional[str]]:
    """
    Extract Phase B trigger values for J2051 from structured note content.

    Returns:
    (
        pain_impact,       # e.g. MODERATE / SEVERE / None
        non_pain_impact,   # highest non-pain symptom impact if any
    )

    Supported pathways:
    - content["assessment"]["pain"]["severity"]
    - content["symptom_impact"] / content["symptomImpact"] dicts
    """
    pain_impact: Optional[str] = None
    non_pain_impact: Optional[str] = None

    logger.info(
        "PHASE_B_J2051_EXTRACT: ENTERED visit_id=%s request_id=%s note_count=%s",
        str(visit_id),
        request_id,
        len(notes),
    )

    for note in notes:
        raw_content = getattr(note, "content", None)

        logger.info(
            "PHASE_B_J2051_EXTRACT: RAW_CONTENT_TYPE "
            "visit_id=%s note_id=%s type=%s request_id=%s",
            str(visit_id),
            str(getattr(note, "id", None)),
            type(raw_content).__name__,
            request_id,
        )

        data: Any = None

        try:
            if raw_content is None:
                continue

            if isinstance(raw_content, dict):
                data = raw_content
            elif isinstance(raw_content, str):
                content_str = raw_content.strip()
                if not content_str:
                    continue
                data = json.loads(content_str)
                if isinstance(data, str):
                    data = json.loads(data)
            else:
                continue
        except (
            TypeError,
            ValueError,
            json.JSONDecodeError,
        ):
            logger.exception(
                "PHASE_B_J2051_EXTRACT: PARSE_FAILED visit_id=%s note_id=%s request_id=%s",
                str(visit_id),
                str(getattr(note, "id", None)),
                request_id,
            )
            continue

        if not isinstance(data, dict):
            continue

        assessment = data.get("assessment")
        if isinstance(assessment, dict):
            pain = assessment.get("pain")
            if isinstance(pain, dict):
                severity = pain.get("severity")
                if severity:
                    sev_code = str(severity).strip().upper()
                    if _severity_rank(sev_code) > _severity_rank(pain_impact):
                        pain_impact = sev_code

            for key, value in assessment.items():
                if str(key).strip().lower() == "pain":
                    continue
                if isinstance(value, dict):
                    severity = value.get("severity")
                    if severity:
                        sev_code = str(severity).strip().upper()
                        if _severity_rank(sev_code) > _severity_rank(non_pain_impact):
                            non_pain_impact = sev_code

        symptom_impact = data.get("symptom_impact") or data.get("symptomImpact")
        if isinstance(symptom_impact, dict):
            for key, value in symptom_impact.items():
                key_code = str(key).strip().lower()
                sev_code = str(value).strip().upper()
                if key_code == "pain":
                    if _severity_rank(sev_code) > _severity_rank(pain_impact):
                        pain_impact = sev_code
                else:
                    if _severity_rank(sev_code) > _severity_rank(non_pain_impact):
                        non_pain_impact = sev_code

    logger.info(
        "PHASE_B_J2051_EXTRACT: RESULT visit_id=%s pain_impact=%s non_pain_impact=%s request_id=%s",
        str(visit_id),
        pain_impact,
        non_pain_impact,
        request_id,
    )

    return pain_impact, non_pain_impact

def _extract_primary_diagnosis_from_notes(
    *,
    notes: list[ClinicalNote],
) -> str | None:
    """
    Extract primary diagnosis from RN ICA clinical note content.

    RN ICA data is currently stored as:

        ClinicalNote.content

    Supported JSON shapes:

        {
            "primary_diagnosis": "C34.90"
        }

        {
            "primary_dx": "C34.90"
        }

        {
            "primary_dx_code": "C34.90"
        }

        {
            "diagnosis": {
                "primary_diagnosis": "C34.90"
            }
        }

        {
            "diagnosis": {
                "primary_dx": "C34.90"
            }
        }

        {
            "diagnosis": {
                "icd_code": "C34.90"
            }
        }

        {
            "diagnoses": {
                "primary_diagnosis": "C34.90"
            }
        }

        {
            "diagnoses": [
                {
                    "type": "PRIMARY",
                    "code": "C34.90"
                }
            ]
        }

    This helper is intentionally tolerant because RN ICA JSON structure
    is not yet locked into a dedicated schema/model.
    """

    for note in notes:
        content = getattr(note, "content", None) or {}

        if not isinstance(content, dict):
            continue

        # -------------------------------------------------
        # DIRECT ROOT-LEVEL KEYS
        # -------------------------------------------------
        direct_candidates = [
            content.get("primary_diagnosis"),
            content.get("primary_dx"),
            content.get("primary_dx_code"),
        ]

        for value in direct_candidates:
            if value is not None and str(value).strip():
                return str(value).strip()

        # -------------------------------------------------
        # diagnosis: {...}
        # -------------------------------------------------
        diagnosis = content.get("diagnosis")

        if isinstance(diagnosis, dict):
            nested_candidates = [
                diagnosis.get("primary_diagnosis"),
                diagnosis.get("primary_dx"),
                diagnosis.get("primary_dx_code"),
                diagnosis.get("icd_code"),
                diagnosis.get("code"),
            ]

            for value in nested_candidates:
                if value is not None and str(value).strip():
                    return str(value).strip()

        # -------------------------------------------------
        # diagnoses: {...}
        # -------------------------------------------------
        diagnoses = content.get("diagnoses")

        if isinstance(diagnoses, dict):
            diagnoses_candidates = [
                diagnoses.get("primary_diagnosis"),
                diagnoses.get("primary_dx"),
                diagnoses.get("primary_dx_code"),
                diagnoses.get("icd_code"),
                diagnoses.get("code"),
            ]

            for value in diagnoses_candidates:
                if value is not None and str(value).strip():
                    return str(value).strip()

        # -------------------------------------------------
        # diagnoses: [{...}]
        # -------------------------------------------------
        if isinstance(diagnoses, list):
            for item in diagnoses:
                if not isinstance(item, dict):
                    continue

                dx_type = str(
                    item.get("type")
                    or item.get("dx_type")
                    or item.get("diagnosis_type")
                    or ""
                ).strip().upper()

                if dx_type != "PRIMARY":
                    continue

                list_candidates = [
                    item.get("primary_diagnosis"),
                    item.get("primary_dx"),
                    item.get("primary_dx_code"),
                    item.get("icd_code"),
                    item.get("code"),
                    item.get("diagnosis"),
                ]

                for value in list_candidates:
                    if value is not None and str(value).strip():
                        return str(value).strip()

    return None

def _find_oldest_open_sfv_requirement_for_patient(
    *,
    db: Session,
    patient_id: uuid.UUID,
) -> Optional[SFVRequirement]:
    return (
        db.query(SFVRequirement)
        .execution_options(skip_tenant_filter=True)
        .with_for_update()
        .filter(
            SFVRequirement.patient_id == patient_id,
            SFVRequirement.status == "OPEN",
        )
        .order_by(SFVRequirement.due_at.asc())
        .first()
    )


def _get_completed_huv_task_type_for_visit(
    *,
    db: Session,
    visit: Visit,
) -> Optional[str]:
    completed = (
        db.query(Task)
        .execution_options(skip_tenant_filter=True)
        .filter(
            Task.tenant_id == visit.tenant_id,
            Task.patient_id == visit.patient_id,
            Task.status == TaskStatus.COMPLETED,
            Task.completion_reference_id == visit.id,
            Task.task_type.in_([TaskType.HUV1, TaskType.HUV2]),
        )
        .order_by(Task.completed_at.desc())
        .first()
    )

    if not completed:
        return None

    return completed.task_type.value if hasattr(completed.task_type, "value") else str(completed.task_type)


def _maybe_complete_open_sfv_for_visit(
    *,
    db: Session,
    visit: Visit,
    request_id: str,
) -> Optional[SFVRequirement]:

    open_requirement = _find_oldest_open_sfv_requirement_for_patient(
        db=db,
        patient_id=visit.patient_id,
    )

    if not open_requirement:
        logger.info(
            "PHASE_B_SFV_COMPLETE: NO_OPEN_REQUIREMENT visit_id=%s request_id=%s",
            str(visit.id),
            request_id,
        )
        return None

    try:
        completed_requirement = complete_sfv_requirement_from_visit(
            db=db,
            sfv_requirement_id=open_requirement.id,
            completing_visit_id=visit.id,
            completing_visit_datetime=visit.visit_datetime,
            discipline=visit.visit_discipline,
            visit_mode=getattr(visit, "visit_mode", None),
        )

        logger.info(
            "PHASE_B_SFV_COMPLETE: COMPLETED requirement_id=%s visit_id=%s request_id=%s",
            str(completed_requirement.id),
            str(visit.id),
            request_id,
        )

        return completed_requirement

    except ValueError as exc:
        logger.info(
            "PHASE_B_SFV_COMPLETE: NOT_ELIGIBLE visit_id=%s requirement_id=%s reason=%s request_id=%s",
            str(visit.id),
            str(open_requirement.id),
            str(exc),
            request_id,
        )
        return None


def _run_phase_b_finalize_hooks(
    *,
    db: Session,
    visit: Visit,
    completed_task_types: list[str],
    notes: list[ClinicalNote],
    request_id: str,
) -> None:
    pain_impact, non_pain_impact = _extract_j2051_impacts_from_notes(
        notes=notes,
        visit_id=visit.id,
        request_id=request_id,
    )

    _maybe_complete_open_sfv_for_visit(
        db=db,
        visit=visit,
        request_id=request_id,
    )

    if "INITIAL_RN_ICA" in completed_task_types:
        logger.info(
            "PHASE_B_HOOK: INITIAL_RN_ICA_TRIGGER visit_id=%s patient_id=%s request_id=%s",
            str(visit.id),
            str(visit.patient_id),
            request_id,
        )

        result = process_initial_rn_ica_finalize(
            db=db,
            tenant_id=visit.tenant_id,
            patient_id=visit.patient_id,
            initial_rn_ica_visit_id=visit.id,
            election_datetime=visit.visit_datetime,
            j2051_pain_impact=pain_impact,
            j2051_non_pain_impact=non_pain_impact,
        )

        rn_ica_primary_diagnosis = _extract_primary_diagnosis_from_notes(
            notes=notes,
        )

        diagnosis_sync_result = sync_official_primary_diagnosis(
            db,
            tenant_id=visit.tenant_id,
            patient_id=visit.patient_id,
            primary_diagnosis=rn_ica_primary_diagnosis,
            source="RN_ICA",
            updated_by=(
                getattr(visit, "finalized_by", None)
                or getattr(visit, "updated_by", None)
                or getattr(visit, "created_by", None)
            ),
        )

        logger.info(
            "PHASE_B_HOOK: INITIAL_RN_ICA_DIAGNOSIS_SYNC visit_id=%s result=%s request_id=%s",
            str(visit.id),
            diagnosis_sync_result,
            request_id,
        )

        logger.info(
            "PHASE_B_HOOK: INITIAL_RN_ICA_RESULT visit_id=%s result=%s request_id=%s",
            str(visit.id),
            result,
            request_id,
        )

    completed_huv_type = _get_completed_huv_task_type_for_visit(
        db=db,
        visit=visit,
    )
    if completed_huv_type in {"HUV1", "HUV2"}:
        logger.info(
            "PHASE_B_HOOK: HUV_TRIGGER visit_id=%s huv_type=%s patient_id=%s request_id=%s",
            str(visit.id),
            completed_huv_type,
            str(visit.patient_id),
            request_id,
        )

        result = process_huv_finalize(
            db=db,
            tenant_id=visit.tenant_id,
            patient_id=visit.patient_id,
            huv_task_type=completed_huv_type,
            huv_visit_id=visit.id,
            election_datetime=visit.visit_datetime,
            completed_visit_datetime=visit.visit_datetime,
            discipline=visit.visit_discipline,
            j2051_pain_impact=pain_impact,
            j2051_non_pain_impact=non_pain_impact,
        )

        logger.info(
            "PHASE_B_HOOK: HUV_RESULT visit_id=%s result=%s request_id=%s",
            str(visit.id),
            result,
            request_id,
        )


# =========================================================
# VISIT STATUS CHANGE
# =========================================================

@router.patch("/{visit_id}/status", response_model=VisitMutationResponse)
def update_visit_status(
    visit_id: uuid.UUID,
    payload: VisitStatusUpdate,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    request_id = _get_request_id(request, response)
    user_id = _resolve_actor_user_id(db, request)

    visit = _load_visit_for_update(db, visit_id)
    _set_db_context(db, visit.tenant_id, user_id, request_id)

    new_status = (payload.status or "").strip().upper()

    if not new_status:
        raise HTTPException(status_code=422, detail="status is required")

    if new_status not in ALLOWED_STATUS_CHANGES:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid status '{payload.status}'. Allowed: {sorted(ALLOWED_STATUS_CHANGES)}",
        )

    already_finalized = (visit.status or "").upper() == "FINALIZED"
    if already_finalized:
        raise HTTPException(
            status_code=409,
            detail=(
                "Cannot change status of a FINALIZED visit. "
                "Create a new visit or document variance in Communications Log."
            ),
        )

    enforce_commlog_for_visit_status_change(
        db=db,
        visit=visit,
        new_status=new_status,
        communications_log_id=payload.communications_log_id,
    )

    now = datetime.now(timezone.utc)
    visit.status = new_status

    if hasattr(visit, "updated_at"):
        visit.updated_at = now

    if hasattr(visit, "communications_log_id"):
        visit.communications_log_id = payload.communications_log_id
    elif hasattr(visit, "details"):
        details = getattr(visit, "details") or {}
        if not isinstance(details, dict):
            details = {}
        details["communications_log_id"] = (
            str(payload.communications_log_id)
            if payload.communications_log_id
            else None
        )
        visit.details = details

    try:
        db.flush()

        _safe_log_event(
            db=db,
            user_id=user_id,
            action="UPDATE_VISIT_STATUS",
            entity_type="visit",
            entity_id=visit.id,
            request_id=request_id,
            metadata={"new_status": new_status},
        )

        db.commit()

    except HTTPException:
        db.rollback()
        raise

    except Exception as exc:
        db.rollback()
        logger.exception(
            "Visit status update failed",
            extra={
                "visit_id": str(visit.id),
                "new_status": new_status,
                "request_id": request_id,
            },
        )
        raise HTTPException(
            status_code=500,
            detail=f"Visit status update failed: {exc}",
        )

    return VisitMutationResponse(
        status="updated",
        visit_id=str(visit.id),
        request_id=request_id,
        completed_task_types=[],
        new_status=new_status,
        communications_log_id=(
            str(payload.communications_log_id)
            if payload.communications_log_id
            else None
        ),
    )


# =========================================================
# CREATE VISIT
# =========================================================

@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    response_model=VisitCreateResponse,
)
def create_visit(
    payload: VisitCreateRequest,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Security(get_current_user),
):
    request_id = _get_request_id(request, response)
    user_id = current_user.user_id

    # =========================================================
    # LOAD PATIENT + CONTEXT
    # =========================================================
    patient = _load_patient_for_update(db, payload.patient_id)
    _set_db_context(db, patient.tenant_id, user_id, request_id)

    # =========================================================
    # VALIDATION / NORMALIZATION
    # =========================================================
    normalized = _canonicalize_discipline(payload.visit_type)
    validated_form_type = _normalize_and_validate_form_type(payload.form_type)
    validated_schedule_type = _normalize_schedule_type(payload.visit_schedule_type)
    validated_event_type = _normalize_event_type_for_form(
        validated_form_type,
        payload.event_type,
    )

    _enforce_form_selection_rules(
        discipline=normalized,
        form_type=validated_form_type,
        visit_schedule_type=validated_schedule_type,
        event_type=validated_event_type,
    )

    now = datetime.now(timezone.utc)

    # =========================================================
    # RESOLVE ACTIVE ADMISSION FOR THIS VISIT
    # =========================================================
    resolved_admission = (
        db.query(Admission)
        .filter(
            Admission.patient_id == patient.id,
            Admission.tenant_id == patient.tenant_id,
            Admission.status == "ADMITTED",
        )
        .order_by(Admission.created_at.desc())
        .first()
    )

    if not resolved_admission:
        raise HTTPException(
            status_code=400,
            detail="Patient must have an active admitted admission before creating a SOC visit",
        )

    # =========================================================
    # SUPERVISORY CONTEXT
    # =========================================================
    is_supervisory, supervisory_targets = _determine_supervisory_context(
        db=db,
        patient=patient,
        normalized_visit_type=normalized,
        validated_form_type=validated_form_type,
        now=now,
    )

    # =========================================================
    # INIT VISIT
    # =========================================================
    visit = Visit(
        id=uuid.uuid4(),
        tenant_id=patient.tenant_id,
        admission_id=resolved_admission.id,
        patient_id=patient.id,
        provider_id=user_id,
        visit_type=normalized,
        visit_discipline=normalized,
        visit_mode="IN_PERSON",
        status="DRAFT",
        visit_datetime=now,
        acuity_state_at_visit=getattr(patient, "acuity_state", None),
        form_type=validated_form_type,
        is_supervisory=is_supervisory,
        created_at=now,
        updated_at=now,
        created_by=user_id,
    )

    try:
        # =========================================================
        # SAVE VISIT
        # =========================================================
        db.add(visit)
        db.flush()

        # 🚨 CRITICAL GUARD
        if not visit.admission_id:
            raise HTTPException(
                status_code=500,
                detail="Visit created without admission_id — system error",
            )


        _apply_supervisory_context_to_visit(
            visit=visit,
            is_supervisory=is_supervisory,
            supervisory_targets=supervisory_targets,
        )

        # =========================================================
        # FORM RESOLUTION
        # =========================================================
        form_config = resolve_form_package(
            discipline=normalized,
            form_type=validated_form_type,
            level_of_care=_normalize_level_of_care(payload.level_of_care),
            event_type=validated_event_type,
        )

        resolved_primary_form = (
            form_config.get("primary_form")
            or form_config.get("form_key")
        )

        resolved_attached_forms = (
            form_config.get("attached_forms")
            or form_config.get("attached_form_keys")
            or []
        )

        resolved_modules = (
            form_config.get("modules")
            or form_config.get("primary_modules")
            or []
        )

        if not form_config or not resolved_primary_form:
            raise HTTPException(
                status_code=422,
                detail="Unable to resolve form package",
            )

        primary_form = _guard_against_generic_note_type(
            resolved_primary_form,
            request_id=request_id,
        )

        attached_forms = [
            _guard_against_generic_note_type(name, request_id=request_id)
            for name in list(resolved_attached_forms)
        ]

        resolved_form_family = form_config.get("form_family")
        form_family = (
            resolved_form_family.value
            if hasattr(resolved_form_family, "value")
            else resolved_form_family
        )

        modules = list(resolved_modules)
        resolved_by = form_config.get("resolved_by")
        resolved_form_type = form_config.get("form_type") or validated_form_type

        # =========================================================
        # ✅ POC TRIGGER DETECTION (KEEP — CRITICAL)
        # =========================================================
        note = payload.clinical_note or {}
        assessment = note.get("assessment", {})

        poc_update_required = False

        pain_score = assessment.get("pain_score")
        psychosocial = assessment.get("psychosocial")
        spiritual = assessment.get("spiritual")

        if pain_score is not None and pain_score >= 5:
            poc_update_required = True

        if psychosocial:
            poc_update_required = True

        if spiritual:
            poc_update_required = True

        logger.info(
            "POC_TRIGGER_DETECTION visit_id=%s pain=%s psychosocial=%s spiritual=%s result=%s request_id=%s",
            str(visit.id),
            pain_score,
            psychosocial,
            spiritual,
            poc_update_required,
            request_id,
        )

        if poc_update_required:
            _safe_log_event(
                db=db,
                user_id=user_id,
                action="POC_TRIGGER_DETECTED",
                entity_type="visit",
                entity_id=visit.id,
                request_id=request_id,
            )

        # =========================================================
        # PRIMARY NOTE
        # =========================================================
        primary_note = ClinicalNote(
            id=uuid.uuid4(),
            visit_id=visit.id,
            author_id=user_id,
            tenant_id=visit.tenant_id,
            patient_id=visit.patient_id,
            note_type=primary_form,
            discipline=visit.visit_discipline,
            form_family=form_family,
            form_key=primary_form,
            module_payload={
                "modules": modules,
                "attached_forms": attached_forms,
                "resolved_by": resolved_by,
                "form_type": resolved_form_type,
            },
            is_primary_form=True,
            parent_form_id=None,
            status="DRAFT",
            encounter_date=now.date(),
            content=(payload.clinical_note or {}),
            plan_of_care_updates={
                "meta": {
                    "version": "1.0",
                    "generated_at": now.isoformat(),
                    "note_id": None,
                    "patient_id": str(visit.patient_id),
                },
                "pocs": [],
            },
            created_by=user_id,
            created_at=now,
            updated_at=now,
            updated_by_user_id=user_id,
            entered_at=now,
            care_level_snapshot=_normalize_level_of_care(payload.level_of_care),
            is_late_entry=False,
        )

        db.add(primary_note)
        db.flush()

        validate_and_trigger_incident(
            db=db,
            note=primary_note,
            actor_user_id=user_id,
            actor_role="CLINICIAN",
        )

        # =========================================================
        # ATTACHED NOTES
        # =========================================================
        for form_key in attached_forms:
            attached_note = ClinicalNote(
                id=uuid.uuid4(),
                visit_id=visit.id,
                author_id=user_id,
                tenant_id=visit.tenant_id,
                patient_id=visit.patient_id,
                note_type=form_key,
                discipline=visit.visit_discipline,
                form_family=form_family,
                form_key=form_key,
                module_payload={
                    "modules": [],
                    "attached_forms": [],
                    "resolved_by": resolved_by,
                    "form_type": resolved_form_type,
                },
                is_primary_form=False,
                parent_form_id=primary_note.id,
                status="DRAFT",
                encounter_date=now.date(),
                content={},
                plan_of_care_updates={
                    "meta": {
                        "version": "1.0",
                        "generated_at": now.isoformat(),
                        "note_id": None,
                        "patient_id": str(visit.patient_id),
                    },
                    "pocs": [],
                },
                created_by=user_id,
                created_at=now,
                updated_at=now,
                updated_by_user_id=user_id,
                entered_at=now,
                care_level_snapshot=_normalize_level_of_care(payload.level_of_care),
                is_late_entry=False,
            )
            db.add(attached_note)

        # =========================================================
        # AUDIT LOG
        # =========================================================
        _safe_log_event(
            db=db,
            user_id=user_id,
            action="CREATE_VISIT",
            entity_type="visit",
            entity_id=visit.id,
            request_id=request_id,
        )

        db.commit()

    except HTTPException:
        db.rollback()
        raise

    except Exception as exc:
        db.rollback()
        logger.exception(
            "VISIT_CREATE_FAILED",
            extra={
                "patient_id": str(patient.id),
                "request_id": request_id,
            },
        )
        raise HTTPException(
            status_code=500,
            detail=f"Visit creation failed: {exc}",
        )

    # =========================================================
    # FINAL RETURN (CRITICAL — NEVER SKIP)
    # =========================================================
    return VisitCreateResponse(
        visit_id=str(visit.id),
        visit_type=normalized,
        form_type=resolved_form_type,
        form_family=form_family,
        primary_form=primary_form,
        attached_forms=attached_forms,
        modules=modules,
        resolved_by=resolved_by,
        is_supervisory=is_supervisory,
        supervisory_targets=supervisory_targets,
        request_id=request_id,
    )

@router.post("/{visit_id}/reopen")
def reopen_visit(
    visit_id: uuid.UUID,
    payload: VisitReopenRequest,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Security(get_current_user),
):
    # =========================================================
    # CONTEXT RESOLUTION
    # =========================================================
    request_id = _get_request_id(request, response)
    user_id = current_user.user_id
    actor_role = str(getattr(current_user, "role", "SYSTEM")).strip().upper()

    # =========================================================
    # LOAD VISIT
    # =========================================================
    visit = _load_visit_for_update(db, visit_id)
    _set_db_context(db, visit.tenant_id, user_id, request_id)

    # =========================================================
    # 🚨 CRITICAL: ADMISSION GUARD
    # =========================================================
    if not getattr(visit, "admission_id", None):
        raise HTTPException(
            status_code=500,
            detail="Visit is not tied to an admission — invalid chart state",
        )

    logger.info(
        "REOPEN: VISIT_LOADED visit_id=%s patient_id=%s status=%s role=%s request_id=%s",
        str(visit.id),
        str(visit.patient_id),
        getattr(visit, "status", None),
        actor_role,
        request_id,
    )

    # =========================================================
    # STATUS VALIDATION
    # =========================================================
    current_status = (getattr(visit, "status", "") or "").upper()

    if current_status != "FINALIZED":
        raise HTTPException(
            status_code=409,
            detail="Only FINALIZED visits can be reopened.",
        )

    # =========================================================
    # ROLE VALIDATION
    # =========================================================
    if actor_role not in ALLOWED_REOPEN_ROLES:
        raise HTTPException(
            status_code=403,
            detail="Supervisor or admin approval is required to reopen finalized documentation.",
        )

    # =========================================================
    # TIME CONTEXT
    # =========================================================
    now = datetime.now(timezone.utc)

    # =========================================================
    # LOCKED STATE CHECK
    # =========================================================
    early_lock, early_lock_reason = _visit_has_early_lock(visit)

    if early_lock:
        raise HTTPException(
            status_code=409,
            detail=(
                f"This documentation is locked because '{early_lock_reason}' is present. "
                "Add an amendment instead of modifying the original record."
            ),
        )

    # =========================================================
    # CORRECTION WINDOW CHECK
    # =========================================================
    if not _visit_is_within_correction_window(visit, now):
        raise HTTPException(
            status_code=409,
            detail=(
                "This documentation is outside the 72-hour correction window. "
                "Add an amendment instead of modifying the original record."
            ),
        )

    # =========================================================
    # APPLY REOPEN
    # =========================================================
    try:
        _apply_reopen_metadata(
            visit=visit,
            user_id=user_id,
            reason=payload.reason,
            now=now,
        )

        db.flush()

        # =====================================================
        # AUDIT LOG (ENHANCED)
        # =====================================================
        _safe_log_event(
            db=db,
            user_id=user_id,
            action="REOPEN_VISIT",
            entity_type="visit",
            entity_id=visit.id,
            request_id=request_id,
            metadata={
                "reason": payload.reason,
                "previous_status": "FINALIZED",
                "new_status": "REOPENED",
                "admission_id": str(visit.admission_id),
                "actor_role": actor_role,
            },
        )

        db.commit()

        logger.info(
            "REOPEN: SUCCESS visit_id=%s request_id=%s",
            str(visit.id),
            request_id,
        )

    except HTTPException:
        db.rollback()
        raise

    except Exception as exc:
        db.rollback()

        logger.exception(
            "REOPEN_VISIT_FAILED",
            extra={
                "visit_id": str(visit.id),
                "request_id": request_id,
            },
        )

        raise HTTPException(
            status_code=500,
            detail=f"Visit reopen failed: {exc}",
        )

    # =========================================================
    # RESPONSE
    # =========================================================
    return {
        "status": "reopened",
        "visit_id": str(visit.id),
        "request_id": request_id,
        "message": (
            "Visit reopened. Update the documentation and finalize again within the 72-hour correction window."
        ),
    }


@router.post("/{visit_id}/chha-outcome")
def upsert_chha_visit_outcome(
    visit_id: uuid.UUID,
    payload: CHHAOutcomeUpsertRequest,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    # =========================================================
    # CONTEXT RESOLUTION
    # =========================================================
    request_id = _get_request_id(request, response)
    user_id = _resolve_actor_user_id(db, request)

    # =========================================================
    # LOAD VISIT
    # =========================================================
    visit = _load_visit_for_update(db, visit_id)
    _set_db_context(db, visit.tenant_id, user_id, request_id)

    # =========================================================
    # 🚨 CRITICAL: ADMISSION GUARD
    # =========================================================
    if not getattr(visit, "admission_id", None):
        raise HTTPException(
            status_code=500,
            detail="Visit is not tied to an admission — invalid state",
        )

    # =========================================================
    # DISCIPLINE VALIDATION
    # =========================================================
    discipline = (getattr(visit, "visit_discipline", "") or "").upper()

    if discipline not in {"AIDE"}:
        raise HTTPException(
            status_code=422,
            detail="CHHA outcome can only be recorded for AIDE/CHHA visits",
        )

    # =========================================================
    # VISIT STATUS GUARD
    # =========================================================
    visit_status = (getattr(visit, "status", "") or "").upper()

    if visit_status == "FINALIZED":
        raise HTTPException(
            status_code=409,
            detail="Cannot modify outcome on finalized visit",
        )

    # =========================================================
    # RESOLVE ADMISSION (FOR AUDIT CONTEXT)
    # =========================================================
    resolved_admission_id = str(visit.admission_id)

    # =========================================================
    # UPSERT OUTCOME
    # =========================================================
    try:
        outcome = upsert_chha_outcome(
            db=db,
            visit=visit,
            user_id=user_id,
            payload=payload,
        )

        # =====================================================
        # AUDIT LOG (REQUIRED)
        # =====================================================
        _safe_log_event(
            db=db,
            user_id=user_id,
            action="UPSERT_CHHA_OUTCOME",
            entity_type="visit",
            entity_id=visit.id,
            request_id=request_id,
            metadata={
                "visit_id": str(visit.id),
                "patient_id": str(visit.patient_id),
                "admission_id": resolved_admission_id,
                "discipline": discipline,
            },
        )

        db.commit()

    except HTTPException:
        db.rollback()
        raise

    except Exception as exc:
        db.rollback()

        logger.exception(
            "CHHA_OUTCOME_SAVE_FAILED",
            extra={
                "visit_id": str(visit.id),
                "patient_id": str(visit.patient_id),
                "request_id": request_id,
            },
        )

        raise HTTPException(
            status_code=500,
            detail=f"CHHA outcome save failed: {exc}",
        )

    # =========================================================
    # RESPONSE
    # =========================================================
    return {
        "status": "saved",
        "visit_id": str(visit.id),
        "outcome_id": str(outcome.id),
        "request_id": request_id,
    }


# =========================================================
# REFUSAL / RE-OFFER
# =========================================================

@router.post(
    "/patients/{patient_id}/refuse",
    status_code=status.HTTP_201_CREATED,
    response_model=RefusalResponse,
)
def refuse_service(
    patient_id: uuid.UUID,
    payload: RefusalRequest,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    # =========================================================
    # CONTEXT RESOLUTION
    # =========================================================
    request_id = _get_request_id(request, response)
    user_id = _resolve_actor_user_id(db, request)

    # =========================================================
    # LOAD PATIENT
    # =========================================================
    patient = _load_patient_for_update(db, patient_id)
    _set_db_context(db, patient.tenant_id, user_id, request_id)

    # =========================================================
    # NORMALIZE + VALIDATE DISCIPLINE
    # =========================================================
    discipline = (payload.discipline or "").strip().upper()

    ALLOWED_DISCIPLINES = {
        "RN",
        "LVN",
        "SW",
        "CHAPLAIN",
        "AIDE",
        "MD",
        "NP",
        "PA",
    }

    if discipline not in ALLOWED_DISCIPLINES:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid discipline '{payload.discipline}'",
        )

    # =========================================================
    # OPTIONAL: RESOLVE ACTIVE ADMISSION
    # =========================================================
    resolved_admission = (
        db.query(Admission)
        .filter(
            Admission.patient_id == patient.id,
            Admission.tenant_id == patient.tenant_id,
            Admission.status == "ADMITTED",
        )
        .order_by(Admission.created_at.desc())
        .first()
    )

    # (Not blocking — refusal can exist without admission,
    # but we log if present)

    # =========================================================
    # RECORD REFUSAL
    # =========================================================
    try:
        refusal = record_refusal(
            db=db,
            patient=patient,
            user_id=user_id,
            discipline=discipline,
            reason=payload.reason,
        )

        # =====================================================
        # AUDIT LOG (ENHANCED)
        # =====================================================
        _safe_log_event(
            db=db,
            user_id=user_id,
            action="RECORD_REFUSAL",
            entity_type="patient",
            entity_id=patient.id,
            request_id=request_id,
            metadata={
                "discipline": discipline,
                "reason": payload.reason,
                "admission_id": str(resolved_admission.id)
                if resolved_admission
                else None,
            },
        )

        db.commit()

    except ValueError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        )

    except HTTPException:
        db.rollback()
        raise

    except Exception as exc:
        db.rollback()

        logger.exception(
            "REFUSAL_RECORDING_FAILED",
            extra={
                "patient_id": str(patient.id),
                "discipline": discipline,
                "request_id": request_id,
            },
        )

        raise HTTPException(
            status_code=500,
            detail=f"Refusal recording failed: {exc}",
        )

    # =========================================================
    # RESPONSE
    # =========================================================
    return RefusalResponse(
        status="refusal recorded",
        patient_id=str(patient.id),
        discipline=refusal.discipline,
        reason=refusal.reason,
        refused_at=(
            refusal.refused_at.isoformat()
            if getattr(refusal, "refused_at", None)
            else None
        ),
        request_id=request_id,
    )

# =========================================================
# CLINICAL REASONING HELPERS
# =========================================================

def _content_to_dict(raw: Any) -> dict[str, Any]:
    if raw is None:
        return {}
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, str):
        try:
            parsed = json.loads(raw)
            return parsed if isinstance(parsed, dict) else {}
        except (TypeError, ValueError, json.JSONDecodeError):
            return {}
    return {}


def _extract_clinical_reasoning_payload_from_notes(
    notes: list[ClinicalNote],
) -> dict[str, Any]:
    payload: dict[str, Any] = {}

    allowed_keys = [
        "weight",
        "previous_weight",
        "mac",
        "previous_mac",
        "appetite",
        "previous_appetite",
        "appetite_decline",
        "pain_score",
        "previous_pain_score",
        "pain_increase",

        "pain_location",
        "pain_quality",
        "pain_cause_category",
        "pain_cause_text",
        "pain_cause_source",
        "cause_determination",
        "associated_diagnosis_text",
        "associated_diagnosis_type",

        "terminal_diagnosis",
        "primary_diagnosis",
        "assessment_summary",
        "nursing_summary",
        
        "weakness_increased",
        "mobility_decline",
        "transfer_assistance_increased",
        "fall_count",
        "caregiver_tearful",
        "caregiver_overwhelmed",
        "respiratory_rate",
        "previous_respiratory_rate",
        "accessory_muscle_use",
        "oxygen_increase",
        "edema_present",
        "edema_worsening",
        "orthopnea",
        "cognitive_decline",
        "behavior_change",
        "spiritual_distress",
        "fear_of_dying",
        "hopelessness",
    ]

    for note in notes:
        content = _content_to_dict(getattr(note, "content", None))
        if not content:
            continue

        assessment = _content_to_dict(content.get("assessment"))
        observed = _content_to_dict(content.get("observed") or content.get("observations"))
        vitals = _content_to_dict(content.get("vitals"))
        pain = _content_to_dict(content.get("pain") or assessment.get("pain"))
        respiratory = _content_to_dict(content.get("respiratory") or assessment.get("respiratory"))
        nutrition = _content_to_dict(content.get("nutrition") or assessment.get("nutrition"))
        functional = _content_to_dict(content.get("functional") or assessment.get("functional"))
        caregiver = _content_to_dict(content.get("caregiver") or assessment.get("caregiver"))
        spiritual = _content_to_dict(content.get("spiritual") or assessment.get("spiritual"))

        sources = [
            content,
            assessment,
            observed,
            vitals,
            pain,
            respiratory,
            nutrition,
            functional,
            caregiver,
            spiritual,
        ]

        for source_dict in sources:
            for key in allowed_keys:
                if key in source_dict and key not in payload:
                    payload[key] = source_dict[key]

        # Common EMR aliases
        if "muac" in payload and "mac" not in payload:
            payload["mac"] = payload["muac"]
        if "current_weight" in payload and "weight" not in payload:
            payload["weight"] = payload["current_weight"]
        if "prior_weight" in payload and "previous_weight" not in payload:
            payload["previous_weight"] = payload["prior_weight"]
        if "current_mac" in payload and "mac" not in payload:
            payload["mac"] = payload["current_mac"]
        if "previous_muac" in payload and "previous_mac" not in payload:
            payload["previous_mac"] = payload["previous_muac"]

    if payload:
        payload["source"] = "RN"
    
    logger.info(
        "CLINICAL_REASONING_EXTRACTED_PAYLOAD_KEYS keys=%s",
        sorted(payload.keys()),
    )
    
    return payload


def _get_or_create_clinical_reasoning_record_for_visit(
    db: Session,
    visit: Visit,
) -> uuid.UUID:
    existing = db.execute(
        text(
            """
            SELECT id
            FROM clinical_reasoning_records
            WHERE patient_id = :patient_id
              AND episode_id = :episode_id
              AND status = 'active'
            ORDER BY updated_at DESC
            LIMIT 1
            """
        ),
        {
            "patient_id": visit.patient_id,
            "episode_id": visit.id,
        },
    ).scalar_one_or_none()

    if existing:
        return existing

    created = db.execute(
        text(
            """
            INSERT INTO clinical_reasoning_records (
                patient_id,
                episode_id,
                status,
                requires_poc_update,
                requires_physician_review,
                requires_idg_review
            )
            VALUES (
                :patient_id,
                :episode_id,
                'active',
                FALSE,
                FALSE,
                FALSE
            )
            RETURNING id
            """
        ),
        {
            "patient_id": visit.patient_id,
            "episode_id": visit.id,
        },
    ).scalar_one()

    return created


def _run_clinical_reasoning_for_visit(
    db: Session,
    visit: Visit,
    notes: list[ClinicalNote],
    request_id: str,
) -> None:
    assessment_payload = _extract_clinical_reasoning_payload_from_notes(notes)
    
    logger.info(
        "CLINICAL_REASONING_PAYLOAD_KEYS visit_id=%s payload_keys=%s request_id=%s",
        str(visit.id),
        sorted(list(assessment_payload.keys())),
        request_id,
    )
    
    if not assessment_payload:
        logger.info(
            "CLINICAL_REASONING_SKIPPED_EMPTY_PAYLOAD visit_id=%s request_id=%s",
            str(visit.id),
            request_id,
        )
        return

    reasoning_record_id = _get_or_create_clinical_reasoning_record_for_visit(
        db=db,
        visit=visit,
    )

    result = clinical_reasoning_engine.process_assessment(
        db=db,
        reasoning_record_id=reasoning_record_id,
        assessment_data=assessment_payload,
        reset_existing=True,
        commit=False,
    )
    
    recommendation_result = reasoning_recommendation_service.generate_for_patient(
        db=db,
        tenant_id=visit.tenant_id,
        patient_id=visit.patient_id,
        commit=False,
    )

    logger.info(
        "DIAGNOSIS_RECOMMENDATIONS_GENERATED visit_id=%s reasoning_record_id=%s result=%s request_id=%s",
        str(visit.id),
        str(reasoning_record_id),
        recommendation_result,
        request_id,
    )
    
    logger.info(
        "CLINICAL_REASONING_COMPLETED visit_id=%s reasoning_record_id=%s result=%s request_id=%s",
        str(visit.id),
        str(reasoning_record_id),
        result,
        request_id,
    )


# =========================================================
# FINALIZE VISIT
# =========================================================

@router.post("/{visit_id}/finalize", response_model=VisitMutationResponse)
def finalize_visit(
    visit_id: uuid.UUID,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Security(get_current_user),
):
    request_id = _get_request_id(request, response)
    user_id = current_user.user_id
    
    logger.warning(
        "FINALIZE ROUTE ENTERED user_id=%s",
        current_user.user_id,
    )
    
    visit = _load_visit_for_update(db, visit_id)
    _set_db_context(db, visit.tenant_id, user_id, request_id)

    if not getattr(visit, "admission_id", None):
        logger.critical(
            "FINALIZE: BLOCKED_NO_ADMISSION visit_id=%s request_id=%s",
            str(visit.id),
            request_id,
        )
        raise HTTPException(
            status_code=500,
            detail="Visit is not tied to an admission - invalid chart state",
        )

    mode = _normalized_mode_from_visit(visit)
    if mode in TELEPHONE_MODES:
        logger.warning(
            "FINALIZE: BLOCKED_TELEPHONE_MODE visit_id=%s mode=%s request_id=%s",
            str(visit.id),
            mode,
            request_id,
        )
        raise HTTPException(
            status_code=400,
            detail="Telephone interactions are not visits",
        )

    if (visit.status or "").upper() == "FINALIZED":
        logger.info(
            "FINALIZE: ALREADY_FINALIZED visit_id=%s request_id=%s",
            str(visit.id),
            request_id,
        )
        return VisitMutationResponse(
            status="already_finalized",
            visit_id=str(visit.id),
            request_id=request_id,
            completed_task_types=[],
        )

    now = datetime.now(timezone.utc)

    visit_type = _normalize_and_validate_visit_type(
        getattr(visit, "visit_type", "") or ""
    )
    discipline = normalize_visit_type(
        getattr(visit, "visit_discipline", "") or ""
    ).upper()
    form_type = getattr(visit, "form_type", None)

    logger.info(
        "FINALIZE: VISIT_CONTEXT visit_id=%s visit_type=%s discipline=%s form_type=%s request_id=%s",
        str(visit.id),
        visit_type,
        discipline,
        form_type,
        request_id,
    )

    is_admin = visit_type == "ADMINISTRATIVE" or discipline == "ADMINISTRATIVE"
    is_rn = visit_type == "RN" or discipline == "RN"

    if is_admin:
        try:
            visit.status = "FINALIZED"
            if hasattr(visit, "finalized_at"):
                visit.finalized_at = now
            if hasattr(visit, "finalized_by"):
                visit.finalized_by = user_id
            if hasattr(visit, "updated_at"):
                visit.updated_at = now

            db.flush()
            _safe_log_event(
                db=db,
                user_id=user_id,
                action="FINALIZE_VISIT",
                entity_type="visit",
                entity_id=visit.id,
                request_id=request_id,
                metadata={
                    "form_type": form_type,
                    "discipline": discipline,
                    "administrative_bypass": True,
                    "admission_id": str(visit.admission_id),
                },
            )
            db.commit()

            return VisitMutationResponse(
                status="finalized",
                visit_id=str(visit.id),
                request_id=request_id,
                completed_task_types=[],
            )
        except HTTPException:
            db.rollback()
            raise
        except Exception as exc:
            db.rollback()
            logger.exception(
                "FINALIZE: ADMIN_FAILED visit_id=%s request_id=%s",
                str(visit.id),
                request_id,
            )
            raise HTTPException(
                status_code=500,
                detail=f"Administrative visit finalization failed: {exc}",
            )

    if not form_type:
        logger.warning(
            "FINALIZE: BLOCKED_MISSING_FORM_TYPE visit_id=%s request_id=%s",
            str(visit.id),
            request_id,
        )
        raise HTTPException(
            status_code=422,
            detail="Visit cannot be finalized without form_type",
        )

    patient = _load_patient_for_update(db, visit.patient_id)

    notes = (
        db.query(ClinicalNote)
        .filter(
            ClinicalNote.visit_id == visit.id,
            ClinicalNote.tenant_id == visit.tenant_id,
        )
        .all()
    )

    logger.info(
        "FINALIZE: NOTES_LOADED visit_id=%s note_count=%s request_id=%s",
        str(visit.id),
        len(notes),
        request_id,
    )

    if not notes:
        raise HTTPException(
            status_code=422,
            detail="Cannot finalize visit without clinical documentation",
        )

    primary_notes = [note for note in notes if note.note_type]
    if not primary_notes:
        raise HTTPException(
            status_code=422,
            detail="Visit must contain at least one valid clinical form",
        )

    _enforce_rn_supervisory_requirement(
        visit=visit,
        patient=patient,
        is_rn=is_rn,
    )

    blocking_recon_items = (
        db.query(MedReconciliationItem)
        .filter(MedReconciliationItem.patient_id == visit.patient_id)
        .filter(MedReconciliationItem.review_status == "PENDING")
        .order_by(MedReconciliationItem.created_at.asc())
        .all()
    )

    if blocking_recon_items:
        blocking_payload = [
            {
                "item_id": str(item.id),
                "import_id": str(item.import_id) if getattr(item, "import_id", None) else None,
                "med_name_raw": item.med_name_raw,
                "med_name_normalized": getattr(item, "med_name_normalized", None),
                "dose": getattr(item, "dose", None),
                "route": getattr(item, "route", None),
                "frequency": getattr(item, "frequency", None),
                "review_status": item.review_status,
                "comparison_review_reason": getattr(item, "comparison_review_reason", None),
                "requires_immediate_review": getattr(item, "requires_immediate_review", False),
                "is_critical_reaction": getattr(item, "is_critical_reaction", False),
            }
            for item in blocking_recon_items
        ]

        raise HTTPException(
            status_code=400,
            detail={
                "code": "RECON_PENDING",
                "message": (
                    "Cannot finalize visit until all pending medication reconciliation "
                    "items have been reviewed."
                ),
                "count": len(blocking_payload),
                "blocking_items": blocking_payload,
            },
        )

    completed_task_types: list[str] = []

    try:
        visit.status = "FINALIZED"
        if hasattr(visit, "finalized_at"):
            visit.finalized_at = now
        if hasattr(visit, "finalized_by"):
            visit.finalized_by = user_id
        if hasattr(visit, "updated_at"):
            visit.updated_at = now

        db.flush()

        _safe_log_event(
            db=db,
            user_id=user_id,
            action="FINALIZE_VISIT",
            entity_type="visit",
            entity_id=visit.id,
            request_id=request_id,
            metadata={
                "form_type": form_type,
                "discipline": discipline,
                "clinical_note_count": len(notes),
                "admission_id": str(visit.admission_id),
            },
        )
        
        logger.info(
            "CLINICAL_REASONING_GATE_CHECK "
            "visit_id=%s visit_type=%s discipline=%s "
            "is_rn=%s note_count=%s request_id=%s",
            str(visit.id),
            visit_type,
            discipline,
            is_rn,
            len(notes),
            request_id,
        )
        
        if is_rn:
            logger.info(
                "FINALIZE: BEFORE_CLINICAL_REASONING visit_id=%s request_id=%s",
                str(visit.id),
                request_id,
            )
            _run_clinical_reasoning_for_visit(
                db=db,
                visit=visit,
                notes=notes,
                request_id=request_id,
            )
            logger.info(
                "FINALIZE: AFTER_CLINICAL_REASONING visit_id=%s request_id=%s",
                str(visit.id),
                request_id,
            )

        logger.info(
            "FINALIZE: BEFORE_POC_POLICY visit_id=%s request_id=%s",
            str(visit.id),
            request_id,
        )

        from app.services.poc_update_automation import on_visit_finalized_apply_poc_policy

        on_visit_finalized_apply_poc_policy(
            db=db,
            visit=visit,
            patient=patient,
            finalized_by_user_id=user_id,
        )

        auto_complete_tasks_for_visit(
            db=db,
            visit=visit,
            user_id=user_id,
        )

        completed_task_types = _complete_initial_task_for_visit(
            db=db,
            visit=visit,
        )

        _run_condition_detection_non_blocking(
            db=db,
            visit=visit,
            patient=patient,
            user_id=user_id,
            now=now,
            request_id=request_id,
        )

        _run_bereavement_aggregation_non_blocking(
            db=db,
            visit=visit,
            patient=patient,
            user_id=user_id,
            request_id=request_id,
        )

        _run_phase_b_finalize_hooks(
            db=db,
            visit=visit,
            completed_task_types=completed_task_types,
            notes=notes,
            request_id=request_id,
        )

        db.commit()

        logger.info(
            "FINALIZE: SUCCESS visit_id=%s request_id=%s completed_task_types=%s",
            str(visit.id),
            request_id,
            completed_task_types,
        )

    except HTTPException:
        db.rollback()
        raise
    except ValueError as exc:
        db.rollback()
        logger.exception(
            "FINALIZE: VALUE_ERROR_ROLLBACK visit_id=%s request_id=%s",
            str(visit.id),
            request_id,
        )
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        )
    except Exception as exc:
        db.rollback()
        logger.exception(
            "FINALIZE: FAILED_ROLLBACK visit_id=%s patient_id=%s request_id=%s",
            str(visit.id),
            str(visit.patient_id),
            request_id,
        )
        raise HTTPException(
            status_code=500,
            detail=f"Visit finalization failed: {exc}",
        )

    return VisitMutationResponse(
        status="finalized",
        visit_id=str(visit.id),
        request_id=request_id,
        completed_task_types=completed_task_types,
    )

# =========================================================
# Pydantic model rebuild (REQUIRED FOR FASTAPI + V2)
# =========================================================

VisitStatusUpdate.model_rebuild()
VisitCreateRequest.model_rebuild()
RefusalRequest.model_rebuild()
VisitMutationResponse.model_rebuild()
VisitReopenRequest.model_rebuild()
VisitCreateResponse.model_rebuild()
RefusalResponse.model_rebuild()