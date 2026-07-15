from __future__ import annotations

import json
from uuid import uuid4

from app.services.poc_generation_service import generate_initial_poc_draft


class MockClinicalNote:
    def __init__(self):
        self.id = uuid4()
        self.patient_id = uuid4()
        self.visit_id = uuid4()

        self.form_key = "RN_ICA"
        self.note_type = "RN_ICA"
        self.discipline = "RN"

        self.content = {
            "primary_diagnosis": "Stroke Sequelae",
            "primary_dx_code": "I69.35", 
            "assessment": {
                "pps": 40,
                "nyha_class": "IV",
                "pain": {
                    "pain_score": 7,
                    "pain_present": True,
                },
                "respiratory": {
                    "dyspnea_level": "SEVERE",
                },
                "adls": {
                    "bathing": "dependent",
                    "dressing": "dependent",
                },
                "caregiver": {
                    "primary_caregiver": "spouse",
                },
            },
            "observed_data": {
                "skin": {
                    "skin_tear": True,
                },
                "nutrition": {
                    "poor_intake": True,
                    "weight_loss": True,
                },
            },
        }

        self.narrative = (
            "Patient with CHF and severe dyspnea. "
            "Reports pain 7/10. "
            "Dependent in ADLs. "
            "Poor intake and weight loss. "
            "Caregiver requires education."
        )


def main():
    note = MockClinicalNote()

    result = generate_initial_poc_draft(note)

    print("=" * 80)
    print("SNS POC GENERATION TEST")
    print("=" * 80)

    print(
        json.dumps(
            result,
            indent=2,
            default=str,
        )
    )

    print()
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)

    print(f"Status: {result.get('status')}")

    pocs = result.get("pocs", [])

    print(f"Generated Problems: {len(pocs)}")

    for item in pocs:
        code = item["problem"]["code"]
        label = item["problem"]["label"]

        print(f"- {code}: {label}")


if __name__ == "__main__":
    main()