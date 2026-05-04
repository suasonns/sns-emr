from datetime import datetime, date
import uuid
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.idg_meeting import IDGMeeting
from app.models.idg_note import IDGNote
from app.models.idg_md_attestation import IDGMDAttestation
from app.models.task import Task
from app.services.audit_logger import log_event

# Phase-locked required disciplines for completion
REQUIRED_DISCIPLINES = {"RN", "SW", "CHAPLAIN"}


def create_idg_meeting(
    db: Session,
    *,
    patient_id: uuid.UUID,
    benefit_period_id: uuid.UUID,
    meeting_date: date,
    created_by: uuid.UUID,
    role: str,
) -> IDGMeeting:
    meeting = IDGMeeting(
        idg_id=uuid.uuid4(),
        patient_id=patient_id,
        benefit_period_id=benefit_period_id,
        meeting_date=meeting_date,
        status="SCHEDULED",
        finalized_at=None,
        created_by=created_by,
    )

    db.add(meeting)
    db.flush()

    log_event(
        user_id=created_by,
        role=role,
        action="CREATE_IDG",
        entity_type="idg_meeting",
        entity_id=str(meeting.idg_id),
        db=db,
    )

    db.commit()
    db.refresh(meeting)
    return meeting


def update_idg_meeting(db: Session, *, meeting: IDGMeeting, payload: dict, updated_by: uuid.UUID, role: str) -> IDGMeeting:
    if meeting.status == "COMPLETED" or meeting.finalized_at is not None:
        raise HTTPException(status_code=400, detail="Finalized IDG cannot be edited")

    # Only allow non-destructive fields
    allowed = {"meeting_date"}  # keep tight; expand later intentionally
    for k, v in payload.items():
        if k in allowed:
            setattr(meeting, k, v)

    db.flush()

    log_event(
        user_id=updated_by,
        role=role,
        action="UPDATE_IDG",
        entity_type="idg_meeting",
        entity_id=str(meeting.idg_id),
        db=db,
    )

    db.commit()
    db.refresh(meeting)
    return meeting


def upsert_idg_note(
    db: Session,
    *,
    idg_id: uuid.UUID,
    discipline: str,
    author_user_id: uuid.UUID,
    summary: str,
    recommendations: str | None,
    change_in_condition: bool,
    poc_change_recommended: bool,
    sign: bool,
    role: str,
) -> IDGNote:
    note = db.query(IDGNote).filter(IDGNote.idg_id == idg_id, IDGNote.discipline == discipline).first()

    if note and note.signed_at is not None:
        raise HTTPException(status_code=400, detail="Signed IDG note cannot be modified")

    if not note:
        note = IDGNote(
            idg_note_id=uuid.uuid4(),
            idg_id=idg_id,
            discipline=discipline,
            author_user_id=author_user_id,
        )

    note.summary = summary
    note.recommendations = recommendations
    note.change_in_condition = change_in_condition
    note.poc_change_recommended = poc_change_recommended

    if sign:
        note.signed_at = datetime.utcnow()

    db.add(note)
    db.flush()

    log_event(
        user_id=author_user_id,
        role=role,
        action="SIGN_IDG_NOTE" if sign else "SAVE_IDG_NOTE",
        entity_type="idg_note",
        entity_id=str(note.idg_note_id),
        db=db,
    )

    db.commit()
    db.refresh(note)
    return note


def attest_idg_meeting(
    db: Session,
    *,
    idg_id: uuid.UUID,
    md_user_id: uuid.UUID,
    attestation_text: str,
    role: str,
) -> IDGMDAttestation:
    existing = db.query(IDGMDAttestation).filter(IDGMDAttestation.idg_id == idg_id).first()
    if existing:
        raise HTTPException(status_code=400, detail="MD attestation already exists")

    att = IDGMDAttestation(
        attestation_id=uuid.uuid4(),
        idg_id=idg_id,
        md_user_id=md_user_id,
        attestation_text=attestation_text,
        signed_at=datetime.utcnow(),
    )

    db.add(att)
    db.flush()

    log_event(
        user_id=md_user_id,
        role=role,
        action="MD_ATTEST_IDG",
        entity_type="idg_md_attestation",
        entity_id=str(att.attestation_id),
        db=db,
    )

    db.commit()
    db.refresh(att)
    return att


def _validate_ready_to_finalize(db: Session, idg_id: uuid.UUID):
    # Require signed notes for RN/SW/CHAPLAIN
    notes = db.query(IDGNote).filter(IDGNote.idg_id == idg_id).all()
    signed = {n.discipline for n in notes if n.signed_at is not None}
    missing = REQUIRED_DISCIPLINES - signed
    if missing:
        raise HTTPException(status_code=400, detail=f"Cannot finalize IDG: missing signed notes for {sorted(missing)}")

    # Require MD/NP attestation
    att = db.query(IDGMDAttestation).filter(IDGMDAttestation.idg_id == idg_id).first()
    if not att:
        raise HTTPException(status_code=400, detail="Cannot finalize IDG: missing MD/NP attestation")

    return notes


def finalize_idg_meeting(db: Session, *, meeting: IDGMeeting, finalized_by: uuid.UUID, role: str) -> IDGMeeting:
    if meeting.status == "COMPLETED" or meeting.finalized_at is not None:
        raise HTTPException(status_code=400, detail="IDG already finalized")

    notes = _validate_ready_to_finalize(db, meeting.idg_id)

    # Finalize
    meeting.status = "COMPLETED"
    meeting.finalized_at = datetime.utcnow()
    db.flush()

    # Complete any open IDG_REVIEW task for this patient/benefit period (evidence-linked)
    idg_task = (
        db.query(Task)
        .filter(Task.patient_id == meeting.patient_id)
        .filter(Task.benefit_period_id == meeting.benefit_period_id)
        .filter(Task.task_type == "IDG_REVIEW")
        .filter(Task.status != "COMPLETED")
        .first()
    )
    if idg_task:
        idg_task.status = "COMPLETED"
        idg_task.completed_at = datetime.utcnow()
        idg_task.completion_reference_type = "IDG_MEETING"
        idg_task.completion_reference_id = str(meeting.idg_id)

    # If any note recommends POC change, create POC_UPDATE task (dedupe)
    if any(n.poc_change_recommended for n in notes):
        existing_poc = (
            db.query(Task)
            .filter(Task.patient_id == meeting.patient_id)
            .filter(Task.benefit_period_id == meeting.benefit_period_id)
            .filter(Task.task_type == "POC_UPDATE")
            .filter(Task.discipline == "RN")
            .filter(Task.status != "COMPLETED")
            .first()
        )

        if not existing_poc:
            t = Task(
                patient_id=meeting.patient_id,
                benefit_period_id=meeting.benefit_period_id,
                discipline="RN",
                task_type="POC_UPDATE",
                origin="MANUAL",
                regulatory_basis="IDG",
                due_date=date.today(),
                status="PENDING",
                completion_reference_type="IDG_MEETING",
                completion_reference_id=str(meeting.idg_id),
            )
            db.add(t)
            db.flush()

            log_event(
                user_id=finalized_by,
                role=role,
                action="IDG_TRIGGER_POC_UPDATE_TASK",
                entity_type="task",
                entity_id=str(getattr(t, "id", "")) if hasattr(t, "id") else "task",
                db=db,
            )

    log_event(
        user_id=finalized_by,
        role=role,
        action="FINALIZE_IDG",
        entity_type="idg_meeting",
        entity_id=str(meeting.idg_id),
        db=db,
    )

    db.commit()
    db.refresh(meeting)
    return meeting