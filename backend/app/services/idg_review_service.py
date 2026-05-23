"""
Enterprise-grade IDG review lifecycle service.

Replaces legacy meeting-based logic.

Authoritative entity:
- IDGReview (CMS CoPs §418.56)
"""

from datetime import date
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.models.idg_review import IDGReview
from app.services.idg_enforcement import validate_idg_ready_to_finalize


def create_idg_review(
    db: Session,
    *,
    patient_id,
    benefit_period_id,
    review_date: date,
    summary: str,
    poc_action: str,
    created_by: str | None = None,
) -> IDGReview:
    review = IDGReview(
        patient_id=patient_id,
        benefit_period_id=benefit_period_id,
        review_date=review_date,
        summary=summary,
        poc_action=poc_action,
        created_by=created_by,
    )
    db.add(review)
    db.commit()
    db.refresh(review)
    return review


def finalize_idg_review(
    db: Session,
    *,
    idg_review_id,
    finalized_by: str | None = None,
) -> IDGReview:
    review = (
        db.query(IDGReview)
        .filter(IDGReview.id == idg_review_id)
        .first()
    )

    if not review:
        raise HTTPException(status_code=404, detail="IDG review not found")

    if review.is_finalized:
        raise HTTPException(status_code=400, detail="IDG review already finalized")

    validate_idg_ready_to_finalize(db, idg_review_id=idg_review_id)

    review.is_finalized = True
    review.finalized_by = finalized_by
    review.finalized_at = date.today()

    db.commit()
    db.refresh(review)
    return review