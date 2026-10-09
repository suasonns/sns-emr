import type { BodySystemCode } from "../../../domain/body-systems";
import { Accordion } from "../../../components/ui/accordion";
import { BodySystemRegisterRow } from "./BodySystemRegisterRow";
import type { SyntheticSystemRow } from "../types/presentation";

export interface BodySystemsRegisterProps {
  rows: readonly SyntheticSystemRow[];
  expandedSystem: BodySystemCode | null;
  onExpandedSystemChange: (system: BodySystemCode | null) => void;
  /** Threaded through to the Respiratory row only — see `BodySystemRegisterRow.tsx`. */
  patientId: string;
}

/**
 * Register of all ten systems, in the canonical fixed order from the
 * fixture. A single row may be expanded at a time (`type="single"`),
 * matching the governing task's "one expanded system at a time" mobile
 * requirement — kept as the single behavior for both desktop and mobile
 * rather than two different interaction models.
 */
export function BodySystemsRegister({ rows, expandedSystem, onExpandedSystemChange, patientId }: BodySystemsRegisterProps) {
  return (
    <Accordion
      type="single"
      collapsible
      value={expandedSystem ?? ""}
      onValueChange={(value) => onExpandedSystemChange(value ? (value as BodySystemCode) : null)}
      aria-label="Body systems register"
      data-testid="body-systems-register"
    >
      {rows.map((row) => (
        <BodySystemRegisterRow key={row.system} row={row} patientId={patientId} />
      ))}
    </Accordion>
  );
}
