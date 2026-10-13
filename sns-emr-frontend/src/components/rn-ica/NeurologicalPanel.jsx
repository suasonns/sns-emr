import React from "react";

// PRODUCT-OWNER DIRECTIVE "NEURO-BASELINE-2026-10-12-V1" Phase 1
// ("Reorganize, not reduce") -- a dedicated, Respiratory-style compact
// two-column panel for the Neurological / Mental / Sensory body system,
// mirroring RespiratoryPanel.tsx's *visual* layout pattern only.
//
// Explicit product-owner decision (asked and confirmed before this file
// was written): this panel does NOT replicate RespiratoryPanel's separate
// backend-API/draft-persistence architecture. It receives already-
// rendered card JSX nodes (the exact same `cardsContent` entries produced
// by `renderGenericSection`'s shared field-rendering pipeline in
// RNICA.jsx -- same `formData.neurological` / `updateField` binding, same
// validation, same narrative/structured-findings/HOPE/POC consumers) and
// only re-arranges where those nodes sit on screen. This component:
//   - does NOT read or write `formData` itself,
//   - does NOT call any API or persistence hook,
//   - introduces NO schema/migration/backend change,
//   - removes NO field, path, option, or value.
// It is presentation/layout only.
//
// PRODUCT OWNER DECISION (2026-10-12) "SNS Cognitive Screen Removal from
// Neuro Workflow" -- supersedes the "Cognitive Screen De-Prioritization"
// Row 6 placement below. The owner's explicit instruction closed off any
// relocation destination ("Do not create Advanced Clinical Tools /
// Optional Assessment Tools / Launch Cognitive Screen or any other
// relocation destination. REMOVE SNS COGNITIVE SCREEN FROM THE
// NEUROLOGICAL WORKFLOW."). SNS Cognitive Screen was already confirmed
// not CMS/HOPE/LCD/eligibility/RNICA-completion/narrative/POC required.
// `cards["SNS Cognitive Screen"]` is intentionally never read by this
// panel now -- the card does not render anywhere in Neuro. This does not
// delete the field/schema/calculation (`computeSnsCognitiveScreen` and
// `cognitiveScreen.*` paths in RNICA.jsx are untouched, and any
// already-charted data still feeds narrative/Structured Findings output)
// -- only its Neuro-workflow UI entry point is gone.
//
// Also per this same decision: "Cognitive / Behavioral Findings" (Anxiety,
// Agitation, Confusion, Delirium, Sundowning, Combative behavior,
// Depression, Restlessness, Seizure History) is no longer collapsed by
// default -- these are higher-value hospice findings than SNS Cognitive
// Screen ever was, and must be immediately visible/expanded, not hidden
// behind a click (see `collapsedByDefault` removed at this card's
// SECTION_CONFIGS entry in RNICA.jsx). Psychiatric History's collapsed-
// by-default state is unchanged (historical info, lower priority than
// current findings).
//
//   Row 1: Neurological Overview            | Overall Change Since Prior Assessment
//   Row 2: Consciousness                    | Orientation
//   Row 3: Communication / Hearing / Vision | Cognitive / Behavioral Findings
//          (Behavioral Findings includes Anxiety/Agitation via the
//          existing Symptoms/Demeanor pill group -- unchanged, still
//          Neuro-owned, still HOPE-harvested downstream exactly as
//          before; expanded by default -- see decision above)
//   Row 4: Sensory Deficits / Sensory Aids  | Psychiatric History
//   Row 5: Sleep / Responsiveness (full width, not paired, primary Neuro
//          section per the same decision -- not split, occupies full
//          available width)
//   Row 6: Neurological Notes (full width, not paired)
//
// Each row reuses the same `grid grid-cols-1 lg:grid-cols-2` Tailwind
// pattern RespiratoryPanel.tsx already uses for its own two-column rows,
// so Neuro visually matches Respiratory's density without introducing a
// new CSS file or any shared-component change that could affect
// Cardiovascular (which keeps using `BodySystemShell` untouched).
// PRODUCT OWNER REVIEW (2026-10-12) "Visual Density Pass" Directive 1
// "Reduce vertical spacing... Target: more information visible without
// scrolling" -- row gap (gap-y-2 -> gap-y-1), per-column field gap
// (gap-2 -> gap-1.5), and the overall row stack (gap-3 -> gap-2) are all
// tightened one notch. This changes spacing only -- no field, row
// pairing, or card content is affected.
function PanelRow({ left, right }) {
  if (!left && !right) return null;
  return (
    <div className="grid grid-cols-1 gap-x-4 gap-y-1 lg:grid-cols-2 lg:items-start">
      {left ? <div className="flex flex-col gap-1.5">{left}</div> : null}
      {right ? <div className="flex flex-col gap-1.5">{right}</div> : null}
    </div>
  );
}

export function NeurologicalPanel({ header, cardsByTitle, changeSincePrior, pocAction }) {
  const cards = cardsByTitle || {};
  return (
    <div className="flex flex-col gap-2" data-testid="neurological-panel">
      {header}
      <PanelRow left={cards["Neurological Overview"]} right={changeSincePrior} />
      <PanelRow left={cards["Consciousness"]} right={cards["Orientation"]} />
      <PanelRow left={cards["Communication / Hearing / Vision"]} right={cards["Cognitive / Behavioral Findings"]} />
      <PanelRow left={cards["Sensory Deficits / Sensory Aids"]} right={cards["Psychiatric History"]} />
      {cards["Sleep / Responsiveness"] ? (
        <div className="flex flex-col gap-1.5" data-testid="neurological-panel-sleep-fullwidth">
          {cards["Sleep / Responsiveness"]}
        </div>
      ) : null}
      {/*
       * PRODUCT OWNER DECISION (2026-10-12) "SNS Cognitive Screen Removal
       * from Neuro Workflow" -- supersedes the prior "Optional Screening
       * Tools" relocation block below Sleep/Responsiveness. The owner's
       * explicit instruction: "Do not create Advanced Clinical Tools /
       * Optional Assessment Tools / Launch Cognitive Screen or any other
       * relocation destination. REMOVE SNS COGNITIVE SCREEN FROM THE
       * NEUROLOGICAL WORKFLOW." The tool was already confirmed not
       * CMS/HOPE/eligibility/RNICA-completion/narrative/POC required.
       * `cards["SNS Cognitive Screen"]` (still produced by
       * `renderGenericSection`'s shared card pipeline in RNICA.jsx) is
       * intentionally never read here, so the card no longer renders
       * anywhere in this panel. No schema/field/path/value/calculation
       * was touched -- any already-charted cognitive screen data remains
       * intact in the record and still feeds the narrative/Structured
       * Findings output; there is simply no Neuro-workflow UI entry point
       * to view or edit it anymore.
       */}
      {cards["Notes"] ? <div className="flex flex-col gap-1.5">{cards["Notes"]}</div> : null}
      {pocAction ? <div className="flex flex-col items-start gap-1.5">{pocAction}</div> : null}
    </div>
  );
}
