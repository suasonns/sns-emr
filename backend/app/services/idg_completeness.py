from __future__ import annotations

from typing import List
from sqlalchemy.orm import Session

from app.models.idg_review import IDGReview
from app.models.idg_note import IDGNote


def validate_idg_completeness(
    db: Session,
    *,
    idg_review_id,
    tenant_id,
) -> List[str]:
    """
    Returns list of missing required elements.
    Empty list = COMPLETE

    Must be called inside transaction-safe workflow (e.g. FOR UPDATE context)
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

    # =====================================================
    # CORE FIELDS
    # =====================================================

    if not review.meeting_date:
        missing.append("meeting_date")

    if not review.patient_id:
        missing.append("patient_id")

    if not review.benefit_period_id:
        missing.append("benefit_period_id")

    # =====================================================
    # PLAN OF CARE
    # =====================================================

    if not review.primary_diagnosis:
        missing.append("primary_diagnosis")

    if not review.goals_of_care:
        missing.append("goals_of_care")

    if not review.interventions:
        missing.append("interventions")

    # =====================================================
    # DISCIPLINE NOTES
    # =====================================================

    notes = (
        db.query(IDGNote)
        .filter(
            IDGNote.idg_review_id == idg_review_id,
            IDGNote.tenant_id == tenant_id,
        )
        .all()
    )

    # ✅ enforce uniqueness per discipline
    disciplines_seen = set()
    note_map = {}

    for note in notes:
        if note.discipline in disciplines_seen:
            missing.append(f"{note.discipline}_duplicate_note")
            continue

        disciplines_seen.add(note.discipline)
        note_map[note.discipline] = note

    # ✅ required IDG disciplines (enterprise-complete)
    REQUIRED_DISCIPLINES = ["RN", "MSW", "MD", "SC"]

    for discipline in REQUIRED_DISCIPLINES:

        if discipline not in note_map:
            missing.append(f"{discipline}_note_missing")
            continue

        note = note_map[discipline]

        # ✅ safe content validation (no strip crash)
        if not note.content:
            missing.append(f"{discipline}_note_empty")
            continue

        if isinstance(note.content, str):
            if note.content.strip() == "":
                missing.append(f"{discipline}_note_empty")

    return missing
