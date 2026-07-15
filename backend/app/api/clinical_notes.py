from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID

from app.db_request_dependency import get_db_tenant_with_request_state
from app.core.security import get_current_user

from app.models.clinical_note import ClinicalNote
from app.services.clinical_note_service import (
    save_clinical_note,
    finalize_clinical_note,
)

router = APIRouter(prefix="/clinical-notes", tags=["Clinical Notes"])


# =========================================================
# ✅ VALIDATION HELPER
# =========================================================

def _validate_note_payload(note_data: dict):
    required_fields = ["discipline", "form_type", "note_type"]

    missing = [f for f in required_fields if f not in note_data]

    if missing:
        raise HTTPException(
            status_code=422,
            detail=f"Missing required fields: {missing}"
        )

    if not note_data.get("care_level"):
        note_data["care_level"] = "ROUTINE"


# =========================================================
# SAVE NOTE (DRAFT)
# =========================================================

@router.post("/save")
def save_note(
    note_data: dict,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db_tenant_with_request_state),
):

    _validate_note_payload(note_data)

    try:
        form_type = note_data.pop("form_type")

        note = ClinicalNote(**note_data)

        setattr(note, "form_type", form_type)

        saved_note, result = save_clinical_note(
            db=db,
            note=note,
            user_id=current_user.id,
        )

        content = (
            saved_note.content
            if isinstance(saved_note.content, dict)
            else {}
        )

        validation = content.get("_validation", {})
        audit_flags = content.get("audit_flags", {})
        observed_data = content.get("observed_data", {})

        return {
            "note_id": str(saved_note.id),
            "form_key": saved_note.form_key,
            "form_family": saved_note.form_family,
            "care_level": saved_note.care_level,
            "clinical_context": observed_data,
            "audit_flags": audit_flags,
            "validation": validation,
            "warnings": validation.get("warnings", []),
            "red_flags": validation.get("red_flags", []),
            "incident_required": validation.get(
                "incident_required",
                False,
            ),
            "incident_status": validation.get(
                "incident_status",
                None,
            ),
            "finalization_allowed": validation.get(
                "finalization_allowed",
                True,
            ),
            "compliance_blocking_items": validation.get(
                "compliance_blocking_items",
                [],
            ),
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to save clinical note: {str(e)}"
        )


# =========================================================
# SIGN NOTE
# =========================================================

@router.post("/{note_id}/sign")
def sign_note(
    note_id: UUID,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db_tenant_with_request_state),
):

    note = db.query(ClinicalNote).filter(
        ClinicalNote.id == note_id
    ).first()

    if not note:
        raise HTTPException(status_code=404, detail="Note not found")

    updated_note, result = finalize_clinical_note(
        db=db,
        note=note,
        user_id=current_user.id,
    )

    content = (
        updated_note.content
        if isinstance(updated_note.content, dict)
        else {}
    )

    validation = content.get("_validation", {})
    audit_flags = content.get("audit_flags", {})

    return {
        "note_id": str(updated_note.id),
        "status": updated_note.status,
        "form_key": updated_note.form_key,
        "audit_flags": audit_flags,
        "validation": validation,
        "warnings": validation.get("warnings", []),
        "red_flags": validation.get("red_flags", []),
        "incident_required": validation.get(
            "incident_required",
            False,
        ),
        "incident_status": validation.get(
            "incident_status",
            None,
        ),
        "finalization_allowed": validation.get(
            "finalization_allowed",
            True,
        ),
            "compliance_blocking_items": validation.get(
            "compliance_blocking_items",
            [],
        ),
    }