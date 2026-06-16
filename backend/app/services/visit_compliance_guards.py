from __future__ import annotations

from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.visit import Visit
from app.models.communications_log import CommunicationsLog


def enforce_commlog_for_visit_status_change(
    *,
    db: Session,
    visit: Visit,
    new_status: str,
    communications_log_id: UUID | None,
) -> None:
    """
    Compliance Rule (Phase 1C):

    MISSED or RESCHEDULED visits MUST reference
    a Communications Log entry that:
      - exists
      - belongs to the same patient

    Assumptions:
    - DB session is already tenant-scoped
    - This function enforces compliance only
    - No visit state is mutated here
    """

    normalized_status = (new_status or "").upper()

    # Only enforce for visit variance
    if normalized_status not in {"MISSED", "RESCHEDULED"}:
        return

    if not communications_log_id:
        raise HTTPException(
            status_code=400,
            detail=(
                "communications_log_id is required when marking a visit "
                "as MISSED or RESCHEDULED"
            ),
        )

    log = (
        db.query(CommunicationsLog)
        .filter(CommunicationsLog.id == communications_log_id)
        .first()
    )

    if not log:
        raise HTTPException(
            status_code=400,
            detail="Referenced Communications Log entry does not exist",
        )

    # Patient-level linkage is the compliance requirement
    if log.patient_id != visit.patient_id:
        raise HTTPException(
            status_code=400,
            detail="Communications Log entry does not match visit patient",
        )
