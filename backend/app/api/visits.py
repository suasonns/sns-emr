from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone, timedelta
from typing import Any, Generator, Optional, Set

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.core.visit_type_normalizer import normalize_visit_type
from app.models.enums import TaskStatus, TaskType
from app.models.patient import Patient
from app.models.task import Task
from app.models.visit import Visit
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
from app.services.visit_compliance_guards import (
    enforce_commlog_for_visit_status_change,
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
    status: str = Field(..., description="Allowed: MISSED, RESCHEDULED")
    communications_log_id: Optional[uuid.UUID] = Field(
        None,
        description="Required when status is MISSED or RESCHEDULED",
    )


class VisitCreateRequest(BaseModel):
    patient_id: uuid.UUID
    visit_type: str = Field(
        ...,
        description="RN/LVN/NP/MD/SW/CHAPLAIN/AIDE/ADMINISTRATIVE",
    )


class RefusalRequest(BaseModel):
    discipline: str = Field(
        ...,
        description="Allowed: LVN/AIDE/CHHA/HHA/MSW/LCSW/SW/CHAPLAIN/SC/RN/MD/F2F",
    )
    reason: Optional[str] = Field(
        None,
        description="Optional free-text refusal reason",
    )


class VisitMutationResponse(BaseModel):
    status: str
    visit_id: str
    request_id: str
    completed_task_types: list[str] = Field(default_factory=list)
    new_status: Optional[str] = None
    communications_log_id: Optional[str] = None

class VisitReopenRequest(BaseModel):
    reason: str = Field(..., min_length=5, max_length=2000)

class VisitCreateResponse(BaseModel):
    visit_id: str
    visit_type: str
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
    """
    Auth-ready extraction path.

    Supported locations:
    - request.state.user_id
    - request.state.user.id
    - X-User-Id header (dev/integration fallback only)

    Replace this later with your real auth dependency if/when available.
    """
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
    """
    Production-ready resolution shape:
    1) authenticated user from request context
    2) fallback to first user ONLY if request context unavailable

    Keep fallback for now so local environments do not break.
    Remove fallback once auth is fully wired.
    """
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


def _normalize_and_validate_visit_type(raw: str) -> str:
    normalized = normalize_visit_type(raw or "")
    if normalized not in ALLOWED_VISIT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid visit_type '{raw}'. Allowed: {sorted(ALLOWED_VISIT_TYPES)}",
        )
    return normalized

VISIT_CORRECTION_WINDOW_HOURS = 72
ALLOWED_REOPEN_ROLES = {"ADMIN", "SUPERVISOR", "DON", "QA", "SYSTEM"}


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
    """
    Signed/reviewed documents lock before the 72-hour window expires.
    """
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
    """
    Preserve audit trail while marking current version reopened.
    If structured visit versioning is not yet implemented, store metadata safely
    on visit.details when available.
    """
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


def _complete_initial_task_for_visit(
    db: Session,
    visit: Visit,
) -> list[str]:
    """
    Deterministic local fallback for initial ICA task completion.
    This prevents finalization from succeeding without evidence linkage
    when downstream automation does not complete the task.
    """
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

    task = (
        db.query(Task)
        .execution_options(skip_tenant_filter=True)
        .with_for_update()
        .filter(
            Task.tenant_id == visit.tenant_id,
            Task.patient_id == visit.patient_id,
            Task.task_type == target_task_type,
            Task.status == TaskStatus.PENDING,
        )
        .first()
    )

    if not task:
        return []

    now = datetime.now(timezone.utc)

    task.status = TaskStatus.COMPLETED
    task.completed_at = now
    task.completion_reference_type = "VISIT"
    task.completion_reference_id = visit.id

    if hasattr(task, "updated_at"):
        task.updated_at = now

    return [target_task_type.value]


def _get_task_type_member(task_type_name: str):
    """
    Safe enum lookup so missing enum values do not crash visit finalization.
    Examples:
      - MSW_REOFFER
      - CHAPLAIN_REOFFER
    """
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
    Idempotent creation of condition-triggered re-offer tasks.

    Returns:
      True  -> task created
      False -> already existed or enum unavailable
    """
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
            Task.status == TaskStatus.PENDING,
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

    if hasattr(task, "origin"):
        task.origin = "SYSTEM"

    if hasattr(task, "discipline"):
        task.discipline = discipline_value

    if hasattr(task, "regulatory_basis"):
        task.regulatory_basis = "CONDITION_TRIGGER"

    if hasattr(task, "alert_reason"):
        task.alert_reason = task_type_name

    db.add(task)
    return True


def _fetch_visit_related_notes(db: Session, visit: Visit) -> list[Any]:
    """
    Best-effort loader for notes tied to a visit/patient.
    This avoids hard import failures if note models differ between environments.

    If no compatible note model exists yet, returns an empty list.
    """
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
    """
    Non-blocking condition detection integration.
    Any failure is logged but does not block visit finalization.
    """
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
    """
    Non-blocking bereavement aggregation.
    Any failure is logged but does not block visit finalization.
    """
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
    Supervisory RN rule:
    - applies only to RN visits
    - ROUTINE acuity
    - patient has support staff (CHHA or LVN)
    - no wounds
    - visit must be marked supervisory before finalization
    """
    acuity = (getattr(patient, "acuity_state", "") or "").upper()
    has_wounds = bool(getattr(patient, "has_wounds", False))
    has_support_staff = bool(
        getattr(patient, "has_chha", False) or getattr(patient, "has_lvn", False)
    )

    if (
        is_rn
        and acuity == "ROUTINE"
        and has_support_staff
        and not has_wounds
        and not getattr(visit, "is_supervisory", False)
    ):
        raise HTTPException(
            status_code=400,
            detail="RN supervisory visit required because patient has CHHA or LVN assigned",
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


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=VisitCreateResponse)
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

    normalized = _normalize_and_validate_visit_type(payload.visit_type)
    now = datetime.now(timezone.utc)

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
        created_at=now,
        updated_at=now,
        created_by=user_id,
    )

    try:
        db.add(visit)
        db.flush()

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
            "Visit creation failed",
            extra={
                "patient_id": str(patient.id),
                "visit_type": normalized,
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
    """
    Record a refusal and trigger re-offer / escalation.
    """
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

    is_admin = visit_type == "ADMINISTRATIVE" or discipline == "ADMINISTRATIVE"
    is_rn = visit_type == "RN" or discipline == "RN"

    patient = _load_patient_for_update(db, visit.patient_id)

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
        )

        if is_admin:
            db.commit()
            return VisitMutationResponse(
                status="finalized",
                visit_id=str(visit.id),
                request_id=request_id,
                completed_task_types=[],
            )

        # Keep local import if your project still has circular import sensitivity.
        from app.services.poc_task_service import handle_poc_on_finalized_rn_visit

        handle_poc_on_finalized_rn_visit(
            db=db,
            patient=patient,
            visit=visit,
            benefit_period_id=getattr(visit, "benefit_period_id", None),
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
