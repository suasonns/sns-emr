from __future__ import annotations

"""
Visit audio recording capture + automatic transcription + staff review
endpoints.

Pipeline (automatic, per Lockdown Mode "staff must never record twice"
directive): audio upload -> durable storage -> BackgroundTasks-triggered
Azure Speech transcription -> generate_note_draft() -> structured findings
harvested into the same PatientHarvestedSignal Apply/Apply-All/provenance/
conflict pipeline every other evidence source uses. Manual transcript entry
is kept ONLY as an explicit fallback for the FAILED state (e.g. Azure
Speech is not configured, or genuinely could not transcribe this audio) --
it is never the default/first path for a recording that has not yet been
attempted.
"""

import logging
import time
import uuid
from datetime import datetime, timezone
from typing import Generator, Iterator, Optional
from urllib.parse import quote

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, Request, Security, UploadFile, status
from pydantic import BaseModel
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from starlette.concurrency import run_in_threadpool
from starlette.responses import StreamingResponse

from app.core.database import SessionLocal
from app.core.patient_access import get_authorized_patient
from app.core.security import get_current_user, CurrentUser
from app.models.patient_evidence import PatientEvidenceRecord, PatientHarvestedSignal
from app.models.visit_recording import VisitRecording
from app.services.evidence.note_draft_service import build_harvested_findings_context, generate_note_draft
from app.services.evidence.transcription_service import azure_speech_configured, transcribe_audio_bytes
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

MAX_TRANSCRIPTION_ATTEMPTS = 3
RETRY_BACKOFF_SECONDS = 3


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
        "client_recording_id": str(rec.client_recording_id) if rec.client_recording_id else None,
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
        "transcript_provider": rec.transcript_provider,
        "transcript_text": rec.transcript_text,
        "transcription_attempts": rec.transcription_attempts,
        "transcription_error": rec.transcription_error,
        "reviewed_by": str(rec.reviewed_by) if rec.reviewed_by else None,
        "reviewed_at": rec.reviewed_at,
        "review_notes": rec.review_notes,
        "ai_note_draft": rec.ai_note_draft,
    }


@router.post("", status_code=status.HTTP_201_CREATED)
async def upload_recording(
    background_tasks: BackgroundTasks,
    patient_id: uuid.UUID = Form(...),
    consent_confirmed: bool = Form(...),
    visit_id: Optional[uuid.UUID] = Form(None),
    assessment_id: Optional[uuid.UUID] = Form(None),
    assessment_type: Optional[str] = Form(None),
    duration_seconds: Optional[int] = Form(None),
    client_recording_id: Optional[uuid.UUID] = Form(None),
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

    # Idempotency: the frontend generates client_recording_id BEFORE the
    # upload attempt so an offline-queued retry (or a flaky-connection
    # retry) after reconnect can safely resend the exact same recording
    # without ever creating a duplicate row/object/transcription. If we've
    # already seen this key, return the existing recording untouched --
    # never re-store the audio, never re-queue transcription.
    if client_recording_id is not None:
        existing = (
            db.query(VisitRecording)
            .filter(VisitRecording.client_recording_id == client_recording_id)
            .one_or_none()
        )
        if existing is not None:
            get_authorized_patient(db, existing.patient_id, current_user)
            return _serialize(existing)

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
        client_recording_id=client_recording_id,
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
        transcript_status="QUEUED",
    )
    try:
        db.add(rec)
        db.commit()
    except IntegrityError as exc:
        # A concurrent request for the same client_recording_id committed
        # first -- this is the same recording, not a conflict. Return the
        # row that won the race instead of erroring or duplicating.
        db.rollback()
        if client_recording_id is not None:
            existing = (
                db.query(VisitRecording)
                .filter(VisitRecording.client_recording_id == client_recording_id)
                .one_or_none()
            )
            if existing is not None:
                try:
                    await run_in_threadpool(storage.delete, object_key)
                except RecordingStorageError:
                    pass
                return _serialize(existing)
        try:
            await run_in_threadpool(storage.delete, object_key)
        except RecordingStorageError:
            pass
        raise HTTPException(status_code=500, detail="Recording database write failed") from exc
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

    # Automatically transcribe -- staff must never be asked to type/paste a
    # transcript for a recording that hasn't even been attempted yet. Runs
    # after the response is sent (its own DB session; the request-scoped
    # session is closed by then).
    background_tasks.add_task(_process_transcription_sync, rec.id)

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


class TranscriptRequest(BaseModel):
    transcript_text: str


def _harvest_note_draft_structured_findings(
    db: Session,
    *,
    rec: VisitRecording,
    structured_findings: list,
    transcript_text: str,
) -> None:
    """Fan the note draft's validated structured_findings out into the same
    PatientEvidenceRecord/PatientHarvestedSignal pipeline every other
    evidence source uses (see app.services.evidence.harvest_service), so a
    visit-transcript-derived finding goes through the identical Apply/Apply
    All + provenance + conflict-review path as one extracted from an
    uploaded document. Best-effort/never raises -- the transcript save
    itself must never fail because of this.
    """
    if not structured_findings:
        return
    try:
        existing = (
            db.query(PatientEvidenceRecord)
            .filter(
                PatientEvidenceRecord.tenant_id == rec.tenant_id,
                PatientEvidenceRecord.source_type == "TRANSCRIPT",
                PatientEvidenceRecord.source_record_id == rec.id,
            )
            .one_or_none()
        )
        if existing is not None:
            # Re-transcription of the same recording -- replace the prior
            # signal rather than accumulate duplicates.
            db.query(PatientHarvestedSignal).filter(
                PatientHarvestedSignal.evidence_record_id == existing.id
            ).delete()
            evidence_record = existing
            evidence_record.original_documentation = transcript_text
        else:
            evidence_record = PatientEvidenceRecord(
                tenant_id=rec.tenant_id,
                patient_id=rec.patient_id,
                source_type="TRANSCRIPT",
                source_record_id=rec.id,
                visit_id=rec.visit_id,
                discipline="RN",
                recorded_by_user_id=rec.recorded_by,
                recorded_at=rec.recorded_at,
                original_documentation=transcript_text,
            )
            db.add(evidence_record)
            db.flush()
        evidence_record.ai_extraction_completed = True
        db.add(
            PatientHarvestedSignal(
                tenant_id=rec.tenant_id,
                patient_id=rec.patient_id,
                evidence_record_id=evidence_record.id,
                source_type="TRANSCRIPT",
                source_discipline="RN",
                recorded_at=rec.recorded_at,
                signal_key="visit_transcript_note_draft",
                signal_text=f"AI note draft findings from visit recording {rec.id}",
                original_text_excerpt=transcript_text[:4000],
                review_status="NEW",
                structured_findings=structured_findings,
            )
        )
    except Exception:
        logger.exception(
            "visit_recordings: failed to harvest note-draft structured_findings recording_id=%s",
            rec.id,
        )


def _generate_and_harvest_note_draft(db: Session, rec: VisitRecording, transcript_text: str) -> bool:
    """Shared by the automatic pipeline and the manual-entry fallback:
    calls generate_note_draft() and fans structured_findings into the
    harvest pipeline. Returns True iff a draft was produced. Never raises.
    """
    try:
        harvested_context = build_harvested_findings_context(db, rec.patient_id)
        draft = generate_note_draft(
            transcript_text=transcript_text,
            assessment_type=rec.assessment_type or "RNICA",
            discipline="RN",
            harvested_context=harvested_context,
        )
    except Exception:
        logger.exception("visit_recordings: note draft generation raised recording_id=%s", rec.id)
        draft = None

    if draft is not None:
        rec.ai_note_draft = draft.to_dict()
        _harvest_note_draft_structured_findings(
            db,
            rec=rec,
            structured_findings=list(draft.structured_findings),
            transcript_text=transcript_text,
        )
        return True
    rec.ai_note_draft = None
    return False


def _run_transcription_pipeline(db: Session, rec: VisitRecording) -> None:
    """Automatic STT pipeline body, shared by the initial post-upload
    background task and the manual retry endpoint. Advances
    QUEUED/RETRYING -> PROCESSING -> COMPLETED, or -> FAILED once attempts
    are exhausted. Never loses the recording/audio on failure -- only the
    row's status/error fields change; the object in storage is untouched.
    """
    if not azure_speech_configured():
        rec.transcript_status = "FAILED"
        rec.transcription_error = "Azure Speech is not configured (AZURE_SPEECH_KEY/AZURE_SPEECH_REGION missing)"
        db.commit()
        return

    storage = get_recording_storage()
    starting_attempts = rec.transcription_attempts
    for i in range(1, MAX_TRANSCRIPTION_ATTEMPTS + 1):
        attempt = starting_attempts + i
        rec.transcription_attempts = attempt
        rec.transcript_status = "PROCESSING" if i == 1 else "RETRYING"
        db.commit()

        audio_bytes = None
        try:
            stored_object = storage.open(rec.file_path)
            try:
                audio_bytes = stored_object.body.read()
            finally:
                stored_object.body.close()
        except Exception:
            logger.exception(
                "transcription pipeline: failed to read stored audio recording_id=%s", rec.id
            )

        transcript_text = None
        if audio_bytes:
            transcript_text = transcribe_audio_bytes(audio_bytes, content_type=rec.mime_type)

        if transcript_text:
            rec.transcript_text = transcript_text
            rec.transcript_provider = "azure_speech"
            rec.transcribed_at = datetime.now(timezone.utc)
            rec.transcription_error = None
            _generate_and_harvest_note_draft(db, rec, transcript_text)
            rec.transcript_status = "COMPLETED"
            db.commit()
            log_event(
                db=db,
                tenant_id=str(rec.tenant_id) if rec.tenant_id else None,
                user_id=str(rec.recorded_by),
                role="SYSTEM",
                action="VISIT_RECORDING_TRANSCRIBED",
                entity_type="VISIT_RECORDING",
                entity_id=str(rec.id),
                metadata={
                    "patient_id": str(rec.patient_id),
                    "transcript_provider": "azure_speech",
                    "attempts": attempt,
                },
            )
            return

        rec.transcription_error = (
            "Could not read stored audio" if not audio_bytes else "Azure Speech returned no transcript"
        )
        db.commit()
        if i < MAX_TRANSCRIPTION_ATTEMPTS:
            time.sleep(RETRY_BACKOFF_SECONDS)

    rec.transcript_status = "FAILED"
    db.commit()
    log_event(
        db=db,
        tenant_id=str(rec.tenant_id) if rec.tenant_id else None,
        user_id=str(rec.recorded_by),
        role="SYSTEM",
        action="VISIT_RECORDING_TRANSCRIPTION_FAILED",
        entity_type="VISIT_RECORDING",
        entity_id=str(rec.id),
        metadata={"patient_id": str(rec.patient_id), "attempts": rec.transcription_attempts},
    )


def _process_transcription_sync(recording_id: uuid.UUID) -> None:
    """Entry point for BackgroundTasks -- opens its own DB session since
    the request-scoped session is already closed by the time this runs."""
    db = SessionLocal()
    try:
        rec = db.query(VisitRecording).filter(VisitRecording.id == recording_id).one_or_none()
        if rec is None or rec.deleted_at is not None:
            return
        _run_transcription_pipeline(db, rec)
    except Exception:
        logger.exception("transcription pipeline: unhandled error recording_id=%s", recording_id)
        try:
            db.rollback()
        except Exception:
            pass
    finally:
        db.close()


@router.post("/{recording_id}/retry-transcription")
def retry_recording_transcription(
    recording_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Security(get_current_user),
):
    """Staff-initiated retry after automatic retries are exhausted (or to
    retry after Azure Speech credentials are fixed). Idempotent -- safe to
    call repeatedly; if a transcript already exists (COMPLETED), it is
    returned unchanged rather than re-transcribed."""
    rec = _get_owned_recording(db, recording_id, current_user)
    if rec.transcript_status == "COMPLETED":
        return _serialize(rec)
    if rec.transcript_status in ("PROCESSING", "RETRYING"):
        # Already in flight -- avoid launching a second concurrent pipeline.
        return _serialize(rec)
    rec.transcript_status = "QUEUED"
    db.commit()
    background_tasks.add_task(_process_transcription_sync, rec.id)
    db.refresh(rec)
    return _serialize(rec)


@router.put("/{recording_id}/transcript")
def save_recording_transcript(
    recording_id: uuid.UUID,
    payload: TranscriptRequest,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Security(get_current_user),
):
    """Manual transcript entry -- FAILED-state fallback ONLY. Automatic
    Azure Speech transcription is the normal path for every recording;
    this endpoint exists solely for the case where it genuinely could not
    transcribe the audio (not configured, unsupported audio, or repeated
    API failure) so the visit is not lost. Rejected outside FAILED so a
    clinician is never asked to type/paste a transcript that automatic
    transcription hasn't even been given a chance to produce.
    """
    rec = _get_owned_recording(db, recording_id, current_user)

    if rec.transcript_status != "FAILED":
        raise HTTPException(
            status_code=409,
            detail=(
                "Manual transcript entry is only available after automatic transcription "
                f"has failed (current status: {rec.transcript_status}). Wait for automatic "
                "transcription to finish, or use retry-transcription if it already failed."
            ),
        )

    cleaned = (payload.transcript_text or "").strip()
    if not cleaned:
        raise HTTPException(status_code=422, detail="Transcript text is required")

    rec.transcript_text = cleaned
    rec.transcript_status = "COMPLETED"
    rec.transcript_provider = "manual_entry"
    rec.transcribed_at = datetime.now(timezone.utc)
    rec.transcription_error = None

    draft_generated = _generate_and_harvest_note_draft(db, rec, cleaned)

    db.commit()
    db.refresh(rec)

    log_event(
        db=db,
        tenant_id=str(rec.tenant_id) if rec.tenant_id else None,
        user_id=str(current_user.user_id),
        role=(current_user.role or "").upper(),
        action="VISIT_RECORDING_TRANSCRIBED",
        entity_type="VISIT_RECORDING",
        entity_id=str(rec.id),
        metadata={
            "patient_id": str(rec.patient_id),
            "transcript_provider": "manual_entry",
            "note_draft_generated": draft_generated,
        },
    )

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
