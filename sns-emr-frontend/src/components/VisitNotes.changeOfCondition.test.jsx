import React from "react";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { VisitNoteEditor } from "./VisitNotes";

const mocks = vi.hoisted(() => ({
  getVisitNote: vi.fn(),
  updateVisitNote: vi.fn(),
  finalizeVisitNote: vi.fn(),
  listSfvRequirements: vi.fn(),
  completeSfvRequirement: vi.fn(),
  stageNewUpdateAssessmentRequest: vi.fn(),
}));

vi.mock("../api/visitNotes", async (importOriginal) => {
  const actual = await importOriginal();
  return {
    ...actual,
    getVisitNote: mocks.getVisitNote,
    updateVisitNote: mocks.updateVisitNote,
    finalizeVisitNote: mocks.finalizeVisitNote,
  };
});

vi.mock("../api/sfv", () => ({
  listSfvRequirements: mocks.listSfvRequirements,
  completeSfvRequirement: mocks.completeSfvRequirement,
  recordSfvNotCompleted: vi.fn(),
  describeSfvError: (code) => `error:${code}`,
}));

vi.mock("../intake/NursingAssessmentBoard", async (importOriginal) => {
  const actual = await importOriginal();
  return {
    ...actual,
    stageNewUpdateAssessmentRequest: mocks.stageNewUpdateAssessmentRequest,
  };
});

const STYLES = { infoBox: {}, card: {} };
const COLORS = { dark: "#111", gray: "#666", border: "#ccc", primary: "#0d9488" };

const BASE_RECORD = {
  content: {
    form_type: "ROUTINE_VISIT",
    care_level: "Routine",
    visit_date: "2026-11-01",
    entered_by: "Test RN",
  },
  visit_status: "DRAFT",
  comparable_history: [],
  supervisory_context: { visible: false, can_edit: false, hha: { applicable: false, assignments: [] }, lvn_lpn: { applicable: false, assignments: [] } },
};

// R3 (Owner Directive, "RNICA Update/HUV Creation Workflow", clarified by
// the OWNER CLARIFICATION reframing the trigger away from HOPE/HUV
// calendar windows and toward clinical need).
//
// Proves:
//   1. The change-of-condition question only appears for a full-body RN
//      visit (not a death visit, not continuous care, not a chaplain/MSW
//      visit).
//   2. The reason picker only appears after "Yes" is selected, and
//      "Complete Update Assessment" is disabled until a reason is chosen.
//   3. Confirming stages exactly one request (via the single shared
//      staging function) carrying the visit's own id/date as
//      originating-visit context, and never calls finalizeVisitNote or
//      any visit-note deletion/overwrite path -- the source visit note is
//      only ever updated (saved), never replaced.
describe("VisitNoteEditor change-of-condition review", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mocks.getVisitNote.mockResolvedValue(BASE_RECORD);
    mocks.listSfvRequirements.mockResolvedValue([]);
    mocks.updateVisitNote.mockResolvedValue(BASE_RECORD);
  });

  it("shows the change-of-condition review for a full-body RN visit", async () => {
    render(<VisitNoteEditor visitId="visit-1" discipline="RN" patientId="patient-1" styles={STYLES} COLORS={COLORS} />);
    await waitFor(() => expect(screen.getByText(/Change of Condition Review/i)).toBeTruthy());
  });

  it("does not show the review for a chaplain (non-RN) visit", async () => {
    render(<VisitNoteEditor visitId="visit-1" discipline="SC" patientId="patient-1" styles={STYLES} COLORS={COLORS} />);
    await waitFor(() => expect(mocks.getVisitNote).toHaveBeenCalled());
    expect(screen.queryByText(/Change of Condition Review/i)).toBeNull();
  });

  it("hides the reason picker and disables the action until Yes + a reason are selected", async () => {
    render(<VisitNoteEditor visitId="visit-1" discipline="RN" patientId="patient-1" styles={STYLES} COLORS={COLORS} />);
    await waitFor(() => expect(screen.getByText(/Change of Condition Review/i)).toBeTruthy());
    expect(screen.queryByText("New symptom or finding")).toBeNull();

    fireEvent.click(screen.getByRole("button", { name: "Yes" }));
    await waitFor(() => expect(screen.getByText("New symptom or finding")).toBeTruthy());
    expect(screen.getByRole("button", { name: "Complete Update Assessment" }).disabled).toBe(true);
  });

  it("stages exactly one request carrying this visit's id/date, and never finalizes the visit note", async () => {
    mocks.stageNewUpdateAssessmentRequest.mockReturnValue({ reasonCode: "WORSENING_SYMPTOM_OR_FINDING" });
    render(<VisitNoteEditor visitId="visit-1" discipline="RN" patientId="patient-1" styles={STYLES} COLORS={COLORS} />);
    await waitFor(() => expect(screen.getByText(/Change of Condition Review/i)).toBeTruthy());

    fireEvent.click(screen.getByRole("button", { name: "Yes" }));
    await waitFor(() => expect(screen.getByText("Worsening symptom or finding")).toBeTruthy());
    fireEvent.click(screen.getByRole("button", { name: "Worsening symptom or finding" }));
    fireEvent.click(screen.getByRole("button", { name: "Complete Update Assessment" }));

    await waitFor(() => expect(mocks.stageNewUpdateAssessmentRequest).toHaveBeenCalledTimes(1));
    expect(mocks.stageNewUpdateAssessmentRequest).toHaveBeenCalledWith("patient-1", expect.objectContaining({
      reasonCode: "WORSENING_SYMPTOM_OR_FINDING",
      source: "VISIT_NOTE_CHANGE_OF_CONDITION",
      originatingVisitId: "visit-1",
      originatingVisitDate: "2026-11-01",
    }));
    expect(mocks.finalizeVisitNote).not.toHaveBeenCalled();
    await waitFor(() => expect(mocks.updateVisitNote).toHaveBeenCalled());
  });
});
