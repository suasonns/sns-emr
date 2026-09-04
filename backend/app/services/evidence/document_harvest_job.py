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

Durability contract (Phase A): a failure here is never terminal. Every
run transitions DocumentRecord.processing_status through
PENDING -> PROCESSING -> COMPLETE | FAILED, and this function is
idempotent -- calling it again on the same document_id is a safe no-op
once COMPLETE, and safely resumes/retries otherwise. This is what lets
`recovery_service.find_recoverable_documents()` re-drive any document
that got interrupted (server restart mid-processing) or failed
transiently (AI service timeout), without ever requiring the source file
to be re-uploaded, and without ever double-harvesting it.
"""

from __future__ import annotations

import hashlib
import logging
from datetime import datetime, timezone
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

# Bounded retry count for the recovery sweep (see recovery_service.py) --
# a document that has genuinely failed this many times (e.g. a corrupt
# file the extractor can never parse) stops being auto-retried and needs
# a human to look at last_processing_error, rather than being hammered
# forever.
MAX_PROCESSING_ATTEMPTS = 5


def run_document_intelligence(*, document_id: UUID) -> None:
    """Extract text, classify via AI, and harvest one uploaded document.

    Idempotent and safe to call more than once for the same document_id
    (the recovery sweep in recovery_service.py relies on this): a document
    already in processing_status == "COMPLETE" is a no-op. Every attempt
    is tracked via processing_status/processing_attempts/
    last_processing_error so a stuck or failed document is always
    recoverable without requiring the source file to be re-uploaded.
    """

    db = SessionLocal()
    try:
        doc = db.query(DocumentRecord).filter(DocumentRecord.id == document_id).one_or_none()
        if not doc or not doc.file_path:
            return

        if doc.processing_status == "COMPLETE":
            # Already fully processed -- nothing to do. Guards against a
            # recovery-sweep retry re-running work that already finished
            # (e.g. it raced a normal in-flight BackgroundTasks run).
            return

        doc.processing_status = "PROCESSING"
        doc.processing_started_at = datetime.now(timezone.utc)
        doc.processing_attempts = (doc.processing_attempts or 0) + 1
        db.add(doc)
        db.commit()

        try:
            storage = get_document_storage()
            stored_object = storage.open(doc.file_path)
            file_bytes = stored_object.body.read()
        except (DocumentStorageError, DocumentObjectNotFound) as exc:
            logger.exception(
                "document_intelligence_job: failed to read stored file document_id=%s",
                document_id,
            )
            doc.processing_status = "FAILED"
            doc.last_processing_error = f"storage read failed: {exc}"
            db.add(doc)
            db.commit()
            return

        if not doc.content_hash:
            doc.content_hash = hashlib.sha256(file_bytes).hexdigest()

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

        doc.processing_status = "COMPLETE"
        doc.processing_completed_at = datetime.now(timezone.utc)
        doc.last_processing_error = None

        db.add(doc)
        db.commit()
        db.refresh(doc)

    except Exception as exc:
        db.rollback()
        logger.exception(
            "document_intelligence_job: failed to process document_id=%s", document_id
        )
        try:
            doc = db.query(DocumentRecord).filter(DocumentRecord.id == document_id).one_or_none()
            if doc is not None:
                doc.processing_status = "FAILED"
                doc.last_processing_error = str(exc)[:2000]
                db.add(doc)
                db.commit()
        except Exception:
            db.rollback()
            logger.exception(
                "document_intelligence_job: failed to record FAILED status document_id=%s",
                document_id,
            )
        return
    finally:
        db.close()

    # ------------------------------
    # AI EVIDENCE HARVESTER -- separate try/except, own DB session, so a
    # harvesting failure can never affect the document-intelligence work
    # already committed above. harvest_from_source() is itself idempotent
    # (see harvest_service.py), so re-running this on an already-harvested
    # document is a safe no-op, not a duplicate.
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

    # ------------------------------
    # FACESHEET / CHART AUTO-POPULATION -- separate try/except, own DB
    # session, so a parsing/persistence failure here can never affect the
    # document-intelligence or harvesting work already committed above.
    # Reuses the SAME shared service the manual /patients/from-hnp endpoint
    # calls (persist_patient_from_hnp_extraction) -- no parsing or
    # persistence logic is duplicated here. If the document text cannot be
    # parsed as an HNP-style record (missing name/MRN/DOB), this is a safe
    # no-op: nothing is fabricated, and the chart is simply left for manual
    # entry as it is today.
    # ------------------------------
    facesheet_db = SessionLocal()
    try:
        doc = facesheet_db.query(DocumentRecord).filter(DocumentRecord.id == document_id).one_or_none()
        if not doc or not doc.document_text or not doc.patient_id:
            return

        from app.api.patients import persist_patient_from_hnp_extraction

        persist_patient_from_hnp_extraction(
            facesheet_db,
            tenant_id=doc.tenant_id,
            user_id=doc.uploaded_by,
            raw_text=doc.document_text,
            patient_id=doc.patient_id,
            source_name="PDF_UPLOAD",
            source_document_id=doc.id,
        )
    except ValueError:
        # Document text did not parse as an HNP-style record (missing
        # name/MRN/DOB) -- expected for many document types (labs,
        # orders, etc). Leave the chart untouched rather than guessing.
        logger.info(
            "document_intelligence_job: document_id=%s did not parse as HNP; "
            "facesheet left unchanged",
            document_id,
        )
    except Exception:
        logger.exception(
            "document_intelligence_job: failed to auto-populate facesheet for document_id=%s",
            document_id,
        )
    finally:
        facesheet_db.close()


def _guess_content_type(file_path: str) -> str:
    from app.services.document_storage import guess_document_content_type

    return guess_document_content_type(file_path=file_path)
