"""Generic harvest orchestrator for the AI Evidence Harvester (UCIER Phase 1).

`harvest_from_source` is the single entry point every documentation source
(ClinicalNote via the service layer, CommunicationsLog, IncidentReport,
CHHAVisitOutcome, IDGNote, PlanOfCare review, Certification/CTI,
F2FEncounter, ...) calls after its own record is finalized/saved.

Isolation contract:
    - This function NEVER raises. Callers can invoke it fire-and-forget
      immediately after their own commit without any try/except of their
      own (though callers SHOULD still wrap the call defensively -- this
      is defense in depth, not a license to skip it).
    - This function performs its own commit via a SAVEPOINT (nested
      transaction) so a harvesting failure can never roll back the
      caller's already-committed clinical documentation.
    - The evidence record is always persisted, even if AI extraction
      fails or is unconfigured ("nothing observed is discarded").
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.patient_evidence import PatientEvidenceRecord, PatientHarvestedSignal
from app.services.evidence.ai_extraction_service import extract_signals

logger = logging.getLogger("sns_emr")


def harvest_from_source(
    db: Session,
    *,
    tenant_id: UUID,
    patient_id: UUID,
    source_type: str,
    source_record_id: UUID,
    recorded_at: datetime,
    text: str,
    visit_id: UUID | None = None,
    communication_log_id: UUID | None = None,
    discipline: str | None = None,
    note_type: str | None = None,
    recorded_by_user_id: UUID | None = None,
    recorded_by_name: str | None = None,
) -> PatientEvidenceRecord | None:
    """Harvest one piece of documentation into the evidence registry.

    Returns the created PatientEvidenceRecord, or None if harvesting could
    not even preserve the evidence record (e.g. a DB error) -- this is
    logged, never raised.
    """

    cleaned_text = (text or "").strip()
    if not cleaned_text:
        # Nothing to harvest from an empty note; not an error.
        return None

    try:
        with db.begin_nested():
            evidence_record = PatientEvidenceRecord(
                tenant_id=tenant_id,
                patient_id=patient_id,
                source_type=source_type,
                source_record_id=source_record_id,
                visit_id=visit_id,
                communication_log_id=communication_log_id,
                discipline=discipline,
                recorded_by_user_id=recorded_by_user_id,
                recorded_by_name=recorded_by_name,
                recorded_at=recorded_at,
                original_documentation=cleaned_text,
            )
            db.add(evidence_record)
            db.flush()

            _run_ai_extraction(
                db,
                evidence_record=evidence_record,
                text=cleaned_text,
                discipline=discipline,
                note_type=note_type,
            )

        db.commit()
        return evidence_record
    except Exception:
        db.rollback()
        logger.exception(
            "evidence_harvester: failed to harvest source_type=%s source_record_id=%s "
            "patient_id=%s -- clinical documentation itself is unaffected",
            source_type,
            source_record_id,
            patient_id,
        )
        return None


def _run_ai_extraction(
    db: Session,
    *,
    evidence_record: PatientEvidenceRecord,
    text: str,
    discipline: str | None,
    note_type: str | None,
) -> None:
    """Run AI extraction and persist resulting signals. Isolated failure handling."""

    try:
        extracted = extract_signals(
            text=text,
            discipline=discipline,
            note_type=note_type,
            source_type=evidence_record.source_type,
        )
        evidence_record.ai_extraction_completed = True
    except Exception as exc:  # pragma: no cover - extract_signals never raises, defense in depth
        evidence_record.ai_extraction_completed = False
        evidence_record.ai_extraction_error = str(exc)[:2000]
        logger.exception(
            "evidence_harvester: unexpected AI extraction error evidence_record_id=%s",
            evidence_record.id,
        )
        return

    for signal in extracted:
        db.add(
            PatientHarvestedSignal(
                tenant_id=evidence_record.tenant_id,
                patient_id=evidence_record.patient_id,
                evidence_record_id=evidence_record.id,
                source_type=evidence_record.source_type,
                source_discipline=discipline,
                recorded_at=evidence_record.recorded_at,
                signal_key=signal.signal_key,
                signal_text=signal.signal_text,
                original_text_excerpt=signal.original_text_excerpt,
                trend=signal.trend,
                confidence=signal.confidence,
                clinical_system=signal.clinical_system,
                requires_idg_review=signal.requires_idg_review,
                requires_poc_review=signal.requires_poc_review,
                review_status="NEW",
            )
        )


def extract_narrative_text(content: Any, *, max_chars: int = 20000) -> str:
    """Best-effort narrative text extraction from a note's JSONB content dict.

    ClinicalNote.content (and similar JSON payloads) mix structured codes,
    booleans, and free-text narrative under many different keys depending
    on discipline/form. Rather than hard-coding every form's schema, this
    walks the structure and collects string values that look like prose
    (long enough to be meaningful narrative, not a short code/enum value).
    """

    fragments: list[str] = []

    def _walk(node: Any) -> None:
        if isinstance(node, dict):
            for value in node.values():
                _walk(value)
        elif isinstance(node, list):
            for value in node:
                _walk(value)
        elif isinstance(node, str):
            stripped = node.strip()
            # Skip short tokens/enums/codes; keep prose-like text.
            if len(stripped) >= 15 and " " in stripped:
                fragments.append(stripped)

    _walk(content)

    joined = "\n".join(fragments)
    return joined[:max_chars]
