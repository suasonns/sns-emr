import { BodySystemsWorkspace } from "./components/BodySystemsWorkspace";
import { syntheticComprehensiveAssessmentFixture } from "./fixtures/comprehensiveAssessment.fixture";

/**
 * Unrouted preview entry point for the Body Systems workspace shell,
 * following the same pattern as the existing
 * `BodySystemShellCardiovascularDemo` precedent in
 * `src/components/rn-ica/BodySystemShell.jsx`: exported for direct import
 * by tests (and the safe dev-only preview route in App.tsx), but not
 * wired into any production navigation.
 *
 * Respiratory's former proof-of-pattern expansion (a real, API-backed
 * detail panel for this one system) was retired per product-authority
 * direction to collapse Respiratory back onto the same plain-register
 * model as the other nine systems — this preview is now purely
 * presentation-only/read-only for all ten, driven entirely by the
 * synthetic fixture, with no network calls.
 */
export function BodySystemsWorkspacePreview() {
  return <BodySystemsWorkspace fixture={syntheticComprehensiveAssessmentFixture} />;
}
