from app.rules.base import BaseRule


class ESRDReadinessRule(BaseRule):
    """
    ESRD / CKD5 audit-readiness rule (WARN-only).

    Triggered only when primary diagnosis looks renal failure/ESRD.
    Checks for common supporting documentation elements.
    """

    rule_id = "ESRD_AUDIT_READINESS"
    rule_name = "ESRD audit readiness (dialysis status / eGFR / uremic symptoms / decline)"

    _RENAL_PREFIXES = ("N18.6", "N18.5", "Z99.2")

    def evaluate(self, ctx):
        primary = (ctx.primary_dx.icd10 if ctx.primary_dx else "") or ""
        code = primary.strip().upper()

        if not any(code.startswith(p) for p in self._RENAL_PREFIXES):
            return self.pass_result(reason="Not an ESRD/CKD5 primary diagnosis; ESRD readiness not applicable.")

        facts = ctx.facts or {}
        missing = []

        # Dialysis status is a huge audit point
        if facts.get("dialysis_status") is None and facts.get("dialysis_stopped") is None:
            missing.append("dialysis_status_or_stopped")

        # Objective renal function
        if facts.get("egfr") is None and facts.get("crcl") is None:
            missing.append("egfr_or_crcl")

        # Symptoms/supporting evidence
        if facts.get("uremic_symptoms") is None and facts.get("metabolic_derangement") is None:
            missing.append("uremic_symptoms_or_metabolic_derangement")

        # Decline evidence (general but useful for ESRD)
        if facts.get("functional_decline") is None and facts.get("poor_intake") is None and facts.get("weight_loss_percent_6_months") is None:
            missing.append("decline_evidence_functional_or_intake_or_weight_loss")

        if missing:
            return self.warn_result(
                reason="ESRD supporting documentation incomplete",
                details={"missing_elements": missing, "primary_dx": code},
                evidence=facts,
            )

        return self.pass_result(
            reason="ESRD supporting documentation present",
            details={"primary_dx": code},
            evidence=facts,
        )