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
    return datetime.now(timezone.utc)


def _date_to_utc_datetime(value: date) -> datetime:
    return datetime.combine(value, time.min, tzinfo=timezone.utc)


# =========================================================
# ENUM HELPERS
# =========================================================

def _task_type_poc_update() -> TaskType | str:
    member = getattr(TaskType, "POC_UPDATE", None)
    return member if member is not None else "POC_UPDATE"


def _active_poc_statuses() -> list:
    statuses: list = []
    for name in ("PENDING", "OPEN", "DUE", "IN_PROGRESS", "OVERDUE"):
        member = getattr(TaskStatus, name, None)
        if member is not None and member not in statuses:
            statuses.append(member)

    if not statuses:
        raise ValueError("TaskStatus enum has no usable active statuses")

    return statuses


def _default_new_task_status():
    for name in ("PENDING", "OPEN", "DUE"):
        member = getattr(TaskStatus, name, None)
        if member is not None:
            return member

    raise ValueError("TaskStatus enum has no usable default active status")


def _completed_status():
    completed = getattr(TaskStatus, "COMPLETED", None)
    if completed is None:
        raise ValueError("TaskStatus enum has no COMPLETED member")
    return completed


def _default_manual_origin():
    for name in ("MANUAL", "SYSTEM"):
        member = getattr(TaskOrigin, name, None)
        if member is not None:
            return member
    raise ValueError("TaskOrigin enum has no usable MANUAL or SYSTEM member")


def _default_periodic_origin():
    for name in ("PERIODIC", "SYSTEM"):
        member = getattr(TaskOrigin, name, None)
        if member is not None:
            return member
    raise ValueError("TaskOrigin enum has no usable PERIODIC or SYSTEM member")


def _is_periodic_origin(origin) -> bool:
    return origin == _default_periodic_origin()


def _visit_reference_type() -> CompletionReferenceType | str:
    member = getattr(CompletionReferenceType, "VISIT", None)
    return member if member is not None else "VISIT"


def _regulatory_basis_poc_update() -> TaskRegulatoryBasis | str:
    member = getattr(TaskRegulatoryBasis, "POC_UPDATE", None)
    return member if member is not None else "POC_UPDATE"


def _resolve_task_discipline(value: Optional[str]) -> TaskDiscipline | str:
    normalized = (value or "").strip().upper()

    for member in TaskDiscipline:
        if str(getattr(member, "value", member)).upper() == normalized:
            return member

    fallback = getattr(TaskDiscipline, "RN", None)
    return fallback if fallback is not None else "RN"


# =========================================================
# VISIT HELPERS
# =========================================================

def normalize_visit_type(value: Optional[str]) -> str:
    if value is None:
        return ""
    try:
        return normalize_domain_visit_type(value)
    except ValueError:
        return ""


def _get_visit_type(visit: Visit) -> str:
    discipline = getattr(visit, "visit_discipline", None)
    if discipline:
        return normalize_visit_type(str(discipline))

    visit_type = getattr(visit, "visit_type", None)
    return normalize_visit_type(str(visit_type) if visit_type else None)


def _is_rn_visit(visit: Visit) -> bool:
    return _get_visit_type(visit) == "RN"


def _is_supervisory_visit(visit: Visit) -> bool:
    return bool(
        getattr(visit, "is_supervisory", False)
        or getattr(visit, "supervisory", False)
    )


def _resolve_visit_service_date(visit: Visit) -> date:
    for value in [
        getattr(visit, "visit_date", None),
        getattr(visit, "visit_datetime", None),
        getattr(visit, "finalized_at", None),
        getattr(visit, "created_at", None),
    ]:
        if isinstance(value, datetime):
            return value.date()
        if isinstance(value, date):
            return value

    raise ValueError("Visit has no usable service date")


# =========================================================
# TENANT HELPERS
# =========================================================

def _apply_tenant_scope(query: Query, *, tenant_id) -> Query:
    if tenant_id is not None and hasattr(Task, "tenant_id"):
        query = query.filter(Task.tenant_id == tenant_id)
    return query


def _resolve_tenant_id(*, patient=None, visit=None):
    if visit and getattr(visit, "tenant_id", None):
        return visit.tenant_id
    if patient and getattr(patient, "tenant_id", None):
        return patient.tenant_id
    return None


# =========================================================
# TASK LOOKUPS
# =========================================================

def get_active_poc_task(db: Session, patient_id, *, tenant_id=None) -> Optional[Task]:
    query = (
        db.query(Task)
        .filter(
            Task.patient_id == patient_id,
            Task.task_type == _task_type_poc_update(),
            Task.status.in_(_active_poc_statuses()),
        )
    )
    query = _apply_tenant_scope(query, tenant_id=tenant_id)
    return query.order_by(Task.due_date.asc(), Task.created_at.asc()).first()


# =========================================================
# TASK MUTATION
# =========================================================

def create_poc_task(
    *,
    db: Session,
    patient: Patient,
    due_date: date,
    origin,
    benefit_period_id=None,
    visit: Optional[Visit] = None,
) -> Task:

    existing = get_active_poc_task(
        db,
        patient.id,
        tenant_id=getattr(patient, "tenant_id", None),
    )
    if existing:
        return existing

    now = utcnow()

    task = Task(
        id=uuid4(),
        patient_id=patient.id,
        tenant_id=getattr(patient, "tenant_id", None),
        task_type=_task_type_poc_update(),
        status=_default_new_task_status(),
        due_date=due_date,
        origin=origin,
        discipline=_resolve_task_discipline(
            getattr(visit, "visit_discipline", None)
        ),
        regulatory_basis=_regulatory_basis_poc_update(),
        alert_reason="POC_UPDATE",
        created_at=now,
        updated_at=now,
    )

    if hasattr(task, "due_at"):
        task.due_at = _date_to_utc_datetime(due_date)

    if visit:
        task.visit_id = visit.id
        task.reference_type = "VISIT"
        task.reference_id = visit.id

    db.add(task)
    db.flush()

    return task


def complete_task_with_visit_evidence(
    *,
    task: Task,
    visit: Visit,
) -> None:

    # ✅ HARD VALIDATION (DO NOT REMOVE)
    if not getattr(visit, "id", None):
        raise ValueError("Visit ID required for completion")

    now = utcnow()

    task.status = _completed_status()

    if hasattr(task, "completed_at"):
        task.completed_at = now

    if hasattr(task, "completion_reference_type"):
        task.completion_reference_type = _visit_reference_type()

    if hasattr(task, "completion_reference_id"):
        task.completion_reference_id = visit.id

    if hasattr(task, "visit_id"):
        task.visit_id = visit.id

    if hasattr(task, "updated_at"):
        task.updated_at = now

    if hasattr(task, "updated_by"):
        task.updated_by = (
            getattr(visit, "finalized_by", None)
            or getattr(visit, "provider_id", None)
        )

    # ✅ AUDIT TRAIL (REQUIRED FOR SURVEY)
    if hasattr(task, "audit_metadata"):
        task.audit_metadata = {
            "event": "TASK_COMPLETED",
            "visit_id": str(visit.id),
            "timestamp": now.isoformat(),
        }


# =========================================================
# MAIN ENTRY
# =========================================================

def handle_poc_on_finalized_rn_visit(
    *,
    db: Session,
    patient: Patient,
    visit: Visit,
    benefit_period_id=None,
) -> Optional[Task]:

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

    return create_poc_task(
        db=db,
        patient=patient,
        due_date=_resolve_visit_service_date(visit) + timedelta(days=14),
        origin=_default_periodic_origin(),
        benefit_period_id=benefit_period_id,
        visit=visit,
    )