from __future__ import annotations

"""
Visit audio recording capture + staff review endpoints.

Scope (per current plan): capture the encounter audio, store it securely,
and let staff review it (playback + optional transcript once STT is wired).
Speech-to-text itself (Azure Speech, per the chosen vendor) is a follow-up —
`transcript_status` stays "not_transcribed" until that integration exists.
"""

import uuid
from datetime import datetime, timezone
from typing import Generator, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, Security, UploadFile, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from starlette.responses import FileResponse

from app.core.database import SessionLocal
from app.core.patient_access import get_authorized_patient
from app.core.security import get_current_user, CurrentUser
from app.models.visit_recording import VisitRecording
from app.services.recording_storage import (
    build_recording_path,
    save_recording_stream,
    resolve_recording_path,
    delete_recording_file,
)
from app.services.audit_logger import log_event

router = APIRouter(prefix="/visit-recordings", tags=["visit-recordings"])

MAX_UPLOAD_BYTES = 250 * 1024 * 1024  # 250MB safety cap per recording


def get_db(request: Request) -> Generator[Session, None, None]:
    db = SessionLocal()
    request.state.db = db
    try:
        yield db
    finally:
        db.close()


class RecordingOut(BaseModel):
    id: str
    patient_id: str
    visit_id: Optional[str]
    assessment_id: Optional[str]
    assessment_type: Optional[str]
    recorded_by: str
    recorded_at: datetime
    duration_seconds: Optional[int]
    size_bytes: Optional[int]
    mime_type: Optional[str]
    consent_confirmed: bool
    transcript_status: str
    transcript_text: Optional[str]
    reviewed_by: Optional[str]
    reviewed_at: Optional[datetime]
    review_notes: Optional[str]

    class Config:
        from_attributes = True


def _serialize(rec: VisitRecording) -> dict:
    return {
        "id": str(rec.id),
        "patient_id": str(rec.patient_id),
        "visit_id": str(rec.visit_id) if rec.visit_id else None,
        "assessment_id": str(rec.assessment_id) if rec.assessment_id else None,
        "assessment_type": rec.assessment_type,
        "recorded_by": str(rec.recorded_by),
        "recorded_at": rec.recorded_at,
        "duration_seconds": rec.duration_seconds,
        "size_bytes": rec.size_bytes,
        "mime_type": rec.mime_type,
        "consent_confirmed": rec.consent_confirmed,
        "transcript_status": rec.transcript_status,
        "transcript_text": rec.transcript_text,
        "reviewed_by": str(rec.reviewed_by) if rec.reviewed_by else None,
        "reviewed_at": rec.reviewed_at,
        "review_notes": rec.review_notes,
    }


@router.post("", status_code=status.HTTP_201_CREATED)
async def upload_recording(
    patient_id: uuid.UUID = Form(...),
    consent_confirmed: bool = Form(...),
    visit_id: Optional[uuid.UUID] = Form(None),
    assessment_id: Optional[uuid.UUID] = Form(None),
    assessment_type: Optional[str] = Form(None),
    duration_seconds: Optional[int] = Form(None),
    audio: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Security(get_current_user),
):
    if not consent_confirmed:
        raise HTTPException(
            status_code=422,
            detail="Consent attestation is required before a recording can be saved "
                   "(confirm the patient/family was informed the visit is being recorded).",
        )

    patient = get_authorized_patient(db, patient_id, current_user)

    recording_id = uuid.uuid4()
    tenant_id = getattr(patient, "tenant_id", None)
    absolute_path, relative_path = build_recording_path(
        tenant_id=tenant_id,
        patient_id=patient.id,
        recording_id=recording_id,
        mime_type=audio.content_type,
        file_name=audio.filename,
    )

    size_bytes = await save_recording_stream(absolute_path, audio)
    if size_bytes > MAX_UPLOAD_BYTES:
        delete_recording_file(relative_path)
        raise HTTPException(status_code=413, detail="Recording exceeds maximum allowed size")
    if size_bytes == 0:
        delete_recording_file(relative_path)
        raise HTTPException(status_code=422, detail="Uploaded recording was empty")

    rec = VisitRecording(
        id=recording_id,
        tenant_id=tenant_id,
        patient_id=patient.id,
        visit_id=visit_id,
        assessment_id=assessment_id,
        assessment_type=assessment_type,
        recorded_by=current_user.id,
        consent_confirmed=True,
        consent_confirmed_at=datetime.now(timezone.utc),
        file_path=relative_path,
        file_name=audio.filename,
        mime_type=audio.content_type,
        duration_seconds=duration_seconds,
        size_bytes=size_bytes,
        recorded_at=datetime.now(timezone.utc),
    )
    db.add(rec)
    db.commit()
    db.refresh(rec)

    log_event(
        db=db,
        tenant_id=str(tenant_id) if tenant_id else None,
        user_id=str(current_user.id),
        role=(current_user.role or "").upper(),
        action="VISIT_RECORDING_CREATED",
        entity_type="VISIT_RECORDING",
        entity_id=str(rec.id),
        metadata={"patient_id": str(patient.id), "assessment_type": assessment_type},
    )

    return _serialize(rec)


@router.get("/patient/{patient_id}")
def list_patient_recordings(
    patient_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Security(get_current_user),
):
    patient = get_authorized_patient(db, patient_id, current_user)
    rows = (
        db.query(VisitRecording)
        .filter(
            VisitRecording.patient_id == patient.id,
            VisitRecording.deleted_at.is_(None),
        )
        .order_by(VisitRecording.recorded_at.desc())
        .all()
    )
    return {"recordings": [_serialize(r) for r in rows]}


def _get_owned_recording(db: Session, recording_id: uuid.UUID, current_user: CurrentUser) -> VisitRecording:
    rec = db.query(VisitRecording).filter(VisitRecording.id == recording_id).one_or_none()
    if not rec or rec.deleted_at is not None:
        raise HTTPException(status_code=404, detail="Recording not found")
    # Enforces the same tenant/care-team scoping as every other patient-scoped
    # endpoint before allowing playback/review of a specific recording.
    get_authorized_patient(db, rec.patient_id, current_user)
    return rec


@router.get("/{recording_id}/audio")
def stream_recording_audio(
    recording_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Security(get_current_user),
):
    rec = _get_owned_recording(db, recording_id, current_user)
    try:
        path = resolve_recording_path(rec.file_path)
    except ValueError:
        raise HTTPException(status_code=500, detail="Recording path invalid")
    if not path.exists():
        raise HTTPException(status_code=404, detail="Recording file missing from storage")
    return FileResponse(path, media_type=rec.mime_type or "application/octet-stream", filename=rec.file_name or f"{recording_id}.webm")


class ReviewRequest(BaseModel):
    review_notes: Optional[str] = None


@router.post("/{recording_id}/review")
def mark_recording_reviewed(
    recording_id: uuid.UUID,
    payload: ReviewRequest,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Security(get_current_user),
):
    rec = _get_owned_recording(db, recording_id, current_user)
    rec.reviewed_by = current_user.id
    rec.reviewed_at = datetime.now(timezone.utc)
    rec.review_notes = payload.review_notes
    db.commit()
    db.refresh(rec)
    return _serialize(rec)


@router.delete("/{recording_id}")
def soft_delete_recording(
    recording_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Security(get_current_user),
):
    """Soft-delete only — the audio file is retained on disk. Recordings are
    audit artifacts; only a separate retention/purge job should ever hard
    delete them, never a routine API call."""
    rec = _get_owned_recording(db, recording_id, current_user)
    rec.deleted_at = datetime.now(timezone.utc)
    rec.deleted_by = current_user.id
    db.commit()
    return {"status": "deleted", "id": str(rec.id)}
