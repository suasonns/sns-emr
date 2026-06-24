# app/api/clinical_notes/router.py

from __future__ import annotations

from uuid import UUID
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db_request_dependency import get_db_tenant_with_request_state

from app.models.clinical_note import ClinicalNote
from app.models.visit import Visit

from app.services.clinical_note_service import (
    save_clinical_note,
    finalize_clinical_note,
)

from app.services.poc_review_gate import (
    POCReviewGateError,
    review_poc,
)

router = APIRouter(prefix="/clinical-notes", tags=["Clinical Notes"])


# =========================================================
# HELPERS
# =========================================================

def _utcnow_naive() -> datetime:
    return datetime.utcnow()


def _get_visit_or_404(db: Session, visit_id: UUID, tenant_id: UUID) -> Visit:
    visit = (
        db.query(Visit)
        .filter(
            Visit.id == visit_id,
            Visit.tenant_id == tenant_id,
        )
        .first()
    )
    if not visit:
        raise HTTPException(status_code=404, detail="Visit not found")
    return visit


def _get_note_or_404(db: Session, note_id: UUID, tenant_id: UUID) -> ClinicalNote:
    note = (
        db.query(ClinicalNote)
        .filter(
            ClinicalNote.id == note_id,
            ClinicalNote.tenant_id == tenant_id,
        )
        .first()
    )
    if not note:
        raise HTTPException(status_code=404, detail="Clinical note not found")
    return note


# =========================================================
# CREATE NOTE (NO DOUBLE COMMIT)
# =========================================================

@router.post("/")
def create_clinical_note(
    payload: dict,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db_tenant_with_request_state),
):
    try:
        visit_id_raw = payload.get("visit_id")
        if not visit_id_raw:
            raise HTTPException(status_code=400, detail="visit_id is required")

        visit_id = UUID(str(visit_id_raw))
        visit = _get_visit_or_404(db, visit_id, current_user.tenant_id)

        note = ClinicalNote()
        now = _utcnow_naive()

        # Required input
        note.visit_id = visit.id
        note.note_type = str(payload.get("note_type") or "").strip().upper()
        note.content = str(payload.get("content") or "").strip()

        if not note.note_type:
            raise HTTPException(status_code=400, detail="note_type is required")
        if not note.content:
            raise HTTPException(status_code=400, detail="content is required")

        # System fields
        note.tenant_id = current_user.tenant_id
        note.author_id = current_user.id
        note.created_by = current_user.id
        note.created_at = now
        note.updated_at = now
        note.status = "DRAFT"

        # Visit-derived
        note.patient_id = visit.patient_id
        note.care_level = getattr(visit, "care_level", None) or "ROUTINE"
        note.visit_type = getattr(visit, "visit_type", None) or "RN"
        note.visit_origin = getattr(visit, "visit_origin", None) or "SCHEDULED"
        note.note_category = getattr(visit, "note_category", None)
        note.encounter_type = getattr(visit, "encounter_type", None) or "ROUTINE"
        note.discipline = getattr(visit, "discipline", None) or "RN"
        note.encounter_date = getattr(visit, "encounter_date", None)

        note, validation = save_clinical_note(
            db=db,
            note=note,
            user_id=current_user.id,
        )

        # ✅ DO NOT COMMIT AGAIN

        return {
            "note_id": str(note.id),
            "validation": validation,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# =========================================================
# REVIEW POC (STRICT + SAFE)
# =========================================================

@router.post("/{note_id}/pocs/{poc_id}/review")
def review_generated_poc(
    note_id: UUID,
    poc_id: str,
    payload: dict,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db_tenant_with_request_state),
):
    try:
        note = _get_note_or_404(db, note_id, current_user.tenant_id)

        decision = str(payload.get("decision") or "").strip().upper()
        comment = payload.get("comment")

        if decision not in {"ACCEPT", "DISMISS", "MODIFY"}:
            raise HTTPException(
                status_code=400,
                detail="decision must be ACCEPT, DISMISS, or MODIFY",
            )

        updated_poc = review_poc(
            note=note,
            poc_id=poc_id,
            reviewer_user_id=current_user.id,
            decision=decision,
            comment=comment,
        )

        db.add(note)
        db.commit()
        db.refresh(note)

        return {
            "note_id": str(note.id),
            "poc_id": poc_id,
            "decision": decision,
            "status": updated_poc.get("status"),
            "reviewed": updated_poc.get("review", {}).get("reviewed"),
            "poc": updated_poc,
        }

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# =========================================================
# FINALIZE NOTE (NO EXTRA COMMIT)
# =========================================================

@router.post("/{note_id}/finalize")
def finalize_note(
    note_id: UUID,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db_tenant_with_request_state),
):
    try:
        note = _get_note_or_404(db, note_id, current_user.tenant_id)

        note, validation = finalize_clinical_note(
            db=db,
            note=note,
            user_id=current_user.id,
        )

        return {
            "note_id": str(note.id),
            "status": "FINALIZED",
            "validation": validation,
        }

    except POCReviewGateError as e:
        raise HTTPException(
            status_code=409,
            detail={
                "message": e.message,
                "blocking_pocs": e.blocking_pocs,
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# =========================================================
# READ ONLY
# =========================================================

@router.get("/{note_id}")
def get_clinical_note(
    note_id: UUID,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db_tenant_with_request_state),
):
    return _get_note_or_404(db, note_id, current_user.tenant_id)


@router.get("/")
def list_clinical_notes(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db_tenant_with_request_state),
):
    return (
        db.query(ClinicalNote)
        .filter(ClinicalNote.tenant_id == current_user.tenant_id)
        .order_by(ClinicalNote.created_at.desc())
        .limit(50)
        .all()
    )