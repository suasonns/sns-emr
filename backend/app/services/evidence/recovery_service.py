"""Phase A durability: recovery sweep for the document-intelligence /
structured-findings pipeline.

Problem this solves: an RN may upload a document (or the app may retry an
upload) while connectivity is marginal, then the RN loses signal before
`run_document_intelligence` (a FastAPI BackgroundTasks job -- in-process,
NOT a durable external queue) ever runs, or while it is mid-flight. If the
server process restarts, or the AI service times out, that document is
left in a PENDING or PROCESSING or FAILED state forever unless something
notices and re-drives it.

This module is that "something": `find_recoverable_documents()` finds
every document stuck in a state that means real clinical work (structured
findings, RNICA population) has not yet completed, and
`recover_documents()` safely re-runs `run_document_intelligence` for each
one. Both the pipeline job (idempotent, see document_harvest_job.py) and
the harvest step (idempotent via a DB unique constraint, see
harvest_service.py) guarantee this can be called any number of times
without ever producing duplicate structured findings or duplicate RNICA
writes.

Three ways this sweep gets triggered (see app/main.py and
app/api/documents.py):
    1. Once at server startup -- catches anything orphaned by a crash or
       deploy restart.
    2. On a periodic interval (RECOVERY_SWEEP_INTERVAL_SECONDS) -- catches
       transient failures (AI service downtime) independent of any
       client action.
    3. On demand via POST /documents/recover-pending -- lets the RN's
       client request an immediate resume the moment connectivity comes
       back, rather than waiting for the periodic sweep.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from app.models.document_record import DocumentRecord

logger = logging.getLogger("sns_emr")

# A PROCESSING row whose processing_started_at is older than this is
# assumed to have died mid-flight (server crash/restart) rather than
# still being legitimately worked on -- FastAPI BackgroundTasks jobs run
# well within this window under normal conditions.
STUCK_PROCESSING_TIMEOUT_MINUTES = 15

# Matches document_harvest_job.MAX_PROCESSING_ATTEMPTS -- kept as its own
# constant here (rather than importing) to avoid a needless second entry
# point behaving differently if that module changes independently later;
# both should be updated together if the retry policy changes.
MAX_PROCESSING_ATTEMPTS = 5


@dataclass
class RecoverableDocument:
    document_id: UUID
    tenant_id: UUID
    processing_status: str
    processing_attempts: int
    last_processing_error: str | None


def find_recoverable_documents(
    db: Session,
    *,
    tenant_id: UUID | None = None,
    stuck_after_minutes: int = STUCK_PROCESSING_TIMEOUT_MINUTES,
    max_attempts: int = MAX_PROCESSING_ATTEMPTS,
    limit: int = 200,
) -> list[RecoverableDocument]:
    """Return every document whose processing has not durably completed
    and is safe/worthwhile to retry.

    A document is recoverable if it is:
      - PENDING: never started (e.g. the background task was scheduled
        but the process restarted before FastAPI ever ran it), or
      - PROCESSING but stuck: started, but processing_started_at is older
        than `stuck_after_minutes` -- almost certainly means the process
        died mid-run rather than still legitimately working, or
      - FAILED with attempts remaining: raised an exception on a prior
        attempt, but hasn't exhausted `max_attempts` yet.

    FAILED documents that have exhausted max_attempts are deliberately
    excluded -- those need a human to look at last_processing_error, not
    another automatic retry.
    """

    stuck_cutoff = datetime.now(timezone.utc) - timedelta(minutes=stuck_after_minutes)

    query = db.query(DocumentRecord).filter(
        or_(
            DocumentRecord.processing_status == "PENDING",
            and_(
                DocumentRecord.processing_status == "PROCESSING",
                or_(
                    DocumentRecord.processing_started_at.is_(None),
                    DocumentRecord.processing_started_at < stuck_cutoff,
                ),
            ),
            and_(
                DocumentRecord.processing_status == "FAILED",
                DocumentRecord.processing_attempts < max_attempts,
            ),
        )
    )
    if tenant_id is not None:
        query = query.filter(DocumentRecord.tenant_id == tenant_id)

    rows = query.order_by(DocumentRecord.uploaded_at.asc()).limit(limit).all()

    return [
        RecoverableDocument(
            document_id=row.id,
            tenant_id=row.tenant_id,
            processing_status=row.processing_status,
            processing_attempts=row.processing_attempts or 0,
            last_processing_error=row.last_processing_error,
        )
        for row in rows
    ]


def recover_documents(
    db: Session,
    *,
    tenant_id: UUID | None = None,
    stuck_after_minutes: int = STUCK_PROCESSING_TIMEOUT_MINUTES,
    max_attempts: int = MAX_PROCESSING_ATTEMPTS,
    limit: int = 200,
) -> dict[str, object]:
    """Find and re-drive every recoverable document.

    Returns a summary dict (never raises -- each document's failure is
    isolated and logged, exactly like a normal first-attempt failure)
    suitable for both the periodic sweep's log line and the on-demand
    recovery endpoint's response body, so an RN's client (or support)
    gets visible confirmation of what was resumed.
    """

    from app.services.evidence.document_harvest_job import run_document_intelligence

    candidates = find_recoverable_documents(
        db,
        tenant_id=tenant_id,
        stuck_after_minutes=stuck_after_minutes,
        max_attempts=max_attempts,
        limit=limit,
    )

    recovered: list[str] = []
    still_failed: list[str] = []

    for candidate in candidates:
        try:
            run_document_intelligence(document_id=candidate.document_id)
        except Exception:
            # run_document_intelligence already catches and records its
            # own failures internally -- this is defense in depth only,
            # for something unexpected escaping that contract.
            logger.exception(
                "recovery_sweep: unexpected error recovering document_id=%s",
                candidate.document_id,
            )
            still_failed.append(str(candidate.document_id))
            continue

        db.expire_all()
        refreshed = db.query(DocumentRecord).filter(DocumentRecord.id == candidate.document_id).one_or_none()
        if refreshed is not None and refreshed.processing_status == "COMPLETE":
            recovered.append(str(candidate.document_id))
        else:
            still_failed.append(str(candidate.document_id))

    if candidates:
        logger.info(
            "recovery_sweep: examined=%s recovered=%s still_failed=%s",
            len(candidates),
            len(recovered),
            len(still_failed),
        )

    return {
        "examined": len(candidates),
        "recovered": recovered,
        "still_failed": still_failed,
    }
