import { AccordionItem, AccordionTrigger, AccordionContent } from "../../../components/ui/accordion";
import { BODY_SYSTEM_LABELS } from "../../../domain/body-systems";
import { ReviewStateBadge } from "./ReviewStateBadge";
import { RespiratoryPanel } from "./RespiratoryPanel";
import type { SyntheticSystemRow } from "../types/presentation";

export interface BodySystemRegisterRowProps {
  row: SyntheticSystemRow;
  /** Only consumed when `row.system === "respiratory"`. */
  patientId: string;
}

/**
 * One expandable register row.
 *
 * Narrowed-shell foundation (unchanged): expanding any of the other nine
 * systems reveals only a fixed, neutral, read-only placeholder line — no
 * clinical-detail panel, assessment-situation presentation, review
 * exception content, editing, persistence, or API access.
 *
 * Respiratory proof-of-pattern expansion (explicit product-authority
 * decision — see `BodySystemsWorkspace.tsx` docstring): Respiratory's row
 * renders the real, editable `RespiratoryPanel` instead, wired to the
 * Respiratory API for `patientId`. No other system may render that panel
 * or call that API.
 */
export function BodySystemRegisterRow({ row, patientId }: BodySystemRegisterRowProps) {
  return (
    <AccordionItem value={row.system}>
      <AccordionTrigger>
        <span className="flex flex-1 items-center justify-between gap-2 pr-2 text-left">
          <span className="text-sm font-semibold text-rnica-textStrong">{BODY_SYSTEM_LABELS[row.system]}</span>
          <ReviewStateBadge reviewState={row.reviewState} />
        </span>
      </AccordionTrigger>
      <AccordionContent>
        {row.system === "respiratory" ? (
          <RespiratoryPanel patientId={patientId} />
        ) : (
          <p className="text-xs text-rnica-muted">Read-only synthetic register preview</p>
        )}
      </AccordionContent>
    </AccordionItem>
  );
}
