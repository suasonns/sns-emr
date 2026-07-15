from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Optional
from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified

from app.models.task import Task
from app.models.clinical_note import ClinicalNote
from app.models.enums import (
    CompletionReferenceType,
    TaskDiscipline,
    TaskOrigin,
    TaskRegulatoryBasis,
    TaskStatus,
    TaskType,
)
from app.services.task_sla_engine import assign_sla_to_task


# =========================================================
# TIME HELPERS
# =========================================================

def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


# =========================================================
# ENUM RESOLUTION HELPERS
# =========================================================

def _resolve_enum_required(enum_cls, *candidates: str):
    """
    Resolve enum by member name or enum value.

    Raises:
        ValueError: if no candidate matches.
    """
    for candidate in candidates:
        if candidate in enum_cls.__members__:
            return enum_cls.__members__[candidate]

        for member in enum_cls:
            if str(member.value) == candidate:
                return member

    raise ValueError(
        f"Could not resolve required enum {enum_cls.__name__} from {candidates}"
    )


def _resolve_enum_optional(enum_cls, *candidates: str):
    """
    Resolve enum by member name or enum value.

    Returns:
        Enum member if found, otherwise None.
    """
    for candidate in candidates:
        if candidate in enum_cls.__members__:
            return enum_cls.__members__[candidate]

        for member in enum_cls:
            if str(member.value) == candidate:
                return member

    return None


# =========================================================
# COMMON ENUM RESOLVERS
# =========================================================

def _task_status_pending():
    return _resolve_enum_required(TaskStatus, "PENDING")


def _task_status_completed():
    return _resolve_enum_required(TaskStatus, "COMPLETED")


def _active_task_statuses():
    """
    Canonical active task statuses.

    These represent tasks that are still open / unresolved in workflow terms,
    even though the system no longer uses a literal OPEN enum value.
    """
    statuses = []
    for name in ("PENDING", "IN_PROGRESS", "OVERDUE"):
        member = _resolve_enum_optional(TaskStatus, name)
        if member is not None and member not in statuses:
            statuses.append(member)
    return statuses


def _origin_periodic():
    return _resolve_enum_required(TaskOrigin, "PERIODIC")


def _origin_manual():
    return _resolve_enum_required(TaskOrigin, "MANUAL")


def _origin_system():
    value = _resolve_enum_optional(TaskOrigin, "SYSTEM")
    return value if value is not None else _origin_manual()


def _discipline_rn():
    return _resolve_enum_required(TaskDiscipline, "RN")


def _discipline_msw():
    value = _resolve_enum_optional(TaskDiscipline, "MSW", "SW", "LCSW", "BSW")
    return value if value is not None else _discipline_rn()


def _discipline_sc():
    value = _resolve_enum_optional(TaskDiscipline, "SC", "CHAPLAIN")
    return value if value is not None else _discipline_rn()


def _discipline_from_note(note_discipline: str | None):
    normalized = (note_discipline or "").strip().upper()
    resolved = _resolve_enum_optional(TaskDiscipline, normalized)
    return resolved if resolved is not None else _discipline_rn()


def _completion_reference_visit():
    return _resolve_enum_required(CompletionReferenceType, "VISIT")


def _completion_reference_note_for_discipline(discipline):
    """
    Compliance-safe note classification.

    IMPORTANT:
    This must only be used for COMPLETED tasks.
    Do not use completion_reference_* for PENDING tasks.
    """
    psychosocial_disciplines = {
        _resolve_enum_optional(TaskDiscipline, "SW"),
        _resolve_enum_optional(TaskDiscipline, "MSW"),
        _resolve_enum_optional(TaskDiscipline, "BSW"),
        _resolve_enum_optional(TaskDiscipline, "LCSW"),
    }
    psychosocial_disciplines.discard(None)

    spiritual_disciplines = {
        _resolve_enum_optional(TaskDiscipline, "SC"),
        _resolve_enum_optional(TaskDiscipline, "CHAPLAIN"),
    }
    spiritual_disciplines.discard(None)

    if discipline in psychosocial_disciplines:
        value = _resolve_enum_optional(
            CompletionReferenceType,
            "PSYCHOSOCIAL_SUPPORT_NOTE",
            "PSYCHOSOCIAL_NOTE",
        )
        if value is not None:
            return value

    if discipline in spiritual_disciplines:
        value = _resolve_enum_optional(
            CompletionReferenceType,
            "SPIRITUAL_CARE_NOTE",
            "SPIRITUAL_NOTE",
        )
        if value is not None:
            return value

    return _resolve_enum_required(CompletionReferenceType, "CLINICAL_NOTE", "NOTE")


# =========================================================
# TASK TYPE / REGULATORY BASIS RESOLUTION
# =========================================================

def _task_type_optional(*candidates: str):
    return _resolve_enum_optional(TaskType, *candidates)


def _task_type_required(*candidates: str):
    return _resolve_enum_required(TaskType, *candidates)


def _reg_basis_optional(*candidates: str):
    return _resolve_enum_optional(TaskRegulatoryBasis, *candidates)


# =========================================================
# SAFETY HELPERS
# =========================================================

def _strip_completion_fields_for_pending(task_kwargs: dict[str, Any]) -> None:
    """
    HARD SAFETY GUARD.

    Pending tasks must never carry completion evidence fields.

    Allowed:
    - reference_type / reference_id = source/origin of task

    Not allowed unless task is COMPLETED:
    - completion_reference_type
    - completion_reference_id
    - completed_at
    """
    task_kwargs.pop("completion_reference_type", None)
    task_kwargs.pop("completion_reference_id", None)
    task_kwargs.pop("completed_at", None)


def _add_reference_fields(
    task_kwargs: dict[str, Any],
    *,
    reference_type: str,
    reference_id: Any,
) -> None:
    """
    Attach source/origin reference fields safely.
    """
    if hasattr(Task, "reference_type"):
        task_kwargs["reference_type"] = reference_type

    if hasattr(Task, "reference_id"):
        task_kwargs["reference_id"] = reference_id


def _poc_alert_reason(problem_code: str) -> str:
    return f"POC_{problem_code}"


# =========================================================
# VISIT FINALIZATION TASK ENGINE
# =========================================================

def handle_visit_finalized(
    *,
    db: Session,
    visit,
    tenant_id: UUID,
    user_id: UUID,
    benefit_period_id: Optional[UUID] = None,
) -> None:
    """
    Gate 2 — RN-anchored obligations.

    Rules:
    - RN visits only
    - CRISIS: finalized RN visit creates and completes same-day POC_UPDATE
    - ROUTINE: supervisory RN visit creates next periodic POC_UPDATE due_date = visit_date + 14 days
    - This function does not commit; caller owns transaction boundary
    """
    task_type_poc = _task_type_required("POC_UPDATE")
    reg_basis_poc = _reg_basis_optional("POC_UPDATE")

    visit_type = (getattr(visit, "visit_type", "") or "").strip().upper()
    discipline = (getattr(visit, "visit_discipline", "") or "").strip().upper()
    acuity = (getattr(visit, "acuity_state_at_visit", "") or "").strip().upper()
    is_supervisory = bool(getattr(visit, "is_supervisory", False))

    is_rn = (discipline == "RN") or (visit_type == "RN")
    if not is_rn:
        return

    visit_id = getattr(visit, "id", None)
    patient_id = getattr(visit, "patient_id", None)

    if not visit_id or not patient_id:
        raise RuntimeError("Visit finalization missing visit_id or patient_id")

    now = _utcnow()
    visit_dt = getattr(visit, "visit_datetime", None) or now
    visit_day = visit_dt.date()
    finalized_at = getattr(visit, "finalized_at", None) or now

    # -----------------------------------------------------
    # CRISIS: create + complete same-day POC_UPDATE
    # -----------------------------------------------------
    if acuity == "CRISIS":
        existing = (
            db.query(Task)
            .filter(
                Task.tenant_id == tenant_id,
                Task.patient_id == patient_id,
                Task.task_type == task_type_poc,
                Task.completion_reference_type == _completion_reference_visit(),
                Task.completion_reference_id == visit_id,
            )
            .one_or_none()
        )

        if existing:
            assign_sla_to_task(db=db, task=existing)
            return

        task_kwargs = {
            "tenant_id": tenant_id,
            "patient_id": patient_id,
            "benefit_period_id": benefit_period_id,
            "task_type": task_type_poc,
            "origin": _origin_manual(),
            "discipline": _discipline_rn(),
            "status": _task_status_completed(),
            "due_date": visit_day,
            "due_at": finalized_at,
            "completed_at": finalized_at,
            "completion_reference_type": _completion_reference_visit(),
            "completion_reference_id": visit_id,
            "created_by": user_id,
            "updated_at": now,
        }

        if reg_basis_poc is not None:
            task_kwargs["regulatory_basis"] = reg_basis_poc

        task = Task(**task_kwargs)
        db.add(task)
        db.flush()

        assign_sla_to_task(db=db, task=task)
        return

    # -----------------------------------------------------
    # ROUTINE: supervisory RN creates next periodic +14 days
    # -----------------------------------------------------
    if acuity in ("", "ROUTINE") and is_supervisory:
        due_day = visit_day + timedelta(days=14)
        due_at = datetime.combine(due_day, datetime.min.time(), tzinfo=timezone.utc)

        existing = (
            db.query(Task)
            .filter(
                Task.tenant_id == tenant_id,
                Task.patient_id == patient_id,
                Task.task_type == task_type_poc,
                Task.status.in_(_active_task_statuses()),
                Task.benefit_period_id == benefit_period_id,
            )
            .one_or_none()
        )

        if existing:
            assign_sla_to_task(db=db, task=existing)
            return

        task_kwargs = {
            "tenant_id": tenant_id,
            "patient_id": patient_id,
            "benefit_period_id": benefit_period_id,
            "task_type": task_type_poc,
            "origin": _origin_periodic(),
            "discipline": _discipline_rn(),
            "status": _task_status_pending(),
            "due_date": due_day,
            "due_at": due_at,
            "sla_due_at": due_at,
            "created_by": user_id,
            "updated_at": now,
        }

        _add_reference_fields(
            task_kwargs,
            reference_type="VISIT",
            reference_id=visit_id,
        )

        _strip_completion_fields_for_pending(task_kwargs)

        if reg_basis_poc is not None:
            task_kwargs["regulatory_basis"] = reg_basis_poc

        task = Task(**task_kwargs)
        db.add(task)
        db.flush()

        assign_sla_to_task(db=db, task=task)
        return


# =========================================================
# NOTE-DRIVEN TASK ENGINE
# =========================================================

def process_tasks_for_note(
    db: Session,
    *,
    note: ClinicalNote,
    user_id: UUID,
) -> None:
    """
    Generate tasks based on:

    - incident_required
    - validation clarification items
    - validation red flags

    IMPORTANT:
    POC-generated note tasks are handled by the canonical
    POC workflow and must not be duplicated here.

    This function does not commit.
    Caller owns transaction boundary.
    """

    validation = {}

    if isinstance(getattr(note, "content", None), dict):
        validation = note.content.get("_validation", {}) or {}

    clarification_items = validation.get(
        "needs_clarification",
        [],
    )

    red_flags = validation.get(
        "red_flags",
        [],
    )

    # -----------------------------------------------------
    # INCIDENT TASK
    # -----------------------------------------------------
    if _note_incident_required(note):
        _create_note_task(
            db=db,
            note=note,
            user_id=user_id,
            task_type_candidate=("INCIDENT_REPORT_REQUIRED",),
            discipline=_discipline_rn(),
            due_hours=4,
            regulatory_basis_candidate=("INCIDENT", "SAFETY", "OTHER"),
        )

    # -----------------------------------------------------
    # CLARIFICATION TASK
    # -----------------------------------------------------
    if _has_items(clarification_items):
        _create_note_task(
            db=db,
            note=note,
            user_id=user_id,
            task_type_candidate=("CLARIFY_DOCUMENTATION",),
            discipline=_discipline_from_note(note.discipline),
            due_hours=24,
            regulatory_basis_candidate=("DOCUMENTATION", "OTHER"),
        )

    # -----------------------------------------------------
    # CLINICAL REVIEW TASK
    # -----------------------------------------------------
    if _has_items(red_flags):
        _create_note_task(
            db=db,
            note=note,
            user_id=user_id,
            task_type_candidate=("CLINICAL_REVIEW_REQUIRED",),
            discipline=_discipline_rn(),
            due_hours=12,
            regulatory_basis_candidate=("CLINICAL_REVIEW", "OTHER"),
        )

    return

# =========================================================
# POC -> TASK BRIDGE (LEGACY / NO-OP)
# =========================================================

def process_poc_tasks_for_note(
    db: Session,
    *,
    note: ClinicalNote,
    user_id: UUID,
) -> None:
    """
    Legacy no-op kept for compatibility.

    Canonical POC follow-up task creation is handled by:
        app.services.poc_task_engine.process_pocs_to_tasks

    This function now only backfills/link-marks already generated POCs when a
    matching canonical task already exists. It does not create tasks.
    """
    if not isinstance(note.plan_of_care_updates, dict):
        return

    pocs = note.plan_of_care_updates.get("pocs")
    if not isinstance(pocs, list) or len(pocs) == 0:
        return

    changed = False

    for poc in pocs:
        if not isinstance(poc, dict):
            continue

        if poc.get("task_generated"):
            continue

        problem = poc.get("problem")
        if not isinstance(problem, dict):
            continue

        code = str(problem.get("code") or "").strip().upper()
        if not code:
            continue

        poc_id = poc.get("poc_id")

        existing = (
            db.query(Task)
            .filter(
                Task.tenant_id == note.tenant_id,
                Task.patient_id == note.patient_id,
                Task.status.in_(_active_task_statuses()),
            )
            .filter(Task.clinical_note_id == note.id)
            .filter(Task.reference_type == "POC")
            .filter(Task.reference_id == poc_id)
            .first()
        )

        if existing is None:
            existing = (
                db.query(Task)
                .filter(
                    Task.tenant_id == note.tenant_id,
                    Task.patient_id == note.patient_id,
                    Task.status.in_(_active_task_statuses()),
                )
                .filter(Task.clinical_note_id == note.id)
                .filter(Task.alert_reason == _poc_alert_reason(code))
                .first()
            )

        if existing is None:
            continue

        poc["task_generated"] = True
        poc["task_id"] = str(existing.id)

        if "task_history" not in poc or not isinstance(poc["task_history"], list):
            poc["task_history"] = []

        poc["task_history"].append(
            {
                "event": "TASK_LINKED_EXISTING",
                "task_id": str(existing.id),
                "generated_at": _utcnow().isoformat(),
                "generated_by": str(user_id) if user_id else None,
            }
        )
        changed = True

    if changed:
        flag_modified(note, "plan_of_care_updates")
        db.add(note)
        db.flush()


# =========================================================
# NOTE TASK CREATOR
# =========================================================

def _create_note_task(
    db: Session,
    *,
    note: ClinicalNote,
    user_id: UUID,
    task_type_candidate: tuple[str, ...],
    discipline,
    due_hours: int,
    regulatory_basis_candidate: tuple[str, ...] = (),
) -> None:
    task_type = _task_type_optional(*task_type_candidate)

    if task_type is None:
        return

    existing = _find_existing_note_task(
        db=db,
        note=note,
        task_type=task_type,
        discipline=discipline,
    )

    if existing:
        assign_sla_to_task(db=db, task=existing)
        return

    now = _utcnow()
    due_at = now + timedelta(hours=due_hours)
    due_date = due_at.date()
    regulatory_basis = _reg_basis_optional(*regulatory_basis_candidate)

    task_kwargs = {
        "tenant_id": note.tenant_id,
        "patient_id": note.patient_id,
        "task_type": task_type,
        "origin": _origin_system(),
        "discipline": discipline,
        "status": _task_status_pending(),
        "created_by": user_id,
        "updated_at": now,
        "due_date": due_date,
        "due_at": due_at,
        "sla_due_at": due_at,
    }

    _add_reference_fields(
        task_kwargs,
        reference_type="CLINICAL_NOTE",
        reference_id=note.id,
    )

    _strip_completion_fields_for_pending(task_kwargs)

    if hasattr(Task, "assigned_user_id"):
        task_kwargs["assigned_user_id"] = user_id

    if hasattr(Task, "clinical_note_id"):
        task_kwargs["clinical_note_id"] = note.id

    if hasattr(Task, "incident_id"):
        task_kwargs["incident_id"] = getattr(note, "incident_id", None)

    if regulatory_basis is not None:
        task_kwargs["regulatory_basis"] = regulatory_basis

    task = Task(**task_kwargs)
    db.add(task)
    db.flush()

    assign_sla_to_task(db=db, task=task)


# =========================================================
# LEGACY POC HELPERS (KEPT FOR COMPATIBILITY / UNUSED)
# =========================================================

def _create_poc_followup_task(
    db: Session,
    *,
    note: ClinicalNote,
    user_id: UUID,
    poc: dict,
    problem_code: str,
) -> Task | None:
    """
    Legacy helper retained for compatibility.

    Canonical POC follow-up task creation was moved to:
        app.services.poc_task_engine.process_pocs_to_tasks

    This helper intentionally returns an existing canonical task when one is
    already present and otherwise returns None to avoid duplicate task creation.
    """
    poc_id = poc.get("poc_id")

    existing = (
        db.query(Task)
        .filter(
            Task.tenant_id == note.tenant_id,
            Task.patient_id == note.patient_id,
            Task.status.in_(_active_task_statuses()),
        )
        .filter(Task.clinical_note_id == note.id)
        .filter(Task.reference_type == "POC")
        .filter(Task.reference_id == poc_id)
        .first()
    )

    if existing is not None:
        assign_sla_to_task(db=db, task=existing)
        return existing

    return None


# =========================================================
# TASK DEDUPLICATION HELPERS
# =========================================================

def _find_existing_note_task(
    *,
    db: Session,
    note: ClinicalNote,
    task_type,
    discipline,
) -> Task | None:
    query = db.query(Task).filter(
        Task.tenant_id == note.tenant_id,
        Task.patient_id == note.patient_id,
        Task.task_type == task_type,
        Task.discipline == discipline,
        Task.status.in_(_active_task_statuses()),
    )

    if hasattr(Task, "clinical_note_id"):
        query = query.filter(Task.clinical_note_id == note.id)

    return query.first()


def _find_existing_poc_task(
    *,
    db: Session,
    note: ClinicalNote,
    task_type,
    discipline,
) -> Task | None:
    query = db.query(Task).filter(
        Task.tenant_id == note.tenant_id,
        Task.patient_id == note.patient_id,
        Task.task_type == task_type,
        Task.discipline == discipline,
        Task.status.in_(_active_task_statuses()),
    )

    if hasattr(Task, "clinical_note_id"):
        query = query.filter(Task.clinical_note_id == note.id)

    return query.first()


# =========================================================
# POC TASK MAPPING
# =========================================================

def _discipline_for_poc(problem_code: str):
    if problem_code == "PSYCHOSOCIAL":
        return _discipline_msw()

    if problem_code == "SPIRITUAL":
        return _discipline_sc()

    return _discipline_rn()


def _poc_task_description(problem_code: str) -> str:
    if problem_code == "PAIN":
        return (
            "Review generated Pain POC, pain assessment, medication effectiveness, "
            "non-pharmacologic interventions, and need for provider notification."
        )

    if problem_code == "WOUND":
        return (
            "Review generated Wound / Skin Integrity POC, wound status, drainage, "
            "infection signs, treatment orders, and supply needs."
        )

    if problem_code == "RESPIRATORY":
        return (
            "Review generated Respiratory POC, dyspnea status, oxygen use, "
            "breathing pattern, secretions, and escalation needs."
        )

    if problem_code == "PSYCHOSOCIAL":
        return (
            "Review generated Psychosocial Support POC, caregiver stress, coping status, "
            "support system, and need for psychosocial support follow-up."
        )

    if problem_code == "SPIRITUAL":
        return (
            "Review generated Spiritual Care POC, chaplain request, prayer/spiritual "
            "support needs, existential concerns, and need for spiritual care follow-up."
        )

    return "Review generated care-plan item and determine appropriate follow-up."


# =========================================================
# GENERAL HELPERS
# =========================================================

def _note_incident_required(note: ClinicalNote) -> bool:
    value = getattr(note, "incident_required", False)

    if isinstance(value, bool):
        return value

    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y"}

    return bool(value)


def _has_items(value) -> bool:
    if isinstance(value, bool):
        return value

    if isinstance(value, list):
        return len(value) > 0

    if isinstance(value, str):
        return bool(value.strip())

    return False