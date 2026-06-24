# app/services/task_auto_complete_engine.py

from __future__ import annotations

from typing import Optional
from uuid import UUID
from datetime import datetime

from sqlalchemy.orm import Session

from app.models.task import Task
from app.models.clinical_note import ClinicalNote
from app.models.enums import CompletionReferenceType, TaskStatus

from app.services.task_completion_evidence import complete_task_with_evidence
from app.domain.tasks.task_form_rules import TASK_REQUIRED_FORMS


# =========================================================
# ✅ HELPER FUNCTIONS
# =========================================================

def _is_task_already_completed(task: Task) -> bool:
    return task.status == TaskStatus.COMPLETED


def _is_valid_form_for_task(task_type: str, form_key: str) -> bool:
    allowed_forms = TASK_REQUIRED_FORMS.get(task_type)

    if not allowed_forms:
        return True  # no restriction configured

    return form_key in allowed_forms


def _validate_discipline_vs_form(discipline: str, form_family: str):
    # ❌ MSW cannot complete clinical forms
    if discipline in {"SW", "MSW"} and form_family == "CLINICAL":
        raise ValueError("MSW cannot complete clinical forms")

    # ❌ RN cannot complete psychosocial
    if discipline in {"RN", "LVN"} and form_family == "PSYCHOSOCIAL":
        raise ValueError("RN cannot complete psychosocial forms")


# =========================================================
# ✅ MAIN ENGINE
# =========================================================

def auto_complete_tasks_from_note(
    *,
    db: Session,
    note: ClinicalNote,
    user_id: Optional[UUID],
) -> None:
    """
    Auto-complete tasks tied to a clinical note using FORM ENGINE enforcement.

    ✅ Enforces:
    - correct form → task mapping
    - discipline validity
    - idempotent completion
    - audit-safe evidence linkage
    """

    # ✅ safety checks
    if not note.form_key:
        return

    # ✅ enforce discipline rules
    _validate_discipline_vs_form(
        discipline=note.discipline,
        form_family=note.form_family,
    )

    # ✅ ensure POC structure exists
    if not isinstance(note.plan_of_care_updates, dict):
        return

    pocs = note.plan_of_care_updates.get("pocs")

    if not isinstance(pocs, list) or not pocs:
        return

    # ✅ iterate POC-linked tasks
    for poc in pocs:
        if not isinstance(poc, dict):
            continue

        task_id = poc.get("task_id")

        if not task_id:
            continue

        task = db.query(Task).filter(Task.id == task_id).one_or_none()

        if not task:
            continue

        # ✅ skip already completed
        if _is_task_already_completed(task):
            continue

        # 🔴 FORM VALIDATION (CRITICAL RULE)
        if not _is_valid_form_for_task(task.task_type, note.form_key):
            continue  # 🚨 BLOCK WRONG FORM

        # ✅ COMPLETE WITH EVIDENCE
        complete_task_with_evidence(
            db,
            task_id=task_id,
            completion_reference_type=CompletionReferenceType.CLINICAL_NOTE,
            completion_reference_id=note.id,
            completed_by=user_id,
        )

    db.flush()