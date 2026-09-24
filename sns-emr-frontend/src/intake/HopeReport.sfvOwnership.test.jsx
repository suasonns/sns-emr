import React from "react";
import { render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import HopeReport from "./HopeReport";
import { ThemeModeProvider } from "../theme/theme";

// SFV ownership remediation (docs/tenant-platform/
// P0_SFV_OWNERSHIP_REMEDIATION.md, SFV_TRIGGER_OWNERSHIP_TRACE.md,
// SFV_OWNERSHIP_TRACE.md): these tests exercise the acceptance-test
// scenarios that were proven FAILING under the prior patient-wide
// "most recently completed SFV" selection, and must PASS now that
// selection is scoped to (triggerSourceType, triggerVisitId).

const mocks = vi.hoisted(() => ({
  listSfvRequirements: vi.fn(),
}));

vi.mock("../api/sfv", () => ({
  listSfvRequirements: mocks.listSfvRequirements,
}));

vi.mock("../api/icaAssessments", () => ({
  closeRnicaHopeWorkflow: vi.fn(),
  exportRnicaHopeWorkflow: vi.fn(),
  patchRnicaHopeInactivation: vi.fn(),
  patchRnicaHopeSubmission: vi.fn(),
  readyRnicaHopeWorkflow: vi.fn(),
  unlockRnicaHopeWorkflow: vi.fn(),
}));

// One completed SFVRequirement per timepoint, each with a distinguishable
// J2053 Pain value ("1 - Slight" / "2 - Moderate" / "3 - Severe") so the
// rendered report can be asserted against unambiguously. completedAt is
// intentionally in REVERSE chronological order of trigger (HUV2's SFV
// completed BEFORE HUV1's, which completed BEFORE ADM's) -- this is the
// exact shape that defeated the old "most recently completed" sort,
// since under that rule the ADM export would have incorrectly won every
// other export too.
const SFV_ADM = {
  sfvRequirementId: "sfv-adm",
  patientId: "patient-1",
  triggerVisitId: "visit-adm",
  triggerSourceType: "INITIAL_RN_ICA",
  status: "COMPLETED",
  completedAt: "2026-03-03T00:00:00Z",
  symptomImpact: { pain: "1" },
};

const SFV_HUV1 = {
  sfvRequirementId: "sfv-huv1",
  patientId: "patient-1",
  triggerVisitId: "visit-huv1",
  triggerSourceType: "HUV1",
  status: "COMPLETED",
  completedAt: "2026-03-02T00:00:00Z",
  symptomImpact: { pain: "2" },
};

const SFV_HUV2 = {
  sfvRequirementId: "sfv-huv2",
  patientId: "patient-1",
  triggerVisitId: "visit-huv2",
  triggerSourceType: "HUV2",
  status: "COMPLETED",
  completedAt: "2026-03-01T00:00:00Z",
  symptomImpact: { pain: "3" },
};

function renderHopeReport({ timepoint, visitId }) {
  return render(
    <ThemeModeProvider>
      <HopeReport
        formData={{}}
        patient={{ firstName: "Test", lastName: "Patient" }}
        agency={{}}
        timepoint={timepoint}
        assessmentMeta={{ assessmentId: "assessment-1", locked: true, visitId }}
        patientId="patient-1"
      />
    </ThemeModeProvider>
  );
}

async function findJ2053PainEntryValue() {
  const labels = await screen.findAllByText(/^A\. Pain$/);
  // J2051 ("Symptom Impact") and J2053 ("SFV Symptom Impact") both use the
  // same symptomEntries() labels -- J2053 is always the second occurrence
  // since it is rendered after J2051 in Section J.
  const j2053Label = labels[labels.length - 1];
  const entry = j2053Label.parentElement;
  return entry ? entry.textContent : "";
}

describe("HopeReport SFV ownership", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mocks.listSfvRequirements.mockResolvedValue([SFV_ADM, SFV_HUV1, SFV_HUV2]);
  });

  it("CASE A: ADM export uses SFV A (triggerVisitId=visit-adm), never SFV B/C", async () => {
    renderHopeReport({ timepoint: "ADMISSION", visitId: "visit-adm" });
    await waitFor(() => expect(mocks.listSfvRequirements).toHaveBeenCalledWith("patient-1"));
    const text = await findJ2053PainEntryValue();
    expect(text).toContain("1 - Slight");
    expect(text).not.toContain("2 - Moderate");
    expect(text).not.toContain("3 - Severe");
  });

  it("CASE B: HUV1 export uses SFV B (triggerVisitId=visit-huv1), never SFV A", async () => {
    renderHopeReport({ timepoint: "HUV1", visitId: "visit-huv1" });
    await waitFor(() => expect(mocks.listSfvRequirements).toHaveBeenCalledWith("patient-1"));
    const text = await findJ2053PainEntryValue();
    expect(text).toContain("2 - Moderate");
    expect(text).not.toContain("1 - Slight");
    expect(text).not.toContain("3 - Severe");
  });

  it("CASE C: HUV2 export uses SFV C (triggerVisitId=visit-huv2), never SFV A/B", async () => {
    renderHopeReport({ timepoint: "HUV2", visitId: "visit-huv2" });
    await waitFor(() => expect(mocks.listSfvRequirements).toHaveBeenCalledWith("patient-1"));
    const text = await findJ2053PainEntryValue();
    expect(text).toContain("3 - Severe");
    expect(text).not.toContain("1 - Slight");
    expect(text).not.toContain("2 - Moderate");
  });

  it("does not fall back to any SFV when no requirement matches this record's own trigger", async () => {
    renderHopeReport({ timepoint: "ADMISSION", visitId: "visit-unrelated" });
    await waitFor(() => expect(mocks.listSfvRequirements).toHaveBeenCalledWith("patient-1"));
    const text = await findJ2053PainEntryValue();
    expect(text).not.toContain("1 - Slight");
    expect(text).not.toContain("2 - Moderate");
    expect(text).not.toContain("3 - Severe");
  });

  it("never performs the lookup at all for Discharge (no J2052/J2053 in scope)", async () => {
    renderHopeReport({ timepoint: "DISCHARGE", visitId: "visit-adm" });
    await waitFor(() => expect(screen.getByText(/HOPE REPORT - Discharge/i)).toBeTruthy());
    expect(mocks.listSfvRequirements).not.toHaveBeenCalled();
  });
});
