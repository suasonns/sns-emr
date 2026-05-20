# app/services/task_engine.py

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.visit_types import normalize_visit_type
from app.services.benefit_periods import get_current_benefit_period


def handle_visit_finalized(
    db: Session,
    *,
    visit: Dict[str, Any],
    tenant_id: Optional[str] = None,
    user_id: Optional[str] = None,
) -> None:
    """
    Task Engine hook: called when a visit is finalized.

    Compliance rules implemented (minimum viable):
      - ROUTINE:
        - Finalized supervisory RN visit creates POC_UPDATE task due_date = visit_date + 14 days (origin PERIODIC)
      - CRISIS:
        - Every finalized RN visit creates same-day POC_UPDATE and completes it (origin MANUAL)

    Evidence requirement on completion:
      - status = COMPLETED
      - completed_at timestamp
      - completion_reference_type = 'VISIT'
      - completion_reference_id = visit_id

    Notes:
      - This function does NOT make clinical decisions; it enforces workflow obligations and audit-ready evidence.
      - Schema-tolerant inserts: tries rich insert first, then falls back to minimal columns if schema differs.
    """
    if db is None:
        raise ValueError("db session is required")
    if not isinstance(visit, dict):
        raise ValueError("visit must be a dict-like object")

    visit_id = str(visit.get("id") or "")
    patient_id = str(visit.get("patient_id") or "")
    raw_visit_type = visit.get("visit_type") or visit.get("discipline") or ""
    is_supervisory = bool(visit.get("is_supervisory") or visit.get("supervisory") or False)

    if not visit_id or not patient_id:
        # No-op: cannot create obligations without core identifiers
        return

    # Determine visit date (fallback to now)
    visit_date = _coerce_datetime(visit.get("visit_date") or visit.get("date") or visit.get("performed_at")) or datetime.utcnow()

    # Determine crisis mode (if your system flags it on the visit)
    # If absent, treat as ROUTINE.
    is_crisis = bool(visit.get("is_crisis") or visit.get("crisis") or False)

    # Normalize visit type (RN/LVN/NP/MD/SW/CHAPLAIN/CHHA/VOLUNTEER)
    try:
        vt = normalize_visit_type(str(raw_visit_type))
    except Exception:
        # If visit_type is malformed, do not crash finalization; no-op for task engine
        return

    # We only generate POC_UPDATE obligations on RN visits
    if vt != "RN":
        return

    # Benefit period association (optional)
    bp = None
    try:
        bp = get_current_benefit_period(db, patient_id=patient_id, tenant_id=str(tenant_id) if tenant_id else None)
    except Exception:
        bp = None
    benefit_period_id = None
    if isinstance(bp, dict):
        benefit_period_id = bp.get("id") or bp.get("benefit_period_id")

    if is_crisis:
        # CRISIS rule: same-day POC_UPDATE created and completed
        due_at = visit_date
        task_id = _create_task(
            db,
            tenant_id=tenant_id,
            patient_id=patient_id,
            benefit_period_id=benefit_period_id,
            task_type="POC_UPDATE",
            origin="MANUAL",
            due_at=due_at,
            created_by=user_id,
        )
        if task_id:
            _complete_task_with_evidence(
                db,
                task_id=task_id,
                completed_at=visit_date,
                completion_reference_type="VISIT",
                completion_reference_id=visit_id,
                completed_by=user_id,
            )
        return

    # ROUTINE rule: supervisory RN visit creates next POC_UPDATE due in +14 days
    if is_supervisory:
        due_at = visit_date + timedelta(days=14)
        _create_task(
            db,
            tenant_id=tenant_id,
            patient_id=patient_id,
            benefit_period_id=benefit_period_id,
            task_type="POC_UPDATE",
            origin="PERIODIC",
            due_at=due_at,
            created_by=user_id,
        )


# ----------------------------
# Internal helpers (schema-tolerant)
# ----------------------------

def _create_task(
    db: Session,
    *,
    tenant_id: Optional[str],
    patient_id: str,
    benefit_period_id: Optional[str],
    task_type: str,
    origin: str,
    due_at: datetime,
    created_by: Optional[str],
) -> Optional[str]:
    """
    Attempt to insert a task row. Returns task_id if available.
    Schema tolerant: tries a rich insert, then falls back to minimal insert.
    """
    now = datetime.utcnow()

    # Rich insert attempt (common columns)
    try:
        row = db.execute(
            text(
                """
                INSERT INTO tasks (
                    tenant_id,
                    patient_id,
                    benefit_period_id,
                    task_type,
                    origin,
                    status,
                    due_at,
                    created_at,
                    created_by
                )
                VALUES (
                    :tenant_id,
                    :patient_id,
                    :benefit_period_id,
                    :task_type,
                    :origin,
                    'OPEN',
                    :due_at,
                    :created_at,
                    :created_by
                )
                RETURNING id
                """
            ),
            {
                "tenant_id": tenant_id,
                "patient_id": patient_id,
                "benefit_period_id": benefit_period_id,
                "task_type": task_type,
                "origin": origin,
                "due_at": due_at,
                "created_at": now,
                "created_by": created_by,
            },
        ).scalar()
        return str(row) if row else None
    except Exception:
        pass

    # Minimal insert fallback
    try:
        row = db.execute(
            text(
                """
                INSERT INTO tasks (
                    patient_id,
                    task_type,
                    status,
                    due_at,
                    created_at
                )
                VALUES (
                    :patient_id,
                    :task_type,
                    'OPEN',
                    :due_at,
                    :created_at
                )
                RETURNING id
                """
            ),
            {
                "patient_id": patient_id,
                "task_type": task_type,
                "due_at": due_at,
                "created_at": now,
            },
        ).scalar()
        return str(row) if row else None
    except Exception:
        return None


def _complete_task_with_evidence(
    db: Session,
    *,
    task_id: str,
    completed_at: datetime,
    completion_reference_type: str,
    completion_reference_id: str,
    completed_by: Optional[str],
) -> None:
    """
    Mark task completed and attach evidence reference.
    Schema tolerant: tries rich update then falls back to status-only.
    """
    # Rich update attempt
    try:
        db.execute(
            text(
                """
                UPDATE tasks
                SET status = 'COMPLETED',
                    completed_at = :completed_at,
                    completion_reference_type = :ref_type,
                    completion_reference_id = :ref_id,
                    completed_by = :completed_by
                WHERE id = :task_id
                """
            ),
            {
                "task_id": task_id,
                "completed_at": completed_at,
                "ref_type": completion_reference_type,
                "ref_id": completion_reference_id,
                "completed_by": completed_by,
            },
        )
        return
    except Exception:
        pass

    # Minimal fallback: status only
    try:
        db.execute(
            text(
                """
                UPDATE tasks
                SET status = 'COMPLETED'
                WHERE id = :task_id
                """
            ),
            {"task_id": task_id},
        )
    except Exception:
        return


def _coerce_datetime(value: Any) -> Optional[datetime]:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    # Allow ISO strings
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except Exception:
        return None
