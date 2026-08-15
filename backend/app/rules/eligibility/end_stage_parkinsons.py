from __future__ import annotations

from typing import Any, Dict, Optional

from app.rules.base import BaseRule


def _get_cms_rule(rule_key: str) -> Optional[dict]:
    """
    Safe dynamic lookup into the active CMS rulepack loaded by the compliance engine.

    This is intentionally filename-agnostic.
    It does not rely on cms_rules.json or cms_rules.yaml.
    It only relies on the structure returned by load_active_rulepacks().
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


class EndStageParkinsonRule(BaseRule):
    """
    End-stage Parkinson disease audit-readiness rule (WARN-only).

    Triggered when the primary diagnosis suggests advanced Parkinson disease
    or related neurodegenerative decline. Checks for commonly expected
    supporting evidence for hospice defensibility.
    """

    rule_id = "END_STAGE_PARKINSON_AUDIT_READINESS"
    rule_name = "End-stage Parkinson disease audit readiness"

    _NEURO_PREFIXES = ("G20", "G20.", "G20.A1", "G20.A2", "G20.B1", "G20.B2")

    def evaluate(self, ctx):
        primary = (ctx.primary_dx.icd10 if getattr(ctx, "primary_dx", None) else "") or ""
        code = primary.strip().upper()

        cms_terminal_rule = _get_cms_rule("eligibility_terminal_illness")

        if not any(code.startswith(prefix) for prefix in self._NEURO_PREFIXES):
            return self.pass_result(
                reason="Not an advanced Parkinson primary diagnosis; Parkinson readiness not applicable."
            )

        facts: Dict[str, Any] = ctx.facts or {}
        missing = []

        # Functional decline / performance status
        if facts.get("functional_decline") is None and facts.get("pps_score") is None:
            missing.append("functional_decline_or_pps_score")

        # Dependence for care
        if facts.get("dependence_adls") is None and facts.get("caregiver_dependence") is None:
            missing.append("dependence_adls_or_caregiver_dependence")

        # Dysphagia / aspiration risk
        if facts.get("dysphagia") is None and facts.get("aspiration_risk") is None:
            missing.append("dysphagia_or_aspiration_risk")

        # Speech / communication decline
        if facts.get("speech_decline") is None and facts.get("communication_impairment") is None:
            missing.append("speech_decline_or_communication_impairment")

        # Nutritional decline / infections
        if (
            facts.get("weight_loss_percent_6_months") is None
            and facts.get("poor_intake") is None
            and facts.get("recurrent_infections") is None
        ):
            missing.append("weight_loss_or_poor_intake_or_recurrent_infections")

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
                reason="End-stage Parkinson supporting documentation incomplete",
                details=details,
                evidence=facts,
            )

        return self.pass_result(
            reason="End-stage Parkinson supporting documentation present",
            details=details,
            evidence=facts,
        )