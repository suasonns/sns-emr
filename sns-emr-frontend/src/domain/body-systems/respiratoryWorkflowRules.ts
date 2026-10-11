/**
 * SNS Body Systems — Respiratory workflow rules.
 *
 * Bridges the generic situation-branch requirement graph in
 * `stateMachine.ts` (section 7) and the generic exception/blocking policy
 * in `exceptionRules.ts` (section 8) to the verified Respiratory field
 * inventory in `respiratoryFieldInventory.ts`. This is the proof-of-pattern
 * module for the Respiratory milestone (specification section 19, "Third
 * recommended GitHub task") — later systems should follow this same shape
 * (a `<system>FieldInventory.ts` + a `<system>WorkflowRules.ts` pair) rather
 * than growing a single shared "do everything" module.
 *
 * Per the milestone's explicit instruction, any situation-branch
 * requirement with no repository-backed field
 * (`RESPIRATORY_NOT_VERIFIED_REQUIREMENTS`) is evaluated as "always
 * informational, never blocking" here — it is surfaced as an open
 * `ReviewException` so the gap stays visible, but it can never prevent a
 * draft save, a recorded review, or a signature, because its presence/
 * absence cannot yet be derived from any approved field.
 */
import { getMissingSituationRequirements, getSituationRequirements } from "./stateMachine";
import {
  buildMissingFollowUpException,
  buildMissingLimitationException,
  buildRequiredFieldMissingException,
} from "./exceptionRules";
import { isRespiratoryRequirementNotVerified } from "./respiratoryFieldInventory";
import { textFilled } from "./respiratoryProductRequirements";
import {
  getMissingProductAuthorizedRequirements,
  type RespiratoryProductAuthorizedValues,
} from "./respiratoryProductRequirements";
import type { AssessmentSituation, ReviewException } from "./types";

export interface RespiratoryOxygenTherapyValues {
  inUse?: boolean;
  type?: string;
  litersPerMinute?: number;
  hoursPerDay?: string;
  deliveryMode?: string;
  satOnO2?: number;
  onRoomAir?: boolean;
  // Product-owner-authorized fields (new canonical oxygen measurement/
  // delivery detail; coexist with the legacy fields above — see
  // respiratoryProductRequirements.ts and spec section 13).
  deliveryDevice?: string;
  otherDevice?: string;
  flowValue?: number;
  flowUnit?: string;
  frequency?: string;
}

export interface RespiratoryVentilatorValues {
  shortTermVentilator?: boolean;
  longTermVentilator?: boolean;
  ventilatorTypeAndSettings?: string;
  tracheostomyType?: string;
  tracheostomySize?: string;
  // Product-owner-authorized fields (coexist with the legacy short/long-term
  // booleans above — see respiratoryProductRequirements.ts).
  duration?: string;
  settingsSource?: string;
  settingsDate?: string;
  settingsTime?: string;
}

/** Shape of the Respiratory data this module evaluates — a subset of the legacy `respiratory` object limited to verified fields. */
export interface RespiratoryAssessmentValues {
  respiratoryOverview?: string;
  respiratoryNoCurrentConcern?: boolean;
  respiratoryUnableToAssess?: boolean;
  respiratoryUnableToAssessReason?: string;
  respiratoryUnableToAssessOther?: string;
  shortnessOfBreathScreened?: boolean;
  screeningDate?: string;
  treatmentDate?: string;
  sobSeverity?: string;
  exertionLevel?: string;
  lungSounds?: readonly string[];
  respirations?: readonly string[];
  coughType?: string;
  sputumCharacter?: string;
  oxygenTherapy?: RespiratoryOxygenTherapyValues;
  ventilator?: RespiratoryVentilatorValues;
  treatmentInitiated?: boolean;
  treatmentDeclined?: boolean;
  clinicalStatusChange?: string;
  notes?: string;

  // --- Product-owner-authorized fields (spec sections 3-9) --------------
  assessmentContext?: string;
  clinicalComparison?: string;
  clinicalStatusChangeDetail?: string;
  comfortFunctionImpact?: string;
  comfortFunctionEvidence?: string;
  comfortFunctionScreeningDate?: string;
  comfortFunctionScreeningTime?: string;
  configuredRequirementResponse?: string;
  configuredFollowUpStatus?: string;
  treatmentDecision?: string;
  treatmentDescription?: string;
  treatmentDeclineReason?: string;
  treatmentActionDate?: string;
  treatmentActionTime?: string;
  treatmentResponseTime?: string;
  treatmentResponse?: string;
  treatmentResponseStatus?: string;
  followUpNeed?: string;
  followUpTimingPlan?: string;
  followUpResponsibleClinician?: string;
  pocReviewNeed?: string;
  pocReviewReason?: string;
  pocSourceReference?: string;
  oxygenUse?: string;
  oxygenUnableToVerifyReason?: string;
  spo2Value?: number;
  spo2MeasurementCondition?: string;
  spo2NotObtainedReason?: string;
  measuredOxygenFlowOrConcentration?: string;
  oxygenMeasurementDate?: string;
  oxygenMeasurementTime?: string;
  oxygenEffectivenessResponse?: string;
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
  respiratorySupportStatus?: string;
  respiratorySupportTypes?: readonly string[];
  airwaySiteFindings?: string;
  respiratorySupportResponse?: string;
  respiratorySupportFollowUpPlan?: string;
  respiratorySupportUnableToVerifyReason?: string;
}

/** Projects the fields `respiratoryProductRequirements.ts` needs out of the full `RespiratoryAssessmentValues` shape. */
function toProductAuthorizedValues(values: RespiratoryAssessmentValues): RespiratoryProductAuthorizedValues {
  return {
    assessmentContext: values.assessmentContext,
    clinicalComparison: values.clinicalComparison,
    clinicalStatusChangeDetail: values.clinicalStatusChangeDetail,
    comfortFunctionImpact: values.comfortFunctionImpact,
    comfortFunctionEvidence: values.comfortFunctionEvidence,
    configuredRequirementResponse: values.configuredRequirementResponse,
    configuredFollowUpStatus: values.configuredFollowUpStatus,
    treatmentDecision: values.treatmentDecision,
    treatmentDescription: values.treatmentDescription,
    treatmentDeclineReason: values.treatmentDeclineReason,
    treatmentActionDate: values.treatmentActionDate,
    treatmentActionTime: values.treatmentActionTime,
    treatmentResponse: values.treatmentResponse,
    treatmentResponseStatus: values.treatmentResponseStatus,
    followUpNeed: values.followUpNeed,
    followUpTimingPlan: values.followUpTimingPlan,
    followUpResponsibleClinician: values.followUpResponsibleClinician,
    pocReviewNeed: values.pocReviewNeed,
    pocReviewReason: values.pocReviewReason,
    oxygenUse: values.oxygenUse,
    oxygenUnableToVerifyReason: values.oxygenUnableToVerifyReason,
    oxygenTherapy: values.oxygenTherapy
      ? {
          deliveryDevice: values.oxygenTherapy.deliveryDevice,
          otherDevice: values.oxygenTherapy.otherDevice,
          flowValue: values.oxygenTherapy.flowValue,
          flowUnit: values.oxygenTherapy.flowUnit,
          frequency: values.oxygenTherapy.frequency,
          hoursPerDay: values.oxygenTherapy.hoursPerDay,
          deliveryMode: values.oxygenTherapy.deliveryMode,
        }
      : undefined,
    spo2Value: values.spo2Value,
    spo2MeasurementCondition: values.spo2MeasurementCondition,
    spo2NotObtainedReason: values.spo2NotObtainedReason,
    measuredOxygenFlowOrConcentration: values.measuredOxygenFlowOrConcentration,
    oxygenMeasurementDate: values.oxygenMeasurementDate,
    oxygenMeasurementTime: values.oxygenMeasurementTime,
    oxygenEffectivenessResponse: values.oxygenEffectivenessResponse,
    coughType: values.coughType,
    sputumCharacter: values.sputumCharacter,
    sputumAmount: values.sputumAmount,
    sputumColor: values.sputumColor,
    sputumOtherSpecification: values.sputumOtherSpecification,
    coughClinicalSignificance: values.coughClinicalSignificance,
    coughActionDecision: values.coughActionDecision,
    coughActionDescription: values.coughActionDescription,
    coughDeclineReason: values.coughDeclineReason,
    coughResponse: values.coughResponse,
    coughActionDateTime: values.coughActionDateTime,
    coughFollowUpTimingPlan: values.coughFollowUpTimingPlan,
    coughFollowUpResponsibleClinician: values.coughFollowUpResponsibleClinician,
    sobSeverity: values.sobSeverity,
    respiratorySupportStatus: values.respiratorySupportStatus,
    respiratorySupportTypes: values.respiratorySupportTypes,
    ventilator: values.ventilator
      ? {
          duration: values.ventilator.duration,
          settingsSource: values.ventilator.settingsSource,
          settingsDate: values.ventilator.settingsDate,
          settingsTime: values.ventilator.settingsTime,
        }
      : undefined,
    airwaySiteFindings: values.airwaySiteFindings,
    respiratorySupportResponse: values.respiratorySupportResponse,
    respiratorySupportFollowUpPlan: values.respiratorySupportFollowUpPlan,
    respiratorySupportUnableToVerifyReason: values.respiratorySupportUnableToVerifyReason,
  };
}

/** Maps the verified `respiratoryOverview` controlled values to the canonical `AssessmentSituation` enum. Exhaustive; throws on an unrecognized value rather than silently defaulting a situation. */
const OVERVIEW_TO_SITUATION: Record<string, AssessmentSituation> = {
  "No Current Respiratory Concern": "no_current_concern",
  "Existing Respiratory Findings Review": "stable_existing",
  "New or Worsening Respiratory Findings": "new_or_worsening",
  "Unable to Assess": "unable_to_assess",
};

export function mapRespiratoryOverviewToSituation(overviewValue: string): AssessmentSituation {
  const mapped = OVERVIEW_TO_SITUATION[overviewValue];
  if (!mapped) {
    throw new Error(`Unrecognized respiratoryOverview value: "${overviewValue}"`);
  }
  return mapped;
}

function hasAnyCurrentFindingFieldPopulated(values: RespiratoryAssessmentValues): boolean {
  return Boolean(
    values.sobSeverity ||
      values.exertionLevel ||
      (values.lungSounds && values.lungSounds.length > 0) ||
      (values.respirations && values.respirations.length > 0) ||
      // "None" is coughType's explicit "no cough finding" sentinel value
      // (same convention as sobSeverity's "None"), not an entered finding.
      // Excluding it here matters once `respiratory_cough_type` becomes
      // an always-required field (respiratoryProductRequirements.ts): a
      // "No current respiratory concern" review must still be able to
      // record coughType = "None" without that choice itself flipping the
      // derived situation away from `no_current_concern`.
      (values.coughType && values.coughType !== "None") ||
      values.sputumCharacter ||
      values.oxygenTherapy?.inUse ||
      values.ventilator?.shortTermVentilator ||
      values.ventilator?.longTermVentilator,
  );
}

function hasDocumentedIntervention(values: RespiratoryAssessmentValues): boolean {
  return values.treatmentDecision === "INITIATED" || values.treatmentDecision === "ALREADY_IN_PLACE";
}

function hasDocumentedResponse(values: RespiratoryAssessmentValues): boolean {
  if (!hasDocumentedIntervention(values)) {
    return false;
  }
  if (!values.treatmentResponseStatus) {
    return false;
  }
  if (values.treatmentResponseStatus === "PENDING") {
    return true;
  }
  return textFilled(values.treatmentResponse);
}

function hasDocumentedDeclineDisposition(values: RespiratoryAssessmentValues): boolean {
  if (values.treatmentDecision !== "DECLINED") {
    return false;
  }
  if (!textFilled(values.treatmentDeclineReason)) {
    return false;
  }
  if (!values.followUpNeed) {
    return false;
  }
  if (values.followUpNeed === "NEEDED") {
    return textFilled(values.followUpTimingPlan) && textFilled(values.followUpResponsibleClinician);
  }
  return true;
}

function hasDocumentedNotIndicatedDisposition(values: RespiratoryAssessmentValues): boolean {
  return values.treatmentDecision === "NOT_INDICATED";
}

/**
 * Canonical Treatment Decision counterpart of the legacy-only check below.
 * Per the product-owner-authorized semantics:
 * - INITIATED/ALREADY_IN_PLACE counts as documented intervention only once
 *   its applicable response evidence is also present (an enum selection
 *   alone is not a complete intervention);
 * - DECLINED counts as a documented disposition (not an intervention) once
 *   the decline reason and applicable follow-up are complete;
 * - NOT_INDICATED counts as a documented disposition (not an intervention
 *   or response) from the selection alone — there is no repository-backed
 *   rationale field for this value yet, so a rationale cannot be required
 *   here without inventing one.
 */
function hasCompleteTreatmentDisposition(values: RespiratoryAssessmentValues): boolean {
  return (
    (hasDocumentedIntervention(values) && hasDocumentedResponse(values)) ||
    hasDocumentedDeclineDisposition(values) ||
    hasDocumentedNotIndicatedDisposition(values)
  );
}

/**
 * Legacy boolean pair (kept, unchanged) OR'd with the canonical Treatment
 * Decision disposition and the canonical oxygen-use/ventilator-duration
 * fields — either path independently satisfies this situation-branch
 * requirement, so a record entered entirely through the canonical UI (with
 * the legacy checkboxes now hidden) is evaluated the same as one entered
 * through the retired legacy controls.
 */
function hasDocumentedInterventionOrResponse(values: RespiratoryAssessmentValues): boolean {
  return Boolean(
    values.treatmentInitiated === true ||
      values.treatmentDeclined === true ||
      values.oxygenTherapy?.inUse === true ||
      values.ventilator?.shortTermVentilator === true ||
      values.ventilator?.longTermVentilator === true ||
      hasCompleteTreatmentDisposition(values) ||
      values.oxygenUse === "YES" ||
      Boolean(values.ventilator?.duration),
  );
}

function hasDocumentedCurrentFindingOrChange(values: RespiratoryAssessmentValues): boolean {
  const changeIndicatesNewOrWorsening =
    values.clinicalStatusChange === "Declining" || values.clinicalStatusChange === "New Symptom Since Prior Assessment";
  return Boolean(changeIndicatesNewOrWorsening || hasAnyCurrentFindingFieldPopulated(values));
}

function hasDocumentedUnableToAssessReason(values: RespiratoryAssessmentValues): boolean {
  if (!values.respiratoryUnableToAssessReason) {
    return false;
  }
  if (values.respiratoryUnableToAssessReason === "Other") {
    return Boolean(values.respiratoryUnableToAssessOther && values.respiratoryUnableToAssessOther.trim().length > 0);
  }
  return true;
}

/**
 * Evaluates which of `stateMachine.ts`'s generic requirement keys are
 * satisfied for `situation`, given the verified Respiratory fields
 * currently entered. A requirement with no backing field
 * (`isRespiratoryRequirementNotVerified`) is never reported as satisfied —
 * it is always listed as missing, but `buildRespiratoryExceptions` below
 * gives it `informational` blocking level rather than a blocking one.
 */
export function getSatisfiedRespiratoryRequirementKeys(
  situation: AssessmentSituation,
  values: RespiratoryAssessmentValues,
): string[] {
  const satisfied = new Set<string>();
  switch (situation) {
    case "no_current_concern":
      // The explicit "No Current Respiratory Concern" selection is itself
      // the documented current-review action in the existing production
      // workflow (see RESPIRATORY_OVERVIEW_FIELD notes) — there is no
      // separate "evidence" field to additionally check.
      satisfied.add("current_review_evidence");
      break;
    case "stable_existing":
      if (hasAnyCurrentFindingFieldPopulated(values) || Boolean(values.clinicalStatusChange)) {
        satisfied.add("current_confirmation");
      }
      break;
    case "new_or_worsening":
      if (hasDocumentedCurrentFindingOrChange(values)) {
        satisfied.add("current_finding_or_change");
      }
      if (hasDocumentedInterventionOrResponse(values)) {
        satisfied.add("intervention_or_response");
      }
      break;
    case "unable_to_assess":
      if (hasDocumentedUnableToAssessReason(values)) {
        satisfied.add("reason");
      }
      break;
    default: {
      const exhaustiveCheck: never = situation;
      throw new Error(`Unhandled assessment situation: ${String(exhaustiveCheck)}`);
    }
  }
  return Array.from(satisfied);
}

/**
 * Builds the open `ReviewException`s for whatever this situation's
 * requirements are still missing, using the generic requirement list from
 * `stateMachine.ts` so this module can never silently diverge from the
 * approved requirement graph. Requirements with no backing field get
 * `informational` blocking level (never blocking); the one genuinely
 * verified gap — a missing `unable_to_assess` reason — reuses the existing
 * `buildMissingLimitationException` at `record_blocking`, matching
 * `AssessmentLimitation.reason` already being a required field in the
 * approved domain model (section 4.2).
 */
export function buildRespiratoryExceptions(
  bodySystemsAssessmentId: string,
  situation: AssessmentSituation,
  values: RespiratoryAssessmentValues,
): Array<Omit<ReviewException, "id">> {
  const satisfiedKeys = getSatisfiedRespiratoryRequirementKeys(situation, values);
  const missingKeys = getMissingSituationRequirements(situation, satisfiedKeys);
  const exceptions: Array<Omit<ReviewException, "id">> = [];

  for (const key of missingKeys) {
    if (isRespiratoryRequirementNotVerified(key)) {
      if (key === "follow_up_decision") {
        exceptions.push(buildMissingFollowUpException(bodySystemsAssessmentId, "respiratory", "informational"));
      } else {
        exceptions.push(
          buildRequiredFieldMissingException(bodySystemsAssessmentId, "respiratory", key, "informational"),
        );
      }
      continue;
    }
    if (situation === "unable_to_assess" && key === "reason") {
      exceptions.push(buildMissingLimitationException(bodySystemsAssessmentId, "respiratory", "record_blocking"));
      continue;
    }
    // Any other verified-but-unmapped key would indicate the requirement
    // graph grew a key this module doesn't yet know how to evaluate —
    // surface it rather than silently dropping it.
    exceptions.push(buildRequiredFieldMissingException(bodySystemsAssessmentId, "respiratory", key, "informational"));
  }

  return exceptions;
}

/** Convenience re-export so callers don't need a separate import from `stateMachine.ts` just to check the full requirement list for a situation. */
export { getSituationRequirements };

// ---------------------------------------------------------------------------
// Non-gating situation derivation (Contract v2 integration)
// ---------------------------------------------------------------------------

/**
 * Derives the current `AssessmentSituation` from entered data, instead of
 * requiring the nurse to pick it from an upfront selector before any other
 * field is enabled. This is the replacement for the retired
 * `respiratoryOverview` entry gate: every current-evidence field is always
 * visible and editable regardless of this derived value, and this function
 * is re-evaluated on every change rather than being fixed once at entry.
 *
 * Returns `null` when nothing has been entered yet — a blank/untouched
 * system has no situation and must never be reported as
 * "no_current_concern" merely because it is empty (Contract v2: blank data
 * can never auto-complete review).
 *
 * Precedence: an explicit "unable to assess" toggle always wins (a nurse
 * may document partial current findings AND a limitation for the rest, but
 * the system as a whole is reported unable-to-assess until that toggle is
 * cleared). Otherwise, any current-evidence field populated means the
 * situation is derived from the data (new_or_worsening vs. stable_existing
 * based on `clinicalStatusChange`). Otherwise, the explicit
 * "no current concern" declaration (and only that explicit declaration)
 * resolves to no_current_concern.
 */
export function deriveRespiratorySituation(values: RespiratoryAssessmentValues): AssessmentSituation | null {
  if (values.respiratoryUnableToAssess) {
    return "unable_to_assess";
  }
  if (hasDocumentedCurrentFindingOrChange(values)) {
    const isWorsening =
      values.clinicalStatusChange === "Declining" || values.clinicalStatusChange === "New Symptom Since Prior Assessment";
    return isWorsening ? "new_or_worsening" : "stable_existing";
  }
  if (values.respiratoryNoCurrentConcern) {
    return "no_current_concern";
  }
  return null;
}

export interface RespiratoryReviewCompletionResult {
  /** Whether "Complete system review" may be performed right now. */
  complete: boolean;
  /** Human-readable, field-referencing messages describing what is missing. Empty when `complete` is true. */
  blockingMessages: string[];
  /** The derived situation used to evaluate completion, or null if nothing has been entered yet. */
  situation: AssessmentSituation | null;
  /** Field IDs (from `respiratoryFieldInventory.ts`) for every unresolved product-owner-authorized requirement — for field-level highlighting in the panel. */
  missingProductAuthorizedFieldIds: string[];
}

const BLOCKING_MESSAGE_BY_REQUIREMENT_KEY: Record<string, string> = {
  current_review_evidence: "Record the explicit \"No current respiratory concern\" declaration.",
  current_confirmation: "Document at least one current respiratory finding or a clinical status change.",
  current_finding_or_change: "Document the current respiratory finding or clinical status change.",
  intervention_or_response: "Document the intervention/response (treatment initiated or declined, or active oxygen/ventilator support).",
  reason: "Document the reason the respiratory system could not be fully assessed.",
};

/**
 * Explicit, non-gating "Complete system review" validation. Unlike the
 * retired entry gate, this is evaluated against whatever situation the
 * data itself resolves to (see `deriveRespiratorySituation`) and never
 * blocks draft save — it only blocks the explicit completion action.
 * Requirement keys with no repository-backed field
 * (`isRespiratoryRequirementNotVerified`) never block completion; they
 * remain informational-only per the existing milestone scope.
 */
export function getRespiratoryReviewCompletion(values: RespiratoryAssessmentValues): RespiratoryReviewCompletionResult {
  const productAuthorizedGaps = getMissingProductAuthorizedRequirements(toProductAuthorizedValues(values));
  const productAuthorizedFieldIds = productAuthorizedGaps.map((gap) => gap.fieldId);
  const productAuthorizedMessages = productAuthorizedGaps.map((gap) => gap.message);

  const situation = deriveRespiratorySituation(values);
  if (!situation) {
    return {
      complete: false,
      situation: null,
      blockingMessages: [
        "Enter at least one respiratory finding, or explicitly record \"No current respiratory concern\" / \"Unable to fully assess\".",
        ...productAuthorizedMessages,
      ],
      missingProductAuthorizedFieldIds: productAuthorizedFieldIds,
    };
  }
  const satisfiedKeys = getSatisfiedRespiratoryRequirementKeys(situation, values);
  const missingKeys = getMissingSituationRequirements(situation, satisfiedKeys).filter(
    (key) => !isRespiratoryRequirementNotVerified(key),
  );
  return {
    // Product-owner-authorized gaps now block completion (UI controls
    // exist for every field this engine can require as of the UI-wiring
    // pass completed in RespiratoryPanel.tsx) — promoted per explicit
    // product-owner direction superseding the prior informational-only
    // decision.
    complete: missingKeys.length === 0 && productAuthorizedGaps.length === 0,
    situation,
    blockingMessages: [
      ...missingKeys.map((key) => BLOCKING_MESSAGE_BY_REQUIREMENT_KEY[key] ?? `Missing requirement: ${key}`),
      ...productAuthorizedMessages,
    ],
    missingProductAuthorizedFieldIds: productAuthorizedFieldIds,
  };
}
