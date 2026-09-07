import React from "react";
import { render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import AlertInboxPage from "./AlertInboxPage";
import { deferred } from "../../test/testUtils";

const mocks = vi.hoisted(() => ({
  fetchFacilityCollectionAlerts: vi.fn(),
  fetchAlertHistory: vi.fn(),
  useAgency: vi.fn(),
}));

vi.mock("../../api/dashboard", async () => {
  const actual = await vi.importActual("../../api/dashboard");
  return {
    ...actual,
    fetchFacilityCollectionAlerts: mocks.fetchFacilityCollectionAlerts,
    fetchAlertHistory: mocks.fetchAlertHistory,
  };
});

vi.mock("../../components/billing/AgencyContext", () => ({
  useAgency: mocks.useAgency,
}));

const baseAlert = {
  id: "alert-1",
  tenant_id: "tenant-1",
  patient_id: "patient-1",
  facility_payment_expectation_id: "expectation-1",
  alert_type: "OVERDUE_90",
  severity: "HIGH",
  expected_amount: "500.00",
  received_amount: "0.00",
  outstanding_amount: "500.00",
  due_date: "2026-01-01",
  days_outstanding: 95,
  status: "OPEN",
  assigned_to: null,
  acknowledged_by: null,
  acknowledged_at: null,
  snoozed_until: null,
  dismissal_reason_code: null,
  resolution_evidence: null,
  resolved_by: null,
  resolved_at: null,
  created_at: "2026-01-05T00:00:00Z",
  updated_at: "2026-01-05T00:00:00Z",
};

describe("AlertInboxPage", () => {
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

  it("shows a loading spinner before alerts resolve", () => {
    const pending = deferred();
    mocks.fetchFacilityCollectionAlerts.mockReturnValue(pending.promise);

    render(<AlertInboxPage />);

    expect(screen.getByRole("progressbar")).toBeTruthy();
  });

  it("renders live alert rows once data resolves", async () => {
    mocks.fetchFacilityCollectionAlerts.mockResolvedValue({ count: 1, items: [baseAlert] });

    render(<AlertInboxPage />);

    await screen.findByText("Overdue 90");
    expect(screen.getByText("patient-1")).toBeTruthy();
    expect(screen.getByText("$500.00")).toBeTruthy();
  });

  it("shows an honest empty state when no alerts match the filters", async () => {
    mocks.fetchFacilityCollectionAlerts.mockResolvedValue({ count: 0, items: [] });

    render(<AlertInboxPage />);

    await screen.findByText("No alerts match the current filters.");
  });

  it("shows alert load failures instead of fabricated rows", async () => {
    mocks.fetchFacilityCollectionAlerts.mockRejectedValue(new Error("Unable to load facility collection alerts."));

    render(<AlertInboxPage />);

    await waitFor(() => {
      expect(screen.getByText("Unable to load facility collection alerts.")).toBeTruthy();
    });
  });
});
