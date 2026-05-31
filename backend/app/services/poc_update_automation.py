from __future__ import annotations

from datetime import datetime, timezone, timedelta
from uuid import UUID, uuid4

from sqlalchemy.orm import Session

from app.models.task import Task
from app.models.patient import Patient
from app.models.enums import (
    TaskType,
    TaskStatus,
    TaskOrigin,
    TaskDiscipline,
    TaskRegulatoryBasis,
    CompletionReferenceType,
)

from app.services.benefit_period_resolver import get_active_benefit_period


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _open_status() -> TaskStatus:
    return TaskStatus.PENDING


def _completed_status() -> TaskStatus:
    return TaskStatus.COMPLETED


def _is_rn_visit(visit) -> bool:
    """
    Normalize RN detection across visit models:
    - prefer visit_discipline if present
    - otherwise visit_type
    """
    d = (getattr(visit, "visit_discipline", None) or "").upper()
    if d:
        return d == "RN"
    t = (getattr(visit, "visit_type", None) or "").upper()
    return t == "RN"


def _visit_time_utc(visit) -> datetime:
    """
    Canonical timestamp: visit.visit_datetime (finalized visit time).
    Defensive fallback to finalized_at, then now.
    """
    for attr in ("visit_datetime", "finalized_at", "completed_at", "occurred_at", "performed_at"):
        v = getattr(visit, attr, None)
        if v is not None:
            return v.astimezone(timezone.utc) if getattr(v, "tzinfo", None) else v.replace(tzinfo=timezone.utc)
    return _utcnow()


def _acuity_at_visit(visit, patient: Patient) -> str:
    """
    Authoritative: visit.acuity_state_at_visit
    Fallback: patient.acuity_state
    Default: ROUTINE
    """
    v = getattr(visit, "acuity_state_at_visit", None)
    if v:
        return str(v).upper()
    p = getattr(patient, "acuity_state", None)
    if p:
        return str(p).upper()
    return "ROUTINE"


def _resolve_benefit_period_id(db: Session, *, tenant_id: UUID, patient_id: UUID, as_of_day) -> UUID | None:
    bp = get_active_benefit_period(
        db,
        tenant_id=tenant_id,
        patient_id=patient_id,
        as_of_date=as_of_day,
    )
    return bp.id if bp else None


def _find_open_poc_task(db: Session, *, tenant_id: UUID, patient_id: UUID) -> Task | None:
    return (
        db.query(Task)
        .filter(
            Task.tenant_id == tenant_id,
            Task.patient_id == patient_id,
            Task.task_type == TaskType.POC_UPDATE,
            Task.status == _open_status(),
        )
        .order_by(Task.created_at.desc())
        .first()
    )


def _create_poc_task(
    db: Session,
    *,
    tenant_id: UUID,
    patient_id: UUID,
    due_at: datetime,
    origin: TaskOrigin,
    created_by: UUID | None,
    benefit_period_id: UUID | None,
) -> Task:
    task = Task(
        id=uuid4(),
        tenant_id=tenant_id,
        patient_id=patient_id,
        task_type=TaskType.POC_UPDATE,

        origin=origin,
        discipline=TaskDiscipline.RN,
        regulatory_basis=TaskRegulatoryBasis.POC_UPDATE,

        status=_open_status(),
        due_at=due_at,
        due_date=due_at.date(),
        created_by=created_by,

        benefit_period_id=benefit_period_id,
    )
    db.add(task)
    db.flush()
    return task


def _complete_task_with_visit_evidence(task: Task, *, visit_id: UUID) -> None:
    task.status = _completed_status()
    task.completed_at = _utcnow()
    task.completion_reference_type = CompletionReferenceType.VISIT
    task.completion_reference_id = visit_id


def on_visit_finalized_apply_poc_policy(
    db: Session,
    *,
    visit,
    patient: Patient,
    finalized_by_user_id: UUID | None,
) -> None:
    """
    SNS EMR POC_UPDATE policy (canonical):

    ROUTINE:
      - Only supervisory RN visits apply
      - Create ONE open POC_UPDATE due = visit_date + 14 days (origin PERIODIC)

    CRISIS:
      - Every RN visit applies
      - Ensure POC_UPDATE due same day and COMPLETE with VISIT evidence (origin MANUAL)
    """
    tenant_id = patient.tenant_id
    patient_id = patient.id

    if not _is_rn_visit(visit):
        return

    visit_time = _visit_time_utc(visit)
    visit_day = visit_time.date()
    acuity = _acuity_at_visit(visit, patient)

    benefit_period_id = _resolve_benefit_period_id(
        db,
        tenant_id=tenant_id,
        patient_id=patient_id,
        as_of_day=visit_day,
    )

    # -----------------------------
    # CRISIS: every RN visit
    # -----------------------------
    if acuity == "CRISIS":
        existing = _find_open_poc_task(db, tenant_id=tenant_id, patient_id=patient_id)
        if existing:
            # attach BP id if missing
            if getattr(existing, "benefit_period_id", None) is None and benefit_period_id is not None:
                existing.benefit_period_id = benefit_period_id
            _complete_task_with_visit_evidence(existing, visit_id=visit.id)
            db.flush()
            return

        task = _create_poc_task(
            db,
            tenant_id=tenant_id,
            patient_id=patient_id,
            due_at=visit_time,
            origin=TaskOrigin.MANUAL,
            created_by=finalized_by_user_id,
            benefit_period_id=benefit_period_id,
        )
        _complete_task_with_visit_evidence(task, visit_id=visit.id)
        db.flush()
        return

    # -----------------------------
    # ROUTINE: supervisory RN only
    # -----------------------------
    if acuity != "ROUTINE":
        return

    if not bool(getattr(visit, "is_supervisory", False) or getattr(visit, "supervisory", False)):
        return

    # do not duplicate open POC_UPDATE tasks
    if _find_open_poc_task(db, tenant_id=tenant_id, patient_id=patient_id):
        return

    due_at = visit_time + timedelta(days=14)
    _create_poc_task(
        db,
        tenant_id=tenant_id,
        patient_id=patient_id,
        due_at=due_at,
        origin=TaskOrigin.PERIODIC,
        created_by=finalized_by_user_id,
        benefit_period_id=benefit_period_id,
    )
    db.flush()