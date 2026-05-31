from __future__ import annotations

from uuid import UUID
from sqlalchemy.orm import Session

from app.models.patient import Patient
from app.services.poc_update_automation import on_visit_finalized_apply_poc_policy


def handle_poc_update_on_visit_finalize(
    db: Session,
    *,
    visit,
    patient: Patient,
    finalized_by_user_id: UUID | None,
) -> None:
    """
    Legacy wrapper for older call sites.

    Canonical behavior lives in app.services.poc_update_automation.on_visit_finalized_apply_poc_policy.
    This wrapper exists to prevent drift between “tasks” and “automation” modules.
    """
    on_visit_finalized_apply_poc_policy(
        db,
        visit=visit,
        patient=patient,
        finalized_by_user_id=finalized_by_user_id,
    )