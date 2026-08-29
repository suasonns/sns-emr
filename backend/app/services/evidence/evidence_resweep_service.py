"""Append-only re-sweep of ALREADY-harvested evidence documents.

Why this exists (context: PR #21 of the RNICA documentation-completion
fix sequence): `ai_extraction_service._SYSTEM_PROMPT` was updated to stop
only surfacing narrative-worthy ("declining"/"notable") signals -- it now
also asks the model to sweep the FULL document for every catalog concept,
including routine/stable facts (e.g. "alert and oriented x4", "gait
steady") that were previously never captured because they never earned a
narrative signal of their own.

That prompt fix helps every NEW harvest automatically. This module is the
backfill path for documents harvested BEFORE the fix: it re-runs
`extract_signals_with_diagnostics()` against each PatientEvidenceRecord's
full `original_documentation` (not just each existing signal's own short
excerpt, unlike structured_findings_reprocess_service) and inserts any
newly-discoverable PatientHarvestedSignal rows.

Safety contract (mirrors structured_findings_reprocess_service.py):
    - APPEND-ONLY. No existing PatientHarvestedSignal row is ever
      modified, re-scored, or deleted -- RN-reviewed signals and their
      review_status/reviewed_by/reviewed_at are completely untouched.
    - DEDUPED. A newly-extracted signal is skipped (not inserted) if an
      existing signal for the same evidence_record_id already has the
      same signal_key OR a matching/overlapping original_text_excerpt
      (normalized, case-insensitive). This is what "no duplicate
      findings" means in this codebase: no two harvested_signal rows for
      the same evidence document may carry the same underlying fact.
    - Structured-field APPLICATION is unaffected by this module: newly
      inserted signals land with review_status="NEW" and go through the
      exact same RN "Apply to RNICA field(s)" review queue as any other
      harvested signal (see harvest_service.list_pending_structured_findings
      docstring) -- nothing here writes to an RNICA assessment directly.
    - Default is DRY RUN; the caller must pass commit=True to persist.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.patient_evidence import PatientEvidenceRecord, PatientHarvestedSignal
from app.services.evidence.ai_extraction_service import extract_signals_with_diagnostics

logger = logging.getLogger("sns_emr")

_WHITESPACE_RE = re.compile(r"\s+")


def _normalize_excerpt(text: str) -> str:
    return _WHITESPACE_RE.sub(" ", (text or "").strip().lower())


@dataclass
class ResweepReport:
    evidence_records_seen: int = 0
    evidence_records_processed: int = 0
    evidence_records_skipped_unconfigured: int = 0
    new_signals_added: int = 0
    new_structured_findings_added: int = 0
    duplicate_signals_skipped: int = 0
    errors: list[str] = field(default_factory=list)


def resweep_evidence_record(
    db: Session,
    *,
    evidence_record: PatientEvidenceRecord,
    commit: bool,
) -> ResweepReport:
    """Re-sweep one evidence record's full text and append any genuinely
    new signals/structured_findings that the (fixed) extraction prompt can
    now surface but the original harvest run did not.
    """

    report = ResweepReport(evidence_records_seen=1)

    existing = (
        db.query(PatientHarvestedSignal)
        .filter(PatientHarvestedSignal.evidence_record_id == evidence_record.id)
        .all()
    )
    existing_keys = {s.signal_key for s in existing}
    existing_excerpts = {_normalize_excerpt(s.original_text_excerpt) for s in existing}

    text = evidence_record.original_documentation or ""
    signals, diagnostics = extract_signals_with_diagnostics(
        text=text,
        discipline=evidence_record.discipline,
        note_type=None,
        source_type=evidence_record.source_type,
    )
    if not diagnostics.succeeded:
        report.evidence_records_skipped_unconfigured += 1
        if diagnostics.error:
            report.errors.append(f"{evidence_record.id}: {diagnostics.error}")
        return report

    report.evidence_records_processed = 1
    now = datetime.now(timezone.utc)

    for signal in signals:
        normalized = _normalize_excerpt(signal.original_text_excerpt)
        is_duplicate = (
            signal.signal_key in existing_keys
            or normalized in existing_excerpts
            or any(
                normalized and (normalized in seen or seen in normalized)
                for seen in existing_excerpts
                if seen
            )
        )
        if is_duplicate:
            report.duplicate_signals_skipped += 1
            continue

        db.add(
            PatientHarvestedSignal(
                tenant_id=evidence_record.tenant_id,
                patient_id=evidence_record.patient_id,
                evidence_record_id=evidence_record.id,
                source_type=evidence_record.source_type,
                source_discipline=evidence_record.discipline,
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
                structured_findings=list(signal.structured_findings),
                structured_findings_status="COMPLETED",
                structured_findings_attempts=1,
                structured_findings_last_attempted_at=now,
                structured_findings_last_error=None,
            )
        )
        # Track locally too, so two near-duplicate new signals in the same
        # response don't both get inserted.
        existing_keys.add(signal.signal_key)
        existing_excerpts.add(normalized)
        report.new_signals_added += 1
        report.new_structured_findings_added += len(signal.structured_findings)

    if commit:
        db.commit()
    else:
        db.rollback()

    return report


def resweep_patient(
    db: Session,
    *,
    patient_id: UUID,
    tenant_id: UUID,
    commit: bool = False,
) -> ResweepReport:
    """Re-sweep every evidence record for one patient. See module docstring
    for the append-only/dedup safety contract.
    """

    total = ResweepReport()
    records = (
        db.query(PatientEvidenceRecord)
        .filter(
            PatientEvidenceRecord.patient_id == patient_id,
            PatientEvidenceRecord.tenant_id == tenant_id,
        )
        .all()
    )

    for record in records:
        try:
            r = resweep_evidence_record(db, evidence_record=record, commit=commit)
        except Exception as exc:  # never let one bad document abort the batch
            db.rollback()
            logger.exception(
                "evidence_resweep: failed evidence_record_id=%s", record.id
            )
            total.errors.append(f"{record.id}: {exc}")
            continue

        total.evidence_records_seen += r.evidence_records_seen
        total.evidence_records_processed += r.evidence_records_processed
        total.evidence_records_skipped_unconfigured += r.evidence_records_skipped_unconfigured
        total.new_signals_added += r.new_signals_added
        total.new_structured_findings_added += r.new_structured_findings_added
        total.duplicate_signals_skipped += r.duplicate_signals_skipped
        total.errors.extend(r.errors)

    return total
