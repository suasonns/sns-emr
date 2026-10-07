/**
 * SNS Body Systems — validation architecture: required invariants, exception
 * generation/resolution, and the completion/blocking policy.
 *
 * Source of truth: docs/design/body-systems-figma/SNS_Body_Systems_Engineering_Specification.md
 * section 8 ("Validation Architecture") and section 9's AI-governance
 * constraint that AI may never set audit/identity fields. Keeps clinical
 * workflow and completion rules out of JSX, per section 8's explicit
 * instruction ("Do not place all rules inside JSX components").
 *
 * This module intentionally does NOT hardcode which `ExceptionType`s are
 * `record_blocking` vs. `signature_blocking` vs. informational — section 8's
 * "Blocking policy" explicitly says "Do not hardcode which fields are
 * blocking until the approved field inventory identifies them." Blocking
 * level is instead a property of each `ReviewException` instance (see
 * types.ts), set by whatever creates the exception; this module only
 * evaluates sets of already-leveled exceptions against the policy.
 */
import {
  BODY_SYSTEMS,
  type AssessmentLimitation,
  type BodySystemCode,
  type BradenAssessment,
  type ClinicalFinding,
  type Evidence,
  type ReviewException,
  type SystemAssessment,
  type WoundRecord,
} from "./types";

// ---------------------------------------------------------------------------
// Required invariants (section 8)
// ---------------------------------------------------------------------------

/** "All ten system rows are created for a new Body Systems assessment." */
export function allTenSystemsCreated(
  systemAssessments: readonly Pick<SystemAssessment, "system">[],
  expectedSystems: readonly BodySystemCode[] = BODY_SYSTEMS,
): boolean {
  const present = new Set(systemAssessments.map((entry) => entry.system));
  return expectedSystems.every((system) => present.has(system));
}

/**
 * "A system cannot be marked reviewed merely because prior data exists."
 * Evaluates whether a review-state transition to "reviewed"/
 * "reviewed_with_exception" is backed only by historical evidence (invalid)
 * versus at least one current-status evidence record (valid).
 */
export function reviewIsBackedByCurrentEvidence(evidenceUsed: readonly Pick<Evidence, "status">[]): boolean {
  return evidenceUsed.some((evidence) => evidence.status === "current");
}

/**
 * "A required finding cannot be silently defaulted to normal." A finding
 * with `currentState` of "present" or "absent" (i.e., an actual clinical
 * conclusion, as opposed to "unknown"/"not_assessed") must cite at least one
 * source evidence record — it cannot be a bare default with no evidence
 * trail.
 */
export function findingIsNotSilentlyDefaulted(finding: Pick<ClinicalFinding, "currentState" | "sourceEvidenceIds">): boolean {
  if (finding.currentState === "present" || finding.currentState === "absent") {
    return finding.sourceEvidenceIds.length > 0;
  }
  return true;
}

/** "AI cannot set `assessedBy`, `recordedBy`, or signature fields." */
const AI_FORBIDDEN_FIELDS = ["assessedBy", "recordedBy", "signedBy", "signedAt"] as const;

export function aiPatchViolatesAuditFieldRestriction(patch: Record<string, unknown>): boolean {
  return AI_FORBIDDEN_FIELDS.some((field) => Object.prototype.hasOwnProperty.call(patch, field));
}

export interface AISuggestionAcceptanceRecord {
  source: string;
  reviewer: string;
  reviewedAt: string;
  originalProposedValue: unknown;
  acceptedOrEditedValue: unknown;
}

/**
 * "An accepted AI suggestion must record source, reviewer, time, original
 * proposal, and accepted/edited value." Validates that an acceptance record
 * has every required field populated (non-empty strings; the two value
 * fields may legitimately be any value including falsy ones, so only
 * presence-as-a-key is checked for those two).
 */
export function aiSuggestionAcceptanceIsComplete(record: Partial<AISuggestionAcceptanceRecord>): boolean {
  return (
    typeof record.source === "string" &&
    record.source.length > 0 &&
    typeof record.reviewer === "string" &&
    record.reviewer.length > 0 &&
    typeof record.reviewedAt === "string" &&
    record.reviewedAt.length > 0 &&
    Object.prototype.hasOwnProperty.call(record, "originalProposedValue") &&
    Object.prototype.hasOwnProperty.call(record, "acceptedOrEditedValue")
  );
}

/** "A limitation requires a reason." */
export function limitationHasReason(limitation: Pick<AssessmentLimitation, "reason">): boolean {
  return limitation.reason.trim().length > 0;
}

/**
 * "Partial scope retains the unassessed scope as an exception." Given a
 * limitation whose `scope` lists the unassessed areas, returns the
 * `partial_scope` exception that must remain open until resolved — callers
 * must not simply drop the unassessed scope once a limitation is recorded.
 * `blockingLevel` is caller-supplied (not hardcoded here) per section 8's
 * instruction not to fix blocking classification ahead of the approved
 * field inventory.
 */
export function buildPartialScopeException(
  bodySystemsAssessmentId: string,
  system: BodySystemCode,
  limitation: Pick<AssessmentLimitation, "scope" | "reason">,
  blockingLevel: ReviewException["blockingLevel"],
): Omit<ReviewException, "id"> {
  return {
    bodySystemsAssessmentId,
    system,
    type: "partial_scope",
    message: `Unassessed scope (${limitation.scope.join(", ")}): ${limitation.reason}`,
    blockingLevel,
    status: "open",
  };
}

/** "Unreviewed system" exception — a system that has not been reviewed for the current assessment. */
export function buildUnreviewedSystemException(
  bodySystemsAssessmentId: string,
  system: BodySystemCode,
  blockingLevel: ReviewException["blockingLevel"],
): Omit<ReviewException, "id"> {
  return {
    bodySystemsAssessmentId,
    system,
    type: "unreviewed_system",
    message: `${system} has not been reviewed for this assessment.`,
    blockingLevel,
    status: "open",
  };
}

/** "Required limitation missing for unable-to-assess" — raised when `situation` is unable_to_assess but no limitation is recorded. */
export function buildMissingLimitationException(
  bodySystemsAssessmentId: string,
  system: BodySystemCode,
  blockingLevel: ReviewException["blockingLevel"],
): Omit<ReviewException, "id"> {
  return {
    bodySystemsAssessmentId,
    system,
    type: "unable_to_assess",
    message: `${system} is marked unable to assess but has no documented limitation (scope and reason).`,
    blockingLevel,
    status: "open",
  };
}

/** "Required field missing" — raised when a field required by the approved configuration (situation branch, wound record, etc.) is absent. */
export function buildRequiredFieldMissingException(
  bodySystemsAssessmentId: string,
  system: BodySystemCode,
  fieldPath: string,
  blockingLevel: ReviewException["blockingLevel"],
): Omit<ReviewException, "id"> {
  return {
    bodySystemsAssessmentId,
    system,
    type: "required_field_missing",
    fieldPath,
    message: `Required field "${fieldPath}" is missing.`,
    blockingLevel,
    status: "open",
  };
}

/** "Missing source" — raised when a finding/evidence record has no identified source. */
export function buildMissingSourceException(
  bodySystemsAssessmentId: string,
  system: BodySystemCode,
  fieldPath: string,
  blockingLevel: ReviewException["blockingLevel"],
): Omit<ReviewException, "id"> {
  return {
    bodySystemsAssessmentId,
    system,
    type: "source_missing",
    fieldPath,
    message: `No evidence source is recorded for "${fieldPath}".`,
    blockingLevel,
    status: "open",
  };
}

/** "Missing date/time" — raised when a finding/evidence record has no observed/sourced date-time. */
export function buildMissingDateTimeException(
  bodySystemsAssessmentId: string,
  system: BodySystemCode,
  fieldPath: string,
  blockingLevel: ReviewException["blockingLevel"],
): Omit<ReviewException, "id"> {
  return {
    bodySystemsAssessmentId,
    system,
    type: "date_time_missing",
    fieldPath,
    message: `No date/time is recorded for "${fieldPath}".`,
    blockingLevel,
    status: "open",
  };
}

/** "Conflicting evidence" — raised when two or more current-status evidence records disagree about the same fact. */
export function buildConflictingEvidenceException(
  bodySystemsAssessmentId: string,
  system: BodySystemCode,
  fieldPath: string,
  blockingLevel: ReviewException["blockingLevel"],
): Omit<ReviewException, "id"> {
  return {
    bodySystemsAssessmentId,
    system,
    type: "conflicting_evidence",
    fieldPath,
    message: `Conflicting evidence found for "${fieldPath}"; clinician reconciliation required.`,
    blockingLevel,
    status: "open",
  };
}

/** "Nurse judgment required" — raised when a situation cannot be resolved by rule alone and needs explicit clinical judgment. */
export function buildNurseJudgmentRequiredException(
  bodySystemsAssessmentId: string,
  system: BodySystemCode,
  message: string,
  blockingLevel: ReviewException["blockingLevel"],
): Omit<ReviewException, "id"> {
  return {
    bodySystemsAssessmentId,
    system,
    type: "nurse_judgment_required",
    message,
    blockingLevel,
    status: "open",
  };
}

/** "Low-confidence AI" — raised when an AI suggestion's confidence is below the threshold required for unreviewed acceptance. */
export function buildLowConfidenceAIException(
  bodySystemsAssessmentId: string,
  system: BodySystemCode,
  fieldPath: string,
  blockingLevel: ReviewException["blockingLevel"],
): Omit<ReviewException, "id"> {
  return {
    bodySystemsAssessmentId,
    system,
    type: "low_confidence_ai",
    fieldPath,
    message: `AI suggestion for "${fieldPath}" has low confidence and requires clinician review.`,
    blockingLevel,
    status: "open",
  };
}

/** "Missing follow-up" — raised when a new_or_worsening situation (or similar) lacks a required follow-up decision. */
export function buildMissingFollowUpException(
  bodySystemsAssessmentId: string,
  system: BodySystemCode,
  blockingLevel: ReviewException["blockingLevel"],
): Omit<ReviewException, "id"> {
  return {
    bodySystemsAssessmentId,
    system,
    type: "follow_up_missing",
    message: `${system} requires a documented follow-up decision.`,
    blockingLevel,
    status: "open",
  };
}

/** "Wound marker alone cannot satisfy wound documentation." */
export function woundMarkerAloneSatisfiesWoundRecord(
  wound: Pick<WoundRecord, "bodyDiagramMarker" | "locationText" | "woundType">,
): boolean {
  const hasOnlyMarker = Boolean(wound.bodyDiagramMarker) && (!wound.locationText || !wound.woundType);
  return hasOnlyMarker ? false : Boolean(wound.locationText && wound.woundType);
}

/** "Braden total must be derived from subscales, not independently editable." */
export function bradenTotalIsDerivedFromSubscales(
  braden: Pick<
    BradenAssessment,
    "sensoryPerception" | "moisture" | "activity" | "mobility" | "nutrition" | "frictionShear" | "total"
  >,
): boolean {
  const derived =
    braden.sensoryPerception + braden.moisture + braden.activity + braden.mobility + braden.nutrition + braden.frictionShear;
  return derived === braden.total;
}

// ---------------------------------------------------------------------------
// Blocking policy (section 8, "Blocking policy")
// ---------------------------------------------------------------------------

/** "Draft save is allowed with open exceptions." Always true — documented as a function for call-site clarity. */
export function canSaveDraft(exceptions: readonly ReviewException[]): true {
  void exceptions;
  return true;
}

function hasOpenExceptionsOfLevel(
  exceptions: readonly ReviewException[],
  blockingLevel: ReviewException["blockingLevel"],
): boolean {
  return exceptions.some((exception) => exception.status === "open" && exception.blockingLevel === blockingLevel);
}

/** "'Record review' requires all `record_blocking` exceptions resolved." */
export function canRecordReview(exceptions: readonly ReviewException[]): boolean {
  return !hasOpenExceptionsOfLevel(exceptions, "record_blocking");
}

/** "Signature requires all `signature_blocking` exceptions resolved." */
export function canSign(exceptions: readonly ReviewException[]): boolean {
  return !hasOpenExceptionsOfLevel(exceptions, "signature_blocking");
}

/**
 * "Unresolved items stay visible; the application must not pretend
 * completion." Returns every still-open exception so a caller can render
 * them rather than hide them once a lower gate (e.g. draft save) succeeds.
 */
export function getOpenExceptions(exceptions: readonly ReviewException[]): ReviewException[] {
  return exceptions.filter((exception) => exception.status === "open");
}
