from __future__ import annotations

from datetime import datetime, timezone, timedelta
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session, joinedload

from app.db_tenant_dependency import get_db_tenant
from app.core.security import get_current_user
from app.models.clinical_note import ClinicalNote, ClinicalNoteVersion
from app.models.visit import Visit
from app.services.audit_logger import log_event


router = APIRouter(prefix="/notes", tags=["notes"])


# =========================================================
# ✅ PHASE 2 — POC INITIALIZATION
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


# ---------------------------------------------------------------------
# SCHEMAS
# ---------------------------------------------------------------------

class NoteCreateRequest(BaseModel):
    note_type: str
    content: str


class NoteUpdateRequest(BaseModel):
    content: str


class NoteAmendRequest(BaseModel):
    reason: str
    content: str


# ---------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------

def _require_role(user_role: str, allowed: set[str]) -> None:
    if (user_role or "").upper() not in allowed:
        raise HTTPException(status_code=403, detail="Forbidden")


def _utc_naive_now() -> datetime:
    return datetime.utcnow()


def _utc_aware_now() -> datetime:
    return datetime.now(timezone.utc)


def _get_visit_or_404(*, db: Session, visit_id: uuid.UUID, tenant_id: uuid.UUID) -> Visit:
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


LOCK_WINDOW_HOURS = 72


def _is_note_locked(note: ClinicalNote) -> bool:
    if note.finalized_at is None:
        return False

    created = note.created_at
    if created is None:
        return False

    now = datetime.utcnow()

    if created.tzinfo is not None:
        created = created.replace(tzinfo=None)

    delta = now - created

    return delta >= timedelta(hours=LOCK_WINDOW_HOURS)


# ---------------------------------------------------------------------
# CREATE NOTE
# ---------------------------------------------------------------------

@router.post(
    "/visits/{visit_id}",
    status_code=status.HTTP_201_CREATED,
)
def create_clinical_note(
    visit_id: uuid.UUID,
    payload: NoteCreateRequest,
    db: Session = Depends(get_db_tenant),
    user=Depends(get_current_user),
):
    role = (user.role or "").upper()
    _require_role(role, {"RN", "LVN", "NP", "MD", "ADMIN"})

    visit = _get_visit_or_404(db=db, visit_id=visit_id, tenant_id=user.tenant_id)
    now_naive = _utc_naive_now()

    note = ClinicalNote(
        visit_id=visit_id,
        author_id=user.id,
        note_type=payload.note_type.strip().upper(),
        content=payload.content.strip(),
        status="DRAFT",
        created_by=user.id,
        created_at=now_naive,
        updated_at=now_naive,
        tenant_id=user.tenant_id,
        patient_id=getattr(visit, "patient_id", None),
        care_level=getattr(visit, "care_level", None),
        visit_type=getattr(visit, "visit_type", None),
        visit_origin=getattr(visit, "visit_origin", None),
        note_category=getattr(visit, "note_category", None),
        encounter_type=getattr(visit, "encounter_type", None),
        discipline=getattr(visit, "discipline", role),
        encounter_date=getattr(visit, "encounter_date", None),
    )

    # ✅ Phase 2 initialization
    _initialize_plan_of_care_updates(note)

    db.add(note)
    db.flush()

    version = _append_version(
        db=db,
        note=note,
        user_id=user.id,
        content=payload.content,
        amend_reason=None,
    )

    log_event(user_id=user.id, role=role, action="CREATE_NOTE", entity_type="clinical_note", entity_id=str(note.id), db=db)
    log_event(user_id=user.id, role=role, action="CREATE_NOTE_VERSION", entity_type="clinical_note_version", entity_id=str(version.id), db=db)

    db.commit()

    note = (
        db.query(ClinicalNote)
        .options(joinedload(ClinicalNote.current_version))
        .filter(
            ClinicalNote.id == note.id,
            ClinicalNote.tenant_id == user.tenant_id,
        )
        .first()
    )

    if not note:
        raise HTTPException(status_code=500, detail="Failed to reload note")

    db.refresh(note)
    return _serialize_note(note)


# ---------------------------------------------------------------------
# FINALIZE NOTE
# ---------------------------------------------------------------------

@router.post("/{note_id}/finalize")
def finalize_clinical_note(
    note_id: uuid.UUID,
    db: Session = Depends(get_db_tenant),
    user=Depends(get_current_user),
):
    role = (user.role or "").upper()
    _require_role(role, {"RN", "NP", "MD", "ADMIN"})

    note = _get_note_or_404(
        db=db,
        note_id=note_id,
        tenant_id=user.tenant_id,
        for_update=True,
    )

    if note.finalized_at is not None:
        raise HTTPException(status_code=400, detail="Note already finalized")

    # ✅ ensure POC structure exists
    _initialize_plan_of_care_updates(note)

    if note.current_version_id is None:
        raise HTTPException(status_code=409, detail="No active version")

    now_naive = _utc_naive_now()

    note.finalized_at = now_naive
    note.finalized_by = user.id
    note.signed_by = user.id
    note.signed_at = now_naive
    note.status = "FINALIZED"
    note.updated_at = now_naive

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