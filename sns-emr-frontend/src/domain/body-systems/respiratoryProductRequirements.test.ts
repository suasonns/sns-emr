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
    expect(fieldIds({ coughType: "Hemoptysis" })).toContain("respiratory_treatment_decision");
    expect(fieldIds({ oxygenUse: "YES" })).toContain("respiratory_treatment_decision");
    expect(fieldIds({ respiratorySupportStatus: "IN_USE" })).toContain("respiratory_treatment_decision");
    expect(fieldIds({ sobSeverity: "None" })).not.toContain("respiratory_treatment_decision");
  });

  it("requires treatmentDescription for INITIATED and ALREADY_IN_PLACE, not for DECLINED/NOT_INDICATED", () => {
    expect(fieldIds({ treatmentDecision: "INITIATED" })).toContain("respiratory_treatment_description");
    expect(fieldIds({ treatmentDecision: "ALREADY_IN_PLACE" })).toContain("respiratory_treatment_description");
    expect(fieldIds({ treatmentDecision: "DECLINED" })).not.toContain("respiratory_treatment_description");
    expect(fieldIds({ treatmentDecision: "NOT_INDICATED" })).not.toContain("respiratory_treatment_description");
  });

  it("requires treatmentDeclineReason only when DECLINED", () => {
    expect(fieldIds({ treatmentDecision: "DECLINED" })).toContain("respiratory_treatment_decline_reason");
    expect(fieldIds({ treatmentDecision: "INITIATED" })).not.toContain("respiratory_treatment_decline_reason");
  });

  it("never requires treatment-decision detail fields when NOT_INDICATED", () => {
    const missing = fieldIds({ treatmentDecision: "NOT_INDICATED" });
    expect(missing).not.toContain("respiratory_treatment_description");
    expect(missing).not.toContain("respiratory_treatment_decline_reason");
    expect(missing).not.toContain("respiratory_treatment_response_status");
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

  it("requires measurement condition, date, and time once an SpO2 value is entered", () => {
    const missing = fieldIds({ spo2Value: 94 });
    expect(missing).toContain("respiratory_spo2_measurement_condition");
    expect(missing).toContain("respiratory_oxygen_measurement_date");
    expect(missing).toContain("respiratory_oxygen_measurement_time");
  });

  it("requires spo2NotObtainedReason only when condition = NOT_OBTAINED", () => {
    expect(fieldIds({ spo2MeasurementCondition: "NOT_OBTAINED" })).toContain(
      "respiratory_spo2_not_obtained_reason",
    );
    expect(fieldIds({ spo2MeasurementCondition: "ON_ROOM_AIR" })).not.toContain(
      "respiratory_spo2_not_obtained_reason",
    );
  });

  it("requires measuredOxygenFlowOrConcentration only when measured on oxygen", () => {
    expect(
      fieldIds({ spo2Value: 92, spo2MeasurementCondition: "ON_OXYGEN" }),
    ).toContain("respiratory_measured_oxygen_flow_or_concentration");
    expect(
      fieldIds({ spo2Value: 92, spo2MeasurementCondition: "ON_ROOM_AIR" }),
    ).not.toContain("respiratory_measured_oxygen_flow_or_concentration");
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

  it("requires coughClinicalSignificance only for Hemoptysis", () => {
    expect(fieldIds({ coughType: "Hemoptysis" })).toContain("respiratory_cough_clinical_significance");
    expect(fieldIds({ coughType: "Productive" })).not.toContain("respiratory_cough_clinical_significance");
  });

  it("requires coughActionDecision for Productive/Hemoptysis only", () => {
    expect(fieldIds({ coughType: "Productive" })).toContain("respiratory_cough_action_decision");
    expect(fieldIds({ coughType: "Hemoptysis" })).toContain("respiratory_cough_action_decision");
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

  it("requires timing plan and responsible clinician only when follow-up is needed", () => {
    const missing = fieldIds({ oxygenUse: "YES", followUpNeed: "NEEDED" });
    expect(missing).toContain("respiratory_follow_up_timing_plan");
    expect(missing).toContain("respiratory_follow_up_responsible_clinician");
    expect(fieldIds({ oxygenUse: "YES", followUpNeed: "NOT_NEEDED" })).not.toContain(
      "respiratory_follow_up_timing_plan",
    );
  });

  it("requires pocReviewReason only when review is needed", () => {
    expect(fieldIds({ pocReviewNeed: "REVIEW_NEEDED" })).toContain("respiratory_poc_review_reason");
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
