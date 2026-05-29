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

    ENTERPRISE RULES (CMS / ACHC / CHAP):

    RN VISITS ONLY:
      - Only RN discipline or RN visit_type anchors POC_UPDATE tasks

    ROUTINE:
      - Supervisory RN finalized visit creates POC_UPDATE
      - due_date = visit_date + 14 days
      - status = PENDING
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

    # -----------------------------
    # Normalize visit properties
    # -----------------------------
    visit_type = (getattr(visit, "visit_type", "") or "").strip().upper()
    discipline = (getattr(visit, "visit_discipline", "") or "").strip().upper()
    acuity = (getattr(visit, "acuity_state_at_visit", "") or "").strip().upper()
    is_supervisory = bool(getattr(visit, "is_supervisory", False))

    # RN determination must tolerate either field
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

    # -----------------------------
    # CRISIS: create + complete same-day POC_UPDATE (idempotent)
    # -----------------------------
    if acuity == "CRISIS":
        # Hard idempotency: do not duplicate evidence-linked completion tasks
        existing = (
            db.query(Task)
            .filter(
                Task.tenant_id == tenant_id,
                Task.patient_id == patient_id,
                Task.task_type == "POC_UPDATE",
                Task.completion_reference_type == "VISIT",
                Task.completion_reference_id == visit_id,
            )
            .one_or_none()
        )
        if existing:
            return

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
            completion_reference_id=visit_id,
            created_by=user_id,
        )
        db.add(task)
        db.flush()
        return

    # -----------------------------
    # ROUTINE: supervisory RN → next due +14 days
    # -----------------------------
    if acuity in ("", "ROUTINE") and is_supervisory:
        due_day = visit_day + timedelta(days=14)

        # HARD idempotency: only ONE open POC_UPDATE per patient per benefit period
        existing = (
            db.query(Task)
            .filter(
                Task.tenant_id == tenant_id,
                Task.patient_id == patient_id,
                Task.task_type == "POC_UPDATE",
                Task.status.in_(["PENDING", "OVERDUE"]),
                Task.benefit_period_id == benefit_period_id,
            )
            .one_or_none()
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
            completion_reference_id=visit_id,
            created_by=user_id,
        )
        db.add(task)
        db.flush()
        return