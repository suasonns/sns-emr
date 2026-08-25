import React from "react";
import { render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import ClaimsManagementPage from "./ClaimsManagementPage";
import { deferred } from "../../test/testUtils";

const mocks = vi.hoisted(() => ({
  fetchClaims: vi.fn(),
  useAgency: vi.fn(),
}));

vi.mock("../../api/dashboard", () => ({
  fetchClaims: mocks.fetchClaims,
}));

vi.mock("../../components/billing/AgencyContext", () => ({
  useAgency: mocks.useAgency,
}));

describe("ClaimsManagementPage", () => {
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

  it("shows a loading spinner before claims resolve", () => {
    const pending = deferred();
    mocks.fetchClaims.mockReturnValue(pending.promise);

    render(<ClaimsManagementPage />);

    expect(screen.getByRole("progressbar")).toBeTruthy();
  });

  it("renders claim rows from the mocked claims API", async () => {
    mocks.fetchClaims.mockResolvedValue({
      tenant_id: "tenant-1",
      count: 1,
      total_claims: 1,
      submitted_count: 1,
      accepted_count: 0,
      denied_count: 0,
      lifecycle: { draft: 0, submitted: 1, accepted: 0, paid: 0, denied: 0 },
      claims: [
        {
          claim_id: "claim-1001",
          patient_id: "patient-1",
          patient_name: "Pat One",
          mrn: "MRN-100",
          payer_name: "Medicare",
          service_date: "2026-08-20",
          total_charge: 1250,
          total_units: 4,
          status: "SENT",
          claim_control_number: "CCN-1001",
          last_status_reason: null,
          created_at: "2026-08-20T00:00:00Z",
          days_in_status: 3,
        },
      ],
    });

    render(<ClaimsManagementPage />);

    await screen.findByText("CCN-1001");
    expect(screen.getByText("Pat One")).toBeTruthy();
    expect(screen.getByText("$1,250.00")).toBeTruthy();
    expect(screen.getByText("Showing 1 of 1 claims")).toBeTruthy();
  });

  it("shows an honest empty state when no claims are returned", async () => {
    mocks.fetchClaims.mockResolvedValue({
      tenant_id: "tenant-1",
      count: 0,
      total_claims: 0,
      submitted_count: 0,
      accepted_count: 0,
      denied_count: 0,
      lifecycle: { draft: 0, submitted: 0, accepted: 0, paid: 0, denied: 0 },
      claims: [],
    });

    render(<ClaimsManagementPage />);

    await screen.findByText("No claims found for this agency.");
  });

  it("shows live API failures instead of fake claims", async () => {
    mocks.fetchClaims.mockRejectedValue(new Error("Unable to load claims."));

    render(<ClaimsManagementPage />);

    await waitFor(() => {
      expect(screen.getByText("Unable to load claims.")).toBeTruthy();
    });
  });
});
