from __future__ import annotations

from typing import Any, Dict, Optional

from app.rules.base import BaseRule


def _get_cms_rule(rule_key: str) -> Optional[dict]:
    """
    Safe dynamic lookup into the CMS rulepack loaded by the compliance engine.
    File-agnostic (works with YAML and future formats).
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


class COPDReadinessRule(BaseRule):
    """
    COPD / Respiratory Failure audit-readiness rule (WARN-only).

    Triggered only when primary diagnosis looks pulmonary (COPD / respiratory failure).
    Checks for common supporting documentation elements.
    """

    rule_id = "COPD_AUDIT_READINESS"
    rule_name = "COPD audit readiness (O2 / hypoxia / hypercapnia / dyspnea / exacerbations)"

    _PULM_PREFIXES = ("J44", "J96")

    def evaluate(self, ctx):
        primary = (ctx.primary_dx.icd10 if getattr(ctx, "primary_dx", None) else "") or ""
        code = primary.strip().upper()

        cms_terminal_rule = _get_cms_rule("eligibility_terminal_illness")

        # NOT COPD → PASS immediately
        if not any(code.startswith(prefix) for prefix in self._PULM_PREFIXES):
            return self.pass_result(
                reason="Not a pulmonary primary diagnosis; COPD readiness not applicable."
            )

        facts: Dict[str, Any] = ctx.facts or {}
        missing = []

        # Oxygen requirement
        if facts.get("oxygen_lpm") is None and facts.get("oxygen_required") is None:
            missing.append("oxygen_required_or_lpm")

        # Hypoxia
        if facts.get("spo2_room_air") is None and facts.get("hypoxia") is None:
            missing.append("spo2_room_air_or_hypoxia")

        # Hypercapnia
        if facts.get("pco2") is None and facts.get("hypercapnia") is None:
            missing.append("pco2_or_hypercapnia")

        # Symptom burden / functional limitation
        if facts.get("dyspnea_at_rest") is None and facts.get("functional_limitation") is None:
            missing.append("dyspnea_at_rest_or_functional_limitation")

        # Disease trajectory
        if (
            facts.get("recent_exacerbations") is None
            and facts.get("recent_hospitalizations") is None
        ):
            missing.append("recent_exacerbations_or_hospitalizations")

        # Shared details block (clean pattern)
        details: Dict[str, Any] = {
            "primary_dx": code,
        }

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
                reason="COPD supporting documentation incomplete",
                details=details,
                evidence=facts,
            )

        # PASS path
        return self.pass_result(
            reason="COPD supporting documentation present",
            details=details,
            evidence=facts,
        )