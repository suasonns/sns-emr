import { Progress } from "../../../components/ui/progress";
import { calculateReviewProgress, calculateReviewStateCounts } from "../selectors/reviewProgress";
import type { SyntheticSystemRow } from "../types/presentation";

export interface BodySystemsProgressProps {
  rows: readonly SyntheticSystemRow[];
}

/**
 * Displays review progress derived exclusively from each row's
 * `reviewState` — never from summary text, exception counts, or
 * expanded/collapsed UI state. Label is fixed to "Review progress" (never
 * "Assessment complete", "Compliant", or similar). The four canonical
 * review states are always shown as separate, readable counts — the
 * optional progress bar is a presentation summary only and never replaces
 * those separate counts.
 */
export function BodySystemsProgress({ rows }: BodySystemsProgressProps) {
  const { reviewedCount, totalCount } = calculateReviewProgress(rows);
  const stateCounts = calculateReviewStateCounts(rows);
  const percent = totalCount === 0 ? 0 : Math.round((reviewedCount / totalCount) * 100);

  return (
    <div className="flex flex-col gap-1.5" data-testid="body-systems-progress">
      <div className="flex items-center justify-between text-xs">
        <span className="font-medium text-rnica-dim">Review progress</span>
      </div>
      <Progress value={percent} aria-label="Review progress" />
      <ul className="flex flex-wrap gap-x-4 gap-y-1 text-xs text-rnica-muted">
        <li>Reviewed: {stateCounts.reviewed}</li>
        <li>Reviewed with exception: {stateCounts.reviewed_with_exception}</li>
        <li>In progress: {stateCounts.in_progress}</li>
        <li>Not reviewed: {stateCounts.not_reviewed}</li>
      </ul>
    </div>
  );
}
