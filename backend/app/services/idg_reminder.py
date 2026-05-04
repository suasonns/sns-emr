from datetime import date, timedelta
from sqlalchemy.orm import Session
from app.models.patient import Patient
from app.models.idg_review import IDGReview

def get_idg_reminders(db: Session):
    cutoff = date.today() - timedelta(days=15)

    reminders = []

    patients = (
        db.query(Patient)
        .filter(Patient.status == "active")
        .all()
    )

    for p in patients:
        last_review = (
            db.query(IDGReview)
            .filter(IDGReview.patient_id == p.id)
            .order_by(IDGReview.review_date.desc())
            .first()
        )

        if not last_review or last_review.review_date < cutoff:
            reminders.append({
                "patient_id": str(p.id),
                "patient_name": p.full_name,
                "last_review": (
                    last_review.review_date if last_review else None
                ),
            })

    return reminders
