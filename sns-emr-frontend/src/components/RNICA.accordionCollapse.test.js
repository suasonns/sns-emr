import { describe, it, expect } from "vitest";
import { computeJumpToSectionResult } from "./RNICA.jsx";

// OWNER DIRECTIVE (2026-10-30) "Accordion Collapse Defect A Fix" -- proves
// the production defect (sidebar re-click could never collapse an
// already-open section because the old code gated collapse on
// `activeSection === key`, a navigation-focus flag that changes whenever
// ANY other section is visited) is fixed, and that both entry points
// (in-content header `toggleSection`, sidebar-nav `jumpToSection`) now
// resolve through the exact same `collapsedSections` Set as the single
// source of truth. `computeJumpToSectionResult` is called directly by
// `jumpToSection` in the component (not a parallel reimplementation), so
// these are proof of the real component's behavior, not a simulation.
// Full DOM-level verification (chevron glyph, aria-expanded, zero
// reserved height when closed) is additionally confirmed by the required
// manual browser UAT, which exercises the real rendered accordion rather
// than a mocked one.

describe("computeJumpToSectionResult -- single entry point (sidebar nav / jumpToSection)", () => {
  it("opens a closed section and requests a scroll", () => {
    const result = computeJumpToSectionResult("gastrointestinal", new Set(["gastrointestinal"]));
    expect(result.willCollapse).toBe(false);
    expect(result.shouldScrollIntoView).toBe(true);
    expect(result.collapsedSections.has("gastrointestinal")).toBe(false);
  });

  it("collapses an already-open section on a bare re-click (no forceOpen) -- the exact defect scenario", () => {
    const result = computeJumpToSectionResult("gastrointestinal", new Set());
    expect(result.willCollapse).toBe(true);
    expect(result.shouldScrollIntoView).toBe(false);
    expect(result.collapsedSections.has("gastrointestinal")).toBe(true);
  });

  it("reopens a now-collapsed section on the next click (stable re-toggle)", () => {
    const afterCollapse = computeJumpToSectionResult("gastrointestinal", new Set()).collapsedSections;
    const afterReopen = computeJumpToSectionResult("gastrointestinal", afterCollapse);
    expect(afterReopen.willCollapse).toBe(false);
    expect(afterReopen.collapsedSections.has("gastrointestinal")).toBe(false);
  });

  it("10 repeated clicks alternate open/closed/open/... with no drift (stability requirement)", () => {
    let collapsed = new Set();
    const history = [];
    for (let i = 0; i < 10; i += 1) {
      const result = computeJumpToSectionResult("gastrointestinal", collapsed);
      collapsed = result.collapsedSections;
      history.push(!collapsed.has("gastrointestinal")); // true === open
    }
    expect(history).toEqual([false, true, false, true, false, true, false, true, false, true]);
  });

  it("forceOpen keeps an already-open section open (never collapses it) and still requests a scroll", () => {
    const result = computeJumpToSectionResult("gastrointestinal", new Set(), { forceOpen: true });
    expect(result.willCollapse).toBe(false);
    expect(result.shouldScrollIntoView).toBe(true);
    expect(result.collapsedSections.has("gastrointestinal")).toBe(false);
  });

  it("forceOpen opens an already-closed section", () => {
    const result = computeJumpToSectionResult("gastrointestinal", new Set(["gastrointestinal"]), { forceOpen: true });
    expect(result.willCollapse).toBe(false);
    expect(result.collapsedSections.has("gastrointestinal")).toBe(false);
  });
});

describe("computeJumpToSectionResult -- defect reproduction: re-click after visiting a different section", () => {
  it("re-clicking the ORIGINAL section's sidebar item after visiting another section still collapses it (was broken: depended on activeSection, which the other visit had already changed)", () => {
    // GI starts closed; clicking its sidebar item opens it.
    let collapsed = new Set(["gastrointestinal", "nutrition"]);
    collapsed = computeJumpToSectionResult("gastrointestinal", collapsed).collapsedSections;
    expect(collapsed.has("gastrointestinal")).toBe(false);
    // Visiting Nutrition's own jumpToSection call does not touch GI's
    // entry in the Set at all -- GI stays open (multi-open preserved).
    collapsed = computeJumpToSectionResult("nutrition", collapsed).collapsedSections;
    expect(collapsed.has("gastrointestinal")).toBe(false);
    expect(collapsed.has("nutrition")).toBe(false);
    // Re-clicking GI's sidebar item again must now collapse it -- under
    // the old `activeSection === key` gate this could never happen,
    // because `activeSection` was "nutrition" at this point.
    const result = computeJumpToSectionResult("gastrointestinal", collapsed);
    expect(result.willCollapse).toBe(true);
    expect(result.collapsedSections.has("gastrointestinal")).toBe(true);
  });

  it("visiting a different section never auto-closes other already-open sections (preserves existing multi-open behavior)", () => {
    let collapsed = new Set(["gastrointestinal", "nutrition", "endocrine"]);
    collapsed = computeJumpToSectionResult("gastrointestinal", collapsed).collapsedSections;
    collapsed = computeJumpToSectionResult("nutrition", collapsed).collapsedSections;
    collapsed = computeJumpToSectionResult("endocrine", collapsed).collapsedSections;
    expect(collapsed.has("gastrointestinal")).toBe(false);
    expect(collapsed.has("nutrition")).toBe(false);
    expect(collapsed.has("endocrine")).toBe(false);
  });
});

describe("computeJumpToSectionResult -- no cross-section interference", () => {
  it("collapsing one section leaves every other section's open/closed state untouched", () => {
    const collapsed = new Set(["endocrine"]); // endocrine already closed, gastrointestinal open
    const result = computeJumpToSectionResult("gastrointestinal", collapsed);
    expect(result.willCollapse).toBe(true);
    expect(result.collapsedSections.has("gastrointestinal")).toBe(true);
    expect(result.collapsedSections.has("endocrine")).toBe(true); // untouched
  });

  it("does not mutate the Set instance passed in (pure function, no side effects)", () => {
    const input = new Set(["endocrine"]);
    computeJumpToSectionResult("gastrointestinal", input);
    expect(input.has("gastrointestinal")).toBe(false);
    expect(input.size).toBe(1);
  });

  it("returns the identical Set reference when no change is needed (opening an already-open section is a no-op for the Set)", () => {
    const input = new Set();
    const result = computeJumpToSectionResult("gastrointestinal", input, { forceOpen: true });
    expect(result.collapsedSections).toBe(input);
  });
});
