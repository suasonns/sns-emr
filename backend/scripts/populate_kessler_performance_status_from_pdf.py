"""Populate Margaret Kessler's KPS/PPS/FAST performance-status fields from
her real, already-uploaded source document "kessler_hnp_chart_consents.pdf"
(Love & Faith Hospice Services, Inc. dementia LCD eligibility worksheet,
"Nature & Condition of Terminal Illness / LCD Eligibility" section, MR#
062512-396).

Root cause this script fixes (found 2026-09-08 while tracing the "Kessler
FAST missing" gap for the Demo Readiness Report,
docs/planning/demo_readiness_thursday.md): the source PDF was already
uploaded, ingested, and OCR'd -- the raw extracted text literally contains
"KPS 30 7-E FAST PPS 30 NYHA" (a table whose columns/values were flattened
out of visual order by OCR extraction: KPS=30, FAST=7-E, PPS=30, NYHA=blank
in the source). This is a genuine, previously-uploaded value that was never
transcribed into the structured RnicaAssessment.form_data.performanceStatus
fields -- it is NOT a case of missing source data, and it is NOT invented
here. Contrast with Norma Suarez, whose evidence records contain no ECOG
value anywhere (checked and confirmed absent) -- that remains a documented
open gap, not something to fabricate a value for.

What this script does:
  1. Reads Kessler's existing RnicaAssessment row (already created; this
     script does not create a new assessment).
  2. Sets performanceStatus.kps = "30", performanceStatus.pps = "30%",
     performanceStatus.fast = "7e" (normalized lowercase per
     scale_interpretations.py's FAST key convention), each with a
     justification quoting the literal source table.
  3. Does NOT set NYHA -- the source table shows no NYHA value for Kessler
     (blank in the same row), consistent with a dementia (not cardiac)
     primary diagnosis; leaving it blank is the correct, non-fabricated
     state.
  4. Does NOT touch medications, diagnoses, or any other RNICA section.

Idempotent: if performanceStatus.kps/pps/fast are already non-blank, the
script reports the existing values and makes no changes.
"""

from __future__ import annotations

import uuid

from dotenv import load_dotenv

load_dotenv()

from sqlalchemy.orm.attributes import flag_modified

from app.core.database import SessionLocal
from app.models.rnica_assessment import RnicaAssessment

ASSESSMENT_ID = uuid.UUID("5d39cc37-19a2-4e83-a1dc-46c8dcefc94b")

SOURCE_CITATION = (
    'Source: kessler_hnp_chart_consents.pdf, "Nature & Condition of Terminal '
    'Illness / LCD Eligibility" worksheet -- literal extracted table text: '
    '"KPS/PPS/FAST/NYHA score effecting ADL? KPS 30 7-E FAST PPS 30 NYHA" '
    "(dementia due to Alzheimer's LCD determination)."
)

NEW_VALUES = {
    "kps": "30",
    "kpsJustification": (
        "Disabled; requires special care and assistance. " + SOURCE_CITATION
    ),
    "pps": "30%",
    "ppsJustification": (
        "Mostly in bed, unable to do any work, extensive disease, may have "
        "some intake, may be fully conscious or drowsy/confused. "
        + SOURCE_CITATION
    ),
    # "fast" is the coded FAST stage select value (per scale_interpretations.py
    # FAST_SCALE key convention); "fastStage" is the free-text stage
    # description field the RNICA form pairs with it (RNICA.jsx: "FAST Stage
    # Description", path "fastStage") -- there is no separate justification
    # field for FAST in this schema.
    "fast": "7e",
    "fastStage": (
        "No longer able to smile (FAST stage 7e), consistent with end-stage "
        "Alzheimer's dementia. " + SOURCE_CITATION
    ),
}


def main() -> None:
    db = SessionLocal()
    try:
        record = (
            db.query(RnicaAssessment)
            .filter(RnicaAssessment.id == ASSESSMENT_ID)
            .first()
        )
        if not record:
            print(f"RnicaAssessment {ASSESSMENT_ID} not found -- nothing done.")
            return

        perf = dict((record.form_data or {}).get("performanceStatus") or {})
        already_set = {
            k: perf.get(k)
            for k in ("kps", "pps", "fast")
            if (perf.get(k) or "").strip()
        }
        if already_set:
            print(
                "performanceStatus already has values, skipping (idempotent): "
                f"{already_set}"
            )
            return

        perf.update(NEW_VALUES)
        record.form_data = dict(record.form_data or {})
        record.form_data["performanceStatus"] = perf
        flag_modified(record, "form_data")
        db.commit()
        print(
            "Updated Kessler performanceStatus: kps=30, pps=30%, fast=7e "
            "(NYHA intentionally left blank -- not present in source)."
        )
    finally:
        db.close()


if __name__ == "__main__":
    main()
