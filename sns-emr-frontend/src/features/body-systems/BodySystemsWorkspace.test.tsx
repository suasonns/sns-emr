import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, within, waitFor } from "@testing-library/react";
import { BodySystemsWorkspace } from "./components/BodySystemsWorkspace";
import { syntheticComprehensiveAssessmentFixture } from "./fixtures/comprehensiveAssessment.fixture";
import { BODY_SYSTEMS, BODY_SYSTEM_LABELS } from "../../domain/body-systems";

// This repository does not have `@testing-library/user-event` or
// `jest-dom` installed (confirmed during pre-edit investigation), and the
// existing test suite's convention is `fireEvent` + plain `screen`
// queries (which throw if an element is missing) rather than
// `toBeInTheDocument()`. These tests follow that same convention rather
// than introducing a new dependency.

// Respiratory's panel calls the real Respiratory API
// (`src/api/bodySystems.ts`) — mocked here so these workspace-level tests
// never make a network call and stay in full control of the load state.
const mocks = vi.hoisted(() => ({
  getRespiratoryAssessment: vi.fn(),
  saveRespiratoryDraft: vi.fn(),
}));

vi.mock("../../api/bodySystems", async () => {
  const actual = await vi.importActual<typeof import("../../api/bodySystems")>("../../api/bodySystems");
  return {
    ...actual,
    getRespiratoryAssessment: mocks.getRespiratoryAssessment,
    saveRespiratoryDraft: mocks.saveRespiratoryDraft,
  };
});

const TEST_PATIENT_ID = "11111111-1111-1111-1111-111111111111";

beforeEach(() => {
  mocks.getRespiratoryAssessment.mockReset();
  mocks.saveRespiratoryDraft.mockReset();
  // Default: Respiratory load never resolves within these tests unless a
  // specific test overrides it — keeps the other-nine-systems assertions
  // unaffected by Respiratory's async load state.
  mocks.getRespiratoryAssessment.mockReturnValue(new Promise(() => {}));
});

function renderWorkspace() {
  return render(
    <BodySystemsWorkspace fixture={syntheticComprehensiveAssessmentFixture} patientId={TEST_PATIENT_ID} />,
  );
}

/** The system label also appears on the accordion trigger button, so
 * navigation-item lookups must be scoped to the `<nav>` to stay unambiguous. */
function clickNavSystem(name: string | RegExp) {
  const nav = screen.getByRole("navigation", { name: "Body systems" });
  fireEvent.click(within(nav).getByRole("button", { name }));
}

/** Review state badges and situation text repeat per row (nav + register),
 * so row-level assertions scope to that row's register trigger button. */
function getRegisterTrigger(name: string | RegExp) {
  const register = screen.getByTestId("body-systems-register");
  return within(register).getByRole("button", { name });
}

describe("BodySystemsWorkspace — canonical systems and labels", () => {
  it("renders all ten canonical body systems in the canonical fixed order", () => {
    renderWorkspace();
    const nav = screen.getByRole("navigation", { name: "Body systems" });
    const buttons = within(nav).getAllByRole("button");
    expect(buttons).toHaveLength(BODY_SYSTEMS.length);
    buttons.forEach((button, index) => {
      expect(button.textContent).toContain(BODY_SYSTEM_LABELS[BODY_SYSTEMS[index]]);
    });
  });

  it("uses the canonical label 'Infection / Immunological', never the legacy label 'Infection'", () => {
    renderWorkspace();
    expect(screen.getAllByText("Infection / Immunological").length).toBeGreaterThan(0);
    expect(screen.queryByText("Infection", { exact: true })).toBeNull();
  });

  it("uses the canonical label 'Integumentary', never the legacy label 'Skin'", () => {
    renderWorkspace();
    expect(screen.getAllByText("Integumentary").length).toBeGreaterThan(0);
    expect(screen.queryByText("Skin", { exact: true })).toBeNull();
  });
});

describe("BodySystemsWorkspace — visit mode presentation", () => {
  it("shows Admission / Comprehensive as the active mode", () => {
    renderWorkspace();
    const active = screen.getByText("Admission / Comprehensive");
    expect(active.getAttribute("aria-current")).toBe("true");
  });

  it("shows Routine RN Visit and Recertification as noninteractive preview labels only", () => {
    renderWorkspace();
    const routine = screen.getByText("Routine RN Visit");
    const recert = screen.getByText("Recertification");
    expect(routine.getAttribute("aria-disabled")).toBe("true");
    expect(recert.getAttribute("aria-disabled")).toBe("true");
    expect(routine.tagName).not.toBe("BUTTON");
    expect(recert.tagName).not.toBe("BUTTON");
  });
});

describe("BodySystemsWorkspace — synthetic data notice", () => {
  it("always displays the synthetic/read-only notice", () => {
    renderWorkspace();
    expect(screen.getByText("Synthetic read-only UI preview")).toBeTruthy();
    expect(screen.getByText("No patient record is loaded. No clinical documentation is saved.")).toBeTruthy();
  });
});

describe("BodySystemsWorkspace — review progress", () => {
  it("derives review progress only from reviewed + reviewed_with_exception rows, shown as separate state counts", () => {
    renderWorkspace();
    // Fixture: reviewed=5 (neurological, respiratory, genitourinary,
    // musculoskeletal, infection_immunological), reviewed_with_exception=2
    // (cardiovascular, integumentary), in_progress=1 (nutrition),
    // not_reviewed=2 (gastrointestinal, endocrine) => 7 of 10 count toward
    // progress (70%). The four states are always rendered as separate
    // counts, never collapsed into a single "x / 10 reviewed" summary.
    expect(screen.getByText("Review progress")).toBeTruthy();
    expect(screen.getByText("Reviewed: 5")).toBeTruthy();
    expect(screen.getByText("Reviewed with exception: 2")).toBeTruthy();
    expect(screen.getByText("In progress: 1")).toBeTruthy();
    expect(screen.getByText("Not reviewed: 2")).toBeTruthy();
    expect(screen.getByRole("progressbar", { name: "Review progress" })).toBeTruthy();
  });
});

describe("BodySystemsWorkspace — review-state badges only (no situation presentation)", () => {
  it("renders Cardiovascular's review-state badge in both the navigation and the register row", () => {
    renderWorkspace();
    const nav = screen.getByRole("navigation", { name: "Body systems" });
    expect(within(nav).getByRole("button", { name: /Cardiovascular/ })).toBeTruthy();

    const trigger = getRegisterTrigger(/Cardiovascular/);
    expect(within(trigger).getByText("Reviewed with exception")).toBeTruthy();
  });

  it("renders an unreviewed system's badge as 'Not reviewed' only, with no additional situation text", () => {
    renderWorkspace();
    const trigger = getRegisterTrigger(/Gastrointestinal/);
    expect(within(trigger).getByText("Not reviewed")).toBeTruthy();
  });
});

describe("BodySystemsWorkspace — selection and the generic read-only placeholder", () => {
  it("selecting a system in the navigation expands that system's register row to the fixed read-only placeholder", () => {
    renderWorkspace();
    clickNavSystem(/Cardiovascular/);
    expect(screen.getByText("Read-only synthetic register preview")).toBeTruthy();
  });

  it("selecting a different system collapses the previously expanded one (one expanded system at a time)", () => {
    renderWorkspace();
    clickNavSystem(/Cardiovascular/);
    const cardiovascularTrigger = getRegisterTrigger(/Cardiovascular/);
    expect(cardiovascularTrigger.getAttribute("aria-expanded")).toBe("true");

    clickNavSystem(/Neurological/);
    expect(cardiovascularTrigger.getAttribute("aria-expanded")).toBe("false");
    const neurologicalTrigger = getRegisterTrigger(/Neurological/);
    expect(neurologicalTrigger.getAttribute("aria-expanded")).toBe("true");
  });

  it("renders only one generic, fixed, neutral placeholder for every system (no specialized per-system detail layout)", () => {
    renderWorkspace();
    clickNavSystem(/Musculoskeletal/);
    expect(screen.getAllByText("Read-only synthetic register preview")).toHaveLength(1);
  });
});

const NON_RESPIRATORY_SYSTEMS = BODY_SYSTEMS.filter((system) => system !== "respiratory");

describe("BodySystemsWorkspace — the remaining nine systems have no deferred-milestone content", () => {
  it("renders no clinical-detail, assessment-situation, or review-exception panel content for any system except Respiratory", () => {
    renderWorkspace();
    NON_RESPIRATORY_SYSTEMS.forEach((system) => {
      clickNavSystem(new RegExp(BODY_SYSTEM_LABELS[system]));
    });
    expect(screen.queryByText(/Current baseline evidence/)).toBeNull();
    expect(screen.queryByText(/Historical reference/)).toBeNull();
    expect(screen.queryByText(/Review items/)).toBeNull();
    expect(screen.queryByText(/New or worsening/)).toBeNull();
    expect(screen.queryByText(/Not yet determined/)).toBeNull();
    expect(screen.queryByTestId("respiratory-panel")).toBeNull();
  });

  it("renders no save, submit, sign, finalize, or approve controls for any system except Respiratory", () => {
    renderWorkspace();
    NON_RESPIRATORY_SYSTEMS.forEach((system) => {
      clickNavSystem(new RegExp(BODY_SYSTEM_LABELS[system]));
    });
    expect(screen.queryByRole("button", { name: /save|submit|sign|finalize|approve/i })).toBeNull();
  });

  it("renders no text input, textarea, or checkbox for any system except Respiratory", () => {
    const { container } = renderWorkspace();
    NON_RESPIRATORY_SYSTEMS.forEach((system) => {
      clickNavSystem(new RegExp(BODY_SYSTEM_LABELS[system]));
    });
    expect(container.querySelectorAll("input, textarea").length).toBe(0);
  });

  it("every navigation item is a real, natively keyboard-operable <button> element", () => {
    renderWorkspace();
    const nav = screen.getByRole("navigation", { name: "Body systems" });
    within(nav)
      .getAllByRole("button")
      .forEach((button) => expect(button.tagName).toBe("BUTTON"));
  });
});

describe("BodySystemsWorkspace — Respiratory proof-of-pattern expansion", () => {
  it("renders the real Respiratory detail panel, calling the Respiratory API for the supplied patientId", async () => {
    mocks.getRespiratoryAssessment.mockResolvedValueOnce({
      id: "sa-1",
      bodySystemsAssessmentId: "bsa-1",
      assessmentStatus: "draft",
      system: "respiratory",
      situation: null,
      reviewState: "not_reviewed",
      data: {},
      summary: null,
      version: 1,
      updatedAt: null,
      openReviewExceptions: [],
    });
    renderWorkspace();
    clickNavSystem(/Respiratory/);
    await waitFor(() => expect(screen.getByTestId("respiratory-panel")).toBeTruthy());
    expect(mocks.getRespiratoryAssessment).toHaveBeenCalledWith(TEST_PATIENT_ID);
  });

  it("selecting another system after Respiratory does not leave the Respiratory panel mounted", async () => {
    mocks.getRespiratoryAssessment.mockResolvedValueOnce({
      id: "sa-1",
      bodySystemsAssessmentId: "bsa-1",
      assessmentStatus: "draft",
      system: "respiratory",
      situation: null,
      reviewState: "not_reviewed",
      data: {},
      summary: null,
      version: 1,
      updatedAt: null,
      openReviewExceptions: [],
    });
    renderWorkspace();
    clickNavSystem(/Respiratory/);
    await waitFor(() => expect(screen.getByTestId("respiratory-panel")).toBeTruthy());
    clickNavSystem(/Neurological/);
    expect(screen.queryByTestId("respiratory-panel")).toBeNull();
    expect(screen.getByText("Read-only synthetic register preview")).toBeTruthy();
  });
});
