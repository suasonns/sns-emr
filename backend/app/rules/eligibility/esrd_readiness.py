from __future__ import annotations

from typing import Any, Dict, Optional

from app.rules.base import BaseRule


def _get_cms_rule(rule_key: str) -> Optional[dict]:
    """
    Safe dynamic lookup into the CMS rulepack loaded by the compliance engine.

    This implementation is file-agnostic and works with YAML or any future format.
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


class ESRDReadinessRule(BaseRule):
    """
    ESRD / CKD5 audit-readiness rule (WARN-only).

    Triggered only when primary diagnosis looks renal failure / ESRD.
    Checks for common supporting documentation elements.
    """

    rule_id = "ESRD_AUDIT_READINESS"
    rule_name = "ESRD audit readiness (dialysis status / eGFR / uremic symptoms / decline)"

    _RENAL_PREFIXES = ("N18.6", "N18.5", "Z99.2")

    def evaluate(self, ctx):
        primary = (ctx.primary_dx.icd10 if getattr(ctx, "primary_dx", None) else "") or ""
        code = primary.strip().upper()

        cms_terminal_rule = _get_cms_rule("eligibility_terminal_illness")

        if not any(code.startswith(prefix) for prefix in self._RENAL_PREFIXES):
            return self.pass_result(
                reason="Not an ESRD/CKD5 primary diagnosis; ESRD readiness not applicable."
            )

        facts: Dict[str, Any] = ctx.facts or {}
        missing = []

        # Dialysis status
        if facts.get("dialysis_status") is None and facts.get("dialysis_stopped") is None:
            missing.append("dialysis_status_or_stopped")

        # Renal function
        if facts.get("egfr") is None and facts.get("crcl") is None:
            missing.append("egfr_or_crcl")

        # Uremic condition / metabolic problems
        if facts.get("uremic_symptoms") is None and facts.get("metabolic_derangement") is None:
            missing.append("uremic_symptoms_or_metabolic_derangement")

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
                reason="ESRD supporting documentation incomplete",
                details=details,
                evidence=facts,
            )

        # PASS path
        return self.pass_result(
            reason="ESRD supporting documentation present",
            details=details,
            evidence=facts,
        )
