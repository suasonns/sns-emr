# app/services/task_overdue_engine.py

from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Dict
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.task import Task


def evaluate_task_timeliness(
    *,
    db: Session,
    tenant_id: UUID,
    as_of: date | None = None,
) -> Dict[str, int]:
    """
    Enterprise Task Timeliness Evaluation Engine (skeleton)

    Returns counts by status for dashboards / compliance read models.
    """
    if as_of is None:
        as_of = datetime.now(timezone.utc).date()

    counts: Dict[str, int] = {"PENDING": 0, "OVERDUE": 0, "COMPLETED": 0}

    rows = (
        db.query(Task.status, sa.func.count(Task.id))  # type: ignore[name-defined]
        .filter(Task.tenant_id == tenant_id)
        .group_by(Task.status)
        .all()
    )

    for status_value, count_value in rows:
        counts[str(status_value)] = int(count_value)

    return counts