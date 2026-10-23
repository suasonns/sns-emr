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
 *
 * PRODUCT-OWNER DIRECTIVE ("Standardize SNS Documentation Coverage",
 * 2026-10-13): measured computed styles showed Neuro and Respiratory
 * items rendering at different `line-height` (14.85px vs 20px) purely
 * from incidental ambient inheritance (no explicit `leading-*` here
 * previously), and the `<ul>`/`<li>` picked up the browser's default
 * disc bullet + 40px indent + 1em vertical margin because Tailwind
 * preflight is disabled project-wide. Fixed by explicitly pinning
 * `leading-[1.35]` (Neuro's approved line-height, matching the
 * `--rnica-h2-line` token) on every item and resetting the list box
 * (`list-none`, zero margin/padding) here, in the one shared component,
 * so neither Body System's surrounding container can change Coverage
 * typography/spacing by accident.
 */
// PRODUCT OWNER DIRECTIVE (2026-12-?) "Final Integumentary Closeout"
// Section 3/4 -- the original design only had two states (complete/
// incomplete), which collapsed genuinely different situations (a real
// gap vs. a non-blocking deferred item vs. a field that is simply not
// applicable to this patient) into the same green checkmark, producing
// nonsensical renders like "✓ Pending" or "✓ Not Applicable". `state` is
// an OPTIONAL, additive discriminator; every existing caller (Neuro,
// Cardiovascular, Respiratory, Musculoskeletal, GI, Nutrition,
// Endocrine, GU, Infection) never sets it, so they fall back to the
// exact original two-state boolean behavior below -- byte-identical
// badge/icon/color for every pre-existing item.
export type DocumentationCoverageState =
  | "complete"
  | "action_required"
  | "pending_non_blocking"
  | "not_applicable"
  | "error";

export interface DocumentationCoverageItem {
  key: string;
  label: string;
  complete: boolean;
  /**
   * Optional 5-state discriminator. Omit to keep the original
   * complete/action_required-only behavior. When present, overrides the
   * badge color/icon independently of `complete` (e.g. a non-blocking
   * "Pending" item can report `complete: true` for gating purposes while
   * still rendering as a neutral, non-checkmarked badge).
   */
  state?: DocumentationCoverageState;
  /** The documented value, already formatted for display. Ignored when the effective state is `action_required` or `error` (unless no `unresolvedHint` is given). */
  value?: string | null;
  /** The exact unresolved requirement. Ignored when the effective state is `complete`, `pending_non_blocking`, or `not_applicable`. */
  unresolvedHint?: string | null;
  // PRODUCT OWNER DIRECTIVE (2026-10-16) "Musculoskeletal Information
  // Architecture Pass" -- optional, purely-visual sub-heading key (e.g.
  // "Movement", "Functional Impact"). Fully backward-compatible: when no
  // item in `items` sets `group`, rendering is byte-identical to the
  // original flat badge row (every other Body System's Coverage card is
  // unaffected). When at least one item sets `group`, items are chunked
  // into labeled clusters in first-seen-group order, with any ungrouped
  // items trailing in their own unlabeled row -- same Badge markup/
  // styling either way, only the wrapping/heading changes.
  group?: string | null;
}

export interface DocumentationCoverageProps {
  /** e.g. "Respiratory Documentation Coverage". */
  title: string;
  items: DocumentationCoverageItem[];
  className?: string;
  "data-testid"?: string;
}

// One mapping, reused by every item: effective `state` (falling back to
// the original complete/incomplete boolean when a caller doesn't set
// `state`) -> Badge variant + leading icon. `showValue` decides whether
// the badge reads `value` (resolved states) or `unresolvedHint` (states
// that still need RN action).
const COVERAGE_STATE_CONFIG: Record<
  DocumentationCoverageState,
  { variant: "success" | "warning" | "neutral" | "critical"; icon: string; showValue: boolean }
> = {
  complete: { variant: "success", icon: "✓ ", showValue: true },
  action_required: { variant: "warning", icon: "⚠ ", showValue: false },
  pending_non_blocking: { variant: "neutral", icon: "", showValue: true },
  not_applicable: { variant: "neutral", icon: "", showValue: true },
  error: { variant: "critical", icon: "⚠ ", showValue: false },
};

export function DocumentationCoverage({ title, items, className, ...rest }: DocumentationCoverageProps) {
  const hasGroups = items.some((item) => Boolean(item.group));
  const renderBadge = (item: DocumentationCoverageItem) => {
    const state: DocumentationCoverageState = item.state ?? (item.complete ? "complete" : "action_required");
    const { variant, icon, showValue } = COVERAGE_STATE_CONFIG[state];
    const text = showValue ? item.value : (item.unresolvedHint ?? item.value);
    return (
      <li key={item.key} className="list-none">
        <Badge
          variant={variant}
          className="normal-case tracking-normal text-[11px] font-normal leading-[1.35]"
        >
          <span className="font-semibold">{item.label}:</span>
          <span>
            {icon}
            {text}
          </span>
        </Badge>
      </li>
    );
  };
  // Chunk into first-seen-group order; items with no `group` are
  // collected into a trailing, unlabeled cluster so they still render
  // (never silently dropped).
  const groupedClusters: { label: string | null; items: DocumentationCoverageItem[] }[] = [];
  if (hasGroups) {
    const byLabel = new Map<string | null, DocumentationCoverageItem[]>();
    for (const item of items) {
      const label = item.group || null;
      if (!byLabel.has(label)) byLabel.set(label, []);
      byLabel.get(label)!.push(item);
    }
    for (const [label, groupItems] of byLabel) {
      if (label != null) groupedClusters.push({ label, items: groupItems });
    }
    const ungrouped = byLabel.get(null);
    if (ungrouped && ungrouped.length > 0) groupedClusters.push({ label: null, items: ungrouped });
  }
  return (
    <section
      className={cn("flex flex-col gap-1.5 rounded-lg border border-rnica-border bg-rnica-bg px-3 py-2", className)}
      aria-label={title}
      data-testid={rest["data-testid"]}
    >
      <h3 className="text-xs font-semibold uppercase text-rnica-muted">{title}</h3>
      {items.length === 0 ? (
        <p className="text-xs text-rnica-muted">No applicable documentation items.</p>
      ) : hasGroups ? (
        <div className="flex flex-col gap-1.5">
          {groupedClusters.map((cluster, ci) => (
            <div key={cluster.label ?? `__ungrouped-${ci}`} className="flex flex-col gap-1">
              {cluster.label && (
                <span className="text-[10px] font-semibold uppercase tracking-wide text-rnica-muted/80">
                  {cluster.label}
                </span>
              )}
              <ul className="m-0 flex list-none flex-wrap gap-1.5 p-0">
                {cluster.items.map((item) => renderBadge(item))}
              </ul>
            </div>
          ))}
        </div>
      ) : (
        <ul className="m-0 flex list-none flex-wrap gap-1.5 p-0">
          {items.map((item) => renderBadge(item))}
        </ul>
      )}
    </section>
  );
}
