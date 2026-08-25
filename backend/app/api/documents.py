from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Iterator, Optional
from uuid import UUID, UUID as UUIDType

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, Request, UploadFile, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session
from starlette.concurrency import run_in_threadpool
from starlette.responses import StreamingResponse
from urllib.parse import quote

from app.core.patient_access import get_authorized_patient
from app.core.database import get_db
from app.dependencies.auth import get_current_user
from app.models.document_record import DocumentRecord
from app.models.document_idg_resolution import DocumentIDGResolution
from app.services.document_flagger import evaluate_document_flags
from app.services.audit_events import audit_event
from app.services.document_notifications import create_document_notifications
from app.services.evidence.document_harvest_job import run_document_intelligence
from app.services.document_storage import (
    DocumentObject,
    DocumentObjectNotFound,
    DocumentRangeNotSatisfiable,
    DocumentStorageConfigurationError,
    DocumentStorageError,
    DocumentStorageProvider,
    DocumentUploadTooLarge,
    build_document_key,
    get_document_storage,
    guess_document_content_type,
    max_upload_bytes_from_env,
    normalize_document_mime_type,
)

router = APIRouter(prefix="/documents", tags=["Documents"])
logger = logging.getLogger(__name__)


class DocumentResolutionRequest(BaseModel):
    resolution_status: str
    resolution_note: Optional[str] = None


class DocumentOut(BaseModel):
    id: str
    patient_id: str
    document_type: str
    source: str
    file_name: Optional[str]
    uploaded_at: datetime
    uploaded_by: Optional[str]
    is_flagged: bool
    flag_tier: Optional[str] = None
    ai_document_type_guess: Optional[str] = None
    ai_summary: Optional[str] = None
    ai_confidence: Optional[float] = None
    ai_key_findings: Optional[list] = None
    ai_needs_manual_review: Optional[bool] = None
    has_extracted_text: bool = False

    model_config = ConfigDict(from_attributes=True)


class DocumentUploadResponse(DocumentOut):
    document_id: str
    size_bytes: int
    content_type: str


class DocumentListResponse(BaseModel):
    documents: list[DocumentOut]


def _serialize(doc: DocumentRecord) -> dict[str, Any]:
    extracted_values = doc.extracted_values or {}
    return {
        "id": str(doc.id),
        "patient_id": str(doc.patient_id),
        "document_type": doc.document_type,
        "source": doc.source,
        "file_name": doc.file_name,
        "uploaded_at": doc.uploaded_at,
        "uploaded_by": str(doc.uploaded_by) if doc.uploaded_by else None,
        "is_flagged": bool(doc.is_flagged),
        "flag_tier": doc.flag_tier,
        "ai_document_type_guess": extracted_values.get("ai_document_type_guess"),
        "ai_summary": extracted_values.get("ai_summary"),
        "ai_confidence": extracted_values.get("ai_confidence"),
        "ai_key_findings": extracted_values.get("ai_key_findings"),
        "ai_needs_manual_review": extracted_values.get("ai_needs_manual_review"),
        "has_extracted_text": bool(doc.document_text),
    }


def _get_owned_document(
    db: Session,
    document_id: UUID,
    current_user,
) -> DocumentRecord:
    tenant_uuid = UUIDType(str(current_user.tenant_id))
    doc = (
        db.query(DocumentRecord)
        .filter(
            DocumentRecord.id == document_id,
            DocumentRecord.tenant_id == tenant_uuid,
        )
        .one_or_none()
    )
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    get_authorized_patient(db, doc.patient_id, current_user)
    if not doc.file_path:
        raise HTTPException(status_code=404, detail="Document file is not available")
    return doc


# ---------------------------------------------------------------------
# Upload Document
# ---------------------------------------------------------------------

@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    response_model=DocumentUploadResponse,
)
async def upload_document(
    background_tasks: BackgroundTasks,
    patient_id: UUID = Form(...),
    document_type: str = Form(...),
    source: str = Form("EXTERNAL"),
    extracted_values: Optional[str] = Form(None),
    document_text: Optional[str] = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    storage: DocumentStorageProvider = Depends(get_document_storage),
):
    tenant_id = UUIDType(str(current_user.tenant_id))
    user_id = UUIDType(str(current_user.id))
    role = (current_user.role or "").strip().upper()
    patient = get_authorized_patient(db, patient_id, current_user)

    try:
        parsed_extracted_values = (
            json.loads(extracted_values) if extracted_values else {}
        )
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=422, detail="extracted_values must be valid JSON") from exc
    if not isinstance(parsed_extracted_values, dict):
        raise HTTPException(status_code=422, detail="extracted_values must be a JSON object")

    try:
        content_type = normalize_document_mime_type(
            file.content_type,
            filename=file.filename,
        )
        max_upload_bytes = max_upload_bytes_from_env()
    except ValueError as exc:
        raise HTTPException(status_code=415, detail=str(exc)) from exc
    except DocumentStorageConfigurationError as exc:
        raise HTTPException(status_code=500, detail="Document storage is misconfigured") from exc

    document_id = uuid.uuid4()
    object_key = build_document_key(
        tenant_id=tenant_id,
        patient_id=patient.id,
        document_id=document_id,
        content_type=content_type,
    )

    try:
        await file.seek(0)
        size_bytes = await run_in_threadpool(
            storage.put,
            object_key,
            file.file,
            content_type=content_type,
            max_bytes=max_upload_bytes,
        )
    except DocumentUploadTooLarge as exc:
        raise HTTPException(status_code=413, detail=str(exc)) from exc
    except DocumentStorageError as exc:
        raise HTTPException(status_code=503, detail="Document storage operation failed") from exc
    if size_bytes == 0:
        try:
            await run_in_threadpool(storage.delete, object_key)
        except DocumentStorageError as exc:
            raise HTTPException(
                status_code=500,
                detail="Empty document cleanup requires operator attention",
            ) from exc
        raise HTTPException(status_code=422, detail="Uploaded document was empty")

    doc = DocumentRecord(
        id=document_id,
        tenant_id=tenant_id,
        patient_id=patient.id,
        document_type=document_type,
        source=source,
        file_name=file.filename or f"{document_id}",
        file_path=object_key,
        extracted_values=parsed_extracted_values,
        document_text=document_text,
        uploaded_by=user_id,
        uploaded_at=datetime.now(timezone.utc),
    )

    flag_result = evaluate_document_flags(
        document_type=document_type,
        extracted_values=parsed_extracted_values,
        document_text=document_text or "",
    )

    doc.is_flagged = flag_result.is_flagged
    doc.flag_tier = flag_result.tier
    doc.matched_rule_ids = flag_result.matched_rule_ids

    try:
        db.add(doc)
        db.flush()

        audit_event(
            db=db,
            tenant_id=str(tenant_id),
            user_id=str(user_id),
            role=role,
            action="DOC_UPLOADED",
            entity_type="DOCUMENT",
            entity_id=str(doc.id),
            meta={"document_type": doc.document_type},
        )

        create_document_notifications(
            db,
            tenant_id=str(tenant_id),
            document_id=doc.id,
            patient_id=doc.patient_id,
            actor_user_id=str(user_id),
            actor_role=role,
        )

        db.commit()
    except Exception as exc:
        db.rollback()
        try:
            await run_in_threadpool(storage.delete, object_key)
        except DocumentStorageError:
            logger.exception(
                "Document database write failed and object cleanup also failed",
                extra={"document_id": str(document_id)},
            )
            raise HTTPException(
                status_code=500,
                detail="Document database write failed; storage cleanup requires operator attention",
            ) from exc
        raise HTTPException(
            status_code=500,
            detail="Document database write failed and uploaded object was removed",
        ) from exc

    db.refresh(doc)
    background_tasks.add_task(run_document_intelligence, document_id=doc.id)
    return {
        **_serialize(doc),
        "document_id": str(doc.id),
        "size_bytes": size_bytes,
        "content_type": content_type,
    }


@router.get("/patient/{patient_id}", response_model=DocumentListResponse)
def list_patient_documents(
    patient_id: UUID,
    document_type: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    patient = get_authorized_patient(db, patient_id, current_user)
    query = (
        db.query(DocumentRecord)
        .filter(
            DocumentRecord.patient_id == patient.id,
            DocumentRecord.tenant_id == UUIDType(str(current_user.tenant_id)),
        )
        .order_by(DocumentRecord.uploaded_at.desc(), DocumentRecord.created_at.desc())
    )
    if document_type:
        query = query.filter(DocumentRecord.document_type == document_type)
    return {"documents": [_serialize(doc) for doc in query.all()]}


@router.get("/{document_id}/download")
def download_document(
    document_id: UUID,
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    storage: DocumentStorageProvider = Depends(get_document_storage),
):
    doc = _get_owned_document(db, document_id, current_user)
    try:
        stored_object = storage.open(doc.file_path, request.headers.get("range"))
    except DocumentObjectNotFound as exc:
        raise HTTPException(status_code=404, detail="Document object missing from storage") from exc
    except DocumentRangeNotSatisfiable as exc:
        raise HTTPException(
            status_code=416,
            detail="Requested document range is not satisfiable",
            headers={"Content-Range": f"bytes */{exc.total_length}"},
        ) from exc
    except DocumentStorageError as exc:
        raise HTTPException(status_code=503, detail="Document storage operation failed") from exc

    content_type = guess_document_content_type(
        file_name=doc.file_name,
        file_path=doc.file_path,
    )
    headers = {
        "Content-Disposition": (
            "inline; filename*=UTF-8''"
            + quote(doc.file_name or f"{document_id}", safe="")
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
        _iter_document(stored_object),
        status_code=response_status,
        media_type=content_type,
        headers=headers,
    )


def _iter_document(stored_object: DocumentObject) -> Iterator[bytes]:
    try:
        while chunk := stored_object.body.read(1024 * 1024):
            yield chunk
    finally:
        stored_object.body.close()


# ---------------------------------------------------------------------
# MD‑ONLY: Resolve Document for IDG (TENANT SAFE)
# ---------------------------------------------------------------------

@router.post("/{document_id}/resolve", status_code=status.HTTP_200_OK)
def resolve_document_for_idg(
    document_id: UUID,
    payload: DocumentResolutionRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    tenant_uuid = UUIDType(str(current_user.tenant_id))
    resolved_by_uuid = UUIDType(str(current_user.id))
    role = (current_user.role or "").strip().upper()

    if role != "MD":
        raise HTTPException(status_code=403, detail="Only MD may resolve documents for IDG")

    status_norm = payload.resolution_status.strip().upper()
    if status_norm not in {"ACCEPTED", "NO_CHANGE", "OVERRIDDEN"}:
        raise HTTPException(status_code=422, detail="Invalid resolution_status")

    doc = (
        db.query(DocumentRecord)
        .filter(
            DocumentRecord.id == document_id,
            DocumentRecord.tenant_id == tenant_uuid,
        )
        .one_or_none()
    )

    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    get_authorized_patient(db, doc.patient_id, current_user)

    now = datetime.now(timezone.utc)

    existing = (
        db.query(DocumentIDGResolution)
        .filter(
            DocumentIDGResolution.document_id == document_id,
            DocumentIDGResolution.tenant_id == tenant_uuid,
        )
        .one_or_none()
    )

    if existing:
        existing.resolution_status = status_norm
        existing.resolution_note = payload.resolution_note
        existing.resolved_by = resolved_by_uuid
        existing.resolved_at = now
    else:
        db.add(
            DocumentIDGResolution(
                tenant_id=tenant_uuid,
                document_id=document_id,
                resolution_status=status_norm,
                resolution_note=payload.resolution_note,
                resolved_by=resolved_by_uuid,
                resolved_at=now,
            )
        )

    audit_event(
        db=db,
        tenant_id=str(tenant_uuid),
        user_id=str(resolved_by_uuid),
        role=role,
        action="DOC_RESOLVED_FOR_IDG",
        entity_type="DOCUMENT",
        entity_id=str(document_id),
        meta={"resolution_status": status_norm},
    )

    db.commit()

    return {
        "status": "ok",
        "document_id": str(document_id),
        "resolution_status": status_norm,
    }