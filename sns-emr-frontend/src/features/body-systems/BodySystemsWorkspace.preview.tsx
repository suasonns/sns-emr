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
 * `patientId` is an obviously-synthetic placeholder UUID — this preview
 * has no real patient context. Selecting Respiratory will call the real
 * Respiratory API with this id; a dev environment with no matching
 * patient record will correctly show the panel's "unavailable" or
 * "unauthorized" state rather than fabricated data.
 */
export function BodySystemsWorkspacePreview() {
  return (
    <BodySystemsWorkspace
      fixture={syntheticComprehensiveAssessmentFixture}
      patientId="00000000-0000-0000-0000-000000000000"
    />
  );
}
