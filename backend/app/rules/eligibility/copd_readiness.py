from app.rules.base import BaseRule


class COPDReadinessRule(BaseRule):
    """
    COPD / Respiratory Failure audit-readiness rule (WARN-only).

    Triggered only when primary diagnosis looks pulmonary (COPD/resp failure).
    Checks for common supporting documentation elements.
    """

    rule_id = "COPD_AUDIT_READINESS"
    rule_name = "COPD audit readiness (O2 / hypoxia / hypercapnia / dyspnea / exacerbations)"

    # ICD-10 families commonly used for COPD/resp failure
    _PULM_PREFIXES = ("J44", "J96")

    def evaluate(self, ctx):
        primary = (ctx.primary_dx.icd10 if ctx.primary_dx else "") or ""
        code = primary.strip().upper()

        # If not a pulmonary code, do nothing (PASS)
        if not any(code.startswith(p) for p in self._PULM_PREFIXES):
            return self.pass_result(reason="Not a pulmonary primary diagnosis; COPD readiness not applicable.")

        facts = ctx.facts or {}
        missing = []

        # Recommended supporting elements (WARN-only if missing)
        if facts.get("oxygen_lpm") is None and facts.get("oxygen_required") is None:
            missing.append("oxygen_required_or_lpm")

        if facts.get("spo2_room_air") is None and facts.get("hypoxia") is None:
            missing.append("spo2_room_air_or_hypoxia")

        if facts.get("pco2") is None and facts.get("hypercapnia") is None:
            missing.append("pco2_or_hypercapnia")

        if facts.get("dyspnea_at_rest") is None and facts.get("functional_limitation") is None:
            missing.append("dyspnea_at_rest_or_functional_limitation")

        if facts.get("recent_exacerbations") is None and facts.get("recent_hospitalizations") is None:
            missing.append("recent_exacerbations_or_hospitalizations")

        if missing:
            return self.warn_result(
                reason="COPD supporting documentation incomplete",
                details={"missing_elements": missing, "primary_dx": code},
                evidence=facts,
            )

        return self.pass_result(
            reason="COPD supporting documentation present",
            details={"primary_dx": code},
            evidence=facts,
        )