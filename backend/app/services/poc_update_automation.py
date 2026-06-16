from __future__ import annotations

from datetime import datetime, timezone, timedelta
from uuid import UUID, uuid4

from sqlalchemy.orm import Session

from app.models.patient import Patient
from app.models.task import Task
from app.models.enums import (
    TaskType,
    TaskStatus,
    TaskOrigin,
    TaskDiscipline,
    TaskRegulatoryBasis,
    CompletionReferenceType,
)
from app.services.benefit_period_resolver import get_active_benefit_period
from app.services.task_completion_evidence import complete_task_with_evidence


# =========================================================
# TIME / NORMALIZATION HELPERS
# =========================================================

def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _open_status() -> TaskStatus:
    # Policy: open POC_UPDATE tasks must be PENDING unless explicitly completed
    return TaskStatus.PENDING


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
    Canonical timestamp:
    prefer visit.visit_datetime, then finalized_at, then completed_at, else now.
    """
    for attr in ("visit_datetime", "finalized_at", "completed_at", "occurred_at", "performed_at"):
        v = getattr(visit, attr, None)
        if v is not None:
            if getattr(v, "tzinfo", None):
                return v.astimezone(timezone.utc)
            return v.replace(tzinfo=timezone.utc)
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


def _has_support_staff(patient: Patient) -> bool:
    """
    Supervisory visits only matter when patient has delegated support staff.
    """
    return bool(
        getattr(patient, "has_chha", False) or
        getattr(patient, "has_lvn", False)
    )


def _has_wounds(patient: Patient) -> bool:
    """
    Wound patients require tighter POC cadence regardless of supervisory status.
    """
    return bool(getattr(patient, "has_wounds", False))


# =========================================================
# BENEFIT PERIOD RESOLUTION
# =========================================================

def _resolve_benefit_period_id(
    db: Session,
    *,
    tenant_id: UUID,
    patient_id: UUID,
    as_of_day,
) -> UUID | None:
    bp = get_active_benefit_period(
        db,
        tenant_id=tenant_id,
        patient_id=patient_id,
        as_of_date=as_of_day,
    )
    return bp.id if bp else None


# =========================================================
# TASK SEARCH / CREATE
# =========================================================

def _find_open_poc_task(db: Session, *, tenant_id: UUID, patient_id: UUID) -> Task | None:
    """
    Finds the most recent open POC_UPDATE task for the patient.
    """
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


def _find_completed_poc_for_visit(
    db: Session,
    *,
    tenant_id: UUID,
    patient_id: UUID,
    visit_id: UUID,
) -> Task | None:
    """
    Crisis idempotency:
    If a POC_UPDATE task has already been completed with VISIT evidence pointing to this visit,
    do nothing.
    """
    return (
        db.query(Task)
        .filter(
            Task.tenant_id == tenant_id,
            Task.patient_id == patient_id,
            Task.task_type == TaskType.POC_UPDATE,
            Task.completion_reference_type == CompletionReferenceType.VISIT,
            Task.completion_reference_id == visit_id,
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
    """
    Creates a POC_UPDATE task in PENDING status.
    """
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


# =========================================================
# PUBLIC ENTRY POINT (CALLED BY VISIT FINALIZE)
# =========================================================

def on_visit_finalized_apply_poc_policy(
    db: Session,
    *,
    visit,
    patient: Patient,
    finalized_by_user_id: UUID | None,
) -> None:
    """
    SNS EMR POC_UPDATE policy (canonical):

    CRISIS:
      - Every finalized RN visit applies
      - Ensure same-day POC_UPDATE and COMPLETE with VISIT evidence

    ROUTINE + WOUNDS:
      - Every finalized RN visit applies
      - Schedule next POC_UPDATE due = visit_time + 14 days

    ROUTINE + SUPPORT STAFF (CHHA/LVN):
      - Only supervisory RN visits apply
      - Schedule next POC_UPDATE due = visit_time + 14 days

    ROUTINE RN-ONLY:
      - Any finalized RN follow-up visit applies
      - Schedule next POC_UPDATE due = visit_time + 14 days
    """
    tenant_id = patient.tenant_id
    patient_id = patient.id

    if not _is_rn_visit(visit):
        return

    visit_time = _visit_time_utc(visit)
    visit_day = visit_time.date()
    acuity = _acuity_at_visit(visit, patient)
    patient_has_wounds = _has_wounds(patient)
    patient_has_support_staff = _has_support_staff(patient)

    benefit_period_id = _resolve_benefit_period_id(
        db,
        tenant_id=tenant_id,
        patient_id=patient_id,
        as_of_day=visit_day,
    )

    # ---------------------------------------------------------
    # CRISIS: every RN visit = same-day POC create/complete
    # ---------------------------------------------------------
    if acuity == "CRISIS":
        # Idempotency per visit evidence
        if _find_completed_poc_for_visit(
            db,
            tenant_id=tenant_id,
            patient_id=patient_id,
            visit_id=visit.id,
        ):
            return

        existing = _find_open_poc_task(db, tenant_id=tenant_id, patient_id=patient_id)

        if existing:
            existing.due_at = visit_time
            existing.due_date = visit_day

            if getattr(existing, "benefit_period_id", None) is None and benefit_period_id is not None:
                existing.benefit_period_id = benefit_period_id

            complete_task_with_evidence(
                db,
                task_id=existing.id,
                completion_reference_type=CompletionReferenceType.VISIT,
                completion_reference_id=visit.id,
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
            origin=TaskOrigin.MANUAL,
            created_by=finalized_by_user_id,
            benefit_period_id=benefit_period_id,
        )

        complete_task_with_evidence(
            db,
            task_id=task.id,
            completion_reference_type=CompletionReferenceType.VISIT,
            completion_reference_id=visit.id,
            completed_by=finalized_by_user_id,
            completed_at=visit_time,
        )
        db.flush()
        return

    # ---------------------------------------------------------
    # Only ROUTINE handled below
    # ---------------------------------------------------------
    if acuity != "ROUTINE":
        return

    # ---------------------------------------------------------
    # ROUTINE + WOUNDS:
    # every RN visit drives the 14-day cadence
    # ---------------------------------------------------------
    if patient_has_wounds:
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
        return

    # ---------------------------------------------------------
    # ROUTINE + support staff:
    # only supervisory RN visits drive the next POC_UPDATE
    # ---------------------------------------------------------
    if patient_has_support_staff:
        if not bool(getattr(visit, "is_supervisory", False) or getattr(visit, "supervisory", False)):
            return

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
        return

    # ---------------------------------------------------------
    # ROUTINE RN-only:
    # any RN follow-up visit drives the next POC_UPDATE
    # ---------------------------------------------------------
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