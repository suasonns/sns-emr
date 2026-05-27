"""
Enterprise-grade IDG finalization enforcement.

Purpose:
- Enforce CMS CoPs §418.56 IDG completeness requirements
- Ensure interdisciplinary documentation integrity
- Prevent IDG finalization with unresolved discrepancies
- NO meeting-based logic (assessment-driven only)
"""

from sqlalchemy.orm import Session
from sqlalchemy import text
from fastapi import HTTPException

from app.models.idg_review import IDGReview
from app.models.idg_note import IDGNote
from app.models.idg_md_attestation import IDGMDAttestation


# ---------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------

REQUIRED_NOTE_DISCIPLINES = {"RN", "MSW", "SC"}


# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------

def _normalize(discipline: str) -> str:
    return discipline.strip().upper() if discipline else ""


# ---------------------------------------------------------------------
# Core Enforcement Entry Point (AUTHORITATIVE)
# ---------------------------------------------------------------------

def validate_idg_ready_to_finalize(
    db: Session,
    *,
    idg_review_id: str,
) -> None:
    """
    Raises HTTPException if the IDGReview cannot be finalized.
    This is the SINGLE authoritative enforcement gate.
    """

    # -------------------------------------------------------------
    # Load IDG review
    # -------------------------------------------------------------
    review = (
        db.query(IDGReview)
        .filter(IDGReview.id == idg_review_id)
        .first()
    )

    if not review:
        raise HTTPException(
            status_code=404,
            detail="IDG review not found.",
        )

    # -------------------------------------------------------------
    # 1) Required discipline notes must exist AND be signed
    # -------------------------------------------------------------
    notes = (
        db.query(IDGNote)
        .filter(IDGNote.idg_review_id == review.id)
        .all()
    )

    signed_disciplines = {
        _normalize(note.discipline)
        for note in notes
        if note.signed_at is not None
    }

    missing = REQUIRED_NOTE_DISCIPLINES - signed_disciplines

    if missing:
        raise HTTPException(
            status_code=400,
            detail=(
                "Cannot finalize IDG. Missing signed notes from disciplines: "
                f"{sorted(missing)}"
            ),
        )

    # -------------------------------------------------------------
    # 2) MD attestation must exist AND be signed
    # -------------------------------------------------------------
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

    if getattr(attestation, "signed_at", None) is None:
        raise HTTPException(
            status_code=400,
            detail="Cannot finalize IDG. MD attestation is not signed.",
        )

    # -------------------------------------------------------------
    # 3) HARD STOP — unresolved interdisciplinary discrepancies
    # -------------------------------------------------------------
    _enforce_idg_discrepancy_gate(
        db=db,
        patient_id=review.patient_id,
    )


# ---------------------------------------------------------------------
# Discrepancy Gate (IDG HARD STOP)
# ---------------------------------------------------------------------

def _enforce_idg_discrepancy_gate(
    *,
    db: Session,
    patient_id: str,
) -> None:
    """
    Blocks IDG finalization if unresolved assessment discrepancies exist.
    """

    exists = db.execute(
        text(
            """
            SELECT 1
            FROM assessment_discrepancies
            WHERE patient_id = :pid
              AND resolved = false
            LIMIT 1
            """
        ),
        {"pid": patient_id},
    ).first()

    if exists:
        raise HTTPException(
            status_code=409,
            detail=(
                "Unresolved interdisciplinary assessment discrepancies "
                "must be reconciled before IDG finalization."
            ),
        )