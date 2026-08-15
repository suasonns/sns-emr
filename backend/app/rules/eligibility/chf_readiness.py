from __future__ import annotations

from typing import Any, Dict, Optional

from app.rules.base import BaseRule


def _get_cms_rule(rule_key: str) -> Optional[dict]:
    """
    Safe dynamic lookup into the active CMS rulepack loaded by the compliance engine.

    This function is intentionally filename-agnostic. It does not rely on a specific
    source file name such as cms_rules.json or cms_rules.yaml. It only relies on the
    structure returned by the active rule loader.
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


class CHFReadinessRule(BaseRule):
    """
    CHF / advanced cardiac disease audit-readiness rule (WARN-only).

    Triggered when the primary diagnosis looks consistent with advanced heart failure
    or end-stage cardiac disease and checks for common supporting documentation
    elements used for audit readiness.
    """

    rule_id = "CHF_AUDIT_READINESS"
    rule_name = "CHF audit readiness (NYHA / EF / symptoms / recurrent decompensation)"

    _CARDIAC_PREFIXES = ("I50", "I11.0", "I13")

    def evaluate(self, ctx):
        primary = (ctx.primary_dx.icd10 if getattr(ctx, "primary_dx", None) else "") or ""
        code = primary.strip().upper()

        cms_terminal_rule = _get_cms_rule("eligibility_terminal_illness")

        if not any(code.startswith(prefix) for prefix in self._CARDIAC_PREFIXES):
            return self.pass_result(
                reason="Not a CHF / advanced cardiac primary diagnosis; CHF readiness not applicable."
            )

        facts: Dict[str, Any] = ctx.facts or {}
        missing = []

        # Objective severity
        if facts.get("nyha_class") is None and facts.get("ef_percent") is None:
            missing.append("nyha_class_or_ef_percent")

        # Symptom burden
        if facts.get("dyspnea_at_rest") is None and facts.get("orthopnea") is None:
            missing.append("dyspnea_at_rest_or_orthopnea")

        # Recurrent decompensation
        if (
            facts.get("recent_chf_exacerbations") is None
            and facts.get("recent_hospitalizations") is None
        ):
            missing.append("recent_chf_exacerbations_or_hospitalizations")

        # Functional / nutritional decline
        if (
            facts.get("functional_decline") is None
            and facts.get("poor_intake") is None
            and facts.get("weight_loss_percent_6_months") is None
        ):
            missing.append("decline_evidence_functional_or_intake_or_weight_loss")

        details: Dict[str, Any] = {
            "primary_dx": code,
        }

        if cms_terminal_rule is not None:
            details["cms_terminal_rule_loaded"] = True
            details["cms_terminal_rule_version"] = cms_terminal_rule.get("version")
        else:
            details["cms_terminal_rule_loaded"] = False

        if missing:
            details["missing_elements"] = missing
            return self.warn_result(
                reason="CHF supporting documentation incomplete",
                details=details,
                evidence=facts,
            )

        return self.pass_result(
            reason="CHF supporting documentation present",
            details=details,
            evidence=facts,
        )