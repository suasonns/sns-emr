from __future__ import annotations

"""
Visit audio recording capture + staff review endpoints.

Scope (per current plan): capture the encounter audio, store it securely,
and let staff review it (playback + optional transcript once STT is wired).
Speech-to-text itself (Azure Speech, per the chosen vendor) is a follow-up —
`transcript_status` stays "not_transcribed" until that integration exists.
"""

import logging
import uuid
from datetime import datetime, timezone
from typing import Generator, Iterator, Optional
from urllib.parse import quote

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, Security, UploadFile, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from starlette.concurrency import run_in_threadpool
from starlette.responses import StreamingResponse

from app.core.database import SessionLocal
from app.core.patient_access import get_authorized_patient
from app.core.security import get_current_user, CurrentUser
from app.models.visit_recording import VisitRecording
from app.services.recording_storage import (
    RecordingObject,
    RecordingObjectNotFound,
    RecordingRangeNotSatisfiable,
    RecordingStorageError,
    RecordingStorageProvider,
    RecordingUploadTooLarge,
    build_recording_key,
    get_recording_storage,
    max_upload_bytes_from_env,
    normalize_recording_mime_type,
)
from app.services.audit_logger import log_event

router = APIRouter(prefix="/visit-recordings", tags=["visit-recordings"])
logger = logging.getLogger(__name__)


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
    storage: RecordingStorageProvider = Depends(get_recording_storage),
):
    if not consent_confirmed:
        raise HTTPException(
            status_code=422,
            detail="Consent attestation is required before a recording can be saved "
                   "(confirm the patient/family was informed the visit is being recorded).",
        )

    patient = get_authorized_patient(db, patient_id, current_user)

    try:
        content_type = normalize_recording_mime_type(audio.content_type)
        max_upload_bytes = max_upload_bytes_from_env()
    except ValueError as exc:
        raise HTTPException(status_code=415, detail=str(exc)) from exc
    except RecordingStorageError as exc:
        raise HTTPException(status_code=500, detail="Recording storage is misconfigured") from exc

    recording_id = uuid.uuid4()
    tenant_id = getattr(patient, "tenant_id", None)
    object_key = build_recording_key(
        tenant_id=tenant_id,
        patient_id=patient.id,
        recording_id=recording_id,
        content_type=content_type,
    )

    try:
        await audio.seek(0)
        size_bytes = await run_in_threadpool(
            storage.put,
            object_key,
            audio.file,
            content_type=content_type,
            max_bytes=max_upload_bytes,
        )
    except RecordingUploadTooLarge as exc:
        raise HTTPException(status_code=413, detail=str(exc)) from exc
    except RecordingStorageError as exc:
        raise HTTPException(status_code=503, detail="Recording storage operation failed") from exc
    if size_bytes == 0:
        try:
            await run_in_threadpool(storage.delete, object_key)
        except RecordingStorageError as exc:
            raise HTTPException(
                status_code=500,
                detail="Empty recording cleanup requires operator attention",
            ) from exc
        raise HTTPException(status_code=422, detail="Uploaded recording was empty")

    rec = VisitRecording(
        id=recording_id,
        tenant_id=tenant_id,
        patient_id=patient.id,
        visit_id=visit_id,
        assessment_id=assessment_id,
        assessment_type=assessment_type,
        recorded_by=current_user.user_id,
        consent_confirmed=True,
        consent_confirmed_at=datetime.now(timezone.utc),
        file_path=object_key,
        file_name=audio.filename,
        mime_type=content_type,
        duration_seconds=duration_seconds,
        size_bytes=size_bytes,
        recorded_at=datetime.now(timezone.utc),
    )
    try:
        db.add(rec)
        db.commit()
    except Exception as exc:
        db.rollback()
        try:
            await run_in_threadpool(storage.delete, object_key)
        except RecordingStorageError:
            logger.exception(
                "Recording database write failed and object cleanup also failed",
                extra={"recording_id": str(recording_id)},
            )
            raise HTTPException(
                status_code=500,
                detail="Recording database write failed; storage cleanup requires operator attention",
            ) from exc
        raise HTTPException(
            status_code=500,
            detail="Recording database write failed and uploaded object was removed",
        ) from exc
    try:
        db.refresh(rec)
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="Recording was saved but could not be reloaded",
        ) from exc

    log_event(
        db=db,
        tenant_id=str(tenant_id) if tenant_id else None,
        user_id=str(current_user.user_id),
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
    request: Request,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Security(get_current_user),
    storage: RecordingStorageProvider = Depends(get_recording_storage),
):
    rec = _get_owned_recording(db, recording_id, current_user)
    try:
        stored_object = storage.open(rec.file_path, request.headers.get("range"))
    except RecordingObjectNotFound as exc:
        raise HTTPException(status_code=404, detail="Recording object missing from storage") from exc
    except RecordingRangeNotSatisfiable as exc:
        raise HTTPException(
            status_code=416,
            detail="Requested recording range is not satisfiable",
            headers={"Content-Range": f"bytes */{exc.total_length}"},
        ) from exc
    except RecordingStorageError as exc:
        raise HTTPException(status_code=503, detail="Recording storage operation failed") from exc
    headers = {
        "Content-Disposition": (
            "inline; filename*=UTF-8''"
            + quote(rec.file_name or f"{recording_id}.webm", safe="")
        ),
        "Cache-Control": "private, no-store",
        "Accept-Ranges": "bytes",
        "Content-Length": str(stored_object.content_length),
    }
    response_status = 200
    if request.headers.get("range"):
        response_status = 206
        headers["Content-Range"] = (
            f"bytes {stored_object.range_start}-{stored_object.range_end}/"
            f"{stored_object.total_length}"
        )
    return StreamingResponse(
        _iter_recording(stored_object),
        status_code=response_status,
        media_type=rec.mime_type or "application/octet-stream",
        headers=headers,
    )


def _iter_recording(stored_object: RecordingObject) -> Iterator[bytes]:
    try:
        while chunk := stored_object.body.read(1024 * 1024):
            yield chunk
    finally:
        stored_object.body.close()


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
    rec.reviewed_by = current_user.user_id
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
    rec.deleted_by = current_user.user_id
    db.commit()
    return {"status": "deleted", "id": str(rec.id)}
