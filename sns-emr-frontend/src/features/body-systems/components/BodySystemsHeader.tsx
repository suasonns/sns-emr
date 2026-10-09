import type { SyntheticComprehensiveAssessmentFixture } from "../types/presentation";
import { SyntheticDataNotice } from "./SyntheticDataNotice";
import { VisitModeDisplay } from "./VisitModeDisplay";

export interface BodySystemsHeaderProps {
  fixture: SyntheticComprehensiveAssessmentFixture;
}

/**
 * Visit-context header: visit label, synthetic patient display name, visit
 * mode, and the always-visible synthetic-data notice. Read-only — no
 * editable field is rendered here.
 */
export function BodySystemsHeader({ fixture }: BodySystemsHeaderProps) {
  return (
    <header className="flex flex-col gap-3 border-b border-rnica-border pb-4">
      <div className="flex flex-col gap-1">
        <h1 className="text-lg font-semibold text-rnica-textStrong">Body Systems</h1>
        <p className="text-xs text-rnica-muted">
          {fixture.visitLabel} &middot; {fixture.patientDisplayName}
        </p>
      </div>
      <VisitModeDisplay activeMode={fixture.visitMode} />
      <SyntheticDataNotice />
    </header>
  );
}
