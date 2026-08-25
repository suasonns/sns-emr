import React from "react";
import { render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import NoeTrackingPage from "./NoeTrackingPage";
import { deferred } from "../../test/testUtils";

const mocks = vi.hoisted(() => ({
  fetchNoeTracking: vi.fn(),
  useAgency: vi.fn(),
}));

vi.mock("../../api/dashboard", () => ({
  fetchNoeTracking: mocks.fetchNoeTracking,
}));

vi.mock("../../components/billing/AgencyContext", () => ({
  useAgency: mocks.useAgency,
}));

const today = new Date();
const electionDate = new Date(today);
electionDate.setDate(electionDate.getDate() - 4);
const dueDate = new Date(electionDate);
dueDate.setDate(dueDate.getDate() + 5);

const electionIso = electionDate.toISOString().slice(0, 10);
const dueIso = dueDate.toISOString().slice(0, 10);

describe("NoeTrackingPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mocks.useAgency.mockReturnValue({
      selectedAgencyId: "tenant-1",
      agencies: [],
      setSelectedAgencyId: vi.fn(),
      loading: false,
      error: null,
    });
  });

  it("shows a loading spinner before NOE data resolves", () => {
    const pending = deferred();
    mocks.fetchNoeTracking.mockReturnValue(pending.promise);

    render(<NoeTrackingPage />);

    expect(screen.getByRole("progressbar")).toBeTruthy();
  });

  it("renders deadline warning text and live NOE rows", async () => {
    mocks.fetchNoeTracking.mockResolvedValue({
      tenant_id: "tenant-1",
      count: 1,
      late_count: 0,
      unfiled_count: 1,
      noe_tracking: [
        {
          patient_id: "patient-1",
          patient_name: "Pat One",
          mrn: "MRN-100",
          benefit_period_id: "bp-1",
          election_date: electionIso,
          noe_submitted_date: null,
          noe_exception_reason: null,
          noe_filed: false,
          is_late: false,
          is_exempt: false,
          non_covered_start: null,
          non_covered_end: null,
          non_covered_days: null,
          penalty_reason: null,
        },
      ],
    });

    render(<NoeTrackingPage />);

    await screen.findByText(/approaching 5-day deadline/i);
    expect(screen.getByText("MRN-100")).toBeTruthy();
    expect(screen.getByText(dueIso)).toBeTruthy();
  });

  it("shows honest empty states when no benefit periods are returned", async () => {
    mocks.fetchNoeTracking.mockResolvedValue({
      tenant_id: "tenant-1",
      count: 0,
      late_count: 0,
      unfiled_count: 0,
      noe_tracking: [],
    });

    render(<NoeTrackingPage />);

    await screen.findByText("No initial benefit periods found for this agency.");
  });

  it("shows NOE load failures instead of fabricated compliance rows", async () => {
    mocks.fetchNoeTracking.mockRejectedValue(new Error("Unable to load NOE tracking."));

    render(<NoeTrackingPage />);

    await waitFor(() => {
      expect(screen.getByText("Unable to load NOE tracking.")).toBeTruthy();
    });
  });
});
