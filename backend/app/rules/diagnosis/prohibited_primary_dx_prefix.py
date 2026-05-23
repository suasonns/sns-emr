from __future__ import annotations

from app.rules.base import BaseRule, RuleContext


class ProhibitedPrimaryDxPrefixRule(BaseRule):
    rule_id = "DX_PRIMARY_PREFIX_DENY"
    rule_name = "Primary DX cannot start with F/R/V/W/X/Y/Z"

    DISALLOWED_PREFIXES = {"F", "R", "V", "W", "X", "Y", "Z"}

    def evaluate(self, ctx: RuleContext):
        if ctx.primary_dx is None or not ctx.primary_dx.icd10:
            # Missing primary diagnosis is a blocking issue when enforcing,
            # but safe to warn during dev.
            return self.block_result("Primary diagnosis is required.")

        code = ctx.primary_dx.icd10.strip().upper()
        first_char = code[:1]

        if first_char in self.DISALLOWED_PREFIXES:
            return self.block_result(
                "Primary diagnosis cannot start with F/R/V/W/X/Y/Z. "
                "These codes are allowed only as secondary/comorbidity diagnoses.",
                details={"primary_dx": code, "disallowed_prefix": first_char},
            )

        return self.pass_result("Primary diagnosis prefix allowed.", details={"primary_dx": code})