from __future__ import annotations

from typing import Any, Dict

from datetime import datetime

from app.rules.base import BaseRule, RuleContext


class ProhibitedPrimaryDxPrefixRule(BaseRule):
    """
    Blocks primary diagnosis codes that are not allowed by current system policy
    for hospice principal diagnosis selection.

    POLICY:
    F / R / V / W / X / Y / Z are blocked as PRIMARY DX.

    ENTERPRISE FEATURES:
    - Exception-safe
    - Audit-ready
    - Deterministic
    """

    rule_id = "DX_PRIMARY_PREFIX_DENY"
    rule_name = "Primary DX cannot start with F/R/V/W/X/Y/Z"

    regulator = "CMS"
    version = "2026.07"

    DISALLOWED_PREFIXES = {"F", "R", "V", "W", "X", "Y", "Z"}

    # ----------------------------------------
    # INTERNAL HELPERS
    # ----------------------------------------
    def _now(self) -> str:
        return datetime.utcnow().isoformat()

    def _build_evidence(self, code: str | None, prefix: str | None) -> Dict[str, Any]:
        return {
            "entered_primary_dx": code,
            "blocked_prefix": prefix,
            "evaluated_at": self._now(),
            "rule_id": self.rule_id,
        }

    def _build_explanation(
        self,
        *,
        code: str | None,
        prefix: str | None,
        reason: str,
        error_code: str,
    ) -> Dict[str, Any]:
        return {
            "error_code": error_code,
            "title": "Primary diagnosis not allowed",
            "message": reason,
            "next_action": (
                "Select a principal diagnosis that represents the terminal illness "
                "and is allowed by current hospice claim rules."
            ),
            "ui_hint": (
                "Codes starting with F, R, V, W, X, Y, or Z are blocked as primary "
                "diagnosis by current system policy."
            ),
            "primary_dx": code,
            "blocked_prefix": prefix,
            "blocked_prefixes": sorted(self.DISALLOWED_PREFIXES),
            "rule_id": self.rule_id,
            "rule_name": self.rule_name,
            "regulator": self.regulator,
            "rule_version": self.version,
        }

    # ----------------------------------------
    # MAIN EVALUATION
    # ----------------------------------------
    def evaluate(self, ctx: RuleContext):

        try:
            # ----------------------------------------------------------
            # 1) Missing primary diagnosis
            # ----------------------------------------------------------
            if ctx.primary_dx is None or not getattr(ctx.primary_dx, "icd10", None):
                reason = "Primary diagnosis is required before admission can proceed."

                explanation = self._build_explanation(
                    code=None,
                    prefix=None,
                    reason=reason,
                    error_code="PRIMARY_DX_MISSING",
                )

                return self.block_result(
                    reason,
                    details=explanation,
                    evidence=self._build_evidence(None, None),
                )

            # ----------------------------------------------------------
            # 2) Normalize safely
            # ----------------------------------------------------------
            raw_code = ctx.primary_dx.icd10

            if not isinstance(raw_code, str):
                reason = "Primary diagnosis must be a valid ICD-10 string."

                explanation = self._build_explanation(
                    code=str(raw_code),
                    prefix=None,
                    reason=reason,
                    error_code="PRIMARY_DX_INVALID_TYPE",
                )

                return self.block_result(
                    reason,
                    details=explanation,
                    evidence=self._build_evidence(str(raw_code), None),
                )

            code = raw_code.strip().upper()

            if not code:
                reason = "Primary diagnosis is blank or invalid."

                explanation = self._build_explanation(
                    code=code,
                    prefix=None,
                    reason=reason,
                    error_code="PRIMARY_DX_INVALID",
                )

                return self.block_result(
                    reason,
                    details=explanation,
                    evidence=self._build_evidence(code, None),
                )

            first_char = code[:1]

            # ----------------------------------------------------------
            # 3) Block disallowed prefixes
            # ----------------------------------------------------------
            if first_char in self.DISALLOWED_PREFIXES:
                reason = (
                    f"Primary diagnosis '{code}' is blocked because codes beginning with "
                    f"'{first_char}' are not allowed as principal diagnosis by current system policy."
                )

                explanation = self._build_explanation(
                    code=code,
                    prefix=first_char,
                    reason=reason,
                    error_code="DISALLOWED_PRIMARY_DX_PREFIX",
                )

                return self.block_result(
                    reason,
                    details=explanation,
                    evidence=self._build_evidence(code, first_char),
                )

            # ----------------------------------------------------------
            # 4) PASS
            # ----------------------------------------------------------
            return self.pass_result(
                "Primary diagnosis prefix allowed.",
                details={
                    "primary_dx": code,
                    "rule_id": self.rule_id,
                    "rule_name": self.rule_name,
                    "regulator": self.regulator,
                    "rule_version": self.version,
                },
                evidence=self._build_evidence(code, None),
            )

        # ----------------------------------------------------------
        # 5) HARD FAIL SAFETY (CRITICAL)
        # ----------------------------------------------------------
        except Exception as e:
            return self.block_result(
                "Rule execution failed. Please review input data.",
                details={
                    "error_code": "RULE_EXECUTION_ERROR",
                    "message": str(e),
                    "rule_id": self.rule_id,
                },
                evidence={
                    "exception": str(e),
                    "evaluated_at": self._now(),
                },
            )