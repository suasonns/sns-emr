from __future__ import annotations

from typing import List

from sqlalchemy.orm import Session

from app.models.idg_attendee import IDGAttendee


REQUIRED_DISCIPLINES = {"RN", "MSW", "MD"}


def validate_required_signatures(
    db: Session,
    *,
    idg_review_id,
) -> List[str]:
    """
    Returns list of missing required disciplines.
    If empty → safe to complete.
    """

    attendees = (
        db.query(IDGAttendee)
        .filter(IDGAttendee.idg_review_id == idg_review_id)
        .all()
    )

    signed_disciplines = {
        a.discipline for a in attendees if a.signed
    }

    missing = REQUIRED_DISCIPLINES - signed_disciplines

    return list(missing)