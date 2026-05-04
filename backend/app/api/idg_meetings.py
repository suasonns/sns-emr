from datetime import date
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.permissions import require_roles
from app.core.auth import CurrentUser

from app.models.idg_meeting import IDGMeeting
from app.services.idg_meeting_service import (
    create_idg_meeting,
    update_idg_meeting,
    upsert_idg_note,
    attest_idg_meeting,
    finalize_idg_meeting,
)

router = APIRouter(prefix="/idg-meetings", tags=["IDG Meetings"])


@router.post("/", summary="Create IDG meeting (scheduled)")
def create_idg_meeting_endpoint(
    patient_id: uuid.UUID,
    benefit_period_id: uuid.UUID,
    meeting_date: date,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_roles(["RN", "NP", "MD", "Administrator"])),
):
    meeting = create_idg_meeting(
        db,
        patient_id=patient_id,
        benefit_period_id=benefit_period_id,
        meeting_date=meeting_date,
        created_by=user.user_id,
        role=user.role,
    )
    return {
        "idg_id": str(meeting.idg_id),
        "patient_id": str(meeting.patient_id),
        "benefit_period_id": str(meeting.benefit_period_id),
        "meeting_date": str(meeting.meeting_date),
        "status": meeting.status,
    }


@router.patch("/{idg_id}", summary="Update IDG meeting (limited fields only)")
def update_idg_meeting_endpoint(
    idg_id: uuid.UUID,
    payload: dict,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_roles(["RN", "NP", "MD", "Administrator"])),
):
    meeting = db.query(IDGMeeting).filter(IDGMeeting.idg_id == idg_id).first()
    if not meeting:
        raise HTTPException(status_code=404, detail="IDG meeting not found")

    meeting = update_idg_meeting(
        db,
        meeting=meeting,
        payload=payload,
        updated_by=user.user_id,
        role=user.role,
    )
    return {"idg_id": str(meeting.idg_id), "status": meeting.status}


@router.post("/{idg_id}/notes", summary="Add/update IDG discipline note (optionally sign)")
def idg_note_endpoint(
    idg_id: uuid.UUID,
    discipline: str,
    summary: str,
    change_in_condition: bool,
    poc_change_recommended: bool,
    recommendations: str | None = None,
    sign: bool = False,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_roles(["RN", "SW", "CHAPLAIN", "NP", "MD", "Administrator"])),
):
    note = upsert_idg_note(
        db,
        idg_id=idg_id,
        discipline=discipline,
        author_user_id=user.user_id,
        summary=summary,
        recommendations=recommendations,
        change_in_condition=change_in_condition,
        poc_change_recommended=poc_change_recommended,
        sign=sign,
        role=user.role,
    )
    return {
        "idg_note_id": str(note.idg_note_id),
        "signed_at": str(note.signed_at) if note.signed_at else None,
    }


@router.post("/{idg_id}/attest", summary="MD/NP attestation for IDG")
def idg_attest_endpoint(
    idg_id: uuid.UUID,
    attestation_text: str,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_roles(["NP", "MD"])),
):
    att = attest_idg_meeting(
        db,
        idg_id=idg_id,
        md_user_id=user.user_id,
        attestation_text=attestation_text,
        role=user.role,
    )
    return {
        "attestation_id": str(att.attestation_id),
        "signed_at": str(att.signed_at),
    }


@router.post("/{idg_id}/finalize", summary="Finalize IDG meeting (hard stop + task triggers)")
def finalize_idg_meeting_endpoint(
    idg_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_roles(["RN", "NP", "MD", "Administrator"])),
):
    meeting = db.query(IDGMeeting).filter(IDGMeeting.idg_id == idg_id).first()
    if not meeting:
        raise HTTPException(status_code=404, detail="IDG meeting not found")

    meeting = finalize_idg_meeting(
        db,
        meeting=meeting,
        finalized_by=user.user_id,
        role=user.role,
    )
    return {
        "idg_id": str(meeting.idg_id),
        "status": meeting.status,
        "finalized_at": str(meeting.finalized_at),
    }