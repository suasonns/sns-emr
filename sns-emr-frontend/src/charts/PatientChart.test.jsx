import React from "react";
import { fireEvent, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import PatientChart from "./PatientChart";
import { deferred, renderWithRoute } from "../test/testUtils";

const mocks = vi.hoisted(() => ({
  fetchPatientSummary: vi.fn(),
  fetchAssessmentHistory: vi.fn(),
  fetchFacesheet: vi.fn(),
  listMedications: vi.fn(),
  getRnicaAssessmentByPatient: vi.fn(),
  listPatientIssues: vi.fn(),
}));

vi.mock("./PatientChartSidebar", () => ({
  default: ({ onNavigate }) => (
    <div>
      <button onClick={() => onNavigate("care-overview")}>Go care overview</button>
      <button onClick={() => onNavigate("intake")}>Go intake</button>
      <button onClick={() => onNavigate("idg")}>Go idg</button>
      <button onClick={() => onNavigate("poc")}>Go poc</button>
      <button onClick={() => onNavigate("issues")}>Go issues</button>
    </div>
  ),
}));

vi.mock("./PatientFacesheet", () => ({ default: () => <div>Facesheet stub</div> }));
vi.mock("../intake/ConsentNotifications", () => ({ default: () => <div>Consent stub</div> }));
vi.mock("../intake/StaffAssignment", () => ({ default: () => <div>Staff assignment stub</div> }));
vi.mock("../intake/ChartCompletionChecklist", () => ({ default: () => <div>Checklist stub</div> }));
vi.mock("../intake/NursingAssessmentBoard", () => ({ default: () => <div>Nursing assessment stub</div> }));
vi.mock("../intake/PsychosocialAssessmentBoard", () => ({ default: () => <div>Psychosocial assessment stub</div> }));
vi.mock("../intake/SpiritualAssessmentBoard", () => ({ default: () => <div>Spiritual assessment stub</div> }));
vi.mock("../components/VisitNotes", () => ({ default: () => <div>Visit notes stub</div> }));
vi.mock("./PhysicianOrdersBoard", () => ({ default: () => <div>Physician orders stub</div> }));
vi.mock("./CertificationsBoard", () => ({ default: () => <div>Certifications stub</div> }));
vi.mock("./F2FBoard", () => ({ default: () => <div>F2F stub</div> }));
vi.mock("../intake/ComplianceHopeBoard", () => ({ default: () => <div>Compliance HOPE stub</div> }));
vi.mock("./DischargePlanningBoard", () => ({ default: () => <div>Discharge stub</div> }));
vi.mock("../components/RNICA", () => ({
  OrdersHubCard: () => <div>Orders hub stub</div>,
  MedicationOrdersCard: () => <div>Medication orders stub</div>,
  MasterPocReviewCard: ({ assessmentId }) => <div>Master POC review {assessmentId}</div>,
  CHHAPocCard: () => <div>CHHA POC stub</div>,
  CHHAVisitNoteCard: () => <div>CHHA visit stub</div>,
  getRnicaColors: () => ({}),
  getRnicaStyles: () => ({}),
}));

vi.mock("../api/patientCharts", () => ({
  fetchPatientSummary: mocks.fetchPatientSummary,
  fetchAssessmentHistory: mocks.fetchAssessmentHistory,
}));
vi.mock("../api/facesheet", () => ({ fetchFacesheet: mocks.fetchFacesheet }));
vi.mock("../api/medications", () => ({ listMedications: mocks.listMedications }));
vi.mock("../api/icaAssessments", () => ({ getRnicaAssessmentByPatient: mocks.getRnicaAssessmentByPatient }));
vi.mock("../api/patientIssues", () => ({
  listPatientIssues: mocks.listPatientIssues,
  createPatientIssue: vi.fn(),
  updatePatientIssue: vi.fn(),
}));

function mockChartData({ idgAssessmentId = null, issues = [], issuesError = null } = {}) {
  mocks.fetchPatientSummary.mockResolvedValue({
    patient: {
      id: "patient-1",
      mrn: "MRN-100",
      full_name: "Pat One",
      primary_diagnosis: "CHF",
      status: "ACTIVE",
      acuity_state: "stable",
      admission_status: "Hospice",
      hospice_election_date: "2026-08-01",
      soc_date: "2026-08-02",
    },
    care_team: [
      { discipline: "Nursing", staff_name: "RN One", primary: true, status: "ACTIVE", service_area: "North" },
      { discipline: "MSW", staff_name: "MSW One", primary: false, status: "ACTIVE", service_area: "North" },
    ],
    recent_visits: [{ id: "visit-1", visit_datetime: "2026-08-23T09:00:00Z", visit_type: "Routine RN Visit", discipline: "RN", status: "Completed", provider_name: "RN One" }],
    communication_summary: { total: 1, latest: [{ id: "comm-1", event_type: "call", focus_area: null, event_time: "2026-08-23T10:00:00Z", summary: "Family requested DME follow-up", status: "OPEN" }] },
    incident_summary: { total: 0, latest: [] },
    compliance_summary: { patient: {}, eligibility: {}, task_counts: { pending: 0, overdue: 0, completed: 0 }, note_counts: { total: 0, hope: 0, poc: 0, f2f: 0 }, hope_status: "Open", qies_status: "Open", open_issues: ["Missing consent"], recent_notes: [] },
    volunteer_summary: { patient: {}, visits: [], assignments: [], task_slots: [] },
  });
  mocks.fetchFacesheet.mockResolvedValue({
    patient_id: "patient-1",
    mrn: "MRN-100",
    identity: { first_name: "Pat", middle_name: null, last_name: "One", dob: "1950-01-01", ssn: null, gender: "F", race: null, ethnicity: null, language: null, religion: null, marital_status: null, phone: null },
    address: { address: null, city: null, state: null, zip: null },
    insurance: { primary_payer: "Hospice Plus", primary_policy_number: null, mbi_number: null, secondary_payer: null, secondary_policy_number: null },
    authorization: { requires_prior_authorization: null, authorization_required_for: null, authorization_number: null, authorization_status: null, authorization_start_date: null, authorization_end_date: null },
    clinical: { primary_diagnosis: "CHF", secondary_diagnoses: null, diagnoses: { primary: null, secondary: [], comorbidities: [] }, active_primary_diagnosis: null, active_secondary_diagnoses: [], active_comorbidities: [], has_allergies: true, allergies: "Penicillin" },
    level_of_care: { current_level_of_care: "Routine Home Care", loc_effective_date: "2026-08-02" },
    place_of_service: { current_pos_type: null, current_pos_name: null, current_pos_address: null, room_number: null, pos_start_date: null, pos_end_date: null },
    contacts: { responsible_party: { name: "Jamie One", relationship: "Daughter", phone: null }, emergency_contact: { name: "Sam One", relationship: "Son", phone: null } },
    physicians: { attending: { name: "Dr Smith", address: null, phone: null, fax: null, npi: null, following: true }, medical_director: { name: null, address: null, phone: null, fax: null, npi: null }, medical_director_designee: { name: null, npi: null }, associate_medical_director: { name: null, npi: null } },
    vendors: { pharmacy: { name: null, phone: null, fax: null }, dme: { name: "Acme DME", phone: "555-0001" }, mortuary: { name: null, phone: null } },
    service_dates: { admission_status: "Hospice", soc_date: "2026-08-02", effective_date: null, admission_date: null, ref_date: null, recert_date: null },
    notes: { special_instructions: null },
  });
  mocks.listMedications.mockResolvedValue([{ medication_id: "med-1", medication_name: "Morphine", dosage: "5 mg", route: "PO", frequency: "q4h", start_date: "2026-08-01", end_date: null, status: "active", flags: [] }]);
  mocks.getRnicaAssessmentByPatient.mockResolvedValue(idgAssessmentId ? { id: idgAssessmentId } : null);
  mocks.fetchAssessmentHistory.mockResolvedValue({ patient_id: "patient-1", items: [], total: 0, limit: 500, offset: 0, sort_order: "asc", filters: { discipline: null, assessment_type: null, status: null, from_date: null, to_date: null } });
  if (issuesError) {
    mocks.listPatientIssues.mockRejectedValue(issuesError);
  } else {
    mocks.listPatientIssues.mockResolvedValue(issues);
  }
}

describe("PatientChart", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("shows a loading state while the patient chart summary loads", () => {
    const pending = deferred();
    mocks.fetchPatientSummary.mockReturnValue(pending.promise);
    mocks.fetchFacesheet.mockResolvedValue(null);
    mocks.listMedications.mockResolvedValue([]);
    mocks.getRnicaAssessmentByPatient.mockResolvedValue(null);
    mocks.fetchAssessmentHistory.mockResolvedValue({ patient_id: "patient-1", items: [], total: 0, limit: 0, offset: 0, sort_order: "asc", filters: { discipline: null, assessment_type: null, status: null, from_date: null, to_date: null } });
    mocks.listPatientIssues.mockResolvedValue([]);

    renderWithRoute(<PatientChart />, { route: "/chart/patient-1", path: "/chart/:patientId", theme: true });

    expect(screen.getByText("Loading patient chart...")).toBeTruthy();
  });

  it("renders the care overview board from live patient summary data", async () => {
    mockChartData();

    renderWithRoute(<PatientChart />, { route: "/chart/patient-1", path: "/chart/:patientId", theme: true });

    await screen.findByText("Facesheet stub");
    fireEvent.click(screen.getByRole("button", { name: "Go care overview" }));
    expect(await screen.findByText("Current care plan")).toBeTruthy();
    expect(screen.getByText(/Primary diagnosis: CHF/i)).toBeTruthy();
    expect(screen.getByText("RN One")).toBeTruthy();
  });

  it("renders the intake board from live facesheet data", async () => {
    mockChartData();

    renderWithRoute(<PatientChart />, { route: "/chart/patient-1", path: "/chart/:patientId", theme: true });

    await screen.findByText("Facesheet stub");
    fireEvent.click(screen.getByRole("button", { name: "Go intake" }));
    expect(await screen.findByText("Intake & admission overview")).toBeTruthy();
    expect(screen.getByText("Hospice Plus")).toBeTruthy();
    expect(screen.getByText("Insurance verification completed")).toBeTruthy();
    expect(screen.getByText("Responsible party on file")).toBeTruthy();
  });

  it("shows honest empty IDG and POC states when no structured plan-of-care record exists", async () => {
    mockChartData({ idgAssessmentId: null });

    renderWithRoute(<PatientChart />, { route: "/chart/patient-1", path: "/chart/:patientId", theme: true });

    await screen.findByText("Facesheet stub");
    fireEvent.click(screen.getByRole("button", { name: "Go idg" }));
    expect(await screen.findByText("No plan of care on file for this patient yet.")).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "Go poc" }));
    expect(await screen.findByText(/Plan of care goals/i)).toBeTruthy();
    expect(screen.getAllByText("No plan of care on file for this patient yet.").length).toBeGreaterThan(0);
  });

  it("renders issues and outcomes from the live issues feed", async () => {
    mockChartData({
      issues: [{ id: "issue-1", tenant_id: "tenant-1", patient_id: "patient-1", category: "clinical", description: "Pain management barrier", identified_date: "2026-08-20", identified_by: null, status: "OPEN", outcome_notes: null, resolved_date: null, resolved_by: null, created_at: "2026-08-20", updated_at: "2026-08-20" }],
    });

    renderWithRoute(<PatientChart />, { route: "/chart/patient-1", path: "/chart/:patientId", theme: true });

    await screen.findByText("Facesheet stub");
    fireEvent.click(screen.getByRole("button", { name: "Go issues" }));
    expect(await screen.findByText("Log new issue")).toBeTruthy();
    expect(screen.getByText("Pain management barrier")).toBeTruthy();
  });

  it("shows issues-board API failures instead of fallback issue rows", async () => {
    mockChartData({ issuesError: new Error("Unable to load issues and outcomes right now.") });

    renderWithRoute(<PatientChart />, { route: "/chart/patient-1", path: "/chart/:patientId", theme: true });

    await screen.findByText("Facesheet stub");
    fireEvent.click(screen.getByRole("button", { name: "Go issues" }));
    await waitFor(() => {
      expect(screen.getByText("Unable to load issues and outcomes right now.")).toBeTruthy();
    });
  });
});
