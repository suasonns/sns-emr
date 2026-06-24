from __future__ import annotations

import logging
from datetime import date, datetime, time, timedelta, timezone
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy.orm import Query, Session

from app.domain.care_model_engine import (
    determine_care_model,
    should_anchor_poc_from_rn_visit,
)
from app.domain.visits import normalize_visit_type as normalize_domain_visit_type
from app.models.enums import (
    CompletionReferenceType,
    TaskDiscipline,
    TaskOrigin,
    TaskRegulatoryBasis,
    TaskStatus,
    TaskType,
)
from app.models.patient import Patient
from app.models.task import Task
from app.models.visit import Visit

logger = logging.getLogger("sns_emr")


# =========================================================
# TIME HELPERS
# =========================================================

def utcnow() -> datetime:
    """
    Return an aware UTC datetime.

    Appropriate for task tables using timestamp with time zone.
    """
    return datetime.now(timezone.utc)


def _date_to_utc_datetime(value: date) -> datetime:
    """
    Convert a date to a UTC datetime at midnight.

    Used only for models that expose due_at in addition to due_date.
    """
    return datetime.combine(value, time.min, tzinfo=timezone.utc)


# =========================================================
# ENUM HELPERS
# =========================================================

def _active_poc_statuses() -> list[TaskStatus]:
    """
    Canonical active statuses for POC task lookup.

    ACTIVE = unresolved workflow states.
    """
    statuses: list[TaskStatus] = []

    for name in ("PENDING", "IN_PROGRESS", "OVERDUE"):
        member = getattr(TaskStatus, name, None)
        if member is not None and member not in statuses:
            statuses.append(member)

    if not statuses:
        raise ValueError(
            "TaskStatus enum has no usable active statuses. "
            "Expected at least PENDING, IN_PROGRESS, or OVERDUE."
        )

    return statuses


def _default_new_task_status() -> TaskStatus:
    """
    Default status for newly created POC tasks.
    """
    member = getattr(TaskStatus, "PENDING", None)
    if member is not None:
        return member

    raise ValueError("TaskStatus enum has no usable PENDING member")


def _completed_status() -> TaskStatus:
    completed = getattr(TaskStatus, "COMPLETED", None)
    if completed is None:
        raise ValueError("TaskStatus enum has no COMPLETED member")
    return completed


def _default_manual_origin() -> TaskOrigin:
    """
    Origin used for same-day crisis POC behavior.
    """
    for name in ("MANUAL", "SYSTEM"):
        member = getattr(TaskOrigin, name, None)
        if member is not None:
            return member

    raise ValueError("TaskOrigin enum has no usable MANUAL or SYSTEM member")


def _default_periodic_origin() -> TaskOrigin:
    """
    Origin used for routine periodic POC cycle tasks.
    """
    for name in ("PERIODIC", "SYSTEM"):
        member = getattr(TaskOrigin, name, None)
        if member is not None:
            return member

    raise ValueError("TaskOrigin enum has no usable PERIODIC or SYSTEM member")


def _is_periodic_origin(origin: TaskOrigin) -> bool:
    return origin == _default_periodic_origin()


def _visit_reference_type() -> CompletionReferenceType | str:
    """
    Resolve VISIT completion reference type safely.

    Supports enum-backed columns and fallback-to-string style schemas.
    """
    member = getattr(CompletionReferenceType, "VISIT", None)
    return member if member is not None else "VISIT"


def _regulatory_basis_poc_update() -> TaskRegulatoryBasis | str:
    """
    Resolve POC_UPDATE regulatory basis safely.

    Supports enum-backed columns and fallback-to-string style schemas.
    """
    member = getattr(TaskRegulatoryBasis, "POC_UPDATE", None)
    return member if member is not None else "POC_UPDATE"


def _resolve_task_discipline(value: Optional[str]) -> TaskDiscipline | str:
    """
    Normalize task discipline safely.

    Falls back to RN if a usable mapped discipline is not available.
    """
    normalized = (value or "").strip().upper()

    candidate_order = {
        "RN": ("RN",),
        "LVN": ("LVN",),
        "NP": ("NP",),
        "MD": ("MD",),
        "CHHA": ("CHHA",),
        "AIDE": ("AIDE",),
        "SW": ("SW", "MSW", "BSW", "LCSW"),
        "MSW": ("MSW", "SW", "BSW", "LCSW"),
        "BSW": ("BSW", "MSW", "SW", "LCSW"),
        "LCSW": ("LCSW", "MSW", "SW", "BSW"),
        "SC": ("SC", "CHAPLAIN"),
        "CHAPLAIN": ("CHAPLAIN", "SC"),
    }

    for candidate in candidate_order.get(normalized, (normalized,)):
        member = getattr(TaskDiscipline, candidate, None)
        if member is not None:
            return member

    fallback = getattr(TaskDiscipline, "RN", None)
    return fallback if fallback is not None else "RN"


# =========================================================
# VISIT NORMALIZATION HELPERS
# =========================================================

def normalize_visit_type(value: Optional[str]) -> str:
    """
    Normalize visit type using the canonical domain visit normalizer.

    Returns an empty string for invalid/missing values so service-level logic can
    safely return None instead of raising during read/automation paths.
    """
    if value is None:
        return ""

    try:
        return normalize_domain_visit_type(value)
    except ValueError:
        return ""


def _get_visit_type(visit: Visit) -> str:
    """
    Resolve visit type from the visit object.

    Preferred:
    - visit.visit_discipline

    Fallback:
    - visit.visit_type
    """
    discipline = getattr(visit, "visit_discipline", None)
    if discipline:
        return normalize_visit_type(str(discipline))

    visit_type = getattr(visit, "visit_type", None)
    return normalize_visit_type(str(visit_type) if visit_type is not None else None)


def _is_rn_visit(visit: Visit) -> bool:
    return _get_visit_type(visit) == "RN"


def _is_supervisory_visit(visit: Visit) -> bool:
    """
    Normalize supervisory visit detection.

    Canonical:
    - visit.is_supervisory

    Legacy fallback:
    - visit.supervisory
    """
    return bool(
        getattr(visit, "is_supervisory", False)
        or getattr(visit, "supervisory", False)
    )


def _resolve_visit_service_date(visit: Visit) -> date:
    """
    Resolve the service date for a visit.

    Preferred order:
    1. visit.visit_date
    2. visit.visit_datetime
    3. visit.finalized_at
    4. visit.created_at

    Raises:
        ValueError if no usable date exists.
    """
    candidate_values = [
        getattr(visit, "visit_date", None),
        getattr(visit, "visit_datetime", None),
        getattr(visit, "finalized_at", None),
        getattr(visit, "created_at", None),
    ]

    for value in candidate_values:
        if value is None:
            continue

        if isinstance(value, datetime):
            return value.date()

        if isinstance(value, date):
            return value

    raise ValueError("Visit has no usable service date")


# =========================================================
# TENANT SCOPING HELPERS
# =========================================================

def _apply_tenant_scope(
    query: Query,
    *,
    tenant_id,
) -> Query:
    """
    Apply explicit tenant scope when the Task model exposes tenant_id.

    This keeps the module safe even when skip_tenant_filter=True is used.
    """
    if tenant_id is not None and hasattr(Task, "tenant_id"):
        query = query.filter(Task.tenant_id == tenant_id)
    return query


def _resolve_tenant_id(
    *,
    patient: Optional[Patient] = None,
    visit: Optional[Visit] = None,
):
    if visit is not None and getattr(visit, "tenant_id", None) is not None:
        return getattr(visit, "tenant_id", None)

    if patient is not None and getattr(patient, "tenant_id", None) is not None:
        return getattr(patient, "tenant_id", None)

    return None


# =========================================================
# TASK LOOKUP HELPERS
# =========================================================

def get_active_poc_task(
    db: Session,
    patient_id,
    *,
    tenant_id=None,
) -> Optional[Task]:
    """
    Return the earliest active POC_UPDATE task for a patient.
    """
    active_statuses = _active_poc_statuses()

    query = (
        db.query(Task)
        .execution_options(skip_tenant_filter=True)
        .filter(
            Task.patient_id == patient_id,
            Task.task_type == TaskType.POC_UPDATE,
            Task.status.in_(active_statuses),
        )
    )
    query = _apply_tenant_scope(query, tenant_id=tenant_id)

    return query.order_by(Task.due_date.asc(), Task.created_at.asc()).first()


def get_periodic_poc_task_for_due_date(
    *,
    db: Session,
    patient_id,
    due_date: date,
    tenant_id=None,
) -> Optional[Task]:
    """
    Return an existing PERIODIC POC_UPDATE task for the exact patient + due_date cycle.

    This prevents duplicate routine periodic POC obligations for the same cycle.
    """
    periodic_origin = _default_periodic_origin()

    query = (
        db.query(Task)
        .execution_options(skip_tenant_filter=True)
        .filter(
            Task.patient_id == patient_id,
            Task.task_type == TaskType.POC_UPDATE,
            Task.origin == periodic_origin,
            Task.due_date == due_date,
        )
    )
    query = _apply_tenant_scope(query, tenant_id=tenant_id)

    return query.order_by(Task.created_at.asc()).first()


def get_poc_task_for_visit_evidence(
    *,
    db: Session,
    patient_id,
    visit_id,
    tenant_id=None,
) -> Optional[Task]:
    """
    Return a POC_UPDATE task already linked to a visit as completion evidence.

    This protects idempotency when a finalize operation is retried.
    """
    reference_type = _visit_reference_type()

    query = (
        db.query(Task)
        .execution_options(skip_tenant_filter=True)
        .filter(
            Task.patient_id == patient_id,
            Task.task_type == TaskType.POC_UPDATE,
            Task.completion_reference_id == visit_id,
        )
    )

    if hasattr(Task, "completion_reference_type"):
        query = query.filter(Task.completion_reference_type == reference_type)

    query = _apply_tenant_scope(query, tenant_id=tenant_id)

    return query.order_by(Task.created_at.asc()).first()


def get_manual_poc_task_for_due_date(
    *,
    db: Session,
    patient_id,
    due_date: date,
    tenant_id=None,
) -> Optional[Task]:
    """
    Return an existing same-day manual/system POC_UPDATE task for a patient.

    Used for crisis same-day behavior so repeat finalize calls do not create duplicates.
    """
    manual_origin = _default_manual_origin()

    query = (
        db.query(Task)
        .execution_options(skip_tenant_filter=True)
        .filter(
            Task.patient_id == patient_id,
            Task.task_type == TaskType.POC_UPDATE,
            Task.origin == manual_origin,
            Task.due_date == due_date,
        )
    )
    query = _apply_tenant_scope(query, tenant_id=tenant_id)

    return query.order_by(Task.created_at.asc()).first()


# =========================================================
# TASK MUTATION HELPERS
# =========================================================

def create_poc_task(
    *,
    db: Session,
    patient: Patient,
    due_date: date,
    origin: TaskOrigin,
    benefit_period_id=None,
    visit: Optional[Visit] = None,
) -> Task:
    """
    Create a POC_UPDATE task.

    Safety rule:
    - Direct PERIODIC task creation with visit context requires a supervisory RN visit.
    - This is a final service-level guard against routine POC drift.
    - Crisis same-day tasks use MANUAL/SYSTEM origin and are handled separately.
    """
    if _is_periodic_origin(origin) and visit is not None:
        if not _is_supervisory_visit(visit):
            raise ValueError(
                "Cannot create PERIODIC POC_UPDATE from a non-supervisory visit"
            )

    now = utcnow()

    discipline_value = None
    if visit is not None:
        discipline_value = getattr(visit, "visit_discipline", None)

    task = Task(
        task_type=TaskType.POC_UPDATE,
        status=_default_new_task_status(),
        due_date=due_date,
        origin=origin,
        discipline=_resolve_task_discipline(discipline_value or "RN"),
        regulatory_basis=_regulatory_basis_poc_update(),
        alert_reason="POC_UPDATE",
        created_at=now,
        updated_at=now,
    )

    if hasattr(task, "id") and getattr(task, "id", None) is None:
        task.id = uuid4()

    if hasattr(task, "due_at"):
        task.due_at = _date_to_utc_datetime(due_date)

    if hasattr(task, "patient_id"):
        task.patient_id = patient.id

    if hasattr(task, "tenant_id"):
        task.tenant_id = getattr(patient, "tenant_id", None)

    if hasattr(task, "benefit_period_id"):
        task.benefit_period_id = benefit_period_id

    if hasattr(task, "visit_id") and visit is not None:
        task.visit_id = getattr(visit, "id", None)

    if hasattr(task, "reference_type") and visit is not None:
        task.reference_type = "VISIT"

    if hasattr(task, "reference_id") and visit is not None:
        task.reference_id = getattr(visit, "id", None)

    if hasattr(task, "created_by"):
        if visit is not None:
            task.created_by = (
                getattr(visit, "finalized_by", None)
                or getattr(visit, "provider_id", None)
                or getattr(patient, "created_by", None)
            )
        else:
            task.created_by = getattr(patient, "created_by", None)

    if hasattr(task, "updated_by"):
        task.updated_by = (
            (
                getattr(visit, "finalized_by", None)
                or getattr(visit, "provider_id", None)
            )
            if visit is not None
            else None
        )

    db.add(task)
    db.flush()

    logger.info(
        "Created POC_UPDATE task task_id=%s patient_id=%s due_date=%s origin=%s",
        str(getattr(task, "id", None)),
        str(getattr(patient, "id", None)),
        str(due_date),
        str(getattr(origin, "value", origin)),
    )

    return task


def complete_task_with_visit_evidence(
    *,
    task: Task,
    visit: Visit,
) -> None:
    """
    Complete a POC_UPDATE task with VISIT evidence.

    Compliance rule:
    - completed status
    - completed_at timestamp
    - completion_reference_type
    - completion_reference_id
    """
    now = utcnow()

    task.status = _completed_status()
    task.completed_at = now
    task.completion_reference_type = _visit_reference_type()
    task.completion_reference_id = visit.id

    if hasattr(task, "visit_id"):
        task.visit_id = getattr(visit, "id", None)

    if hasattr(task, "updated_at"):
        task.updated_at = now

    if hasattr(task, "updated_by"):
        task.updated_by = (
            getattr(visit, "finalized_by", None)
            or getattr(visit, "provider_id", None)
        )


def attach_visit_as_same_cycle_context(
    *,
    task: Task,
    visit: Visit,
    benefit_period_id=None,
) -> Task:
    """
    Refresh an existing same-cycle POC task with supporting visit context.

    This does not create a duplicate task.

    IMPORTANT:
    - For active tasks, attach visit context only
    - Do NOT write completion evidence unless the task is actually completed
    """
    now = utcnow()

    if hasattr(task, "updated_at"):
        task.updated_at = now

    if hasattr(task, "updated_by"):
        task.updated_by = (
            getattr(visit, "finalized_by", None)
            or getattr(visit, "provider_id", None)
        )

    if benefit_period_id is not None and hasattr(task, "benefit_period_id"):
        if getattr(task, "benefit_period_id", None) is None:
            task.benefit_period_id = benefit_period_id

    if hasattr(task, "visit_id"):
        task.visit_id = getattr(visit, "id", None)

    if hasattr(task, "reference_type"):
        task.reference_type = "VISIT"

    if hasattr(task, "reference_id"):
        task.reference_id = getattr(visit, "id", None)

    return task


# =========================================================
# PERIODIC ROUTINE POC FLOW
# =========================================================

def upsert_next_periodic_poc_task(
    *,
    db: Session,
    patient: Patient,
    anchor_visit: Visit,
    benefit_period_id=None,
) -> Optional[Task]:
    """
    Create or update the next routine PERIODIC POC_UPDATE task.

    Locked Phase 1 policy:
    - PERIODIC POC_UPDATE anchoring requires a supervisory RN visit.
    - Non-supervisory RN visits must not create, move, or reuse a PERIODIC
      POC_UPDATE cycle as the anchor visit.
    - One PERIODIC POC task is allowed per patient per due_date cycle.

    Returns:
        Task when a periodic task is created/reused/updated.
        None when the visit is not allowed to anchor periodic behavior.
    """
    if not _is_supervisory_visit(anchor_visit):
        return None

    tenant_id = _resolve_tenant_id(patient=patient, visit=anchor_visit)
    anchor_date = _resolve_visit_service_date(anchor_visit)
    next_due_date = anchor_date + timedelta(days=14)

    # ---------------------------------------------------------
    # 1) Exact same periodic cycle already exists: reuse it.
    # ---------------------------------------------------------
    existing_same_due = get_periodic_poc_task_for_due_date(
        db=db,
        patient_id=patient.id,
        due_date=next_due_date,
        tenant_id=tenant_id,
    )
    if existing_same_due:
        return attach_visit_as_same_cycle_context(
            task=existing_same_due,
            visit=anchor_visit,
            benefit_period_id=benefit_period_id,
        )

    # ---------------------------------------------------------
    # 2) Existing active POC task exists: move/update it.
    # ---------------------------------------------------------
    existing_active = get_active_poc_task(
        db,
        patient.id,
        tenant_id=tenant_id,
    )
    if existing_active:
        existing_active.due_date = next_due_date

        if hasattr(existing_active, "due_at"):
            existing_active.due_at = _date_to_utc_datetime(next_due_date)

        if hasattr(existing_active, "origin"):
            existing_active.origin = _default_periodic_origin()

        if hasattr(existing_active, "updated_at"):
            existing_active.updated_at = utcnow()

        if hasattr(existing_active, "updated_by"):
            existing_active.updated_by = (
                getattr(anchor_visit, "finalized_by", None)
                or getattr(anchor_visit, "provider_id", None)
            )

        if hasattr(existing_active, "visit_id"):
            existing_active.visit_id = getattr(anchor_visit, "id", None)

        if hasattr(existing_active, "reference_type"):
            existing_active.reference_type = "VISIT"

        if hasattr(existing_active, "reference_id"):
            existing_active.reference_id = getattr(anchor_visit, "id", None)

        if benefit_period_id is not None and hasattr(existing_active, "benefit_period_id"):
            existing_active.benefit_period_id = benefit_period_id

        logger.info(
            "Updated existing POC_UPDATE task task_id=%s patient_id=%s new_due_date=%s origin=%s",
            str(getattr(existing_active, "id", None)),
            str(getattr(patient, "id", None)),
            str(next_due_date),
            str(getattr(existing_active.origin, "value", existing_active.origin)),
        )

        return existing_active

    # ---------------------------------------------------------
    # 3) Truly new routine periodic cycle: create it.
    # ---------------------------------------------------------
    return create_poc_task(
        db=db,
        patient=patient,
        due_date=next_due_date,
        origin=_default_periodic_origin(),
        benefit_period_id=benefit_period_id,
        visit=anchor_visit,
    )


# =========================================================
# CRISIS SAME-DAY POC FLOW
# =========================================================

def create_and_complete_same_day_crisis_poc(
    *,
    db: Session,
    patient: Patient,
    visit: Visit,
    benefit_period_id=None,
) -> Task:
    """
    Create or reuse a same-day crisis POC_UPDATE task and complete it with visit evidence.

    Crisis behavior:
    - Same-day POC_UPDATE review
    - Completed with VISIT evidence
    - Uses MANUAL/SYSTEM origin, not PERIODIC
    """
    tenant_id = _resolve_tenant_id(patient=patient, visit=visit)
    today_due = _resolve_visit_service_date(visit)

    existing_for_visit = get_poc_task_for_visit_evidence(
        db=db,
        patient_id=patient.id,
        visit_id=visit.id,
        tenant_id=tenant_id,
    )
    if existing_for_visit:
        return existing_for_visit

    existing_same_day_manual = get_manual_poc_task_for_due_date(
        db=db,
        patient_id=patient.id,
        due_date=today_due,
        tenant_id=tenant_id,
    )
    if existing_same_day_manual:
        if benefit_period_id is not None and hasattr(existing_same_day_manual, "benefit_period_id"):
            if getattr(existing_same_day_manual, "benefit_period_id", None) is None:
                existing_same_day_manual.benefit_period_id = benefit_period_id

        current_status = getattr(existing_same_day_manual, "status", None)
        if current_status in _active_poc_statuses():
            complete_task_with_visit_evidence(
                task=existing_same_day_manual,
                visit=visit,
            )
            db.flush()

        return existing_same_day_manual

    task = create_poc_task(
        db=db,
        patient=patient,
        due_date=today_due,
        origin=_default_manual_origin(),
        benefit_period_id=benefit_period_id,
        visit=visit,
    )

    complete_task_with_visit_evidence(task=task, visit=visit)
    db.flush()

    logger.info(
        "Completed same-day crisis POC_UPDATE task task_id=%s patient_id=%s visit_id=%s",
        str(getattr(task, "id", None)),
        str(getattr(patient, "id", None)),
        str(getattr(visit, "id", None)),
    )

    return task


# =========================================================
# PUBLIC ENTRY POINT
# =========================================================

def handle_poc_on_finalized_rn_visit(
    *,
    db: Session,
    patient: Patient,
    visit: Visit,
    benefit_period_id=None,
) -> Optional[Task]:
    """
    Apply POC_UPDATE behavior when a finalized RN visit is processed.

    Locked Phase 1 behavior:

    CRISIS:
      - RN visit may create/complete same-day POC_UPDATE review
      - Uses MANUAL/SYSTEM origin
      - Separate from routine PERIODIC anchoring

    ROUTINE:
      - Only a supervisory RN visit may anchor the next PERIODIC POC_UPDATE
      - Non-supervisory RN visits do not create, move, or reuse a PERIODIC anchor

    Clinical semantic boundary:
      - POC_UPDATE task behavior is an operational/compliance checkpoint
      - It is not the full clinical POC lifecycle
      - Condition-specific reassessment cadence belongs to condition logic, not this
        routine periodic anchoring function
    """
    if not _is_rn_visit(visit):
        return None

    decision = determine_care_model(
        has_chha=bool(getattr(patient, "has_chha", False)),
        has_lvn=bool(getattr(patient, "has_lvn", False)),
        has_wounds=bool(getattr(patient, "has_wounds", False)),
        acuity_state=getattr(patient, "acuity_state", None),
    )

    trigger_policy_value = getattr(
        getattr(decision, "poc_trigger_policy", None),
        "value",
        getattr(decision, "poc_trigger_policy", None),
    )

    if trigger_policy_value == "SAME_DAY_ANY_RN_CRISIS":
        return create_and_complete_same_day_crisis_poc(
            db=db,
            patient=patient,
            visit=visit,
            benefit_period_id=benefit_period_id,
        )

    should_anchor = should_anchor_poc_from_rn_visit(
        is_supervisory_visit=_is_supervisory_visit(visit),
        decision=decision,
    )

    if not should_anchor:
        return None

    return upsert_next_periodic_poc_task(
        db=db,
        patient=patient,
        anchor_visit=visit,
        benefit_period_id=benefit_period_id,
    )
