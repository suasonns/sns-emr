from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

POLICY_FILE = (
    PROJECT_ROOT
    / "app"
    / "config"
    / "icd10_primary_dx_policy.json"
)


@lru_cache(maxsize=1)
def load_policy() -> dict:
    with open(POLICY_FILE, "r", encoding="utf-8") as file:
        return json.load(file)


def normalize_icd10_code(code: str) -> str:
    return (
        code.strip()
        .upper()
        .replace(".", "")
        .replace(" ", "")
    )


def get_icd10_prefix(code: str) -> str:
    normalized = normalize_icd10_code(code)

    if not normalized:
        return ""

    return normalized[0]


def validate_primary_diagnosis(
    icd10_code: str,
) -> dict:
    """
    Hospice Primary Diagnosis Validation

    Returns:

    {
        "allowed": bool,
        "reason": str | None,
        "message": str | None,
        "rule_type": str | None,
    }
    """

    policy = load_policy()

    normalized_code = normalize_icd10_code(
        icd10_code
    )

    prefix = get_icd10_prefix(
        normalized_code
    )

    #
    # Explicit Never Primary Codes
    #
    explicit_codes = set(
        normalize_icd10_code(code)
        for code in policy
        .get(
            "explicit_never_primary_codes",
            {},
        )
        .get(
            "codes",
            [],
        )
    )

    if normalized_code in explicit_codes:
        return {
            "allowed": False,
            "reason": "Explicit Never Primary ICD-10 Code",
            "message": "This ICD-10 diagnosis is not allowed as a hospice primary diagnosis.",
            "rule_type": "explicit_code_block",
        }

    #
    # Prefix Rules
    #
    prefix_rules = policy.get(
        "primary_diagnosis_prefix_blocks",
        []
    )

    for rule in prefix_rules:
        if rule.get("prefix") == prefix:
            return {
                "allowed": False,
                "reason": rule.get(
                    "reason"
                ),
                "message": rule.get(
                    "user_message"
                ),
                "rule_type": "prefix_block",
            }

    return {
        "allowed": True,
        "reason": None,
        "message": None,
        "rule_type": None,
    }


def validate_secondary_diagnosis(
    icd10_code: str,
) -> dict:
    """
    Secondary diagnoses are currently allowed.

    Future:
        CMS-specific exclusions
        Payer-specific exclusions
        LCD-specific exclusions
    """

    return {
        "allowed": True,
        "reason": None,
        "message": None,
        "rule_type": None,
    }


def validate_comorbidity(
    icd10_code: str,
) -> dict:
    return {
        "allowed": True,
        "reason": None,
        "message": None,
        "rule_type": None,
    }


def validate_contributing_condition(
    icd10_code: str,
) -> dict:
    return {
        "allowed": True,
        "reason": None,
        "message": None,
        "rule_type": None,
    }