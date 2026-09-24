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

  // Phase 3 -- J2053 manual symptom-impact capture (Option A,
  // docs/tenant-platform/J2053_SOURCE_OF_TRUTH_ANALYSIS.md). The completion
  // visit itself must expose manual capture controls for the same 8-field
  // vocabulary used by hopeReportMapper.js's IMPACT_MAP/IMPACT_KEYS.
  it("renders J2053 symptom-impact capture controls when an SFV is open on this visit", async () => {
    mocks.listSfvRequirements.mockResolvedValue([OPEN_REQUIREMENT]);
    render(
      <SymptomFollowUpVisitSection patientId="patient-1" visitId="visit-2" isFinalized={false} styles={STYLES} COLORS={COLORS} symptomImpact={{}} onSymptomImpactChange={() => {}} />
    );
    expect(await screen.findByText(/HOPE J2053/i)).toBeTruthy();
    expect(screen.getByText("Pain")).toBeTruthy();
    expect(screen.getByText("Shortness of Breath")).toBeTruthy();
    expect(screen.getByText("Agitation")).toBeTruthy();
  });

  it("renders J2053 symptom-impact capture controls when the SFV was already completed on this visit", async () => {
    mocks.listSfvRequirements.mockResolvedValue([
      { sfvRequirementId: "req-1", patientId: "patient-1", triggerVisitId: "trigger-visit-1", status: "COMPLETED", completionVisitId: "visit-2", completedAt: "2026-01-11T00:00:00Z" },
    ]);
    render(
      <SymptomFollowUpVisitSection patientId="patient-1" visitId="visit-2" isFinalized symptomImpact={{ pain: "2" }} onSymptomImpactChange={() => {}} styles={STYLES} COLORS={COLORS} />
    );
    expect(await screen.findByText(/HOPE J2053/i)).toBeTruthy();
  });

  it("calls onSymptomImpactChange with the updated symptom-impact map when a value is selected", async () => {
    mocks.listSfvRequirements.mockResolvedValue([OPEN_REQUIREMENT]);
    const onSymptomImpactChange = vi.fn();
    render(
      <SymptomFollowUpVisitSection patientId="patient-1" visitId="visit-2" isFinalized={false} styles={STYLES} COLORS={COLORS} symptomImpact={{}} onSymptomImpactChange={onSymptomImpactChange} />
    );
    await screen.findByText(/HOPE J2053/i);
    const painSelect = screen.getByLabelText("Pain");
    fireEvent.change(painSelect, { target: { value: "2" } });
    expect(onSymptomImpactChange).toHaveBeenCalledWith({ pain: "2" });
  });

  it("disables symptom-impact capture controls once the visit is finalized", async () => {
    mocks.listSfvRequirements.mockResolvedValue([
      { sfvRequirementId: "req-1", patientId: "patient-1", triggerVisitId: "trigger-visit-1", status: "COMPLETED", completionVisitId: "visit-2", completedAt: "2026-01-11T00:00:00Z" },
    ]);
    render(
      <SymptomFollowUpVisitSection patientId="patient-1" visitId="visit-2" isFinalized symptomImpact={{ pain: "2" }} onSymptomImpactChange={() => {}} styles={STYLES} COLORS={COLORS} />
    );
    const painSelect = await screen.findByLabelText("Pain");
    expect(painSelect.disabled).toBe(true);
  });
});
