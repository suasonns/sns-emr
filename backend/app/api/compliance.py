from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session, joinedload
from datetime import datetime, date, timedelta

from app.core.db import get_db
from app.core.permissions import require_roles
from app.core.security import CurrentUser

from app.models.idg_review import IDGReview
from app.models.visit import Visit
from app.models.clinical_note import ClinicalNote
from app.models.patient import Patient
from app.models.amendment import Amendment


router = APIRouter(prefix="/compliance", tags=["compliance"])


NOTE_COMPLETION_HOURS = 24
DRAFT_NOTE_WARNING_HOURS = 48


@router.get("/late-notes")
def late_notes_report(
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(
        require_roles(["RN", "NP", "MD", "Administrator", "DPCS"])
    ),
):
    cutoff = datetime.utcnow() - timedelta(hours=NOTE_COMPLETION_HOURS)

    visits = (
        db.query(Visit)
        .options(joinedload(Visit.notes))
        .filter(Visit.visit_datetime < cutoff)
        .all()
    )

    results = []

    for v in visits:
        if not v.notes:
            results.append({
                "visit_id": str(v.id),
                "patient_id": str(v.patient_id),
                "issue": "Missing note"
            })

    return results


@router.get("/draft-notes")
def draft_notes_report(
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(
        require_roles(["RN", "NP", "MD", "Administrator", "DPCS"])
    ),
):
    cutoff = datetime.utcnow() - timedelta(hours=DRAFT_NOTE_WARNING_HOURS)

    notes = (
        db.query(ClinicalNote)
        .filter(ClinicalNote.status == "draft")
        .filter(ClinicalNote.created_at < cutoff)
        .all()
    )

    return [
        {
            "note_id": str(n.id),
            "visit_id": str(n.visit_id),
            "created_at": n.created_at,
        }
        for n in notes
    ]


@router.get("/idg-trends")
def idg_compliance_trends(
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(
        require_roles(["RN", "NP", "MD", "Administrator", "DPCS"])
    ),
):
    today = date.today()
    trend = []

    active_patients = db.query(Patient).filter(Patient.status == "active").all()

    for days_ago in range(0, 60, 5):
        as_of = today - timedelta(days=days_ago)
        cutoff = as_of - timedelta(days=15)

        compliant = 0

        for p in active_patients:
            last_review = (
                db.query(IDGReview)
                .filter(IDGReview.patient_id == p.id)
                .filter(IDGReview.review_date <= as_of)
                .order_by(IDGReview.review_date.desc())
                .first()
            )

            if last_review and last_review.review_date >= cutoff:
                compliant += 1

        trend.append({
            "as_of": as_of,
            "total_active": len(active_patients),
            "compliant": compliant,
            "non_compliant": len(active_patients) - compliant,
        })

    return trend
