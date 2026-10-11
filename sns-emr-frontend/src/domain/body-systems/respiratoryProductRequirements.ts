/**
 * SNS Body Systems — Respiratory product-owner-authorized requirement
 * engine.
 *
 * Implements the required/conditional-visibility rules from the written
 * product-owner Respiratory field specification ("PRODUCT-OWNER
 * AUTHORIZATION: COMPLETE THE RESPIRATORY FIELD SPECIFICATION", session
 * record) for every field added in `respiratoryFieldInventory.ts`'s
 * "Product-owner-authorized canonical fields" section. This is
 * deliberately a SEPARATE module from `respiratoryWorkflowRules.ts` (the
 * original situation-branch/exception engine) rather than an extension of
 * it: the original engine evaluates the legacy-ported field set against
 * `stateMachine.ts`'s generic situation-requirement graph, while this
 * engine evaluates the newly-authorized field set against the explicit,
 * field-specific "required when" rules the specification itself states.
 * Mixing the two would make either graph harder to audit against its own
 * source document.
 *
 * Policy applied uniformly (specification section 11):
 * - top-level review decisions (assessmentContext, oxygenUse,
 *   respiratorySupportStatus) are always required for completion;
 * - conditional detail is required only once its triggering response is
 *   entered;
 * - optional notes remain optional;
 * - blank never means normal and is never silently satisfied;
 * - these requirements only block the explicit "Complete System Review"
 *   action — draft save is never blocked (see `RespiratoryPanel.tsx`'s
 *   `handleSaveDraft`, which never calls this module).
 */

export interface RespiratoryProductOxygenTherapyValues {
  deliveryDevice?: string;
  otherDevice?: string;
  flowValue?: number;
  flowUnit?: string;
  frequency?: string;
  hoursPerDay?: string;
  deliveryMode?: string;
}

export interface RespiratoryProductVentilatorValues {
  duration?: string;
  settingsSource?: string;
  settingsDate?: string;
  settingsTime?: string;
}

/** The product-owner-authorized field subset this module evaluates. */
export interface RespiratoryProductAuthorizedValues {
  assessmentContext?: string;
  clinicalComparison?: string;
  clinicalStatusChangeDetail?: string;

  comfortFunctionImpact?: string;
  comfortFunctionEvidence?: string;
  configuredRequirementResponse?: string;
  configuredFollowUpStatus?: string;

  treatmentDecision?: string;
  treatmentDescription?: string;
  treatmentDeclineReason?: string;
  treatmentActionDate?: string;
  treatmentActionTime?: string;
  treatmentResponse?: string;
  treatmentResponseStatus?: string;

  followUpNeed?: string;
  followUpTimingPlan?: string;
  followUpResponsibleClinician?: string;
  pocReviewNeed?: string;
  pocReviewReason?: string;

  oxygenUse?: string;
  oxygenUnableToVerifyReason?: string;
  oxygenTherapy?: RespiratoryProductOxygenTherapyValues;
  spo2Value?: number;
  spo2MeasurementCondition?: string;
  spo2NotObtainedReason?: string;
  measuredOxygenFlowOrConcentration?: string;
  oxygenMeasurementDate?: string;
  oxygenMeasurementTime?: string;
  oxygenEffectivenessResponse?: string;

  coughType?: string;
  sputumCharacter?: string;
  sputumAmount?: string;
  sputumColor?: string;
  sputumOtherSpecification?: string;
  coughClinicalSignificance?: string;
  coughActionDecision?: string;
  coughActionDescription?: string;
  coughDeclineReason?: string;
  coughResponse?: string;
  coughActionDateTime?: string;
  coughFollowUpTimingPlan?: string;
  coughFollowUpResponsibleClinician?: string;

  sobSeverity?: string;
  respiratorySupportStatus?: string;
  respiratorySupportTypes?: readonly string[];
  ventilator?: RespiratoryProductVentilatorValues;
  airwaySiteFindings?: string;
  respiratorySupportResponse?: string;
  respiratorySupportFollowUpPlan?: string;
  respiratorySupportUnableToVerifyReason?: string;
}

export interface RespiratoryProductRequirementGap {
  fieldId: string;
  message: string;
}

export function textFilled(value: string | undefined): boolean {
  return Boolean(value && value.trim().length > 0);
}

/**
 * Returns every unresolved product-owner-authorized requirement for the
 * current values. An empty array means "Complete System Review" is not
 * blocked by this engine (the original `respiratoryWorkflowRules.ts`
 * engine is evaluated separately and independently).
 */
export function getMissingProductAuthorizedRequirements(
  values: RespiratoryProductAuthorizedValues,
): RespiratoryProductRequirementGap[] {
  const gaps: RespiratoryProductRequirementGap[] = [];
  const push = (fieldId: string, message: string) => gaps.push({ fieldId, message });

  // --- Section 3: Assessment context & comparison ---------------------
  if (!values.assessmentContext) {
    push("respiratory_assessment_context", "Record the Respiratory assessment context.");
  }
  if (!values.clinicalComparison) {
    push("respiratory_clinical_comparison", "Record the comparison to the prior Respiratory assessment.");
  }
  if (values.clinicalComparison === "CHANGED_FROM_PRIOR" && !textFilled(values.clinicalStatusChangeDetail)) {
    push("respiratory_clinical_status_change_detail", "Describe the change from the prior assessment.");
  }

  // --- Section 4: Comfort / function -----------------------------------
  const requiresComfortFunction =
    values.assessmentContext === "CURRENT_CONCERNS_ASSESSED" || values.assessmentContext === "UNABLE_TO_FULLY_ASSESS";
  if (requiresComfortFunction && !values.comfortFunctionImpact) {
    push("respiratory_comfort_function_impact", "Record the comfort/functional impact.");
  }
  if (values.comfortFunctionImpact === "IMPACT_PRESENT" && !textFilled(values.comfortFunctionEvidence)) {
    push("respiratory_comfort_function_evidence", "Describe the comfort/function evidence.");
  }
  if (values.comfortFunctionImpact === "UNABLE_TO_ASSESS" && !textFilled(values.comfortFunctionEvidence)) {
    push("respiratory_comfort_function_evidence", "Describe why comfort/function could not be evaluated.");
  }
  if (
    values.configuredRequirementResponse &&
    values.configuredRequirementResponse !== "NOT_APPLICABLE" &&
    values.configuredRequirementResponse === "FOLLOW_UP_REQUIRED" &&
    !values.configuredFollowUpStatus
  ) {
    push("respiratory_configured_follow_up_status", "Record the configured follow-up status.");
  }

  // --- Section 5: Treatment decision -----------------------------------
  // "Treatment decision applicable" is operationalized as: dyspnea is
  // documented beyond None, OR an abnormal finding requiring disposition
  // is present (productive/hemoptysis cough, oxygen in use, respiratory
  // support in use). This mirrors the spec's own enumerated triggers.
  const treatmentApplicable =
    Boolean(values.sobSeverity && values.sobSeverity !== "None") ||
    values.coughType === "Productive" ||
    values.coughType === "Hemoptysis" ||
    values.oxygenUse === "YES" ||
    values.respiratorySupportStatus === "IN_USE";
  if (treatmentApplicable && !values.treatmentDecision) {
    push("respiratory_treatment_decision", "Record the treatment decision.");
  }
  if (values.treatmentDecision === "INITIATED" || values.treatmentDecision === "ALREADY_IN_PLACE") {
    if (!textFilled(values.treatmentDescription)) {
      push("respiratory_treatment_description", "Describe the treatment.");
    }
  }
  if (values.treatmentDecision === "DECLINED" && !textFilled(values.treatmentDeclineReason)) {
    push("respiratory_treatment_decline_reason", "Record the reason treatment was declined.");
  }
  // NOT_INDICATED reuses the same canonical `treatmentDescription` field,
  // displayed contextually as "Clinical Rationale" (see RespiratoryPanel.tsx's
  // treatmentDescriptionContext()), rather than adding a second rationale
  // field. It is required only when a significant finding would otherwise
  // require disposition (the same `treatmentApplicable` trigger used to
  // require the Treatment Decision itself) — NOT_INDICATED never bypasses
  // an unresolved significant finding, but also never demands an
  // explanation when no significant finding exists.
  if (values.treatmentDecision === "NOT_INDICATED" && treatmentApplicable && !textFilled(values.treatmentDescription)) {
    push("respiratory_treatment_description", "Record the clinical rationale for not indicating Respiratory treatment.");
  }
  if (values.treatmentDecision && values.treatmentDecision !== "NOT_INDICATED" && !values.treatmentResponseStatus) {
    push("respiratory_treatment_response_status", "Record the treatment response status.");
  }
  if (
    values.treatmentDecision === "INITIATED" &&
    values.treatmentResponseStatus !== "PENDING" &&
    !textFilled(values.treatmentResponse)
  ) {
    push("respiratory_treatment_response", "Record the observed/reported treatment response.");
  }
  if (
    values.treatmentDecision === "ALREADY_IN_PLACE" &&
    (values.treatmentResponseStatus === "OBSERVED" || values.treatmentResponseStatus === "REPORTED") &&
    !textFilled(values.treatmentResponse)
  ) {
    push("respiratory_treatment_response", "Record the current treatment effectiveness.");
  }

  // --- Section 6: Finding-level follow-up / POC review ------------------
  const findingLevelFollowUpApplicable = treatmentApplicable;
  if (findingLevelFollowUpApplicable && !values.followUpNeed) {
    push("respiratory_follow_up_need", "Record whether Respiratory follow-up is needed.");
  }
  if (values.followUpNeed === "NEEDED") {
    if (!textFilled(values.followUpTimingPlan)) {
      push("respiratory_follow_up_timing_plan", "Record the follow-up timing/plan.");
    }
    if (!textFilled(values.followUpResponsibleClinician)) {
      push("respiratory_follow_up_responsible_clinician", "Record who is responsible for Respiratory follow-up.");
    }
  }
  if (values.pocReviewNeed === "REVIEW_NEEDED" && !textFilled(values.pocReviewReason)) {
    push("respiratory_poc_review_reason", "Record why Plan of Care review is needed.");
  }

  // --- Section 7: Oxygen -------------------------------------------------
  if (!values.oxygenUse) {
    push("respiratory_oxygen_use", "Record whether oxygen is in use.");
  }
  if (values.oxygenUse === "UNABLE_TO_VERIFY" && !textFilled(values.oxygenUnableToVerifyReason)) {
    push("respiratory_oxygen_unable_to_verify_reason", "Record why oxygen use could not be verified.");
  }
  if (values.oxygenUse === "YES") {
    if (!values.oxygenTherapy?.deliveryDevice) {
      push("respiratory_oxygen_delivery_device", "Record the oxygen delivery device.");
    }
    if (values.oxygenTherapy?.deliveryDevice === "OTHER" && !textFilled(values.oxygenTherapy?.otherDevice)) {
      push("respiratory_oxygen_other_device", "Specify the oxygen delivery device.");
    }
    if (!values.oxygenTherapy?.frequency) {
      push("respiratory_oxygen_frequency", "Record the oxygen frequency.");
    }
  }
  const usesLitersPerMinute = values.oxygenTherapy?.flowUnit === "L_MIN";
  if (values.oxygenUse === "YES" && usesLitersPerMinute && values.oxygenTherapy?.flowValue === undefined) {
    push("respiratory_oxygen_flow_value", "Record the oxygen flow value.");
  }
  if (values.spo2Value !== undefined && !values.spo2MeasurementCondition) {
    push("respiratory_spo2_measurement_condition", "Record the SpO2 measurement condition.");
  }
  if (values.spo2MeasurementCondition === "NOT_OBTAINED" && !textFilled(values.spo2NotObtainedReason)) {
    push("respiratory_spo2_not_obtained_reason", "Record why SpO2 was not obtained.");
  }
  if (values.spo2Value !== undefined) {
    if (!textFilled(values.oxygenMeasurementDate)) {
      push("respiratory_oxygen_measurement_date", "Record the SpO2 measurement date.");
    }
    if (!textFilled(values.oxygenMeasurementTime)) {
      push("respiratory_oxygen_measurement_time", "Record the SpO2 measurement time.");
    }
  }
  if (
    values.spo2MeasurementCondition === "ON_OXYGEN" &&
    values.spo2Value !== undefined &&
    !textFilled(values.measuredOxygenFlowOrConcentration)
  ) {
    push("respiratory_measured_oxygen_flow_or_concentration", "Record the measured oxygen flow/concentration.");
  }
  if (
    (values.oxygenUse === "YES" || (values.treatmentDecision && values.treatmentDecision !== "NOT_INDICATED")) &&
    !textFilled(values.oxygenEffectivenessResponse)
  ) {
    push("respiratory_oxygen_effectiveness_response", "Record oxygen/treatment effectiveness or response.");
  }

  // --- Section 8: Cough and secretions ------------------------------------
  if (!values.coughType) {
    push("respiratory_cough_type", "Record the cough type.");
  }
  if (values.coughType === "Productive") {
    if (!values.sputumAmount) {
      push("respiratory_sputum_amount", "Record the sputum amount.");
    }
    if (!values.sputumColor) {
      push("respiratory_sputum_color", "Record the sputum color.");
    }
  }
  if (
    (values.sputumCharacter === "OTHER" || values.sputumColor === "OTHER") &&
    !textFilled(values.sputumOtherSpecification)
  ) {
    push("respiratory_sputum_other_specification", "Specify the sputum character/color.");
  }
  const coughRequiresAction = values.coughType === "Productive" || values.coughType === "Hemoptysis";
  if (values.coughType === "Hemoptysis" && !textFilled(values.coughClinicalSignificance)) {
    push("respiratory_cough_clinical_significance", "Record the clinical significance of hemoptysis.");
  }
  if (coughRequiresAction && !values.coughActionDecision) {
    push("respiratory_cough_action_decision", "Record the cough action decision.");
  }
  if (values.coughActionDecision === "ACTION_TAKEN") {
    if (!textFilled(values.coughActionDescription)) {
      push("respiratory_cough_action_description", "Describe the action taken for cough/secretions.");
    }
    if (!textFilled(values.coughResponse)) {
      push("respiratory_cough_response", "Record the response to the cough/secretions action.");
    }
    if (!textFilled(values.coughActionDateTime)) {
      push("respiratory_cough_action_date_time", "Record when the cough/secretions action occurred.");
    }
  }
  if (values.coughActionDecision === "DECLINED" && !textFilled(values.coughDeclineReason)) {
    push("respiratory_cough_decline_reason", "Record why the cough/secretions action was declined.");
  }
  if (
    (values.coughActionDecision === "ACTION_TAKEN" || values.coughActionDecision === "DECLINED") &&
    (!textFilled(values.coughFollowUpTimingPlan) || !textFilled(values.coughFollowUpResponsibleClinician))
  ) {
    if (!textFilled(values.coughFollowUpTimingPlan)) {
      push("respiratory_cough_follow_up_timing_plan", "Record the cough/secretions follow-up timing/plan.");
    }
    if (!textFilled(values.coughFollowUpResponsibleClinician)) {
      push("respiratory_cough_follow_up_responsible_clinician", "Record who is responsible for cough/secretions follow-up.");
    }
  }

  // --- Section 9: Respiratory support and airway --------------------------
  if (!values.respiratorySupportStatus) {
    push("respiratory_support_status", "Record the respiratory support status.");
  }
  if (values.respiratorySupportStatus === "IN_USE" && (!values.respiratorySupportTypes || values.respiratorySupportTypes.length === 0)) {
    push("respiratory_support_types", "Record the respiratory support type(s) in use.");
  }
  const supportTypes = values.respiratorySupportTypes ?? [];
  if (supportTypes.includes("VENTILATOR")) {
    if (!values.ventilator?.duration) {
      push("respiratory_ventilator_duration", "Record whether the ventilator is short-term or long-term.");
    }
  }
  if (supportTypes.includes("TRACHEOSTOMY")) {
    if (!textFilled(values.airwaySiteFindings)) {
      push("respiratory_airway_site_findings", "Record the airway/tracheostomy site findings.");
    }
  }
  if (values.respiratorySupportStatus === "IN_USE" && !textFilled(values.respiratorySupportResponse)) {
    push("respiratory_support_response", "Record the respiratory support effectiveness/response.");
  }
  if (values.respiratorySupportStatus === "UNABLE_TO_VERIFY" && !textFilled(values.respiratorySupportUnableToVerifyReason)) {
    push("respiratory_support_unable_to_verify_reason", "Record why respiratory support could not be verified.");
  }

  return gaps;
}
