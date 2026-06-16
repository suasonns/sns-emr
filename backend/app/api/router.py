from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID

# ✅ TENANT-SAFE DB
from app.db_request_dependency import get_db_tenant_with_request_state

# ✅ AUTH (DO NOT ACCEPT USER ID FROM REQUEST)
from app.core.security import get_current_user

from app.models.clinical_note import ClinicalNote
from app.services.clinical_note_service import (
    save_clinical_note,
    finalize_clinical_note,
)

router = APIRouter(prefix="/clinical-notes", tags=["Clinical Notes"])


# =========================================================
# SAVE NOTE (DRAFT)
# =========================================================

@router.post("/save")
def save_note(
    note_data: dict,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db_tenant_with_request_state),
):
    """
    Save draft note + run validation engine
    """

    note = ClinicalNote(**note_data)

    saved_note, result = save_clinical_note(
        db=db,
        note=note,
        user_id=current_user.id,
    )

    return {
        "note_id": str(saved_note.id),
        "warnings": result.warnings,
        "red_flags": result.red_flags,
        "incident_required": result.incident_required,
        "incident_status": result.incident_status,
    }


# =========================================================
# SIGN NOTE
# =========================================================

@router.post("/{note_id}/sign")
def sign_note(
    note_id: UUID,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db_tenant_with_request_state),
):
    """
    Finalize + sign clinical note
    """

    note = db.query(ClinicalNote).filter(ClinicalNote.id == note_id).first()

    if not note:
        raise HTTPException(status_code=404, detail="Note not found")

    # ✅ FINALIZE + VALIDATION + INCIDENT ENGINE
    updated_note, result = finalize_clinical_note(
        db=db,
        note=note,
        user_id=current_user.id,
    )

    return {
        "note_id": str(updated_note.id),
        "status": updated_note.status,
        "incident_required": updated_note.incident_required,
        "incident_status": updated_note.incident_status,
        "incident_id": str(updated_note.incident_id) if updated_note.incident_id else None,
        "warnings": result.warnings,
        "red_flags": result.red_flags,
    }