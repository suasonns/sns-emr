import React from "react";
import { fireEvent, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import SNSAnalytics from "./SNSAnalytics";
import { renderWithRoute } from "../test/testUtils";

const mocks = vi.hoisted(() => ({
  fetchCensusWorkspace: vi.fn(),
  fetchTenantDashboard: vi.fn(),
  fetchClinicalAlerts: vi.fn(),
  listStaff: vi.fn(),
  listIdgSessions: vi.fn(),
  getCurrentUser: vi.fn(),
}));

vi.mock("../components/PortalShell", () => ({
  default: ({ children }) => <div data-testid="portal-shell">{children}</div>,
}));

vi.mock("./SNSNewReports", () => ({
  default: ({ activeReport }) => <div>{activeReport}</div>,
}));

vi.mock("../api/census", () => ({
  fetchCensusWorkspace: mocks.fetchCensusWorkspace,
}));

vi.mock("../api/dashboard", () => ({
  fetchClinicalAlerts: mocks.fetchClinicalAlerts,
  fetchTenantDashboard: mocks.fetchTenantDashboard,
}));

vi.mock("../api/staff", () => ({
  listStaff: mocks.listStaff,
}));

vi.mock("../api/idgWorkspace", () => ({
  listIdgSessions: mocks.listIdgSessions,
}));

vi.mock("../api/session", () => ({
  getCurrentUser: mocks.getCurrentUser,
}));

function mockAnalyticsData({ empty = false } = {}) {
  mocks.fetchCensusWorkspace.mockResolvedValue({
    tenant_id: "tenant-1",
    patient_count: empty ? 0 : 1,
    patients: empty
      ? []
      : [{ patient_id: "patient-1", mrn: "MRN-100", full_name: "Pat One", date_of_birth: "1950-01-01", primary_diagnosis: "CHF", patient_status: "ACTIVE", admission_status: "ACTIVE", admission_at: "2026-08-01", discharge_date: null, discharge_reason: null, attending_physician: "Dr Smith", payer_name: "Medicare", last_visit_at: "2026-08-23T09:00:00Z", census_bucket: "active" }],
  });
  mocks.fetchTenantDashboard.mockResolvedValue({
    tenant_id: "tenant-1",
    tenant_name: "Alpha Hospice",
    ai_enabled: true,
    billing_enabled: true,
    dashboard: {
      metrics: [],
      task_type_counts: {},
      incident_type_counts: {},
      open_tasks: empty ? [] : [{ task_id: "task-1", patient_id: "patient-1", task_type: "recert_review", status: "OPEN", due_date: "2026-08-30", due_at: null, clinical_note_id: "note-1", incident_id: null }],
      pending_incidents: empty ? [] : [{ incident_id: "incident-1", patient_id: "patient-1", incident_type: "fall", incident_severity: "high", incident_date: "2026-08-22", clinical_note_id: null }],
      flagged_notes: empty ? [] : [{ note_id: "note-1", patient_id: "patient-1", encounter_date: "2026-08-20", discipline: "rn", visit_type: "routine", note_category: "clinical", incident_required: false, incident_status: null, red_flags: ["Missing pain reassessment"], needs_clarification: ["Verify wound dimensions"] }],
      blocked_patients: empty ? [] : [{ patient_id: "patient-1", blockers: ["Missing F2F Documentation"] }],
      unsigned_orders: empty ? [] : [{ order_id: "order-1", patient_id: "patient-1", patient_name: "Pat One", order_category: "Medication", order_text: "Morphine", status: "PENDING", source_type: "POC", ordered_by_provider_name: "Dr Smith", ordered_by_provider_role: "MD", entered_by_name: null, ordered_at: "2026-08-21T08:00:00Z", signed_by_name: null, signed_at: null }],
      all_orders: empty ? [] : [{ order_id: "order-1", patient_id: "patient-1", patient_name: "Pat One", order_category: "Medication", order_text: "Morphine", status: "PENDING", source_type: "POC", ordered_by_provider_name: "Dr Smith", ordered_by_provider_role: "MD", entered_by_name: null, ordered_at: "2026-08-21T08:00:00Z", signed_by_name: null, signed_at: null }],
    },
  });
  mocks.fetchClinicalAlerts.mockResolvedValue({ metrics: [], alerts: empty ? [] : [{ alert_id: "alert-1", priority: "High", alert_type: "Missed visit", patient_id: "patient-1", patient_name: "Pat One", description: "Missed nursing visit", generated: "2026-08-24T12:00:00Z", status: "Open", source_type: "workflow" }] });
  mocks.listStaff.mockResolvedValue(empty ? [] : [{ id: "staff-1", tenant_id: "tenant-1", email: "rn@example.com", full_name: "RN One", first_name: "RN", middle_name: null, last_name: "One", role: "RN", active: true, date_of_birth: null, address_street: null, address_city: null, address_state: null, address_zip: null, phone: null, home_phone: null, job_title: null, discipline: "RN", license_number: null, npi: null, employment_date: null, employment_end_date: null, staff_type: "C", access_level: null, ssn_masked: null, has_ssn: false, created_at: "2026-08-01", updated_at: null }]);
  mocks.listIdgSessions.mockResolvedValue(empty ? [] : [{ meeting_date: "2026-08-28T12:00:00Z", patient_count: 2 }]);
}

describe("SNSAnalytics", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mocks.getCurrentUser.mockReturnValue({ tenant_name: "Alpha Hospice", full_name: "Analytics User", role: "TENANT_ADMIN" });
  });

  it("renders clinical analytics from live census, dashboard, and alert feeds", async () => {
    mockAnalyticsData();

    renderWithRoute(<SNSAnalytics defaultDomain="Clinical" />, { route: "/analytics", path: "/analytics" });

    await screen.findByText("Patient Census Summary");
    expect(screen.getByText("Pat One")).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "Compliance & Documentation" }));
    expect(await screen.findByText("Open Clinical Workflow Queue")).toBeTruthy();
    expect(screen.getByText(/recert review/i)).toBeTruthy();
  });

  it("shows the honest clinical empty-state messaging after fabricated recertification data was removed", async () => {
    mockAnalyticsData({ empty: true });

    renderWithRoute(<SNSAnalytics defaultDomain="Clinical" />, { route: "/analytics", path: "/analytics" });

    await screen.findByText("Patient Census Summary");
    expect(screen.getByText("No active patients are available.")).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "Recertification Tracker" }));
    expect(await screen.findByText("Structured recertification tracker is not available yet")).toBeTruthy();
  });

  it("shows the QAPI honest-empty-state and no-fabrication messaging", async () => {
    mockAnalyticsData({ empty: true });

    renderWithRoute(<SNSAnalytics defaultDomain="QAPI" />, { route: "/analytics", path: "/analytics" });

    await screen.findByText("Recent Incident Reports");
    expect(screen.getByText("No pending incidents are currently open.")).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "Quality Measures" }));
    expect(await screen.findByText("Structured quality-measure scoring is not available yet")).toBeTruthy();
  });
});
