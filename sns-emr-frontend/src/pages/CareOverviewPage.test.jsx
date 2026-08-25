import React from "react";
import { screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import CareOverviewPage from "./CareOverviewPage";
import { deferred, renderWithRoute } from "../test/testUtils";

const mocks = vi.hoisted(() => ({
  fetchPatientSummary: vi.fn(),
  fetchCensusWorkspace: vi.fn(),
}));

vi.mock("../components/PatientModuleShell", () => ({
  default: ({ title, patientName, metrics = [], children }) => (
    <div>
      <h1>{title}</h1>
      <div>{patientName}</div>
      <div>{metrics.map((metric) => <div key={metric.label}>{metric.label}: {metric.value}</div>)}</div>
      {children}
    </div>
  ),
}));

vi.mock("../api/patientCharts", () => ({
  fetchPatientSummary: mocks.fetchPatientSummary,
}));

vi.mock("../api/census", () => ({
  fetchCensusWorkspace: mocks.fetchCensusWorkspace,
}));

describe("CareOverviewPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders recent visits and clinical readiness from the live patient summary", async () => {
    mocks.fetchPatientSummary.mockResolvedValue({
      patient: { id: "patient-1", mrn: "MRN-100", full_name: "Pat One", primary_diagnosis: "CHF", status: "ACTIVE", acuity_state: "stable", admission_status: "Hospice", hospice_election_date: "2026-08-01", soc_date: "2026-08-02" },
      care_team: [{ discipline: "RN", staff_name: "RN One", primary: true, status: "ACTIVE", service_area: "North" }],
      recent_visits: [{ id: "visit-1", visit_datetime: "2026-08-23T09:00:00Z", visit_type: "Routine RN Visit", discipline: "RN", status: "Completed", provider_name: "RN One" }],
      communication_summary: { total: 1, latest: [{ id: "comm-1", event_type: "call", focus_area: null, event_time: "2026-08-22", summary: "Family requested supply follow-up", status: "OPEN" }] },
      incident_summary: { total: 0, latest: [] },
      compliance_summary: { patient: {}, eligibility: {}, task_counts: { pending: 0, overdue: 0, completed: 0 }, note_counts: { total: 0, hope: 0, poc: 0, f2f: 0 }, hope_status: "Open", qies_status: "Open", open_issues: ["Missing consent"], recent_notes: [] },
      volunteer_summary: { patient: {}, visits: [], assignments: [], task_slots: [] },
    });

    renderWithRoute(<CareOverviewPage />, { route: "/care-overview?patientId=patient-1", path: "/care-overview" });

    await screen.findByText("Recent / upcoming visits");
    expect(screen.getByText("Routine RN Visit")).toBeTruthy();
    expect(screen.getByText("Clinical readiness")).toBeTruthy();
    expect(screen.getByText("1 recent visit record(s) on chart")).toBeTruthy();
  });

  it("shows a loading shell before the patient summary resolves", () => {
    const pending = deferred();
    mocks.fetchPatientSummary.mockReturnValue(pending.promise);

    renderWithRoute(<CareOverviewPage />, { route: "/care-overview?patientId=patient-1", path: "/care-overview" });

    expect(screen.getByText("Loading patient...")).toBeTruthy();
  });

  it("shows the honest empty-state when no patient can be selected from census", async () => {
    mocks.fetchCensusWorkspace.mockResolvedValue({ tenant_id: "tenant-1", patient_count: 0, patients: [] });

    renderWithRoute(<CareOverviewPage />, { route: "/care-overview", path: "/care-overview" });

    expect(await screen.findByText("Choose a patient from the census to open the chart.")).toBeTruthy();
  });
});
