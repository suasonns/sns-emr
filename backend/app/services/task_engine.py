# app/services/task_engine.py

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session

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


# =========================================================
# ENUM RESOLUTION HELPERS
# =========================================================

def _resolve_enum_required(enum_cls, *candidates: str):
    """
    Resolve enum by member name OR value.
    Raises if none match.
    """
    for candidate in candidates:
        if candidate in enum_cls.__members__:
            return enum_cls.__members__[candidate]

        for member in enum_cls:
            if str(member.value) == candidate:
                return member

    raise ValueError(f"Could not resolve required enum {enum_cls.__name__} from {candidates}")


def _resolve_enum_optional(enum_cls, *candidates: str):
    """
    Resolve enum by member name OR value.
    Returns None if no match found.
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
    return _resolve_enum_required(TaskStatus, "PENDING", "DUE")


def _task_status_due():
    return _resolve_enum_required(TaskStatus, "DUE", "PENDING")


def _task_status_completed():
    return _resolve_enum_required(TaskStatus, "COMPLETED")


def _origin_periodic():
    return _resolve_enum_required(TaskOrigin, "PERIODIC")


def _origin_manual():
    return _resolve_enum_required(TaskOrigin, "MANUAL")


def _origin_system():
    value = _resolve_enum_optional(TaskOrigin, "SYSTEM")
    return value if value is not None else _origin_manual()


def _discipline_rn():
    return _resolve_enum_required(TaskDiscipline, "RN")


def _discipline_from_note(note_discipline: str):
    resolved = _resolve_enum_optional(TaskDiscipline, note_discipline)
    return resolved if resolved is not None else _discipline_rn()


def _completion_reference_visit():
    return _resolve_enum_required(CompletionReferenceType, "VISIT")


# =========================================================
# NOTE TASK TYPE RESOLUTION
# =========================================================

def _task_type_optional(*candidates: str):
    return _resolve_enum_optional(TaskType, *candidates)


def _task_type_required(*candidates: str):
    return _resolve_enum_required(TaskType, *candidates)


def _reg_basis_optional(*candidates: str):
    return _resolve_enum_optional(TaskRegulatoryBasis, *candidates)


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
    Gate 2 — RN-anchored obligations (Evidence-driven)

    ENTERPRISE RULES (CMS / ACHC / CHAP):

    RN VISITS ONLY:
      - Only RN discipline or RN visit_type anchors POC_UPDATE tasks

    ROUTINE:
      - Supervisory RN finalized visit creates POC_UPDATE
      - due_date = visit_date + 14 days
      - status = PENDING/DUE
      - origin = PERIODIC
      - evidence = VISIT(visit.id)
      - ONLY ONE open POC_UPDATE per patient per benefit period

    CRISIS:
      - Any RN finalized visit creates + COMPLETES same-day POC_UPDATE
      - origin = MANUAL
      - evidence = VISIT(visit.id)

    NOTE:
      - This function does NOT commit.
      - Caller owns transaction boundaries.
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

    visit_dt = getattr(visit, "visit_datetime", None) or datetime.now(timezone.utc)
    visit_day = visit_dt.date()
    finalized_at = getattr(visit, "finalized_at", None) or datetime.now(timezone.utc)

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
            "completed_at": finalized_at,
            "completion_reference_type": _completion_reference_visit(),
            "completion_reference_id": visit_id,
            "created_by": user_id,
        }

        if reg_basis_poc is not None:
            task_kwargs["regulatory_basis"] = reg_basis_poc

        task = Task(**task_kwargs)
        db.add(task)
        db.flush()
        return

    # -----------------------------------------------------
    # ROUTINE: supervisory RN → next due +14 days
    # -----------------------------------------------------
    if acuity in ("", "ROUTINE") and is_supervisory:
        due_day = visit_day + timedelta(days=14)

        existing = (
            db.query(Task)
            .filter(
                Task.tenant_id == tenant_id,
                Task.patient_id == patient_id,
                Task.task_type == task_type_poc,
                Task.status.in_([_task_status_pending(), _task_status_due()]),
                Task.benefit_period_id == benefit_period_id,
            )
            .one_or_none()
        )
        if existing:
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
            "completion_reference_type": _completion_reference_visit(),
            "completion_reference_id": visit_id,
            "created_by": user_id,
        }

        if reg_basis_poc is not None:
            task_kwargs["regulatory_basis"] = reg_basis_poc

        task = Task(**task_kwargs)
        db.add(task)
        db.flush()
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
    - red_flags
    - needs_clarification

    NOTE:
    - This function does NOT commit.
    - Caller owns transaction boundaries.
    """

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
    if _has_items(note.needs_clarification):
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
    if _has_items(note.red_flags):
        _create_note_task(
            db=db,
            note=note,
            user_id=user_id,
            task_type_candidate=("CLINICAL_REVIEW_REQUIRED",),
            discipline=_discipline_rn(),
            due_hours=12,
            regulatory_basis_candidate=("CLINICAL_REVIEW", "OTHER"),
        )


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

    # Safe enterprise behavior while enums are being expanded:
    # if canonical enum not available yet, do not create bad string data.
    if task_type is None:
        return

    existing = (
        db.query(Task)
        .filter(
            getattr(Task, "clinical_note_id") == note.id,
            Task.task_type == task_type,
        )
        .first()
    )

    if existing:
        return

    due_at = datetime.now(timezone.utc) + timedelta(hours=due_hours)
    regulatory_basis = _reg_basis_optional(*regulatory_basis_candidate)

    task_kwargs = {
        "tenant_id": note.tenant_id,
        "patient_id": note.patient_id,
        "task_type": task_type,
        "origin": _origin_system(),
        "discipline": discipline,
        "status": _task_status_pending(),
        "assigned_user_id": user_id,
        "created_by": user_id,
        "due_at": due_at,
    }

    if hasattr(Task, "clinical_note_id"):
        task_kwargs["clinical_note_id"] = note.id

    if hasattr(Task, "incident_id"):
        task_kwargs["incident_id"] = note.incident_id

    if regulatory_basis is not None:
        task_kwargs["regulatory_basis"] = regulatory_basis

    task = Task(**task_kwargs)
    db.add(task)
    db.flush()


# =========================================================
# HELPERS
# =========================================================

def _note_incident_required(note: ClinicalNote) -> bool:
    value = getattr(note, "incident_required", False)

    if isinstance(value, bool):
        return value

    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y"}

    return bool(value)


def _has_items(value) -> bool:
    return isinstance(value, list) and len(value) > 0