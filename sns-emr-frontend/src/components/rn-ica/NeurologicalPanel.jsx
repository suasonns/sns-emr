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
//   Row 1:  Documentation Coverage, full width, no card/title/wrapper --
//          see the 2026-10-13 "Remove The Neurological Overview
//          Container" directive: the former "Neurological Overview" card
//          only ever wrapped Coverage with no Overview content of its
//          own, so the wrapper is gone and Coverage renders standalone
//          (matching Respiratory's full-width Coverage exactly). The
//          "Assessment" card that briefly replaced it (the "Unable to
//          Assess This Visit?" gate and its proposed "Assessment
//          Context" replacement) was retired entirely by PRODUCT OWNER
//          DIRECTIVE (2026-10-13) "Remove The Standalone Neurological
//          'Unable To Assess This Visit?' Gate -- No Replacement": both
//          required the nurse to declare something already derivable
//          from documented findings. No card/row replaces it.
//   Row 1b: Overall Change Since Prior Assessment, full width, directly
//          below Row 1 (mirrors Respiratory's full-width "Assessment
//          context" row placement right after its Coverage).
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
// PRODUCT OWNER DIRECTIVE (2026-10-13) "Body System Layout
// Standardization -- SNS Design System V1 / Infection Is The Reference
// Layout" -- supersedes the Row 2-5 two-column-pair layout documented
// above (`PanelRow`/`grid-cols-2`). Infection's 3-independent-height-
// column Assessment Grid (`.rnica-bodysystem-grid-columns`/`-column`,
// RNICACommandWorkspace.css) is now the one approved layout for every
// Body System's assessment content:
//   Layer 1  Documentation Coverage      -- full width (unchanged below)
//   Layer 2  Assessment Grid (3 columns) -- Current Findings / History
//            & Context / Monitoring & Support
//   Layer 3  Clinical Status Change      -- full width, BELOW the grid
//            (moved out of its prior "Row 1b", directly under Coverage,
//            position -- same `changeSincePrior` prop, same
//            `clinicalStatusChange` path, same control; only its
//            position in the DOM moved)
//   Layer 4  Notes                       -- full width, below Clinical
//            Status Change (unchanged)
// Same cards, same fields, same data, same order of appearance within
// each column -- only the wrapper markup and the Clinical Status Change
// position change.
//
// PRODUCT OWNER DIRECTIVE (2026-10-23) "Just Lay It Out How You Laid Out
// Infection" (Part 2 -- live-screen follow-up) -- the Part 1 rebalance
// above (committed moments earlier) still produced lopsided columns on
// the user's real screen the instant a nurse expanded one of Neuro's two
// `collapsedByDefault` cards (Psychiatric History, Sleep / Responsiveness):
// whichever column held the expanded card grew to several screens tall
// while its neighbor columns sat mostly empty beside it all the way down
// -- the exact "wasted space" complaint, just relocated to a different
// column. Root cause: NONE of Infection's reference 3-column grid cards
// (Active Infection, Resistant Organisms, Infection History, Immune
// Status, Antibiotic Therapy, Precautions, Temperature) are
// `collapsedByDefault` -- Infection's grid only ever holds content of
// fairly predictable height, which is *why* its columns stay close to
// level. Infection's own "Infection History Notes" card (free-text,
// unpredictable height) was, for the same reason, deliberately pulled
// OUT of its 3-column grid and rendered as its own full-width row below
// the grid (see the 2026-10-14 "Wasted Space Elimination" directive
// above). Applying that identical precedent here: Neuro's two
// unpredictable-height collapsible cards move out of the grid entirely
// and render as their own full-width rows directly below it, so
// expanding either one can never again distort the 3 columns' relative
// heights. No field/path/value/collapse-state change to either card --
// only their position in the DOM (grid column -> full-width row).
//   Column 1 "Current Findings": Consciousness, Orientation.
//   Column 2 "History / Context": Cognitive / Behavioral Findings
//     (Behavior) -- always-expanded, predictable height.
//   Column 3 "Monitoring / Support": Communication / Hearing / Vision,
//     Sensory Deficits / Sensory Aids -- both always-expanded,
//     predictable height, grouped together as the two sensory-function
//     cards (closer clinical fit than Sensory Deficits/Aids alone).
//   Full-width rows below the grid (Infection's "Notes" precedent):
//     Psychiatric History, then Sleep / Responsiveness -- both remain
//     exactly as collapsible/expandable as before; they simply no
//     longer share column space with the always-expanded cards above.
export function NeurologicalPanel({ header, documentationCoverage, cardsByTitle, changeSincePrior, pocAction }) {
  const cards = cardsByTitle || {};
  // PRODUCT OWNER DIRECTIVE (2026-10-21, "Neurological Layout Review --
  // One Layout Model Only") -- supersedes the Column 2 "Cognitive +
  // Psychiatric History" stacking immediately above: mixing a 3-column
  // grid, a 2-card-stacked column, and full-width rows in the same
  // section was flagged as visually inconsistent ("three different
  // layout models in the same section"). Collapsing to exactly two
  // models --
  //   Primary Findings (3-column grid, always-expanded cards only):
  //     Column 1: Consciousness, Orientation, Sensory Deficits/Sensory Aids
  //     Column 2: Cognitive / Behavioral Findings (alone)
  //     Column 3: Communication / Hearing / Vision
  //   Secondary Assessments (collapsed-by-default, full width, below the
  //   grid -- both unpredictable-height collapsible cards grouped here
  //   together instead of one living inside the grid):
  //     Psychiatric History, Sleep / Responsiveness
  //   Notes (full width, below Secondary Assessments): Neurological Notes
  //   -- sole narrative field.
  // No field/path/value/collapse-state change to any card -- column/
  // section placement only.
  // PRODUCT OWNER CORRECTION (2026-10-21) "Neurological Layout and HOPE
  // Anxiety/Agitation Impact" Section 9 "Neuro Must Follow Infection
  // Layout" -- supersedes the "Infection Is The Layout Reference
  // Standard" full-width-collapsible-row grouping immediately above:
  // that layout let every collapsed secondary card accumulate in one
  // place while a sibling column sat empty, which the owner rejected as
  // unbalanced ("Do not allow all collapsed secondary content to
  // accumulate in Column 2 while Column 3 remains mostly empty.
  // Balance the secondary collapsible panels across Columns 2 and 3.").
  // Neuro now uses Infection's actual one-balanced-three-column
  // structure, not merely its CSS class:
  //   Column 1: Consciousness, Orientation, Sensory Deficits/Sensory Aids.
  //   Column 2: Behavioral Symptoms (+ its own conditional Anxiety/
  //     Agitation Impact controls, rendered inside the same card -- see
  //     SECTION_CONFIGS.neurological), then Cognitive Findings and
  //     Neurological Findings.
  //   Column 3: Communication / Hearing / Vision, then Psychiatric
  //     History.
  // No field/path/value change to any card -- column placement only.
  //
  // PRODUCT OWNER REVIEW (2026-10-24) "Organize, Don't Hide" -- supersedes
  // the "Psychiatric History in Column 2, collapsed by default" placement
  // above: Column 2 had become "a dumping ground for multiple unrelated
  // sections" while Column 3 sat underutilized. Psychiatric History moves
  // to Column 3, directly below Communication / Hearing / Vision, and its
  // `collapsedByDefault` flag is removed (see SECTION_CONFIGS.neurological
  // in RNICA.jsx) -- "DO NOT COLLAPSE PSYCHIATRIC HISTORY... THE GOAL IS
  // NOT TO REDUCE VISIBILITY." Neurological Findings stays in Column 2,
  // alongside Cognitive Findings, with its collapse state unchanged --
  // only Psychiatric History's column and collapse state moved.
  //
  // PRODUCT OWNER REVIEW (2026-10-24) "Sleep / Responsiveness -- Own
  // 3-Column Layout" -- Sleep / Responsiveness is pulled OUT of the
  // primary Assessment Grid entirely ("THIS SECTION SHALL NOT BE MERGED
  // INTO THE PRIMARY NEUROLOGICAL GRID") and now renders as its own
  // standalone, full-width, ALWAYS-VISIBLE section directly below the
  // 3-column Assessment Grid -- the same full-width-row placement already
  // established for Infection's unpredictable-height "Notes" card and for
  // this panel's own `changeSincePrior` row. It is rendered immediately
  // ABOVE `changeSincePrior` ("Overall Change Since Prior Assessment") so
  // that Sleep's own internal Row 2 (Responsiveness, Change Since Prior
  // Visit -- see SECTION_CONFIGS.neurological's "Sleep / Responsiveness"
  // field order/CSS) sits directly adjacent to the section-wide Overall
  // Change control, letting all three read as one visual block without
  // duplicating `changeSincePrior` inside the Sleep card itself.
  // PRODUCT OWNER REVIEW (2026-10-24) "Sleep Assessment Is Not Clinically
  // Aligned With Responsiveness / Status Change" -- supersedes the
  // "Sleep / Responsiveness" standalone-card note above: that single
  // card mixed three different clinical questions ("How is the patient
  // sleeping?", "How responsive is the patient?", "Has the neurological
  // condition changed?") into one group. It is now split into three
  // separate, always-visible, full-width sections rendered in this
  // order below the Assessment Grid: "Sleep Assessment" (own 3-column
  // layout, CSS override in RNICACommandWorkspace.css), "Responsiveness"
  // (its own section, not part of Sleep), and "Neurological Status
  // Change" (the card's "Change Since Prior Visit" field grouped
  // together with the existing section-wide `changeSincePrior` prop
  // ("Overall Change Since Prior Assessment") -- "THESE ARE TREND
  // ANALYSIS FIELDS. THEY SHOULD BE TOGETHER."). None of these three
  // cards is collapsed by default. No field/path/value change -- split,
  // order, and grouping only.
  const column1 = [
    cards["Consciousness"],
    cards["Orientation"],
    cards["Sensory Deficits / Sensory Aids"],
  ].filter((entry) => entry != null);
  const column2 = [
    cards["Behavioral Symptoms"],
    cards["Cognitive Findings"],
    cards["Neurological Findings"],
  ].filter((entry) => entry != null);
  const column3 = [
    cards["Communication / Hearing / Vision"],
    cards["Psychiatric History"],
  ].filter((entry) => entry != null);
  const hasGridContent = column1.length > 0 || column2.length > 0 || column3.length > 0;
  const sleepAssessment = cards["Sleep Assessment"];
  const responsiveness = cards["Responsiveness"];
  const neurologicalStatusChange = cards["Neurological Status Change"];
  const hasStatusChangeContent = neurologicalStatusChange != null || changeSincePrior != null;
  return (
    <div className="flex flex-col gap-2" data-testid="neurological-panel">
      {header}
      {/*
       * PRODUCT OWNER DIRECTIVE (2026-10-13) "Remove The Standalone
       * Neurological 'Unable To Assess This Visit?' Gate -- No
       * Replacement" -- Documentation Coverage renders directly, full
       * width, with no card/title/wrapper around it at all (matching
       * Respiratory's top-level `<DocumentationCoverage>` exactly) -- no
       * "Assessment" card follows it anymore. A patient who truly cannot
       * be assessed is documented at the specific finding level instead
       * (each field already carries its own "Unable to assess" option).
       */}
      {documentationCoverage ? (
        <div className="flex flex-col gap-1.5" data-testid="neurological-panel-coverage-fullwidth">
          {documentationCoverage}
        </div>
      ) : null}
      {hasGridContent ? (
        <div className="rnica-bodysystem-grid-columns" data-testid="neurological-panel-assessment-grid">
          <div className="rnica-bodysystem-grid-column">{column1}</div>
          <div className="rnica-bodysystem-grid-column">{column2}</div>
          <div className="rnica-bodysystem-grid-column">{column3}</div>
        </div>
      ) : null}
      {/*
       * PRODUCT OWNER REVIEW (2026-10-24) "Sleep Assessment Is Not
       * Clinically Aligned With Responsiveness / Status Change" --
       * standalone, full-width, own 3-column section, explicitly NOT
       * part of the 3-column Assessment Grid above and NOT merged with
       * Responsiveness or Neurological Status Change below.
       */}
      {sleepAssessment ? (
        <div className="flex flex-col gap-1.5" data-testid="neurological-panel-sleep-assessment-fullwidth">
          {sleepAssessment}
        </div>
      ) : null}
      {/*
       * PRODUCT OWNER REVIEW (2026-10-24) -- Responsiveness is "a
       * neurological observation. It is not part of the sleep
       * assessment." Its own standalone, full-width section, rendered
       * directly after Sleep Assessment and before Neurological Status
       * Change.
       */}
      {responsiveness ? (
        <div className="flex flex-col gap-1.5" data-testid="neurological-panel-responsiveness-fullwidth">
          {responsiveness}
        </div>
      ) : null}
      {/*
       * PRODUCT OWNER REVIEW (2026-10-24) -- "Neurological Status Change
       * GROUP: Change Since Prior Visit, Overall Change Since Prior
       * Assessment. THESE ARE TREND ANALYSIS FIELDS. THEY SHOULD BE
       * TOGETHER." `neurologicalStatusChange` (the card's own "Change
       * Since Prior Visit" field) renders directly above the existing
       * section-wide `changeSincePrior` prop ("Overall Change Since
       * Prior Assessment") inside one shared wrapper, so the two trend
       * fields read as a single grouped section without duplicating
       * `clinicalStatusChange` inside the card itself.
       */}
      {hasStatusChangeContent ? (
        <div className="flex flex-col gap-1.5" data-testid="neurological-panel-status-change-fullwidth">
          {neurologicalStatusChange}
          {changeSincePrior}
        </div>
      ) : null}
      {/*
       * PRODUCT OWNER DECISION (2026-10-12) "SNS Cognitive Screen Removal
       * from Neuro Workflow" -- `cards["SNS Cognitive Screen"]` (still
       * produced by `renderGenericSection`'s shared card pipeline in
       * RNICA.jsx) is intentionally never read here, so the card no
       * longer renders anywhere in this panel. No schema/field/path/
       * value/calculation was touched -- any already-charted cognitive
       * screen data remains intact in the record and still feeds the
       * narrative/Structured Findings output; there is simply no
       * Neuro-workflow UI entry point to view or edit it anymore.
       */}
      {cards["Notes"] ? <div className="flex flex-col gap-1.5">{cards["Notes"]}</div> : null}
      {pocAction ? <div className="flex flex-col items-start gap-1.5">{pocAction}</div> : null}
    </div>
  );
}
