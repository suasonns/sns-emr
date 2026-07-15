from __future__ import annotations

import json
from uuid import uuid4

from app.services.poc_generation_service import (
    generate_initial_poc_draft,
)


class MockClinicalNote:
    def __init__(self):
        self.id = uuid4()
        self.patient_id = uuid4()
        self.visit_id = uuid4()

        self.form_key = "RN_ICA"
        self.note_type = "RN_ICA"
        self.discipline = "RN"

        self.content = {
            "primary_diagnosis": "Parkinson Disease",
            "primary_dx_code": "G20",

            "assessment": {
                "pps_score": 40,
                "kps_score": 50,

                "adl_dependency_count": 5,

                "dysphagia": True,

                "oral_intake_decline": True,

                "weight_loss_lbs": 12,

                "fall_risk": True,

                "caregiver_stress": True,

                "communication_ability": "LIMITED",

                "speech_pattern": "BARELY_INTELLIGIBLE",
            },

            "observed_data": {
                "nutrition": {
                    "poor_intake": True,
                    "weight_loss": True,
                }
            },
        }

        self.narrative = (
            "Advanced Parkinson disease with progressive decline. "
            "Patient demonstrates dysphagia, poor intake, weight loss, "
            "increased dependence in ADLs and caregiver stress."
        )


def main():
    note = MockClinicalNote()

    result = generate_initial_poc_draft(note)

    print("=" * 80)
    print("SNS PARKINSON POC INTEGRATION TEST")
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

    print(
        f"Rule Condition: "
        f"{result.get('rule_match', {}).get('condition')}"
    )

    pocs = result.get("pocs", [])

    print(f"Generated Problems: {len(pocs)}")

    for item in pocs:
        print(
            f"- {item['problem']['code']}: "
            f"{item['problem']['label']}"
        )


if __name__ == "__main__":
    main()