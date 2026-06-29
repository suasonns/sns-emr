from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.idg_review import IDGReview
from app.services.idg_signature_validation import validate_required_signatures
from app.services.idg_signature_tasks import create_signature_tasks


def finalize_idg_review(
    db: Session,
    *,
    idg_review_id,
    finalized_by=None,  # ✅ optional user tracking
):

    review = (
        db.query(IDGReview)
        .filter(IDGReview.id == idg_review_id)
        .first()
    )

    if not review:
        return {
            "success": False,
            "error": "IDG_REVIEW_NOT_FOUND",
        }

    # =====================================================
    # ✅ IDENTITY / IDEMPOTENCY CHECK
    # =====================================================

    if review.is_finalized:
        return {
            "success": False,
            "error": "ALREADY_FINALIZED",
        }

    # =====================================================
    # ✅ SIGNATURE VALIDATION
    # =====================================================

    missing = validate_required_signatures(
        db=db,
        idg_review_id=idg_review_id,
    )

    # =====================================================
    # ✅ BLOCK + CREATE TASKS
    # =====================================================

    if missing:

        # ✅ CREATE REMEDIATION TASKS
        create_signature_tasks(
            db=db,
            idg_review=review,
        )

        return {
            "success": False,
            "error": "MISSING_REQUIRED_SIGNATURES",
            "missing_disciplines": missing,
        }

    # =====================================================
    # ✅ FINALIZE
    # =====================================================

    review.is_finalized = True
    review.finalized_at = datetime.now(timezone.utc)

    if finalized_by:
        review.finalized_by = finalized_by

    # =====================================================
    # ✅ COMMIT (CRITICAL)
    # =====================================================

    db.commit()

    return {
        "success": True,
    }