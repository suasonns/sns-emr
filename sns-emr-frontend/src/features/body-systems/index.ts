/**
 * SNS Body Systems — read-only workspace shell feature barrel.
 *
 * Public surface for this presentation-only milestone. Does not re-export
 * anything from `src/domain/body-systems/` — callers that need canonical
 * domain types/constants should import directly from that barrel.
 */
export { BodySystemsWorkspace } from "./components/BodySystemsWorkspace";
export { BodySystemsWorkspacePreview } from "./BodySystemsWorkspace.preview";
export { syntheticComprehensiveAssessmentFixture } from "./fixtures/comprehensiveAssessment.fixture";
export {
  calculateReviewProgress,
  countsTowardReviewProgress,
  calculateReviewStateCounts,
} from "./selectors/reviewProgress";
export type { ReviewProgress, ReviewStateCounts } from "./selectors/reviewProgress";
export type { SyntheticComprehensiveAssessmentFixture, SyntheticSystemRow } from "./types/presentation";
