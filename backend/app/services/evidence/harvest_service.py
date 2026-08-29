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
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from sqlalchemy.exc import IntegrityError
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
    commit: bool = True,
) -> PatientEvidenceRecord | None:
    """Harvest one piece of documentation into the evidence registry.

    Returns the created PatientEvidenceRecord, or None if harvesting could
    not even preserve the evidence record (e.g. a DB error) -- this is
    logged, never raised.

    `commit`: True (default) when called standalone, after the caller has
    already committed its own record (e.g. finalize_clinical_note) -- this
    function performs its own isolated commit/rollback via a SAVEPOINT.
    Pass `commit=False` when called from *inside* a larger unit of work
    that has not committed yet (e.g. mid-request-handler service
    functions) -- the SAVEPOINT still isolates a harvesting failure from
    the rest of the pending transaction (only the harvester's own nested
    work is rolled back on error, via the `with db.begin_nested()` context
    manager), but the final commit is left to the caller so the evidence
    record lands atomically with the source record it was harvested from.
    """

    cleaned_text = (text or "").strip()
    if not cleaned_text:
        # Nothing to harvest from an empty note; not an error.
        return None

    # Idempotency guard: if this exact source was already harvested (e.g. a
    # recovery-sweep retry racing a request that already succeeded, or a
    # document reprocessed after an interrupted first attempt), reuse the
    # existing evidence record instead of creating a second one. This is
    # backed by a DB-level unique constraint on
    # (tenant_id, source_type, source_record_id), so it also holds under
    # concurrent retries, not just this in-process check.
    existing = (
        db.query(PatientEvidenceRecord)
        .filter(
            PatientEvidenceRecord.tenant_id == tenant_id,
            PatientEvidenceRecord.source_type == source_type,
            PatientEvidenceRecord.source_record_id == source_record_id,
        )
        .one_or_none()
    )
    if existing is not None:
        logger.info(
            "evidence_harvester: source_type=%s source_record_id=%s already harvested "
            "(evidence_record_id=%s) -- skipping duplicate harvest",
            source_type,
            source_record_id,
            existing.id,
        )
        return existing

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

        if commit:
            db.commit()
        return evidence_record
    except IntegrityError:
        # Lost a race against a concurrent harvest of the exact same
        # source (e.g. a recovery-sweep retry overlapping a live request).
        # The unique constraint on (tenant_id, source_type,
        # source_record_id) means the other caller's row is the durable
        # one -- fetch and return it rather than reporting failure for
        # documentation that was, in fact, successfully harvested.
        if commit:
            db.rollback()
        return (
            db.query(PatientEvidenceRecord)
            .filter(
                PatientEvidenceRecord.tenant_id == tenant_id,
                PatientEvidenceRecord.source_type == source_type,
                PatientEvidenceRecord.source_record_id == source_record_id,
            )
            .one_or_none()
        )
    except Exception:
        if commit:
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

    now = datetime.now(timezone.utc)

    try:
        extracted = extract_signals(
            text=text,
            discipline=discipline,
            note_type=note_type,
            source_type=evidence_record.source_type,
        )
        evidence_record.ai_extraction_completed = True
        structured_findings_status = "COMPLETED"
        structured_findings_error = None
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
                structured_findings=list(signal.structured_findings),
                structured_findings_status=structured_findings_status,
                structured_findings_attempts=1,
                structured_findings_last_attempted_at=now,
                structured_findings_last_error=structured_findings_error,
            )
        )


def list_pending_structured_findings(db: Session, patient_id: UUID) -> list[dict[str, Any]]:
    """Return every not-yet-reviewed harvested signal for `patient_id` that
    carries at least one validated StructuredFinding.

    This is the read side of the RNICA structured-findings application
    layer: each entry pairs one signal's provenance (excerpt, source type,
    recorded_at) with the concept-coded findings extracted from it, so the
    frontend can offer an "Apply to RNICA field(s)" action per signal
    without ever seeing an un-validated field_path/value pair -- only what
    already passed `validate_findings()` at harvest time is ever returned
    here.

    Signals with an empty `structured_findings` list are excluded entirely
    -- this is scoped to structured-findings consumption only, not a
    general narrative-signal review queue.
    """

    rows = (
        db.query(PatientHarvestedSignal)
        .filter(
            PatientHarvestedSignal.patient_id == patient_id,
            PatientHarvestedSignal.review_status == "NEW",
        )
        .order_by(PatientHarvestedSignal.recorded_at.desc())
        .limit(200)
        .all()
    )

    results: list[dict[str, Any]] = []
    for row in rows:
        findings = row.structured_findings or []
        if not findings:
            continue
        results.append(
            {
                "id": str(row.id),
                "source_type": row.source_type,
                "clinical_system": row.clinical_system,
                "recorded_at": row.recorded_at.isoformat() if row.recorded_at else None,
                "original_text_excerpt": row.original_text_excerpt,
                "structured_findings": findings,
            }
        )
    return results


VALID_SIGNAL_REVIEW_DISPOSITIONS = {
    "APPLIED",
    "DISMISSED",
    # Added for the verified-apply engine (see visits.update_rnica_assessment's
    # fieldWrites handling and rnica_apply_verification.py): a signal must be
    # able to land in one of these outcomes too, since blindly forcing every
    # apply into APPLIED/DISMISSED is exactly the data-loss defect this fixes.
    # PARTIALLY_APPLIED: some of the signal's destination writes verified as
    #   persisted, others did not (or other findings in the same signal are
    #   still blocked by a conflict).
    # CONFLICT: every finding in the signal was blocked by an existing
    #   non-blank/RN-entered value -- nothing was ever attempted.
    # FAILED: at least one destination write was attempted but did not verify
    #   as persisted (mapping bug, concurrent overwrite, etc.).
    "PARTIALLY_APPLIED",
    "CONFLICT",
    "FAILED",
}


def review_harvested_signal(
    db: Session,
    *,
    signal_id: UUID,
    tenant_id: UUID,
    disposition: str,
    reviewed_by_user_id: UUID | None = None,
    reason: str | None = None,
) -> PatientHarvestedSignal:
    """Record an RN's disposition of one structured-finding-bearing signal.

    `disposition` must be one of VALID_SIGNAL_REVIEW_DISPOSITIONS:
    "APPLIED" (every destination write this signal's findings resolved to
    was verified persisted -- see rnica_apply_verification.py, which
    computes this disposition from a fresh DB read, never assumed),
    "PARTIALLY_APPLIED" (some but not all verified, or some findings still
    blocked by a conflict), "CONFLICT" (every finding was blocked by an
    existing value, nothing was ever attempted), "FAILED" (a write was
    attempted but did not verify as persisted), or "DISMISSED" (the RN
    reviewed the finding(s) and chose not to apply them, or the finding had
    no actionable destination field at all). Combined with the "NEW"
    default set at harvest time, review_status is always exactly one of
    these values -- never a broader narrative-signal review vocabulary.

    Never applies anything to a chart itself -- this only records a
    disposition the caller has ALREADY verified (or explicitly chosen, for
    DISMISSED). Scoped to `tenant_id` so a signal from one tenant can never
    be reviewed via another tenant's session.
    """

    if disposition not in VALID_SIGNAL_REVIEW_DISPOSITIONS:
        raise ValueError(f"disposition must be one of {sorted(VALID_SIGNAL_REVIEW_DISPOSITIONS)}")

    signal = (
        db.query(PatientHarvestedSignal)
        .filter(
            PatientHarvestedSignal.id == signal_id,
            PatientHarvestedSignal.tenant_id == tenant_id,
        )
        .first()
    )
    if signal is None:
        raise LookupError("Harvested signal not found")

    signal.review_status = disposition
    signal.reviewed_by_user_id = reviewed_by_user_id
    signal.reviewed_at = datetime.now(timezone.utc)
    signal.review_disposition_reason = reason
    db.commit()
    db.refresh(signal)
    return signal


def review_harvested_signals_batch(
    db: Session,
    *,
    signal_ids: list[UUID],
    tenant_id: UUID,
    disposition: str,
    reviewed_by_user_id: UUID | None = None,
    reason: str | None = None,
) -> dict[str, list[str]]:
    """Bulk version of `review_harvested_signal`, used by "Apply All
    Non-Conflicting" so one round trip records every cleanly-applied
    signal's disposition instead of N. Still fully scoped to `tenant_id`
    and still validating `disposition` against the same closed vocabulary.

    Returns {"updated": [signal_id, ...], "not_found": [signal_id, ...]} so
    the caller (and RN) can tell which signals genuinely didn't exist / were
    already reviewed by someone else / belonged to a different tenant,
    rather than silently dropping them.
    """

    if disposition not in VALID_SIGNAL_REVIEW_DISPOSITIONS:
        raise ValueError(f"disposition must be one of {sorted(VALID_SIGNAL_REVIEW_DISPOSITIONS)}")

    now = datetime.now(timezone.utc)

    rows = (
        db.query(PatientHarvestedSignal)
        .filter(
            PatientHarvestedSignal.id.in_(signal_ids),
            PatientHarvestedSignal.tenant_id == tenant_id,
        )
        .all()
    )
    found_ids = {str(row.id) for row in rows}
    not_found = [str(sid) for sid in signal_ids if str(sid) not in found_ids]

    for row in rows:
        row.review_status = disposition
        row.reviewed_by_user_id = reviewed_by_user_id
        row.reviewed_at = now
        row.review_disposition_reason = reason

    db.commit()
    return {"updated": sorted(found_ids), "not_found": not_found}


# Every review_status value the state machine can hold today (see the
# REVIEW STATE MACHINE comment on PatientHarvestedSignal.review_status).
# Acceptance Analytics reports ONLY these persisted values -- it does not
# invent "MODIFIED" or "CONFLICTED" buckets, since neither is stored
# anywhere on the signal today. If those are needed later, that is a
# separate schema/design decision, not something this function should
# approximate from ephemeral, non-persisted state.
_KNOWN_REVIEW_STATUSES = ("NEW", "APPLIED", "DISMISSED", "PARTIALLY_APPLIED", "CONFLICT", "FAILED")


def get_structured_findings_acceptance_analytics(
    db: Session,
    *,
    tenant_id: UUID,
    patient_id: UUID | None = None,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
) -> dict[str, Any]:
    """Read-only rollup of harvested-signal review outcomes, computed
    entirely from the persisted `review_status` column (NEW / APPLIED /
    DISMISSED) and the persisted `structured_findings` concept codes on
    each signal. No new tables or columns -- every number here is derived
    from data that already exists.

    Dimensions returned:
      - by_status: counts of NEW / APPLIED / DISMISSED signals
      - by_concept: per concept_code counts + status breakdown
      - by_patient: per patient_id counts + status breakdown
      - application_rate: APPLIED / (APPLIED + DISMISSED), i.e. of the
        signals an RN has actually reviewed (excluding still-pending
        NEW ones), what fraction were applied to the chart. None when
        nothing has been reviewed yet, to avoid a misleading 0%/100%.

    Always scoped to `tenant_id`; `patient_id`/`start_date`/`end_date`
    further narrow the signals considered, but are all optional -- with
    none supplied this reports tenant-wide acceptance across all patients
    and all time.
    """

    query = db.query(PatientHarvestedSignal).filter(PatientHarvestedSignal.tenant_id == tenant_id)
    if patient_id is not None:
        query = query.filter(PatientHarvestedSignal.patient_id == patient_id)
    if start_date is not None:
        query = query.filter(PatientHarvestedSignal.recorded_at >= start_date)
    if end_date is not None:
        query = query.filter(PatientHarvestedSignal.recorded_at <= end_date)

    # Scope strictly to signals that actually carry >=1 structured
    # finding -- the review_status/reviewed_at columns are shared with the
    # broader narrative AI-signal review workflow (whose statuses include
    # ACKNOWLEDGED/ESCALATED, not just NEW/APPLIED/DISMISSED), so without
    # this filter "Structured Findings Acceptance Analytics" would silently
    # include unrelated narrative signals that were never part of this
    # feature at all.
    rows = [row for row in query.all() if row.structured_findings]

    def _empty_status_counts() -> dict[str, int]:
        return {status: 0 for status in _KNOWN_REVIEW_STATUSES}

    by_status = _empty_status_counts()
    by_concept: dict[str, dict[str, Any]] = {}
    by_patient: dict[str, dict[str, Any]] = {}

    for row in rows:
        status = row.review_status if row.review_status in _KNOWN_REVIEW_STATUSES else row.review_status
        by_status[status] = by_status.get(status, 0) + 1

        patient_key = str(row.patient_id)
        patient_bucket = by_patient.setdefault(
            patient_key, {"patient_id": patient_key, "total": 0, **_empty_status_counts()}
        )
        patient_bucket["total"] += 1
        patient_bucket[status] = patient_bucket.get(status, 0) + 1

        for finding in row.structured_findings or []:
            concept_code = finding.get("concept_code") if isinstance(finding, dict) else None
            if not concept_code:
                continue
            concept_bucket = by_concept.setdefault(
                concept_code, {"concept_code": concept_code, "total": 0, **_empty_status_counts()}
            )
            concept_bucket["total"] += 1
            concept_bucket[status] = concept_bucket.get(status, 0) + 1

    applied = by_status.get("APPLIED", 0)
    dismissed = by_status.get("DISMISSED", 0)
    reviewed = applied + dismissed
    application_rate = round(applied / reviewed, 4) if reviewed > 0 else None

    return {
        "total_signals": len(rows),
        "by_status": by_status,
        "by_concept": sorted(by_concept.values(), key=lambda c: c["concept_code"]),
        "by_patient": sorted(by_patient.values(), key=lambda p: p["patient_id"]),
        "reviewed_count": reviewed,
        "application_rate": application_rate,
    }


def get_rn_productivity_metrics(
    db: Session,
    *,
    tenant_id: UUID,
    patient_id: UUID | None = None,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
) -> dict[str, Any]:
    """Read-only RN Productivity Metrics, derived strictly from persisted
    data already used by Acceptance Analytics (PR #16) -- no new tables or
    columns, and deliberately NO time-saved estimate, since "seconds saved
    per field" is an assumption, not something ever recorded on a signal.

    Two counts, both scoped to signals with review_status == "APPLIED"
    and >=1 structured finding (same narrative-signal exclusion as
    get_structured_findings_acceptance_analytics):

      - fields_populated: total structured_findings entries across every
        APPLIED signal. Each entry corresponds to one concept-code write
        attempted against a RNICA field by applyStructuredFindings() on
        the frontend at apply time (the field itself may or may not have
        been blank at that moment -- this counts what was *offered* by an
        applied signal, since per-field apply/conflict outcomes are not
        persisted anywhere to count from instead).
      - manual_entries_avoided: count of APPLIED signals themselves --
        each one represents one harvested piece of documentation an RN
        reviewed and applied instead of re-transcribing it by hand.

    Always scoped to `tenant_id`; `patient_id`/`start_date`/`end_date`
    optionally narrow further, exactly like the Acceptance Analytics
    endpoint.
    """

    query = db.query(PatientHarvestedSignal).filter(
        PatientHarvestedSignal.tenant_id == tenant_id,
        PatientHarvestedSignal.review_status == "APPLIED",
    )
    if patient_id is not None:
        query = query.filter(PatientHarvestedSignal.patient_id == patient_id)
    if start_date is not None:
        query = query.filter(PatientHarvestedSignal.recorded_at >= start_date)
    if end_date is not None:
        query = query.filter(PatientHarvestedSignal.recorded_at <= end_date)

    # Same narrative-signal exclusion as Acceptance Analytics: only count
    # signals that actually carry structured findings.
    applied_rows = [row for row in query.all() if row.structured_findings]

    fields_populated = sum(len(row.structured_findings or []) for row in applied_rows)
    manual_entries_avoided = len(applied_rows)

    return {
        "fields_populated": fields_populated,
        "manual_entries_avoided": manual_entries_avoided,
    }



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
