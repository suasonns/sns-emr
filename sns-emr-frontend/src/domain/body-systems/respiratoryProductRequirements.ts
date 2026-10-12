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
  /** FINAL PRODUCT-OWNER DIRECTIVE: documents the patient's observed
   * clinical response for INITIATED/ALREADY_IN_PLACE. See
   * respiratoryFieldInventory.ts's RESPIRATORY_CLINICAL_RESPONSE_FIELD. */
  clinicalResponse?: string;

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
  /** Independent finding -- can coexist with Productive or Non-productive coughType. Not a coughType value. */
  hemoptysisPresent?: boolean;
  /** Independent thoracic-inspection finding -- not a cough characteristic. */
  barrelChestPresent?: boolean;
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
  // Hospice-admission simplification (product-owner directive): Configured
  // Requirement Response / Configured Follow-Up Status were removed from
  // the admission workflow UI along with the rest of the Treatment
  // section's secondary fields (Treatment Action Date/Time, Response,
  // Response Status/Time, Follow-Up Timing Plan/Responsible Clinician, POC
  // Review Need/Reason/Source Reference — see RespiratoryPanel.tsx's
  // LEGACY_HIDDEN_FIELD_IDS). No requirement is ever raised for
  // `respiratory_configured_follow_up_status` now, since the nurse has no
  // visible control to resolve it.

  // --- Section 5: Treatment decision -----------------------------------
  // "Treatment decision applicable" is operationalized as: dyspnea is
  // documented beyond None, OR an abnormal finding requiring disposition
  // is present (productive/hemoptysis cough, oxygen in use, respiratory
  // support in use). This mirrors the spec's own enumerated triggers.
  const treatmentApplicable =
    Boolean(values.sobSeverity && values.sobSeverity !== "None") ||
    values.coughType === "Productive" ||
    Boolean(values.hemoptysisPresent) ||
    values.oxygenUse === "YES" ||
    values.respiratorySupportStatus === "IN_USE";
  if (treatmentApplicable && !values.treatmentDecision) {
    push("respiratory_treatment_decision", "Record the treatment decision.");
  }
  // FINAL PRODUCT-OWNER DIRECTIVE (clinical workflow / data-ownership
  // correction): the free-text "Describe the treatment" requirement for
  // INITIATED/ALREADY_IN_PLACE is REMOVED — it let a nurse re-enter
  // medication/order details (drug, dose, route, frequency) that belong
  // exclusively to the authoritative Orders/Medications workflow, a data-
  // ownership defect, not a training issue. Treatment Decision itself
  // (INITIATED/ALREADY_IN_PLACE/DECLINED/NOT_INDICATED) is unchanged and
  // is never remapped. In its place, the two values now require the
  // Clinical Response (patient's observed response only — never an order).
  if (
    (values.treatmentDecision === "INITIATED" || values.treatmentDecision === "ALREADY_IN_PLACE") &&
    !values.clinicalResponse
  ) {
    push("respiratory_clinical_response", "Record the clinical response to the current treatment.");
  }
  // Hospice-admission simplification (product-owner directive): DECLINED
  // reuses the single canonical Treatment Narrative field
  // (`treatmentDescription`, presented contextually as "Decline Reason" —
  // see RespiratoryPanel.tsx's treatmentDescriptionContext()). There is no
  // longer a separate `respiratory_treatment_decline_reason` field in the
  // admission workflow.
  if (values.treatmentDecision === "DECLINED" && !textFilled(values.treatmentDescription)) {
    push("respiratory_treatment_description", "Record the reason treatment was declined.");
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
  // Hospice-admission correction (product-owner directive): Treatment
  // Response / Response Status / Response Time / Action Time are never
  // required for "Complete System Review" on the Initial Comprehensive
  // Assessment, for ANY Treatment Decision value (INITIATED,
  // ALREADY_IN_PLACE, DECLINED, or NOT_INDICATED). A hospice RN frequently
  // documents an intervention a family member, caregiver, or facility
  // already performed before the RN arrived, and cannot know its exact
  // action time or response — response/effectiveness is routinely
  // evaluated on a later follow-up visit, not at admission. These fields
  // remain fully enterable (optional) but must never block completion.
  // Date fields (e.g. respiratory_treatment_action_date) may remain
  // required/optional per their own existing rules — unaffected here.

  // --- Section 6: Finding-level follow-up / POC review ------------------
  // Hospice-admission simplification (product-owner directive): Follow-Up
  // Timing Plan, Follow-Up Responsible Clinician, and POC Review
  // Need/Reason were removed from the admission workflow UI entirely
  // (RespiratoryPanel.tsx's LEGACY_HIDDEN_FIELD_IDS) — only whether
  // follow-up is needed at all is recorded now. Requiring their
  // sub-fields here would permanently block completion since the nurse
  // has no visible control to resolve them.
  const findingLevelFollowUpApplicable = treatmentApplicable;
  if (findingLevelFollowUpApplicable && !values.followUpNeed) {
    push("respiratory_follow_up_need", "Record whether Respiratory follow-up is needed.");
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
  // PRODUCT-OWNER DIRECTIVE ("REMOVE Measured Oxygen Flow / Concentration"):
  // duplicate charting — the Oxygen Flow Rate documented above IS the flow
  // SpO2 was measured on. A second free-text re-entry of the same fact is
  // never required (see RESPIRATORY_MEASURED_OXYGEN_FLOW_OR_CONCENTRATION_FIELD
  // in respiratoryFieldInventory.ts and LEGACY_HIDDEN_FIELD_IDS in
  // RespiratoryPanel.tsx).
  //
  // PRODUCT-OWNER DIRECTIVE ("REMOVE O2 EFFECTIVENESS / RESPONSE"): SpO2
  // Value + SpO2 Measurement Condition already serve as the objective
  // oxygen-treatment outcome measure. A separate subjective
  // effective/ineffective field is never required (see
  // RESPIRATORY_OXYGEN_EFFECTIVENESS_RESPONSE_FIELD and
  // LEGACY_HIDDEN_FIELD_IDS in RespiratoryPanel.tsx).

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
  const coughRequiresAction = values.coughType === "Productive" || Boolean(values.hemoptysisPresent);
  if (values.hemoptysisPresent && !textFilled(values.coughClinicalSignificance)) {
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
  // PRODUCT-OWNER DIRECTIVE ("FINAL RESPIRATORY USABILITY REVIEW" --
  // A=Assessment Finding vs B=Future Plan): coughFollowUpTimingPlan /
  // coughFollowUpResponsibleClinician documented *who will do what, when,
  // in the future* -- POC's purpose (goals, interventions, follow-up
  // actions, treatment plans), not RNICA's (assessment, findings,
  // clinical status, clinical response). Same classification and
  // disposition as the already-retired respiratory_support_follow_up_plan.
  // Never required going forward; see RESPIRATORY_COUGH_FOLLOW_UP_* fields
  // in respiratoryFieldInventory.ts and LEGACY_HIDDEN_FIELD_IDS in
  // RespiratoryPanel.tsx.

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
