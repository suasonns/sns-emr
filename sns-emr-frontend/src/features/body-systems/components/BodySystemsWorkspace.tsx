import { useState } from "react";
import type { BodySystemCode } from "../../../domain/body-systems";
import type { SyntheticComprehensiveAssessmentFixture } from "../types/presentation";
import { BodySystemsHeader } from "./BodySystemsHeader";
import { BodySystemsProgress } from "./BodySystemsProgress";
import { BodySystemsNavigation } from "./BodySystemsNavigation";
import { BodySystemsRegister } from "./BodySystemsRegister";

export interface BodySystemsWorkspaceProps {
  fixture: SyntheticComprehensiveAssessmentFixture;
  /**
   * Real patient identifier used only for the Respiratory API wiring (see
   * `RespiratoryPanel.tsx`). The other nine systems never use this value —
   * they remain register-only and make no network calls.
   */
  patientId: string;
}

/**
 * "Initial Comprehensive RN Assessment" Body Systems register shell.
 *
 * Completed narrowed-shell foundation: the ten-system register, canonical
 * navigation, review-state badges, and review-progress counts remain
 * presentation-only and read-only, driven entirely by the caller-supplied
 * synthetic fixture — no editing, persistence, API, AI, or RNICA
 * integration for nine of the ten systems.
 *
 * Respiratory proof-of-pattern expansion (explicit product-authority
 * decision — see `RespiratoryPanel.tsx`): selecting and expanding
 * Respiratory renders a real, editable detail panel wired to the
 * Respiratory API (`src/api/bodySystems.ts`) for `patientId`, with load,
 * save, review-exception, and optimistic-concurrency-conflict handling.
 * Every other system's register row still renders only the fixed,
 * neutral, read-only placeholder — this expansion does not generalize to
 * the remaining nine systems and does not change canonical identifiers,
 * labels, or ordering.
 */
export function BodySystemsWorkspace({ fixture, patientId }: BodySystemsWorkspaceProps) {
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
            patientId={patientId}
          />
        </div>
      </div>
    </div>
  );
}
