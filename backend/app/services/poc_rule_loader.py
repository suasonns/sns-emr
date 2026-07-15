from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any


RULES_FILE = (
    Path(__file__).resolve().parent.parent
    / "config"
    / "poc_generation_rules.json"
)


@lru_cache(maxsize=1)
def load_poc_rules() -> dict[str, Any]:
    with open(RULES_FILE, "r", encoding="utf-8") as file:
        return json.load(file)


def get_rules_version() -> str:
    data = load_poc_rules()
    return str(data.get("version", "unknown"))


def get_governance() -> dict[str, Any]:
    data = load_poc_rules()
    return data.get("governance", {})


def get_all_rules() -> dict[str, Any]:
    data = load_poc_rules()
    return data.get("rules", {})


def get_rule_by_icd(icd_code: str) -> dict[str, Any] | None:
    if not icd_code:
        return None

    rules = get_all_rules()

    code = str(icd_code).strip().upper()

    if code in rules:
        return rules[code]

    if "." in code:
        parent_code = code.split(".")[0]
        return rules.get(parent_code)

    return None


def is_primary_allowed(rule: dict[str, Any] | None) -> bool:
    """
    Governance gate.

    Returns True only when a diagnosis
    is explicitly allowed to be used
    in a primary diagnosis workflow.
    """

    if not rule:
        return False

    return bool(
        rule.get(
            "primary_allowed",
            False,
        )
    )


def is_promotable_to_primary(rule: dict[str, Any] | None) -> bool:
    """
    Returns True only when governance
    allows diagnosis promotion.
    """

    if not rule:
        return False

    return bool(
        rule.get(
            "promotable_to_primary",
            False,
        )
    )


def is_comorbidity_only(rule: dict[str, Any] | None) -> bool:
    """
    Returns True when diagnosis is
    classified as COMORBIDITY_ONLY.
    """

    if not rule:
        return False

    return (
        rule.get(
            "diagnosis_classification"
        )
        == "COMORBIDITY_ONLY"
    )


def get_rule_scope(rule: dict[str, Any] | None) -> str:
    if not rule:
        return "UNKNOWN"

    return str(
        rule.get(
            "rule_scope",
            "UNKNOWN",
        )
    )


def validate_primary_diagnosis_rule(
    icd_code: str,
) -> tuple[bool, str]:
    """
    Enterprise governance enforcement.

    Returns:
        (True, "ALLOWED")
        (False, "<REASON>")
    """

    rule = get_rule_by_icd(icd_code)

    if not rule:
        return (
            True,
            "NO_RULE_FOUND",
        )

    if not is_primary_allowed(rule):
        return (
            False,
            "COMORBIDITY_ONLY",
        )

    return (
        True,
        "ALLOWED",
    )


def reload_poc_rules() -> dict[str, Any]:
    load_poc_rules.cache_clear()
    return load_poc_rules()