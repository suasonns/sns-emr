from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from datetime import datetime, date, timedelta

from app.core.db_session import get_db
from app.core.permissions import require_roles
from app.core.auth import CurrentUser

from app.models.idg_review import IDGReview
from app.models.visit import Visit
from app.models.clinical_note import ClinicalNote
from app.models.patient import Patient
from app.models.amendment import Amendment
from app.services.idg_pdf import generate_idg_report_pdf

router = APIRouter(prefix="/compliance", tags=["compliance"])

NOTE_COMPLETION_HOURS = 24
DRAFT_NOTE_WARNING_HOURS = 48


@router.get("/late-notes", summary="Visits with late or missing clinical notes")
def late_notes_report(
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_roles(["RN", "NP", "MD", "Administrator"])),
):
    cutoff = datetime.utcnow() - timedelta(hours=NOTE_COMPLETION_HOURS)

    visits = (
        db.query(Visit)
        .filter(Visit.visit_datetime < cutoff)
        .all()
    )

    results = []

    for v in visits:
        note = (
            db.query(ClinicalNote)
            .filter(ClinicalNote.visit_id == v.id)
            .filter(ClinicalNote.status == "finalized")
            .first()
        )

        if not note:
            results.append({
                "visit_id": str(v.id),
                "patient_id": str(v.patient_id),
                "visit_datetime": v.visit_datetime,
                "issue": "Missing or late note",
            })

    return results


@router.get("/draft-notes", summary="Stale draft clinical notes")
def draft_notes_report(
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_roles(["RN", "NP", "MD", "Administrator"])),
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
            "status": n.status,
        }
        for n in notes
    ]


@router.get("/missing-visit-notes", summary="Visits with no clinical notes")
def visits_without_notes(
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_roles(["RN", "NP", "MD", "Administrator"])),
):
    visits = db.query(Visit).all()
    results = []

    for v in visits:
        has_note = (
            db.query(ClinicalNote)
            .filter(ClinicalNote.visit_id == v.id)
            .first()
        )

        if not has_note:
            results.append({
                "visit_id": str(v.id),
                "patient_id": str(v.patient_id),
                "visit_datetime": v.visit_datetime,
            })

    return results


@router.get("/amendments", summary="Amendment audit summary")
def amendment_activity(
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_roles(["RN", "NP", "MD", "Administrator"])),
):
    amendments = db.query(Amendment).all()

    return [
        {
            "amendment_id": str(a.id),
            "clinical_note_id": str(a.clinical_note_id),
            "created_at": a.created_at,
            "reason": a.reason,
        }
        for a in amendments
    ]


@router.get("/discharged-open-items", summary="Discharged patients with open documentation")
def discharged_open_items(
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_roles(["RN", "NP", "MD", "Administrator"])),
):
    patients = (
        db.query(Patient)
        .filter(Patient.status == "discharged")
        .all()
    )

    issues = []

    for p in patients:
        drafts = (
            db.query(ClinicalNote)
            .join(Visit, ClinicalNote.visit_id == Visit.id)
            .filter(Visit.patient_id == p.id)
            .filter(ClinicalNote.status != "finalized")
            .all()
        )

        if drafts:
            issues.append({
                "patient_id": str(p.id),
                "open_draft_notes": len(drafts),
            })

    return issues


@router.get("/idg-trends", summary="15-day rolling IDG compliance trends")
def idg_compliance_trends(
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_roles(["RN", "NP", "MD", "Administrator"])),
):
    today = date.today()
    trend = []

    for days_ago in range(0, 60, 5):
        as_of = today - timedelta(days=days_ago)
        cutoff = as_of - timedelta(days=15)

        active_patients = (
            db.query(Patient)
            .filter(Patient.status == "active")
            .all()
        )

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


