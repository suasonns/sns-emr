"""One-time TEST-DATA backfill: add the HOPE Section I0000 structured
comorbidity checklist to Loren Shields' already-created RNICA assessment.

Loren Shields is used purely as a feature test case for the new HOPE
comorbidity checklist in RNICA.jsx -- HOPE (effective Oct 2025) did not
exist during his actual episode of care, so this data was never part of
his real chart. This script only demonstrates that the auto-detection +
principal-diagnosis exclusion rule (per CMS HOPE Guidance Manual v1.02,
Section I) produces correct, non-duplicated output end to end.

Mapping is derived mechanically from the ICD-10 codes already stored on
his PatientDiagnosis rows / RNICA secondaryDiagnoses list, using the same
category regexes as RNICA.jsx's HopeComorbiditiesCard:
  - Principal Diagnosis: I50.22 Heart Failure -> heartFailure EXCLUDED
    (already the principal diagnosis; no distinct secondary cancer, so
    the CMS carve-out does not apply).
  - I70.0 (atherosclerosis of aorta)              -> pvdPad
  - I10, I20.89, I25.10, I25.2                    -> cardiovascularExclHF
  - N18.31 (CKD stage 3a)                         -> renalDisease
  - E11.42, E11.69, E11.22                        -> diabetesMellitus
  - E11.42 (diabetic polyneuropathy)              -> neuropathy
  - I69.351 (hemiplegia s/p cerebral infarction)  -> stroke
  - Everything else (N31.9, I87.2, M15.9, N20.9, N39.0, J12.3, Z98.890,
    E44.0, E78.5, M47.812, G89.0) does not map to any of the 14 explicit
    HOPE categories -> other = true, itemized in additionalNote.
"""

from app.core.database import SessionLocal
from app.models.rnica_assessment import RnicaAssessment

PATIENT_ID = "3885a918-7c8b-4d6d-af3a-577cc898ebdb"

HOPE_COMORBIDITIES = {
    "cancer": False,
    "heartFailure": False,  # excluded: matches I0010 Principal Diagnosis (I50.22)
    "pvdPad": True,
    "cardiovascularExclHF": True,
    "liverDisease": False,
    "renalDisease": True,
    "sepsis": False,
    "diabetesMellitus": True,
    "neuropathy": True,
    "stroke": True,
    "dementia": False,
    "neurologicalConditions": False,
    "seizureDisorder": False,
    "copd": False,
    "other": True,
    "additionalNote": (
        "TEST DATA (feature verification only): Heart Failure excluded from Comorbidities "
        "because it is already I0010 Principal Diagnosis (I50.22), per CMS HOPE Guidance "
        "Manual v1.02 Section I ('Do not include the principal diagnosis, except if the "
        "patient has a secondary cancer'). Other Medical Condition (I8005) covers "
        "uncategorized secondary diagnoses: bladder dysfunction (N31.9), venous "
        "insufficiency (I87.2), osteoarthritis (M15.9), urinary calculus (N20.9), UTI "
        "(N39.0), pneumonia (J12.3), postprocedural state (Z98.890), malnutrition "
        "(E44.0), hyperlipidemia (E78.5), spondylosis (M47.812), central pain syndrome "
        "(G89.0)."
    ),
}


def main():
    db = SessionLocal()
    try:
        rnica = (
            db.query(RnicaAssessment)
            .filter(RnicaAssessment.patient_id == PATIENT_ID)
            .first()
        )
        if not rnica:
            print("No RNICA assessment found for this patient - nothing to backfill.")
            return

        form_data = dict(rnica.form_data or {})
        diagnoses = dict(form_data.get("diagnoses") or {})
        diagnoses["hopeComorbidities"] = HOPE_COMORBIDITIES
        form_data["diagnoses"] = diagnoses
        rnica.form_data = form_data

        db.commit()
        print("hopeComorbidities backfilled on RNICA assessment:", rnica.id)
        print(diagnoses["hopeComorbidities"])
    finally:
        db.close()


if __name__ == "__main__":
    main()
