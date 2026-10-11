"""SNS Body Systems — Respiratory product-owner-authorized requirement
engine (backend mirror).

This is a line-for-line Python port of
`sns-emr-frontend/src/domain/body-systems/respiratoryProductRequirements.ts`.
It MUST be kept in lockstep with that file: the frontend is the
originally-authored source of truth for the written product-owner
Respiratory field specification, but a client-side-only check can be
bypassed by any direct API caller, so the backend independently
re-evaluates the same "required when" rules before a
REVIEWED/REVIEWED_WITH_EXCEPTION reviewState is accepted
(`_assert_completion_is_not_forged` in
`app/api/routes/body_systems.py`).

Deliberately kept separate from `_missing_blocking_respiratory_requirements`
in `body_systems.py` (the legacy situation-branch mirror), for the same
reason the two frontend engines are kept separate: this evaluates the
newly-authorized field set against the specification's own explicit
per-field rules, not the legacy situation-requirement graph.

Policy applied uniformly (specification section 11):
- top-level review decisions (assessmentContext, oxygenUse,
  respiratorySupportStatus, clinicalComparison, coughType) are always
  required for completion;
- conditional detail is required only once its triggering response is
  entered;
- optional notes remain optional;
- blank never means normal and is never silently satisfied;
- these requirements only block the explicit "Complete System Review"
  action -- draft save is never blocked.
"""
from __future__ import annotations

from typing import Any, Optional


def _text_filled(value: Any) -> bool:
    return bool(value and str(value).strip())


def get_missing_product_authorized_requirements(data: dict[str, Any]) -> list[tuple[str, str]]:
    """Returns every unresolved (fieldId, message) requirement gap for the
    product-owner-authorized Respiratory field set in `data` (the same
    flat `BodySystemsAssessment.data["respiratory"]`-shaped dict the
    frontend sends). An empty list means this engine does not block
    completion; `_missing_blocking_respiratory_requirements` is evaluated
    separately and independently."""
    gaps: list[tuple[str, str]] = []

    def push(field_id: str, message: str) -> None:
        gaps.append((field_id, message))

    oxygen_therapy: dict[str, Any] = data.get("oxygenTherapy") or {}
    ventilator: dict[str, Any] = data.get("ventilator") or {}

    assessment_context: Optional[str] = data.get("assessmentContext")
    clinical_comparison: Optional[str] = data.get("clinicalComparison")
    cough_type: Optional[str] = data.get("coughType")
    oxygen_use: Optional[str] = data.get("oxygenUse")
    sob_severity: Optional[str] = data.get("sobSeverity")
    support_status: Optional[str] = data.get("respiratorySupportStatus")
    treatment_decision: Optional[str] = data.get("treatmentDecision")
    treatment_response_status: Optional[str] = data.get("treatmentResponseStatus")
    cough_action_decision: Optional[str] = data.get("coughActionDecision")

    # --- Section 3: Assessment context & comparison -----------------------
    if not assessment_context:
        push("respiratory_assessment_context", "Record the Respiratory assessment context.")
    if not clinical_comparison:
        push("respiratory_clinical_comparison", "Record the comparison to the prior Respiratory assessment.")
    if clinical_comparison == "CHANGED_FROM_PRIOR" and not _text_filled(data.get("clinicalStatusChangeDetail")):
        push("respiratory_clinical_status_change_detail", "Describe the change from the prior assessment.")

    # --- Section 4: Comfort / function -------------------------------------
    requires_comfort_function = assessment_context in ("CURRENT_CONCERNS_ASSESSED", "UNABLE_TO_FULLY_ASSESS")
    comfort_function_impact: Optional[str] = data.get("comfortFunctionImpact")
    if requires_comfort_function and not comfort_function_impact:
        push("respiratory_comfort_function_impact", "Record the comfort/functional impact.")
    if comfort_function_impact == "IMPACT_PRESENT" and not _text_filled(data.get("comfortFunctionEvidence")):
        push("respiratory_comfort_function_evidence", "Describe the comfort/function evidence.")
    if comfort_function_impact == "UNABLE_TO_ASSESS" and not _text_filled(data.get("comfortFunctionEvidence")):
        push("respiratory_comfort_function_evidence", "Describe why comfort/function could not be evaluated.")
    configured_requirement_response: Optional[str] = data.get("configuredRequirementResponse")
    if (
        configured_requirement_response
        and configured_requirement_response != "NOT_APPLICABLE"
        and configured_requirement_response == "FOLLOW_UP_REQUIRED"
        and not data.get("configuredFollowUpStatus")
    ):
        push("respiratory_configured_follow_up_status", "Record the configured follow-up status.")

    # --- Section 5: Treatment decision --------------------------------------
    treatment_applicable = bool(
        (sob_severity and sob_severity != "None")
        or cough_type in ("Productive", "Hemoptysis")
        or oxygen_use == "YES"
        or support_status == "IN_USE"
    )
    if treatment_applicable and not treatment_decision:
        push("respiratory_treatment_decision", "Record the treatment decision.")
    if treatment_decision in ("INITIATED", "ALREADY_IN_PLACE") and not _text_filled(data.get("treatmentDescription")):
        push("respiratory_treatment_description", "Describe the treatment.")
    if treatment_decision == "DECLINED" and not _text_filled(data.get("treatmentDeclineReason")):
        push("respiratory_treatment_decline_reason", "Record the reason treatment was declined.")
    if treatment_decision and treatment_decision != "NOT_INDICATED" and not treatment_response_status:
        push("respiratory_treatment_response_status", "Record the treatment response status.")
    if (
        treatment_decision == "INITIATED"
        and treatment_response_status != "PENDING"
        and not _text_filled(data.get("treatmentResponse"))
    ):
        push("respiratory_treatment_response", "Record the observed/reported treatment response.")
    if (
        treatment_decision == "ALREADY_IN_PLACE"
        and treatment_response_status in ("OBSERVED", "REPORTED")
        and not _text_filled(data.get("treatmentResponse"))
    ):
        push("respiratory_treatment_response", "Record the current treatment effectiveness.")

    # --- Section 6: Finding-level follow-up / POC review --------------------
    finding_level_follow_up_applicable = treatment_applicable
    follow_up_need: Optional[str] = data.get("followUpNeed")
    if finding_level_follow_up_applicable and not follow_up_need:
        push("respiratory_follow_up_need", "Record whether Respiratory follow-up is needed.")
    if follow_up_need == "NEEDED":
        if not _text_filled(data.get("followUpTimingPlan")):
            push("respiratory_follow_up_timing_plan", "Record the follow-up timing/plan.")
        if not _text_filled(data.get("followUpResponsibleClinician")):
            push("respiratory_follow_up_responsible_clinician", "Record who is responsible for Respiratory follow-up.")
    if data.get("pocReviewNeed") == "REVIEW_NEEDED" and not _text_filled(data.get("pocReviewReason")):
        push("respiratory_poc_review_reason", "Record why Plan of Care review is needed.")

    # --- Section 7: Oxygen ----------------------------------------------------
    if not oxygen_use:
        push("respiratory_oxygen_use", "Record whether oxygen is in use.")
    if oxygen_use == "UNABLE_TO_VERIFY" and not _text_filled(data.get("oxygenUnableToVerifyReason")):
        push("respiratory_oxygen_unable_to_verify_reason", "Record why oxygen use could not be verified.")
    if oxygen_use == "YES":
        if not oxygen_therapy.get("deliveryDevice"):
            push("respiratory_oxygen_delivery_device", "Record the oxygen delivery device.")
        if oxygen_therapy.get("deliveryDevice") == "OTHER" and not _text_filled(oxygen_therapy.get("otherDevice")):
            push("respiratory_oxygen_other_device", "Specify the oxygen delivery device.")
        if not oxygen_therapy.get("frequency"):
            push("respiratory_oxygen_frequency", "Record the oxygen frequency.")
    uses_liters_per_minute = oxygen_therapy.get("flowUnit") == "L_MIN"
    if oxygen_use == "YES" and uses_liters_per_minute and oxygen_therapy.get("flowValue") is None:
        push("respiratory_oxygen_flow_value", "Record the oxygen flow value.")
    spo2_value = data.get("spo2Value")
    spo2_measurement_condition: Optional[str] = data.get("spo2MeasurementCondition")
    if spo2_value is not None and not spo2_measurement_condition:
        push("respiratory_spo2_measurement_condition", "Record the SpO2 measurement condition.")
    if spo2_measurement_condition == "NOT_OBTAINED" and not _text_filled(data.get("spo2NotObtainedReason")):
        push("respiratory_spo2_not_obtained_reason", "Record why SpO2 was not obtained.")
    if spo2_value is not None:
        if not _text_filled(data.get("oxygenMeasurementDate")):
            push("respiratory_oxygen_measurement_date", "Record the SpO2 measurement date.")
        if not _text_filled(data.get("oxygenMeasurementTime")):
            push("respiratory_oxygen_measurement_time", "Record the SpO2 measurement time.")
    if (
        spo2_measurement_condition == "ON_OXYGEN"
        and spo2_value is not None
        and not _text_filled(data.get("measuredOxygenFlowOrConcentration"))
    ):
        push("respiratory_measured_oxygen_flow_or_concentration", "Record the measured oxygen flow/concentration.")
    if (
        oxygen_use == "YES" or (treatment_decision and treatment_decision != "NOT_INDICATED")
    ) and not _text_filled(data.get("oxygenEffectivenessResponse")):
        push("respiratory_oxygen_effectiveness_response", "Record oxygen/treatment effectiveness or response.")

    # --- Section 8: Cough and secretions ---------------------------------------
    if not cough_type:
        push("respiratory_cough_type", "Record the cough type.")
    if cough_type == "Productive":
        if not data.get("sputumAmount"):
            push("respiratory_sputum_amount", "Record the sputum amount.")
        if not data.get("sputumColor"):
            push("respiratory_sputum_color", "Record the sputum color.")
    if (data.get("sputumCharacter") == "OTHER" or data.get("sputumColor") == "OTHER") and not _text_filled(
        data.get("sputumOtherSpecification")
    ):
        push("respiratory_sputum_other_specification", "Specify the sputum character/color.")
    cough_requires_action = cough_type in ("Productive", "Hemoptysis")
    if cough_type == "Hemoptysis" and not _text_filled(data.get("coughClinicalSignificance")):
        push("respiratory_cough_clinical_significance", "Record the clinical significance of hemoptysis.")
    if cough_requires_action and not cough_action_decision:
        push("respiratory_cough_action_decision", "Record the cough action decision.")
    if cough_action_decision == "ACTION_TAKEN":
        if not _text_filled(data.get("coughActionDescription")):
            push("respiratory_cough_action_description", "Describe the action taken for cough/secretions.")
        if not _text_filled(data.get("coughResponse")):
            push("respiratory_cough_response", "Record the response to the cough/secretions action.")
        if not _text_filled(data.get("coughActionDateTime")):
            push("respiratory_cough_action_date_time", "Record when the cough/secretions action occurred.")
    if cough_action_decision == "DECLINED" and not _text_filled(data.get("coughDeclineReason")):
        push("respiratory_cough_decline_reason", "Record why the cough/secretions action was declined.")
    if cough_action_decision in ("ACTION_TAKEN", "DECLINED") and (
        not _text_filled(data.get("coughFollowUpTimingPlan"))
        or not _text_filled(data.get("coughFollowUpResponsibleClinician"))
    ):
        if not _text_filled(data.get("coughFollowUpTimingPlan")):
            push("respiratory_cough_follow_up_timing_plan", "Record the cough/secretions follow-up timing/plan.")
        if not _text_filled(data.get("coughFollowUpResponsibleClinician")):
            push(
                "respiratory_cough_follow_up_responsible_clinician",
                "Record who is responsible for cough/secretions follow-up.",
            )

    # --- Section 9: Respiratory support and airway ----------------------------
    if not support_status:
        push("respiratory_support_status", "Record the respiratory support status.")
    support_types: list[str] = list(data.get("respiratorySupportTypes") or [])
    if support_status == "IN_USE" and not support_types:
        push("respiratory_support_types", "Record the respiratory support type(s) in use.")
    if "VENTILATOR" in support_types and not ventilator.get("duration"):
        push("respiratory_ventilator_duration", "Record whether the ventilator is short-term or long-term.")
    if "TRACHEOSTOMY" in support_types and not _text_filled(data.get("airwaySiteFindings")):
        push("respiratory_airway_site_findings", "Record the airway/tracheostomy site findings.")
    if support_status == "IN_USE" and not _text_filled(data.get("respiratorySupportResponse")):
        push("respiratory_support_response", "Record the respiratory support effectiveness/response.")
    if support_status == "UNABLE_TO_VERIFY" and not _text_filled(data.get("respiratorySupportUnableToVerifyReason")):
        push(
            "respiratory_support_unable_to_verify_reason",
            "Record why respiratory support could not be verified.",
        )

    return gaps
