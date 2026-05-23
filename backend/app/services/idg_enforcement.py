"""
Enterprise-grade IDG completion enforcement.

Purpose:
- Enforce CMS CoPs §418.56 IDG completeness rules
- Validate readiness to finalize an IDGReview
- NO meeting-based logic
"""

from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.models.idg_review import IDGReview
from app.models.idg_note import IDGNote
from app.models.idg_md_attestation import IDGMDAttestation


REQUIRED_NOTE_DISCIPLINES = {"RN", "MSW", "SC"}


def _normalize(discipline: str) -> str:
    return discipline.strip().upper() if discipline else ""


def validate_idg_ready_to_finalize(
    db: Session,
    *,
    idg_review_id,
) -> None:
    """
    Raises HTTPException if IDGReview cannot be finalized.
    """

    review = (
        db.query(IDGReview)
        .filter(IDGReview.id == idg_review_id)
        .first()
    )

    if not review:
        raise HTTPException(
            status_code=404,
            detail="IDG review not found",
        )

    # ------------------------------------------------------------------
    # 1) Required discipline notes must exist and be signed
    # ------------------------------------------------------------------
    notes = (
        db.query(IDGNote)
        .filter(IDGNote.idg_review_id == review.id)
        .all()
    )

    signed_disciplines = {
        _normalize(n.discipline)
        for n in notes
        if n.signed_at is not None
    }

    missing = REQUIRED_NOTE_DISCIPLINES - signed_disciplines

    if missing:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot finalize IDG. Missing signed notes from: {sorted(missing)}",
        )

    # ------------------------------------------------------------------
    # 2) MD attestation must exist and be signed
    # ------------------------------------------------------------------
    attestation = (
        db.query(IDGMDAttestation)
        .filter(IDGMDAttestation.idg_review_id == review.id)
        .first()
    )

    if not attestation:
        raise HTTPException(
            status_code=400,
            detail="Cannot finalize IDG. Missing MD attestation.",
        )

    if hasattr(attestation, "signed_at") and attestation.signed_at is None:
        raise HTTPException(
            status_code=400,
            detail="Cannot finalize IDG. MD attestation not signed.",
        )