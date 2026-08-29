"""CLI entrypoint for the append-only evidence re-sweep backfill.

See app.services.evidence.evidence_resweep_service for the underlying
safety contract (append-only, deduped by signal_key/excerpt, never
touches an existing PatientHarvestedSignal row).

Usage:
    # Dry run (default) -- shows what WOULD be added, writes nothing
    python -m app.scripts.resweep_evidence_extraction \
        --patient-id ba24830e-19f8-4b84-bbf3-e88374a6db25 \
        --tenant-id 01271980-0000-0000-0000-005101977

    # Persist
    python -m app.scripts.resweep_evidence_extraction \
        --patient-id ba24830e-19f8-4b84-bbf3-e88374a6db25 \
        --tenant-id 01271980-0000-0000-0000-005101977 \
        --commit
"""

from __future__ import annotations

import argparse
import logging
import sys
import uuid

import app.models  # noqa: F401

try:
    from app.db.session import SessionLocal
except Exception:
    from app.core.database import SessionLocal  # fallback used elsewhere in SNS EMR

from app.services.evidence.evidence_resweep_service import resweep_patient

logger = logging.getLogger("sns_emr")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--patient-id", required=True, type=uuid.UUID)
    parser.add_argument("--tenant-id", required=True, type=uuid.UUID)
    parser.add_argument("--commit", action="store_true", help="Persist changes (default: dry run)")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

    db = SessionLocal()
    try:
        report = resweep_patient(
            db,
            patient_id=args.patient_id,
            tenant_id=args.tenant_id,
            commit=args.commit,
        )
    finally:
        db.close()

    print(f"mode: {'COMMIT' if args.commit else 'DRY RUN'}")
    print(f"evidence_records_seen: {report.evidence_records_seen}")
    print(f"evidence_records_processed: {report.evidence_records_processed}")
    print(f"evidence_records_skipped_unconfigured: {report.evidence_records_skipped_unconfigured}")
    print(f"new_signals_added: {report.new_signals_added}")
    print(f"new_structured_findings_added: {report.new_structured_findings_added}")
    print(f"duplicate_signals_skipped: {report.duplicate_signals_skipped}")
    if report.errors:
        print(f"errors ({len(report.errors)}):")
        for err in report.errors:
            print(f"  - {err}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
