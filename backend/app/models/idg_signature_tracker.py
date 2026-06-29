from __future__ import annotations

from typing import List, Dict

from sqlalchemy.orm import Session

from app.models.idg_attendee import IDGAttendee


# =========================================================
# GET ALL ATTENDEES
# =========================================================

def get_idg_attendees(
    db: Session,
    *,
    idg_review_id,
) -> List[IDGAttendee]:

    return (
        db.query(IDGAttendee)
        .filter(IDGAttendee.idg_review_id == idg_review_id)
        .all()
    )


# =========================================================
# WHO HAS SIGNED
# =========================================================

def get_signed_attendees(
    db: Session,
    *,
    idg_review_id,
):

    attendees = get_idg_attendees(db, idg_review_id=idg_review_id)

    return [a for a in attendees if a.signed]


# =========================================================
# WHO HAS NOT SIGNED (IMPORTANT)
# =========================================================

def get_pending_signatures(
    db: Session,
    *,
    idg_review_id,
):

    attendees = get_idg_attendees(db, idg_review_id=idg_review_id)

    return [a for a in attendees if not a.signed]


# =========================================================
# SIGNATURE STATUS SUMMARY
# =========================================================

def get_signature_status_summary(
    db: Session,
    *,
    idg_review_id,
) -> Dict:

    attendees = get_idg_attendees(db, idg_review_id=idg_review_id)

    total = len(attendees)
    signed = len([a for a in attendees if a.signed])
    pending = total - signed

    return {
        "total_attendees": total,
        "signed": signed,
        "pending": pending,
        "completion_rate": round((signed / total) * 100, 2) if total > 0 else 0,
    }


# =========================================================
# REQUIRE CORE SIGNATURES (OPTIONAL BUT POWERFUL)
# =========================================================

REQUIRED_DISCIPLINES = {"RN", "MSW", "MD"}


def get_missing_required_signatures(
    db: Session,
    *,
    idg_review_id,
):

    attendees = get_idg_attendees(db, idg_review_id=idg_review_id)

    signed_disciplines = {
        a.discipline for a in attendees if a.signed
    }

    missing = REQUIRED_DISCIPLINES - signed_disciplines

    return list(missing)