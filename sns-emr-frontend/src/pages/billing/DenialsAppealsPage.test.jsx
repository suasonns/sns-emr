import React from "react";
import { render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import DenialsAppealsPage from "./DenialsAppealsPage";
import { deferred } from "../../test/testUtils";

const mocks = vi.hoisted(() => ({
  fetchDenials: vi.fn(),
  useAgency: vi.fn(),
}));

vi.mock("../../api/dashboard", () => ({
  fetchDenials: mocks.fetchDenials,
}));

vi.mock("../../components/billing/AgencyContext", () => ({
  useAgency: mocks.useAgency,
}));

describe("DenialsAppealsPage", () => {
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

  it("shows a loading spinner before denials load", () => {
    const pending = deferred();
    mocks.fetchDenials.mockReturnValue(pending.promise);

    render(<DenialsAppealsPage />);

    expect(screen.getByRole("progressbar")).toBeTruthy();
  });

  it("renders denial reason breakdown and registry rows from live mocked data", async () => {
    mocks.fetchDenials.mockResolvedValue({
      tenant_id: "tenant-1",
      count: 1,
      total_denials: 1,
      appeals_filed: 1,
      appeal_rate: 100,
      overturn_rate: 50,
      avg_resolution_days: 12,
      reason_breakdown: [{ reason: "Authorization missing", count: 1, percent: 100 }],
      denials: [
        {
          denial_id: "denial-1",
          claim_id: "claim-1",
          patient_id: "patient-1",
          patient_name: "Pat One",
          mrn: "MRN-100",
          payer_name: "Medicare",
          denial_date: "2026-08-15",
          carc_code: "CO-16",
          reason_description: "Authorization missing",
          denied_amount: 500,
          status: "OPEN",
          appeal_status_label: "In Review",
          appeal_deadline: "2026-09-01",
          days_elapsed: 10,
        },
      ],
    });

    render(<DenialsAppealsPage />);

    await screen.findAllByText("Authorization missing");
    expect(screen.getByText("Pat One")).toBeTruthy();
    expect(screen.getByText("$500.00")).toBeTruthy();
    expect(screen.getByText("Showing 1 of 1 denial records")).toBeTruthy();
  });

  it("shows an honest empty state when there are no denials", async () => {
    mocks.fetchDenials.mockResolvedValue({
      tenant_id: "tenant-1",
      count: 0,
      total_denials: 0,
      appeals_filed: 0,
      appeal_rate: null,
      overturn_rate: null,
      avg_resolution_days: null,
      reason_breakdown: [],
      denials: [],
    });

    render(<DenialsAppealsPage />);

    await screen.findByText("No denials on file.");
    expect(screen.getByText("No denial records found for this agency.")).toBeTruthy();
  });

  it("shows denial load failures instead of fallback rows", async () => {
    mocks.fetchDenials.mockRejectedValue(new Error("Unable to load denials."));

    render(<DenialsAppealsPage />);

    await waitFor(() => {
      expect(screen.getByText("Unable to load denials.")).toBeTruthy();
    });
  });
});
