import React from "react";
import { render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import ReportsPage from "./ReportsPage";
import { deferred } from "../../test/testUtils";

const mocks = vi.hoisted(() => ({
  fetchTenantBillingReadinessReport: vi.fn(),
  fetchClaims: vi.fn(),
  fetchDenials: vi.fn(),
  fetchEligibilityRoster: vi.fn(),
  fetchRemittances: vi.fn(),
  fetchHospiceCapRecord: vi.fn(),
  upsertHospiceCapRecord: vi.fn(),
  useAgency: vi.fn(),
}));

vi.mock("../../api/dashboard", () => ({
  fetchTenantBillingReadinessReport: mocks.fetchTenantBillingReadinessReport,
  fetchClaims: mocks.fetchClaims,
  fetchDenials: mocks.fetchDenials,
  fetchEligibilityRoster: mocks.fetchEligibilityRoster,
  fetchRemittances: mocks.fetchRemittances,
}));

vi.mock("../../api/hospiceCap", () => ({
  fetchHospiceCapRecord: mocks.fetchHospiceCapRecord,
  upsertHospiceCapRecord: mocks.upsertHospiceCapRecord,
}));

vi.mock("../../components/billing/AgencyContext", () => ({
  useAgency: mocks.useAgency,
}));

describe("ReportsPage", () => {
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

  it("shows a loading spinner while report feeds resolve", () => {
    const pending = deferred();
    mocks.fetchTenantBillingReadinessReport.mockReturnValue(pending.promise);
    mocks.fetchClaims.mockReturnValue(pending.promise);
    mocks.fetchDenials.mockReturnValue(pending.promise);
    mocks.fetchEligibilityRoster.mockReturnValue(pending.promise);
    mocks.fetchRemittances.mockReturnValue(pending.promise);
    mocks.fetchHospiceCapRecord.mockReturnValue(pending.promise);

    render(<ReportsPage />);

    expect(screen.getByRole("progressbar")).toBeTruthy();
  });

  it("renders live report snapshot cards from the mocked billing feeds", async () => {
    mocks.fetchTenantBillingReadinessReport.mockResolvedValue({
      tenant_id: "tenant-1",
      service_date: "2026-08-24",
      total_patients: 4,
      ready_count: 3,
      not_ready_count: 1,
      patients: [],
    });
    mocks.fetchClaims.mockResolvedValue({
      tenant_id: "tenant-1",
      count: 1,
      total_claims: 12,
      submitted_count: 5,
      accepted_count: 4,
      denied_count: 1,
      lifecycle: { draft: 2, submitted: 5, accepted: 4, paid: 1, denied: 1 },
      claims: [],
    });
    mocks.fetchDenials.mockResolvedValue({
      tenant_id: "tenant-1",
      count: 1,
      total_denials: 2,
      appeals_filed: 1,
      appeal_rate: 50,
      overturn_rate: 100,
      avg_resolution_days: 7,
      reason_breakdown: [],
      denials: [],
    });
    mocks.fetchEligibilityRoster.mockResolvedValue({
      tenant_id: "tenant-1",
      count: 1,
      total_active: 4,
      eligible_count: 3,
      pending_count: 0,
      inactive_count: 1,
      roster: [],
      upcoming_reverifications: [],
    });
    mocks.fetchRemittances.mockResolvedValue({
      tenant_id: "tenant-1",
      count: 1,
      total_payments_mtd: 25000,
      era_received_count: 3,
      posted_count: 2,
      pending_manual_match_count: 1,
      payer_breakdown: [{ payer_name: "Medicare", total_paid: 25000 }],
      unmatched_payments: [],
      remittances: [],
    });
    mocks.fetchHospiceCapRecord.mockResolvedValue({
      cap_year: 2025,
      configured: true,
      beneficiary_count: "25",
      gross_reimbursement_collected: "85000",
      source_note: "NGS PS&R Aug 2026",
      cap_usage: {
        cap_year: 2025,
        cap_amount: "4000",
        beneficiary_count: "25",
        allowed_amount: "100000",
        gross_reimbursement_collected: "85000",
        available_amount: "15000",
        over_cap_amount: "0",
        is_over_cap: false,
      },
    });

    render(<ReportsPage />);

    await screen.findByText("Claims Lifecycle");
    expect(screen.getByText("Ready: 3")).toBeTruthy();
    expect(screen.getByText("Payments (MTD): $25,000.00")).toBeTruthy();
    expect(screen.getByText("Total Denials: 2")).toBeTruthy();
  });

  it("shows the honest hospice-cap empty state when no cap data is configured", async () => {
    mocks.fetchTenantBillingReadinessReport.mockResolvedValue({ tenant_id: "tenant-1", service_date: "2026-08-24", total_patients: 0, ready_count: 0, not_ready_count: 0, patients: [] });
    mocks.fetchClaims.mockResolvedValue({ tenant_id: "tenant-1", count: 0, total_claims: 0, submitted_count: 0, accepted_count: 0, denied_count: 0, lifecycle: { draft: 0, submitted: 0, accepted: 0, paid: 0, denied: 0 }, claims: [] });
    mocks.fetchDenials.mockResolvedValue({ tenant_id: "tenant-1", count: 0, total_denials: 0, appeals_filed: 0, appeal_rate: null, overturn_rate: null, avg_resolution_days: null, reason_breakdown: [], denials: [] });
    mocks.fetchEligibilityRoster.mockResolvedValue({ tenant_id: "tenant-1", count: 0, total_active: 0, eligible_count: 0, pending_count: 0, inactive_count: 0, roster: [], upcoming_reverifications: [] });
    mocks.fetchRemittances.mockResolvedValue({ tenant_id: "tenant-1", count: 0, total_payments_mtd: 0, era_received_count: 0, posted_count: 0, pending_manual_match_count: 0, payer_breakdown: [], unmatched_payments: [], remittances: [] });
    mocks.fetchHospiceCapRecord.mockResolvedValue({ cap_year: 2025, configured: false, cap_usage: null, cap_error: "No PS&R figures logged yet." });

    render(<ReportsPage />);

    await screen.findByText("No PS&R figures logged yet.");
    expect(screen.getByText("Log cap data")).toBeTruthy();
  });

  it("shows report load failures instead of synthesized report cards", async () => {
    mocks.fetchTenantBillingReadinessReport.mockRejectedValue(new Error("Unable to load report data."));
    mocks.fetchClaims.mockResolvedValue({ tenant_id: "tenant-1", count: 0, total_claims: 0, submitted_count: 0, accepted_count: 0, denied_count: 0, lifecycle: { draft: 0, submitted: 0, accepted: 0, paid: 0, denied: 0 }, claims: [] });
    mocks.fetchDenials.mockResolvedValue({ tenant_id: "tenant-1", count: 0, total_denials: 0, appeals_filed: 0, appeal_rate: null, overturn_rate: null, avg_resolution_days: null, reason_breakdown: [], denials: [] });
    mocks.fetchEligibilityRoster.mockResolvedValue({ tenant_id: "tenant-1", count: 0, total_active: 0, eligible_count: 0, pending_count: 0, inactive_count: 0, roster: [], upcoming_reverifications: [] });
    mocks.fetchRemittances.mockResolvedValue({ tenant_id: "tenant-1", count: 0, total_payments_mtd: 0, era_received_count: 0, posted_count: 0, pending_manual_match_count: 0, payer_breakdown: [], unmatched_payments: [], remittances: [] });
    mocks.fetchHospiceCapRecord.mockResolvedValue({ cap_year: 2025, configured: false, cap_usage: null });

    render(<ReportsPage />);

    await waitFor(() => {
      expect(screen.getByText("Unable to load report data.")).toBeTruthy();
    });
  });
});
