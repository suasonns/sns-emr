import { AccordionItem, AccordionTrigger, AccordionContent } from "../../../components/ui/accordion";
import { BODY_SYSTEM_LABELS } from "../../../domain/body-systems";
import { ReviewStateBadge } from "./ReviewStateBadge";
import type { SyntheticSystemRow } from "../types/presentation";

export interface BodySystemRegisterRowProps {
  row: SyntheticSystemRow;
}

/**
 * One expandable register row.
 *
 * Narrowed-shell foundation: expanding any of the ten systems reveals only
 * a fixed, neutral, read-only placeholder line — no clinical-detail panel,
 * assessment-situation presentation, review exception content, editing,
 * persistence, or API access.
 *
 * Respiratory's former proof-of-pattern expansion (a real, API-backed
 * `RespiratoryPanel` for this one system) was retired per product-
 * authority direction to collapse Respiratory back onto the same
 * plain-register model as every other system — this preview harness no
 * longer special-cases any system.
 */
export function BodySystemRegisterRow({ row }: BodySystemRegisterRowProps) {
  return (
    <AccordionItem value={row.system}>
      <AccordionTrigger>
        <span className="flex flex-1 items-center justify-between gap-2 pr-2 text-left">
          <span className="text-sm font-semibold text-rnica-textStrong">{BODY_SYSTEM_LABELS[row.system]}</span>
          <ReviewStateBadge reviewState={row.reviewState} />
        </span>
      </AccordionTrigger>
      <AccordionContent>
        <p className="text-xs text-rnica-muted">Read-only synthetic register preview</p>
      </AccordionContent>
    </AccordionItem>
  );
}
