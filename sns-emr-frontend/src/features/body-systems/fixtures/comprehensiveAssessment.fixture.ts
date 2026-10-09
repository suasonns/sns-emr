/**
 * SNS Body Systems — synthetic read-only register-shell fixture.
 *
 * SYNTHETIC DEMONSTRATION DATA ONLY.
 *
 * Narrowed to the approved first-shell scope: this fixture carries only a
 * review state per canonical system — no assessment situations, review
 * exceptions, clinical narratives, evidence, interventions, follow-up,
 * limitations, or historical references. Every value here is fictional
 * and exists solely to drive the read-only register-shell preview and its
 * tests. This fixture is intentionally kept outside the canonical domain
 * barrel (`src/domain/body-systems/`) — it must never be imported from
 * that folder, and the domain layer must never import from here.
 *
 * `patientDisplayName` and `id` are deliberately obvious placeholders so
 * this can never be mistaken for a production assessment if it is ever
 * logged, screenshotted, or inspected.
 */
import { BODY_SYSTEMS } from "../../../domain/body-systems";
import type { SyntheticComprehensiveAssessmentFixture, SyntheticSystemRow } from "../types/presentation";

/**
 * Synthetic per-system review states, in the canonical fixed system order
 * from `BODY_SYSTEMS`. Chosen to exercise every canonical
 * `SystemReviewState` at least once for test coverage — not derived from
 * the Figma reference screenshots' sample content.
 */
const syntheticSystemRows: readonly SyntheticSystemRow[] = [
  { system: "neurological", reviewState: "reviewed" },
  { system: "respiratory", reviewState: "reviewed" },
  { system: "cardiovascular", reviewState: "reviewed_with_exception" },
  { system: "nutrition", reviewState: "in_progress" },
  { system: "gastrointestinal", reviewState: "not_reviewed" },
  { system: "genitourinary", reviewState: "reviewed" },
  { system: "musculoskeletal", reviewState: "reviewed" },
  { system: "integumentary", reviewState: "reviewed_with_exception" },
  { system: "infection_immunological", reviewState: "reviewed" },
  { system: "endocrine", reviewState: "not_reviewed" },
];

if (syntheticSystemRows.length !== BODY_SYSTEMS.length) {
  throw new Error(
    "syntheticComprehensiveAssessmentFixture must describe exactly the ten canonical body systems."
  );
}

/**
 * The synthetic, read-only fixture consumed by `BodySystemsWorkspace`. Not
 * connected to a patient record, an API, or persistence of any kind.
 */
export const syntheticComprehensiveAssessmentFixture: SyntheticComprehensiveAssessmentFixture = {
  id: "synthetic-body-systems-assessment",
  patientDisplayName: "Fictional Demo Patient",
  visitLabel: "Initial Comprehensive RN Assessment (synthetic)",
  observedAt: "2026-10-14T09:00:00.000Z",
  visitMode: "admission_comprehensive",
  systems: syntheticSystemRows,
};
