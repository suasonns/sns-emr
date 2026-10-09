/**
 * SNS Body Systems Workspace — single row in the always-visible, fixed-order
 * ten-system registry. Never reordered, never filtered, never
 * diagnosis-driven — the registry always renders every BODY_SYSTEMS entry
 * via this component, in BODY_SYSTEMS order (see BodyShieldShell).
 */
import * as React from "react";
import { AlertTriangle, Circle, CircleDot, CheckCircle2 } from "lucide-react";
import { cn } from "../../../lib/utils";
import { BODY_SYSTEM_LABELS, type BodySystemCode, type SystemReviewState } from "../../../domain/body-systems";

export interface SystemRegisterRowProps {
  system: BodySystemCode;
  reviewState: SystemReviewState;
  exceptionCount: number;
  isSelected: boolean;
  isPilotImplemented: boolean;
  onSelect: (system: BodySystemCode) => void;
  /** "rail" = vertical desktop sidebar row; "strip" = horizontal mobile chip. */
  layout?: "rail" | "strip";
}

const REVIEW_STATE_ICON: Record<SystemReviewState, React.ComponentType<{ className?: string }>> = {
  not_reviewed: Circle,
  in_progress: CircleDot,
  reviewed: CheckCircle2,
  reviewed_with_exception: AlertTriangle,
};

const REVIEW_STATE_LABEL: Record<SystemReviewState, string> = {
  not_reviewed: "Not reviewed",
  in_progress: "In progress",
  reviewed: "Reviewed",
  reviewed_with_exception: "Reviewed with exception",
};

export function SystemRegisterRow({
  system,
  reviewState,
  exceptionCount,
  isSelected,
  isPilotImplemented,
  onSelect,
  layout = "rail",
}: SystemRegisterRowProps) {
  const Icon = REVIEW_STATE_ICON[reviewState];
  const label = BODY_SYSTEM_LABELS[system];

  return (
    <button
      type="button"
      onClick={() => onSelect(system)}
      aria-current={isSelected ? "true" : undefined}
      title={`${label} — ${REVIEW_STATE_LABEL[reviewState]}${exceptionCount > 0 ? `, ${exceptionCount} open exception(s)` : ""}`}
      className={cn(
        "flex items-center gap-2 rounded-lg border border-transparent text-left text-[12px] font-medium transition-colors",
        layout === "rail" ? "w-full px-3 py-2" : "shrink-0 px-3 py-1.5 whitespace-nowrap",
        isSelected
          ? "border-rnica-teal bg-rnica-tealSoftBg text-rnica-teal"
          : "text-rnica-text hover:bg-rnica-hoverSurface",
      )}
    >
      <Icon
        className={cn(
          "h-3.5 w-3.5 shrink-0",
          reviewState === "reviewed" && "text-rnica-green",
          reviewState === "reviewed_with_exception" && "text-rnica-orange",
          reviewState === "not_reviewed" && "text-rnica-muted",
          reviewState === "in_progress" && "text-rnica-teal",
        )}
      />
      <span className="flex-1 truncate">{label}</span>
      {!isPilotImplemented && (
        <span className="shrink-0 rounded px-1 text-[9px] uppercase tracking-wide text-rnica-muted">Phase 2</span>
      )}
      {exceptionCount > 0 && (
        <span className="shrink-0 rounded-full bg-rnica-criticalBg px-1.5 text-[10px] font-bold text-rnica-red">
          {exceptionCount}
        </span>
      )}
    </button>
  );
}
