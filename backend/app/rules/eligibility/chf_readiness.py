from app.rules.base import BaseRule, Workflow


class CHFReadinessRule(BaseRule):
    """
    CHF audit-readiness rule (WARN-only).

    Checks for commonly expected CHF supporting documentation:
    - Ejection Fraction (EF)
    - NYHA Class
    - Refractory symptoms
    """

    rule_id = "CHF_AUDIT_READINESS"
    rule_name = "CHF audit readiness (EF / NYHA / refractory symptoms)"
    workflows = {Workflow.ADMISSION}

    def evaluate(self, ctx):
        facts = ctx.facts or {}
        missing = []

        if not facts.get("ejection_fraction"):
            missing.append("ejection_fraction")

        if not facts.get("nyha_class"):
            missing.append("nyha_class")

        if not facts.get("refractory_symptoms"):
            missing.append("refractory_symptoms")

        if missing:
            return self.warn_result(
                reason="CHF supporting documentation incomplete",
                details={
                    "missing_elements": missing,
                },
                evidence=facts,
            )

        return self.pass_result(
            reason="CHF supporting documentation present",
            details={},
            evidence=facts,
        )