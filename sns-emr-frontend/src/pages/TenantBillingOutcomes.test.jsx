import React from "react";
import { render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import TenantBillingOutcomes from "./TenantBillingOutcomes";
import { deferred } from "../test/testUtils";

const mocks = vi.hoisted(() => ({
  getCurrentUser: vi.fn(),
  fetchBillableAgencies: vi.fn(),
  fetchTenantBillingReadinessReport: vi.fn(),
  fetchClaimLifecycle: vi.fn(),
  fetchClaims: vi.fn(),
  fetchDenials: vi.fn(),
  fetchDenialsAppealsSummary: vi.fn(),
  fetchRemittances: vi.fn(),
  fetchNoeTracking: vi.fn(),
  fetchBillingQueue: vi.fn(),
}));

vi.mock("../api/session", () => ({
  getCurrentUser: mocks.getCurrentUser,
}));

vi.mock("../api/dashboard", () => ({
  fetchBillableAgencies: mocks.fetchBillableAgencies,
  fetchTenantBillingReadinessReport: mocks.fetchTenantBillingReadinessReport,
  fetchClaimLifecycle: mocks.fetchClaimLifecycle,
  fetchClaims: mocks.fetchClaims,
  fetchDenials: mocks.fetchDenials,
  fetchDenialsAppealsSummary: mocks.fetchDenialsAppealsSummary,
  fetchRemittances: mocks.fetchRemittances,
  fetchNoeTracking: mocks.fetchNoeTracking,
  fetchBillingQueue: mocks.fetchBillingQueue,
}));

function mockSuccessfulMirrorData() {
  mocks.fetchTenantBillingReadinessReport.mockResolvedValue({
    tenant_id: "tenant-1",
    service_date: "2026-08-24",
    total_patients: 4,
    ready_count: 3,
    not_ready_count: 1,
    patients: [{ patient_id: "p1", mrn: "MRN-1", period_number: 1, ready: false, blockers: ["Notice of Election (NOE) has not been filed"], warnings: [] }],
  });
  mocks.fetchClaimLifecycle.mockResolvedValue({ metrics: [], ready: 2, sent: 1, accepted: 3, paid: 2, denied: 1 });
  mocks.fetchClaims.mockResolvedValue({ tenant_id: "tenant-1", count: 2, total_claims: 8, submitted_count: 4, accepted_count: 3, denied_count: 1, lifecycle: { draft: 1, submitted: 4, accepted: 3, paid: 2, denied: 1 }, claims: [] });
  mocks.fetchDenials.mockResolvedValue({ tenant_id: "tenant-1", count: 1, total_denials: 2, appeals_filed: 1, appeal_rate: 50, overturn_rate: 100, avg_resolution_days: 8, reason_breakdown: [], denials: [] });
  mocks.fetchDenialsAppealsSummary.mockResolvedValue({ open_denials: 1, appealed_denials: 1, overturned_denials: 0, upheld_denials: 0, written_off_denials: 0, total_denied_amount: 900, open_denied_amount: 300, total_recovered_amount: 600, top_denial_codes: [{ carc_code: "CO-16", reason_description: "Missing documentation", case_count: 1, total_amount: 300 }] });
  mocks.fetchRemittances.mockResolvedValue({ tenant_id: "tenant-1", count: 1, total_payments_mtd: 12000, era_received_count: 2, posted_count: 1, pending_manual_match_count: 1, payer_breakdown: [{ payer_name: "Medicare", total_paid: 12000 }], unmatched_payments: [], remittances: [{ era_id: "era-1", payer_name: "Medicare", received_at: "2026-08-22", claim_count: 2, total_paid_amount: 12000, status: "POSTED", file_name: "era.txt" }] });
  mocks.fetchNoeTracking.mockResolvedValue({ tenant_id: "tenant-1", count: 1, late_count: 0, unfiled_count: 0, noe_tracking: [{ patient_id: "p1", patient_name: "Pat One", mrn: "MRN-1", benefit_period_id: "bp-1", election_date: "2026-08-10", noe_submitted_date: "2026-08-12", noe_exception_reason: null, noe_filed: true, is_late: false, is_exempt: false, non_covered_start: null, non_covered_end: null, non_covered_days: null, penalty_reason: null }] });
  mocks.fetchBillingQueue.mockResolvedValue([{ billing_cycle_id: "cycle-1", patient_id: "p1", patient_name: "Pat One", total_charge: 10000, status: "READY" }]);
}

describe("TenantBillingOutcomes", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    window.localStorage.clear();
    mocks.getCurrentUser.mockReturnValue({
      tenant_id: "tenant-1",
      tenant_name: "Alpha Hospice",
      full_name: "Billing User",
      role: "BILLER",
      access_scope: "billing",
    });
  });

  it("shows a loading state while the live outcomes mirror is fetching", async () => {
    mocks.fetchBillableAgencies.mockResolvedValue({ agencies: [{ tenant_id: "tenant-1", display_name: "Alpha Hospice", legal_name: "Alpha Hospice" }] });
    const pending = deferred();
    mocks.fetchTenantBillingReadinessReport.mockReturnValue(pending.promise);
    mocks.fetchClaimLifecycle.mockReturnValue(pending.promise);
    mocks.fetchClaims.mockReturnValue(pending.promise);
    mocks.fetchDenials.mockReturnValue(pending.promise);
    mocks.fetchDenialsAppealsSummary.mockReturnValue(pending.promise);
    mocks.fetchRemittances.mockReturnValue(pending.promise);
    mocks.fetchNoeTracking.mockReturnValue(pending.promise);
    mocks.fetchBillingQueue.mockReturnValue(pending.promise);

    render(<TenantBillingOutcomes />);

    expect(await screen.findByText("Loading live billing outcomes…")).toBeTruthy();
  });

  it("renders billing outcomes, blocker counts, and top denial reasons from live mocked sources", async () => {
    mocks.fetchBillableAgencies.mockResolvedValue({ agencies: [{ tenant_id: "tenant-1", display_name: "Alpha Hospice", legal_name: "Alpha Hospice" }] });
    mockSuccessfulMirrorData();

    render(<TenantBillingOutcomes />);

    await screen.findByText("CO-16");
    expect(screen.getByText("Missing NOE Filing")).toBeTruthy();
    expect(screen.getByText(/Missing documentation/i)).toBeTruthy();
    expect(screen.getByText(/Ready to bill/i)).toBeTruthy();
  });

  it("shows source notices when one of the live billing feeds fails", async () => {
    mocks.fetchBillableAgencies.mockResolvedValue({ agencies: [{ tenant_id: "tenant-1", display_name: "Alpha Hospice", legal_name: "Alpha Hospice" }] });
    mockSuccessfulMirrorData();
    mocks.fetchRemittances.mockRejectedValue(new Error("remittances unavailable"));

    render(<TenantBillingOutcomes />);

    await screen.findByText("Source notice");
    expect(screen.getByText("remittances unavailable")).toBeTruthy();
  });

  it("shows an explicit empty-state prompt when billing users have no tenant selected", async () => {
    mocks.fetchBillableAgencies.mockResolvedValue({ agencies: [] });
    mockSuccessfulMirrorData();

    render(<TenantBillingOutcomes />);

    await waitFor(() => {
      expect(screen.getByText("Select a tenant to view billing outcomes")).toBeTruthy();
    });
  });
});
