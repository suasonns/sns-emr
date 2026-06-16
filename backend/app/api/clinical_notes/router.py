# app/api/clinical_notes/router.py

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db_request_dependency import get_db_tenant_with_request_state

from app.models.clinical_note import ClinicalNote
from app.services.clinical_note_service import (
    save_clinical_note,
    finalize_clinical_note,
)

router = APIRouter(prefix="/clinical-notes", tags=["Clinical Notes"])


# =========================================================
# ✅ CREATE / SAVE NOTE (DRAFT)
# =========================================================

@router.post("/")
def create_clinical_note(
    payload: dict,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db_tenant_with_request_state),
):
    """
    Create and save a clinical note draft.
    """

    try:
        note = ClinicalNote(
            **payload,
            tenant_id=current_user.tenant_id,
        )

        note, validation = save_clinical_note(
            db=db,
            note=note,
            user_id=current_user.id,
        )

        return {
            "note_id": str(note.id),
            "validation": validation,
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# =========================================================
# ✅ FINALIZE (SIGN NOTE)
# =========================================================

@router.post("/{note_id}/finalize")
def finalize_note(
    note_id: UUID,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db_tenant_with_request_state),
):
    """
    Finalize (sign) a clinical note.
    """

    note = (
        db.query(ClinicalNote)
        .filter(
            ClinicalNote.id == note_id,
            ClinicalNote.tenant_id == current_user.tenant_id,
        )
        .first()
    )

    if not note:
        raise HTTPException(status_code=404, detail="Clinical note not found")

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


# =========================================================
# ✅ GET NOTE
# =========================================================

@router.get("/{note_id}")
def get_clinical_note(
    note_id: UUID,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db_tenant_with_request_state),
):
    """
    Retrieve a clinical note.
    """

    note = (
        db.query(ClinicalNote)
        .filter(
            ClinicalNote.id == note_id,
            ClinicalNote.tenant_id == current_user.tenant_id,
        )
        .first()
    )

    if not note:
        raise HTTPException(status_code=404, detail="Clinical note not found")

    return note


# =========================================================
# ✅ LIST NOTES (OPTIONAL)
# =========================================================

@router.get("/")
def list_clinical_notes(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db_tenant_with_request_state),
):
    """
    List notes for tenant (basic view).
    """

    notes = (
        db.query(ClinicalNote)
        .filter(ClinicalNote.tenant_id == current_user.tenant_id)
        .order_by(ClinicalNote.created_at.desc())
        .limit(50)
        .all()
    )

    return notes