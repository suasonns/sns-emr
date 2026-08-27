"""Backfill & reprocessing for structured_findings on already-harvested
PatientHarvestedSignal rows (UCIER Phase 1).

Why this exists
----------------
`app.services.evidence.structured_findings` (the concept-aware
structured_findings extraction/validation layer) was added after many
`patient_harvested_signals` rows already existed. Those older rows carry
`structured_findings = []`, the same value a fresh row gets when the model
genuinely finds nothing -- so the empty list alone can't tell "never
processed by this pipeline" apart from "processed, nothing found". The
`structured_findings_status` / `_attempts` / `_last_attempted_at` /
`_last_error` columns on `PatientHarvestedSignal` (see
app.models.patient_evidence) resolve that ambiguity, and this module is the
only place that transitions those columns after the row's initial harvest.

This module NEVER re-ingests a new document. It only re-runs the current
extraction + validation pipeline (`ai_extraction_service.
extract_signals_with_diagnostics` / `structured_findings.validate_findings`)
against text a row already has stored (`original_text_excerpt`), which is
exactly the excerpt that originally produced that row's signal_text -- so a
reprocess pass is a pure "run today's smarter extraction over yesterday's
already-approved-as-evidence text", never new clinical documentation.

Safety / idempotency contract (see also PatientHarvestedSignal docstring):
    - A row whose `review_status != "NEW"` (an RN has already acted on it)
      is NEVER touched, even when `force=True`. RN disposition always wins.
    - A row whose `structured_findings_status == "COMPLETED"` is skipped
      unless `force=True` -- this is what makes re-running the exact same
      backfill/retry call a no-op the second time.
    - `structured_findings` is always fully REPLACED, never appended to,
      on a successful reprocess -- there is exactly one reprocess pass
      "in flight" per row at a time (no duplicate concept entries).
    - On success (including a legitimate zero-findings result):
      status -> COMPLETED, attempts += 1, last_attempted_at = now(),
      last_error cleared.
    - On failure (network error, timeout, malformed output, or any other
      exception -- this module, like ai_extraction_service, is designed to
      never raise, but still defends against it): status -> FAILED,
      attempts += 1, last_attempted_at = now(), error stored (truncated),
      and the row's existing `structured_findings` is left untouched (never
      clobber a possibly-good prior state with a failed attempt).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, asdict
from datetime import date, datetime, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.patient_evidence import PatientEvidenceRecord, PatientHarvestedSignal
from app.services.evidence.ai_extraction_service import extract_signals_with_diagnostics

logger = logging.getLogger("sns_emr")

# Only these structured_findings_status values are ever eligible for a
# reprocess pass without `force=True`. COMPLETED is only reachable via
# force=True (explicit re-run); RN-reviewed rows are never reachable at all.
REPROCESSABLE_STATUSES = ("PENDING", "FAILED")

MAX_ERROR_LEN = 2000


@dataclass
class ReprocessReport:
    """Structured, additive result of one reprocess call. Every public
    function in this module returns one of these (never raises)."""

    harvested_signals_count: int = 0
    structured_findings_generated_count: int = 0
    completed_count: int = 0
    failed_count: int = 0
    rejected_count: int = 0
    skipped_already_completed_count: int = 0
    skipped_rn_reviewed_count: int = 0
    skipped_other_count: int = 0

    @property
    def skipped_count(self) -> int:
        return (
            self.skipped_already_completed_count
            + self.skipped_rn_reviewed_count
            + self.skipped_other_count
        )

    def to_dict(self) -> dict:
        data = asdict(self)
        data["skipped_count"] = self.skipped_count
        return data

    def merge(self, other: "ReprocessReport") -> "ReprocessReport":
        self.harvested_signals_count += other.harvested_signals_count
        self.structured_findings_generated_count += other.structured_findings_generated_count
        self.completed_count += other.completed_count
        self.failed_count += other.failed_count
        self.rejected_count += other.rejected_count
        self.skipped_already_completed_count += other.skipped_already_completed_count
        self.skipped_rn_reviewed_count += other.skipped_rn_reviewed_count
        self.skipped_other_count += other.skipped_other_count
        return self


def _reprocess_signal(
    db: Session,
    signal: PatientHarvestedSignal,
    *,
    force: bool,
    report: ReprocessReport,
) -> None:
    """Reprocess exactly one row in place. Never raises -- any failure is
    captured onto the row's own structured_findings_last_error/_status."""

    report.harvested_signals_count += 1

    # RN disposition always wins, no exceptions -- not even with force=True.
    if signal.review_status != "NEW":
        report.skipped_rn_reviewed_count += 1
        return

    if signal.structured_findings_status == "COMPLETED" and not force:
        report.skipped_already_completed_count += 1
        return

    if signal.structured_findings_status not in REPROCESSABLE_STATUSES and not (
        force and signal.structured_findings_status == "COMPLETED"
    ):
        # Defensive: any status this module doesn't recognize is left alone
        # rather than guessed at.
        report.skipped_other_count += 1
        return

    text = (signal.original_text_excerpt or "").strip()
    if not text:
        # Fall back to the parent evidence record's full source text only
        # when this row somehow has no excerpt of its own (legacy/edge
        # case) -- normal rows always have their own excerpt, which is the
        # exact text that produced this specific signal.
        evidence_record: Optional[PatientEvidenceRecord] = signal.evidence_record
        text = (evidence_record.original_documentation if evidence_record else "") or ""

    now = datetime.now(timezone.utc)
    signal.structured_findings_attempts = (signal.structured_findings_attempts or 0) + 1
    signal.structured_findings_last_attempted_at = now

    try:
        extracted_signals, diagnostics = extract_signals_with_diagnostics(
            text=text,
            discipline=signal.source_discipline,
            note_type=None,
            source_type=signal.source_type,
        )
    except Exception as exc:  # pragma: no cover - defense in depth, mirrors ai_extraction_service contract
        signal.structured_findings_status = "FAILED"
        signal.structured_findings_last_error = str(exc)[:MAX_ERROR_LEN]
        report.failed_count += 1
        logger.exception(
            "structured_findings_reprocess: unexpected error harvested_signal_id=%s",
            signal.id,
        )
        return

    if not diagnostics.succeeded:
        # extract_signals_with_diagnostics never raises (same contract as
        # extract_signals), but a network/HTTP/parse error or missing Azure
        # OpenAI config still means no real extraction happened -- that is
        # a FAILED attempt, not a legitimate zero-findings result, so the
        # row's existing structured_findings (if any) is left untouched.
        signal.structured_findings_status = "FAILED"
        signal.structured_findings_last_error = (diagnostics.error or "extraction did not complete")[:MAX_ERROR_LEN]
        report.failed_count += 1
        return

    # The excerpt fed in is exactly this row's own excerpt (one isolated
    # narrative fragment), so every concept finding the model returns for it
    # belongs to this row -- flatten across whatever ExtractedSignal
    # entries came back rather than trying to re-match signal_key (a
    # re-extraction pass over the same short excerpt commonly reproduces
    # one signal, but is not guaranteed to reuse an identical signal_key).
    new_findings = [
        finding for extracted in extracted_signals for finding in extracted.structured_findings
    ]

    # Full replace, never append -- this is the only write path for
    # structured_findings once the concept-aware pipeline is involved.
    signal.structured_findings = new_findings
    signal.structured_findings_status = "COMPLETED"
    signal.structured_findings_last_error = None

    report.completed_count += 1
    report.structured_findings_generated_count += len(new_findings)
    report.rejected_count += diagnostics.rejected_findings_count


def _scope_query(
    db: Session,
    *,
    tenant_id: Optional[UUID] = None,
    patient_id: Optional[UUID] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
):
    """Every PatientHarvestedSignal in scope (tenant/patient/date), with NO
    status filtering at all. Used by reprocess_patient/reprocess_batch so
    the resulting ReprocessReport can accurately attribute every row to a
    reason (completed / RN-reviewed-skip / already-completed-skip) instead
    of silently excluding skip-worthy rows from the count. `recorded_at`
    (the underlying clinical documentation date) is used for date
    filtering rather than `created_at` (the harvest timestamp) -- an
    incremental rollout is more naturally described as "reprocess signals
    from documentation recorded in this date range" than "harvested in
    this date range", and it keeps behavior stable if a batch backfill is
    itself re-run days later.
    """

    query = db.query(PatientHarvestedSignal)
    if tenant_id is not None:
        query = query.filter(PatientHarvestedSignal.tenant_id == tenant_id)
    if patient_id is not None:
        query = query.filter(PatientHarvestedSignal.patient_id == patient_id)
    if start_date is not None:
        query = query.filter(PatientHarvestedSignal.recorded_at >= start_date)
    if end_date is not None:
        query = query.filter(PatientHarvestedSignal.recorded_at <= end_date)
    return query.order_by(PatientHarvestedSignal.recorded_at.asc(), PatientHarvestedSignal.id.asc())


def _run_over(
    db: Session,
    signals: list[PatientHarvestedSignal],
    *,
    force: bool,
) -> ReprocessReport:
    report = ReprocessReport()
    for signal in signals:
        _reprocess_signal(db, signal, force=force, report=report)
        # Flush (not commit) after each row so a later failure in the same
        # batch doesn't lose earlier in-memory progress if the caller
        # decides to commit incrementally; callers still control commit().
        db.flush()
    logger.info(
        "structured_findings_reprocess: %s",
        report.to_dict(),
    )
    return report


def reprocess_patient(
    db: Session,
    *,
    patient_id: UUID,
    tenant_id: UUID,
    force: bool = False,
) -> ReprocessReport:
    """Reprocess every eligible PatientHarvestedSignal for one patient.

    `force=True` also reprocesses rows already COMPLETED by this pipeline
    (explicit re-run, e.g. after a CONCEPT_REGISTRY change) -- it never
    bypasses the RN-reviewed skip rule.
    """

    signals = _scope_query(db, tenant_id=tenant_id, patient_id=patient_id).all()
    return _run_over(db, signals, force=force)


def reprocess_batch(
    db: Session,
    *,
    tenant_id: Optional[UUID] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    limit: Optional[int] = None,
    force: bool = False,
) -> ReprocessReport:
    """Reprocess every eligible PatientHarvestedSignal across a tenant (or
    all tenants if `tenant_id` is None), optionally scoped to a
    `recorded_at` date range, with an optional row-count `limit` for safe
    incremental rollout (e.g. backfilling in batches of a few hundred)."""

    query = _scope_query(
        db,
        tenant_id=tenant_id,
        start_date=start_date,
        end_date=end_date,
    )
    if limit is not None:
        query = query.limit(limit)
    signals = query.all()
    return _run_over(db, signals, force=force)


def retry_failed_and_pending(
    db: Session,
    *,
    tenant_id: Optional[UUID] = None,
    max_attempts: int = 3,
    limit: Optional[int] = None,
) -> ReprocessReport:
    """Find every PENDING/FAILED, non-RN-reviewed signal that hasn't yet
    exhausted `max_attempts` and reprocess it. Safe to invoke repeatedly
    (e.g. from a scheduled job or an admin action) without a human having
    to hand-pick which rows failed -- rows that have already hit
    `max_attempts` are left alone (no infinite retry loop) and rows that
    are already COMPLETED are untouched (this never uses force).

    Unlike reprocess_patient/reprocess_batch, this deliberately queries only
    the targeted PENDING/FAILED/under-attempt-cap subset (not the full
    scope) since its purpose is efficient, repeatable retry rather than
    full skip-reason observability -- rows already at the attempt cap are
    simply out of scope here, not reported as "skipped".
    """

    query = (
        db.query(PatientHarvestedSignal)
        .filter(
            PatientHarvestedSignal.review_status == "NEW",
            PatientHarvestedSignal.structured_findings_status.in_(REPROCESSABLE_STATUSES),
            PatientHarvestedSignal.structured_findings_attempts < max_attempts,
        )
        .order_by(PatientHarvestedSignal.recorded_at.asc(), PatientHarvestedSignal.id.asc())
    )
    if tenant_id is not None:
        query = query.filter(PatientHarvestedSignal.tenant_id == tenant_id)
    if limit is not None:
        query = query.limit(limit)
    signals = query.all()
    return _run_over(db, signals, force=False)
