/**
 * SNS Respiratory ADR-004 Documentation Coverage.
 *
 * Implements `docs/architecture/decision-records/ADR-004-sns-documentation-coverage.md`
 * for the Respiratory body system, following the Neurological reference
 * implementation's item shape exactly
 * (`computeNeurologicalDocumentationCoverage` in `src/components/RNICA.jsx`):
 * each item is `{ key, label, complete, value, unresolvedHint, sourceFieldKeys }`.
 *
 * PRODUCT-OWNER DIRECTIVE ("RESPIRATORY COVERAGE MODEL" / "SNS COVERAGE
 * STANDARD"): Coverage is a Documentation Inventory, not a validation,
 * workflow, or completion engine. It shows what has been documented
 * alongside what remains undocumented, in one list, and suppresses items
 * that are not currently applicable rather than showing them as
 * unresolved. It must never include the legacy situation/requirement-key
 * engine's validation-aggregate concepts (current_confirmation,
 * current_finding_or_change, intervention_or_response, stable_existing) —
 * those remain in `getRespiratoryReviewCompletion`'s
 * `legacySituationMessages` and are surfaced separately in the panel's
 * "Legacy Respiratory Workflow Alerts" section, not here.
 *
 * The approved 27-item inventory and every `unresolvedHint` string below
 * were accepted by explicit product-owner review; the hint text is reused
 * verbatim from the already-approved `respiratoryProductRequirements.ts`
 * completion-blocker messages (same clinical guidance, now also used for
 * Coverage display) rather than inventing new copy.
 *
 * Unlike Neuro's static per-item `unresolvedHint` string, a small number
 * of Respiratory items need context-dependent guidance (e.g. "Treatment
 * Narrative" means a different thing for DECLINED vs. NOT_INDICATED) —
 * `unresolvedHint` here is therefore a function of the draft, not a
 * constant. This is the only structural difference from the Neuro
 * pattern; the output item shape is identical.
 */
import type { RespiratoryAssessmentValues } from "./respiratoryWorkflowRules";

/** This module reads the same assessment-values shape the legacy and product-authorized requirement engines evaluate -- not the feature-layer `RespiratoryDraft` (which merely extends it with load/save metadata), keeping this module domain-layer-only. */
type RespiratoryDraft = RespiratoryAssessmentValues;

/** One ADR-004 Documentation Coverage row. */
export interface RespiratoryCoverageItem {
  key: string;
  label: string;
  complete: boolean;
  /** The documented value, formatted for display. Null when `complete` is false. */
  value: string | null;
  /** The exact unresolved requirement, shown instead of `value` when `complete` is false. Null when `complete` is true. */
  unresolvedHint: string | null;
  /** Field IDs (from `respiratoryFieldInventory.ts`) this item is sourced from. */
  sourceFieldKeys: string[];
}

interface RespiratoryCoverageItemConfig {
  key: string;
  label: string;
  sourceFieldKeys: string[];
  /** Whether this item is currently applicable. Non-applicable items are omitted entirely, never shown as unresolved. */
  applicable: (d: RespiratoryDraft) => boolean;
  check: (d: RespiratoryDraft) => boolean;
  summarize: (d: RespiratoryDraft) => string;
  unresolvedHint: (d: RespiratoryDraft) => string;
}

/**
 * Display-only transform for raw controlled-value enum constants (e.g.
 * `CURRENT_CONCERNS_ASSESSED`, `NASAL_CANNULA`) — mirrors
 * `RespiratoryPanel.tsx`'s `humanizeOption`/`OPTION_LABEL_OVERRIDES`
 * (duplicated here, not imported, since that module is UI-layer and this
 * is domain-layer; keeping this a pure display formatter with no
 * behavioral logic avoids a domain→feature import direction). Values that
 * are not SCREAMING_SNAKE_CASE (already human-readable, e.g. the
 * `respiratoryUnableToAssessReason` options) pass through unchanged.
 */
const COVERAGE_OPTION_LABEL_OVERRIDES: Record<string, string> = {
  L_MIN: "L/min",
};

function formatCoverageOptionValue(option: string): string {
  if (COVERAGE_OPTION_LABEL_OVERRIDES[option]) return COVERAGE_OPTION_LABEL_OVERRIDES[option];
  if (!/^[A-Z0-9_]+$/.test(option)) return option;
  return option
    .toLowerCase()
    .split("_")
    .map((word) => (word.length > 0 ? word[0].toUpperCase() + word.slice(1) : word))
    .join(" ");
}

function textFilled(value: string | undefined): boolean {
  return Boolean(value && value.trim().length > 0);
}

/**
 * Mirrors `respiratoryProductRequirements.ts`'s `treatmentApplicable`
 * derivation exactly (duplicated intentionally — that module's own header
 * explains why the product-authorized engine is kept separate from the
 * legacy situation engine; Coverage is a third, display-only consumer of
 * the same rule and must not import validation-engine internals).
 */
function isRespiratoryTreatmentApplicable(d: RespiratoryDraft): boolean {
  return (
    Boolean(d.sobSeverity && d.sobSeverity !== "None") ||
    d.coughType === "Productive" ||
    Boolean(d.hemoptysisPresent) ||
    d.oxygenUse === "YES" ||
    d.respiratorySupportStatus === "IN_USE"
  );
}

const RESPIRATORY_COVERAGE_ITEMS: RespiratoryCoverageItemConfig[] = [
  {
    key: "assessmentContext",
    label: "Assessment Context",
    sourceFieldKeys: ["respiratory_assessment_context"],
    applicable: () => true,
    check: (d) => Boolean(d.assessmentContext),
    summarize: (d) => formatCoverageOptionValue(d.assessmentContext as string),
    unresolvedHint: () => "Record the Respiratory assessment context.",
  },
  {
    key: "comparison",
    label: "Comparison",
    sourceFieldKeys: ["respiratory_clinical_comparison"],
    applicable: () => true,
    check: (d) => Boolean(d.clinicalComparison),
    summarize: (d) => formatCoverageOptionValue(d.clinicalComparison as string),
    unresolvedHint: () => "Record the comparison to the prior Respiratory assessment.",
  },
  {
    key: "comparisonDetail",
    label: "Comparison Detail",
    sourceFieldKeys: ["respiratory_clinical_status_change_detail"],
    applicable: (d) => d.clinicalComparison === "CHANGED_FROM_PRIOR",
    check: (d) => textFilled(d.clinicalStatusChangeDetail),
    summarize: (d) => d.clinicalStatusChangeDetail as string,
    unresolvedHint: () => "Describe the change from the prior assessment.",
  },
  {
    key: "comfortFunctionImpact",
    label: "Comfort / Functional Impact",
    sourceFieldKeys: ["respiratory_comfort_function_impact"],
    applicable: (d) => d.assessmentContext === "CURRENT_CONCERNS_ASSESSED" || d.assessmentContext === "UNABLE_TO_FULLY_ASSESS",
    check: (d) => Boolean(d.comfortFunctionImpact),
    summarize: (d) => formatCoverageOptionValue(d.comfortFunctionImpact as string),
    unresolvedHint: () => "Record the comfort/functional impact.",
  },
  {
    key: "treatmentDecision",
    label: "Treatment Decision",
    sourceFieldKeys: ["respiratory_treatment_decision"],
    applicable: isRespiratoryTreatmentApplicable,
    check: (d) => Boolean(d.treatmentDecision),
    summarize: (d) => formatCoverageOptionValue(d.treatmentDecision as string),
    unresolvedHint: () => "Record the treatment decision.",
  },
  {
    key: "clinicalResponse",
    label: "Clinical Response",
    sourceFieldKeys: ["respiratory_clinical_response"],
    applicable: (d) => d.treatmentDecision === "INITIATED" || d.treatmentDecision === "ALREADY_IN_PLACE",
    check: (d) => Boolean(d.clinicalResponse),
    summarize: (d) => formatCoverageOptionValue(d.clinicalResponse as string),
    unresolvedHint: () => "Record the clinical response to the current treatment.",
  },
  {
    key: "treatmentNarrative",
    label: "Treatment Narrative",
    sourceFieldKeys: ["respiratory_treatment_description"],
    applicable: (d) =>
      d.treatmentDecision === "DECLINED" || (d.treatmentDecision === "NOT_INDICATED" && isRespiratoryTreatmentApplicable(d)),
    check: (d) => textFilled(d.treatmentDescription),
    summarize: (d) => d.treatmentDescription as string,
    unresolvedHint: (d) =>
      d.treatmentDecision === "DECLINED"
        ? "Record the reason treatment was declined."
        : "Record the clinical rationale for not indicating Respiratory treatment.",
  },
  {
    key: "followUpNeed",
    label: "Follow-Up Need",
    sourceFieldKeys: ["respiratory_follow_up_need"],
    applicable: isRespiratoryTreatmentApplicable,
    check: (d) => Boolean(d.followUpNeed),
    summarize: (d) => formatCoverageOptionValue(d.followUpNeed as string),
    unresolvedHint: () => "Record whether Respiratory follow-up is needed.",
  },
  {
    key: "oxygenUse",
    label: "Oxygen Use",
    sourceFieldKeys: ["respiratory_oxygen_use"],
    applicable: () => true,
    check: (d) => Boolean(d.oxygenUse),
    summarize: (d) => formatCoverageOptionValue(d.oxygenUse as string),
    unresolvedHint: () => "Record whether oxygen is in use.",
  },
  {
    key: "oxygenVerificationReason",
    label: "Oxygen Verification Reason",
    sourceFieldKeys: ["respiratory_oxygen_unable_to_verify_reason"],
    applicable: (d) => d.oxygenUse === "UNABLE_TO_VERIFY",
    check: (d) => textFilled(d.oxygenUnableToVerifyReason),
    summarize: (d) => d.oxygenUnableToVerifyReason as string,
    unresolvedHint: () => "Record why oxygen use could not be verified.",
  },
  {
    key: "oxygenDevice",
    label: "Oxygen Device",
    sourceFieldKeys: ["respiratory_oxygen_delivery_device"],
    applicable: (d) => d.oxygenUse === "YES",
    check: (d) => Boolean(d.oxygenTherapy?.deliveryDevice),
    summarize: (d) => formatCoverageOptionValue(d.oxygenTherapy?.deliveryDevice as string),
    unresolvedHint: () => "Record the oxygen delivery device.",
  },
  {
    key: "oxygenFrequency",
    label: "Oxygen Frequency",
    sourceFieldKeys: ["respiratory_oxygen_frequency"],
    applicable: (d) => d.oxygenUse === "YES",
    check: (d) => Boolean(d.oxygenTherapy?.frequency),
    summarize: (d) => formatCoverageOptionValue(d.oxygenTherapy?.frequency as string),
    unresolvedHint: () => "Record the oxygen frequency.",
  },
  {
    key: "oxygenFlowRate",
    label: "Oxygen Flow Rate",
    sourceFieldKeys: ["respiratory_oxygen_flow_value", "respiratory_oxygen_flow_unit"],
    applicable: (d) => d.oxygenUse === "YES",
    check: (d) => d.oxygenTherapy?.flowValue !== undefined,
    summarize: (d) => {
      const unit = d.oxygenTherapy?.flowUnit ? formatCoverageOptionValue(d.oxygenTherapy.flowUnit) : "";
      return unit ? `${d.oxygenTherapy?.flowValue} ${unit}` : `${d.oxygenTherapy?.flowValue}`;
    },
    unresolvedHint: () => "Record the oxygen flow value.",
  },
  {
    key: "spo2MeasurementCondition",
    label: "SpO2 Measurement Condition",
    sourceFieldKeys: ["respiratory_spo2_measurement_condition"],
    applicable: (d) => d.spo2Value !== undefined,
    check: (d) => Boolean(d.spo2MeasurementCondition),
    summarize: (d) => formatCoverageOptionValue(d.spo2MeasurementCondition as string),
    unresolvedHint: () => "Record the SpO2 measurement condition.",
  },
  {
    key: "spo2NotObtainedReason",
    label: "SpO2 Not Obtained Reason",
    sourceFieldKeys: ["respiratory_spo2_not_obtained_reason"],
    applicable: (d) => d.spo2MeasurementCondition === "NOT_OBTAINED",
    check: (d) => textFilled(d.spo2NotObtainedReason),
    summarize: (d) => d.spo2NotObtainedReason as string,
    unresolvedHint: () => "Record why SpO2 was not obtained.",
  },
  {
    key: "coughType",
    label: "Cough Type",
    sourceFieldKeys: ["respiratory_cough_type"],
    applicable: () => true,
    check: (d) => Boolean(d.coughType),
    summarize: (d) => d.coughType as string,
    unresolvedHint: () => "Record the cough type.",
  },
  {
    key: "sputumAmount",
    label: "Sputum Amount",
    sourceFieldKeys: ["respiratory_sputum_amount"],
    applicable: (d) => d.coughType === "Productive",
    check: (d) => Boolean(d.sputumAmount),
    summarize: (d) => formatCoverageOptionValue(d.sputumAmount as string),
    unresolvedHint: () => "Record the sputum amount.",
  },
  {
    key: "sputumColor",
    label: "Sputum Color",
    sourceFieldKeys: ["respiratory_sputum_color"],
    applicable: (d) => d.coughType === "Productive",
    check: (d) => Boolean(d.sputumColor),
    summarize: (d) => formatCoverageOptionValue(d.sputumColor as string),
    unresolvedHint: () => "Record the sputum color.",
  },
  {
    key: "sputumSpecification",
    label: "Sputum Specification",
    sourceFieldKeys: ["respiratory_sputum_other_specification"],
    applicable: (d) => d.sputumCharacter === "OTHER" || d.sputumColor === "OTHER",
    check: (d) => textFilled(d.sputumOtherSpecification),
    summarize: (d) => d.sputumOtherSpecification as string,
    unresolvedHint: () => "Specify the sputum character/color.",
  },
  {
    key: "hemoptysisSignificance",
    label: "Hemoptysis Significance",
    sourceFieldKeys: ["respiratory_cough_clinical_significance"],
    applicable: (d) => d.hemoptysisPresent === true,
    check: (d) => textFilled(d.coughClinicalSignificance),
    summarize: (d) => d.coughClinicalSignificance as string,
    unresolvedHint: () => "Record the clinical significance of hemoptysis.",
  },
  {
    key: "supportStatus",
    label: "Support Status",
    sourceFieldKeys: ["respiratory_support_status"],
    applicable: () => true,
    check: (d) => Boolean(d.respiratorySupportStatus),
    summarize: (d) => formatCoverageOptionValue(d.respiratorySupportStatus as string),
    unresolvedHint: () => "Record the respiratory support status.",
  },
  {
    key: "supportTypes",
    label: "Support Type(s)",
    sourceFieldKeys: ["respiratory_support_types"],
    applicable: (d) => d.respiratorySupportStatus === "IN_USE",
    check: (d) => Boolean(d.respiratorySupportTypes && d.respiratorySupportTypes.length > 0),
    summarize: (d) => (d.respiratorySupportTypes ?? []).map(formatCoverageOptionValue).join(", "),
    unresolvedHint: () => "Record the respiratory support type(s) in use.",
  },
  {
    key: "ventilatorDuration",
    label: "Ventilator Duration",
    sourceFieldKeys: ["respiratory_ventilator_duration"],
    applicable: (d) => Boolean(d.respiratorySupportTypes?.includes("VENTILATOR")),
    check: (d) => Boolean(d.ventilator?.duration),
    summarize: (d) => formatCoverageOptionValue(d.ventilator?.duration as string),
    unresolvedHint: () => "Record whether the ventilator is short-term or long-term.",
  },
  {
    key: "airwayFindings",
    label: "Airway Findings",
    sourceFieldKeys: ["respiratory_airway_site_findings"],
    applicable: (d) => Boolean(d.respiratorySupportTypes?.includes("TRACHEOSTOMY")),
    check: (d) => textFilled(d.airwaySiteFindings),
    summarize: (d) => d.airwaySiteFindings as string,
    unresolvedHint: () => "Record the airway/tracheostomy site findings.",
  },
  {
    key: "supportResponse",
    label: "Support Response",
    sourceFieldKeys: ["respiratory_support_response"],
    applicable: (d) => d.respiratorySupportStatus === "IN_USE",
    check: (d) => textFilled(d.respiratorySupportResponse),
    summarize: (d) => d.respiratorySupportResponse as string,
    unresolvedHint: () => "Record the respiratory support effectiveness/response.",
  },
  {
    key: "supportVerificationReason",
    label: "Support Verification Reason",
    sourceFieldKeys: ["respiratory_support_unable_to_verify_reason"],
    applicable: (d) => d.respiratorySupportStatus === "UNABLE_TO_VERIFY",
    check: (d) => textFilled(d.respiratorySupportUnableToVerifyReason),
    summarize: (d) => d.respiratorySupportUnableToVerifyReason as string,
    unresolvedHint: () => "Record why respiratory support could not be verified.",
  },
  {
    key: "unableToAssessReason",
    label: "Unable To Assess Reason",
    sourceFieldKeys: ["respiratory_unable_to_assess_reason"],
    applicable: (d) => d.respiratoryUnableToAssess === true,
    check: (d) => Boolean(d.respiratoryUnableToAssessReason),
    summarize: (d) => d.respiratoryUnableToAssessReason as string,
    unresolvedHint: () => "Record the reason the respiratory system could not be fully assessed.",
  },
];

/**
 * ADR-004 Respiratory Documentation Coverage. Pure function of the
 * current draft — read-only, never mutates, never gates Save or
 * "Complete System Review" (see `getRespiratoryReviewCompletion` for
 * that, a deliberately separate engine). Non-applicable conditional items
 * are omitted entirely rather than shown as unresolved.
 */
export function computeRespiratoryDocumentationCoverage(draft: RespiratoryDraft): RespiratoryCoverageItem[] {
  return RESPIRATORY_COVERAGE_ITEMS.filter((item) => item.applicable(draft)).map((item) => {
    const complete = item.check(draft);
    return {
      key: item.key,
      label: item.label,
      complete,
      value: complete ? item.summarize(draft) : null,
      unresolvedHint: complete ? null : item.unresolvedHint(draft),
      sourceFieldKeys: item.sourceFieldKeys,
    };
  });
}
