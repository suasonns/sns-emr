# services/idg_enforcement.py

"""
Enterprise-grade IDG finalization enforcement.

Purpose:
- Enforce CMS CoPs §418.56 IDG completeness requirements
- Ensure interdisciplinary documentation integrity
- Prevent IDG finalization with unresolved discrepancies
"""

from sqlalchemy.orm import Session
from sqlalchemy import text
from fastapi import HTTPException

from app.models.idg_review import IDGReview
from app.models.idg_note import IDGNote
from app.models.idg_md_attestation import IDGMDAttestation
from app.services.tenant_settings_service import TenantSettingsService

# ---------------------------------------------------------------------
# Default policy fallback
# ---------------------------------------------------------------------

DEFAULT_REQUIRED_NOTE_DISCIPLINES = {
    "RN",
    "MSW",
    "SC",
}


# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------

def _normalize(discipline: str) -> str:
    return discipline.strip().upper() if discipline else ""


# ---------------------------------------------------------------------
# Core Enforcement Entry Point
# ---------------------------------------------------------------------

def validate_idg_ready_to_finalize(
    db: Session,
    *,
    idg_review_id: str,
) -> None:
    """
    Raises HTTPException if the IDGReview cannot be finalized.
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
    # Prevent re-finalization
    # -------------------------------------------------------------
    if review.is_finalized:
        raise HTTPException(
            status_code=400,
            detail="IDG review already finalized.",
        )

    # -------------------------------------------------------------
    # CRITICAL: Must be linked to Plan of Care
    # -------------------------------------------------------------
    if not review.plan_of_care_version_id:
        raise HTTPException(
            status_code=400,
            detail="IDG must be linked to a Plan of Care before finalization.",
        )

    # -------------------------------------------------------------
    # 1) Required discipline notes must exist AND be signed
    # -------------------------------------------------------------
    notes = (
        db.query(IDGNote)
        .filter(IDGNote.idg_review_id == review.id)
        .all()
    )

    documented_disciplines: set[str] = set()

    for note in notes:
        if not note.note or not note.note.strip():
            continue

        documented_disciplines.add(_normalize(note.discipline))

    try:
        required_disciplines = (
            TenantSettingsService.get_idg_required_note_disciplines(
                db=db,
                tenant_id=review.tenant_id,
                review_type=getattr(review, "review_type", None),
            )
        )
    except Exception:
        required_disciplines = DEFAULT_REQUIRED_NOTE_DISCIPLINES

    missing = required_disciplines - documented_disciplines

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

    if not getattr(attestation, "attested", False):
        raise HTTPException(
            status_code=400,
            detail="Cannot finalize IDG. MD attestation is not complete.",
        )

    if getattr(attestation, "attested_at", None) is None:
        raise HTTPException(
            status_code=400,
            detail="Cannot finalize IDG. MD attestation timestamp is missing.",
        )

    # -------------------------------------------------------------
    # 3) HARD STOP — unresolved discrepancies
    # -------------------------------------------------------------
    _enforce_idg_discrepancy_gate(
        db=db,
        patient_id=review.patient_id,
        tenant_id=review.tenant_id,
    )


# ---------------------------------------------------------------------
# Discrepancy Gate (HARD STOP)
# ---------------------------------------------------------------------

def _enforce_idg_discrepancy_gate(
    *,
    db: Session,
    patient_id: str,
    tenant_id: str,
) -> None:
    """
    Blocks IDG finalization if unresolved discrepancies exist.
    """

    exists = db.execute(
        text(
            """
            SELECT 1
            FROM assessment_discrepancies
            WHERE patient_id = :pid
              AND tenant_id = :tid
              AND resolved = false
            LIMIT 1
            """
        ),
        {"pid": patient_id, "tid": tenant_id},
    ).first()

    if exists:
        raise HTTPException(
            status_code=409,
            detail=(
                "Unresolved interdisciplinary assessment discrepancies "
                "must be reconciled before IDG finalization."
            ),
        )