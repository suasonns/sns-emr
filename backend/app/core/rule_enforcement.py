from enum import Enum
from app.core.settings import settings


class RuleEnforcementMode(str, Enum):
    ENFORCE = "ENFORCE"
    EVALUATE_ONLY = "EVALUATE_ONLY"


def get_rule_enforcement_mode() -> RuleEnforcementMode:
    """
    Returns the configured rule enforcement mode.

    Defaults to EVALUATE_ONLY for safety.
    Any invalid value will fail closed (no enforcement).
    """

    raw_value = getattr(settings, "RULE_ENFORCEMENT_MODE", None)
    value = (raw_value or "EVALUATE_ONLY").upper()

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

    # Primary safety gate
    if not getattr(settings, "ALLOW_RULE_ENFORCEMENT", False):
        return False

    # Mode check
    return get_rule_enforcement_mode() == RuleEnforcementMode.ENFORCE