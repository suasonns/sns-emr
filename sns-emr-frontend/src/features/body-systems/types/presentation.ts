/**
 * SNS Body Systems — read-only register-shell presentation types.
 *
 * Narrowed to the approved first-shell scope: synthetic assessment
 * identity, visit-mode display, canonical system navigation, and
 * register-row review state. Clinical-detail, assessment-situation, and
 * review-exception presentation types are deferred to a later milestone
 * and intentionally not declared here.
 *
 * These types do not redeclare canonical domain identifiers, enums, or
 * business rules — `BodySystemCode`, `SystemReviewState`, and `VisitMode`
 * are imported from the domain barrel and reused directly.
 */
import type { BodySystemCode, SystemReviewState, VisitMode } from "../../../domain/body-systems";

/**
 * One synthetic, read-only register row within the fixture: a canonical
 * system paired with its current review state only.
 */
export interface SyntheticSystemRow {
  system: BodySystemCode;
  reviewState: SystemReviewState;
}

/**
 * The full synthetic, read-only fixture consumed by this workspace shell.
 * Every identifier in this type is obviously synthetic (see
 * `fixtures/comprehensiveAssessment.fixture.ts`) and must never be
 * confused with a production `BodySystemsAssessment` record.
 */
export interface SyntheticComprehensiveAssessmentFixture {
  id: string;
  patientDisplayName: string;
  visitLabel: string;
  observedAt: string;
  visitMode: VisitMode;
  systems: readonly SyntheticSystemRow[];
}
