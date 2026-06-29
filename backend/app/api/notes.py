from __future__ import annotations

from datetime import datetime, timezone
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db_tenant_dependency import get_db_tenant
from app.core.security import get_current_user
from app.models.clinical_note import ClinicalNote, ClinicalNoteVersion
from app.models.visit import Visit
from app.services.audit_logger import log_event


router = APIRouter(prefix="/notes", tags=["notes"])


# =========================================================
# POC INIT
# =========================================================

def _initialize_plan_of_care_updates(note: ClinicalNote) -> None:
    if note.plan_of_care_updates:
        return

    note.plan_of_care_updates = {
        "meta": {
            "version": "1.0",
            "generated_at": datetime.utcnow().isoformat(),
            "note_id": str(note.id),
            "patient_id": str(note.patient_id),
        },
        "pocs": []
    }


# =========================================================
# SCHEMAS
# =========================================================

class NoteCreateRequest(BaseModel):
    note_type: str
    content: str


class NoteUpdateRequest(BaseModel):
    content: str


class NoteAmendRequest(BaseModel):
    reason: str
    content: str


# =========================================================
# HELPERS
# =========================================================

def _require_role(user_role: str, allowed: set[str]) -> None:
    if (user_role or "").upper() not in allowed:
        raise HTTPException(status_code=403, detail="Forbidden")


def _get_visit_or_404(*, db: Session, visit_id: uuid.UUID, tenant_id: uuid.UUID) -> Visit:
    visit = (
        db.query(Visit)
        .filter(Visit.id == visit_id, Visit.tenant_id == tenant_id)
        .first()
    )
    if not visit:
        raise HTTPException(status_code=404, detail="Visit not found")
    return visit


def _get_note_or_404(*, db: Session, note_id: uuid.UUID, tenant_id: uuid.UUID, for_update: bool = False) -> ClinicalNote:
    query = db.query(ClinicalNote)

    if for_update:
        query = query.with_for_update()

    note = query.filter(
        ClinicalNote.id == note_id,
        ClinicalNote.tenant_id == tenant_id,
    ).first()

    if not note:
        raise HTTPException(status_code=404, detail="Note not found")

    return note


# =========================================================
# CREATE NOTE
# =========================================================

@router.post("/visits/{visit_id}", status_code=status.HTTP_201_CREATED)
def create_clinical_note(
    visit_id: uuid.UUID,
    payload: NoteCreateRequest,
    db: Session = Depends(get_db_tenant),
    user=Depends(get_current_user),
):
    role = (user.role or "").upper()

    _require_role(role, {"RN", "LVN", "NP", "MD", "SC", "MSW", "LCSW", "BSW", "ADMIN"})

    visit = _get_visit_or_404(db=db, visit_id=visit_id, tenant_id=user.tenant_id)

    now = datetime.utcnow()

    note = ClinicalNote(
        visit_id=visit_id,
        author_id=user.id,
        note_type=payload.note_type.strip().upper(),
        content=payload.content,
        status="DRAFT",
        created_by=user.id,
        created_at=now,
        updated_at=now,
        tenant_id=user.tenant_id,
        patient_id=getattr(visit, "patient_id", None),
        encounter_date=getattr(visit, "encounter_date", None),
        discipline=role,
    )

    # ✅ MODEL handles enforcement too → keep aligned
    if role == "BSW":
        note.requires_countersign = True

    _initialize_plan_of_care_updates(note)

    db.add(note)
    db.flush()

    version = ClinicalNoteVersion(
        clinical_note_id=note.id,
        version_number=1,
        content=payload.content,
        created_by=user.id,
    )

    db.add(version)
    note.current_version_id = version.id

    db.flush()

    log_event(
        user_id=user.id,
        role=role,
        action="CREATE_NOTE",
        entity_type="clinical_note",
        entity_id=str(note.id),
        db=db
    )

    db.commit()
    db.refresh(note)

    return {
        "note_id": str(note.id),
        "status": note.status,
    }


# =========================================================
# COUNTERSIGN
# =========================================================

@router.post("/{note_id}/countersign")
def countersign_note(
    note_id: uuid.UUID,
    db: Session = Depends(get_db_tenant),
    user=Depends(get_current_user),
):
    role = (user.role or "").upper()

    if role not in {"MSW", "LCSW"}:
        raise HTTPException(status_code=403, detail="Only MSW/LCSW allowed")

    note = _get_note_or_404(
        db=db,
        note_id=note_id,
        tenant_id=user.tenant_id,
        for_update=True,
    )

    # ✅ FAIL FAST (API layer protection)
    if note.finalized_at:
        raise HTTPException(status_code=400, detail="Cannot modify finalized note")

    if note.discipline != "BSW":
        raise HTTPException(status_code=400, detail="Not a BSW note")

    if note.countersigned_by:
        raise HTTPException(status_code=400, detail="Already countersigned")

    now = datetime.utcnow()

    note.countersigned_by = user.id
    note.countersigned_at = now
    note.updated_at = now

    db.flush()

    log_event(
        user_id=user.id,
        role=role,
        action="COUNTERSIGN_NOTE",
        entity_type="clinical_note",
        entity_id=str(note.id),
        db=db,
    )

    db.commit()

    return {"status": "COUNTERSIGNED"}


# =========================================================
# FINALIZE NOTE
# =========================================================

@router.post("/{note_id}/finalize")
def finalize_clinical_note(
    note_id: uuid.UUID,
    db: Session = Depends(get_db_tenant),
    user=Depends(get_current_user),
):
    role = (user.role or "").upper()

    _require_role(role, {"RN", "NP", "MD", "ADMIN", "SC", "MSW", "LCSW"})

    tenant_id = user.tenant_id

    note = _get_note_or_404(
        db=db,
        note_id=note_id,
        tenant_id=tenant_id,
        for_update=True,
    )

    if note.finalized_at:
        raise HTTPException(status_code=400, detail="Already finalized")

    if note.current_version_id is None:
        raise HTTPException(status_code=409, detail="No active version")

    # =========================================================
    # ✅ IDG COMPLETENESS VALIDATION (NEW)
    # =========================================================

    if not note.idg_review_id:
        raise HTTPException(status_code=400, detail="Missing IDG review")

    missing = validate_idg_completeness(
        db,
        idg_review_id=note.idg_review_id,
        tenant_id=tenant_id,
    )

    if missing:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "IDG_INCOMPLETE",
                "missing": missing,
            },
        )

    # =========================================================
    # ✅ SUPERVISION RULE
    # =========================================================

    if note.discipline == "BSW":
        if not note.requires_countersign:
            raise HTTPException(status_code=400, detail="Invalid supervision state")

        if not note.countersigned_by or not note.countersigned_at:
            raise HTTPException(status_code=400, detail="BSW requires countersign")

    now = datetime.utcnow()

    note.status = "FINALIZED"
    note.finalized_at = now
    note.finalized_by = user.id
    note.signed_by = user.id
    note.signed_at = now
    note.updated_at = now

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

    return {
        "note_id": str(note.id),
        "status": note.status,
    }