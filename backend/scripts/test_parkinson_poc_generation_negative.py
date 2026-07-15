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
                "pps_score": 70,
                "kps_score": 70,

                "adl_dependency_count": 1,

                "dysphagia": False,

                "oral_intake_decline": False,

                "weight_loss_lbs": 0,

                "fall_risk": False,

                "caregiver_stress": False,

                "communication_ability": "NORMAL",

                "speech_pattern": "CLEAR",
            }
        }

        self.narrative = (
            "Parkinson disease documented. "
            "Patient remains largely independent. "
            "No significant nutritional decline. "
            "No dysphagia. "
            "No documented caregiver stress."
        )


def main():
    note = MockClinicalNote()

    result = generate_initial_poc_draft(note)

    print("=" * 80)
    print("SNS PARKINSON NEGATIVE INTEGRATION TEST")
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
    print("VALIDATION")
    print("=" * 80)

    print(
        f"Rule Condition: "
        f"{result.get('rule_match', {}).get('condition')}"
    )

    pocs = result.get("pocs", [])

    print(f"Generated Problems: {len(pocs)}")

    parkinson_found = False

    for item in pocs:
        code = item["problem"]["code"]
        label = item["problem"]["label"]

        print(f"- {code}: {label}")

        if code == "END_STAGE_PARKINSON_DECLINE":
            parkinson_found = True

    print()
    print("=" * 80)
    print("RESULT")
    print("=" * 80)

    if parkinson_found:
        print(
            "FAILED: Parkinson evidence gate allowed "
            "END_STAGE_PARKINSON_DECLINE generation."
        )
    else:
        print(
            "PASSED: Parkinson evidence gate successfully "
            "blocked END_STAGE_PARKINSON_DECLINE generation."
        )


if __name__ == "__main__":
    main()