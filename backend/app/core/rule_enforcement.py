import os
from enum import Enum


class RuleEnforcementMode(str, Enum):
    ENFORCE = "ENFORCE"
    EVALUATE_ONLY = "EVALUATE_ONLY"


def get_rule_enforcement_mode() -> RuleEnforcementMode:
    """
    Returns the configured rule enforcement mode.

    Defaults to EVALUATE_ONLY for safety.
    Any invalid value will fail closed (no enforcement).
    """
    value = os.getenv("RULE_ENFORCEMENT_MODE", "EVALUATE_ONLY").upper()
    try:
        return RuleEnforcementMode(value)
    except ValueError:
        # Fail-safe: never enforce on invalid config
        return RuleEnforcementMode.EVALUATE_ONLY


def rule_enforcement_enabled() -> bool:
    """
    Returns True only when rule enforcement is EXPLICITLY enabled.

    Enforcement requires TWO conditions:
      1) RULE_ENFORCEMENT_MODE=ENFORCE
      2) ALLOW_RULE_ENFORCEMENT=true

    This prevents accidental enforcement in local/dev environments.
    """
    allow_enforcement = os.getenv("ALLOW_RULE_ENFORCEMENT", "false").lower() == "true"
    if not allow_enforcement:
        return False

    return get_rule_enforcement_mode() == RuleEnforcementMode.ENFORCE