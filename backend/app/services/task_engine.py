# app/services/task_engine.py

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.task import Task


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

    ROUTINE:
      - Supervisory RN finalized visit creates POC_UPDATE task
      - due_date = visit_date + 14 days
      - status = PENDING
      - origin = PERIODIC
      - evidence = VISIT(visit.id)

    CRISIS:
      - Any RN finalized visit creates + completes same-day POC_UPDATE task
      - status = COMPLETED
      - origin = MANUAL
      - evidence = VISIT(visit.id)

    NOTE: This function does NOT commit. Caller owns the transaction.
    """

    discipline = (getattr(visit, "visit_discipline", "") or "").strip().upper()
    acuity = (getattr(visit, "acuity_state_at_visit", "") or "").strip().upper()
    is_supervisory = bool(getattr(visit, "is_supervisory", False))

    # Only RN discipline anchors POC_UPDATE tasks
    if discipline != "RN":
        return

    visit_dt = getattr(visit, "visit_datetime", None) or datetime.now(timezone.utc)
    visit_day = visit_dt.date()
    visit_id = getattr(visit, "id", None)
    patient_id = getattr(visit, "patient_id", None)
    finalized_at = getattr(visit, "finalized_at", None) or datetime.now(timezone.utc)

    if not visit_id or not patient_id:
        return

    # -------------------------------------------------
    # CRISIS: create + complete same-day POC_UPDATE
    # -------------------------------------------------
    if acuity == "CRISIS":
        task = Task(
            tenant_id=tenant_id,
            patient_id=patient_id,
            benefit_period_id=benefit_period_id,
            task_type="POC_UPDATE",
            regulatory_basis="POC_UPDATE",
            origin="MANUAL",
            discipline="RN",
            status="COMPLETED",
            due_date=visit_day,
            completed_at=finalized_at,
            completion_reference_type="VISIT",
            completion_reference_id=visit_id,  # ✅ UUID, not str
            created_by=user_id,
        )
        db.add(task)
        db.flush()
        return

    # -------------------------------------------------
    # ROUTINE: supervisory RN → next due +14 days
    # -------------------------------------------------
    if acuity in ("", "ROUTINE") and is_supervisory:
        due_day = (visit_dt + timedelta(days=14)).date()

        # Idempotency: do not create duplicates
        existing = (
            db.query(Task)
            .filter(
                Task.tenant_id == tenant_id,
                Task.patient_id == patient_id,
                Task.task_type == "POC_UPDATE",
                Task.due_date == due_day,
                Task.status.in_(["PENDING", "OVERDUE"]),
            )
            .first()
        )
        if existing:
            return

        task = Task(
            tenant_id=tenant_id,
            patient_id=patient_id,
            benefit_period_id=benefit_period_id,
            task_type="POC_UPDATE",
            regulatory_basis="POC_UPDATE",
            origin="PERIODIC",
            discipline="RN",
            status="PENDING",
            due_date=due_day,
            completion_reference_type="VISIT",
            completion_reference_id=visit_id,  # ✅ UUID
            created_by=user_id,
        )
        db.add(task)
        db.flush()
        return