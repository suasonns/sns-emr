import React from "react";
import { render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import BillingOverviewPage from "./BillingOverviewPage";
import { deferred } from "../../test/testUtils";

const mocks = vi.hoisted(() => ({
  fetchTenantBillingReadinessReport: vi.fn(),
  fetchClaimLifecycle: vi.fn(),
  useAgency: vi.fn(),
}));

vi.mock("../../api/dashboard", () => ({
  fetchTenantBillingReadinessReport: mocks.fetchTenantBillingReadinessReport,
  fetchClaimLifecycle: mocks.fetchClaimLifecycle,
}));

vi.mock("../../components/billing/AgencyContext", () => ({
  useAgency: mocks.useAgency,
}));

describe("BillingOverviewPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mocks.useAgency.mockReturnValue({
      selectedAgencyId: "tenant-1",
      agencies: [{ tenant_id: "tenant-1", display_name: "Alpha Hospice", legal_name: "Alpha Hospice" }],
      setSelectedAgencyId: vi.fn(),
      loading: false,
      error: null,
    });
  });

  it("shows a loading spinner while the billing dashboard feeds resolve", () => {
    const readiness = deferred();
    const lifecycle = deferred();
    mocks.fetchTenantBillingReadinessReport.mockReturnValue(readiness.promise);
    mocks.fetchClaimLifecycle.mockReturnValue(lifecycle.promise);

    render(<BillingOverviewPage />);

    expect(screen.getByRole("progressbar")).toBeTruthy();
  });

  it("renders blocker breakdown and lifecycle counts from the live billing data", async () => {
    mocks.fetchTenantBillingReadinessReport.mockResolvedValue({
      tenant_id: "tenant-1",
      service_date: "2026-08-24",
      total_patients: 2,
      ready_count: 1,
      not_ready_count: 1,
      patients: [
        {
          patient_id: "patient-1",
          mrn: "MRN-100",
          period_number: 1,
          ready: false,
          blockers: [
            "No benefit period covers 2026-08-24",
            "Required face-to-face encounter is missing",
          ],
          warnings: [],
        },
      ],
    });
    mocks.fetchClaimLifecycle.mockResolvedValue({
      metrics: [],
      ready: 2,
      sent: 1,
      accepted: 4,
      paid: 3,
      denied: 1,
    });

    render(<BillingOverviewPage />);

    await screen.findByText(/Billing Dashboard/i);
    expect(screen.getAllByText(/Alpha Hospice/i).length).toBeGreaterThan(0);
    expect(screen.getByText("Missing Benefit Period")).toBeTruthy();
    expect(screen.getByText("Missing F2F Documentation")).toBeTruthy();
    expect(screen.getByText(/claims lifecycle snapshot/i)).toBeTruthy();
    expect(screen.getByText(/Accepted & Validated/i)).toBeTruthy();
  });

  it("shows honest empty states when there are no blockers or lifecycle rows", async () => {
    mocks.fetchTenantBillingReadinessReport.mockResolvedValue({
      tenant_id: "tenant-1",
      service_date: "2026-08-24",
      total_patients: 0,
      ready_count: 0,
      not_ready_count: 0,
      patients: [],
    });
    mocks.fetchClaimLifecycle.mockResolvedValue(null);

    render(<BillingOverviewPage />);

    await screen.findByText("No unresolved billing blockers for this agency.");
    expect(screen.getByText("No claim lifecycle data available.")).toBeTruthy();
  });

  it("surfaces readiness load failures instead of silently inventing fallback data", async () => {
    mocks.fetchTenantBillingReadinessReport.mockRejectedValue(new Error("Unable to load billing readiness."));
    mocks.fetchClaimLifecycle.mockResolvedValue({ metrics: [], ready: 0, sent: 0, accepted: 0, paid: 0, denied: 0 });

    render(<BillingOverviewPage />);

    await waitFor(() => {
      expect(screen.getByText("Unable to load billing readiness.")).toBeTruthy();
    });
  });
});
