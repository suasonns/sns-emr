import React from "react";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { SymptomFollowUpVisitSection } from "./VisitNotes";

const mocks = vi.hoisted(() => ({
  listSfvRequirements: vi.fn(),
  completeSfvRequirement: vi.fn(),
}));

vi.mock("../api/sfv", () => ({
  listSfvRequirements: mocks.listSfvRequirements,
  completeSfvRequirement: mocks.completeSfvRequirement,
  describeSfvError: (code) => `error:${code}`,
}));

const STYLES = {};
const COLORS = {};

const OPEN_REQUIREMENT = {
  sfvRequirementId: "req-1",
  patientId: "patient-1",
  triggerVisitId: "trigger-visit-1",
  status: "OPEN",
  dueAt: "2026-01-10T00:00:00Z",
  completionVisitId: null,
  completedAt: null,
};

describe("SymptomFollowUpVisitSection", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders nothing when there is no open requirement and nothing was completed on this visit", async () => {
    mocks.listSfvRequirements.mockResolvedValue([]);
    const { container } = render(
      <SymptomFollowUpVisitSection patientId="patient-1" visitId="visit-2" isFinalized={false} styles={STYLES} COLORS={COLORS} />
    );
    await waitFor(() => expect(mocks.listSfvRequirements).toHaveBeenCalledWith("patient-1"));
    await waitFor(() => expect(container.textContent).toBe(""));
  });

  it("disables the Complete SFV action until the current visit is finalized", async () => {
    mocks.listSfvRequirements.mockResolvedValue([OPEN_REQUIREMENT]);
    render(
      <SymptomFollowUpVisitSection patientId="patient-1" visitId="visit-2" isFinalized={false} styles={STYLES} COLORS={COLORS} />
    );

    const button = await screen.findByRole("button", { name: /complete sfv/i });
    expect(button.disabled).toBe(true);
    expect(mocks.completeSfvRequirement).not.toHaveBeenCalled();
  });

  it("calls the authoritative completion endpoint with the persisted visit id once finalized, and never sends clinician/tenant/patient identity", async () => {
    mocks.listSfvRequirements.mockResolvedValue([OPEN_REQUIREMENT]);
    mocks.completeSfvRequirement.mockResolvedValue({
      sfvRequirementId: "req-1",
      status: "COMPLETED",
      completionVisitId: "visit-2",
      completedAt: "2026-01-11T00:00:00Z",
    });

    render(
      <SymptomFollowUpVisitSection patientId="patient-1" visitId="visit-2" isFinalized styles={STYLES} COLORS={COLORS} />
    );

    const button = await screen.findByRole("button", { name: /complete sfv/i });
    expect(button.disabled).toBe(false);
    fireEvent.click(button);

    await waitFor(() => expect(mocks.completeSfvRequirement).toHaveBeenCalledWith("req-1", "visit-2"));
    expect(mocks.completeSfvRequirement.mock.calls[0]).toHaveLength(2);
    expect(await screen.findByText(/completed and recorded on this visit/i)).toBeTruthy();
  });

  it("surfaces the SAME_VISIT_NOT_ALLOWED error without marking the SFV completed in the UI", async () => {
    mocks.listSfvRequirements.mockResolvedValue([OPEN_REQUIREMENT]);
    mocks.completeSfvRequirement.mockRejectedValue({ code: "SAME_VISIT_NOT_ALLOWED", message: "same visit" });

    render(
      <SymptomFollowUpVisitSection patientId="patient-1" visitId="visit-2" isFinalized styles={STYLES} COLORS={COLORS} />
    );

    const button = await screen.findByRole("button", { name: /complete sfv/i });
    fireEvent.click(button);

    expect(await screen.findByText("error:SAME_VISIT_NOT_ALLOWED")).toBeTruthy();
    expect(screen.queryByText(/completed and recorded/i)).toBeNull();
  });
});
