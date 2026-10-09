import { ReviewStateBadge } from "./ReviewStateBadge";
import type { SyntheticSystemRow } from "../types/presentation";
import { BODY_SYSTEM_LABELS } from "../../../domain/body-systems";
import { cn } from "../../../lib/utils";

export interface BodySystemNavigationItemProps {
  row: SyntheticSystemRow;
  isSelected: boolean;
  onSelect: () => void;
}

/**
 * One real, focusable `<button>` per system. Native button semantics give
 * keyboard operability (Tab to focus, Enter/Space to activate) without any
 * additional keyboard-event wiring.
 */
export function BodySystemNavigationItem({ row, isSelected, onSelect }: BodySystemNavigationItemProps) {
  return (
    <button
      type="button"
      aria-current={isSelected ? "true" : undefined}
      onClick={onSelect}
      className={cn(
        "flex shrink-0 items-center gap-2 whitespace-nowrap rounded-md border px-3 py-2 text-left text-xs font-medium",
        "focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-rnica-focusRing",
        isSelected
          ? "border-rnica-borderSelected bg-rnica-selectedSurface text-rnica-textStrong"
          : "border-transparent bg-transparent text-rnica-muted hover:bg-rnica-hoverSurface"
      )}
    >
      <span>{BODY_SYSTEM_LABELS[row.system]}</span>
      <ReviewStateBadge reviewState={row.reviewState} />
    </button>
  );
}
