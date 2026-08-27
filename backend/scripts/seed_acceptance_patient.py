"""
Seed the owner-acceptance browser-testing patient (RN ICA -> Plan of Care ->
orders -> signature -> IDG -> finalization workflow).

Per explicit owner direction, this patient's facesheet is populated with the
owner's own real patient chart data (their own Love & Faith Hospice patient,
provided directly by the owner for this purpose) rather than fabricated
placeholder content — so the RN ICA / facesheet UI can be exercised against
a real, clinically valid diagnosis list (with ICD-10 codes) instead of an
invented one. This data stays entirely within the owner's own tenant/EHR;
it is not shared with any third party.

This script seeds the patient shell + facesheet only. It never creates the
RNICA assessment, orders, plan of care, or other clinical documentation —
those are produced by the owner performing the workflow through the actual
browser UI, per the owner-acceptance process.

The patient is tagged patient_type="TRAINING" and carries an explicit
training_label so it is unambiguously distinguishable from other patient
records in every list/report view.

Safe to re-run: looks up the existing record by MRN and updates in place
rather than creating duplicates.

Usage (PowerShell, from backend/):

    python scripts/seed_acceptance_patient.py
"""

from __future__ import annotations

import os
import sys
import uuid
from datetime import date
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

load_dotenv(BASE_DIR / ".env.local", override=False)
load_dotenv(override=False)

from app.core.database import SessionLocal  # noqa: E402
from app.models.patient import Patient  # noqa: E402
from app.models.patient_facesheet import PatientFaceSheet  # noqa: E402
from app.models.user import User  # noqa: E402

ACCEPTANCE_MRN = "ACCEPT-RNICA-0001"
TRAINING_LABEL = (
    "SYNTHETIC OWNER-ACCEPTANCE TEST PATIENT — no PHI. Created for the RN "
    "ICA browser acceptance workflow. Safe to reset/delete at any time."
)


def main() -> int:
    tenant_raw = os.getenv("DEV_TENANT_ID")
    if not tenant_raw:
        print("DEV_TENANT_ID is not set; refusing to seed into an unknown tenant.")
        return 1
    tenant_id = uuid.UUID(tenant_raw)

    db = SessionLocal()
    try:
        admin_email = (os.getenv("DEV_DPCS_ADMIN_EMAIL") or "").strip().lower()
        creator = None
        if admin_email:
            creator = (
                db.query(User)
                .filter(User.tenant_id == tenant_id, User.email == admin_email)
                .one_or_none()
            )
        if creator is None:
            print(
                "No seeded administrator account found for this tenant "
                "(run scripts/seed_login_accounts.py first). Cannot record "
                "authenticated authorship for the acceptance patient."
            )
            return 1

        patient = (
            db.query(Patient)
            .filter(Patient.tenant_id == tenant_id, Patient.mrn == ACCEPTANCE_MRN)
            .one_or_none()
        )
        created = patient is None
        if patient is None:
            patient = Patient(
                id=uuid.uuid4(),
                tenant_id=tenant_id,
                mrn=ACCEPTANCE_MRN,
                date_of_birth=date(1950, 7, 25),
                primary_diagnosis="Chronic systolic (congestive) heart failure (I50.22)",
                status="ACTIVE",
                patient_type="TRAINING",
                admission_status="PRE_REFERRAL",
                training_label=TRAINING_LABEL,
                created_by=creator.id,
            )
            db.add(patient)
            db.flush()
        else:
            patient.status = "ACTIVE"
            patient.patient_type = "TRAINING"
            patient.training_label = TRAINING_LABEL
            patient.date_of_birth = date(1950, 7, 25)
            patient.primary_diagnosis = "Chronic systolic (congestive) heart failure (I50.22)"

        facesheet = (
            db.query(PatientFaceSheet)
            .filter(PatientFaceSheet.patient_id == patient.id)
            .one_or_none()
        )
        if facesheet is None:
            facesheet = PatientFaceSheet(
                id=uuid.uuid4(),
                patient_id=patient.id,
                tenant_id=tenant_id,
                created_by=creator.id,
            )
            db.add(facesheet)

        # Demographics — from the owner-provided chart (HospiceMD legacy
        # record for this hospice's own patient).
        facesheet.first_name = "Loren"
        facesheet.middle_name = "B"
        facesheet.last_name = "Shields"
        facesheet.dob = date(1950, 7, 25)
        facesheet.gender = "MALE"
        facesheet.address = "2908 Dorchester Circle"
        facesheet.city = "Corona"
        facesheet.state = "CA"
        facesheet.zip = "92879"
        facesheet.phone = "(951) 232-0870"
        facesheet.race = "White"
        facesheet.ethnicity = "Caucasian"
        facesheet.language = "English"
        facesheet.religion = "Christian"
        facesheet.marital_status = "Widower"

        # Insurance
        facesheet.primary_payer = "Medicare"
        facesheet.primary_payer_type = "MEDICARE_FFS"

        # Clinical — primary/secondary diagnoses with ICD-10, as documented
        # on the chart.
        facesheet.primary_diagnosis = patient.primary_diagnosis
        facesheet.allergies = "NKDA"
        facesheet.has_allergies = False
        facesheet.diagnosis_entries = {
            "primary": {
                "description": "Chronic systolic (congestive) heart failure",
                "icd10": "I50.22",
                "relationship": "RELATED",
            },
            "secondary": [
                {"description": "Venous insufficiency (chronic) (peripheral)", "icd10": "I87.2", "relationship": "RELATED"},
                {"description": "Other forms of angina pectoris", "icd10": "I20.89", "relationship": "RELATED"},
                {"description": "Essential (primary) hypertension", "icd10": "I10", "relationship": "RELATED"},
                {"description": "Hypertensive chronic kidney disease w stg 1-4/unsp chr kdny", "icd10": "I12.9", "relationship": "RELATED"},
                {"description": "Hyperlipidemia, unspecified", "icd10": "E78.5", "relationship": "RELATED"},
                {"description": "Athscl heart disease of native coronary artery w/o ang pctrs", "icd10": "I25.10", "relationship": "RELATED"},
                {"description": "Old myocardial infarction", "icd10": "I25.2", "relationship": "RELATED"},
                {"description": "Atherosclerosis of aorta", "icd10": "I70.0", "relationship": "RELATED"},
                {"description": "Type 2 diabetes mellitus with other specified complication", "icd10": "E11.69", "relationship": "UNRELATED"},
                {"description": "Type 2 diabetes mellitus w diabetic chronic kidney disease", "icd10": "E11.22", "relationship": "UNRELATED"},
                {"description": "Chronic kidney disease, stage 3a", "icd10": "N18.31", "relationship": "UNRELATED"},
                {"description": "Spondylosis w/o myelopathy or radiculopathy, cervical region", "icd10": "M47.812", "relationship": "UNRELATED"},
                {"description": "Central pain syndrome", "icd10": "G89.0", "relationship": "UNRELATED"},
                {"description": "Human metapneumovirus pneumonia", "icd10": "J12.3", "relationship": "UNRELATED"},
                {"description": "Other specified postprocedural states", "icd10": "Z98.890", "relationship": "UNRELATED"},
                {"description": "Personal history of malignant neoplasm, unspecified", "icd10": "Z85.9", "relationship": "UNRELATED"},
                {"description": "Moderate protein-calorie malnutrition", "icd10": "E44.0", "relationship": "UNRELATED"},
                {"description": "Hemiplegia following cerebral infarction affecting right dominant side", "icd10": "I69.351", "relationship": "UNRELATED"},
                {"description": "Type 2 diabetes mellitus with diabetic polyneuropathy", "icd10": "E11.42", "relationship": "UNRELATED"},
                {"description": "Urinary calculus, unspecified", "icd10": "N20.9", "relationship": "UNRELATED"},
                {"description": "Urinary tract infection, site not specified", "icd10": "N39.0", "relationship": "UNRELATED"},
                {"description": "Polyosteoarthritis, unspecified", "icd10": "M15.9", "relationship": "UNRELATED"},
                {"description": "Neuromuscular dysfunction of bladder, unspecified", "icd10": "N31.9", "relationship": "UNRELATED"},
            ],
        }
        facesheet.secondary_diagnoses = "; ".join(
            f"{entry['description']} ({entry['icd10']}) - {entry['relationship'].title()}"
            for entry in facesheet.diagnosis_entries["secondary"]
        )

        # Service dates / benefit period, per chart
        facesheet.soc_date = date(2024, 5, 22)
        facesheet.election_date = date(2024, 5, 22)
        facesheet.recert_date = date(2025, 1, 16)
        facesheet.benefit_period_number = "3"
        facesheet.current_level_of_care = "ROUTINE"
        facesheet.code_status = "DNR"

        # Care team, per chart
        facesheet.medical_director_name = "John Liu, MD"
        facesheet.attending_physician_name = "Tejon Woods, NP"

        db.commit()

        print(f"{'created' if created else 'updated'} acceptance patient")
        print(f"  patient_id: {patient.id}")
        print(f"  tenant_id:  {patient.tenant_id}")
        print(f"  mrn:        {patient.mrn}")
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
