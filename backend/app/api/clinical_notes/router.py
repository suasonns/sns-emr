from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
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
# CREATE NOTE ✅ CORRECTED
# =========================================================

@router.post("/", status_code=status.HTTP_201_CREATED)
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

        # ✅ Extract metadata
        metadata = payload.get("metadata") or {}

        # ✅ Extract discipline EXACTLY as provided
        discipline_value = metadata.get("discipline") or getattr(visit, "visit_discipline", None)

        if not discipline_value:
            raise HTTPException(
                status_code=400,
                detail="discipline is required",
            )

        # ✅ Validate discipline using YOUR domain
        VALID_DISCIPLINES = {"RN", "LVN", "SN", "MSW", "CHAPLAIN", "PHYSICIAN"}

        if discipline_value not in VALID_DISCIPLINES:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid discipline: {discipline_value}",
            )

        # ✅ Build ORM object (NO TRANSFORMATION)
        new_note = ClinicalNote(
            id=UUID(payload.get("id")) if payload.get("id") else None,
            visit_id=visit.id,
            author_id=current_user.user_id,
            tenant_id=current_user.tenant_id,
            patient_id=UUID(str(payload["patient_id"])) if payload.get("patient_id") else None,
            note_type=payload.get("note_type"),
            discipline=discipline_value,
            form_family=payload.get("form_family"),
            status="DRAFT",
            encounter_date=_utcnow_naive().date(),
            content=payload.get("content") or {},
            plan_of_care_updates=payload.get("plan_of_care_updates") or {},
            created_by=current_user.user_id,
        )

        # ✅ Save using service layer
        note, _ = save_clinical_note(
            db=db,
            note=new_note,
            user_id=current_user.user_id,
        )

        return note

    except HTTPException:
        raise
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create clinical note: {exc}"
        ) from exc


# =========================================================
# REVIEW POC
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

        decision = payload.get("decision")
        if not decision:
            raise HTTPException(status_code=400, detail="decision is required")

        comment = payload.get("comment")

        updated_poc = review_poc(
            note=note,
            poc_id=poc_id,
            reviewer_user_id=current_user.user_id,
            decision=str(decision),
            comment=comment,
        )

        db.add(note)
        db.commit()
        db.refresh(note)

        return {
            "note_id": str(note.id),
            "poc_id": poc_id,
            "status": updated_poc.get("status"),
            "reviewed": updated_poc.get("review", {}).get("reviewed"),
            "poc": updated_poc,
        }

    except HTTPException:
        raise
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to review POC: {exc}"
        ) from exc


# =========================================================
# FINALIZE NOTE
# =========================================================

@router.post("/{note_id}/finalize")
def finalize_note(
    note_id: UUID,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db_tenant_with_request_state),
):
    try:
        note = _get_note_or_404(db, note_id, current_user.tenant_id)

        result = finalize_clinical_note(
            db=db,
            note=note,
            current_user=current_user,
        )

        return result

    except POCReviewGateError as exc:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail={
                "message": exc.message,
                "blocking_pocs": exc.blocking_pocs,
            },
        ) from exc
    except HTTPException:
        raise
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to finalize note: {exc}"
        ) from exc


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
    limit: int = Query(default=50, ge=1, le=200),
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db_tenant_with_request_state),
):
    return (
        db.query(ClinicalNote)
        .filter(ClinicalNote.tenant_id == current_user.tenant_id)
        .order_by(ClinicalNote.created_at.desc())
        .limit(limit)
        .all()
    )
