/**
 * SNS Body Systems — Respiratory verified field inventory.
 *
 * Proof-of-pattern source of truth for the Respiratory clinical-detail
 * milestone (docs/design/body-systems-figma/SNS_Body_Systems_Engineering_Specification.md
 * section 19, "Third recommended GitHub task"). Per that task's explicit
 * constraint, every field listed here is reused from an existing,
 * owner-approved repository source — none are invented from Figma sample
 * content. The authoritative source for every field below is the
 * owner-approved production respiratory module in
 * `src/components/RNICA.jsx` (default data block, "RESPIRATORY" section,
 * and its matching `respiratory` render-schema card list) — see the
 * `legacySource` on each entry.
 *
 * Fields referenced in the approved specification's situation/limitation
 * model (section 7) that have NO existing repository-backed equivalent are
 * intentionally NOT represented here (e.g. a per-field "dated prior
 * evidence reference", an explicit follow-up responsible-clinician/timing
 * pair, or an "assessed portion" sub-field of a limitation). Those gaps are
 * tracked in `workflowRules.ts` as NOT VERIFIED and excluded from any
 * blocking requirement for this milestone, per the task's directive:
 * "If no repository-backed field exists, omit it from the production
 * contract and record it as NOT VERIFIED. The milestone must still proceed
 * with all verified fields."
 */
import type { BodySystemCode } from "./types";

export type RespiratoryFieldResponseType =
  | "single_select"
  | "multi_select"
  | "text"
  | "number"
  | "boolean"
  | "date";

export interface RespiratoryFieldDefinition {
  /** Canonical, stable identifier for this field within the Body Systems domain model. */
  fieldId: string;
  /** Display label, reused verbatim from the existing production UI copy. */
  label: string;
  /** Owning body system — always "respiratory" for this inventory, restated for self-containment. */
  owner: BodySystemCode;
  /** The ownership fact key this field maps to in `ownership.ts`'s OWNERSHIP_REGISTRY. */
  ownerFactKey: string;
  /** Dotted path into the existing legacy RNICA `respiratory` data object (src/components/RNICA.jsx). */
  legacySource: string;
  responseType: RespiratoryFieldResponseType;
  /** Allowed values, transcribed verbatim from the existing production options list. Omitted for free-text/number/boolean/date fields. */
  controlledValues?: readonly string[];
  units?: string;
  /** Whether an absent/empty value is a valid, non-blocking state (draft saves always allow this; see workflowRules.ts). */
  nullable: boolean;
  /** How an explicit "unknown" response is represented, if the field supports one. */
  unknownBehavior?: string;
  /** How a "not assessed" response is represented, if the field supports one. */
  notAssessedBehavior?: string;
  notes?: string;
}

/**
 * Situation selector. Legacy source: `respiratoryOverview` (segmented,
 * "Respiratory Overview" card) — owner-approved "Respiratory Overview
 * Workflow Reorganization" (2026-10-06). Maps 1:1 to the canonical
 * `AssessmentSituation` enum; see `mapLegacyRespiratoryOverviewToSituation`
 * below for the exact value mapping.
 */
export const RESPIRATORY_OVERVIEW_FIELD: RespiratoryFieldDefinition = {
  fieldId: "respiratory_overview",
  label: "Respiratory Overview",
  owner: "respiratory",
  ownerFactKey: "respiratory_exertion_tolerance",
  legacySource: "respiratory.respiratoryOverview",
  responseType: "single_select",
  controlledValues: [
    "No Current Respiratory Concern",
    "Existing Respiratory Findings Review",
    "New or Worsening Respiratory Findings",
    "Unable to Assess",
  ],
  nullable: false,
  notes: "Gates which detail fields below are required; this selection itself is the explicit current-review action for the no_current_concern situation.",
};

export const RESPIRATORY_UNABLE_TO_ASSESS_REASON_FIELD: RespiratoryFieldDefinition = {
  fieldId: "respiratory_unable_to_assess_reason",
  label: "Reason Unable to Assess",
  owner: "respiratory",
  ownerFactKey: "respiratory_exertion_tolerance",
  legacySource: "respiratory.respiratoryUnableToAssessReason",
  responseType: "single_select",
  controlledValues: [
    "Patient unable to participate",
    "Patient unresponsive",
    "Clinical condition prevented completion",
    "Assessment interrupted",
    "Patient or representative declined",
    "Other",
  ],
  nullable: true,
  notes: "Required only when respiratoryOverview === 'Unable to Assess'. Satisfies AssessmentLimitation.reason.",
};

export const RESPIRATORY_UNABLE_TO_ASSESS_OTHER_FIELD: RespiratoryFieldDefinition = {
  fieldId: "respiratory_unable_to_assess_other",
  label: "Other Reason (if selected above)",
  owner: "respiratory",
  ownerFactKey: "respiratory_exertion_tolerance",
  legacySource: "respiratory.respiratoryUnableToAssessOther",
  responseType: "text",
  nullable: true,
  notes: "Required only when respiratoryUnableToAssessReason === 'Other'.",
};

export const RESPIRATORY_SOB_SEVERITY_FIELD: RespiratoryFieldDefinition = {
  fieldId: "respiratory_sob_severity",
  label: "SOB Severity",
  owner: "respiratory",
  ownerFactKey: "dyspnea",
  legacySource: "respiratory.sobSeverity",
  responseType: "single_select",
  controlledValues: ["None", "Mild", "Moderate", "Severe", "At rest"],
  nullable: true,
};

export const RESPIRATORY_EXERTION_LEVEL_FIELD: RespiratoryFieldDefinition = {
  fieldId: "respiratory_exertion_level",
  label: "Exertion Level",
  owner: "respiratory",
  ownerFactKey: "respiratory_exertion_tolerance",
  legacySource: "respiratory.exertionLevel",
  responseType: "single_select",
  controlledValues: [
    "At rest",
    "Minimal exertion",
    "Moderate exertion",
    "Severe exertion",
    "With speech",
    "Push of speech",
    "Pursed-lip breathing",
    "Other",
  ],
  nullable: true,
};

export const RESPIRATORY_LUNG_SOUNDS_FIELD: RespiratoryFieldDefinition = {
  fieldId: "respiratory_lung_sounds",
  label: "Lung Sounds",
  owner: "respiratory",
  ownerFactKey: "lung_sounds",
  legacySource: "respiratory.lungSounds",
  responseType: "multi_select",
  controlledValues: ["Clear", "Crackles", "Wheezes", "Rhonchi", "Diminished", "Absent", "Stridor", "Pleural rub", "Rales"],
  nullable: true,
};

export const RESPIRATORY_RESPIRATION_PATTERN_FIELD: RespiratoryFieldDefinition = {
  fieldId: "respiratory_respiration_pattern",
  label: "Respiration Pattern",
  owner: "respiratory",
  ownerFactKey: "respiratory_rate_pattern",
  legacySource: "respiratory.respirations",
  responseType: "multi_select",
  controlledValues: [
    "Regular",
    "Normal",
    "Irregular",
    "Labored",
    "Cheyne-Stokes",
    "Apneic episodes",
    "Kussmaul",
    "Agonal",
    "Tachypnea",
    "Bradypnea",
    "Orthopnea",
  ],
  nullable: true,
};

export const RESPIRATORY_COUGH_TYPE_FIELD: RespiratoryFieldDefinition = {
  fieldId: "respiratory_cough_type",
  label: "Cough Type",
  owner: "respiratory",
  ownerFactKey: "cough",
  legacySource: "respiratory.coughType",
  responseType: "single_select",
  controlledValues: ["None", "Productive", "Non-productive", "Hemoptysis", "Barrel chest"],
  nullable: true,
};

export const RESPIRATORY_SPUTUM_CHARACTER_FIELD: RespiratoryFieldDefinition = {
  fieldId: "respiratory_sputum_character",
  label: "Sputum Character",
  owner: "respiratory",
  ownerFactKey: "sputum",
  legacySource: "respiratory.sputumCharacter",
  responseType: "text",
  nullable: true,
};

export const RESPIRATORY_OXYGEN_IN_USE_FIELD: RespiratoryFieldDefinition = {
  fieldId: "respiratory_oxygen_in_use",
  label: "Oxygen in Use",
  owner: "respiratory",
  ownerFactKey: "oxygen_use",
  legacySource: "respiratory.oxygenTherapy.inUse",
  responseType: "boolean",
  nullable: true,
};

export const RESPIRATORY_OXYGEN_DELIVERY_TYPE_FIELD: RespiratoryFieldDefinition = {
  fieldId: "respiratory_oxygen_delivery_type",
  label: "Delivery Type",
  owner: "respiratory",
  ownerFactKey: "oxygen_use",
  legacySource: "respiratory.oxygenTherapy.type",
  responseType: "single_select",
  controlledValues: ["Nasal cannula", "Simple mask", "Non-rebreather", "Venturi mask", "High flow"],
  nullable: true,
};

export const RESPIRATORY_OXYGEN_LITERS_PER_MINUTE_FIELD: RespiratoryFieldDefinition = {
  fieldId: "respiratory_oxygen_liters_per_minute",
  label: "Liters/Minute",
  owner: "respiratory",
  ownerFactKey: "oxygen_use",
  legacySource: "respiratory.oxygenTherapy.litersPerMinute",
  responseType: "number",
  units: "L/min",
  nullable: true,
};

export const RESPIRATORY_OXYGEN_SAT_ON_O2_FIELD: RespiratoryFieldDefinition = {
  fieldId: "respiratory_oxygen_sat_on_o2",
  label: "SpO2 on O2",
  owner: "respiratory",
  ownerFactKey: "oxygen_use",
  legacySource: "respiratory.oxygenTherapy.satOnO2",
  responseType: "number",
  units: "%",
  nullable: true,
};

export const RESPIRATORY_ON_ROOM_AIR_FIELD: RespiratoryFieldDefinition = {
  fieldId: "respiratory_on_room_air",
  label: "On Room Air",
  owner: "respiratory",
  ownerFactKey: "oxygen_use",
  legacySource: "respiratory.oxygenTherapy.onRoomAir",
  responseType: "boolean",
  nullable: true,
};

export const RESPIRATORY_VENTILATOR_SHORT_TERM_FIELD: RespiratoryFieldDefinition = {
  fieldId: "respiratory_ventilator_short_term",
  label: "Short-Term Ventilator",
  owner: "respiratory",
  ownerFactKey: "ventilator_airway_support",
  legacySource: "respiratory.ventilator.shortTermVentilator",
  responseType: "boolean",
  nullable: true,
};

export const RESPIRATORY_VENTILATOR_LONG_TERM_FIELD: RespiratoryFieldDefinition = {
  fieldId: "respiratory_ventilator_long_term",
  label: "Long-Term Ventilator",
  owner: "respiratory",
  ownerFactKey: "ventilator_airway_support",
  legacySource: "respiratory.ventilator.longTermVentilator",
  responseType: "boolean",
  nullable: true,
};

export const RESPIRATORY_TREATMENT_INITIATED_FIELD: RespiratoryFieldDefinition = {
  fieldId: "respiratory_treatment_initiated",
  label: "Treatment for shortness of breath initiated",
  owner: "respiratory",
  ownerFactKey: "respiratory_exertion_tolerance",
  legacySource: "respiratory.treatmentInitiated",
  responseType: "boolean",
  nullable: true,
  notes: "Serves as the Intervention signal for the new_or_worsening situation branch.",
};

export const RESPIRATORY_TREATMENT_DECLINED_FIELD: RespiratoryFieldDefinition = {
  fieldId: "respiratory_treatment_declined",
  label: "Treatment Declined (when applicable)",
  owner: "respiratory",
  ownerFactKey: "respiratory_exertion_tolerance",
  legacySource: "respiratory.treatmentDeclined",
  responseType: "boolean",
  nullable: true,
  notes: "An explicit decline also satisfies the Intervention-or-response requirement (a documented response, not an omission).",
};

export const RESPIRATORY_CLINICAL_STATUS_CHANGE_FIELD: RespiratoryFieldDefinition = {
  fieldId: "respiratory_clinical_status_change",
  label: "Clinical Status Change",
  owner: "respiratory",
  ownerFactKey: "respiratory_exertion_tolerance",
  legacySource: "respiratory.clinicalStatusChange",
  responseType: "single_select",
  controlledValues: [
    "Stable / No Change",
    "Improving",
    "Symptom Well-Managed",
    "Declining",
    "New Symptom Since Prior Assessment",
    "Not Applicable",
  ],
  nullable: true,
  notes: "Serves as the current-finding-or-change signal for the new_or_worsening and stable_existing situation branches.",
};

export const RESPIRATORY_NOTES_FIELD: RespiratoryFieldDefinition = {
  fieldId: "respiratory_notes",
  label: "Respiratory Notes",
  owner: "respiratory",
  ownerFactKey: "respiratory_exertion_tolerance",
  legacySource: "respiratory.notes",
  responseType: "text",
  nullable: true,
};

/** Every verified Respiratory field, in the same order as the existing production render-schema. */
export const RESPIRATORY_FIELD_INVENTORY: readonly RespiratoryFieldDefinition[] = [
  RESPIRATORY_OVERVIEW_FIELD,
  RESPIRATORY_UNABLE_TO_ASSESS_REASON_FIELD,
  RESPIRATORY_UNABLE_TO_ASSESS_OTHER_FIELD,
  RESPIRATORY_SOB_SEVERITY_FIELD,
  RESPIRATORY_EXERTION_LEVEL_FIELD,
  RESPIRATORY_LUNG_SOUNDS_FIELD,
  RESPIRATORY_RESPIRATION_PATTERN_FIELD,
  RESPIRATORY_COUGH_TYPE_FIELD,
  RESPIRATORY_SPUTUM_CHARACTER_FIELD,
  RESPIRATORY_OXYGEN_IN_USE_FIELD,
  RESPIRATORY_OXYGEN_DELIVERY_TYPE_FIELD,
  RESPIRATORY_OXYGEN_LITERS_PER_MINUTE_FIELD,
  RESPIRATORY_OXYGEN_SAT_ON_O2_FIELD,
  RESPIRATORY_ON_ROOM_AIR_FIELD,
  RESPIRATORY_VENTILATOR_SHORT_TERM_FIELD,
  RESPIRATORY_VENTILATOR_LONG_TERM_FIELD,
  RESPIRATORY_TREATMENT_INITIATED_FIELD,
  RESPIRATORY_TREATMENT_DECLINED_FIELD,
  RESPIRATORY_CLINICAL_STATUS_CHANGE_FIELD,
  RESPIRATORY_NOTES_FIELD,
] as const;

/**
 * Situation-branch sub-requirements from specification section 7 with NO
 * existing repository-backed field, as of this milestone. Tracked here so
 * `workflowRules.ts` can treat them as informational-only (never
 * record/signature blocking) instead of silently dropping them or
 * incorrectly promoting them to a hard blocker. Revisit if/when an
 * approved field inventory update adds a backing field.
 */
export const RESPIRATORY_NOT_VERIFIED_REQUIREMENTS = [
  "dated_prior_reference",
  "follow_up_decision",
  "scope",
  "assessed_portion_if_any",
  "follow_up_responsibility",
  "timing_or_contingency",
] as const;

export type RespiratoryNotVerifiedRequirement = (typeof RESPIRATORY_NOT_VERIFIED_REQUIREMENTS)[number];

export function isRespiratoryRequirementNotVerified(requirementKey: string): boolean {
  return (RESPIRATORY_NOT_VERIFIED_REQUIREMENTS as readonly string[]).includes(requirementKey);
}
