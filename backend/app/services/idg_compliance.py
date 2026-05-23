"""
Enterprise-grade IDG compliance evaluation.

Purpose:
- Determine whether patients are IDG compliant
- Based solely on IDGReview recency and completeness
"""

from datetime import date, timedelta
from sqlalchemy.orm import Session

from app.models.patient import Patient
from app.models.idg_review import IDGReview


IDG_LOOKBACK_DAYS = 15


def get_idg_compliance_summary(db: Session):
    """
    Returns compliance status for all active patients.
    """
    today = date.today()
    cutoff = today - timedelta(days=IDG_LOOKBACK_DAYS)

    patients = (
        db.query(Patient)
        .filter(Patient.status == "active")
        .all()
    )

    results = []

    for patient in patients:
        last_review = (
            db.query(IDGReview)
            .filter(IDGReview.patient_id == patient.id)
            .order_by(IDGReview.review_date.desc())
            .first()
        )

        compliant = (
            last_review is not None
            and last_review.review_date >= cutoff
        )

        results.append({
            "patient_id": str(patient.id),
            "last_idg_review_date": (
                last_review.review_date if last_review else None
            ),
            "compliant": compliant,
        })

    return results