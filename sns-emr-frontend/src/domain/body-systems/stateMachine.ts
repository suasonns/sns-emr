/**
 * SNS Body Systems — assessment state machine.
 *
 * Source of truth: docs/design/body-systems-figma/SNS_Body_Systems_Engineering_Specification.md
 * section 7 ("System State Machine"). Transcribes the review-state
 * transition graph and the per-situation required-evidence branches exactly
 * as specified. "Unable to assess" must never be convertible to normal,
 * reviewed-without-limitation, or fully assessed — `nextReviewState` and
 * `getSituationRequirements` enforce this by construction, not by a special
 * case a caller could bypass.
 */
import type { AssessmentSituation, SystemReviewState } from "./types";

export interface ReviewStateTransition {
  from: SystemReviewState;
  to: SystemReviewState;
  trigger: string;
}

/**
 * The full transition graph from section 7:
 *
 * NOT_REVIEWED -> IN_PROGRESS -> REVIEWED -> REVIEWED_WITH_EXCEPTION
 * REVIEWED_WITH_EXCEPTION -> IN_PROGRESS (correction opens)
 * REVIEWED_WITH_EXCEPTION -> REVIEWED (all exceptions resolve)
 * REVIEWED -> IN_PROGRESS (explicit reopen only — distinct from the
 * correction-opened edge above; a reviewed system never silently reverts
 * to in_progress as a side effect of any other action)
 */
export const REVIEW_STATE_TRANSITIONS: readonly ReviewStateTransition[] = [
  { from: "not_reviewed", to: "in_progress", trigger: "review_started" },
  { from: "in_progress", to: "reviewed", trigger: "review_completed_no_exceptions" },
  { from: "in_progress", to: "reviewed_with_exception", trigger: "review_completed_with_open_exceptions" },
  { from: "reviewed", to: "reviewed_with_exception", trigger: "new_exception_raised" },
  { from: "reviewed", to: "in_progress", trigger: "explicit_reopen" },
  { from: "reviewed_with_exception", to: "in_progress", trigger: "correction_opened" },
  { from: "reviewed_with_exception", to: "reviewed", trigger: "all_exceptions_resolved" },
];

/** Whether a direct transition from `from` to `to` is defined in the graph above. */
export function canTransition(from: SystemReviewState, to: SystemReviewState): boolean {
  return REVIEW_STATE_TRANSITIONS.some((edge) => edge.from === from && edge.to === to);
}

/**
 * Computes the next review state after a review is completed/updated, given
 * whether any exceptions remain open. This is the single place that decides
 * REVIEWED vs. REVIEWED_WITH_EXCEPTION so no call site can independently
 * invent a "reviewed" result while exceptions are open.
 */
export function nextReviewStateAfterReview(
  current: SystemReviewState,
  hasOpenExceptions: boolean,
): SystemReviewState {
  if (current === "not_reviewed") {
    // A review cannot complete directly from not_reviewed; it must pass
    // through in_progress first.
    return "in_progress";
  }
  if (hasOpenExceptions) {
    return "reviewed_with_exception";
  }
  return "reviewed";
}

/** Opens a correction on a REVIEWED_WITH_EXCEPTION system, per the graph above. */
export function openCorrection(current: SystemReviewState): SystemReviewState {
  if (current !== "reviewed_with_exception") {
    throw new Error(
      `Cannot open a correction from review state "${current}"; corrections only open from "reviewed_with_exception".`,
    );
  }
  return "in_progress";
}

/**
 * Explicitly reopens a REVIEWED system back to IN_PROGRESS. Distinct from
 * `openCorrection`: this is the only path by which a plain "reviewed" state
 * (no open exceptions) returns to in_progress, and it must be an explicit
 * caller action — no other transition in the graph produces this edge as a
 * side effect.
 */
export function reopenReviewed(current: SystemReviewState): SystemReviewState {
  if (current !== "reviewed") {
    throw new Error(`Cannot explicitly reopen from review state "${current}"; explicit reopen only applies from "reviewed".`);
  }
  return "in_progress";
}

// ---------------------------------------------------------------------------
// Situation branches (section 7, "Situation branches")
// ---------------------------------------------------------------------------

export interface SituationRequirement {
  situation: AssessmentSituation;
  /** Named requirement keys a caller must satisfy before the situation can be recorded as complete. */
  requires: readonly string[];
}

export const SITUATION_REQUIREMENTS: readonly SituationRequirement[] = [
  {
    situation: "no_current_concern",
    requires: ["current_review_evidence"],
  },
  {
    situation: "stable_existing",
    requires: ["current_confirmation", "dated_prior_reference"],
  },
  {
    situation: "new_or_worsening",
    requires: ["current_finding_or_change", "intervention_or_response", "follow_up_decision"],
  },
  {
    situation: "unable_to_assess",
    requires: [
      "scope",
      "reason",
      "assessed_portion_if_any",
      "follow_up_responsibility",
      "timing_or_contingency",
    ],
  },
];

export function getSituationRequirements(situation: AssessmentSituation): readonly string[] {
  const rule = SITUATION_REQUIREMENTS.find((entry) => entry.situation === situation);
  if (!rule) {
    throw new Error(`Unknown assessment situation: "${situation}"`);
  }
  return rule.requires;
}

/**
 * Given the requirement keys actually satisfied so far, returns the keys
 * still missing for `situation`. An empty result means the situation's
 * branch requirements are fully satisfied.
 */
export function getMissingSituationRequirements(
  situation: AssessmentSituation,
  satisfiedKeys: readonly string[],
): string[] {
  const satisfied = new Set(satisfiedKeys);
  return getSituationRequirements(situation).filter((key) => !satisfied.has(key));
}

/**
 * Invariant guard: "Unable to assess" must never be converted to normal,
 * reviewed without limitation, or fully assessed. Returns false whenever a
 * caller attempts to treat an `unable_to_assess` situation as fully
 * satisfied without every one of its required keys present — there is no
 * situation-specific shortcut that reduces this requirement list.
 */
export function unableToAssessIsFullyDocumented(satisfiedKeys: readonly string[]): boolean {
  return getMissingSituationRequirements("unable_to_assess", satisfiedKeys).length === 0;
}
