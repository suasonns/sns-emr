"""CLI entrypoint for backfilling / reprocessing structured_findings on
already-harvested PatientHarvestedSignal rows.

See app.services.evidence.structured_findings_reprocess_service for the
underlying safety/idempotency contract (RN-reviewed rows are never
touched; already-COMPLETED rows are a no-op unless --force is passed).

Usage:
    # One patient
    python -m app.scripts.reprocess_structured_findings \
        --patient-id 3ea2f6fa-8dd9-4e3c-9b7d-009ddbe17ab0 \
        --tenant-id 01271980-0000-0000-0000-000005101977 \
        --commit

    # Batch backfill across a tenant, date-range limited, incremental
    python -m app.scripts.reprocess_structured_findings \
        --all --tenant-id <tenant-uuid> \
        --start-date 2026-01-01 --end-date 2026-08-27 \
        --limit 200 --commit

    # Automatic retry of anything still PENDING/FAILED under attempt cap
    python -m app.scripts.reprocess_structured_findings \
        --retry-failed --max-attempts 3 --commit

Default mode is DRY RUN (matches this repo's other backfill scripts, e.g.
backfill_med_recon_duplicate_backlog.py) -- pass --commit to persist. Note
that any mode that actually reaches the AI extraction step still makes a
live Azure OpenAI call regardless of --commit (the network call itself has
no "dry run"); --commit only controls whether the resulting DB changes are
persisted or rolled back.
"""

from __future__ import annotations

import argparse
import logging
import sys
import uuid
from datetime import date, datetime
from typing import Optional

# Force-load all models so SQLAlchemy relationships resolve, matching the
# convention used by the other app/scripts/backfill_*.py entrypoints.
import app.models  # noqa: F401

try:
    from app.db.session import SessionLocal
except Exception:
    from app.core.database import SessionLocal  # fallback used elsewhere in SNS EMR

from app.services.evidence.structured_findings_reprocess_service import (
    ReprocessReport,
    reprocess_batch,
    reprocess_patient,
    retry_failed_and_pending,
)

logger = logging.getLogger("sns_emr")


def _configure_logging(verbose: bool) -> None:
    level = logging.INFO if verbose else logging.WARNING
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )


def _parse_uuid(value: Optional[str], *, flag: str) -> Optional[uuid.UUID]:
    if not value:
        return None
    try:
        return uuid.UUID(str(value))
    except ValueError as exc:
        raise SystemExit(f"Invalid {flag}: {exc}") from exc


def _parse_date(value: Optional[str], *, flag: str) -> Optional[date]:
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError as exc:
        raise SystemExit(f"Invalid {flag} (expected YYYY-MM-DD): {exc}") from exc


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Backfill/reprocess structured_findings on already-harvested "
            "PatientHarvestedSignal rows using the current concept-aware "
            "extraction pipeline. Default mode is DRY RUN; pass --commit to persist."
        )
    )
    mode_group = parser.add_mutually_exclusive_group(required=True)
    mode_group.add_argument(
        "--patient-id",
        help="Reprocess every eligible signal for one patient (requires --tenant-id).",
    )
    mode_group.add_argument(
        "--all",
        action="store_true",
        help="Batch mode: reprocess every eligible signal across the given scope "
        "(optionally --tenant-id / --start-date / --end-date / --limit).",
    )
    mode_group.add_argument(
        "--retry-failed",
        action="store_true",
        help="Retry every PENDING/FAILED signal under --max-attempts "
        "(optionally scoped by --tenant-id / --limit).",
    )

    parser.add_argument("--tenant-id", help="Tenant UUID to scope the run to.")
    parser.add_argument(
        "--start-date", help="YYYY-MM-DD; only signals with recorded_at >= this date."
    )
    parser.add_argument(
        "--end-date", help="YYYY-MM-DD; only signals with recorded_at <= this date."
    )
    parser.add_argument(
        "--limit", type=int, default=None, help="Max rows to process in one run."
    )
    parser.add_argument(
        "--max-attempts",
        type=int,
        default=3,
        help="Only used with --retry-failed. Rows at/above this attempt count are skipped.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Also reprocess rows already COMPLETED by this pipeline (never bypasses "
        "the RN-reviewed skip rule). Only valid with --patient-id or --all.",
    )
    parser.add_argument(
        "--commit",
        action="store_true",
        help="Persist changes. Without this flag, the script performs a dry run and rolls back.",
    )
    parser.add_argument("--verbose", action="store_true", help="Enable INFO-level logging")

    args = parser.parse_args()
    _configure_logging(args.verbose)

    if args.patient_id and not args.tenant_id:
        print("--patient-id requires --tenant-id", file=sys.stderr)
        return 2
    if args.force and args.retry_failed:
        print("--force is not applicable to --retry-failed (it never re-runs COMPLETED rows)", file=sys.stderr)
        return 2

    tenant_uuid = _parse_uuid(args.tenant_id, flag="--tenant-id")
    patient_uuid = _parse_uuid(args.patient_id, flag="--patient-id")
    start_date = _parse_date(args.start_date, flag="--start-date")
    end_date = _parse_date(args.end_date, flag="--end-date")

    db = SessionLocal()
    try:
        if patient_uuid is not None:
            report: ReprocessReport = reprocess_patient(
                db, patient_id=patient_uuid, tenant_id=tenant_uuid, force=args.force
            )
            mode = "PATIENT"
        elif args.retry_failed:
            report = retry_failed_and_pending(
                db, tenant_id=tenant_uuid, max_attempts=args.max_attempts, limit=args.limit
            )
            mode = "RETRY_FAILED"
        else:
            report = reprocess_batch(
                db,
                tenant_id=tenant_uuid,
                start_date=start_date,
                end_date=end_date,
                limit=args.limit,
                force=args.force,
            )
            mode = "BATCH"

        if args.commit:
            db.commit()
            action = "COMMITTED"
        else:
            db.rollback()
            action = "DRY_RUN_ROLLED_BACK"

        print({"mode": mode, "action": action, **report.to_dict()})
        return 0
    except Exception as exc:
        db.rollback()
        print(f"Reprocess failed: {exc}", file=sys.stderr)
        return 1
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())
