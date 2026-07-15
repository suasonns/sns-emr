from __future__ import annotations

from typing import Any

from app.rules.base import BaseRule, Workflow


class EndStageParkinsonRule(BaseRule):
    """
    End-Stage Parkinson Disease evidence validation rule.

    Purpose:
    - Evaluate whether sufficient documented evidence exists
      to support advanced/end-stage Parkinson disease.

    This rule DOES NOT:
    - Determine hospice eligibility
    - Generate Plan of Care content
    - Override clinician judgment

    This rule ONLY:
    - Evaluate supporting evidence
    - Return PASS/WARN
    - Support audit readiness
    - Support evidence-gated Parkinson POC generation

    SNS Governance:

    G20 alone must never automatically trigger
    END_STAGE_PARKINSON_DISEASE.

    Required:

    Functional decline:
    - PPS <= 50
    OR
    - KPS <= 50
    OR
    - ADL dependency count >= 3
    OR
    - Bedbound

    PLUS

    At least two supporting indicators:
    - Dysphagia
    - Oral intake decline
    - Weight loss
    - Fall risk
    - Caregiver stress
    - Communication impairment
    - Speech impairment
    """

    rule_id = "END_STAGE_PARKINSON"

    rule_name = "End-stage Parkinson evidence validation"

    workflows = {
        Workflow.ADMISSION,
        Workflow.RECERTIFICATION,
    }

    MIN_SUPPORTING_INDICATORS = 2

    def evaluate(self, ctx):
        facts = ctx.facts or {}

        pps = self._to_int(facts.get("pps"))
        kps = self._to_int(facts.get("kps"))

        adl_dependency_count = self._to_int(
            facts.get("adl_dependency_count")
        )

        is_bedbound = self._truthy(
            facts.get("is_bedbound")
        )

        dysphagia = self._truthy(
            facts.get("dysphagia")
        )

        oral_intake_decline = self._truthy(
            facts.get("oral_intake_decline")
        )

        weight_loss_lbs = self._to_float(
            facts.get("weight_loss_lbs")
        )

        fall_risk = self._truthy(
            facts.get("fall_risk")
        )

        caregiver_stress = self._truthy(
            facts.get("caregiver_stress")
        )

        communication_ability = str(
            facts.get("communication_ability") or ""
        ).strip().upper()

        speech_pattern = str(
            facts.get("speech_pattern") or ""
        ).strip().upper()

        communication_impairment = (
            communication_ability
            and communication_ability
            not in {
                "NORMAL",
                "INTACT",
                "NONE",
            }
        )

        speech_impairment = (
            speech_pattern
            and speech_pattern
            not in {
                "NORMAL",
                "CLEAR",
                "INTACT",
                "NONE",
            }
        )

        functional_matches: list[str] = []

        if pps is not None and pps <= 50:
            functional_matches.append(
                "pps_less_than_or_equal_50"
            )

        if kps is not None and kps <= 50:
            functional_matches.append(
                "kps_less_than_or_equal_50"
            )

        if (
            adl_dependency_count is not None
            and adl_dependency_count >= 3
        ):
            functional_matches.append(
                "adl_dependency_count_greater_than_or_equal_3"
            )

        if is_bedbound:
            functional_matches.append(
                "is_bedbound"
            )

        functional_decline = bool(
            functional_matches
        )

        supporting_indicators: list[str] = []

        if dysphagia:
            supporting_indicators.append(
                "dysphagia"
            )

        if oral_intake_decline:
            supporting_indicators.append(
                "oral_intake_decline"
            )

        if (
            weight_loss_lbs is not None
            and weight_loss_lbs > 0
        ):
            supporting_indicators.append(
                "weight_loss_lbs"
            )

        if fall_risk:
            supporting_indicators.append(
                "fall_risk"
            )

        if caregiver_stress:
            supporting_indicators.append(
                "caregiver_stress"
            )

        if communication_impairment:
            supporting_indicators.append(
                "communication_impairment"
            )

        if speech_impairment:
            supporting_indicators.append(
                "speech_impairment"
            )

        supporting_indicator_count = len(
            supporting_indicators
        )

        eligible = (
            functional_decline
            and supporting_indicator_count
            >= self.MIN_SUPPORTING_INDICATORS
        )

        if eligible:
            return self.pass_result(
                reason=(
                    "End-stage Parkinson evidence "
                    "threshold met"
                ),
                details={
                    "functional_decline": True,
                    "functional_matches": (
                        functional_matches
                    ),
                    "supporting_indicator_count": (
                        supporting_indicator_count
                    ),
                    "matched_indicators": (
                        supporting_indicators
                    ),
                    "required_minimum": (
                        self.MIN_SUPPORTING_INDICATORS
                    ),
                },
                evidence=facts,
            )

        return self.warn_result(
            reason=(
                "Insufficient end-stage "
                "Parkinson evidence"
            ),
            details={
                "functional_decline": (
                    functional_decline
                ),
                "functional_matches": (
                    functional_matches
                ),
                "supporting_indicator_count": (
                    supporting_indicator_count
                ),
                "matched_indicators": (
                    supporting_indicators
                ),
                "required_minimum": (
                    self.MIN_SUPPORTING_INDICATORS
                ),
            },
            evidence=facts,
        )

    def _truthy(self, value: Any) -> bool:
        if value is None:
            return False

        if isinstance(value, bool):
            return value

        if isinstance(value, (int, float)):
            return value != 0

        if isinstance(value, str):
            normalized = value.strip().lower()

            return normalized in {
                "true",
                "yes",
                "y",
                "1",
                "present",
                "positive",
                "high",
                "severe",
            }

        return bool(value)

    def _to_int(
        self,
        value: Any,
    ) -> int | None:
        if value is None:
            return None

        try:
            return int(value)
        except (
            TypeError,
            ValueError,
        ):
            return None

    def _to_float(
        self,
        value: Any,
    ) -> float | None:
        if value is None:
            return None

        try:
            return float(value)
        except (
            TypeError,
            ValueError,
        ):
            return None