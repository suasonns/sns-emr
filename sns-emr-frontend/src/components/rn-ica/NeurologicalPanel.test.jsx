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

// PRODUCT OWNER DIRECTIVE (2026-10-13) "Body System Layout
// Standardization -- SNS Design System V1 / Infection Is The Reference
// Layout" -- proves Neurological now renders the same 3-independent-
// height-column Assessment Grid as Infection (shared
// `rnica-bodysystem-grid-columns`/`-column` classes) instead of the
// prior 2-column `PanelRow` pairs, with Clinical Status Change
// ("Overall Change Since Prior Assessment") moved to directly below the
// grid instead of above it.
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
          "Sleep / Responsiveness": <div data-testid="card-sleep">Sleep card</div>,
          "Cognitive / Behavioral Findings": <div data-testid="card-cognitive">Cognitive card</div>,
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
    // PRODUCT OWNER DIRECTIVE (2026-10-23) "Just Lay It Out How You Laid
    // Out Infection" (Part 2) -- Psychiatric History and Sleep /
    // Responsiveness (Neuro's only two `collapsedByDefault` cards, both
    // unpredictable-height when expanded) are pulled OUT of the 3-column
    // grid and render as their own full-width rows below it instead,
    // mirroring Infection's "Infection History Notes" precedent -- see
    // the NeurologicalPanel doc comment. Only the grid's three
    // always-expanded, predictable-height cards remain column content.
    expect(columns[0].querySelector('[data-testid="card-consciousness"]')).not.toBeNull();
    expect(columns[0].querySelector('[data-testid="card-orientation"]')).not.toBeNull();
    expect(columns[1].querySelector('[data-testid="card-cognitive"]')).not.toBeNull();
    expect(columns[2].querySelector('[data-testid="card-communication"]')).not.toBeNull();
    expect(columns[2].querySelector('[data-testid="card-sensory"]')).not.toBeNull();
    expect(columns[1].querySelector('[data-testid="card-psych"]')).toBeNull();
    expect(columns[1].querySelector('[data-testid="card-sleep"]')).toBeNull();
    // Psychiatric History and Sleep / Responsiveness instead render as
    // full-width rows directly below the grid.
    const fullWidthCollapsible = getByTestId("neurological-panel-collapsible-fullwidth");
    expect(fullWidthCollapsible.querySelector('[data-testid="card-psych"]')).not.toBeNull();
    expect(fullWidthCollapsible.querySelector('[data-testid="card-sleep"]')).not.toBeNull();
    // No findings are lost -- every card passed in is present somewhere in the DOM.
    expect(container.querySelector('[data-testid="card-consciousness"]')).not.toBeNull();
    expect(container.querySelector('[data-testid="card-orientation"]')).not.toBeNull();
    expect(container.querySelector('[data-testid="card-communication"]')).not.toBeNull();
    expect(container.querySelector('[data-testid="card-sleep"]')).not.toBeNull();
    expect(container.querySelector('[data-testid="card-cognitive"]')).not.toBeNull();
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
    const changeRow = container.querySelector('[data-testid="neurological-panel-change-since-prior-fullwidth"]');
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
