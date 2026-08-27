from __future__ import annotations

from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy import and_
from sqlalchemy.orm import Session, aliased

from app.billing.security import require_automated_billing
from app.core.database import get_db
from app.core.security import get_current_user
from app.core.tenant_scope import resolve_billing_scope_tenant_id
from app.models.clinical_note import ClinicalNote
from app.models.patient import Patient
from app.models.patient_facesheet import PatientFaceSheet
from app.models.user import User
from app.models.visit import Visit

router = APIRouter(prefix="/billing", tags=["Billing Visits & Notes"])


def _patient_name(first_name: str | None, middle_name: str | None, last_name: str | None) -> str | None:
    parts = [p for p in (first_name, middle_name, last_name) if p]
    return " ".join(parts) if parts else None


@router.get("/visits-notes")
def list_visits_notes(
    patient_id: str | None = None,
    encounter_date_from: date | None = None,
    encounter_date_to: date | None = None,
    note_type: str | None = None,
    discipline: str | None = None,
    status: str | None = None,
    unsigned_only: bool = Query(
        False,
        description="Only return notes with no signed_by/finalized_at -- documentation gaps that block billing.",
    ),
    limit: int = Query(200, le=1000),
    tenant_id: UUID | None = Query(
        None, description="Agency tenant to view. Required for billing-department accounts, which must explicitly pick an agency."
    ),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """
    Tenant-scoped, read-only view over real ``clinical_notes`` rows, joined to
    the visit they document and the patient/author identities, so billers can
    see documentation status (signed/finalized/countersigned) directly tied
    to the visits that feed billing -- without exposing raw clinical note
    content (``content`` / ``raw_transcript`` are never returned here).
    """
    scoped_tenant_id = str(resolve_billing_scope_tenant_id(db, user, tenant_id))
    require_automated_billing(db, scoped_tenant_id)

    Author = aliased(User)
    Countersigner = aliased(User)

    query = (
        db.query(
            ClinicalNote.id.label("note_id"),
            ClinicalNote.patient_id.label("patient_id"),
            ClinicalNote.visit_id.label("visit_id"),
            ClinicalNote.note_type.label("note_type"),
            ClinicalNote.discipline.label("discipline"),
            ClinicalNote.status.label("status"),
            ClinicalNote.encounter_date.label("encounter_date"),
            ClinicalNote.entered_at.label("entered_at"),
            ClinicalNote.finalized_at.label("finalized_at"),
            ClinicalNote.signed_by.label("signed_by"),
            ClinicalNote.signed_at.label("signed_at"),
            ClinicalNote.requires_countersign.label("requires_countersign"),
            ClinicalNote.countersigned_by.label("countersigned_by"),
            ClinicalNote.countersigned_at.label("countersigned_at"),
            ClinicalNote.is_late_entry.label("is_late_entry"),
            Visit.visit_datetime.label("visit_datetime"),
            Visit.visit_type.label("visit_type"),
            Visit.status.label("visit_status"),
            PatientFaceSheet.first_name.label("patient_first_name"),
            PatientFaceSheet.middle_name.label("patient_middle_name"),
            PatientFaceSheet.last_name.label("patient_last_name"),
            Patient.mrn.label("mrn"),
            Author.full_name.label("author_name"),
            Countersigner.full_name.label("countersigner_name"),
        )
        .join(Visit, Visit.id == ClinicalNote.visit_id)
        .join(Patient, Patient.id == ClinicalNote.patient_id)
        .outerjoin(PatientFaceSheet, PatientFaceSheet.patient_id == Patient.id)
        .outerjoin(Author, Author.id == ClinicalNote.author_id)
        .outerjoin(Countersigner, Countersigner.id == ClinicalNote.countersigned_by)
        .filter(ClinicalNote.tenant_id == scoped_tenant_id)
    )

    if patient_id:
        query = query.filter(ClinicalNote.patient_id == patient_id)
    if encounter_date_from:
        query = query.filter(ClinicalNote.encounter_date >= encounter_date_from)
    if encounter_date_to:
        query = query.filter(ClinicalNote.encounter_date <= encounter_date_to)
    if note_type:
        query = query.filter(ClinicalNote.note_type == note_type)
    if discipline:
        query = query.filter(ClinicalNote.discipline == discipline.upper())
    if status:
        query = query.filter(ClinicalNote.status == status.upper())
    if unsigned_only:
        query = query.filter(
            and_(ClinicalNote.signed_by.is_(None), ClinicalNote.finalized_at.is_(None))
        )

    rows = (
        query.order_by(ClinicalNote.encounter_date.desc().nullslast(), ClinicalNote.entered_at.desc())
        .limit(limit)
        .all()
    )

    results = []
    for r in rows:
        results.append(
            {
                "note_id": str(r.note_id),
                "patient_id": str(r.patient_id) if r.patient_id else None,
                "patient_name": _patient_name(
                    r.patient_first_name, r.patient_middle_name, r.patient_last_name
                ),
                "mrn": r.mrn,
                "visit_id": str(r.visit_id) if r.visit_id else None,
                "visit_datetime": r.visit_datetime.isoformat() if r.visit_datetime else None,
                "visit_type": r.visit_type,
                "visit_status": r.visit_status,
                "note_type": r.note_type,
                "discipline": r.discipline,
                "status": r.status,
                "encounter_date": r.encounter_date.isoformat() if r.encounter_date else None,
                "entered_at": r.entered_at.isoformat() if r.entered_at else None,
                "author_name": r.author_name,
                "signed_by": str(r.signed_by) if r.signed_by else None,
                "signed_at": r.signed_at.isoformat() if r.signed_at else None,
                "finalized_at": r.finalized_at.isoformat() if r.finalized_at else None,
                "requires_countersign": bool(r.requires_countersign),
                "countersigned_by": str(r.countersigned_by) if r.countersigned_by else None,
                "countersigner_name": r.countersigner_name,
                "countersigned_at": r.countersigned_at.isoformat() if r.countersigned_at else None,
                "is_late_entry": bool(r.is_late_entry),
                "documentation_complete": bool(r.finalized_at)
                and (not r.requires_countersign or bool(r.countersigned_by)),
            }
        )

    return {
        "tenant_id": scoped_tenant_id,
        "count": len(results),
        "visits_notes": results,
    }
