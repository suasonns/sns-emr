from __future__ import annotations

from typing import Any, Dict, Optional
from uuid import UUID, UUID as UUIDType
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.patient_access import get_authorized_patient
from app.core.database import get_db
from app.dependencies.auth import get_current_user
from app.models.document_record import DocumentRecord
from app.models.document_notification import DocumentNotification
from app.models.document_idg_resolution import DocumentIDGResolution
from app.services.document_flagger import evaluate_document_flags
from app.services.audit_events import audit_event
from app.services.document_notifications import create_document_notifications

router = APIRouter(prefix="/documents", tags=["Documents"])


# ---------------------------------------------------------------------
# Request Models
# ---------------------------------------------------------------------

class DocumentUploadRequest(BaseModel):
    patient_id: UUID
    document_type: str
    source: str = "EXTERNAL"
    file_name: Optional[str] = None
    file_path: Optional[str] = None
    extracted_values: Dict[str, Any] = Field(default_factory=dict)
    document_text: Optional[str] = None


class DocumentResolutionRequest(BaseModel):
    resolution_status: str
    resolution_note: Optional[str] = None


# ---------------------------------------------------------------------
# Upload Document
# ---------------------------------------------------------------------

@router.post("/", status_code=status.HTTP_201_CREATED)
def upload_document(
    payload: DocumentUploadRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    tenant_id = current_user.tenant_id
    user_id = current_user.id
    role = (current_user.role or "").strip().upper()
    get_authorized_patient(db, payload.patient_id, current_user)

    doc = DocumentRecord(
        tenant_id=tenant_id,
        patient_id=payload.patient_id,
        document_type=payload.document_type,
        source=payload.source,
        file_name=payload.file_name,
        file_path=payload.file_path,
        extracted_values=payload.extracted_values,
        document_text=payload.document_text,
        uploaded_by=user_id,
        uploaded_at=datetime.now(timezone.utc),
    )

    flag_result = evaluate_document_flags(
        document_type=payload.document_type,
        extracted_values=payload.extracted_values,
        document_text=payload.document_text or "",
    )

    doc.is_flagged = flag_result.is_flagged
    doc.flag_tier = flag_result.tier
    doc.matched_rule_ids = flag_result.matched_rule_ids

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
    db.refresh(doc)

    return {"document_id": str(doc.id)}


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