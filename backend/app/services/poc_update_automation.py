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
    """
    Canonical open state for automatically managed POC_UPDATE tasks.

    Policy:
    - Open POC_UPDATE tasks must remain PENDING unless explicitly completed.
    - Completed tasks must be completed through evidence-aware completion logic.
    """
    return TaskStatus.PENDING


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
    return visit_type == "RN"


def _is_supervisory_visit(visit) -> bool:
    """
    Determine whether a visit is supervisory.

    Enterprise-safe normalization across schema variations.

    Supports:
    - is_supervisory (preferred)
    - supervisory (legacy)
    - form_type / visit subtype fallback (common in EMRs)

    Returns:
        bool
    """

    # ✅ Direct boolean fields (best case)
    if hasattr(visit, "is_supervisory"):
        return bool(visit.is_supervisory)

    if hasattr(visit, "supervisory"):
        return bool(visit.supervisory)

    # ✅ Fallback to form_type if used in your system
    form_type = getattr(visit, "form_type", None)
    if form_type:
        return str(form_type).upper() in {
            "SUPV",
            "SUPERVISORY",
            "SUPV VISIT",
            "SUPV VISIT ONLY",
            "RN SUPERVISORY",
        }

    # ✅ DEBUG visibility (temporary — remove later)
    print(f">>> WARNING: No supervisory field found on visit {getattr(visit, 'id', 'UNKNOWN')}")

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

    Naive datetimes are treated as UTC.
    """
    for attr in ("visit_datetime", "finalized_at", "completed_at", "occurred_at", "performed_at"):
        value = getattr(visit, attr, None)
        if value is not None:
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

    # ✅ IMPORTANT: check for None explicitly, NOT truthiness
    if visit_acuity is not None:
        return str(visit_acuity).strip().upper()

    # ⚠️ fallback ONLY if visit-level completely missing
    patient_acuity = getattr(patient, "acuity_state", None)

    if patient_acuity is not None:
        return str(patient_acuity).strip().upper()

    return "ROUTINE"

def _has_support_staff(patient: Patient) -> bool:
    """
    Return whether the patient has delegated support staff.

    Support staff currently means:
    - CHHA
    - LVN
    """
    return bool(
        getattr(patient, "has_chha", False)
        or getattr(patient, "has_lvn", False)
    )


def _has_wounds(patient: Patient) -> bool:
    """
    Return whether the patient currently has wound-related monitoring needs.

    Important Phase 1 rule:
    - Wounds may influence clinical reassessment cadence.
    - Wounds must NOT bypass the supervisory RN anchor requirement for PERIODIC
      POC_UPDATE scheduling in this automation layer.
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
    """
    Resolve the active benefit period for the patient as of the visit day.

    Returns:
    - benefit period UUID when found
    - None when no active benefit period is available
    """
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
    tenant_id: UUID,
    patient_id: UUID,
) -> Task | None:
    """
    Find the most recent open POC_UPDATE task for the patient.

    Open means:
    - status == PENDING
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
    Find a POC_UPDATE task already linked to this visit as completion evidence.

    This protects same-visit idempotency, especially for crisis behavior.
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
    Create a POC_UPDATE task in PENDING status.

    This low-level function intentionally does not contain visit policy logic.
    Policy guards must be applied by the caller before invoking this function.
    """

    # ✅ Unified timestamp (audit requirement)
    now = _utcnow()

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

        # ✅ Audit fields
        created_at=now,
        updated_at=now,
               
        # ✅ ✅ SLA FIELDS (NEW — CRITICAL)
        sla_start_at=now,
        sla_due_at=due_at,
        is_overdue=False,
    )

    db.add(task)
    db.flush()
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

    tenant_id = patient.tenant_id
    patient_id = patient.id

    existing_task = _find_open_poc_task(
        db,
        tenant_id=tenant_id,
        patient_id=patient_id,
    )

    # ✅ STRICT: reuse ONLY if still PENDING
    if existing_task:
        if existing_task.status == TaskStatus.PENDING:
            return existing_task
        # ❗ ignore COMPLETED or invalid tasks
        existing_task = None

    due_at = visit_time + timedelta(days=14)

    task = _create_poc_task(
        db,
        tenant_id=tenant_id,
        patient_id=patient_id,
        due_at=due_at,
        origin=TaskOrigin.PERIODIC,
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

    Phase 1 Compliance Policy:

    CRISIS:
        - Every finalized RN visit MUST create a same-day POC_UPDATE.
        - The task MUST be completed immediately with VISIT evidence.
        - Origin = MANUAL.

    ROUTINE:
        - Only supervisory RN visits can anchor periodic POC_UPDATE.
        - Create a PENDING POC_UPDATE with due_date = visit_date + 14 days.
        - Origin = PERIODIC.
        - MUST NOT auto-complete.

    Key Rule:
        - CRISIS and ROUTINE behaviors must be mutually exclusive.
    """

    # ---------------------------------------------------------
    # BASIC DEBUG / TRACE
    # ---------------------------------------------------------
    print(">>> POC POLICY TRIGGERED", visit.id)
    print(">>> RN CHECK:", _is_rn_visit(visit))
    print(">>> SUPERVISORY:", _is_supervisory_visit(visit))

    if not _is_rn_visit(visit):
        return

    tenant_id = patient.tenant_id
    patient_id = patient.id

    visit_time = _visit_time_utc(visit)
    visit_day = visit_time.date()

    acuity = _acuity_at_visit(visit, patient)
    print(">>> FINAL RESOLVED ACUITY:", acuity)

    benefit_period_id = _resolve_benefit_period_id(
        db,
        tenant_id=tenant_id,
        patient_id=patient_id,
        as_of_day=visit_day,
    )

    # =========================================================
    # CRISIS LOGIC (STRICT ISOLATION)
    # =========================================================
    if acuity == "CRISIS":

        # ✅ Idempotency: already completed for this visit
        existing_completed = _find_completed_poc_for_visit(
            db,
            tenant_id=tenant_id,
            patient_id=patient_id,
            visit_id=visit.id,
        )
        if existing_completed:
            return

        existing_open_task = _find_open_poc_task(
            db,
            tenant_id=tenant_id,
            patient_id=patient_id,
        )

        if existing_open_task:
            # Update timing
            existing_open_task.due_at = visit_time
            existing_open_task.due_date = visit_day

            # Attach benefit period if missing
            if (
                getattr(existing_open_task, "benefit_period_id", None) is None
                and benefit_period_id is not None
            ):
                existing_open_task.benefit_period_id = benefit_period_id

            # ✅ COMPLETE EXISTING TASK
            complete_task_with_evidence(
                db,
                task_id=existing_open_task.id,
                completion_reference_type=CompletionReferenceType.VISIT,
                completion_reference_id=visit.id,
                completed_by=finalized_by_user_id,
                completed_at=visit_time,
            )

            db.flush()
            return  # ✅ HARD STOP (prevents ROUTINE logic)

        # ✅ CREATE + COMPLETE NEW TASK
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
        return  # ✅ HARD STOP

    # =========================================================
    # ROUTINE GUARD
    # =========================================================
    if acuity != "ROUTINE":
        return

    # =========================================================
    # ROUTINE LOGIC (NO COMPLETION ALLOWED)
    # =========================================================
    _schedule_next_periodic_poc_from_supervisory_visit(
        db,
        visit=visit,
        patient=patient,
        visit_time=visit_time,
        finalized_by_user_id=finalized_by_user_id,
        benefit_period_id=benefit_period_id,
    )

    db.flush()
