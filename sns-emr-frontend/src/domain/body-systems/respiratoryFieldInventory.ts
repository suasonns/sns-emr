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
  | "date"
  | "time"
  | "datetime";

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
 * HISTORICAL/LEGACY-READ ONLY. The `respiratoryOverview` 4-way selector
 * ("No Current Respiratory Concern" / "Existing Respiratory Findings
 * Review" / "New or Worsening Respiratory Findings" / "Unable to Assess")
 * was the legacy production situation-entry gate: it had to be answered
 * before any other field was enabled/required, it decided which fields
 * rendered, and it gated Save itself. Contract v2 (RNICA Body Systems
 * Single Build Contract v2, section on review-state/situation gates)
 * explicitly prohibits a situation selector from controlling whether a
 * system renders, whether review is required, requiredness, completion,
 * or Save availability.
 *
 * This definition is kept ONLY so `legacyRNICAAdapter.ts` can continue to
 * read historical `respiratory.respiratoryOverview` values already stored
 * on legacy records for read-only historical display — it must never again
 * be rendered as a gating control in the Contract v2 Respiratory panel.
 * See `RESPIRATORY_NO_CURRENT_CONCERN_FIELD` and
 * `RESPIRATORY_UNABLE_TO_ASSESS_FIELD` below for the two explicit,
 * non-gating actions that replace it.
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
  nullable: true,
  notes: "HISTORICAL READ-ONLY. Not rendered as a gate in the Contract v2 panel; superseded by RESPIRATORY_NO_CURRENT_CONCERN_FIELD and RESPIRATORY_UNABLE_TO_ASSESS_FIELD.",
};

/**
 * Explicit, non-gating "no current concern" declaration. Unlike the legacy
 * overview selector, this does not have to be answered before other fields
 * are visible/editable — all current-evidence fields are always rendered.
 * It exists because Contract v2 requires an explicit nurse action (not a
 * blank default) to record "reviewed, no current respiratory concern";
 * leaving every field blank must never be silently treated as normal.
 */
export const RESPIRATORY_NO_CURRENT_CONCERN_FIELD: RespiratoryFieldDefinition = {
  fieldId: "respiratory_no_current_concern",
  label: "No current respiratory concern",
  owner: "respiratory",
  ownerFactKey: "respiratory_exertion_tolerance",
  legacySource: "respiratory.respiratoryNoCurrentConcern",
  responseType: "boolean",
  nullable: true,
  notes: "Explicit nurse declaration only; does not gate rendering or requiredness of any other field.",
};

/**
 * Explicit, non-gating "unable to fully assess" toggle. Opens the
 * Assessment Limitation fields (reason / other) below it without hiding or
 * disabling any current-evidence field — a nurse may document both partial
 * current findings AND a limitation for the remaining scope.
 */
export const RESPIRATORY_UNABLE_TO_ASSESS_FIELD: RespiratoryFieldDefinition = {
  fieldId: "respiratory_unable_to_assess",
  label: "Unable to fully assess respiratory system",
  owner: "respiratory",
  ownerFactKey: "respiratory_exertion_tolerance",
  legacySource: "respiratory.respiratoryUnableToAssess",
  responseType: "boolean",
  nullable: true,
  notes: "Explicit limitation toggle; reveals (does not require) the limitation reason fields. Never hides current-evidence fields.",
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

/**
 * Ported from the owner-approved legacy production respiratory module
 * (src/components/RNICA.jsx, "Dyspnea / SOB" card) — these three fields
 * already exist in the legacy data block and render schema but were
 * omitted from this milestone's initial verified-field port. No new
 * clinical finding is introduced; this closes a porting gap, not a field
 * addition.
 */
export const RESPIRATORY_SHORTNESS_OF_BREATH_SCREENED_FIELD: RespiratoryFieldDefinition = {
  fieldId: "respiratory_shortness_of_breath_screened",
  label: "Screened for shortness of breath",
  owner: "respiratory",
  ownerFactKey: "dyspnea",
  legacySource: "respiratory.shortnessOfBreathScreened",
  responseType: "boolean",
  nullable: true,
};

export const RESPIRATORY_SCREENING_DATE_FIELD: RespiratoryFieldDefinition = {
  fieldId: "respiratory_screening_date",
  label: "SOB Screening Date",
  owner: "respiratory",
  ownerFactKey: "dyspnea",
  legacySource: "respiratory.screeningDate",
  responseType: "date",
  nullable: true,
};

export const RESPIRATORY_TREATMENT_DATE_FIELD: RespiratoryFieldDefinition = {
  fieldId: "respiratory_treatment_date",
  label: "SOB Treatment Date",
  owner: "respiratory",
  ownerFactKey: "dyspnea",
  legacySource: "respiratory.treatmentDate",
  responseType: "date",
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

/**
 * Ported from the owner-approved legacy "Oxygen Therapy" card
 * (src/components/RNICA.jsx) — both already exist in the legacy
 * `oxygenTherapy` data block and render schema but were omitted from this
 * milestone's initial verified-field port.
 */
export const RESPIRATORY_OXYGEN_HOURS_PER_DAY_FIELD: RespiratoryFieldDefinition = {
  fieldId: "respiratory_oxygen_hours_per_day",
  label: "Hours/Day",
  owner: "respiratory",
  ownerFactKey: "oxygen_use",
  legacySource: "respiratory.oxygenTherapy.hoursPerDay",
  responseType: "text",
  nullable: true,
};

export const RESPIRATORY_OXYGEN_DELIVERY_MODE_FIELD: RespiratoryFieldDefinition = {
  fieldId: "respiratory_oxygen_delivery_mode",
  label: "Delivery Mode",
  owner: "respiratory",
  ownerFactKey: "oxygen_use",
  legacySource: "respiratory.oxygenTherapy.deliveryMode",
  responseType: "single_select",
  controlledValues: ["Continuous", "PRN"],
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

/**
 * Ported from the owner-approved legacy "Ventilator / Airway Support"
 * card (src/components/RNICA.jsx) — already exist in the legacy
 * `ventilator` data block and render schema, including that card's own
 * documented visibility rule ("only render once a Short-Term or Long-Term
 * Ventilator is actually in use"), but were omitted from this milestone's
 * initial verified-field port.
 */
export const RESPIRATORY_VENTILATOR_TYPE_AND_SETTINGS_FIELD: RespiratoryFieldDefinition = {
  fieldId: "respiratory_ventilator_type_and_settings",
  label: "Ventilator Type and Settings",
  owner: "respiratory",
  ownerFactKey: "ventilator_airway_support",
  legacySource: "respiratory.ventilator.ventilatorTypeAndSettings",
  responseType: "text",
  nullable: true,
};

export const RESPIRATORY_TRACHEOSTOMY_TYPE_FIELD: RespiratoryFieldDefinition = {
  fieldId: "respiratory_tracheostomy_type",
  label: "Tracheostomy Type",
  owner: "respiratory",
  ownerFactKey: "ventilator_airway_support",
  legacySource: "respiratory.ventilator.tracheostomyType",
  responseType: "text",
  nullable: true,
};

export const RESPIRATORY_TRACHEOSTOMY_SIZE_FIELD: RespiratoryFieldDefinition = {
  fieldId: "respiratory_tracheostomy_size",
  label: "Tracheostomy Size",
  owner: "respiratory",
  ownerFactKey: "ventilator_airway_support",
  legacySource: "respiratory.ventilator.tracheostomySize",
  responseType: "text",
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

// ---------------------------------------------------------------------------
// Product-owner-authorized canonical fields (NOT ported from Figma sample
// content; NOT ported from legacy RNICA.jsx). These field IDs, allowed
// values, and required-status rules are transcribed verbatim from the
// written product-owner Respiratory field specification that authorizes
// them ("PRODUCT-OWNER AUTHORIZATION: COMPLETE THE RESPIRATORY FIELD
// SPECIFICATION", session record). Per that specification's explicit
// source-of-truth decision: "Figma sample patient values... are not
// business rules... this product-owner instruction provides the missing
// clinical vocabulary and completion semantics." Required/optional and
// conditional-visibility logic for every field below is implemented in
// `respiratoryRequirementEngine.ts`, not inferred here.
// ---------------------------------------------------------------------------

export const RESPIRATORY_ASSESSMENT_CONTEXT_FIELD: RespiratoryFieldDefinition = {
  fieldId: "respiratory_assessment_context",
  label: "Assessment Context",
  owner: "respiratory",
  ownerFactKey: "respiratory_exertion_tolerance",
  legacySource: "respiratory.assessmentContext",
  responseType: "single_select",
  controlledValues: ["CURRENT_CONCERNS_ASSESSED", "NO_CURRENT_RESPIRATORY_CONCERN", "UNABLE_TO_FULLY_ASSESS"],
  nullable: false,
  notes: "Required for completion. Product-owner-authorized field (spec section 3).",
};

export const RESPIRATORY_CLINICAL_COMPARISON_FIELD: RespiratoryFieldDefinition = {
  fieldId: "respiratory_clinical_comparison",
  label: "Comparison to Prior",
  owner: "respiratory",
  ownerFactKey: "respiratory_exertion_tolerance",
  legacySource: "respiratory.clinicalComparison",
  responseType: "single_select",
  controlledValues: ["INITIAL_BASELINE", "UNCHANGED_FROM_PRIOR", "CHANGED_FROM_PRIOR", "COMPARISON_UNAVAILABLE"],
  nullable: false,
  notes: "Required for completion. Product-owner-authorized field (spec section 3).",
};

export const RESPIRATORY_CLINICAL_STATUS_CHANGE_DETAIL_FIELD: RespiratoryFieldDefinition = {
  fieldId: "respiratory_clinical_status_change_detail",
  label: "Describe the Change",
  owner: "respiratory",
  ownerFactKey: "respiratory_exertion_tolerance",
  legacySource: "respiratory.clinicalStatusChangeDetail",
  responseType: "text",
  nullable: true,
  notes: "Required only when clinicalComparison = CHANGED_FROM_PRIOR. Product-owner-authorized field (spec section 3).",
};

export const RESPIRATORY_COMFORT_FUNCTION_IMPACT_FIELD: RespiratoryFieldDefinition = {
  fieldId: "respiratory_comfort_function_impact",
  label: "Comfort / Functional Impact",
  owner: "respiratory",
  ownerFactKey: "dyspnea",
  legacySource: "respiratory.comfortFunctionImpact",
  responseType: "single_select",
  controlledValues: ["NO_IMPACT", "IMPACT_PRESENT", "UNABLE_TO_ASSESS"],
  nullable: true,
  notes: "Required when assessment context includes current concerns or limited assessability. Product-owner-authorized field (spec section 4).",
};

export const RESPIRATORY_COMFORT_FUNCTION_EVIDENCE_FIELD: RespiratoryFieldDefinition = {
  fieldId: "respiratory_comfort_function_evidence",
  label: "Comfort / Function Evidence",
  owner: "respiratory",
  ownerFactKey: "dyspnea",
  legacySource: "respiratory.comfortFunctionEvidence",
  responseType: "text",
  nullable: true,
  notes: "Required when comfortFunctionImpact is IMPACT_PRESENT or UNABLE_TO_ASSESS. Must not auto-populate from severity.",
};

export const RESPIRATORY_COMFORT_FUNCTION_SCREENING_DATE_FIELD: RespiratoryFieldDefinition = {
  fieldId: "respiratory_comfort_function_screening_date",
  label: "Comfort / Function Screening Date",
  owner: "respiratory",
  ownerFactKey: "dyspnea",
  legacySource: "respiratory.comfortFunctionScreeningDate",
  responseType: "date",
  nullable: true,
};

export const RESPIRATORY_COMFORT_FUNCTION_SCREENING_TIME_FIELD: RespiratoryFieldDefinition = {
  fieldId: "respiratory_comfort_function_screening_time",
  label: "Comfort / Function Screening Time",
  owner: "respiratory",
  ownerFactKey: "dyspnea",
  legacySource: "respiratory.comfortFunctionScreeningTime",
  responseType: "time",
  nullable: true,
};

export const RESPIRATORY_CONFIGURED_REQUIREMENT_RESPONSE_FIELD: RespiratoryFieldDefinition = {
  fieldId: "respiratory_configured_requirement_response",
  label: "Configured Requirement Response",
  owner: "respiratory",
  ownerFactKey: "dyspnea",
  legacySource: "respiratory.configuredRequirementResponse",
  responseType: "single_select",
  controlledValues: ["NOT_APPLICABLE", "REVIEWED_NO_ADDITIONAL_ACTION", "FOLLOW_UP_REQUIRED", "UNABLE_TO_DETERMINE"],
  nullable: true,
  notes: "Nurse-facing only; never displays HOPE/CMS item codes. Product-owner-authorized field (spec section 4).",
};

export const RESPIRATORY_CONFIGURED_FOLLOW_UP_STATUS_FIELD: RespiratoryFieldDefinition = {
  fieldId: "respiratory_configured_follow_up_status",
  label: "Configured Follow-Up Status",
  owner: "respiratory",
  ownerFactKey: "dyspnea",
  legacySource: "respiratory.configuredFollowUpStatus",
  responseType: "single_select",
  controlledValues: ["NOT_APPLICABLE", "NOT_STARTED", "PLANNED", "IN_PROGRESS", "COMPLETED", "UNABLE_TO_COMPLETE"],
  nullable: true,
  notes: "Required when the configured requirement produces follow-up. Must not be inferred from dyspnea severity.",
};

export const RESPIRATORY_TREATMENT_DECISION_FIELD: RespiratoryFieldDefinition = {
  fieldId: "respiratory_treatment_decision",
  label: "Treatment Decision",
  owner: "respiratory",
  ownerFactKey: "respiratory_exertion_tolerance",
  legacySource: "respiratory.treatmentDecision",
  responseType: "single_select",
  controlledValues: ["INITIATED", "ALREADY_IN_PLACE", "DECLINED", "NOT_INDICATED"],
  nullable: true,
  notes:
    "Canonical replacement for the legacy treatmentInitiated/treatmentDeclined boolean pair (preserved below for backward compatibility; see respiratoryBackwardCompatibility.ts). Product-owner-authorized field (spec section 5).",
};

export const RESPIRATORY_TREATMENT_DESCRIPTION_FIELD: RespiratoryFieldDefinition = {
  fieldId: "respiratory_treatment_description",
  label: "Treatment Description",
  owner: "respiratory",
  ownerFactKey: "respiratory_exertion_tolerance",
  legacySource: "respiratory.treatmentDescription",
  responseType: "text",
  nullable: true,
  notes: "Required for INITIATED and ALREADY_IN_PLACE.",
};

export const RESPIRATORY_TREATMENT_DECLINE_REASON_FIELD: RespiratoryFieldDefinition = {
  fieldId: "respiratory_treatment_decline_reason",
  label: "Treatment Decline Reason",
  owner: "respiratory",
  ownerFactKey: "respiratory_exertion_tolerance",
  legacySource: "respiratory.treatmentDeclineReason",
  responseType: "text",
  nullable: true,
  notes: "Required for DECLINED.",
};

export const RESPIRATORY_TREATMENT_ACTION_DATE_FIELD: RespiratoryFieldDefinition = {
  fieldId: "respiratory_treatment_action_date",
  label: "Treatment Action Date",
  owner: "respiratory",
  ownerFactKey: "respiratory_exertion_tolerance",
  legacySource: "respiratory.treatmentActionDate",
  responseType: "date",
  nullable: true,
};

export const RESPIRATORY_TREATMENT_ACTION_TIME_FIELD: RespiratoryFieldDefinition = {
  fieldId: "respiratory_treatment_action_time",
  label: "Treatment Action Time",
  owner: "respiratory",
  ownerFactKey: "respiratory_exertion_tolerance",
  legacySource: "respiratory.treatmentActionTime",
  responseType: "time",
  nullable: true,
};

export const RESPIRATORY_TREATMENT_RESPONSE_TIME_FIELD: RespiratoryFieldDefinition = {
  fieldId: "respiratory_treatment_response_time",
  label: "Treatment Response Time",
  owner: "respiratory",
  ownerFactKey: "respiratory_exertion_tolerance",
  legacySource: "respiratory.treatmentResponseTime",
  responseType: "time",
  nullable: true,
};

export const RESPIRATORY_TREATMENT_RESPONSE_FIELD: RespiratoryFieldDefinition = {
  fieldId: "respiratory_treatment_response",
  label: "Treatment Response",
  owner: "respiratory",
  ownerFactKey: "respiratory_exertion_tolerance",
  legacySource: "respiratory.treatmentResponse",
  responseType: "text",
  nullable: true,
  notes: "Required for INITIATED unless response is pending; required for ALREADY_IN_PLACE when effectiveness is currently assessed.",
};

export const RESPIRATORY_TREATMENT_RESPONSE_STATUS_FIELD: RespiratoryFieldDefinition = {
  fieldId: "respiratory_treatment_response_status",
  label: "Treatment Response Status",
  owner: "respiratory",
  ownerFactKey: "respiratory_exertion_tolerance",
  legacySource: "respiratory.treatmentResponseStatus",
  responseType: "single_select",
  controlledValues: ["OBSERVED", "REPORTED", "PENDING", "NOT_APPLICABLE", "UNABLE_TO_ASSESS"],
  nullable: true,
  notes: "Required whenever a treatment decision is applicable.",
};

export const RESPIRATORY_FOLLOW_UP_NEED_FIELD: RespiratoryFieldDefinition = {
  fieldId: "respiratory_follow_up_need",
  label: "Follow-Up Need",
  owner: "respiratory",
  ownerFactKey: "respiratory_exertion_tolerance",
  legacySource: "respiratory.followUpNeed",
  responseType: "single_select",
  controlledValues: ["NEEDED", "NOT_INDICATED"],
  nullable: true,
  notes: "Required for findings requiring disposition. Product-owner-authorized field (spec section 6).",
};

export const RESPIRATORY_FOLLOW_UP_TIMING_PLAN_FIELD: RespiratoryFieldDefinition = {
  fieldId: "respiratory_follow_up_timing_plan",
  label: "Follow-Up Timing / Plan",
  owner: "respiratory",
  ownerFactKey: "respiratory_exertion_tolerance",
  legacySource: "respiratory.followUpTimingPlan",
  responseType: "text",
  nullable: true,
  notes: "Required when followUpNeed = NEEDED.",
};

export const RESPIRATORY_FOLLOW_UP_RESPONSIBLE_CLINICIAN_FIELD: RespiratoryFieldDefinition = {
  fieldId: "respiratory_follow_up_responsible_clinician",
  label: "Follow-Up Responsible Clinician",
  owner: "respiratory",
  ownerFactKey: "respiratory_exertion_tolerance",
  legacySource: "respiratory.followUpResponsibleClinician",
  responseType: "text",
  nullable: true,
  notes: "Required when followUpNeed = NEEDED.",
};

export const RESPIRATORY_POC_REVIEW_NEED_FIELD: RespiratoryFieldDefinition = {
  fieldId: "respiratory_poc_review_need",
  label: "POC Review Need",
  owner: "respiratory",
  ownerFactKey: "respiratory_exertion_tolerance",
  legacySource: "respiratory.pocReviewNeed",
  responseType: "single_select",
  controlledValues: ["REVIEW_NEEDED", "NO_REVIEW_NEEDED"],
  nullable: true,
  notes:
    "Required when a clinically significant Respiratory finding or intervention may affect the Plan of Care. Does not automatically modify the POC.",
};

export const RESPIRATORY_POC_REVIEW_REASON_FIELD: RespiratoryFieldDefinition = {
  fieldId: "respiratory_poc_review_reason",
  label: "POC Review Reason",
  owner: "respiratory",
  ownerFactKey: "respiratory_exertion_tolerance",
  legacySource: "respiratory.pocReviewReason",
  responseType: "text",
  nullable: true,
  notes: "Required when pocReviewNeed = REVIEW_NEEDED.",
};

export const RESPIRATORY_POC_SOURCE_REFERENCE_FIELD: RespiratoryFieldDefinition = {
  fieldId: "respiratory_poc_source_reference",
  label: "POC Source Reference",
  owner: "respiratory",
  ownerFactKey: "respiratory_exertion_tolerance",
  legacySource: "respiratory.pocSourceReference",
  responseType: "text",
  nullable: true,
  notes: "Optional; references an existing POC source/issue/intervention only. Does not create or modify the POC.",
};

export const RESPIRATORY_OXYGEN_USE_FIELD: RespiratoryFieldDefinition = {
  fieldId: "respiratory_oxygen_use",
  label: "Oxygen Use",
  owner: "respiratory",
  ownerFactKey: "oxygen_use",
  legacySource: "respiratory.oxygenUse",
  responseType: "single_select",
  controlledValues: ["YES", "NO", "UNABLE_TO_VERIFY"],
  nullable: false,
  notes: "Required for completion. Product-owner-authorized field (spec section 7).",
};

export const RESPIRATORY_OXYGEN_UNABLE_TO_VERIFY_REASON_FIELD: RespiratoryFieldDefinition = {
  fieldId: "respiratory_oxygen_unable_to_verify_reason",
  label: "Oxygen Unable-to-Verify Reason",
  owner: "respiratory",
  ownerFactKey: "oxygen_use",
  legacySource: "respiratory.oxygenUnableToVerifyReason",
  responseType: "text",
  nullable: true,
  notes: "Required when oxygenUse = UNABLE_TO_VERIFY.",
};

export const RESPIRATORY_OXYGEN_DELIVERY_DEVICE_FIELD: RespiratoryFieldDefinition = {
  fieldId: "respiratory_oxygen_delivery_device",
  label: "Delivery Device",
  owner: "respiratory",
  ownerFactKey: "oxygen_use",
  legacySource: "respiratory.oxygenTherapy.deliveryDevice",
  responseType: "single_select",
  controlledValues: ["NASAL_CANNULA", "MASK", "OTHER"],
  nullable: true,
  notes: "Required when oxygenUse = YES. Distinct from the legacy free-vocabulary oxygenTherapy.type (preserved for backward compatibility).",
};

export const RESPIRATORY_OXYGEN_OTHER_DEVICE_FIELD: RespiratoryFieldDefinition = {
  fieldId: "respiratory_oxygen_other_device",
  label: "Other Device Specification",
  owner: "respiratory",
  ownerFactKey: "oxygen_use",
  legacySource: "respiratory.oxygenTherapy.otherDevice",
  responseType: "text",
  nullable: true,
  notes: "Required when deliveryDevice = OTHER.",
};

export const RESPIRATORY_OXYGEN_FLOW_VALUE_FIELD: RespiratoryFieldDefinition = {
  fieldId: "respiratory_oxygen_flow_value",
  label: "Flow Value",
  owner: "respiratory",
  ownerFactKey: "oxygen_use",
  legacySource: "respiratory.oxygenTherapy.flowValue",
  responseType: "number",
  nullable: true,
  notes: "Required when the selected device uses liters per minute. Must be nonnegative; no inferred/default value.",
};

export const RESPIRATORY_OXYGEN_FLOW_UNIT_FIELD: RespiratoryFieldDefinition = {
  fieldId: "respiratory_oxygen_flow_unit",
  label: "Flow Unit",
  owner: "respiratory",
  ownerFactKey: "oxygen_use",
  legacySource: "respiratory.oxygenTherapy.flowUnit",
  responseType: "single_select",
  controlledValues: ["L_MIN", "OTHER"],
  nullable: true,
  notes: "No hidden clinical default; set only when the user enters a value through a field explicitly labeled L/min.",
};

export const RESPIRATORY_OXYGEN_FREQUENCY_FIELD: RespiratoryFieldDefinition = {
  fieldId: "respiratory_oxygen_frequency",
  label: "Oxygen Frequency",
  owner: "respiratory",
  ownerFactKey: "oxygen_use",
  legacySource: "respiratory.oxygenTherapy.frequency",
  responseType: "single_select",
  controlledValues: ["CONTINUOUS", "PRN", "SCHEDULED", "OTHER"],
  nullable: true,
  notes: "Required when oxygenUse = YES.",
};

export const RESPIRATORY_SPO2_VALUE_FIELD: RespiratoryFieldDefinition = {
  fieldId: "respiratory_spo2_value",
  label: "SpO2 Value",
  owner: "respiratory",
  ownerFactKey: "oxygen_use",
  legacySource: "respiratory.spo2Value",
  responseType: "number",
  units: "%",
  nullable: true,
  notes: "Range 0-100. Not universally required if not obtained. Must not alone be used to infer oxygen use or severity.",
};

export const RESPIRATORY_SPO2_MEASUREMENT_CONDITION_FIELD: RespiratoryFieldDefinition = {
  fieldId: "respiratory_spo2_measurement_condition",
  label: "SpO2 Measurement Condition",
  owner: "respiratory",
  ownerFactKey: "oxygen_use",
  legacySource: "respiratory.spo2MeasurementCondition",
  responseType: "single_select",
  controlledValues: ["ROOM_AIR", "ON_OXYGEN", "NOT_OBTAINED"],
  nullable: true,
  notes: "Required whenever the SpO2 group is reviewed.",
};

export const RESPIRATORY_SPO2_NOT_OBTAINED_REASON_FIELD: RespiratoryFieldDefinition = {
  fieldId: "respiratory_spo2_not_obtained_reason",
  label: "SpO2 Not Obtained Reason",
  owner: "respiratory",
  ownerFactKey: "oxygen_use",
  legacySource: "respiratory.spo2NotObtainedReason",
  responseType: "text",
  nullable: true,
  notes: "Required when spo2MeasurementCondition = NOT_OBTAINED.",
};

export const RESPIRATORY_MEASURED_OXYGEN_FLOW_OR_CONCENTRATION_FIELD: RespiratoryFieldDefinition = {
  fieldId: "respiratory_measured_oxygen_flow_or_concentration",
  label: "Measured Oxygen Flow / Concentration",
  owner: "respiratory",
  ownerFactKey: "oxygen_use",
  legacySource: "respiratory.measuredOxygenFlowOrConcentration",
  responseType: "text",
  nullable: true,
  notes: "Required when SpO2 is documented on oxygen and the active therapy is measurable. No example-string defaults.",
};

export const RESPIRATORY_OXYGEN_MEASUREMENT_DATE_FIELD: RespiratoryFieldDefinition = {
  fieldId: "respiratory_oxygen_measurement_date",
  label: "Oxygen Measurement Date",
  owner: "respiratory",
  ownerFactKey: "oxygen_use",
  legacySource: "respiratory.oxygenMeasurementDate",
  responseType: "date",
  nullable: true,
  notes: "Required when an SpO2 value is documented.",
};

export const RESPIRATORY_OXYGEN_MEASUREMENT_TIME_FIELD: RespiratoryFieldDefinition = {
  fieldId: "respiratory_oxygen_measurement_time",
  label: "Oxygen Measurement Time",
  owner: "respiratory",
  ownerFactKey: "oxygen_use",
  legacySource: "respiratory.oxygenMeasurementTime",
  responseType: "time",
  nullable: true,
  notes: "Required when an SpO2 value is documented.",
};

export const RESPIRATORY_OXYGEN_EFFECTIVENESS_RESPONSE_FIELD: RespiratoryFieldDefinition = {
  fieldId: "respiratory_oxygen_effectiveness_response",
  label: "Oxygen Effectiveness / Response",
  owner: "respiratory",
  ownerFactKey: "oxygen_use",
  legacySource: "respiratory.oxygenEffectivenessResponse",
  responseType: "text",
  nullable: true,
  notes: "Required when oxygen use or a treatment response is currently assessed. Must not infer effectiveness from SpO2 alone.",
};

export const RESPIRATORY_SPUTUM_AMOUNT_FIELD: RespiratoryFieldDefinition = {
  fieldId: "respiratory_sputum_amount",
  label: "Sputum Amount",
  owner: "respiratory",
  ownerFactKey: "sputum",
  legacySource: "respiratory.sputumAmount",
  responseType: "single_select",
  controlledValues: ["SCANT", "SMALL", "MODERATE", "LARGE", "UNABLE_TO_ASSESS"],
  nullable: true,
  notes: "Required when coughType = Productive. Product-owner-authorized field (spec section 8).",
};

export const RESPIRATORY_SPUTUM_COLOR_FIELD: RespiratoryFieldDefinition = {
  fieldId: "respiratory_sputum_color",
  label: "Sputum Color",
  owner: "respiratory",
  ownerFactKey: "sputum",
  legacySource: "respiratory.sputumColor",
  responseType: "single_select",
  controlledValues: ["CLEAR", "WHITE", "YELLOW", "GREEN", "BROWN", "PINK", "RED_BLOODY", "RUST", "OTHER", "UNABLE_TO_ASSESS"],
  nullable: true,
  notes: "Required when coughType = Productive.",
};

export const RESPIRATORY_SPUTUM_OTHER_SPECIFICATION_FIELD: RespiratoryFieldDefinition = {
  fieldId: "respiratory_sputum_other_specification",
  label: "Sputum Other Specification",
  owner: "respiratory",
  ownerFactKey: "sputum",
  legacySource: "respiratory.sputumOtherSpecification",
  responseType: "text",
  nullable: true,
  notes: "Required when sputum character or color is OTHER.",
};

export const RESPIRATORY_COUGH_CLINICAL_SIGNIFICANCE_FIELD: RespiratoryFieldDefinition = {
  fieldId: "respiratory_cough_clinical_significance",
  label: "Cough Clinical Significance",
  owner: "respiratory",
  ownerFactKey: "cough",
  legacySource: "respiratory.coughClinicalSignificance",
  responseType: "text",
  nullable: true,
  notes: "Required for hemoptysis or when productive cough/secretions require action.",
};

export const RESPIRATORY_COUGH_ACTION_DECISION_FIELD: RespiratoryFieldDefinition = {
  fieldId: "respiratory_cough_action_decision",
  label: "Cough Action Decision",
  owner: "respiratory",
  ownerFactKey: "cough",
  legacySource: "respiratory.coughActionDecision",
  responseType: "single_select",
  controlledValues: ["ACTION_TAKEN", "DECLINED", "NOT_INDICATED"],
  nullable: true,
  notes: "Required when cough is productive, hemoptysis is present, or secretions require disposition.",
};

export const RESPIRATORY_COUGH_ACTION_DESCRIPTION_FIELD: RespiratoryFieldDefinition = {
  fieldId: "respiratory_cough_action_description",
  label: "Cough Action Description",
  owner: "respiratory",
  ownerFactKey: "cough",
  legacySource: "respiratory.coughActionDescription",
  responseType: "text",
  nullable: true,
  notes: "Required when coughActionDecision = ACTION_TAKEN.",
};

export const RESPIRATORY_COUGH_DECLINE_REASON_FIELD: RespiratoryFieldDefinition = {
  fieldId: "respiratory_cough_decline_reason",
  label: "Cough Action Decline Reason",
  owner: "respiratory",
  ownerFactKey: "cough",
  legacySource: "respiratory.coughDeclineReason",
  responseType: "text",
  nullable: true,
  notes: "Required when coughActionDecision = DECLINED.",
};

export const RESPIRATORY_COUGH_RESPONSE_FIELD: RespiratoryFieldDefinition = {
  fieldId: "respiratory_cough_response",
  label: "Cough Action Response",
  owner: "respiratory",
  ownerFactKey: "cough",
  legacySource: "respiratory.coughResponse",
  responseType: "text",
  nullable: true,
  notes: "Required when an action was taken unless response is pending.",
};

export const RESPIRATORY_COUGH_ACTION_DATE_TIME_FIELD: RespiratoryFieldDefinition = {
  fieldId: "respiratory_cough_action_date_time",
  label: "Cough Action Date/Time",
  owner: "respiratory",
  ownerFactKey: "cough",
  legacySource: "respiratory.coughActionDateTime",
  responseType: "datetime",
  nullable: true,
  notes: "Required when an action occurred during the current assessment.",
};

export const RESPIRATORY_COUGH_FOLLOW_UP_TIMING_PLAN_FIELD: RespiratoryFieldDefinition = {
  fieldId: "respiratory_cough_follow_up_timing_plan",
  label: "Cough Follow-Up Timing / Plan",
  owner: "respiratory",
  ownerFactKey: "cough",
  legacySource: "respiratory.coughFollowUpTimingPlan",
  responseType: "text",
  nullable: true,
  notes: "Required when cough follow-up is needed.",
};

export const RESPIRATORY_COUGH_FOLLOW_UP_RESPONSIBLE_CLINICIAN_FIELD: RespiratoryFieldDefinition = {
  fieldId: "respiratory_cough_follow_up_responsible_clinician",
  label: "Cough Follow-Up Responsible Clinician",
  owner: "respiratory",
  ownerFactKey: "cough",
  legacySource: "respiratory.coughFollowUpResponsibleClinician",
  responseType: "text",
  nullable: true,
  notes: "Required when cough follow-up is needed.",
};

export const RESPIRATORY_SUPPORT_STATUS_FIELD: RespiratoryFieldDefinition = {
  fieldId: "respiratory_support_status",
  label: "Respiratory Support Status",
  owner: "respiratory",
  ownerFactKey: "ventilator_airway_support",
  legacySource: "respiratory.respiratorySupportStatus",
  responseType: "single_select",
  controlledValues: ["NONE", "IN_USE", "UNABLE_TO_VERIFY"],
  nullable: false,
  notes: "Required for completion. Product-owner-authorized field (spec section 9).",
};

export const RESPIRATORY_SUPPORT_TYPES_FIELD: RespiratoryFieldDefinition = {
  fieldId: "respiratory_support_types",
  label: "Respiratory Support Types",
  owner: "respiratory",
  ownerFactKey: "ventilator_airway_support",
  legacySource: "respiratory.respiratorySupportTypes",
  responseType: "multi_select",
  controlledValues: ["VENTILATOR", "NON_INVASIVE_SUPPORT", "TRACHEOSTOMY", "SUCTION", "OTHER"],
  nullable: true,
  notes: "Required when respiratorySupportStatus = IN_USE.",
};

export const RESPIRATORY_VENTILATOR_DURATION_FIELD: RespiratoryFieldDefinition = {
  fieldId: "respiratory_ventilator_duration",
  label: "Ventilator Duration",
  owner: "respiratory",
  ownerFactKey: "ventilator_airway_support",
  legacySource: "respiratory.ventilator.duration",
  responseType: "single_select",
  controlledValues: ["SHORT_TERM", "LONG_TERM"],
  nullable: true,
  notes: "Required when VENTILATOR is selected. Canonical replacement for the legacy shortTermVentilator/longTermVentilator boolean pair.",
};

export const RESPIRATORY_VENTILATOR_SETTINGS_SOURCE_FIELD: RespiratoryFieldDefinition = {
  fieldId: "respiratory_ventilator_settings_source",
  label: "Ventilator Settings Source",
  owner: "respiratory",
  ownerFactKey: "ventilator_airway_support",
  legacySource: "respiratory.ventilator.settingsSource",
  responseType: "text",
  nullable: true,
  notes: "Required when settings are documented.",
};

export const RESPIRATORY_VENTILATOR_SETTINGS_DATE_FIELD: RespiratoryFieldDefinition = {
  fieldId: "respiratory_ventilator_settings_date",
  label: "Ventilator Settings Date",
  owner: "respiratory",
  ownerFactKey: "ventilator_airway_support",
  legacySource: "respiratory.ventilator.settingsDate",
  responseType: "date",
  nullable: true,
};

export const RESPIRATORY_VENTILATOR_SETTINGS_TIME_FIELD: RespiratoryFieldDefinition = {
  fieldId: "respiratory_ventilator_settings_time",
  label: "Ventilator Settings Time",
  owner: "respiratory",
  ownerFactKey: "ventilator_airway_support",
  legacySource: "respiratory.ventilator.settingsTime",
  responseType: "time",
  nullable: true,
  notes: "Required when current settings are documented as verified.",
};

export const RESPIRATORY_AIRWAY_SITE_FINDINGS_FIELD: RespiratoryFieldDefinition = {
  fieldId: "respiratory_airway_site_findings",
  label: "Airway Site Findings",
  owner: "respiratory",
  ownerFactKey: "ventilator_airway_support",
  legacySource: "respiratory.airwaySiteFindings",
  responseType: "text",
  nullable: true,
  notes: "Required when a tracheostomy or other artificial airway is assessed.",
};

export const RESPIRATORY_SUPPORT_RESPONSE_FIELD: RespiratoryFieldDefinition = {
  fieldId: "respiratory_support_response",
  label: "Respiratory Support Response",
  owner: "respiratory",
  ownerFactKey: "ventilator_airway_support",
  legacySource: "respiratory.respiratorySupportResponse",
  responseType: "text",
  nullable: true,
  notes: "Required when active support effectiveness is assessed.",
};

export const RESPIRATORY_SUPPORT_FOLLOW_UP_PLAN_FIELD: RespiratoryFieldDefinition = {
  fieldId: "respiratory_support_follow_up_plan",
  label: "Respiratory Support Follow-Up Plan",
  owner: "respiratory",
  ownerFactKey: "ventilator_airway_support",
  legacySource: "respiratory.respiratorySupportFollowUpPlan",
  responseType: "text",
  nullable: true,
  notes: "Required when a support concern, limitation, or unresolved finding exists.",
};

export const RESPIRATORY_SUPPORT_UNABLE_TO_VERIFY_REASON_FIELD: RespiratoryFieldDefinition = {
  fieldId: "respiratory_support_unable_to_verify_reason",
  label: "Respiratory Support Unable-to-Verify Reason",
  owner: "respiratory",
  ownerFactKey: "ventilator_airway_support",
  legacySource: "respiratory.respiratorySupportUnableToVerifyReason",
  responseType: "text",
  nullable: true,
  notes: "Required when respiratorySupportStatus = UNABLE_TO_VERIFY. Must not infer support from diagnosis, medication, or oxygen use.",
};

/**
 * Every verified Respiratory field, in the same order as the existing
 * production render-schema. `RESPIRATORY_OVERVIEW_FIELD` is intentionally
 * NOT included here — it is historical/legacy-read-only and must never be
 * rendered by the Contract v2 panel. `RESPIRATORY_NO_CURRENT_CONCERN_FIELD`
 * and `RESPIRATORY_UNABLE_TO_ASSESS_FIELD` are its non-gating replacements.
 */
export const RESPIRATORY_FIELD_INVENTORY: readonly RespiratoryFieldDefinition[] = [
  RESPIRATORY_ASSESSMENT_CONTEXT_FIELD,
  RESPIRATORY_CLINICAL_COMPARISON_FIELD,
  RESPIRATORY_CLINICAL_STATUS_CHANGE_DETAIL_FIELD,
  RESPIRATORY_NO_CURRENT_CONCERN_FIELD,
  RESPIRATORY_UNABLE_TO_ASSESS_FIELD,
  RESPIRATORY_UNABLE_TO_ASSESS_REASON_FIELD,
  RESPIRATORY_UNABLE_TO_ASSESS_OTHER_FIELD,
  RESPIRATORY_SHORTNESS_OF_BREATH_SCREENED_FIELD,
  RESPIRATORY_SCREENING_DATE_FIELD,
  RESPIRATORY_SOB_SEVERITY_FIELD,
  RESPIRATORY_EXERTION_LEVEL_FIELD,
  RESPIRATORY_COMFORT_FUNCTION_IMPACT_FIELD,
  RESPIRATORY_COMFORT_FUNCTION_EVIDENCE_FIELD,
  RESPIRATORY_COMFORT_FUNCTION_SCREENING_DATE_FIELD,
  RESPIRATORY_COMFORT_FUNCTION_SCREENING_TIME_FIELD,
  RESPIRATORY_CONFIGURED_REQUIREMENT_RESPONSE_FIELD,
  RESPIRATORY_CONFIGURED_FOLLOW_UP_STATUS_FIELD,
  RESPIRATORY_TREATMENT_DATE_FIELD,
  RESPIRATORY_LUNG_SOUNDS_FIELD,
  RESPIRATORY_RESPIRATION_PATTERN_FIELD,
  RESPIRATORY_TREATMENT_DECISION_FIELD,
  RESPIRATORY_TREATMENT_DESCRIPTION_FIELD,
  RESPIRATORY_TREATMENT_DECLINE_REASON_FIELD,
  RESPIRATORY_TREATMENT_ACTION_DATE_FIELD,
  RESPIRATORY_TREATMENT_ACTION_TIME_FIELD,
  RESPIRATORY_TREATMENT_RESPONSE_TIME_FIELD,
  RESPIRATORY_TREATMENT_RESPONSE_FIELD,
  RESPIRATORY_TREATMENT_RESPONSE_STATUS_FIELD,
  RESPIRATORY_FOLLOW_UP_NEED_FIELD,
  RESPIRATORY_FOLLOW_UP_TIMING_PLAN_FIELD,
  RESPIRATORY_FOLLOW_UP_RESPONSIBLE_CLINICIAN_FIELD,
  RESPIRATORY_POC_REVIEW_NEED_FIELD,
  RESPIRATORY_POC_REVIEW_REASON_FIELD,
  RESPIRATORY_POC_SOURCE_REFERENCE_FIELD,
  RESPIRATORY_COUGH_TYPE_FIELD,
  RESPIRATORY_SPUTUM_CHARACTER_FIELD,
  RESPIRATORY_SPUTUM_AMOUNT_FIELD,
  RESPIRATORY_SPUTUM_COLOR_FIELD,
  RESPIRATORY_SPUTUM_OTHER_SPECIFICATION_FIELD,
  RESPIRATORY_COUGH_CLINICAL_SIGNIFICANCE_FIELD,
  RESPIRATORY_COUGH_ACTION_DECISION_FIELD,
  RESPIRATORY_COUGH_ACTION_DESCRIPTION_FIELD,
  RESPIRATORY_COUGH_DECLINE_REASON_FIELD,
  RESPIRATORY_COUGH_RESPONSE_FIELD,
  RESPIRATORY_COUGH_ACTION_DATE_TIME_FIELD,
  RESPIRATORY_COUGH_FOLLOW_UP_TIMING_PLAN_FIELD,
  RESPIRATORY_COUGH_FOLLOW_UP_RESPONSIBLE_CLINICIAN_FIELD,
  RESPIRATORY_OXYGEN_USE_FIELD,
  RESPIRATORY_OXYGEN_UNABLE_TO_VERIFY_REASON_FIELD,
  RESPIRATORY_OXYGEN_IN_USE_FIELD,
  RESPIRATORY_OXYGEN_DELIVERY_TYPE_FIELD,
  RESPIRATORY_OXYGEN_DELIVERY_DEVICE_FIELD,
  RESPIRATORY_OXYGEN_OTHER_DEVICE_FIELD,
  RESPIRATORY_OXYGEN_LITERS_PER_MINUTE_FIELD,
  RESPIRATORY_OXYGEN_FLOW_VALUE_FIELD,
  RESPIRATORY_OXYGEN_FLOW_UNIT_FIELD,
  RESPIRATORY_OXYGEN_FREQUENCY_FIELD,
  RESPIRATORY_OXYGEN_HOURS_PER_DAY_FIELD,
  RESPIRATORY_OXYGEN_DELIVERY_MODE_FIELD,
  RESPIRATORY_OXYGEN_SAT_ON_O2_FIELD,
  RESPIRATORY_ON_ROOM_AIR_FIELD,
  RESPIRATORY_SPO2_VALUE_FIELD,
  RESPIRATORY_SPO2_MEASUREMENT_CONDITION_FIELD,
  RESPIRATORY_SPO2_NOT_OBTAINED_REASON_FIELD,
  RESPIRATORY_MEASURED_OXYGEN_FLOW_OR_CONCENTRATION_FIELD,
  RESPIRATORY_OXYGEN_MEASUREMENT_DATE_FIELD,
  RESPIRATORY_OXYGEN_MEASUREMENT_TIME_FIELD,
  RESPIRATORY_OXYGEN_EFFECTIVENESS_RESPONSE_FIELD,
  RESPIRATORY_SUPPORT_STATUS_FIELD,
  RESPIRATORY_SUPPORT_TYPES_FIELD,
  RESPIRATORY_VENTILATOR_SHORT_TERM_FIELD,
  RESPIRATORY_VENTILATOR_LONG_TERM_FIELD,
  RESPIRATORY_VENTILATOR_DURATION_FIELD,
  RESPIRATORY_VENTILATOR_TYPE_AND_SETTINGS_FIELD,
  RESPIRATORY_VENTILATOR_SETTINGS_SOURCE_FIELD,
  RESPIRATORY_VENTILATOR_SETTINGS_DATE_FIELD,
  RESPIRATORY_VENTILATOR_SETTINGS_TIME_FIELD,
  RESPIRATORY_TRACHEOSTOMY_TYPE_FIELD,
  RESPIRATORY_TRACHEOSTOMY_SIZE_FIELD,
  RESPIRATORY_AIRWAY_SITE_FINDINGS_FIELD,
  RESPIRATORY_SUPPORT_RESPONSE_FIELD,
  RESPIRATORY_SUPPORT_FOLLOW_UP_PLAN_FIELD,
  RESPIRATORY_SUPPORT_UNABLE_TO_VERIFY_REASON_FIELD,
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
