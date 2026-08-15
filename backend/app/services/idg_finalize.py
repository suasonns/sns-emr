# services/idg_finalize.py

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.idg_review import IDGReview
from app.services.idg_signature_validation import validate_required_signatures
from app.services.idg_signature_tasks import create_signature_tasks
from app.services.idg_enforcement import (
    validate_idg_ready_to_finalize,
)

def finalize_idg_review(
    db: Session,
    *,
    idg_review_id,
    finalized_by=None,
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

    if review.is_finalized:
        return {
            "success": False,
            "error": "ALREADY_FINALIZED",
        }

    try:
        # Enterprise compliance gate
        validate_idg_ready_to_finalize(
            db=db,
            idg_review_id=idg_review_id,
        )

        # Signature validation
        missing = validate_required_signatures(
            db=db,
            idg_review_id=idg_review_id,
        )

        if missing:
            create_signature_tasks(
                db=db,
                idg_review=review,
            )

            db.commit()

            return {
                "success": False,
                "error": "MISSING_REQUIRED_SIGNATURES",
                "missing_disciplines": missing,
            }

        review.is_finalized = True
        review.finalized_at = datetime.now(timezone.utc)

        if finalized_by:
            review.finalized_by = finalized_by

        db.commit()

        return {
            "success": True,
        }

    except Exception:
        db.rollback()
        raise

    
    