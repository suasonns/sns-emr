import { describe, expect, it } from "vitest";
import {
  getMissingProductAuthorizedRequirements,
  type RespiratoryProductAuthorizedValues,
} from "./respiratoryProductRequirements";

function fieldIds(values: RespiratoryProductAuthorizedValues): string[] {
  return getMissingProductAuthorizedRequirements(values).map((gap) => gap.fieldId);
}

describe("respiratoryProductRequirements — assessment context & comparison", () => {
  it("requires assessmentContext and clinicalComparison on an empty record", () => {
    const missing = fieldIds({});
    expect(missing).toContain("respiratory_assessment_context");
    expect(missing).toContain("respiratory_clinical_comparison");
  });

  it("requires clinicalStatusChangeDetail only when comparison is CHANGED_FROM_PRIOR", () => {
    expect(fieldIds({ clinicalComparison: "NO_CHANGE" })).not.toContain("respiratory_clinical_status_change_detail");
    expect(fieldIds({ clinicalComparison: "CHANGED_FROM_PRIOR" })).toContain(
      "respiratory_clinical_status_change_detail",
    );
    expect(
      fieldIds({ clinicalComparison: "CHANGED_FROM_PRIOR", clinicalStatusChangeDetail: "New wheeze noted" }),
    ).not.toContain("respiratory_clinical_status_change_detail");
  });
});

describe("respiratoryProductRequirements — comfort/function", () => {
  it("requires comfortFunctionImpact once assessment context is current-concerns", () => {
    expect(fieldIds({ assessmentContext: "CURRENT_CONCERNS_ASSESSED" })).toContain(
      "respiratory_comfort_function_impact",
    );
  });

  it("requires comfortFunctionEvidence when impact is present or unable-to-assess, not otherwise", () => {
    expect(fieldIds({ comfortFunctionImpact: "NO_IMPACT" })).not.toContain("respiratory_comfort_function_evidence");
    expect(fieldIds({ comfortFunctionImpact: "IMPACT_PRESENT" })).toContain("respiratory_comfort_function_evidence");
    expect(fieldIds({ comfortFunctionImpact: "UNABLE_TO_ASSESS" })).toContain(
      "respiratory_comfort_function_evidence",
    );
    expect(
      fieldIds({ comfortFunctionImpact: "IMPACT_PRESENT", comfortFunctionEvidence: "Reports distress on exertion" }),
    ).not.toContain("respiratory_comfort_function_evidence");
  });
});

describe("respiratoryProductRequirements — treatment decision", () => {
  it("is not required when nothing clinically applicable is documented", () => {
    expect(fieldIds({})).not.toContain("respiratory_treatment_decision");
  });

  it("becomes required once dyspnea, productive/hemoptysis cough, oxygen use, or active support is documented", () => {
    expect(fieldIds({ sobSeverity: "Moderate" })).toContain("respiratory_treatment_decision");
    expect(fieldIds({ coughType: "Productive" })).toContain("respiratory_treatment_decision");
    expect(fieldIds({ hemoptysisPresent: true })).toContain("respiratory_treatment_decision");
    expect(fieldIds({ oxygenUse: "YES" })).toContain("respiratory_treatment_decision");
    expect(fieldIds({ respiratorySupportStatus: "IN_USE" })).toContain("respiratory_treatment_decision");
    expect(fieldIds({ sobSeverity: "None" })).not.toContain("respiratory_treatment_decision");
  });

  it("requires clinicalResponse for INITIATED and ALREADY_IN_PLACE (not treatmentDescription)", () => {
    // FINAL PRODUCT-OWNER DIRECTIVE: the free-text "Treatment /
    // Intervention" box let a nurse re-enter medication/order details that
    // belong exclusively to the authoritative Orders/Medications workflow.
    // It is removed as a requirement for these two decisions and replaced
    // by Clinical Response to Treatment (the patient's observed response
    // only — never an order).
    expect(fieldIds({ treatmentDecision: "INITIATED" })).toContain("respiratory_clinical_response");
    expect(fieldIds({ treatmentDecision: "ALREADY_IN_PLACE" })).toContain("respiratory_clinical_response");
    expect(fieldIds({ treatmentDecision: "INITIATED" })).not.toContain("respiratory_treatment_description");
    expect(fieldIds({ treatmentDecision: "ALREADY_IN_PLACE" })).not.toContain("respiratory_treatment_description");
    expect(
      fieldIds({ treatmentDecision: "INITIATED", clinicalResponse: "EFFECTIVE" }),
    ).not.toContain("respiratory_clinical_response");
  });

  // Hospice-admission simplification (product-owner directive): DECLINED
  // reuses the single canonical Treatment Narrative field
  // (`treatmentDescription`, presented contextually as "Decline Reason")
  // instead of a separate `treatmentDeclineReason` field — there is no
  // longer a separate requirement/field for decline reason.
  it("requires treatmentDescription (as the Decline Reason) only when DECLINED", () => {
    expect(fieldIds({ treatmentDecision: "DECLINED" })).toContain("respiratory_treatment_description");
    expect(fieldIds({ treatmentDecision: "DECLINED", treatmentDescription: "Family declined nebulizer" })).not.toContain(
      "respiratory_treatment_description",
    );
  });

  it("never requires treatment-decision detail fields when NOT_INDICATED and nothing clinically applicable", () => {
    const missing = fieldIds({ treatmentDecision: "NOT_INDICATED" });
    expect(missing).not.toContain("respiratory_treatment_description");
    expect(missing).not.toContain("respiratory_treatment_response_status");
  });

  it("hospice workflow correction: never requires Treatment Response, Response Status, Action Time, or Response Time, for any Treatment Decision value", () => {
    // A hospice RN is frequently documenting a caregiver-, family-, or
    // facility-administered intervention that occurred before the RN
    // arrived. Response/effectiveness is routinely assessed on a later
    // follow-up visit, not at the Initial Comprehensive Assessment.
    for (const treatmentDecision of ["INITIATED", "ALREADY_IN_PLACE", "DECLINED", "NOT_INDICATED"] as const) {
      const missing = fieldIds({ treatmentDecision });
      expect(missing).not.toContain("respiratory_treatment_response_status");
      expect(missing).not.toContain("respiratory_treatment_response");
      expect(missing).not.toContain("respiratory_treatment_action_time");
      expect(missing).not.toContain("respiratory_treatment_response_time");
    }
  });
});

describe("respiratoryProductRequirements — oxygen", () => {
  it("requires oxygenUse on an empty record", () => {
    expect(fieldIds({})).toContain("respiratory_oxygen_use");
  });

  it("requires oxygenUnableToVerifyReason only when oxygenUse = UNABLE_TO_VERIFY", () => {
    expect(fieldIds({ oxygenUse: "UNABLE_TO_VERIFY" })).toContain("respiratory_oxygen_unable_to_verify_reason");
    expect(fieldIds({ oxygenUse: "NO" })).not.toContain("respiratory_oxygen_unable_to_verify_reason");
  });

  it("requires delivery device and frequency once oxygen is in use", () => {
    const missing = fieldIds({ oxygenUse: "YES" });
    expect(missing).toContain("respiratory_oxygen_delivery_device");
    expect(missing).toContain("respiratory_oxygen_frequency");
  });

  it("requires otherDevice only when deliveryDevice = OTHER", () => {
    expect(
      fieldIds({ oxygenUse: "YES", oxygenTherapy: { deliveryDevice: "NASAL_CANNULA", frequency: "CONTINUOUS" } }),
    ).not.toContain("respiratory_oxygen_other_device");
    expect(
      fieldIds({ oxygenUse: "YES", oxygenTherapy: { deliveryDevice: "OTHER", frequency: "CONTINUOUS" } }),
    ).toContain("respiratory_oxygen_other_device");
  });

  it("requires flowValue only when flowUnit = L_MIN", () => {
    expect(
      fieldIds({
        oxygenUse: "YES",
        oxygenTherapy: { deliveryDevice: "NASAL_CANNULA", frequency: "CONTINUOUS", flowUnit: "PERCENT" },
      }),
    ).not.toContain("respiratory_oxygen_flow_value");
    expect(
      fieldIds({
        oxygenUse: "YES",
        oxygenTherapy: { deliveryDevice: "NASAL_CANNULA", frequency: "CONTINUOUS", flowUnit: "L_MIN" },
      }),
    ).toContain("respiratory_oxygen_flow_value");
  });

  it("requires measurement condition once an SpO2 value is entered", () => {
    const missing = fieldIds({ spo2Value: 94 });
    expect(missing).toContain("respiratory_spo2_measurement_condition");
  });

  // PRODUCT-OWNER DIRECTIVE ("REMOVE OXYGEN MEASUREMENT DATE AND TIME"):
  // RNICA is visit-based -- Visit Date / Time In / Time Out already supply
  // the timing context for an SpO2 documented during the current visit, so
  // these two fields must never be required, regardless of SpO2 value.
  it("never requires oxygen measurement date/time, even when an SpO2 value is entered", () => {
    const missing = fieldIds({ spo2Value: 94 });
    expect(missing).not.toContain("respiratory_oxygen_measurement_date");
    expect(missing).not.toContain("respiratory_oxygen_measurement_time");
  });

  it("requires spo2NotObtainedReason only when condition = NOT_OBTAINED", () => {
    expect(fieldIds({ spo2MeasurementCondition: "NOT_OBTAINED" })).toContain(
      "respiratory_spo2_not_obtained_reason",
    );
    expect(fieldIds({ spo2MeasurementCondition: "ON_ROOM_AIR" })).not.toContain(
      "respiratory_spo2_not_obtained_reason",
    );
  });

  // PRODUCT-OWNER DIRECTIVE ("REMOVE Measured Oxygen Flow / Concentration"):
  // duplicate charting -- the Oxygen Flow Rate documented under "Oxygen
  // use & measurement" IS the flow SpO2 was measured on, so a second
  // free-text re-entry of the same fact must never be required.
  it("never requires measuredOxygenFlowOrConcentration, even when measured on oxygen", () => {
    expect(
      fieldIds({ spo2Value: 92, spo2MeasurementCondition: "ON_OXYGEN" }),
    ).not.toContain("respiratory_measured_oxygen_flow_or_concentration");
    expect(
      fieldIds({ spo2Value: 92, spo2MeasurementCondition: "ON_ROOM_AIR" }),
    ).not.toContain("respiratory_measured_oxygen_flow_or_concentration");
  });

  // PRODUCT-OWNER DIRECTIVE ("REMOVE O2 EFFECTIVENESS / RESPONSE"): SpO2
  // Value + SpO2 Measurement Condition already serve as the objective
  // oxygen-treatment outcome measure, so a separate subjective
  // effective/ineffective field must never be required.
  it("never requires oxygenEffectivenessResponse, even when oxygen is in use or treatment is initiated", () => {
    expect(
      fieldIds({
        oxygenUse: "YES",
        oxygenTherapy: { deliveryDevice: "NASAL_CANNULA", frequency: "CONTINUOUS", flowUnit: "L_MIN", flowValue: 3 },
      }),
    ).not.toContain("respiratory_oxygen_effectiveness_response");
    expect(fieldIds({ treatmentDecision: "INITIATED" })).not.toContain(
      "respiratory_oxygen_effectiveness_response",
    );
  });
});

describe("respiratoryProductRequirements — cough and secretions", () => {
  it("requires coughType on an empty record", () => {
    expect(fieldIds({})).toContain("respiratory_cough_type");
  });

  it("requires sputumAmount and sputumColor only when coughType = Productive", () => {
    const missing = fieldIds({ coughType: "Productive" });
    expect(missing).toContain("respiratory_sputum_amount");
    expect(missing).toContain("respiratory_sputum_color");
    expect(fieldIds({ coughType: "Dry" })).not.toContain("respiratory_sputum_amount");
  });

  it("requires coughClinicalSignificance only when hemoptysisPresent", () => {
    expect(fieldIds({ hemoptysisPresent: true })).toContain("respiratory_cough_clinical_significance");
    expect(fieldIds({ coughType: "Productive" })).not.toContain("respiratory_cough_clinical_significance");
  });

  it("requires coughActionDecision for Productive cough or hemoptysisPresent only", () => {
    expect(fieldIds({ coughType: "Productive" })).toContain("respiratory_cough_action_decision");
    expect(fieldIds({ hemoptysisPresent: true })).toContain("respiratory_cough_action_decision");
    expect(fieldIds({ coughType: "Dry" })).not.toContain("respiratory_cough_action_decision");
  });

  it("requires action description/response/datetime only when ACTION_TAKEN", () => {
    const missing = fieldIds({ coughType: "Productive", coughActionDecision: "ACTION_TAKEN" });
    expect(missing).toContain("respiratory_cough_action_description");
    expect(missing).toContain("respiratory_cough_response");
    expect(missing).toContain("respiratory_cough_action_date_time");
  });

  it("requires coughDeclineReason only when DECLINED", () => {
    expect(fieldIds({ coughType: "Productive", coughActionDecision: "DECLINED" })).toContain(
      "respiratory_cough_decline_reason",
    );
  });
});

describe("respiratoryProductRequirements — respiratory support and airway", () => {
  it("requires respiratorySupportStatus on an empty record", () => {
    expect(fieldIds({})).toContain("respiratory_support_status");
  });

  it("requires support types only when status = IN_USE", () => {
    expect(fieldIds({ respiratorySupportStatus: "IN_USE" })).toContain("respiratory_support_types");
    expect(fieldIds({ respiratorySupportStatus: "NOT_IN_USE" })).not.toContain("respiratory_support_types");
  });

  it("requires ventilator.duration only when VENTILATOR is among the support types", () => {
    expect(
      fieldIds({ respiratorySupportStatus: "IN_USE", respiratorySupportTypes: ["VENTILATOR"] }),
    ).toContain("respiratory_ventilator_duration");
    expect(
      fieldIds({ respiratorySupportStatus: "IN_USE", respiratorySupportTypes: ["OXYGEN_CONCENTRATOR"] }),
    ).not.toContain("respiratory_ventilator_duration");
  });

  it("requires airwaySiteFindings only when TRACHEOSTOMY is among the support types", () => {
    expect(
      fieldIds({ respiratorySupportStatus: "IN_USE", respiratorySupportTypes: ["TRACHEOSTOMY"] }),
    ).toContain("respiratory_airway_site_findings");
  });

  it("requires respiratorySupportUnableToVerifyReason only when UNABLE_TO_VERIFY", () => {
    expect(fieldIds({ respiratorySupportStatus: "UNABLE_TO_VERIFY" })).toContain(
      "respiratory_support_unable_to_verify_reason",
    );
    expect(fieldIds({ respiratorySupportStatus: "NOT_IN_USE" })).not.toContain(
      "respiratory_support_unable_to_verify_reason",
    );
  });
});

describe("respiratoryProductRequirements — follow-up and POC review", () => {
  it("requires followUpNeed once a treatment-applicable finding is documented", () => {
    expect(fieldIds({ oxygenUse: "YES" })).toContain("respiratory_follow_up_need");
    expect(fieldIds({})).not.toContain("respiratory_follow_up_need");
  });

  // Hospice-admission simplification (product-owner directive): Follow-Up
  // Timing Plan / Responsible Clinician and POC Review Need/Reason were
  // removed from the admission workflow entirely — only whether follow-up
  // is needed at all is ever required.
  it("never requires follow-up timing plan or responsible clinician, even when follow-up is needed", () => {
    const missing = fieldIds({ oxygenUse: "YES", followUpNeed: "NEEDED" });
    expect(missing).not.toContain("respiratory_follow_up_timing_plan");
    expect(missing).not.toContain("respiratory_follow_up_responsible_clinician");
  });

  it("never requires pocReviewReason, even when review is needed", () => {
    expect(fieldIds({ pocReviewNeed: "REVIEW_NEEDED" })).not.toContain("respiratory_poc_review_reason");
    expect(fieldIds({ pocReviewNeed: "NOT_NEEDED" })).not.toContain("respiratory_poc_review_reason");
  });

  it("returns an empty array once every applicable requirement is satisfied for a minimal no-findings record", () => {
    const missing = getMissingProductAuthorizedRequirements({
      assessmentContext: "CURRENT_CONCERNS_ASSESSED",
      clinicalComparison: "NO_CHANGE",
      comfortFunctionImpact: "NO_IMPACT",
      oxygenUse: "NO",
      coughType: "None",
      respiratorySupportStatus: "NOT_IN_USE",
    });
    expect(missing).toEqual([]);
  });
});
