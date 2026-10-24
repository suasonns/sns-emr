"""Reset a shared e2e fixture patient's skin-impairment carry-forward state.

Background: a wound record's clinical detail lives directly in
`RnicaAssessment.form_data->skin->wounds` (JSONB), while a separate
`skin_impairments` table tracks lifecycle identity/status (New/
Existing/Treat/Resolved/COC) so a real unresolved wound can never
silently disappear between visits (see
`backend/app/models/skin_impairment.py`). The backend's save path
appears to defensively re-merge any still-unresolved identity row back
into `form_data.skin.wounds` on save, so the Skin Impairment Workspace's
"Remove" button -- which only edits the current in-session draft
`wounds` array -- can click-and-autosave "remove" a record any number of
times without it ever durably disappearing, as long as its identity row
in `skin_impairments` has not itself been marked "Resolved".

For the shared e2e fixture patient (used by
`sns-emr-frontend/e2e/structured-wound-location.spec.ts`, which needs a
truly empty wound inventory at the start of every test) this script
performs the equivalent of a full, durable close-out:
  1. Marks every non-"Resolved" `skin_impairments` row "Resolved"
     (never deleting -- the model's own docstring requires resolved
     rows to remain searchable, reportable, and auditable), so the
     backend's save-time merge no longer reintroduces them, and
  2. Clears `form_data.skin.wounds` to `[]` on every `rnica_assessments`
     row for that patient, since with (1) already applied there is no
     longer any unresolved identity row that behavior depends on
     preserving -- this is purely a test-fixture reset, not a change to
     any application code path.

It is scoped to local/dev-test use only: as a safety guard, it refuses
to touch any patient whose `patient_type` is not an explicitly test/
demo/training-labeled record AND whose id does not match the documented
e2e fixture id, unless --force is passed.

Usage:
    python scripts/reset_e2e_skin_impairments.py <patient_id>
    python scripts/reset_e2e_skin_impairments.py <patient_id> --force
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# The one documented shared RNICA e2e fixture patient (see
# docs/INFECTION_ALLERGY_TEST_DATA_CLEANUP_REPORT.md). Any other patient
# id requires --force plus a TEST/DEMO/TRAINING patient_type match, to
# make it hard to accidentally point this at a real patient record.
KNOWN_E2E_FIXTURE_PATIENT_IDS = {"53fe69e1-fcd5-4b49-8203-9b890b18b7d6"}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("patient_id", help="Patient id whose skin_impairments rows should be resolved")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Allow a patient id outside the known e2e fixture allow-list, provided it is TEST/DEMO/TRAINING-labeled",
    )
    args = parser.parse_args()

    base_dir = Path(__file__).resolve().parents[1]
    load_dotenv(base_dir / ".env.local", override=False)
    load_dotenv(base_dir / ".env", override=False)

    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL is not set. Refusing to run without DB config.")

    engine = create_engine(database_url, future=True)
    with engine.begin() as conn:
        if args.patient_id not in KNOWN_E2E_FIXTURE_PATIENT_IDS:
            row = conn.execute(
                text("SELECT patient_type, mrn FROM patients WHERE id = :pid"),
                {"pid": args.patient_id},
            ).fetchone()
            is_test_labeled = bool(row) and (
                row[0] in ("TRAINING", "DEMO", "TEST") or (row[1] or "").startswith("TEST-")
            )
            if not (args.force and is_test_labeled):
                print(
                    "Refusing to reset: patient id is not the known e2e fixture patient and is not "
                    "TEST/DEMO/TRAINING-labeled. Pass --force only for a confirmed test/demo patient.",
                    file=sys.stderr,
                )
                return 1

        result = conn.execute(
            text(
                """
                UPDATE skin_impairments
                SET status = 'Resolved',
                    resolved_date = now()::date,
                    resolution_reason = 'e2e_test_fixture_reset',
                    resolution_narrative = 'Resolved via reset_e2e_skin_impairments.py -- synthetic e2e test fixture reset, not a clinical determination.'
                WHERE patient_id = :pid AND status != 'Resolved'
                """
            ),
            {"pid": args.patient_id},
        )
        print(f"rows resolved: {result.rowcount}")

        wounds_result = conn.execute(
            text(
                """
                UPDATE rnica_assessments
                SET form_data = jsonb_set(form_data, '{skin,wounds}', '[]'::jsonb)
                WHERE patient_id = :pid
                  AND form_data #> '{skin,wounds}' IS NOT NULL
                  AND form_data #> '{skin,wounds}' != '[]'::jsonb
                """
            ),
            {"pid": args.patient_id},
        )
        print(f"assessments cleared: {wounds_result.rowcount}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
