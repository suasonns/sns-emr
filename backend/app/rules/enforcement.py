from __future__ import annotations

import logging
from typing import List

from app.core.rule_enforcement import rule_enforcement_enabled
from app.rules.base import RuleResult, RuleOutcome, RuleSeverity

logger = logging.getLogger(__name__)


class RuleViolationError(Exception):
    def __init__(self, result: RuleResult):
        self.result = result
        super().__init__(result.reason)


def handle_rule_result(result: RuleResult) -> None:
    """
    Central enforcement gate.
    - Always logs evaluation
    - Blocks only if enforcement is enabled AND rule is BLOCK severity violation
    """
    logger.info(
        "RULE_EVALUATED",
        extra={
            "rule_id": result.rule_id,
            "rule_name": result.rule_name,
            "outcome": result.outcome.value,
            "severity": result.severity.value,
            "reason": result.reason,
            "enforcement_enabled": rule_enforcement_enabled(),
            "details": result.details,
            "evidence": result.evidence,
        },
    )

    if rule_enforcement_enabled():
        if result.outcome == RuleOutcome.VIOLATION and result.severity == RuleSeverity.BLOCK:
            raise RuleViolationError(result)


def apply_rules(results: List[RuleResult]) -> None:
    """
    Apply a list of RuleResult objects through the enforcement gate.
    """
    for r in results:
        handle_rule_result(r)