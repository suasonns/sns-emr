import { Badge } from "./badge";
import { cn } from "../../lib/utils";

/**
 * SNS Documentation Coverage — shared ADR-004 component.
 *
 * Reference: `docs/architecture/decision-records/ADR-004-sns-documentation-coverage.md`.
 * One Coverage design, one behavior, frozen and reused across every Body
 * System (Neurological, Respiratory, and future systems); only the
 * `items` content varies. Renders in the Tailwind/shadcn idiom (`Badge`,
 * `cn`) rather than global CSS classes. Both Neurological (`RNICA.jsx`)
 * and Respiratory (`RespiratoryPanel.tsx`) render through this single
 * component — Neuro's former inline `.rnica-documentation-coverage*`
 * markup/CSS is retired (see `RNICACommandWorkspace.css`).
 *
 * Read-only: Information Display only (SNS Design System §10). Never a
 * second entry point for editing a field, and never displays a retired
 * field — callers must exclude retired fields from `items` themselves.
 */
export interface DocumentationCoverageItem {
  key: string;
  label: string;
  complete: boolean;
  /** The documented value, already formatted for display. Ignored when `complete` is false. */
  value?: string | null;
  /** The exact unresolved requirement. Ignored when `complete` is true. */
  unresolvedHint?: string | null;
}

export interface DocumentationCoverageProps {
  /** e.g. "Respiratory Documentation Coverage". */
  title: string;
  items: DocumentationCoverageItem[];
  className?: string;
  "data-testid"?: string;
}

export function DocumentationCoverage({ title, items, className, ...rest }: DocumentationCoverageProps) {
  return (
    <section
      className={cn("flex flex-col gap-1.5 rounded-lg border border-rnica-border bg-rnica-bg px-3 py-2", className)}
      aria-label={title}
      data-testid={rest["data-testid"]}
    >
      <h3 className="text-xs font-semibold uppercase text-rnica-muted">{title}</h3>
      {items.length === 0 ? (
        <p className="text-xs text-rnica-muted">No applicable documentation items.</p>
      ) : (
        <ul className="flex flex-wrap gap-1.5">
          {items.map((item) => (
            <li key={item.key}>
              <Badge
                variant={item.complete ? "success" : "warning"}
                className="normal-case tracking-normal text-[11px] font-normal"
              >
                <span className="font-semibold">{item.label}:</span>
                <span>
                  {item.complete ? "✓ " : "⚠ "}
                  {item.complete ? item.value : item.unresolvedHint}
                </span>
              </Badge>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
