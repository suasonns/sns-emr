import { useState } from "react";
import type { BodySystemCode } from "../../../domain/body-systems";
import type { SyntheticComprehensiveAssessmentFixture } from "../types/presentation";
import { BodySystemsHeader } from "./BodySystemsHeader";
import { BodySystemsProgress } from "./BodySystemsProgress";
import { BodySystemsNavigation } from "./BodySystemsNavigation";
import { BodySystemsRegister } from "./BodySystemsRegister";

export interface BodySystemsWorkspaceProps {
  fixture: SyntheticComprehensiveAssessmentFixture;
}

/**
 * "Initial Comprehensive RN Assessment" Body Systems register shell.
 *
 * Narrowed-shell foundation: the ten-system register, canonical
 * navigation, review-state badges, and review-progress counts are
 * presentation-only and read-only, driven entirely by the caller-supplied
 * synthetic fixture — no editing, persistence, API, AI, or RNICA
 * integration for any of the ten systems.
 *
 * Respiratory's former proof-of-pattern expansion (a real, API-backed
 * detail panel wired to `src/api/bodySystems.ts`) was retired per
 * product-authority direction: Respiratory now behaves identically to the
 * other nine systems in production (plain `formData`-backed fields, no
 * separate persistence), so this dev-only preview no longer has a
 * one-off expansion case either — every row renders the fixed, neutral,
 * read-only placeholder.
 */
export function BodySystemsWorkspace({ fixture }: BodySystemsWorkspaceProps) {
  const [selectedSystem, setSelectedSystem] = useState<BodySystemCode | null>(null);

  return (
    <div className="flex flex-col gap-4" data-testid="body-systems-workspace">
      <BodySystemsHeader fixture={fixture} />

      <div className="flex flex-col gap-4 lg:flex-row">
        <div className="lg:w-64 lg:shrink-0">
          <BodySystemsNavigation
            rows={fixture.systems}
            selectedSystem={selectedSystem}
            onSelectSystem={setSelectedSystem}
          />
        </div>

        <div className="flex flex-1 flex-col gap-4">
          <BodySystemsProgress rows={fixture.systems} />

          <BodySystemsRegister
            rows={fixture.systems}
            expandedSystem={selectedSystem}
            onExpandedSystemChange={setSelectedSystem}
          />
        </div>
      </div>
    </div>
  );
}
