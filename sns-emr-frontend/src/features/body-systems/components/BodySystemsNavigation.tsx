import type { BodySystemCode } from "../../../domain/body-systems";
import { BodySystemNavigationItem } from "./BodySystemNavigationItem";
import type { SyntheticSystemRow } from "../types/presentation";

export interface BodySystemsNavigationProps {
  rows: readonly SyntheticSystemRow[];
  selectedSystem: BodySystemCode | null;
  onSelectSystem: (system: BodySystemCode) => void;
}

/**
 * Single navigation list, in the canonical fixed system order, reused for
 * both the desktop persistent rail and the mobile system-jump list via
 * responsive layout classes only (`flex-col` at the `lg` breakpoint). This
 * avoids rendering the same accessible system list twice in the DOM.
 */
export function BodySystemsNavigation({ rows, selectedSystem, onSelectSystem }: BodySystemsNavigationProps) {
  return (
    <nav aria-label="Body systems">
      <ul className="flex gap-2 overflow-x-auto pb-1 lg:flex-col lg:overflow-visible lg:pb-0">
        {rows.map((row) => (
          <li key={row.system}>
            <BodySystemNavigationItem
              row={row}
              isSelected={row.system === selectedSystem}
              onSelect={() => onSelectSystem(row.system)}
            />
          </li>
        ))}
      </ul>
    </nav>
  );
}
