from datetime import datetime
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.permissions import require_roles
from app.core.auth import CurrentUser

from app.models.clinical_note import ClinicalNote
from app.models.visit import Visit
from app.models.amendment import Amendment

from app.services.audit_logger import log_event
from app.services.poc_warning_tasks import warn_rn_np_md  # POC warning tasks
from app.services.poc_warning_autosuggest import suggest_close_poc_noncompliant_structure_tasks

router = APIRouter(prefix="/notes", tags=["notes"])


@router.post(
    "/visits/{visit_id}",
    status_code=status.HTTP_201_CREATED,
    summary="Create draft clinical note",
)
def create_clinical_note(
    *,
    visit_id: uuid.UUID,
    note_type: str,
    content: str,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_roles(["RN", "LVN", "NP", "MD"])),
):
    visit = db.query(Visit).filter(Visit.id == visit_id).first()
    if not visit:
        raise HTTPException(status_code=404, detail="Visit not found")

    note = ClinicalNote(
        visit_id=visit_id,
        author_id=user.user_id,
        note_type=note_type,
        content=content,
        status="draft",
    )

    db.add(note)
    db.flush()  # ensure note.id exists

    log_event(
        user_id=user.user_id,
        role=user.role,
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
    *,
    note_id: uuid.UUID,
    content: str,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_roles(["RN", "LVN", "NP", "MD"])),
):
    note = db.query(ClinicalNote).filter(ClinicalNote.id == note_id).first()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")

    if note.finalized_at is not None:
        raise HTTPException(status_code=400, detail="Finalized notes cannot be edited; use amendment")

    note.content = content
    db.flush()

    log_event(
        user_id=user.user_id,
        role=user.role,
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
    user: CurrentUser = Depends(require_roles(["RN", "NP", "MD"])),
):
    note = db.query(ClinicalNote).filter(ClinicalNote.id == note_id).first()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")

    try:
        note.finalize(finalized_by=user.user_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    db.flush()

    # POC Compliance Warning + Auto-suggest
    if note.note_type in ("POC_UPDATE", "POC_NOTE", "PLAN_OF_CARE"):
        content_lower = (note.content or "").lower()
        missing = [t for t in ("goal", "intervention", "frequency", "discipline") if t not in content_lower]

        visit = db.query(Visit).filter(Visit.id == note.visit_id).first()
        if visit:
            if missing:
                try:
                    warn_rn_np_md(
                        db=db,
                        patient_id=visit.patient_id,
                        task_type="POC_NONCOMPLIANT_STRUCTURE",
                        due_date=datetime.utcnow().date(),
                        origin="MANUAL",
                        message=f"POC note missing required elements: {missing}",
                        reference_type="NOTE",
                        reference_id=note.id,
                    )
                except ValueError:
                    log_event(
                        user_id=user.user_id,
                        role=user.role,
                        action="POC_WARNING_NOT_CREATED",
                        entity_type="clinical_note",
                        entity_id=str(note.id),
                        db=db,
                    )
            else:
                updated = suggest_close_poc_noncompliant_structure_tasks(
                    db=db,
                    patient_id=visit.patient_id,
                    corrected_note_id=note.id,
                )
                if updated:
                    log_event(
                        user_id=user.user_id,
                        role=user.role,
                        action="POC_AUTOSUGGEST_CLOSE",
                        entity_type="clinical_note",
                        entity_id=str(note.id),
                        db=db,
                    )

    log_event(
        user_id=user.user_id,
        role=user.role,
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
        "finalized_at": note.finalized_at,
        "finalized_by": str(note.finalized_by),
    }

@router.post("/{note_id}/amend", summary="Amend a finalized clinical note")
def amend_clinical_note(
    note_id: uuid.UUID,
    reason: str,
    content: str,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_roles(["RN", "NP", "MD"])),
):
    note = db.query(ClinicalNote).filter(ClinicalNote.id == note_id).first()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")

    if note.finalized_at is None:
        raise HTTPException(status_code=400, detail="Only finalized notes can be amended")

    if not reason.strip():
        raise HTTPException(status_code=400, detail="Amendment reason is required")
    if not content.strip():
        raise HTTPException(status_code=400, detail="Amendment content is required")

    amendment = Amendment(
        clinical_note_id=note.id,
        author_id=user.user_id,
        created_by=user.user_id,
        reason=reason.strip(),
        content=content.strip(),
        original_finalized_at=note.finalized_at,
    )

    db.add(amendment)
    db.flush()

    log_event(
        user_id=user.user_id,
        role=user.role,
        action="AMEND_NOTE",
        entity_type="amendment",
        entity_id=str(amendment.id),
        db=db,
    )

    db.commit()
    db.refresh(amendment)

    return {
        "amendment_id": str(amendment.id),
        "note_id": str(note.id),
        "created_at": amendment.created_at,
        "original_finalized_at": amendment.original_finalized_at,
    }


@router.get("/visits/{visit_id}", summary="List notes for a visit (read-only)")
def list_notes_for_visit(
    visit_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_roles(["RN", "LVN", "NP", "MD", "Surveyor"])),
):
    notes = (
        db.query(ClinicalNote)
        .filter(ClinicalNote.visit_id == visit_id)
        .order_by(ClinicalNote.created_at.asc())
        .all()
    )

    return [
        {
            "note_id": str(n.id),
            "note_type": n.note_type,
            "status": n.status,
            "finalized_at": n.finalized_at,
        }
        for n in notes
    ]