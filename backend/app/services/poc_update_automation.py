from __future__ import annotations

import logging
from datetime import date, datetime, time, timedelta, timezone
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy.orm import Session

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
from app.services.benefit_period_resolver import get_active_benefit_period
from app.services.task_completion_evidence import complete_task_with_evidence

logger = logging.getLogger("sns_emr")


# =========================================================
# TIME / NORMALIZATION HELPERS
# =========================================================

def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _date_to_utc_datetime(value: date) -> datetime:
    return datetime.combine(value, time.min, tzinfo=timezone.utc)


def _task_type_poc_update() -> TaskType | str:
    member = getattr(TaskType, "POC_UPDATE", None)
    return member if member is not None else "POC_UPDATE"


def _open_status() -> TaskStatus | str:
    """
    Canonical open state for automatically managed POC_UPDATE tasks.

    Policy:
    - Open POC_UPDATE tasks remain PENDING unless explicitly completed.
    """
    member = getattr(TaskStatus, "PENDING", None)
    return member if member is not None else "PENDING"


def _completed_status() -> TaskStatus | str:
    member = getattr(TaskStatus, "COMPLETED", None)
    return member if member is not None else "COMPLETED"


def _origin_manual() -> TaskOrigin | str:
    for name in ("MANUAL", "SYSTEM"):
        member = getattr(TaskOrigin, name, None)
        if member is not None:
            return member
    return "MANUAL"


def _origin_periodic() -> TaskOrigin | str:
    for name in ("PERIODIC", "SYSTEM"):
        member = getattr(TaskOrigin, name, None)
        if member is not None:
            return member
    return "PERIODIC"


def _regulatory_basis_poc_update() -> TaskRegulatoryBasis | str:
    member = getattr(TaskRegulatoryBasis, "POC_UPDATE", None)
    return member if member is not None else "POC_UPDATE"


def _reference_type_visit() -> CompletionReferenceType | str:
    member = getattr(CompletionReferenceType, "VISIT", None)
    return member if member is not None else "VISIT"


def _discipline_rn() -> TaskDiscipline | str:
    member = getattr(TaskDiscipline, "RN", None)
    return member if member is not None else "RN"


def _is_rn_visit(visit) -> bool:
    """
    Normalize RN visit detection across visit models.

    Preferred source:
    - visit.visit_discipline

    Fallback source:
    - visit.visit_type
    """
    discipline = (getattr(visit, "visit_discipline", None) or "").upper()
    if discipline:
        return discipline == "RN"

    visit_type = (getattr(visit, "visit_type", None) or "").upper()
    if visit_type:
        return visit_type == "RN"

    # final fallback through domain normalizer if raw value exists
    raw_value = getattr(visit, "visit_type", None) or getattr(visit, "visit_discipline", None)
    if raw_value:
        try:
            return normalize_domain_visit_type(str(raw_value)) == "RN"
        except Exception:
            return False

    return False


def _is_supervisory_visit(visit) -> bool:
    """
    Determine whether a visit is supervisory.

    Supports:
    - is_supervisory (preferred)
    - supervisory (legacy)
    - form_type fallback
    """
    if hasattr(visit, "is_supervisory"):
        return bool(visit.is_supervisory)

    if hasattr(visit, "supervisory"):
        return bool(visit.supervisory)

    form_type = getattr(visit, "form_type", None)
    if form_type:
        return str(form_type).upper() in {
            "SUPV",
            "SUPERVISORY",
            "SUPV VISIT",
            "SUPV VISIT ONLY",
            "RN SUPERVISORY",
        }

    logger.debug(
        "No supervisory discriminator found on visit_id=%s",
        str(getattr(visit, "id", None)),
    )
    return False


def _visit_time_utc(visit) -> datetime:
    """
    Resolve the canonical visit timestamp in UTC.

    Preferred order:
    1. visit.visit_datetime
    2. visit.finalized_at
    3. visit.completed_at
    4. visit.occurred_at
    5. visit.performed_at
    6. current UTC time
    """
    for attr in ("visit_datetime", "finalized_at", "completed_at", "occurred_at", "performed_at"):
        value = getattr(visit, attr, None)
        if value is None:
            continue

        if getattr(value, "tzinfo", None):
            return value.astimezone(timezone.utc)

        return value.replace(tzinfo=timezone.utc)

    return _utcnow()


def _acuity_at_visit(visit, patient: Patient) -> str:
    """
    STRICT policy:
    - ALWAYS use visit-level acuity when present
    - NEVER allow patient-level acuity to override visit-level decisions
    """
    visit_acuity = getattr(visit, "acuity_state_at_visit", None)
    if visit_acuity is not None:
        return str(visit_acuity).strip().upper()

    patient_acuity = getattr(patient, "acuity_state", None)
    if patient_acuity is not None:
        return str(patient_acuity).strip().upper()

    return "ROUTINE"


# =========================================================
# BENEFIT PERIOD RESOLUTION
# =========================================================

def _resolve_benefit_period_id(
    db: Session,
    *,
    tenant_id: UUID | None,
    patient_id: UUID,
    as_of_day: date,
) -> UUID | None:
    benefit_period = get_active_benefit_period(
        db,
        tenant_id=tenant_id,
        patient_id=patient_id,
        as_of_date=as_of_day,
    )
    return benefit_period.id if benefit_period else None


# =========================================================
# TASK SEARCH / CREATE
# =========================================================

def _find_open_poc_task(
    db: Session,
    *,
    tenant_id: UUID | None,
    patient_id: UUID,
) -> Task | None:
    """
    Find the most recent open POC_UPDATE task for the patient.

    Open means:
    - status == PENDING (policy choice for this automation layer)
    """
    query = (
        db.query(Task)
        .filter(Task.patient_id == patient_id)
        .filter(Task.task_type == _task_type_poc_update())
        .filter(Task.status == _open_status())
    )

    if tenant_id is not None and hasattr(Task, "tenant_id"):
        query = query.filter(Task.tenant_id == tenant_id)

    return query.order_by(Task.created_at.desc()).first()


def _find_completed_poc_for_visit(
    db: Session,
    *,
    tenant_id: UUID | None,
    patient_id: UUID,
    visit_id: UUID,
) -> Task | None:
    """
    Find a POC_UPDATE task already linked to this visit as completion evidence.

    Protects same-visit idempotency, especially for crisis behavior.
    """
    query = (
        db.query(Task)
        .filter(Task.patient_id == patient_id)
        .filter(Task.task_type == _task_type_poc_update())
    )

    if tenant_id is not None and hasattr(Task, "tenant_id"):
        query = query.filter(Task.tenant_id == tenant_id)

    if hasattr(Task, "completion_reference_type"):
        query = query.filter(Task.completion_reference_type == _reference_type_visit())
    else:
        return None

    if hasattr(Task, "completion_reference_id"):
        query = query.filter(Task.completion_reference_id == visit_id)
    else:
        return None

    return query.order_by(Task.created_at.desc()).first()


def _create_poc_task(
    db: Session,
    *,
    tenant_id: UUID | None,
    patient_id: UUID,
    due_at: datetime,
    origin: TaskOrigin | str,
    created_by: UUID | None,
    benefit_period_id: UUID | None,
) -> Task:
    """
    Create a POC_UPDATE task in PENDING status.

    This function intentionally does not contain visit policy logic.
    """
    now = _utcnow()

    task = Task(
        id=uuid4(),
        task_type=_task_type_poc_update(),
        origin=origin,
        discipline=_discipline_rn(),
        regulatory_basis=_regulatory_basis_poc_update(),
        status=_open_status(),
        due_date=due_at.date(),
        created_at=now,
        updated_at=now,
    )

    if hasattr(task, "tenant_id"):
        task.tenant_id = tenant_id

    if hasattr(task, "patient_id"):
        task.patient_id = patient_id

    if hasattr(task, "due_at"):
        task.due_at = due_at

    if hasattr(task, "due_date"):
        task.due_date = due_at.date()

    if hasattr(task, "created_by"):
        task.created_by = created_by

    if hasattr(task, "benefit_period_id"):
        task.benefit_period_id = benefit_period_id

    if hasattr(task, "alert_reason"):
        task.alert_reason = "POC_UPDATE"

    if hasattr(task, "sla_start_at"):
        task.sla_start_at = now

    if hasattr(task, "sla_due_at"):
        task.sla_due_at = due_at

    if hasattr(task, "is_overdue"):
        task.is_overdue = False

    db.add(task)
    db.flush()

    logger.info(
        "Created POC_UPDATE task task_id=%s patient_id=%s due_date=%s origin=%s",
        str(getattr(task, "id", None)),
        str(patient_id),
        str(due_at.date()),
        str(getattr(origin, "value", origin)),
    )

    return task


def _schedule_next_periodic_poc_from_supervisory_visit(
    db: Session,
    *,
    visit,
    patient: Patient,
    visit_time: datetime,
    finalized_by_user_id: UUID | None,
    benefit_period_id: UUID | None,
) -> Task | None:
    """
    Create NEXT ROUTINE POC task.

    RULE:
    - ONLY reuse PENDING tasks
    - NEVER reuse COMPLETED tasks
    """
    if not _is_supervisory_visit(visit):
        return None

    tenant_id = getattr(patient, "tenant_id", None)
    patient_id = patient.id

    existing_task = _find_open_poc_task(
        db,
        tenant_id=tenant_id,
        patient_id=patient_id,
    )

    if existing_task:
        if getattr(existing_task, "status", None) == _open_status():
            return existing_task

    due_at = visit_time + timedelta(days=14)

    task = _create_poc_task(
        db,
        tenant_id=tenant_id,
        patient_id=patient_id,
        due_at=due_at,
        origin=_origin_periodic(),
        created_by=finalized_by_user_id,
        benefit_period_id=benefit_period_id,
    )

    db.flush()
    return task


# =========================================================
# PUBLIC ENTRY POINT
# =========================================================

def on_visit_finalized_apply_poc_policy(
    db: Session,
    *,
    visit,
    patient: Patient,
    finalized_by_user_id: UUID | None,
) -> None:
    """
    Apply SNS EMR POC_UPDATE automation when an RN visit is finalized.

    CRISIS:
        - Every finalized RN crisis visit creates a same-day POC_UPDATE
        - The task is completed immediately with VISIT evidence
        - Origin = MANUAL/SYSTEM fallback

    ROUTINE:
        - Only supervisory RN visits can anchor periodic POC_UPDATE
        - Create a PENDING POC_UPDATE with due_date = visit_date + 14 days
        - Origin = PERIODIC/SYSTEM fallback
        - MUST NOT auto-complete

    NOTE:
        This automation is an operational/compliance checkpoint layer.
        It does not replace the official documented POC review/version workflow.
    """
    if patient is None or visit is None:
        return

    if not getattr(patient, "id", None):
        return

    if not _is_rn_visit(visit):
        return

    tenant_id = getattr(patient, "tenant_id", None)
    patient_id = patient.id
    visit_id = getattr(visit, "id", None)

    if visit_id is None:
        return

    visit_time = _visit_time_utc(visit)
    visit_day = visit_time.date()

    acuity = _acuity_at_visit(visit, patient)

    logger.info(
        "POC policy triggered visit_id=%s patient_id=%s rn=%s supervisory=%s acuity=%s",
        str(visit_id),
        str(patient_id),
        _is_rn_visit(visit),
        _is_supervisory_visit(visit),
        acuity,
    )

    benefit_period_id = _resolve_benefit_period_id(
        db,
        tenant_id=tenant_id,
        patient_id=patient_id,
        as_of_day=visit_day,
    )

    # =========================================================
    # CRISIS LOGIC
    # =========================================================
    if acuity == "CRISIS":
        existing_completed = _find_completed_poc_for_visit(
            db,
            tenant_id=tenant_id,
            patient_id=patient_id,
            visit_id=visit_id,
        )
        if existing_completed:
            return

        existing_open_task = _find_open_poc_task(
            db,
            tenant_id=tenant_id,
            patient_id=patient_id,
        )

        if existing_open_task:
            if hasattr(existing_open_task, "due_at"):
                existing_open_task.due_at = visit_time
            if hasattr(existing_open_task, "due_date"):
                existing_open_task.due_date = visit_day

            if (
                benefit_period_id is not None
                and hasattr(existing_open_task, "benefit_period_id")
                and getattr(existing_open_task, "benefit_period_id", None) is None
            ):
                existing_open_task.benefit_period_id = benefit_period_id

            complete_task_with_evidence(
                db,
                task_id=existing_open_task.id,
                completion_reference_type=_reference_type_visit(),
                completion_reference_id=visit_id,
                completed_by=finalized_by_user_id,
                completed_at=visit_time,
            )
            db.flush()
            return

        task = _create_poc_task(
            db,
            tenant_id=tenant_id,
            patient_id=patient_id,
            due_at=visit_time,
            origin=_origin_manual(),
            created_by=finalized_by_user_id,
            benefit_period_id=benefit_period_id,
        )

        complete_task_with_evidence(
            db,
            task_id=task.id,
            completion_reference_type=_reference_type_visit(),
            completion_reference_id=visit_id,
            completed_by=finalized_by_user_id,
            completed_at=visit_time,
        )

        db.flush()

        logger.info(
            "Completed same-day crisis POC_UPDATE task task_id=%s patient_id=%s visit_id=%s",
            str(getattr(task, "id", None)),
            str(patient_id),
            str(visit_id),
        )
        return

    # =========================================================
    # ROUTINE GUARD
    # =========================================================
    if acuity != "ROUTINE":
        return

    _schedule_next_periodic_poc_from_supervisory_visit(
        db,
        visit=visit,
        patient=patient,
        visit_time=visit_time,
        finalized_by_user_id=finalized_by_user_id,
        benefit_period_id=benefit_period_id,
    )

    db.flush()