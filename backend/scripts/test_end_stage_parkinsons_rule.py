from __future__ import annotations

import json

from app.rules.base import (
    RuleContext,
    Workflow,
)
from app.rules.eligibility.end_stage_parkinsons import (
    EndStageParkinsonRule,
)


def print_result(title: str, result) -> None:
    print("=" * 80)
    print(title)
    print("=" * 80)

    print(
        json.dumps(
            result,
            indent=2,
            default=str,
        )
    )

    print()


def create_context(facts: dict):
    return RuleContext(
        tenant_id="TEST",
        patient_id="TEST_PATIENT",
        workflow=Workflow.ADMISSION,
        facts=facts,
        primary_dx=None,
        secondary_dx=[],
    )

def run_negative_test() -> None:
    """
    Should FAIL Parkinson evidence gate.
    """

    facts = {
        "pps": 70,
        "kps": 70,
        "adl_dependency_count": 1,
        "is_bedbound": False,
        "dysphagia": False,
        "oral_intake_decline": False,
        "weight_loss_lbs": 0,
        "fall_risk": False,
        "caregiver_stress": False,
        "communication_ability": "NORMAL",
        "speech_pattern": "CLEAR",
    }

    rule = EndStageParkinsonRule()
    ctx = create_context(facts)

    result = rule.evaluate(ctx)

    print_result(
        "NEGATIVE TEST - SHOULD WARN",
        result,
    )


def run_positive_test() -> None:
    """
    Should PASS Parkinson evidence gate.
    """

    facts = {
        "pps": 40,
        "kps": 50,
        "adl_dependency_count": 5,
        "is_bedbound": False,
        "dysphagia": True,
        "oral_intake_decline": True,
        "weight_loss_lbs": 12,
        "fall_risk": True,
        "caregiver_stress": True,
        "communication_ability": "LIMITED",
        "speech_pattern": "BARELY_INTELLIGIBLE",
    }

    rule = EndStageParkinsonRule()
    ctx = create_context(facts)

    result = rule.evaluate(ctx)

    print_result(
        "POSITIVE TEST - SHOULD PASS",
        result,
    )


def run_minimum_threshold_test() -> None:
    """
    Functional decline present.
    Exactly two supporting indicators.
    Should PASS.
    """

    facts = {
        "pps": 50,
        "kps": None,
        "adl_dependency_count": 3,
        "is_bedbound": False,
        "dysphagia": True,
        "oral_intake_decline": False,
        "weight_loss_lbs": 5,
        "fall_risk": False,
        "caregiver_stress": False,
        "communication_ability": "NORMAL",
        "speech_pattern": "CLEAR",
    }

    rule = EndStageParkinsonRule()
    ctx = create_context(facts)

    result = rule.evaluate(ctx)

    print_result(
        "THRESHOLD TEST - SHOULD PASS",
        result,
    )


def main() -> None:
    print()
    print("=" * 80)
    print("SNS END-STAGE PARKINSON RULE TEST")
    print("=" * 80)
    print()

    run_negative_test()

    run_positive_test()

    run_minimum_threshold_test()


if __name__ == "__main__":
    main()