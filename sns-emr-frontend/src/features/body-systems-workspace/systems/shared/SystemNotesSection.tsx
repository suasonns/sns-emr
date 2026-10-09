/**
 * SNS Body Systems Workspace — shared "RN Notes" (optional clinical notes)
 * section.
 *
 * Source of truth: the SNS Clinical Notes / Documentation-Clarity Standard
 * (product-owner decision). Establishes the forward-going SNS pattern:
 * every clinical system should provide an optional narrative-context field,
 * placed after all structured findings and before Unable-to-Assess/final
 * completion controls. The CAPABILITY is required; an individual ENTRY is
 * always optional.
 *
 * RN Notes:
 * - supplement structured documentation; they never replace it.
 * - are dated supporting narrative evidence that may participate in
 *   Current/Historical review as context (see `historicalEvidenceDoesNotCompleteCurrentReview`
 *   in `domain/body-systems/ownership.ts` — the same "evidence never
 *   auto-completes current review" rule applies to notes).
 * - never satisfy a required structured finding, never complete a system
 *   review by themselves, and never close a Review By Exception item by
 *   themselves (see `systemNotesDoNotSatisfyStructuredFindings` in
 *   ownership.ts).
 * - are never required — a blank note is valid and must never be shown as
 *   an incomplete/error state (see `systemNotesAreOptional`).
 *
 * This component is created once, here, and reused by every system that
 * adopts the standard (Infection first) rather than each panel
 * implementing its own ad hoc notes textarea. Retrofitting the four
 * already-accepted systems whose existing mid-form "status notes" field
 * predates this shared component is explicitly out of scope for this
 * change (incremental adoption, per product-owner direction) — it is left
 * for a separate, dedicated retrofit plan.
 */
import { Textarea } from "../../../../components/ui/textarea";

export interface SystemNotesSectionProps {
  /** Stable id so the label/helper text/textarea are correctly associated for assistive technology. */
  id: string;
  /** Clinician-facing label. Defaults to "RN Notes". */
  label?: string;
  /** Current note value. Undefined/empty is valid — notes are always optional. */
  value: string | undefined;
  onChange: (value: string) => void;
}

/**
 * Optional narrative-context field. Renders a labeled, accessible textarea
 * with explicit "optional" helper text — never styled or labeled as
 * required, and never shown as incomplete when blank.
 */
export function SystemNotesSection({ id, label = "RN Notes", value, onChange }: SystemNotesSectionProps) {
  const helperId = `${id}-helper`;
  return (
    <div className="flex flex-col gap-1.5">
      <label htmlFor={id} className="text-[11px] font-medium text-rnica-muted">
        {label}
      </label>
      <p id={helperId} className="text-[11px] text-rnica-muted">
        Optional. Add context or explain the clinical reasoning behind selected findings when helpful.
      </p>
      <Textarea
        id={id}
        aria-describedby={helperId}
        placeholder="Optional clinical context or explanation"
        value={value ?? ""}
        onChange={(e) => onChange(e.target.value)}
      />
    </div>
  );
}
