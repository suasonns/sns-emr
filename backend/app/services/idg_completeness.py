# services/idg_completeness.py

from __future__ import annotations

from typing import List

from sqlalchemy.orm import Session

from app.models.idg_note import IDGNote
from app.models.idg_review import IDGReview


def validate_idg_completeness(
    db: Session,
    *,
    idg_review_id,
    tenant_id,
) -> List[str]:
    """
    Validate IDG review completeness.

    Returns:
        list[str]: Missing or invalid IDG elements.
        Empty list means the IDG review is complete.
    """

    review = (
        db.query(IDGReview)
        .filter(
            IDGReview.id == idg_review_id,
            IDGReview.tenant_id == tenant_id,
        )
        .first()
    )

    if not review:
        return ["IDG_REVIEW_NOT_FOUND"]

    missing: List[str] = []

    if not review.review_date:
        missing.append("review_date")

    if not review.patient_id:
        missing.append("patient_id")

    if not review.summary:
        missing.append("summary")

    notes = (
        db.query(IDGNote)
        .filter(
            IDGNote.idg_review_id == idg_review_id,
            IDGNote.tenant_id == tenant_id,
        )
        .all()
    )

    disciplines_seen = set()
    note_map = {}

    for note_record in notes:
        discipline = note_record.discipline

        if discipline in disciplines_seen:
            missing.append(f"{discipline}_duplicate_note")
            continue

        disciplines_seen.add(discipline)
        note_map[discipline] = note_record

    required_disciplines = [
        "RN",
        "MSW",
        "MD",
        "SC",
    ]

    for discipline in required_disciplines:
        if discipline not in note_map:
            missing.append(f"{discipline}_note_missing")
            continue

        note_record = note_map[discipline]

        if not note_record.note:
            missing.append(f"{discipline}_note_empty")
            continue

        if (
            isinstance(note_record.note, str)
            and note_record.note.strip() == ""
        ):
            missing.append(f"{discipline}_note_empty")

    return missing