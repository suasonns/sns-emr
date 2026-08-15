from __future__ import annotations

from typing import Any, Dict, Optional

from app.rules.base import BaseRule


def _get_cms_rule(rule_key: str) -> Optional[dict]:
    """
    Safe dynamic lookup into the CMS rulepack loaded by the compliance engine.

    File-agnostic: does not depend on JSON or YAML filenames.
    """
    try:
        from app.compliance.rule_loader import load_active_rulepacks
    except Exception:
        return None

    try:
        packs = load_active_rulepacks()
        cms_items = packs.get("CMS", [])
    except Exception:
        return None

    for item in cms_items:
        if not isinstance(item, dict):
            continue

        rules = item.get("rules", {})
        if not isinstance(rules, dict):
            continue

        rule_value = rules.get(rule_key)
        if isinstance(rule_value, dict):
            return rule_value

    return None


class FunctionalDeclineReadinessRule(BaseRule):
    """
    Functional decline audit-readiness rule (WARN-only).

    Used when hospice eligibility depends heavily on measurable decline,
    poor intake, reduced performance status, or progressive dependence.
    """

    rule_id = "FUNCTIONAL_DECLINE_AUDIT_READINESS"
    rule_name = "Functional decline audit readiness"

    def evaluate(self, ctx):
        cms_terminal_rule = _get_cms_rule("eligibility_terminal_illness")

        facts: Dict[str, Any] = ctx.facts or {}
        missing = []

        # Performance status
        if facts.get("pps_score") is None and facts.get("kps_score") is None:
            missing.append("pps_score_or_kps_score")

        # Functional decline / ADL dependence
        if facts.get("adl_decline") is None and facts.get("dependence_adls") is None:
            missing.append("adl_decline_or_dependence_adls")

        # Nutritional decline
        if (
            facts.get("weight_loss_percent_6_months") is None
            and facts.get("poor_intake") is None
        ):
            missing.append("weight_loss_or_poor_intake")

        # Physical decline indicators
        if facts.get("falls") is None and facts.get("progressive_weakness") is None:
            missing.append("falls_or_progressive_weakness")

        # Care needs escalation
        if (
            facts.get("caregiver_burden") is None
            and facts.get("increased_assistance_needs") is None
        ):
            missing.append("caregiver_burden_or_increased_assistance_needs")

        details: Dict[str, Any] = {}

        # Attach CMS rule metadata (audit trace)
        if cms_terminal_rule is not None:
            details["cms_terminal_rule_loaded"] = True
            details["cms_terminal_rule_version"] = cms_terminal_rule.get("version")
        else:
            details["cms_terminal_rule_loaded"] = False

        # WARN path
        if missing:
            details["missing_elements"] = missing

            return self.warn_result(
                reason="Functional decline supporting documentation incomplete",
                details=details,
                evidence=facts,
            )

        # PASS path
        return self.pass_result(
            reason="Functional decline supporting documentation present",
            details=details,
            evidence=facts,
        )