from __future__ import annotations

from datetime import datetime, timezone
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.clinical_note import ClinicalNote
from app.models.visit import Visit
from app.models.amendment import Amendment
from app.services.audit_logger import log_event


router = APIRouter(prefix="/notes", tags=["notes"])


class NoteCreateRequest(BaseModel):
    note_type: str = Field(..., example="RN_SUPERVISORY")
    content: str = Field(..., example="Patient seen for routine RN supervisory visit.")


class NoteUpdateRequest(BaseModel):
    content: str = Field(..., example="Updated draft note content.")


class NoteAmendRequest(BaseModel):
    reason: str = Field(..., example="Correction: clarified symptom description.")
    content: str = Field(..., example="Amendment content.")


def _set_db_context(db: Session, *, tenant_id: uuid.UUID, user_id: uuid.UUID) -> None:
    db.execute(text("SET LOCAL app.current_tenant = :tid"), {"tid": str(tenant_id)})
    db.execute(text("SELECT set_config('app.user_id', :uid, true)"), {"uid": str(user_id)})


def _require_role(user_role: str, allowed: set[str]) -> None:
    if user_role.upper() not in allowed:
        raise HTTPException(status_code=403, detail="Forbidden")


@router.post(
    "/visits/{visit_id}",
    status_code=status.HTTP_201_CREATED,
    summary="Create draft clinical note",
)
def create_clinical_note(
    visit_id: uuid.UUID,
    payload: NoteCreateRequest,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    tenant_id = getattr(user, "tenant_id", None)
    user_id = getattr(user, "user_id", None) or getattr(user, "id", None)
    role = str(getattr(user, "role", "") or "").upper()

    if not tenant_id or not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")

    _require_role(role, {"RN", "LVN", "NP", "MD", "ADMIN"})
    _set_db_context(db, tenant_id=tenant_id, user_id=user_id)

    visit = (
        db.query(Visit)
        .filter(Visit.id == visit_id, Visit.tenant_id == tenant_id)
        .first()
    )
    if not visit:
        raise HTTPException(status_code=404, detail="Visit not found")

    note = ClinicalNote(
        visit_id=visit_id,
        author_id=user_id,
        note_type=payload.note_type.strip().upper(),
        content=payload.content,
        status="draft",
    )

    if hasattr(note, "tenant_id"):
        setattr(note, "tenant_id", tenant_id)
    if hasattr(note, "created_by"):
        setattr(note, "created_by", user_id)

    db.add(note)
    db.flush()

    log_event(
        user_id=user_id,
        role=role,
        action="CREATE_NOTE",
        entity_type="clinical_note",
        entity_id=str(note.id),
        db=db,
    )

    db.commit()
    db.refresh(note)

    return {"note_id": str(note.id), "status": note.status}


@router.put("/{note_id}", summary="Update draft clinical note")
def update_clinical_note(
    note_id: uuid.UUID,
    payload: NoteUpdateRequest,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    tenant_id = getattr(user, "tenant_id", None)
    user_id = getattr(user, "user_id", None) or getattr(user, "id", None)
    role = str(getattr(user, "role", "") or "").upper()

    if not tenant_id or not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")

    _require_role(role, {"RN", "LVN", "NP", "MD", "ADMIN"})
    _set_db_context(db, tenant_id=tenant_id, user_id=user_id)

    q = db.query(ClinicalNote).filter(ClinicalNote.id == note_id)
    if hasattr(ClinicalNote, "tenant_id"):
        q = q.filter(ClinicalNote.tenant_id == tenant_id)
    note = q.first()

    if not note:
        raise HTTPException(status_code=404, detail="Note not found")

    if getattr(note, "finalized_at", None) is not None:
        raise HTTPException(status_code=400, detail="Finalized notes cannot be edited; use amendment")

    note.content = payload.content
    db.flush()

    log_event(
        user_id=user_id,
        role=role,
        action="UPDATE_NOTE",
        entity_type="clinical_note",
        entity_id=str(note.id),
        db=db,
    )

    db.commit()
    db.refresh(note)

    return {"note_id": str(note.id), "status": note.status}


@router.post("/{note_id}/finalize", summary="Finalize clinical note")
def finalize_clinical_note(
    note_id: uuid.UUID,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    tenant_id = getattr(user, "tenant_id", None)
    user_id = getattr(user, "user_id", None) or getattr(user, "id", None)
    role = str(getattr(user, "role", "") or "").upper()

    if not tenant_id or not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")

    _require_role(role, {"RN", "NP", "MD", "ADMIN"})
    _set_db_context(db, tenant_id=tenant_id, user_id=user_id)

    q = db.query(ClinicalNote).filter(ClinicalNote.id == note_id)
    if hasattr(ClinicalNote, "tenant_id"):
        q = q.filter(ClinicalNote.tenant_id == tenant_id)
    note = q.first()

    if not note:
        raise HTTPException(status_code=404, detail="Note not found")

    if hasattr(note, "finalize") and callable(getattr(note, "finalize")):
        note.finalize(finalized_by=user_id)
    else:
        if getattr(note, "finalized_at", None) is not None:
            raise HTTPException(status_code=400, detail="Note already finalized")
        if hasattr(note, "finalized_at"):
            setattr(note, "finalized_at", datetime.now(timezone.utc))
        if hasattr(note, "finalized_by"):
            setattr(note, "finalized_by", user_id)
        note.status = "finalized"

    db.flush()

    log_event(
        user_id=user_id,
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
        "finalized_at": str(getattr(note, "finalized_at", "")) if getattr(note, "finalized_at", None) else None,
    }


@router.post("/{note_id}/amend", summary="Amend a finalized clinical note")
def amend_clinical_note(
    note_id: uuid.UUID,
    payload: NoteAmendRequest,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    tenant_id = getattr(user, "tenant_id", None)
    user_id = getattr(user, "user_id", None) or getattr(user, "id", None)
    role = str(getattr(user, "role", "") or "").upper()

    if not tenant_id or not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")

    _require_role(role, {"RN", "NP", "MD", "ADMIN"})
    _set_db_context(db, tenant_id=tenant_id, user_id=user_id)

    q = db.query(ClinicalNote).filter(ClinicalNote.id == note_id)
    if hasattr(ClinicalNote, "tenant_id"):
        q = q.filter(ClinicalNote.tenant_id == tenant_id)
    note = q.first()

    if not note:
        raise HTTPException(status_code=404, detail="Note not found")

    if getattr(note, "finalized_at", None) is None:
        raise HTTPException(status_code=400, detail="Only finalized notes can be amended")

    amendment = Amendment(
        clinical_note_id=note.id,
        author_id=user_id,
        created_by=user_id,
        reason=payload.reason.strip(),
        content=payload.content.strip(),
        original_finalized_at=getattr(note, "finalized_at", None),
    )

    if hasattr(amendment, "tenant_id"):
        setattr(amendment, "tenant_id", tenant_id)

    db.add(amendment)
    db.flush()

    log_event(
        user_id=user_id,
        role=role,
        action="AMEND_NOTE",
        entity_type="amendment",
        entity_id=str(amendment.id),
        db=db,
    )

    db.commit()
    db.refresh(amendment)

    return {"amendment_id": str(amendment.id), "note_id": str(note.id)}


@router.get("/visits/{visit_id}", summary="List notes for a visit (read-only)")
def list_notes_for_visit(
    visit_id: uuid.UUID,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    tenant_id = getattr(user, "tenant_id", None)
    user_id = getattr(user, "user_id", None) or getattr(user, "id", None)
    role = str(getattr(user, "role", "") or "").upper()

    if not tenant_id or not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")

    _require_role(role, {"RN", "LVN", "NP", "MD", "SURVEYOR", "ADMIN"})
    _set_db_context(db, tenant_id=tenant_id, user_id=user_id)

    visit = (
        db.query(Visit)
        .filter(Visit.id == visit_id, Visit.tenant_id == tenant_id)
        .first()
    )
    if not visit:
        raise HTTPException(status_code=404, detail="Visit not found")

    q = db.query(ClinicalNote).filter(ClinicalNote.visit_id == visit_id)
    if hasattr(ClinicalNote, "tenant_id"):
        q = q.filter(ClinicalNote.tenant_id == tenant_id)

    notes = q.all()

    return [
        {
            "note_id": str(n.id),
            "note_type": getattr(n, "note_type", None),
            "status": getattr(n, "status", None),
            "finalized_at": str(getattr(n, "finalized_at", "")) if getattr(n, "finalized_at", None) else None,
        }
        for n in notes
    ]