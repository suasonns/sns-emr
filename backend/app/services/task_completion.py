# app/services/task_completion.py

from __future__ import annotations

from sqlalchemy.orm import Session


def auto_complete_tasks_for_visit(
    *,
    db: Session,
    tenant_id,
    visit,
    completed_by,
) -> None:
    """
    Enterprise-safe stub.

    This hook is intentionally conservative:
    - Do not mutate tasks unless you have deterministic rules + evidence references
    - Do not commit; caller owns the transaction
    """
    return