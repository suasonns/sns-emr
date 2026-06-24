
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Set, Generator, Any

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
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
from app.models.chha_visit_outcome import CHHAVisitOutcome
from app.services.chha_outcome_service import upsert_chha_outcome

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


logger = logging.getLogger(__name__)

if not logger.handlers:
    logging.basicConfig(level=logging.INFO)

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

# =========================================================
# ENGINE SINGLETONS
# =========================================================

condition_engine = DynamicConditionDetectionEngine()
bereavement_engine = BereavementAggregationEngine()

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
    patient_id: uuid.UUID = Field(
        ...,
        description="Patient identifier",
    )

    visit_type: str = Field(
        ...,
        description="Discipline: RN, LVN, CHHA, MSW, BSW, LCSW, SC, MD, NP, PA, ADMIN",
    )

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

    level_of_care: Optional[str] = Field(
        None,
        description="RC, CC, IP, RSP",
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
    task_results: List[CHHATaskResultItem] = []

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
    except Exception:
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


from calendar import monthrange
from sqlalchemy import and_
from sqlalchemy.dialects.postgresql import JSONB  # only if already available/used elsewhere

ASSESSMENT_EVENT_FORM_TYPES: Set[str] = {
    VisitFormType.ASSESS.value,
}

def _normalize_event_type_for_form(
    form_type: str,
    raw: Optional[str],
) -> Optional[str]:
    """
    event_type is only meaningful for assessment-driven workflows.
    For all other visit workflows, do not block creation based on event_type.
    """
    if form_type not in ASSESSMENT_EVENT_FORM_TYPES:
        return None

    if not raw:
        return None

    value = str(raw).strip().upper()
    allowed = {"CHANGE_OF_CONDITION", "NEW_ORDER", "UPDATE_ASSESSMENT", "RECERT"}

    if value not in allowed:
        raise HTTPException(
            status_code=422,
            detail=(
                f"Invalid event_type '{raw}' for form_type '{form_type}'. "
                f"Allowed: {sorted(allowed)}"
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
            detail=f"Invalid visit_type '{raw}'. Allowed: {sorted(ALLOWED_VISIT_TYPES | set(VISIT_TYPE_ALIASES.keys()))}",
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

    NOTE: Requires VisitFormType.ROUTINE_VISIT to exist in app.models.enums.
    """
    discipline = _canonicalize_discipline(discipline)
    form_type = _normalize_and_validate_form_type(form_type)
    schedule = _normalize_schedule_type(visit_schedule_type)
    event = event_type  # already normalized upstream

    issue_present = event in ISSUE_EVENT_TYPES
    is_prn = schedule == "UNSCHEDULED"

    # SOCIAL WORK FAMILY
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

    # SHORT FORM = PRN FALSE ALARM ONLY FOR RN/LVN
    if form_type == VisitFormType.SHORT_FORM.value:
        if discipline not in {"RN", "LVN"}:
            raise HTTPException(
                status_code=422,
                detail="SHORT_FORM is only allowed for RN or LVN.",
            )

        if not is_prn:
            raise HTTPException(
                status_code=422,
                detail=(
                    "SHORT_FORM is only allowed for PRN/unscheduled visits "
                    "with no issues found on assessment."
                ),
            )

        if issue_present:
            raise HTTPException(
                status_code=422,
                detail=(
                    "SHORT_FORM is not allowed when issues are present. "
                    "RN must use ASSESS with UPDATE_ASSESSMENT. "
                    "LVN must use ROUTINE_VISIT and escalate change of condition per protocol."
                ),
            )
        return

    # RN ISSUE PATH
    if discipline == "RN":
        if issue_present:
            if form_type != VisitFormType.ASSESS.value:
                raise HTTPException(
                    status_code=422,
                    detail=(
                        "RN must use ASSESS when issues are present. "
                        "For PRN with issues, use ASSESS + event_type=UPDATE_ASSESSMENT."
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

    # LVN ISSUE PATH
    if discipline == "LVN":
        if issue_present:
            if form_type != VisitFormType.ROUTINE_VISIT.value:
                raise HTTPException(
                    status_code=422,
                    detail=(
                        "LVN with issues must use ROUTINE_VISIT (routine SN form). "
                        "LVN cannot use SHORT_FORM when issues are present."
                    ),
                )
            return
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

    row = db.execute(
        text("SELECT id FROM users ORDER BY created_at ASC LIMIT 1")
    ).fetchone()
    if not row:
        raise HTTPException(status_code=500, detail="No users available")
    return row[0]

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

# =========================================================
# SUPERVISORY LOGIC HELPERS
# =========================================================

def _get_patient_refusal_flag(patient: Patient, service_key: str) -> bool:
    """
    Safe local refusal check.

    Uses optional patient-level flags if they exist.
    """
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
    """
    Determine whether the patient actively has the discipline on service.
    """
    key = service_key.strip().upper()

    if key == "CHHA":
        return bool(getattr(patient, "has_chha", False))

    if key == "LVN":
        return bool(getattr(patient, "has_lvn", False))

    return False


def _read_supervisory_targets_from_visit(visit: Visit) -> list[str]:
    """
    Read supervisory targets from visit.details if present.
    """
    details = getattr(visit, "details", None)
    if not isinstance(details, dict):
        return []

    targets = details.get("supervisory_targets")
    if not isinstance(targets, list):
        return []

    return [str(t).strip().upper() for t in targets if str(t).strip()]


def _last_rn_supervisory_visit_for_target(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    patient_id: uuid.UUID,
    target: str,
) -> Optional[Visit]:
    """
    Return the most recent FINALIZED RN supervisory visit for a target.
    """
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
    """
    CMS-backed logic:
    - only relevant if CHHA services are active
    - not applicable if CHHA services are refused
    - on-site RN supervisory visit required at least every 14 days
      when hospice aide services are active. 
    """
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
    """
    SNS operational policy:
    - only relevant if LVN services are active
    - not applicable if LVN services are refused
    - RN supervisory review expected monthly when LVN services remain active
    """
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
    """
    Determine if this new visit should be marked supervisory.

    RULES:
    - only RN ROUTINE_VISIT can satisfy routine supervisory context
    - RN cannot supervise RN care
    - supervision applies only when another discipline's services are active
      and not refused
    - CHHA supervision: every 14 days when aide services are active
    - LVN supervision: monthly per SNS workflow policy
    """
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
    """
    Persist supervisory context without requiring a schema migration.

    Stores:
    - visit.is_supervisory
    - visit.details["supervisory_targets"]
    """
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

def _complete_task_with_visit(task: Task, visit: Visit, now: datetime):
    """
    Canonical completion logic for visit-linked tasks.

    Ensures:
    - status = COMPLETED
    - completed_at timestamp
    - completion_reference_type = VISIT
    - completion_reference_id = visit.id
    - audit fields updated

    Idempotent:
    - Does nothing if task is already COMPLETED
    """

    # -----------------------------------------------------
    # SAFETY VALIDATION
    # -----------------------------------------------------
    if not getattr(task, "tenant_id", None):
        raise ValueError("Task missing tenant_id")

    if not getattr(visit, "id", None):
        raise ValueError("Visit missing id")

    # Idempotency guard
    if task.status == TaskStatus.COMPLETED:
        return

    # -----------------------------------------------------
    # COMPLETE TASK
    # -----------------------------------------------------
    task.status = TaskStatus.COMPLETED
    task.completed_at = now

    task.completion_reference_type = (
        CompletionReferenceType.VISIT
        if hasattr(CompletionReferenceType, "VISIT")
        else "VISIT"
    )

    task.completion_reference_id = visit.id

    # -----------------------------------------------------
    # AUDIT FIELDS
    # -----------------------------------------------------
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
    """
    Complete initial discipline onboarding task tied to visit.

    Rules:
    - RN → INITIAL_RN_ICA
    - SW → INITIAL_MSW_ICA
    - CHAPLAIN → INITIAL_SC_ICA

    Completion requires:
    - status = COMPLETED
    - completed_at timestamp
    - completion_reference_type = VISIT
    - completion_reference_id = visit.id
    """

    # -----------------------------------------------------
    # VALIDATION
    # -----------------------------------------------------
    if not getattr(visit, "tenant_id", None):
        raise ValueError("Visit missing tenant_id")

    visit_type = _normalize_and_validate_visit_type(
        getattr(visit, "visit_type", "") or ""
    )

    discipline = normalize_visit_type(
        getattr(visit, "visit_discipline", "") or ""
    ).upper()

    # -----------------------------------------------------
    # RESOLVE TARGET TASK TYPE
    # -----------------------------------------------------
    target_task_type = None

    if visit_type == "RN" or discipline == "RN":
        target_task_type = TaskType.INITIAL_RN_ICA

    elif visit_type == "SW" or discipline == "SW":
        target_task_type = TaskType.INITIAL_MSW_ICA

    elif visit_type == "CHAPLAIN" or discipline == "CHAPLAIN":
        target_task_type = TaskType.INITIAL_SC_ICA

    if not target_task_type:
        return []

    # -----------------------------------------------------
    # FIND ACTIVE TASK (CRITICAL FIX)
    # -----------------------------------------------------
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

    if not task:
        return []

    # -----------------------------------------------------
    # COMPLETE TASK (COMPLIANCE-SAFE)
    # -----------------------------------------------------
    now = datetime.now(timezone.utc)

    _complete_task_with_visit(task, visit, now)

    logger.info(
        "Completed initial task task_type=%s patient_id=%s via visit_id=%s",
        target_task_type.value,
        str(getattr(visit, "patient_id", None)),
        str(getattr(visit, "id", None)),
    )

    task.completion_reference_id = visit.id

    # -----------------------------------------------------
    # AUDIT FIELDS
    # -----------------------------------------------------
    if hasattr(task, "updated_at"):
        task.updated_at = now

    if hasattr(task, "updated_by"):
        task.updated_by = (
            getattr(visit, "finalized_by", None)
            or getattr(visit, "provider_id", None)
        )

    # -----------------------------------------------------
    # LOGGING (OPTIONAL BUT GOOD)
    # -----------------------------------------------------
    logger.info(
        "Completed initial task task_type=%s patient_id=%s via visit_id=%s",
        target_task_type.value,
        str(getattr(visit, "patient_id", None)),
        str(getattr(visit, "id", None)),
    )

    return [target_task_type.value]

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
    """
    Create a condition-triggered task if no ACTIVE task exists.

    ACTIVE = PENDING, IN_PROGRESS, OVERDUE

    Returns:
        True if created
        False if skipped (already exists or invalid)
    """

    # -----------------------------------------------------
    # VALIDATION
    # -----------------------------------------------------
    if not getattr(patient, "tenant_id", None):
        raise ValueError("Patient missing tenant_id")

    task_type_member = _get_task_type_member(task_type_name)
    if task_type_member is None:
        logger.warning("Missing TaskType enum member: %s", task_type_name)
        return False

    # -----------------------------------------------------
    # ACTIVE TASK CHECK (CRITICAL FIX)
    # -----------------------------------------------------
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

    # -----------------------------------------------------
    # CREATE TASK
    # -----------------------------------------------------
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

    # -----------------------------------------------------
    # DUE FIELDS
    # -----------------------------------------------------
    if hasattr(task, "due_date"):
        task.due_date = now.date()

    if hasattr(task, "due_at"):
        task.due_at = now

    # -----------------------------------------------------
    # ENUM SAFE ASSIGNMENTS
    # -----------------------------------------------------
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

    # -----------------------------------------------------
    # FINALIZE
    # -----------------------------------------------------
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
    """
    Finalization integrity check.

    Do NOT assume every RN routine visit is supervisory.
    Supervisory applies only when:
    - another discipline's services remain active
    - supervision is due
    - services were not refused

    This function now only validates internal consistency.
    """
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

    if (visit.status or "").upper() == "FINALIZED":
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
):
    request_id = _get_request_id(request, response)
    user_id = _resolve_actor_user_id(db, request)

    patient = _load_patient_for_update(db, payload.patient_id)
    _set_db_context(db, patient.tenant_id, user_id, request_id)

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

    is_supervisory = False
    supervisory_targets: list[str] = []

    is_supervisory, supervisory_targets = _determine_supervisory_context(
        db=db,
        patient=patient,
        normalized_visit_type=normalized,
        validated_form_type=validated_form_type,
        now=now,
    )

    primary_form: Optional[str] = None
    attached_forms: list[str] = []
    form_family: Optional[str] = None
    modules: list[str] = []
    resolved_by: Optional[str] = None

    visit = Visit(
        id=uuid.uuid4(),
        tenant_id=patient.tenant_id,
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
        
        db.add(visit)
        db.flush()

        _apply_supervisory_context_to_visit(
            visit=visit,
            is_supervisory=is_supervisory,
            supervisory_targets=supervisory_targets,
        )

        form_config = resolve_form_package(

            discipline=normalized,
            form_type=validated_form_type,
            level_of_care=getattr(payload, "level_of_care", None),
            event_type=validated_event_type,
        )

        if not form_config or not form_config.get("primary_form"):
            logger.error(
                "FORM_RESOLUTION_FAILED",
                extra={
                    "discipline": normalized,
                    "form_type": validated_form_type,
                    "event_type": validated_event_type,
                    "request_id": request_id,
                },
            )
            raise HTTPException(
                status_code=422,
                detail="Unable to resolve form package",
            )

        primary_form = _guard_against_generic_note_type(
            form_config.get("primary_form"),
            request_id=request_id,
        )

        attached_forms = [
            _guard_against_generic_note_type(name, request_id=request_id)
            for name in list(form_config.get("attached_forms", []))
        ]

        resolved_form_family = form_config.get("form_family")
        form_family = (
            resolved_form_family.value
            if hasattr(resolved_form_family, "value")
            else resolved_form_family
        )

        modules = list(form_config.get("modules", []))
        resolved_by = form_config.get("resolved_by")

        primary_note = ClinicalNote(
            id=uuid.uuid4(),
            visit_id=visit.id,
            author_id=user_id,
            tenant_id=visit.tenant_id,
            patient_id=visit.patient_id,
            note_type=primary_form,
            note_category=primary_form,
            discipline=visit.visit_discipline,
            form_family=form_family,
            encounter_type="VISIT",
            visit_origin="VISIT_CREATE",
            status="DRAFT",
            encounter_date=now.date(),
            content="",
            created_by=user_id,
            created_at=now,
            updated_at=now,
        )
        db.add(primary_note)

        for form_name in attached_forms:
            db.add(
                ClinicalNote(
                    id=uuid.uuid4(),
                    visit_id=visit.id,
                    author_id=user_id,
                    tenant_id=visit.tenant_id,
                    patient_id=visit.patient_id,
                    note_type=form_name,
                    note_category=form_name,
                    discipline=visit.visit_discipline,
                    form_family=form_family,
                    encounter_type="VISIT",
                    visit_origin="VISIT_CREATE",
                    status="DRAFT",
                    encounter_date=now.date(),
                    content="",
                    created_by=user_id,
                    created_at=now,
                    updated_at=now,
                )
            )

        _safe_log_event(
            db=db,
            user_id=user_id,
            action="CREATE_VISIT",
            entity_type="visit",
            entity_id=visit.id,
            request_id=request_id,
            metadata={
                "discipline": normalized,
                "form_type": validated_form_type,
                "visit_schedule_type": validated_schedule_type,
                "event_type": validated_event_type,
                "primary_form": primary_form,
                "attached_forms": attached_forms,
                "resolved_by": resolved_by,
            },
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
                "discipline": normalized,
                "form_type": validated_form_type,
                "event_type": validated_event_type,
                "request_id": request_id,
            },
        )
        raise HTTPException(
            status_code=500,
            detail=f"Visit creation failed: {exc}",
        )

    return VisitCreateResponse(
        visit_id=str(visit.id),
        visit_type=normalized,
        form_type=validated_form_type,
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
):
    request_id = _get_request_id(request, response)
    user_id = _resolve_actor_user_id(db, request)
    actor_role = _resolve_actor_role(request)

    visit = _load_visit_for_update(db, visit_id)
    _set_db_context(db, visit.tenant_id, user_id, request_id)

    current_status = (getattr(visit, "status", "") or "").upper()
    if current_status != "FINALIZED":
        raise HTTPException(
            status_code=409,
            detail="Only FINALIZED visits can be reopened.",
        )

    if actor_role not in ALLOWED_REOPEN_ROLES:
        raise HTTPException(
            status_code=403,
            detail="Supervisor or admin approval is required to reopen finalized documentation.",
        )

    now = datetime.now(timezone.utc)

    early_lock, early_lock_reason = _visit_has_early_lock(visit)
    if early_lock:
        raise HTTPException(
            status_code=409,
            detail=(
                f"This documentation is locked because '{early_lock_reason}' is present. "
                "Add an amendment instead of modifying the original record."
            ),
        )

    if not _visit_is_within_correction_window(visit, now):
        raise HTTPException(
            status_code=409,
            detail=(
                "This documentation is outside the 72-hour correction window. "
                "Add an amendment instead of modifying the original record."
            ),
        )

    try:
        _apply_reopen_metadata(
            visit=visit,
            user_id=user_id,
            reason=payload.reason,
            now=now,
        )

        db.flush()

        _safe_log_event(
            db=db,
            user_id=user_id,
            action="REOPEN_VISIT",
            entity_type="visit",
            entity_id=visit.id,
            request_id=request_id,
            metadata={"reason": payload.reason},
        )

        db.commit()

    except HTTPException:
        db.rollback()
        raise
    except Exception as exc:
        db.rollback()
        logger.exception(
            "Visit reopen failed",
            extra={"visit_id": str(visit.id), "request_id": request_id},
        )
        raise HTTPException(
            status_code=500,
            detail=f"Visit reopen failed: {exc}",
        )

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
    request_id = _get_request_id(request, response)
    user_id = _resolve_actor_user_id(db, request)

    visit = _load_visit_for_update(db, visit_id)
    _set_db_context(db, visit.tenant_id, user_id, request_id)

    try:
        outcome = upsert_chha_outcome(
            db=db,
            visit=visit,
            user_id=user_id,
            payload=payload,
        )

        db.commit()

    except HTTPException:
        db.rollback()
        raise

    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"CHHA outcome save failed: {exc}"
        )

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
    request_id = _get_request_id(request, response)
    user_id = _resolve_actor_user_id(db, request)

    patient = _load_patient_for_update(db, patient_id)
    _set_db_context(db, patient.tenant_id, user_id, request_id)

    try:
        refusal = record_refusal(
            db=db,
            patient=patient,
            user_id=user_id,
            discipline=payload.discipline,
            reason=payload.reason,
        )

        _safe_log_event(
            db=db,
            user_id=user_id,
            action="RECORD_REFUSAL",
            entity_type="patient",
            entity_id=patient.id,
            request_id=request_id,
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
            "Refusal recording failed",
            extra={
                "patient_id": str(patient.id),
                "discipline": payload.discipline,
                "request_id": request_id,
            },
        )
        raise HTTPException(
            status_code=500,
            detail=f"Refusal recording failed: {exc}",
        )

    return RefusalResponse(
        status="refusal recorded",
        patient_id=str(patient.id),
        discipline=refusal.discipline,
        reason=refusal.reason,
        refused_at=refusal.refused_at.isoformat() if refusal.refused_at else None,
        request_id=request_id,
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
):
    request_id = _get_request_id(request, response)
    user_id = _resolve_actor_user_id(db, request)

    visit = _load_visit_for_update(db, visit_id)
    _set_db_context(db, visit.tenant_id, user_id, request_id)

    mode = _normalized_mode_from_visit(visit)
    if mode in TELEPHONE_MODES:
        raise HTTPException(
            status_code=400,
            detail="Telephone interactions are not visits",
        )

    if (visit.status or "").upper() == "FINALIZED":
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

    if not form_type:
        raise HTTPException(
            status_code=422,
            detail="Visit cannot be finalized without form_type",
        )

    is_admin = visit_type == "ADMINISTRATIVE" or discipline == "ADMINISTRATIVE"
    is_rn = visit_type == "RN" or discipline == "RN"

    patient = _load_patient_for_update(db, visit.patient_id)

    notes = (
        db.query(ClinicalNote)
        .filter(
            ClinicalNote.visit_id == visit.id,
            ClinicalNote.tenant_id == visit.tenant_id,
        )
        .all()
    )

    if not notes:
        raise HTTPException(
            status_code=422,
            detail="Cannot finalize visit without clinical documentation",
        )

    primary_notes = [n for n in notes if (n.note_type and n.note_category)]

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

    visit.status = "FINALIZED"

    if hasattr(visit, "finalized_at"):
        visit.finalized_at = now
    if hasattr(visit, "finalized_by"):
        visit.finalized_by = user_id
    if hasattr(visit, "updated_at"):
        visit.updated_at = now

    completed_task_types: list[str] = []

    try:
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
            },
        )

        if is_admin:
            db.commit()
            return VisitMutationResponse(
                status="finalized",
                visit_id=str(visit.id),
                request_id=request_id,
                completed_task_types=[],
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

        db.commit()

    except HTTPException:
        db.rollback()
        raise

    except ValueError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        )

    except Exception as exc:
        db.rollback()
        logger.exception(
            "Visit finalization failed",
            extra={
                "visit_id": str(visit.id),
                "patient_id": str(visit.patient_id),
                "request_id": request_id,
            },
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
