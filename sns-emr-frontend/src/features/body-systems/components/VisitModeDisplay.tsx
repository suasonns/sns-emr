import type { VisitMode } from "../../../domain/body-systems";
import { cn } from "../../../lib/utils";

const VISIT_MODE_LABELS: Record<VisitMode, string> = {
  admission_comprehensive: "Admission / Comprehensive",
  routine_rn: "Routine RN Visit",
  recertification: "Recertification",
};

export interface VisitModeDisplayProps {
  activeMode: VisitMode;
}

/**
 * Presents the three canonical visit modes. Only `activeMode` is shown as
 * selected/interactive; the other two are rendered as disabled,
 * noninteractive preview labels only — this milestone does not implement
 * mode switching, so no click handler or state change is wired to them.
 */
export function VisitModeDisplay({ activeMode }: VisitModeDisplayProps) {
  const modes: VisitMode[] = ["admission_comprehensive", "routine_rn", "recertification"];

  return (
    <div role="group" aria-label="Visit mode" className="flex flex-wrap gap-2">
      {modes.map((mode) => {
        const isActive = mode === activeMode;
        return (
          <span
            key={mode}
            aria-current={isActive ? "true" : undefined}
            aria-disabled={isActive ? undefined : "true"}
            className={cn(
              "rounded-md border px-2.5 py-1 text-[11px] font-medium",
              isActive
                ? "border-rnica-tealSoftBorder bg-rnica-tealSoftBg text-rnica-teal"
                : "border-rnica-border bg-rnica-bgAlt text-rnica-textDisabled"
            )}
          >
            {VISIT_MODE_LABELS[mode]}
            {!isActive && <span className="sr-only"> (not available in this preview)</span>}
          </span>
        );
      })}
    </div>
  );
}
