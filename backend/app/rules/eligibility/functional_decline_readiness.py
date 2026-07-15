from __future__ import annotations

from typing import Any

from app.rules.base import BaseRule, Workflow


class FunctionalDeclineReadinessRule(BaseRule):
    """
    Functional decline audit-readiness rule.

    Purpose:
    - Evaluate whether core functional decline evidence is present.
    - Use harvested facts from RuleContext.facts.
    - Support survey defensibility and eligibility readiness.
    - Do not determine hospice eligibility.
    - Do not make clinical decisions.

    Scope:
    - PPS
    - KPS
    - FAST when dementia-related diagnosis is present

    This rule is WARN-only.
    """

    rule_id = "FUNCTIONAL_DECLINE_READINESS"
    rule_name = "Functional decline audit readiness (PPS / KPS / FAST)"
    workflows = {Workflow.ADMISSION, Workflow.RECERTIFICATION}

    DEMENTIA_KEYWORDS = {
        "DEMENTIA",
        "ALZHEIMER",
        "ALZHEIMER'S",
        "SENILE DEGENERATION",
        "LEWY BODY",
        "FRONTOTEMPORAL",
        "VASCULAR DEMENTIA",
        "PICK",
        "F01",
        "F02",
        "F03",
        "G30",
    }

    def evaluate(self, ctx):
        facts = ctx.facts or {}
        missing: list[str] = []

        pps = facts.get("pps")
        kps = facts.get("kps")
        fast_stage = facts.get("fast_stage")

        diagnosis_text = self._collect_diagnosis_text(ctx)
        dementia_related = self._contains_any_keyword(
            diagnosis_text,
            self.DEMENTIA_KEYWORDS,
        )

        if self._empty(pps):
            missing.append("pps")

        if self._empty(kps):
            missing.append("kps")

        if dementia_related and self._empty(fast_stage):
            missing.append("fast_stage")

        if missing:
            return self.warn_result(
                reason="Functional decline supporting documentation incomplete",
                details={
                    "missing_elements": missing,
                    "dementia_related": dementia_related,
                    "rule_scope": [
                        "pps",
                        "kps",
                        "fast_stage_when_dementia_related",
                    ],
                },
                evidence=facts,
            )

        return self.pass_result(
            reason="Functional decline supporting documentation present",
            details={
                "dementia_related": dementia_related,
                "rule_scope": [
                    "pps",
                    "kps",
                    "fast_stage_when_dementia_related",
                ],
            },
            evidence=facts,
        )

    def _collect_diagnosis_text(self, ctx) -> str:
        values: list[str] = []

        primary_dx = getattr(ctx, "primary_dx", None)
        secondary_dx = getattr(ctx, "secondary_dx", []) or []

        if primary_dx:
            self._collect_text(getattr(primary_dx, "icd10", None), values)
            self._collect_text(getattr(primary_dx, "description", None), values)

        for diagnosis in secondary_dx:
            self._collect_text(getattr(diagnosis, "icd10", None), values)
            self._collect_text(getattr(diagnosis, "description", None), values)

        return " ".join(values).upper()

    def _collect_text(self, value: Any, output: list[str]) -> None:
        if value is None:
            return

        if isinstance(value, str):
            cleaned = value.strip()
            if cleaned:
                output.append(cleaned)
            return

        if isinstance(value, (int, float, bool)):
            output.append(str(value))
            return

        if isinstance(value, dict):
            for nested_value in value.values():
                self._collect_text(nested_value, output)
            return

        if isinstance(value, list):
            for nested_value in value:
                self._collect_text(nested_value, output)
            return

    def _contains_any_keyword(
        self,
        text: str,
        keywords: set[str],
    ) -> bool:
        normalized = str(text or "").upper()

        if not normalized:
            return False

        return any(keyword in normalized for keyword in keywords)

    def _empty(self, value: Any) -> bool:
        if value is None:
            return True

        if isinstance(value, str):
            return not value.strip()

        if isinstance(value, list):
            return len(value) == 0

        if isinstance(value, dict):
            return len(value) == 0

        return False