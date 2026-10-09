/**
 * SNS Body Systems — review-progress selector.
 *
 * Pure, presentation-agnostic calculation of "review progress" for the
 * read-only workspace shell. Per the governing specification: only
 * `"reviewed"` and `"reviewed_with_exception"` count toward progress.
 * `"in_progress"` and `"not_reviewed"` never count, regardless of any
 * summary text, exception count, expanded/collapsed state, or historical
 * evidence presence. This selector reads `reviewState` only — nothing else.
 */
import type { SystemReviewState } from "../../../domain/body-systems";

export interface ReviewProgress {
  reviewedCount: number;
  totalCount: number;
}

const COUNTS_TOWARD_PROGRESS: ReadonlySet<SystemReviewState> = new Set([
  "reviewed",
  "reviewed_with_exception",
]);

/**
 * Returns whether a single review state counts toward review progress.
 * Exported separately so callers (and tests) can assert the rule in
 * isolation from any aggregation logic.
 */
export function countsTowardReviewProgress(reviewState: SystemReviewState): boolean {
  return COUNTS_TOWARD_PROGRESS.has(reviewState);
}

/**
 * Computes `{ reviewedCount, totalCount }` from a list of systems' review
 * states only. Does not accept or inspect situation, summary text,
 * exception counts, or any other field — those are intentionally not part
 * of this selector's input type so they cannot silently influence the
 * result.
 */
export function calculateReviewProgress(
  rows: readonly { reviewState: SystemReviewState }[]
): ReviewProgress {
  const reviewedCount = rows.reduce(
    (count, row) => (countsTowardReviewProgress(row.reviewState) ? count + 1 : count),
    0
  );
  return { reviewedCount, totalCount: rows.length };
}

/** Separate, non-collapsed count per canonical `SystemReviewState`. */
export type ReviewStateCounts = Record<SystemReviewState, number>;

/**
 * Computes a distinct count per canonical review state. Per the governing
 * specification, these four counts must always be displayed separately —
 * never collapsed into a single clinical-completion percentage.
 */
export function calculateReviewStateCounts(
  rows: readonly { reviewState: SystemReviewState }[]
): ReviewStateCounts {
  const counts: ReviewStateCounts = {
    not_reviewed: 0,
    in_progress: 0,
    reviewed: 0,
    reviewed_with_exception: 0,
  };
  for (const row of rows) {
    counts[row.reviewState] += 1;
  }
  return counts;
}
