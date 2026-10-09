import { Badge } from "../../../components/ui/badge";
import type { SystemReviewState } from "../../../domain/body-systems";

/**
 * Canonical display label for each of the four `SystemReviewState` values.
 * No new states or wording are introduced here — these are presentation
 * labels for the exact canonical enum values only.
 */
const REVIEW_STATE_LABELS: Record<SystemReviewState, string> = {
  not_reviewed: "Not reviewed",
  in_progress: "In progress",
  reviewed: "Reviewed",
  reviewed_with_exception: "Reviewed with exception",
};

/**
 * Badge color variant per review state. Status is never conveyed by color
 * alone: the canonical text label above is always rendered alongside it.
 */
const REVIEW_STATE_BADGE_VARIANT: Record<SystemReviewState, "neutral" | "success" | "warning"> = {
  not_reviewed: "neutral",
  in_progress: "neutral",
  reviewed: "success",
  reviewed_with_exception: "warning",
};

export interface ReviewStateBadgeProps {
  reviewState: SystemReviewState;
}

/** Renders only the review-state badge — never a situation value. */
export function ReviewStateBadge({ reviewState }: ReviewStateBadgeProps) {
  return <Badge variant={REVIEW_STATE_BADGE_VARIANT[reviewState]}>{REVIEW_STATE_LABELS[reviewState]}</Badge>;
}
