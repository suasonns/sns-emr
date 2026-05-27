from __future__ import annotations

from datetime import datetime, timezone
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.db_tenant_dependency import get_db_tenant
from app.core.security import get_current_user
from app.models.clinical_note import ClinicalNote
from app.models.visit import Visit
from app.models.amendment import Amendment
from app.services.audit_logger import log_event


router = APIRouter(prefix="/notes", tags=["notes"])


# ---------------------------------------------------------------------
# SCHEMAS
# ---------------------------------------------------------------------

class NoteCreateRequest(BaseModel):
    note_type: str = Field(..., example="RN_SUPERVISORY")
    content: str = Field(..., example="Patient seen for routine RN supervisory visit.")


class NoteUpdateRequest(BaseModel):
    content: str = Field(..., example="Updated draft note content.")


class NoteAmendRequest(BaseModel):
    reason: str = Field(..., example="Correction: clarified symptom description.")
    content: str = Field(..., example="Amendment content.")


# ---------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------

def _require_role(user_role: str, allowed: set[str]) -> None:
    if user_role.upper() not in allowed:
        raise HTTPException(status_code=403, detail="Forbidden")


# ---------------------------------------------------------------------
# CREATE NOTE
# ---------------------------------------------------------------------

@router.post(
    "/visits/{visit_id}",
    status_code=status.HTTP_201_CREATED,
    summary="Create draft clinical note",
)
def create_clinical_note(
    visit_id: uuid.UUID,
    payload: NoteCreateRequest,
    db: Session = Depends(get_db_tenant),
    user=Depends(get_current_user),
):
    role = (user.role or "").upper()

    _require_role(role, {"RN", "LVN", "NP", "MD", "ADMIN"})

    visit = db.query(Visit).filter(Visit.id == visit_id).first()
    if not visit:
        raise HTTPException(status_code=404, detail="Visit not found")

    note = ClinicalNote(
        visit_id=visit_id,
        author_id=user.id,
        note_type=payload.note_type.strip().upper(),
        content=payload.content,
        status="DRAFT",
        created_by=user.id,
        tenant_id=user.tenant_id,
    )

    db.add(note)
    db.flush()

    log_event(
        user_id=user.id,
        role=role,
        action="CREATE_NOTE",
        entity_type="clinical_note",
        entity_id=str(note.id),
        db=db,
    )

    db.commit()
    db.refresh(note)

    return {"note_id": str(note.id), "status": note.status}


# ---------------------------------------------------------------------
# UPDATE NOTE
# ---------------------------------------------------------------------

@router.put("/{note_id}", summary="Update draft clinical note")
def update_clinical_note(
    note_id: uuid.UUID,
    payload: NoteUpdateRequest,
    db: Session = Depends(get_db_tenant),
    user=Depends(get_current_user),
):
    role = (user.role or "").upper()
    _require_role(role, {"RN", "LVN", "NP", "MD", "ADMIN"})

    note = db.query(ClinicalNote).filter(ClinicalNote.id == note_id).first()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")

    if note.finalized_at is not None:
        raise HTTPException(
            status_code=400,
            detail="Finalized notes cannot be edited; use amendment",
        )

    note.content = payload.content
    db.flush()

    log_event(
        user_id=user.id,
        role=role,
        action="UPDATE_NOTE",
        entity_type="clinical_note",
        entity_id=str(note.id),
        db=db,
    )

    db.commit()
    db.refresh(note)

    return {"note_id": str(note.id), "status": note.status}


# ---------------------------------------------------------------------
# FINALIZE NOTE
# ---------------------------------------------------------------------

@router.post("/{note_id}/finalize", summary="Finalize clinical note")
def finalize_clinical_note(
    note_id: uuid.UUID,
    db: Session = Depends(get_db_tenant),
    user=Depends(get_current_user),
):
    role = (user.role or "").upper()
    _require_role(role, {"RN", "NP", "MD", "ADMIN"})

    note = db.query(ClinicalNote).filter(ClinicalNote.id == note_id).first()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")

    if note.finalized_at is not None:
        raise HTTPException(status_code=400, detail="Note already finalized")

    note.finalized_at = datetime.now(timezone.utc)
    note.finalized_by = user.id
    note.status = "FINALIZED"

    db.flush()

    log_event(
        user_id=user.id,
        role=role,
        action="FINALIZE_NOTE",
        entity_type="clinical_note",
        entity_id=str(note.id),
        db=db,
    )

    db.commit()
    db.refresh(note)

    return {
        "note_id": str(note.id),
        "status": note.status,
        "finalized_at": note.finalized_at.isoformat(),
    }


# ---------------------------------------------------------------------
# AMEND NOTE
# ---------------------------------------------------------------------

@router.post("/{note_id}/amend", summary="Amend a finalized clinical note")
def amend_clinical_note(
    note_id: uuid.UUID,
    payload: NoteAmendRequest,
    db: Session = Depends(get_db_tenant),
    user=Depends(get_current_user),
):
    role = (user.role or "").upper()
    _require_role(role, {"RN", "NP", "MD", "ADMIN"})

    note = db.query(ClinicalNote).filter(ClinicalNote.id == note_id).first()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")

    if note.finalized_at is None:
        raise HTTPException(status_code=400, detail="Only finalized notes can be amended")

    amendment = Amendment(
        clinical_note_id=note.id,
        author_id=user.id,
        created_by=user.id,
        reason=payload.reason.strip(),
        content=payload.content.strip(),
        original_finalized_at=note.finalized_at,
        tenant_id=user.tenant_id,
    )

    db.add(amendment)
    db.flush()

    log_event(
        user_id=user.id,
        role=role,
        action="AMEND_NOTE",
        entity_type="amendment",
        entity_id=str(amendment.id),
        db=db,
    )

    db.commit()
    db.refresh(amendment)

    return {"amendment_id": str(amendment.id), "note_id": str(note.id)}


# ---------------------------------------------------------------------
# LIST NOTES
# ---------------------------------------------------------------------

@router.get("/visits/{visit_id}", summary="List notes for a visit (read-only)")
def list_notes_for_visit(
    visit_id: uuid.UUID,
    db: Session = Depends(get_db_tenant),
    user=Depends(get_current_user),
):
    role = (user.role or "").upper()
    _require_role(role, {"RN", "LVN", "NP", "MD", "SURVEYOR", "ADMIN"})

    visit = db.query(Visit).filter(Visit.id == visit_id).first()
    if not visit:
        raise HTTPException(status_code=404, detail="Visit not found")

    notes = db.query(ClinicalNote).filter(ClinicalNote.visit_id == visit_id).all()

    return [
        {
            "note_id": str(n.id),
            "note_type": n.note_type,
            "status": n.status,
            "finalized_at": n.finalized_at.isoformat() if n.finalized_at else None,
        }
        for n in notes
    ]