from __future__ import annotations

from datetime import datetime, timedelta
from uuid import uuid4

from sqlalchemy.orm import Session

from app.models.task import Task
from app.models.clinical_note import ClinicalNote


def create_clinical_review_task(
    db: Session,
    *,
    note: ClinicalNote,
) -> None:

    # ---------------------------------------------------
    # SAFETY GUARDS
    # ---------------------------------------------------
    if not note:
        return

    if not note.patient_id or not note.tenant_id:
        return

    now = datetime.utcnow()

    # ---------------------------------------------------
    # PREVENT DUPLICATES
    # ---------------------------------------------------
    existing = (
        db.query(Task)
        .filter(Task.patient_id == note.patient_id)
        .filter(Task.task_type == "CLINICAL_REVIEW_REQUIRED")
        .filter(Task.status.in_(["PENDING", "IN_PROGRESS", "OVERDUE"]))
        .first()
    )

    if existing:
        return

    # ---------------------------------------------------
    # SAFE DEFAULTS
    # ---------------------------------------------------
    discipline = "RN"

    due_at = now + timedelta(hours=24)
    due_date = due_at.date()

    # ---------------------------------------------------
    # ✅ CRITICAL FIX
    # ---------------------------------------------------
    # THIS TASK IS NOT COMPLETED → DO NOT USE COMPLETION FIELDS
    # ---------------------------------------------------

    new_task = Task(
        id=uuid4(),

        tenant_id=note.tenant_id,
        patient_id=note.patient_id,

        task_type="CLINICAL_REVIEW_REQUIRED",
        status="PENDING",

        discipline=discipline,

        created_at=now,
        updated_at=now,

        due_date=due_date,
        due_at=due_at,
        sla_due_at=due_at,

        created_by=note.author_id,
        assigned_user_id=note.author_id,

        origin="SYSTEM",
        regulatory_basis="POC_UPDATE",

        # ✅ USE REFERENCE (NOT COMPLETION)
        reference_type="CLINICAL_NOTE",
        reference_id=note.id,

        # 🚫 DO NOT ADD THESE:
        # completion_reference_type ❌
        # completion_reference_id ❌
        # completed_at ❌
    )

    db.add(new_task)