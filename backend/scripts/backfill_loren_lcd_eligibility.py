"""
One-time data-correction script: backfill structured LCD Heart Failure
eligibility criteria (checklist answers) onto Loren Shields' locked RN ICA
assessment (id 9cd5c9e9-b20c-43c5-8d08-78660e90da5f, patient_id
c4410e1f-8ca7-4635-900e-9883e8aca122).

Why this is needed:
- The record's form_data.diagnoses.ndsEligibility.criteriaAnswers/
  criteriaFacts were both empty ({}), so the Compliance LCD Eligibility
  view showed "0 answers / 0 facts" instead of the real Yes/No checklist
  the source assessment documents.
- detectedDisease was persisted as "GENERAL_DECLINE_TERMINAL_STATUS", but
  Loren's primary diagnosis is I50.22 (Chronic systolic congestive heart
  failure), which app.services.eligibility.engine's ICD-10 prefix map
  (_ICD10_PREFIX_MAP["HEART_FAILURE"] includes "I50") correctly resolves
  to HEART_FAILURE today. The stale GENERAL_DECLINE value on this record
  pre-dates that detection working correctly (or the record was created
  before the ICD-10-based detection path existed) -- it is not a genuine
  fallback determination, so it is corrected here rather than left as-is.

Sourcing (no fabrication -- every answer below is read directly from the
real HospiceMD RN Comprehensive Nursing Assessment for Loren Shields,
5/22/2024, transcribed in
session-state/files/rn_assessment_extracted.txt, "2. NYHA classification"
/ "3. History/Progression - Supporting Factor" checklist, lines ~400-424):

  Question                                                    Documented answer
  1a. Ruled out as surgical candidate?                        Yes   -> True
  1b. Declined surgical procedures?                            (blank/"Select") -> None (not documented)
  1c. Optimally treated w/ diuretics and vasodilators?         Yes   -> True
  1d. Unable to be on vasodilators (other condition)?          (blank/"Select") -> None (not documented)
  2a. Meets NYHA Class IV?                                     Yes   -> True   (also: "COMORBIDITIES" section states NYHA IV directly)
  2b. Ejection fraction < 20 (if available)?                   (blank/"Select") -> None (not documented -- no EF value in the source assessment)
  3a. Hx treatment-resistant arrhythmias?                      (blank/"Select") -> None (not documented)
  3b. Hx cardiac arrest/resuscitation?                         (blank/"Select") -> None (not documented)
  3c. Hx unexplained syncope/fainting?                         Yes   -> True   ("Patient has history of unexplained syncope/fainting" -- narrative)
  3d. Brain embolism of cardiac origin?                        (blank/"Select") -> None (not documented)
  3e. Concomitant HIV disease?                                 (blank/"Select") -> None (not documented)

Values are real booleans (True/False/None), matching
components/RNICA.jsx's LcdTernaryButtons convention (true/false/null) and
app.services.eligibility.engine._compare's EQUALS operator (which compares
against Python True, not the string "yes"). criteriaFacts is left empty
because the source assessment does not document a numeric ejection
fraction, serum albumin, etc. for Loren -- inventing a number here would
violate the "no fabricated clinical data" policy.

Run with: python scripts/backfill_loren_lcd_eligibility.py
"""
from app.core.database import SessionLocal
from app.models.rnica_assessment import RnicaAssessment

RNICA_ID = "9cd5c9e9-b20c-43c5-8d08-78660e90da5f"
PATIENT_ID = "c4410e1f-8ca7-4635-900e-9883e8aca122"

HEART_FAILURE_CRITERIA_ANSWERS = {
    "1a": True,
    "1b": None,
    "1c": True,
    "1d": None,
    "2a": True,
    "2b": None,
    "3a": None,
    "3b": None,
    "3c": True,
    "3d": None,
    "3e": None,
}


def main():
    db = SessionLocal()
    try:
        record = (
            db.query(RnicaAssessment)
            .filter(RnicaAssessment.id == RNICA_ID, RnicaAssessment.patient_id == PATIENT_ID)
            .first()
        )
        if record is None:
            raise SystemExit(f"RnicaAssessment {RNICA_ID} for patient {PATIENT_ID} not found")

        form_data = dict(record.form_data or {})
        diagnoses = dict(form_data.get("diagnoses") or {})
        diagnoses["ndsEligibility"] = {
            "detectedDisease": "HEART_FAILURE",
            "criteriaAnswers": {"HEART_FAILURE": HEART_FAILURE_CRITERIA_ANSWERS},
            "criteriaFacts": {"HEART_FAILURE": {}},
        }
        form_data["diagnoses"] = diagnoses
        record.form_data = form_data

        # SQLAlchemy doesn't auto-detect in-place mutation of JSONB columns;
        # this record is locked, so a normal API PUT would be rejected anyway
        # (see app/api/visits.py::update_rnica_assessment) -- this one-time
        # script bypasses that guard deliberately for a documented data
        # correction, not a live edit.
        from sqlalchemy.orm.attributes import flag_modified

        flag_modified(record, "form_data")
        db.commit()
        print(f"Backfilled LCD eligibility criteria for RNICA {RNICA_ID} (HEART_FAILURE, 3 Yes / 8 unknown)")
    finally:
        db.close()


if __name__ == "__main__":
    main()
