import React from "react";
import { screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import VolunteerSchedulingDataPage from "./VolunteerSchedulingDataPage";
import { deferred, renderWithRoute } from "../test/testUtils";

const mocks = vi.hoisted(() => ({
  fetchPatientSummary: vi.fn(),
  fetchVolunteerScheduling: vi.fn(),
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
  fetchVolunteerScheduling: mocks.fetchVolunteerScheduling,
}));

describe("VolunteerSchedulingDataPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mocks.fetchPatientSummary.mockResolvedValue({ patient: { full_name: "Pat One", mrn: "MRN-100" } });
  });

  it("shows a loading state while volunteer scheduling data resolves", () => {
    const pending = deferred();
    mocks.fetchVolunteerScheduling.mockReturnValue(pending.promise);

    renderWithRoute(<VolunteerSchedulingDataPage />, { route: "/volunteer-scheduling?patientId=patient-1", path: "/volunteer-scheduling" });

    expect(screen.getByText("Loading volunteer schedule...")).toBeTruthy();
  });

  it("renders live volunteer visit slots and assignments", async () => {
    mocks.fetchVolunteerScheduling.mockResolvedValue({
      patient: { id: "patient-1", mrn: "MRN-100", full_name: "Pat One" },
      visits: [{ id: "visit-1", visit_datetime: "2026-08-25T10:00:00Z", visit_type: "Friendly Visit", visit_discipline: "Volunteer", status: "Scheduled", provider_name: "Volunteer Amy", is_supervisory: false }],
      assignments: [{ id: "assignment-1", discipline: "Volunteer", staff_name: "Volunteer Amy", primary: true, service_area: "North", status: "ACTIVE", assigned_at: "2026-08-20" }],
      task_slots: [{ id: "task-1", task_type: "Check-in call", status: "OPEN", due_date: "2026-08-26", assigned_user_id: null, assigned_role: null, alert_reason: null }],
    });

    renderWithRoute(<VolunteerSchedulingDataPage />, { route: "/volunteer-scheduling?patientId=patient-1", path: "/volunteer-scheduling" });

    await screen.findByText("Calendar view");
    expect(screen.getByText("Friendly Visit")).toBeTruthy();
    expect(screen.getByText("Volunteer Amy")).toBeTruthy();
    expect(screen.getByText("Assignments: 1")).toBeTruthy();
  });

  it("leaves the page empty instead of fabricating volunteer schedule rows on fetch failure", async () => {
    mocks.fetchVolunteerScheduling.mockRejectedValue(new Error("schedule unavailable"));

    renderWithRoute(<VolunteerSchedulingDataPage />, { route: "/volunteer-scheduling?patientId=patient-1", path: "/volunteer-scheduling" });

    await waitFor(() => {
      expect(screen.queryByText("Loading volunteer schedule...")).toBeNull();
    });
    expect(screen.queryByText("Calendar view")).toBeNull();
    expect(screen.queryByText("Assignments")).toBeNull();
  });
});
