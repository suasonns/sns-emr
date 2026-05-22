# app/services/task_generation.py

from __future__ import annotations

from typing import Dict, List
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.task import Task


def generate_tasks_for_benefit_period(
    *,
    db: Session,
    tenant_id: UUID,
    patient_id: UUID,
    benefit_period_id: UUID,
    frequency_map: Dict[str, int],
    created_by: UUID,
) -> List[Task]:
    """
    Enterprise-safe placeholder.

    Intentionally returns an empty list until the frequency policy is finalized.
    """
    return []