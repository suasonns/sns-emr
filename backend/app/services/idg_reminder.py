from __future__ import annotations

from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from uuid import UUID

from app.models.patient import Patient
from app.models.idg_review import IDGReview


IDG_LOOKBACK_DAYS = 15  # configurable


def get_idg_reminders(
    db: Session,
    *,
    tenant_id: UUID,
) -> list[dict]:
    """
    Enterprise-grade IDG reminder generator.

    Triggers reminders when:
    - No IDG review exists
    - IDG review not finalized
    - Missing POC linkage
    - Review is outdated
    """

    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(days=IDG_LOOKBACK_DAYS)

    reminders = []

    patients = (
        db.query(Patient)
        .filter(
            Patient.status == "active",
            Patient.tenant_id == tenant_id,
        )
        .all()
    )

    for p in patients:
        review = (
            db.query(IDGReview)
            .filter(
                IDGReview.patient_id == p.id,
                IDGReview.tenant_id == tenant_id,
            )
            .order_by(IDGReview.review_date.desc())
            .first()
        )

        reason = None

        if not review:
            reason = "NO_IDG_REVIEW"

        elif not review.is_finalized:
            reason = "NOT_FINALIZED"

        elif not review.plan_of_care_version_id:
            reason = "NO_POC_LINK"

        elif review.review_date < cutoff:
            reason = "OUTDATED"

        if reason:
            reminders.append(
                {
                    "patient_id": str(p.id),
                    "patient_name": p.full_name,
                    "last_review": review.review_date if review else None,
                    "reason": reason,
                }
            )

    return reminders