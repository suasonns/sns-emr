import React from "react";
import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import {
  BodySystemShell,
  BodySystemShellHeader,
  BodySystemShellCardiovascularDemo,
} from "./BodySystemShell";

// OWNER DECISION (2026-10-06) "Body Systems Architecture Review" Pass 1 --
// proves the shared shell enforces the canonical 7-part order BY
// CONSTRUCTION (DOM order always matches the blueprint regardless of the
// order props are supplied in) and that no separate large Summary card
// can exist inside it. Required Tests #1-7 ("shared shell" category).

describe("BodySystemShell canonical order (Required Test #1)", () => {
  it("renders header, assessment state, essential findings, change since prior, triggered detail, notes, and POC action in that fixed DOM order even when props are passed out of order", () => {
    const { container } = render(
      <BodySystemShell
        pocAction={<button type="button">+ Add to POC</button>}
        notes={<textarea aria-label="notes" />}
        triggeredDetail={<div>triggered detail content</div>}
        changeSincePrior={<div>change since prior content</div>}
        essentialFindings={<div>essential findings content</div>}
        assessmentState={<div>assessment state content</div>}
        header={<div>header content</div>}
      />
    );
    const slotClasses = Array.from(container.firstChild.children).map((el) => el.className);
    expect(slotClasses).toEqual([
      "body-system-shell__header",
      "body-system-shell__assessment-state",
      "body-system-shell__essential-findings",
      "body-system-shell__change-since-prior",
      "body-system-shell__triggered-detail",
      "body-system-shell__notes",
      "body-system-shell__poc-action",
    ]);
  });

  it("has no Summary slot at all -- a caller cannot reintroduce a large duplicate Summary card", () => {
    const { container } = render(<BodySystemShell assessmentState={<div>state</div>} />);
    expect(container.querySelector('[class*="summary-card"]')).toBeNull();
    expect(container.querySelector(".body-system-shell__summary")).toBeNull();
  });

  it("omits optional slots entirely from the DOM when not supplied (no reserved blank space)", () => {
    const { container } = render(<BodySystemShell assessmentState={<div>state only</div>} />);
    expect(container.querySelector(".body-system-shell__triggered-detail")).toBeNull();
    expect(container.querySelector(".body-system-shell__change-since-prior")).toBeNull();
    expect(container.querySelector(".body-system-shell__poc-action")).toBeNull();
  });
});

describe("BodySystemShellHeader (Required Test: exactly one workflow status)", () => {
  it("renders exactly one status badge and one concise summary line, never a large Summary card", () => {
    render(
      <BodySystemShellHeader
        icon="❤️"
        name="Cardiovascular"
        status="Review Required"
        findingCount={1}
        summaryLine="Peripheral edema documented."
      />
    );
    expect(screen.getAllByText("Review Required")).toHaveLength(1);
    expect(screen.getByText("Peripheral edema documented.")).toBeTruthy();
    expect(screen.getByText("1 finding")).toBeTruthy();
  });
});

describe("BodySystemShellCardiovascularDemo (synthetic Pass 1 demonstration)", () => {
  it("renders the real Cardiovascular card shape (Overview, Circulation & Perfusion, Clinical Status Change, Notes, POC) through the shell in canonical order", () => {
    const { container } = render(<BodySystemShellCardiovascularDemo />);
    expect(screen.getByText("Cardiovascular")).toBeTruthy();
    expect(screen.getByText("Cardiovascular Overview")).toBeTruthy();
    expect(screen.getByText(/Circulation & Perfusion/)).toBeTruthy();
    expect(screen.getByText("Clinical Status Change")).toBeTruthy();
    expect(screen.getByText(/Cardiovascular Notes/)).toBeTruthy();
    expect(screen.getByText("+ Add to POC")).toBeTruthy();

    // Exactly one assessment-state radio group (four canonical options),
    // not a system-specific taxonomy.
    const overviewRadios = container.querySelectorAll('input[name="cv-demo-overview"]');
    expect(overviewRadios).toHaveLength(4);

    // Exactly one POC action area, rendered last.
    const pocButtons = screen.getAllByText("+ Add to POC");
    expect(pocButtons).toHaveLength(1);
    const slots = Array.from(container.firstChild.children).map((el) => el.className);
    expect(slots[slots.length - 1]).toBe("body-system-shell__poc-action");
  });
});
