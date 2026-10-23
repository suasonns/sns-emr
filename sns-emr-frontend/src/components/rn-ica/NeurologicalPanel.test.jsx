import React from "react";
import { describe, it, expect } from "vitest";
import { render } from "@testing-library/react";
import { NeurologicalPanel } from "./NeurologicalPanel";

// PRODUCT OWNER DIRECTIVE (2026-10-13) "Remove The Neuro-Only Derived
// Overview / Freeze Body-System Presentation Changes" -- proves the
// rendered prose paragraph previously produced by
// `computeNeurologicalOverviewSynthesis` (e.g. "Awake and oriented x4
// with intact communication...", "This is the initial neurological
// assessment; no prior comparison is available.") is no longer rendered
// above Neurological Documentation Coverage, now that RNICA.jsx passes
// `header={null}` to this panel instead of `bodySystemShellHeader`.
// Documentation Coverage itself (now passed as the standalone
// `documentationCoverage` prop -- see the follow-up "Remove The
// Neurological Overview Container" directive below) and every other row
// remain unaffected.

describe("NeurologicalPanel -- derived Overview synthesis removal", () => {
  it("renders nothing in the header slot when header is null (current authorized state)", () => {
    const { container } = render(
      <NeurologicalPanel
        header={null}
        documentationCoverage={<div data-testid="neurological-documentation-coverage">Coverage content</div>}
        cardsByTitle={{}}
        changeSincePrior={<div>change since prior</div>}
        pocAction={<button type="button">+ Add to POC</button>}
      />
    );
    expect(container.textContent).not.toMatch(/no prior comparison is available/i);
    expect(container.textContent).not.toMatch(/oriented x4/i);
    expect(container.textContent).not.toMatch(/intact communication/i);
  });

  it("never emits the retired synthesis wording even when cards include real Documentation Coverage content", () => {
    const { container } = render(
      <NeurologicalPanel
        header={null}
        documentationCoverage={
          <div data-testid="neurological-documentation-coverage">
            Consciousness: Alert · Orientation: oriented x4
          </div>
        }
        cardsByTitle={{
          "Consciousness": <div>Consciousness card</div>,
        }}
      />
    );
    // Documentation Coverage content is preserved...
    expect(container.textContent).toMatch(/neurological-documentation-coverage|Consciousness: Alert/);
    // ...but the retired derived-Overview synthesis sentence structure is not.
    expect(container.textContent).not.toMatch(/this is the initial neurological assessment/i);
    expect(container.textContent).not.toMatch(/anxiety, agitation, depression/i);
  });

  it("still supports a header slot mechanically (regression guard for the shared panel contract)", () => {
    const { container } = render(
      <NeurologicalPanel header={<div>some future approved header</div>} cardsByTitle={{}} />
    );
    expect(container.textContent).toMatch(/some future approved header/);
  });
});

// PRODUCT OWNER DIRECTIVE (2026-10-13) "Remove The Standalone
// Neurological 'Unable To Assess This Visit?' Gate -- No Replacement" --
// supersedes the prior "Remove The Neurological Overview Container"
// directive referenced below (which still rendered a renamed
// "Assessment" card under Coverage). That card, and the gate it held,
// is retired entirely with no replacement row. Documentation Coverage
// renders standalone with no title/card/wrapper around it.
describe("NeurologicalPanel -- Neurological Overview container removal", () => {
  it("renders Documentation Coverage standalone, with no surrounding Overview title", () => {
    const { container, queryByText } = render(
      <NeurologicalPanel
        header={null}
        documentationCoverage={<div data-testid="neurological-documentation-coverage">Coverage content</div>}
        cardsByTitle={{}}
      />
    );
    expect(container.querySelector('[data-testid="neurological-panel-coverage-fullwidth"]')).not.toBeNull();
    expect(queryByText(/^Neurological Overview$/)).toBeNull();
  });

  it("renders no Assessment card/row of any kind -- the gate was retired with no replacement", () => {
    const { container, queryByText } = render(
      <NeurologicalPanel
        header={null}
        documentationCoverage={<div data-testid="neurological-documentation-coverage">Coverage content</div>}
        cardsByTitle={{
          "Assessment": <div data-testid="neurological-assessment-card">Unable to Assess This Visit?</div>,
        }}
      />
    );
    expect(container.querySelector('[data-testid="neurological-panel-assessment-fullwidth"]')).toBeNull();
    expect(container.querySelector('[data-testid="neurological-assessment-card"]')).toBeNull();
    expect(queryByText(/Unable to Assess This Visit\?/)).toBeNull();
  });

  it("renders nothing for the Coverage row when documentationCoverage is not provided (no empty wrapper)", () => {
    const { container } = render(
      <NeurologicalPanel header={null} documentationCoverage={null} cardsByTitle={{}} />
    );
    expect(container.querySelector('[data-testid="neurological-panel-coverage-fullwidth"]')).toBeNull();
  });
});

// PRODUCT OWNER CORRECTION (2026-10-21) "Neurological Layout and HOPE
// Anxiety/Agitation Impact" Section 9 "Neuro Must Follow Infection
// Layout" -- secondary cards balanced directly inside Columns 2/3 of the
// one 3-column grid, not pooled into a separate full-width row below it.
//
// PRODUCT OWNER REVIEW (2026-10-24) "Organize, Don't Hide" -- supersedes
// the Column 2 "dumping ground" placement below: Psychiatric History
// moves to Column 3 (directly below Communication / Hearing / Vision)
// and is no longer collapsed by default. Final structure --
//   Column 1: Consciousness, Orientation, Sensory Deficits/Sensory Aids.
//   Column 2: Behavioral Symptoms, Cognitive Findings, Neurological
//     Findings.
//   Column 3: Communication / Hearing / Vision, Psychiatric History.
//
// PRODUCT OWNER REVIEW (2026-10-24) "Sleep Assessment Is Not Clinically
// Aligned With Responsiveness / Status Change" -- the former "Sleep /
// Responsiveness" standalone card is split into three cards ("Sleep
// Assessment", "Responsiveness", "Neurological Status Change"), none of
// which are part of any grid column -- all three render as their own
// standalone, always-visible, full-width sections below the grid.
describe("NeurologicalPanel -- Body System Layout Standardization (3-column Assessment Grid)", () => {
  it("buckets existing cards into 3 independent-height columns using the shared body-system grid classes", () => {
    const { container, getByTestId } = render(
      <NeurologicalPanel
        header={null}
        documentationCoverage={<div data-testid="neurological-documentation-coverage">Coverage content</div>}
        cardsByTitle={{
          "Consciousness": <div data-testid="card-consciousness">Consciousness card</div>,
          "Orientation": <div data-testid="card-orientation">Orientation card</div>,
          "Communication / Hearing / Vision": <div data-testid="card-communication">Communication card</div>,
          "Sleep Assessment": <div data-testid="card-sleep-assessment">Sleep Assessment card</div>,
          "Responsiveness": <div data-testid="card-responsiveness">Responsiveness card</div>,
          "Neurological Status Change": <div data-testid="card-status-change">Status Change card</div>,
          "Behavioral Symptoms": <div data-testid="card-behavioral">Behavioral card</div>,
          "Cognitive Findings": <div data-testid="card-cognitive">Cognitive card</div>,
          "Neurological Findings": <div data-testid="card-neuro-findings">Neuro findings card</div>,
          "Psychiatric History": <div data-testid="card-psych">Psych card</div>,
          "Sensory Deficits / Sensory Aids": <div data-testid="card-sensory">Sensory card</div>,
        }}
        changeSincePrior={<div data-testid="neuro-change-since-prior">change since prior</div>}
      />
    );
    const grid = getByTestId("neurological-panel-assessment-grid");
    expect(grid.classList.contains("rnica-bodysystem-grid-columns")).toBe(true);
    const columns = grid.querySelectorAll(".rnica-bodysystem-grid-column");
    expect(columns.length).toBe(3);
    // Column 1: Consciousness, Orientation, Sensory Deficits/Sensory Aids.
    expect(columns[0].querySelector('[data-testid="card-consciousness"]')).not.toBeNull();
    expect(columns[0].querySelector('[data-testid="card-orientation"]')).not.toBeNull();
    expect(columns[0].querySelector('[data-testid="card-sensory"]')).not.toBeNull();
    // Column 2: Behavioral Symptoms, Cognitive Findings, Neurological
    // Findings -- Psychiatric History moved to Column 3 (below).
    expect(columns[1].querySelector('[data-testid="card-behavioral"]')).not.toBeNull();
    expect(columns[1].querySelector('[data-testid="card-cognitive"]')).not.toBeNull();
    expect(columns[1].querySelector('[data-testid="card-neuro-findings"]')).not.toBeNull();
    expect(columns[1].querySelector('[data-testid="card-psych"]')).toBeNull();
    // Column 3: Communication / Hearing / Vision, then Psychiatric
    // History -- Sleep Assessment/Responsiveness/Neurological Status
    // Change are NOT in this grid at all (see standalone-section tests
    // below).
    expect(columns[2].querySelector('[data-testid="card-communication"]')).not.toBeNull();
    expect(columns[2].querySelector('[data-testid="card-psych"]')).not.toBeNull();
    expect(columns[2].querySelector('[data-testid="card-sleep-assessment"]')).toBeNull();
    expect(columns[2].querySelector('[data-testid="card-responsiveness"]')).toBeNull();
    expect(columns[2].querySelector('[data-testid="card-status-change"]')).toBeNull();
    // The pooled full-width collapsible row is retired entirely.
    expect(
      container.querySelector('[data-testid="neurological-panel-fullwidth-collapsible-cards"]')
    ).toBeNull();
    // No findings are lost -- every card passed in is present somewhere in the DOM
    // (Sleep Assessment/Responsiveness/Status Change render in their own
    // standalone sections, not the grid).
    expect(container.querySelector('[data-testid="card-consciousness"]')).not.toBeNull();
    expect(container.querySelector('[data-testid="card-orientation"]')).not.toBeNull();
    expect(container.querySelector('[data-testid="card-communication"]')).not.toBeNull();
    expect(container.querySelector('[data-testid="card-sleep-assessment"]')).not.toBeNull();
    expect(container.querySelector('[data-testid="card-responsiveness"]')).not.toBeNull();
    expect(container.querySelector('[data-testid="card-status-change"]')).not.toBeNull();
    expect(container.querySelector('[data-testid="card-behavioral"]')).not.toBeNull();
    expect(container.querySelector('[data-testid="card-cognitive"]')).not.toBeNull();
    expect(container.querySelector('[data-testid="card-neuro-findings"]')).not.toBeNull();
    expect(container.querySelector('[data-testid="card-psych"]')).not.toBeNull();
    expect(container.querySelector('[data-testid="card-sensory"]')).not.toBeNull();
  });

  it("positions Clinical Status Change (changeSincePrior) after the Assessment Grid, not before it", () => {
    const { container } = render(
      <NeurologicalPanel
        header={null}
        documentationCoverage={<div data-testid="neurological-documentation-coverage">Coverage content</div>}
        cardsByTitle={{
          "Consciousness": <div data-testid="card-consciousness">Consciousness card</div>,
        }}
        changeSincePrior={<div data-testid="neuro-change-since-prior">change since prior</div>}
      />
    );
    const grid = container.querySelector('[data-testid="neurological-panel-assessment-grid"]');
    const changeRow = container.querySelector('[data-testid="neurological-panel-status-change-fullwidth"]');
    expect(grid).not.toBeNull();
    expect(changeRow).not.toBeNull();
    // DOCUMENT_POSITION_FOLLOWING (4) means `changeRow` comes after `grid` in document order.
    // eslint-disable-next-line no-bitwise
    expect(grid.compareDocumentPosition(changeRow) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
  });

  it("does not render the Assessment Grid wrapper when no grid cards are supplied", () => {
    const { container } = render(
      <NeurologicalPanel header={null} documentationCoverage={null} cardsByTitle={{}} />
    );
    expect(container.querySelector('[data-testid="neurological-panel-assessment-grid"]')).toBeNull();
  });
});

// PRODUCT OWNER REVIEW (2026-10-24) "Sleep Assessment Is Not Clinically
// Aligned With Responsiveness / Status Change" -- "SLEEP ANSWERS: How is
// the patient sleeping? RESPONSIVENESS ANSWERS: How responsive is the
// patient? STATUS CHANGE ANSWERS: Has the neurological condition
// changed? THREE DIFFERENT QUESTIONS. THREE DIFFERENT GROUPS." Sleep
// Assessment, Responsiveness, and Neurological Status Change each render
// as their own standalone full-width section, outside every grid column,
// in that order: Sleep Assessment, then Responsiveness, then
// Neurological Status Change (grouped with `changeSincePrior` --
// "Overall Change Since Prior Assessment" -- so the two trend fields
// read together as one visual block).
describe("NeurologicalPanel -- Sleep Assessment / Responsiveness / Neurological Status Change standalone sections", () => {
  it("renders Sleep Assessment, Responsiveness, and Neurological Status Change outside the Assessment Grid, each in its own full-width row", () => {
    const { container } = render(
      <NeurologicalPanel
        header={null}
        documentationCoverage={<div data-testid="neurological-documentation-coverage">Coverage content</div>}
        cardsByTitle={{
          "Consciousness": <div data-testid="card-consciousness">Consciousness card</div>,
          "Communication / Hearing / Vision": <div data-testid="card-communication">Communication card</div>,
          "Sleep Assessment": <div data-testid="card-sleep-assessment">Sleep Assessment card</div>,
          "Responsiveness": <div data-testid="card-responsiveness">Responsiveness card</div>,
          "Neurological Status Change": <div data-testid="card-status-change">Status Change card</div>,
        }}
        changeSincePrior={<div data-testid="neuro-change-since-prior">change since prior</div>}
      />
    );
    const grid = container.querySelector('[data-testid="neurological-panel-assessment-grid"]');
    const sleepRow = container.querySelector('[data-testid="neurological-panel-sleep-assessment-fullwidth"]');
    const responsivenessRow = container.querySelector('[data-testid="neurological-panel-responsiveness-fullwidth"]');
    const statusChangeRow = container.querySelector('[data-testid="neurological-panel-status-change-fullwidth"]');
    expect(grid).not.toBeNull();
    expect(sleepRow).not.toBeNull();
    expect(responsivenessRow).not.toBeNull();
    expect(statusChangeRow).not.toBeNull();
    expect(sleepRow.querySelector('[data-testid="card-sleep-assessment"]')).not.toBeNull();
    expect(responsivenessRow.querySelector('[data-testid="card-responsiveness"]')).not.toBeNull();
    expect(statusChangeRow.querySelector('[data-testid="card-status-change"]')).not.toBeNull();
    // Overall Change Since Prior Assessment is grouped inside the same
    // status-change row as Neurological Status Change's own field, not a
    // separate row.
    expect(statusChangeRow.querySelector('[data-testid="neuro-change-since-prior"]')).not.toBeNull();
    // None are inside the grid at all.
    expect(grid.querySelector('[data-testid="card-sleep-assessment"]')).toBeNull();
    expect(grid.querySelector('[data-testid="card-responsiveness"]')).toBeNull();
    expect(grid.querySelector('[data-testid="card-status-change"]')).toBeNull();
  });

  it("positions Sleep Assessment, Responsiveness, and Neurological Status Change in that order after the Assessment Grid", () => {
    const { container } = render(
      <NeurologicalPanel
        header={null}
        documentationCoverage={null}
        cardsByTitle={{
          "Consciousness": <div data-testid="card-consciousness">Consciousness card</div>,
          "Sleep Assessment": <div data-testid="card-sleep-assessment">Sleep Assessment card</div>,
          "Responsiveness": <div data-testid="card-responsiveness">Responsiveness card</div>,
          "Neurological Status Change": <div data-testid="card-status-change">Status Change card</div>,
        }}
        changeSincePrior={<div data-testid="neuro-change-since-prior">change since prior</div>}
      />
    );
    const grid = container.querySelector('[data-testid="neurological-panel-assessment-grid"]');
    const sleepRow = container.querySelector('[data-testid="neurological-panel-sleep-assessment-fullwidth"]');
    const responsivenessRow = container.querySelector('[data-testid="neurological-panel-responsiveness-fullwidth"]');
    const statusChangeRow = container.querySelector('[data-testid="neurological-panel-status-change-fullwidth"]');
    // eslint-disable-next-line no-bitwise
    expect(grid.compareDocumentPosition(sleepRow) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    // eslint-disable-next-line no-bitwise
    expect(sleepRow.compareDocumentPosition(responsivenessRow) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    // eslint-disable-next-line no-bitwise
    expect(responsivenessRow.compareDocumentPosition(statusChangeRow) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
  });

  it("renders no Sleep Assessment / Responsiveness / Neurological Status Change row when none of the cards (or changeSincePrior) are supplied", () => {
    const { container } = render(
      <NeurologicalPanel header={null} documentationCoverage={null} cardsByTitle={{}} />
    );
    expect(container.querySelector('[data-testid="neurological-panel-sleep-assessment-fullwidth"]')).toBeNull();
    expect(container.querySelector('[data-testid="neurological-panel-responsiveness-fullwidth"]')).toBeNull();
    expect(container.querySelector('[data-testid="neurological-panel-status-change-fullwidth"]')).toBeNull();
  });
});
