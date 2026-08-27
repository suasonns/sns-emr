"""Background job: run document intelligence (extraction + AI classification)
on a freshly-uploaded DocumentRecord, then harvest it into the AI Evidence
Registry.

This is invoked via FastAPI BackgroundTasks from the upload endpoint, AFTER
the upload's own request/response cycle has already committed the
DocumentRecord + stored file. It intentionally opens its OWN database
session (SessionLocal) rather than reusing the request-scoped session,
since the request's session is closed by the `get_db` dependency once the
response is sent -- background tasks must not touch a closed session.

Isolation contract: this job can never fail the original upload (it only
ever runs after the upload has already succeeded and responded), and a
failure partway through (extraction error, AI error, DB error) only means
the document keeps its pre-existing document_text/extracted_values (most
likely empty) -- the uploaded file and its DocumentRecord row are
completely unaffected either way.
"""

from __future__ import annotations

import logging
from uuid import UUID

from app.core.database import SessionLocal
from app.models.document_record import DocumentRecord
from app.services.document_flagger import evaluate_document_flags
from app.services.document_storage import get_document_storage, DocumentStorageError, DocumentObjectNotFound
from app.services.evidence.document_intelligence_service import (
    classify_and_extract_document,
    extract_text_from_file,
)
from app.services.evidence.harvest_service import harvest_from_source

logger = logging.getLogger("sns_emr")


def run_document_intelligence(*, document_id: UUID) -> None:
    """Extract text, classify via AI, and harvest one uploaded document.

    Never raises -- any failure is logged and simply leaves the document
    without AI-derived text/findings (it remains fully usable/downloadable
    either way).
    """

    db = SessionLocal()
    try:
        doc = db.query(DocumentRecord).filter(DocumentRecord.id == document_id).one_or_none()
        if not doc or not doc.file_path:
            return

        try:
            storage = get_document_storage()
            stored_object = storage.open(doc.file_path)
            file_bytes = stored_object.body.read()
        except (DocumentStorageError, DocumentObjectNotFound):
            logger.exception(
                "document_intelligence_job: failed to read stored file document_id=%s",
                document_id,
            )
            return

        content_type = _guess_content_type(doc.file_path)
        extraction = extract_text_from_file(
            file_bytes=file_bytes, content_type=content_type, file_name=doc.file_name
        )

        ai_result = classify_and_extract_document(
            text=extraction.text or None,
            image_base64=extraction.image_base64,
            content_type=content_type,
            hint_document_type=doc.document_type,
        )

        # ------------------------------
        # Persist extracted text + AI findings onto the document row.
        # ------------------------------
        if extraction.text:
            doc.document_text = extraction.text

        merged_extracted_values = dict(doc.extracted_values or {})
        if ai_result is not None:
            merged_extracted_values["ai_document_type_guess"] = ai_result.document_type_guess
            merged_extracted_values["ai_summary"] = ai_result.summary
            merged_extracted_values["ai_confidence"] = ai_result.confidence
            merged_extracted_values["ai_key_findings"] = [
                {
                    "label": f.label,
                    "value": f.value,
                    "category": f.category,
                    "original_text_excerpt": f.original_text_excerpt,
                }
                for f in ai_result.key_findings
            ]
        merged_extracted_values["ai_needs_manual_review"] = extraction.needs_manual_review
        doc.extracted_values = merged_extracted_values

        # Re-run the existing rule-based flagger now that real text exists.
        flag_result = evaluate_document_flags(
            document_type=doc.document_type,
            extracted_values=merged_extracted_values,
            document_text=doc.document_text or "",
        )
        doc.is_flagged = doc.is_flagged or flag_result.is_flagged
        if flag_result.is_flagged:
            doc.flag_tier = flag_result.tier
            doc.matched_rule_ids = flag_result.matched_rule_ids

        db.add(doc)
        db.commit()
        db.refresh(doc)

    except Exception:
        db.rollback()
        logger.exception(
            "document_intelligence_job: failed to process document_id=%s", document_id
        )
        return
    finally:
        db.close()

    # ------------------------------
    # AI EVIDENCE HARVESTER -- separate try/except, own DB session, so a
    # harvesting failure can never affect the document-intelligence work
    # already committed above.
    # ------------------------------
    harvest_db = SessionLocal()
    try:
        doc = harvest_db.query(DocumentRecord).filter(DocumentRecord.id == document_id).one_or_none()
        if not doc:
            return
        harvest_text_parts = [doc.document_text or ""]
        ai_summary = (doc.extracted_values or {}).get("ai_summary")
        if ai_summary:
            harvest_text_parts.append(str(ai_summary))
        harvest_text = "\n\n".join(p for p in harvest_text_parts if p).strip()

        harvest_from_source(
            db=harvest_db,
            tenant_id=doc.tenant_id,
            patient_id=doc.patient_id,
            source_type="DOCUMENT_UPLOAD",
            source_record_id=doc.id,
            recorded_at=doc.uploaded_at,
            text=harvest_text,
            discipline=None,
            note_type=(doc.extracted_values or {}).get("ai_document_type_guess") or doc.document_type,
            recorded_by_user_id=doc.uploaded_by,
        )
    except Exception:
        logger.exception(
            "document_intelligence_job: failed to harvest document_id=%s", document_id
        )
    finally:
        harvest_db.close()


def _guess_content_type(file_path: str) -> str:
    from app.services.document_storage import guess_document_content_type

    return guess_document_content_type(file_path=file_path)
