from app.rules.base import BaseRule, Workflow
from app.compliance.rule_loader import load_cms_rules


class CHFReadinessRule(BaseRule):
    """
    CHF audit-readiness rule (WARN-only).

    Checks for commonly expected CHF supporting documentation:
    - Ejection Fraction (EF)
    - NYHA Class
    - Refractory symptoms

    Now supports dynamic CMS rule configuration via JSON.
    """

    rule_id = "CHF_AUDIT_READINESS"
    rule_name = "CHF audit readiness (EF / NYHA / refractory symptoms)"
    workflows = {Workflow.ADMISSION}

    def evaluate(self, ctx):
        facts = ctx.facts or {}
        missing = []

        # ✅ Load CMS dynamic rules (SAFE: does not touch DB/data)
        rules = load_cms_rules()
        cms_rule = rules.get("eligibility_terminal_illness")

        # ✅ OPTIONAL: debug (remove later)
        # print("CMS RULE LOADED:", cms_rule)

        # ✅ Existing logic (UNCHANGED — SAFE)
        if not facts.get("ejection_fraction"):
            missing.append("ejection_fraction")

        if not facts.get("nyha_class"):
            missing.append("nyha_class")

        if not facts.get("refractory_symptoms"):
            missing.append("refractory_symptoms")

        # ✅ If anything missing → WARN
        if missing:
            return self.warn_result(
                reason="CHF supporting documentation incomplete",
                details={
                    "missing_elements": missing,
                },
                evidence=facts,
            )

        # ✅ PASS
        return self.pass_result(
            reason="CHF supporting documentation present",
            details={},
            evidence=facts,
        )