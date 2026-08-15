# backend/app/services/idg_signature_validation.py

from __future__ import annotations

from typing import List

from sqlalchemy.orm import Session

from app.models.idg_attendee import IDGAttendee
from app.models.idg_review import IDGReview
from app.services.tenant_settings_service import TenantSettingsService


DEFAULT_REQUIRED_DISCIPLINES = {
    "RN",
    "MSW",
    "MD",
}


def _normalize_discipline(value: str | None) -> str:
    """
    Normalize discipline values for comparison.

    Examples:
        rn -> RN
        Rn -> RN
        RN -> RN
    """

    if not value:
        return ""

    return str(value).strip().upper()


def validate_required_signatures(
    db: Session,
    *,
    idg_review_id,
) -> List[str]:
    """
    Returns a list of missing required disciplines.

    Empty list:
        Safe to complete review.

    Non-empty list:
        Required disciplines have not signed.
    """

    review = (
        db.query(IDGReview)
        .filter(IDGReview.id == idg_review_id)
        .first()
    )

    if not review:
        raise ValueError(
            f"IDG review not found: {idg_review_id}"
        )

    attendees = (
        db.query(IDGAttendee)
        .filter(IDGAttendee.idg_review_id == idg_review_id)
        .all()
    )

    signed_disciplines = {
        _normalize_discipline(attendee.discipline)
        for attendee in attendees
        if getattr(attendee, "signed", False)
    }

    try:
        required_disciplines = (
            TenantSettingsService.get_idg_required_note_disciplines(
                db=db,
                tenant_id=review.tenant_id,
                review_type=getattr(
                    review,
                    "review_type",
                    None,
                ),
            )
        )
    except Exception:
        required_disciplines = DEFAULT_REQUIRED_DISCIPLINES

    missing_disciplines = (
        required_disciplines
        - signed_disciplines
    )

    return sorted(missing_disciplines)