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
// Documentation Coverage itself (`cardsByTitle["Neurological Overview"]`,
// which still renders `computeNeurologicalDocumentationCoverage`'s
// output) and every other row remain unaffected.

describe("NeurologicalPanel -- derived Overview synthesis removal", () => {
  it("renders nothing in the header slot when header is null (current authorized state)", () => {
    const { container } = render(
      <NeurologicalPanel
        header={null}
        cardsByTitle={{
          "Neurological Overview": <div data-testid="neurological-documentation-coverage">Coverage content</div>,
        }}
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
        cardsByTitle={{
          "Neurological Overview": (
            <div data-testid="neurological-documentation-coverage">
              Consciousness: Alert · Orientation: oriented x4
            </div>
          ),
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
