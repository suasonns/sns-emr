from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List

from app.core.rule_enforcement import rule_enforcement_enabled
from app.rules.base import RuleResult, RuleOutcome, RuleSeverity


logger = logging.getLogger(__name__)


class RuleViolationError(Exception):
    """
    Raised only when enforcement is enabled and a blocking rule violation
    must stop the workflow.
    """

    def __init__(self, result: RuleResult):
        self.result = result
        super().__init__(result.reason)


@dataclass(frozen=True)
class RuleApplicationSummary:
    """
    Batch summary returned by apply_rules().

    This is useful for:
    - API responses
    - dry runs
    - debug output
    - audit packet generation
    """

    evaluated_count: int
    pass_count: int
    warn_count: int
    violation_count: int
    blocking_violation_count: int
    enforcement_enabled: bool


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _safe_dict(value: Any) -> Dict[str, Any]:
    """
    Best-effort conversion to a log-safe dictionary.
    Prevents logging failures if details/evidence contain odd values.
    """
    if isinstance(value, dict):
        safe: Dict[str, Any] = {}
        for k, v in value.items():
            try:
                # keep simple primitives as-is
                if isinstance(v, (str, int, float, bool, type(None), list, dict)):
                    safe[str(k)] = v
                else:
                    safe[str(k)] = str(v)
            except Exception:
                safe[str(k)] = "<unserializable>"
        return safe

    return {}


def handle_rule_result(result: RuleResult, *, enforcement_enabled: bool) -> None:
    """
    Central enforcement gate.

    - Always logs evaluation
    - Blocks only if enforcement is enabled AND result is a BLOCK-severity violation
    """

    logger.info(
        "RULE_EVALUATED",
        extra={
            "event_type": "RULE_EVALUATED",
            "ts_utc": _utc_now_iso(),
            "rule_id": result.rule_id,
            "rule_name": result.rule_name,
            "outcome": result.outcome.value,
            "severity": result.severity.value,
            "reason": result.reason,
            "regulator": result.regulator,
            "rule_version": result.rule_version,
            "enforcement_enabled": enforcement_enabled,
            "details": _safe_dict(result.details),
            "evidence": _safe_dict(result.evidence),
        },
    )

    if enforcement_enabled:
        if result.outcome == RuleOutcome.VIOLATION and result.severity == RuleSeverity.BLOCK:
            raise RuleViolationError(result)


def apply_rules(results: List[RuleResult]) -> RuleApplicationSummary:
    """
    Apply a list of RuleResult objects through the enforcement gate.

    Returns a structured batch summary.
    Raises RuleViolationError only when a blocking violation is encountered
    and enforcement is enabled.
    """

    enforcement_on = rule_enforcement_enabled()

    pass_count = 0
    warn_count = 0
    violation_count = 0
    blocking_violation_count = 0

    for result in results:
        if result.outcome == RuleOutcome.PASS:
            pass_count += 1
        elif result.outcome == RuleOutcome.WARN:
            warn_count += 1
        elif result.outcome == RuleOutcome.VIOLATION:
            violation_count += 1
            if result.severity == RuleSeverity.BLOCK:
                blocking_violation_count += 1

        handle_rule_result(result, enforcement_enabled=enforcement_on)

    return RuleApplicationSummary(
        evaluated_count=len(results),
        pass_count=pass_count,
        warn_count=warn_count,
        violation_count=violation_count,
        blocking_violation_count=blocking_violation_count,
        enforcement_enabled=enforcement_on,
    )
