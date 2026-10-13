import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, within, waitFor } from "@testing-library/react";
import { RespiratoryPanel } from "./RespiratoryPanel";
import { RespiratoryStaleVersionError, type RespiratoryAssessmentDTO } from "../../../api/bodySystems";

// Same mocking convention as BodySystemsWorkspace.test.tsx: this repo has
// no `@testing-library/user-event`/`jest-dom`, so these tests use
// `fireEvent` + plain `screen` queries throughout.
const mocks = vi.hoisted(() => ({
  getRespiratoryAssessment: vi.fn(),
  saveRespiratoryDraft: vi.fn(),
}));

vi.mock("../../../api/bodySystems", async () => {
  const actual = await vi.importActual<typeof import("../../../api/bodySystems")>("../../../api/bodySystems");
  return {
    ...actual,
    getRespiratoryAssessment: mocks.getRespiratoryAssessment,
    saveRespiratoryDraft: mocks.saveRespiratoryDraft,
  };
});

const TEST_PATIENT_ID = "22222222-2222-2222-2222-222222222222";
const TEST_ASSESSMENT_ID = "33333333-3333-3333-3333-333333333333";

function baseAssessment(overrides: Partial<RespiratoryAssessmentDTO> = {}): RespiratoryAssessmentDTO {
  return {
    id: "sa-1",
    bodySystemsAssessmentId: "bsa-1",
    rnicaAssessmentId: TEST_ASSESSMENT_ID,
    assessmentStatus: "draft",
    system: "respiratory",
    situation: null,
    reviewState: "not_reviewed",
    data: {},
    summary: null,
    version: 1,
    updatedAt: null,
    openReviewExceptions: [],
    ...overrides,
  };
}

function selectSingle(name: string, value: string) {
  const trigger = screen.getByRole("combobox", { name });
  fireEvent.click(trigger);
  const option = screen.getByRole("option", { name: value });
  fireEvent.click(option);
}

/** For fields the approved production candidate renders as a segmented
 * button row or true radio group (not a dropdown): SOB Severity, Treatment
 * Decision, Oxygen Use, Cough Type, Respiratory Support Status, Assessment
 * Context, Comparison to Prior, etc. */
function selectExclusive(name: string, value: string) {
  const group = screen.getByRole("radiogroup", { name });
  const option = within(group).getByRole("radio", { name: value });
  fireEvent.click(option);
}

beforeEach(() => {
  mocks.getRespiratoryAssessment.mockReset();
  mocks.saveRespiratoryDraft.mockReset();
});

describe("RespiratoryPanel — load states", () => {
  it("shows a loading state before the API resolves", () => {
    mocks.getRespiratoryAssessment.mockReturnValue(new Promise(() => {}));
    render(<RespiratoryPanel patientId={TEST_PATIENT_ID} assessmentId={TEST_ASSESSMENT_ID} />);
    expect(screen.getByRole("status").textContent).toContain("Loading Respiratory assessment");
  });

  it("renders every current-evidence field immediately — no upfront selector gates them", async () => {
    mocks.getRespiratoryAssessment.mockResolvedValueOnce(baseAssessment());
    render(<RespiratoryPanel patientId={TEST_PATIENT_ID} assessmentId={TEST_ASSESSMENT_ID} />);
    await waitFor(() => expect(screen.getByTestId("respiratory-panel")).toBeTruthy());
    // The retired overview selector must never be rendered.
    expect(screen.queryByRole("combobox", { name: "Respiratory Overview" })).toBeNull();
    expect(screen.getByTestId("respiratory-current-evidence-section")).toBeTruthy();
    expect(screen.getByTestId("respiratory-intervention-section")).toBeTruthy();
    expect(screen.getByTestId("respiratory-follow-up-section")).toBeTruthy();
    expect(screen.queryByTestId("respiratory-limitation-section")).toBeNull();
    // Progressive disclosure: intervention fields are hidden until dyspnea
    // is moderate/severe or an intervention has already been documented.
    expect(screen.queryByTestId("respiratory-field-respiratory_treatment_initiated")).toBeNull();
  });

  it("hydrates a previously-saved draft's fields", async () => {
    mocks.getRespiratoryAssessment.mockResolvedValueOnce(
      baseAssessment({
        situation: "new_or_worsening",
        data: { sobSeverity: "Moderate" },
      }),
    );
    render(<RespiratoryPanel patientId={TEST_PATIENT_ID} assessmentId={TEST_ASSESSMENT_ID} />);
    await waitFor(() => expect(screen.getByTestId("respiratory-panel")).toBeTruthy());
    expect(within(screen.getByRole("radiogroup", { name: "SOB Severity" })).getByRole("radio", { name: "Moderate", checked: true })).toBeTruthy();
  });

  it("shows an unauthorized message on a 401/403 response", async () => {
    mocks.getRespiratoryAssessment.mockRejectedValueOnce({ response: { status: 403 } });
    render(<RespiratoryPanel patientId={TEST_PATIENT_ID} assessmentId={TEST_ASSESSMENT_ID} />);
    await waitFor(() => expect(screen.getByText(/not authorized/)).toBeTruthy());
  });

  it("shows an unavailable message on a 404 response", async () => {
    mocks.getRespiratoryAssessment.mockRejectedValueOnce({ response: { status: 404 } });
    render(<RespiratoryPanel patientId={TEST_PATIENT_ID} assessmentId={TEST_ASSESSMENT_ID} />);
    await waitFor(() => expect(screen.getByText(/unavailable/)).toBeTruthy());
  });

  it("shows a retry control on a network error and reloads when clicked", async () => {
    mocks.getRespiratoryAssessment.mockRejectedValueOnce(new Error("network down"));
    render(<RespiratoryPanel patientId={TEST_PATIENT_ID} assessmentId={TEST_ASSESSMENT_ID} />);
    await waitFor(() => expect(screen.getByRole("button", { name: "Retry" })).toBeTruthy());

    mocks.getRespiratoryAssessment.mockResolvedValueOnce(baseAssessment());
    fireEvent.click(screen.getByRole("button", { name: "Retry" }));
    await waitFor(() => expect(screen.getByTestId("respiratory-current-evidence-section")).toBeTruthy());
    expect(mocks.getRespiratoryAssessment).toHaveBeenCalledTimes(2);
  });
});

describe("RespiratoryPanel — assessment limitation is explicit and non-gating", () => {
  beforeEach(() => {
    mocks.getRespiratoryAssessment.mockResolvedValueOnce(baseAssessment());
  });

  it("shows the Assessment limitation section only once 'Unable to fully assess' is checked, without hiding current evidence", async () => {
    render(<RespiratoryPanel patientId={TEST_PATIENT_ID} assessmentId={TEST_ASSESSMENT_ID} />);
    await waitFor(() => expect(screen.getByTestId("respiratory-panel")).toBeTruthy());

    expect(screen.queryByTestId("respiratory-limitation-section")).toBeNull();
    selectExclusive("Assessment Context", "Unable To Fully Assess");

    expect(screen.getByTestId("respiratory-limitation-section")).toBeTruthy();
    expect(screen.getByRole("combobox", { name: "Reason Unable to Assess" })).toBeTruthy();
    // Current evidence stays visible and editable even while limitation is open.
    expect(screen.getByTestId("respiratory-current-evidence-section")).toBeTruthy();
  });

  it("only shows the free-text 'Other reason' field once 'Other' is chosen as the reason", async () => {
    render(<RespiratoryPanel patientId={TEST_PATIENT_ID} assessmentId={TEST_ASSESSMENT_ID} />);
    await waitFor(() => expect(screen.getByTestId("respiratory-panel")).toBeTruthy());

    selectExclusive("Assessment Context", "Unable To Fully Assess");
    expect(screen.queryByRole("textbox", { name: "Other Reason (if selected above)" })).toBeNull();

    selectSingle("Reason Unable to Assess", "Other");

    expect(screen.getByRole("textbox", { name: "Other Reason (if selected above)" })).toBeTruthy();
  });
});

// Product Owner directive ("One clinical fact. One nurse action. One
// source of truth. Assessment Context is canonical.", 2026-10-12): the
// legacy respiratory_no_current_concern / respiratory_unable_to_assess
// checkboxes duplicated Assessment Context's own controlled values and
// are retired as independent nurse-facing controls; they become derived
// compatibility values kept in sync with Assessment Context.
describe("RespiratoryPanel — Assessment Context is the sole source of truth (no duplicate declarations)", () => {
  beforeEach(() => {
    mocks.getRespiratoryAssessment.mockResolvedValueOnce(baseAssessment());
  });

  it("never renders the retired 'No current respiratory concern' / 'Unable to fully assess' checkboxes as standalone controls", async () => {
    render(<RespiratoryPanel patientId={TEST_PATIENT_ID} assessmentId={TEST_ASSESSMENT_ID} />);
    await waitFor(() => expect(screen.getByTestId("respiratory-panel")).toBeTruthy());

    expect(screen.queryByTestId("respiratory-field-respiratory_no_current_concern")).toBeNull();
    expect(screen.queryByTestId("respiratory-field-respiratory_unable_to_assess")).toBeNull();
  });

  it("derives the legacy respiratoryNoCurrentConcern/respiratoryUnableToAssess compatibility keys from the Assessment Context selection on save", async () => {
    mocks.saveRespiratoryDraft.mockResolvedValueOnce(baseAssessment({ version: 2 }));
    render(<RespiratoryPanel patientId={TEST_PATIENT_ID} assessmentId={TEST_ASSESSMENT_ID} />);
    await waitFor(() => expect(screen.getByTestId("respiratory-panel")).toBeTruthy());

    selectExclusive("Assessment Context", "No Current Respiratory Concern");
    fireEvent.click(screen.getByTestId("respiratory-save-button"));

    await waitFor(() => expect(mocks.saveRespiratoryDraft).toHaveBeenCalled());
    const savedData = mocks.saveRespiratoryDraft.mock.calls[0][1].data;
    expect(savedData.respiratoryNoCurrentConcern).toBe(true);
    expect(savedData.respiratoryUnableToAssess).toBe(false);
  });

  it("derives respiratoryUnableToAssess=true and clears respiratoryNoCurrentConcern when Assessment Context is Unable To Fully Assess", async () => {
    mocks.saveRespiratoryDraft.mockResolvedValueOnce(baseAssessment({ version: 2 }));
    render(<RespiratoryPanel patientId={TEST_PATIENT_ID} assessmentId={TEST_ASSESSMENT_ID} />);
    await waitFor(() => expect(screen.getByTestId("respiratory-panel")).toBeTruthy());

    selectExclusive("Assessment Context", "Unable To Fully Assess");
    fireEvent.click(screen.getByTestId("respiratory-save-button"));

    await waitFor(() => expect(mocks.saveRespiratoryDraft).toHaveBeenCalled());
    const savedData = mocks.saveRespiratoryDraft.mock.calls[0][1].data;
    expect(savedData.respiratoryUnableToAssess).toBe(true);
    expect(savedData.respiratoryNoCurrentConcern).toBe(false);
  });

  it("derives both legacy flags false when Assessment Context is Current Concerns Assessed", async () => {
    mocks.saveRespiratoryDraft.mockResolvedValueOnce(baseAssessment({ version: 2 }));
    render(<RespiratoryPanel patientId={TEST_PATIENT_ID} assessmentId={TEST_ASSESSMENT_ID} />);
    await waitFor(() => expect(screen.getByTestId("respiratory-panel")).toBeTruthy());

    selectExclusive("Assessment Context", "Current Concerns Assessed");
    fireEvent.click(screen.getByTestId("respiratory-save-button"));

    await waitFor(() => expect(mocks.saveRespiratoryDraft).toHaveBeenCalled());
    const savedData = mocks.saveRespiratoryDraft.mock.calls[0][1].data;
    expect(savedData.respiratoryNoCurrentConcern).toBe(false);
    expect(savedData.respiratoryUnableToAssess).toBe(false);
  });
});

describe("RespiratoryPanel — field editing", () => {
  it("records a canonical Treatment Decision selection into the editable draft and keeps the legacy compatibility keys in sync", async () => {
    // Intervention fields are progressively disclosed once dyspnea is
    // moderate or severe (usability-first directive section 9/15).
    mocks.getRespiratoryAssessment.mockResolvedValueOnce(
      baseAssessment({ situation: "new_or_worsening", data: { sobSeverity: "Moderate" } }),
    );
    render(<RespiratoryPanel patientId={TEST_PATIENT_ID} assessmentId={TEST_ASSESSMENT_ID} />);
    await waitFor(() => expect(screen.getByTestId("respiratory-panel")).toBeTruthy());

    // The retired legacy "Treatment for shortness of breath initiated" /
    // "Treatment declined" checkboxes must no longer render as standalone
    // nurse-facing controls — Treatment Decision is the sole source of
    // truth now.
    expect(screen.queryByTestId("respiratory-field-respiratory_treatment_initiated")).toBeNull();
    expect(screen.queryByTestId("respiratory-field-respiratory_treatment_declined")).toBeNull();

    const option = within(screen.getByRole("radiogroup", { name: "Treatment Decision" })).getByRole("radio", {
      name: "Initiated",
    });
    expect(option.getAttribute("aria-checked")).toBe("false");
    fireEvent.click(option);
    expect(option.getAttribute("aria-checked")).toBe("true");
  });

  it("clicking the already-selected Treatment Decision pill clears it back to unselected (hospice-usability clear/undo fix)", async () => {
    mocks.getRespiratoryAssessment.mockResolvedValueOnce(
      baseAssessment({ situation: "new_or_worsening", data: { sobSeverity: "Moderate", treatmentDecision: "INITIATED" } }),
    );
    render(<RespiratoryPanel patientId={TEST_PATIENT_ID} assessmentId={TEST_ASSESSMENT_ID} />);
    await waitFor(() => expect(screen.getByTestId("respiratory-panel")).toBeTruthy());

    const group = within(screen.getByRole("radiogroup", { name: "Treatment Decision" }));
    const initiated = group.getByRole("radio", { name: "Initiated" });
    expect(initiated.getAttribute("aria-checked")).toBe("true");

    fireEvent.click(initiated);
    expect(initiated.getAttribute("aria-checked")).toBe("false");
    expect(group.getByRole("radio", { name: "Already In Place" }).getAttribute("aria-checked")).toBe("false");
    expect(group.getByRole("radio", { name: "Declined" }).getAttribute("aria-checked")).toBe("false");
    expect(group.getByRole("radio", { name: "Not Indicated" }).getAttribute("aria-checked")).toBe("false");
  });

  // HOPE field audit: respiratory_treatment_date ("SOB Treatment Date")
  // feeds only HOPE J2040-B reporting and has no nurse-facing control
  // (hidden per the hospice-admission Treatment section simplification).
  // It must be auto-generated when Initiated is selected, and the legacy
  // treatmentInitiated/treatmentDeclined/treatmentDate values must never
  // go stale when the nurse changes or clears the Treatment Decision.
  it("auto-generates a treatment date (and keeps legacy flags in sync) when Treatment Decision is set to Initiated, with no nurse-facing control for it", async () => {
    mocks.getRespiratoryAssessment.mockResolvedValueOnce(
      baseAssessment({ situation: "new_or_worsening", data: { sobSeverity: "Moderate" } }),
    );
    mocks.saveRespiratoryDraft.mockResolvedValueOnce(baseAssessment({ version: 2 }));
    render(<RespiratoryPanel patientId={TEST_PATIENT_ID} assessmentId={TEST_ASSESSMENT_ID} />);
    await waitFor(() => expect(screen.getByTestId("respiratory-panel")).toBeTruthy());

    expect(screen.queryByTestId("respiratory-field-respiratory_treatment_date")).toBeNull();

    fireEvent.click(within(screen.getByRole("radiogroup", { name: "Treatment Decision" })).getByRole("radio", {
      name: "Initiated",
    }));
    expect(screen.queryByTestId("respiratory-field-respiratory_treatment_date")).toBeNull();

    fireEvent.click(screen.getByTestId("respiratory-save-button"));
    await waitFor(() => expect(mocks.saveRespiratoryDraft).toHaveBeenCalled());
    const savedData = mocks.saveRespiratoryDraft.mock.calls[0][1].data;
    expect(savedData.treatmentInitiated).toBe(true);
    expect(savedData.treatmentDeclined).toBe(false);
    expect(typeof savedData.treatmentDate).toBe("string");
    expect(savedData.treatmentDate.length).toBeGreaterThan(0);
  });

  it("resets the legacy treatmentInitiated/treatmentDeclined/treatmentDate flags instead of leaving them stale when Treatment Decision is cleared", async () => {
    mocks.getRespiratoryAssessment.mockResolvedValueOnce(
      baseAssessment({
        situation: "new_or_worsening",
        data: {
          sobSeverity: "Moderate",
          treatmentDecision: "INITIATED",
          treatmentInitiated: true,
          treatmentDeclined: false,
          treatmentDate: "2026-01-01",
        },
      }),
    );
    mocks.saveRespiratoryDraft.mockResolvedValueOnce(baseAssessment({ version: 2 }));
    render(<RespiratoryPanel patientId={TEST_PATIENT_ID} assessmentId={TEST_ASSESSMENT_ID} />);
    await waitFor(() => expect(screen.getByTestId("respiratory-panel")).toBeTruthy());

    const initiated = within(screen.getByRole("radiogroup", { name: "Treatment Decision" })).getByRole("radio", {
      name: "Initiated",
    });
    fireEvent.click(initiated); // clears the decision (clear/undo)

    fireEvent.click(screen.getByTestId("respiratory-save-button"));
    await waitFor(() => expect(mocks.saveRespiratoryDraft).toHaveBeenCalled());
    const savedData = mocks.saveRespiratoryDraft.mock.calls[0][1].data;
    expect(savedData.treatmentInitiated).toBeUndefined();
    expect(savedData.treatmentDeclined).toBeUndefined();
    expect(savedData.treatmentDate).toBeUndefined();
  });

  // Hospice-admission simplification (product-owner "PRODUCT OWNER
  // CORRECTION" directive): the Treatment section must contain exactly
  // Treatment Decision, Treatment Narrative, Follow-Up Needed, and
  // Respiratory Notes — Treatment Action Date/Time, Response, Response
  // Status/Time, Follow-Up Timing Plan/Responsible Clinician, and POC
  // Review Need/Reason/Source Reference must never render, for ANY
  // Treatment Decision value, because hospital-style exact-timing and
  // immediate-effectiveness requirements do not reflect real hospice
  // admission practice.
  describe("hospice-admission Treatment section simplification", () => {
    const hiddenFieldIds = [
      "respiratory_treatment_action_date",
      "respiratory_treatment_action_time",
      "respiratory_treatment_response_time",
      "respiratory_treatment_response",
      "respiratory_treatment_response_status",
      "respiratory_treatment_decline_reason",
      "respiratory_follow_up_timing_plan",
      "respiratory_follow_up_responsible_clinician",
      "respiratory_poc_review_need",
      "respiratory_poc_review_reason",
      "respiratory_poc_source_reference",
      "respiratory_configured_requirement_response",
      "respiratory_configured_follow_up_status",
      "respiratory_treatment_date",
    ];

    it.each(["INITIATED", "ALREADY_IN_PLACE", "DECLINED", "NOT_INDICATED"])(
      "never renders the removed Treatment/follow-up/POC fields when Treatment Decision = %s",
      async (treatmentDecision) => {
        mocks.getRespiratoryAssessment.mockResolvedValueOnce(
          baseAssessment({ situation: "new_or_worsening", data: { sobSeverity: "Moderate", treatmentDecision } }),
        );
        render(<RespiratoryPanel patientId={TEST_PATIENT_ID} assessmentId={TEST_ASSESSMENT_ID} />);
        await waitFor(() => expect(screen.getByTestId("respiratory-panel")).toBeTruthy());

        for (const fieldId of hiddenFieldIds) {
          expect(screen.queryByTestId(`respiratory-field-${fieldId}`)).toBeNull();
        }
      },
    );

    // FINAL PRODUCT-OWNER DIRECTIVE: the free-text "Treatment/Intervention"
    // box duplicated the authoritative Orders/Medications workflow and is
    // removed as an active control for Initiated/Already In Place. Those
    // two values now show Clinical Response to Treatment instead.
    it("shows Clinical Response (not Treatment Narrative) for INITIATED and ALREADY_IN_PLACE", async () => {
      mocks.getRespiratoryAssessment.mockResolvedValueOnce(
        baseAssessment({ situation: "new_or_worsening", data: { sobSeverity: "Moderate", treatmentDecision: "INITIATED" } }),
      );
      render(<RespiratoryPanel patientId={TEST_PATIENT_ID} assessmentId={TEST_ASSESSMENT_ID} />);
      await waitFor(() => expect(screen.getByTestId("respiratory-panel")).toBeTruthy());

      expect(screen.getByTestId("respiratory-field-respiratory_treatment_decision")).toBeTruthy();
      expect(screen.getByTestId("respiratory-field-respiratory_follow_up_need")).toBeTruthy();
      expect(screen.getByTestId("respiratory-field-respiratory_clinical_response")).toBeTruthy();
      expect(screen.queryByTestId("respiratory-field-respiratory_treatment_description")).toBeNull();
    });

    it("keeps Treatment Narrative visible (as Decline Reason/Clinical Rationale) for DECLINED and NOT_INDICATED", async () => {
      mocks.getRespiratoryAssessment.mockResolvedValueOnce(
        baseAssessment({ situation: "new_or_worsening", data: { sobSeverity: "Moderate", treatmentDecision: "DECLINED" } }),
      );
      render(<RespiratoryPanel patientId={TEST_PATIENT_ID} assessmentId={TEST_ASSESSMENT_ID} />);
      await waitFor(() => expect(screen.getByTestId("respiratory-panel")).toBeTruthy());

      expect(screen.getByTestId("respiratory-field-respiratory_treatment_decision")).toBeTruthy();
      expect(screen.getByTestId("respiratory-field-respiratory_treatment_description")).toBeTruthy();
      expect(screen.getByTestId("respiratory-field-respiratory_follow_up_need")).toBeTruthy();
      expect(screen.queryByTestId("respiratory-field-respiratory_clinical_response")).toBeNull();
    });

    it("reuses Treatment Narrative as 'Decline Reason' for DECLINED instead of a separate field", async () => {
      mocks.getRespiratoryAssessment.mockResolvedValueOnce(
        baseAssessment({ situation: "new_or_worsening", data: { sobSeverity: "Moderate", treatmentDecision: "DECLINED" } }),
      );
      render(<RespiratoryPanel patientId={TEST_PATIENT_ID} assessmentId={TEST_ASSESSMENT_ID} />);
      await waitFor(() => expect(screen.getByTestId("respiratory-panel")).toBeTruthy());

      expect(screen.getByRole("textbox", { name: "Decline Reason" })).toBeTruthy();
    });
  });

  // FINAL PRODUCT-OWNER DIRECTIVE: data-ownership correction — Respiratory
  // must not let a nurse re-enter medication/order details that belong
  // exclusively to the authoritative Orders/Medications workflow.
  describe("clinical-response data-ownership correction (FINAL PRODUCT-OWNER DIRECTIVE)", () => {
    it("preserves historical Treatment/Intervention free text read-only for INITIATED/ALREADY_IN_PLACE records predating the correction", async () => {
      mocks.getRespiratoryAssessment.mockResolvedValueOnce(
        baseAssessment({
          situation: "new_or_worsening",
          data: {
            sobSeverity: "Moderate",
            treatmentDecision: "ALREADY_IN_PLACE",
            treatmentDescription: "Budesonide 0.5 mg BID; Duoneb QID",
          },
        }),
      );
      render(<RespiratoryPanel patientId={TEST_PATIENT_ID} assessmentId={TEST_ASSESSMENT_ID} />);
      await waitFor(() => expect(screen.getByTestId("respiratory-panel")).toBeTruthy());

      const legacyBlock = screen.getByTestId("respiratory-legacy-treatment-documentation");
      expect(legacyBlock.textContent).toContain("Budesonide 0.5 mg BID; Duoneb QID");
      // Never editable — no textbox renders this historical value.
      expect(screen.queryByTestId("respiratory-field-respiratory_treatment_description")).toBeNull();
    });

    it("does not render the legacy documentation block when there is no historical value", async () => {
      mocks.getRespiratoryAssessment.mockResolvedValueOnce(
        baseAssessment({ situation: "new_or_worsening", data: { sobSeverity: "Moderate", treatmentDecision: "INITIATED" } }),
      );
      render(<RespiratoryPanel patientId={TEST_PATIENT_ID} assessmentId={TEST_ASSESSMENT_ID} />);
      await waitFor(() => expect(screen.getByTestId("respiratory-panel")).toBeTruthy());

      expect(screen.queryByTestId("respiratory-legacy-treatment-documentation")).toBeNull();
    });

  });

  // Hospice is visit-based, not minute-by-minute event tracking: Visit
  // Date/Type/Timestamp already establish the clinical time reference, so
  // "Comfort / Function Screening Time" is removed entirely. The Date
  // field is likewise hidden from the nurse workflow (see "visit-date
  // default-fill" below) — RNICA is visit-centric, so both the Time and
  // the Date are no longer separate nurse-facing controls.
  describe("comfort/function screening time removal (visit-based documentation directive)", () => {
    it("never renders Comfort / Function Screening Time or Date", async () => {
      mocks.getRespiratoryAssessment.mockResolvedValueOnce(
        baseAssessment({
          situation: "new_or_worsening",
          data: { sobSeverity: "Moderate", comfortFunctionImpact: "IMPACT_PRESENT" },
        }),
      );
      render(<RespiratoryPanel patientId={TEST_PATIENT_ID} assessmentId={TEST_ASSESSMENT_ID} />);
      await waitFor(() => expect(screen.getByTestId("respiratory-panel")).toBeTruthy());

      expect(screen.queryByTestId("respiratory-field-respiratory_comfort_function_screening_time")).toBeNull();
      expect(screen.queryByTestId("respiratory-field-respiratory_comfort_function_screening_date")).toBeNull();
    });
  });

  // PRODUCT-OWNER DECISION ("What unique business purpose remains after
  // Treatment Decision / Clinical Response / Follow-Up Need already exist
  // for SOB?"): Cough Action Decision/Description/Response/Date-Time/
  // Decline Reason have no HOPE, SFV, POC, structured-finding, or
  // narrative ownership and duplicate SOB's own intervention/response
  // fields, so they're retired from the active Respiratory UI entirely —
  // for both a Productive cough and a Declined action, none of the five
  // controls render, while Cough Type and the sputum/hemoptysis findings
  // (the actual assessment findings) remain visible.
  describe("cough action retirement (no HOPE/SFV/POC/structured-finding/narrative ownership)", () => {
    it("never renders Cough Action Decision, Description, Response, or Date/Time for a productive cough", async () => {
      mocks.getRespiratoryAssessment.mockResolvedValueOnce(
        baseAssessment({
          situation: "new_or_worsening",
          data: { coughType: "Productive", coughActionDecision: "ACTION_TAKEN" },
        }),
      );
      render(<RespiratoryPanel patientId={TEST_PATIENT_ID} assessmentId={TEST_ASSESSMENT_ID} />);
      await waitFor(() => expect(screen.getByTestId("respiratory-panel")).toBeTruthy());

      expect(screen.queryByTestId("respiratory-field-respiratory_cough_action_decision")).toBeNull();
      expect(screen.queryByTestId("respiratory-field-respiratory_cough_action_description")).toBeNull();
      expect(screen.queryByTestId("respiratory-field-respiratory_cough_response")).toBeNull();
      expect(screen.queryByTestId("respiratory-field-respiratory_cough_action_date_time")).toBeNull();
      // Cough Type remains an active, visible assessment finding.
      expect(screen.getByTestId("respiratory-field-respiratory_cough_type")).toBeTruthy();
    });

    it("never renders Cough Decline Reason even when a decision was previously declined", async () => {
      mocks.getRespiratoryAssessment.mockResolvedValueOnce(
        baseAssessment({
          situation: "new_or_worsening",
          data: { coughType: "Productive", coughActionDecision: "DECLINED" },
        }),
      );
      render(<RespiratoryPanel patientId={TEST_PATIENT_ID} assessmentId={TEST_ASSESSMENT_ID} />);
      await waitFor(() => expect(screen.getByTestId("respiratory-panel")).toBeTruthy());

      expect(screen.queryByTestId("respiratory-field-respiratory_cough_decline_reason")).toBeNull();
    });
  });

  // PRODUCT-OWNER DECISION ("Permanent Retirement Enforcement" / "Two
  // Authorized Removal States"): Comfort / Function Evidence is
  // RETIRED_FROM_ACTIVE_WORKFLOW (docs/governance/SNS_RETIRED_FEATURES.json,
  // id "respiratory.comfortFunctionEvidence"). It must never render, even
  // when comfortFunctionImpact is a value ("Impact Present" /
  // "Unable to Assess") that previously triggered the free-text follow-up.
  it("never renders Comfort / Function Evidence regardless of Comfort / Functional Impact value", async () => {
    mocks.getRespiratoryAssessment.mockResolvedValueOnce(
      baseAssessment({
        situation: "new_or_worsening",
        data: { assessmentContext: "CURRENT_CONCERNS_ASSESSED", comfortFunctionImpact: "IMPACT_PRESENT" },
      }),
    );
    render(<RespiratoryPanel patientId={TEST_PATIENT_ID} assessmentId={TEST_ASSESSMENT_ID} />);
    await waitFor(() => expect(screen.getByTestId("respiratory-panel")).toBeTruthy());

    expect(screen.queryByTestId("respiratory-field-respiratory_comfort_function_evidence")).toBeNull();
    // Comfort / Functional Impact remains an active, visible finding.
    expect(screen.getByTestId("respiratory-field-respiratory_comfort_function_impact")).toBeTruthy();
    // Documentation Coverage must never surface a Comfort Evidence gap.
    expect(screen.queryByText(/Comfort Evidence/i)).toBeNull();
  });

  // Hospice visit-based documentation directive ("RNICA is visit-centric"):
  // SOB Screening Date and Comfort/Function Screening Date are hidden from
  // the nurse workflow entirely (no visible field, no toggle, no override
  // UI) and silently default to the visit date rather than asking the
  // nurse to re-enter a date for an assessment already being performed
  // during the current documented visit. The default is a one-time fill
  // of a blank field; a date already on the draft (e.g. a historical/
  // late-documented value) is always preserved. A true exception is
  // recorded narratively in Respiratory Notes, not via a structured field.
  describe("visit-date default-fill (hospice visit-based documentation directive)", () => {
    it("never renders a SOB Screening Date or Comfort / Function Screening Date field", async () => {
      mocks.getRespiratoryAssessment.mockResolvedValueOnce(
        baseAssessment({
          situation: "new_or_worsening",
          data: { shortnessOfBreathScreened: true, comfortFunctionImpact: "IMPACT_PRESENT" },
        }),
      );
      render(
        <RespiratoryPanel patientId={TEST_PATIENT_ID} assessmentId={TEST_ASSESSMENT_ID} visitDate="2026-03-14" />,
      );
      await waitFor(() => expect(screen.getByTestId("respiratory-panel")).toBeTruthy());

      expect(screen.queryByTestId("respiratory-field-respiratory_screening_date")).toBeNull();
      expect(screen.queryByTestId("respiratory-field-respiratory_comfort_function_screening_date")).toBeNull();
    });

    it("silently fills the SOB Screening Date from the visit date once SOB has been screened and the date is blank", async () => {
      mocks.getRespiratoryAssessment.mockResolvedValueOnce(
        baseAssessment({ situation: "new_or_worsening", data: { shortnessOfBreathScreened: true } }),
      );
      mocks.saveRespiratoryDraft.mockResolvedValueOnce(baseAssessment({ version: 2 }));
      render(
        <RespiratoryPanel patientId={TEST_PATIENT_ID} assessmentId={TEST_ASSESSMENT_ID} visitDate="2026-03-14" />,
      );
      await waitFor(() => expect(screen.getByTestId("respiratory-panel")).toBeTruthy());

      fireEvent.click(screen.getByTestId("respiratory-save-button"));
      await waitFor(() => expect(mocks.saveRespiratoryDraft).toHaveBeenCalled());
      const savedData = mocks.saveRespiratoryDraft.mock.calls[0][1].data;
      expect(savedData.screeningDate).toBe("2026-03-14");
    });

    it("does not overwrite an already-entered SOB Screening Date with the visit date", async () => {
      mocks.getRespiratoryAssessment.mockResolvedValueOnce(
        baseAssessment({
          situation: "new_or_worsening",
          data: { shortnessOfBreathScreened: true, screeningDate: "2026-02-01" },
        }),
      );
      mocks.saveRespiratoryDraft.mockResolvedValueOnce(baseAssessment({ version: 2 }));
      render(
        <RespiratoryPanel patientId={TEST_PATIENT_ID} assessmentId={TEST_ASSESSMENT_ID} visitDate="2026-03-14" />,
      );
      await waitFor(() => expect(screen.getByTestId("respiratory-panel")).toBeTruthy());

      fireEvent.click(screen.getByTestId("respiratory-save-button"));
      await waitFor(() => expect(mocks.saveRespiratoryDraft).toHaveBeenCalled());
      const savedData = mocks.saveRespiratoryDraft.mock.calls[0][1].data;
      expect(savedData.screeningDate).toBe("2026-02-01");
    });

    it("silently fills the Comfort / Function Screening Date from the visit date once an impact is recorded and the date is blank", async () => {
      mocks.getRespiratoryAssessment.mockResolvedValueOnce(
        baseAssessment({
          situation: "new_or_worsening",
          data: { sobSeverity: "Moderate", comfortFunctionImpact: "IMPACT_PRESENT" },
        }),
      );
      mocks.saveRespiratoryDraft.mockResolvedValueOnce(baseAssessment({ version: 2 }));
      render(
        <RespiratoryPanel patientId={TEST_PATIENT_ID} assessmentId={TEST_ASSESSMENT_ID} visitDate="2026-03-14" />,
      );
      await waitFor(() => expect(screen.getByTestId("respiratory-panel")).toBeTruthy());

      fireEvent.click(screen.getByTestId("respiratory-save-button"));
      await waitFor(() => expect(mocks.saveRespiratoryDraft).toHaveBeenCalled());
      const savedData = mocks.saveRespiratoryDraft.mock.calls[0][1].data;
      expect(savedData.comfortFunctionScreeningDate).toBe("2026-03-14");
    });

    it("leaves both screening dates unset when no visitDate prop is supplied", async () => {
      mocks.getRespiratoryAssessment.mockResolvedValueOnce(
        baseAssessment({
          situation: "new_or_worsening",
          data: { shortnessOfBreathScreened: true, comfortFunctionImpact: "IMPACT_PRESENT" },
        }),
      );
      mocks.saveRespiratoryDraft.mockResolvedValueOnce(baseAssessment({ version: 2 }));
      render(<RespiratoryPanel patientId={TEST_PATIENT_ID} assessmentId={TEST_ASSESSMENT_ID} />);
      await waitFor(() => expect(screen.getByTestId("respiratory-panel")).toBeTruthy());

      fireEvent.click(screen.getByTestId("respiratory-save-button"));
      await waitFor(() => expect(mocks.saveRespiratoryDraft).toHaveBeenCalled());
      const savedData = mocks.saveRespiratoryDraft.mock.calls[0][1].data;
      expect(savedData.screeningDate).toBeUndefined();
      expect(savedData.comfortFunctionScreeningDate).toBeUndefined();
    });
  });

  // Hospice admission Treatment simplification + RNICA visit-centricity:
  // respiratory_treatment_date (HOPE J2040-B reporting-only) now prefers
  // the RNICA visit date over today's date, since the RN is documenting
  // during that visit, not necessarily on today's calendar date.
  describe("treatment date auto-generation uses the visit date when available", () => {
    it("uses the visitDate prop instead of today's date when Treatment Decision becomes Initiated", async () => {
      mocks.getRespiratoryAssessment.mockResolvedValueOnce(
        baseAssessment({ situation: "new_or_worsening", data: { sobSeverity: "Moderate" } }),
      );
      mocks.saveRespiratoryDraft.mockResolvedValueOnce(baseAssessment({ version: 2 }));
      render(
        <RespiratoryPanel patientId={TEST_PATIENT_ID} assessmentId={TEST_ASSESSMENT_ID} visitDate="2026-03-14" />,
      );
      await waitFor(() => expect(screen.getByTestId("respiratory-panel")).toBeTruthy());

      fireEvent.click(within(screen.getByRole("radiogroup", { name: "Treatment Decision" })).getByRole("radio", {
        name: "Initiated",
      }));

      fireEvent.click(screen.getByTestId("respiratory-save-button"));
      await waitFor(() => expect(mocks.saveRespiratoryDraft).toHaveBeenCalled());
      const savedData = mocks.saveRespiratoryDraft.mock.calls[0][1].data;
      expect(savedData.treatmentDate).toBe("2026-03-14");
    });
  });

  it("records a free-text notes entry", async () => {
    mocks.getRespiratoryAssessment.mockResolvedValueOnce(baseAssessment());
    render(<RespiratoryPanel patientId={TEST_PATIENT_ID} assessmentId={TEST_ASSESSMENT_ID} />);
    await waitFor(() => expect(screen.getByTestId("respiratory-panel")).toBeTruthy());

    const notes = screen.getByRole("textbox", { name: "Respiratory Notes" }) as HTMLTextAreaElement;
    fireEvent.change(notes, { target: { value: "Patient reports improved breathing today." } });
    expect(notes.value).toBe("Patient reports improved breathing today.");
  });
});

describe("RespiratoryPanel — draft save is always available", () => {
  it("draft save is enabled even with nothing entered yet", async () => {
    mocks.getRespiratoryAssessment.mockResolvedValueOnce(baseAssessment());
    render(<RespiratoryPanel patientId={TEST_PATIENT_ID} assessmentId={TEST_ASSESSMENT_ID} />);
    await waitFor(() => expect(screen.getByTestId("respiratory-panel")).toBeTruthy());
    const saveButton = screen.getByTestId("respiratory-save-button") as HTMLButtonElement;
    expect(saveButton.disabled).toBe(false);
  });

  it("saves an incomplete draft successfully as IN_PROGRESS", async () => {
    mocks.getRespiratoryAssessment.mockResolvedValueOnce(baseAssessment());
    mocks.saveRespiratoryDraft.mockResolvedValueOnce(baseAssessment({ version: 2, reviewState: "in_progress" }));
    render(<RespiratoryPanel patientId={TEST_PATIENT_ID} assessmentId={TEST_ASSESSMENT_ID} />);
    await waitFor(() => expect(screen.getByTestId("respiratory-panel")).toBeTruthy());

    fireEvent.click(screen.getByTestId("respiratory-save-button"));

    await waitFor(() => expect(screen.getByTestId("respiratory-save-status").textContent).toContain("Saved"));
    expect(mocks.saveRespiratoryDraft).toHaveBeenCalledWith(
      TEST_ASSESSMENT_ID,
      expect.objectContaining({ reviewState: "in_progress", expectedVersion: 1 }),
    );
  });

  it("shows a failed-save message with a retry control, and retry succeeds", async () => {
    mocks.getRespiratoryAssessment.mockResolvedValueOnce(baseAssessment());
    mocks.saveRespiratoryDraft.mockRejectedValueOnce(new Error("network down"));
    render(<RespiratoryPanel patientId={TEST_PATIENT_ID} assessmentId={TEST_ASSESSMENT_ID} />);
    await waitFor(() => expect(screen.getByTestId("respiratory-panel")).toBeTruthy());

    fireEvent.click(screen.getByTestId("respiratory-save-button"));
    await waitFor(() => expect(screen.getByTestId("respiratory-save-status").textContent).toContain("Save failed"));

    mocks.saveRespiratoryDraft.mockResolvedValueOnce(baseAssessment({ version: 2 }));
    fireEvent.click(screen.getByRole("button", { name: "Retry" }));
    await waitFor(() => expect(screen.getByTestId("respiratory-save-status").textContent).toContain("Saved"));
  });

  it("shows a stale-version conflict message with a reload control, and reload re-hydrates", async () => {
    mocks.getRespiratoryAssessment.mockResolvedValueOnce(baseAssessment());
    mocks.saveRespiratoryDraft.mockRejectedValueOnce(new RespiratoryStaleVersionError());
    render(<RespiratoryPanel patientId={TEST_PATIENT_ID} assessmentId={TEST_ASSESSMENT_ID} />);
    await waitFor(() => expect(screen.getByTestId("respiratory-panel")).toBeTruthy());

    fireEvent.click(screen.getByTestId("respiratory-save-button"));
    await waitFor(() => expect(screen.getByTestId("respiratory-save-status").textContent).toContain("Save blocked"));

    mocks.getRespiratoryAssessment.mockResolvedValueOnce(
      baseAssessment({ situation: "new_or_worsening", version: 3 }),
    );
    fireEvent.click(screen.getByRole("button", { name: "Reload latest" }));
    await waitFor(() => expect(mocks.getRespiratoryAssessment).toHaveBeenCalledTimes(2));
  });
});

describe("RespiratoryPanel — Complete system review is explicit and blocking-validated", () => {
  it("blocks completion and lists what is missing when nothing has been entered", async () => {
    mocks.getRespiratoryAssessment.mockResolvedValueOnce(baseAssessment());
    render(<RespiratoryPanel patientId={TEST_PATIENT_ID} assessmentId={TEST_ASSESSMENT_ID} />);
    await waitFor(() => expect(screen.getByTestId("respiratory-panel")).toBeTruthy());

    // ADR-004: the legacy single "completion blockers" banner is replaced
    // by the Documentation Coverage inventory plus a separate Legacy
    // Respiratory Workflow Alerts section -- both still gate completion.
    expect(screen.getByTestId("respiratory-documentation-coverage")).toBeTruthy();
    expect(screen.getByTestId("respiratory-legacy-workflow-alerts")).toBeTruthy();
    const completeButton = screen.getByTestId("respiratory-complete-review-button") as HTMLButtonElement;
    expect(completeButton.disabled).toBe(true);
    expect(mocks.saveRespiratoryDraft).not.toHaveBeenCalled();
  });

  it("enables completion once the explicit 'no current concern' declaration is checked", async () => {
    mocks.getRespiratoryAssessment.mockResolvedValueOnce(baseAssessment());
    mocks.saveRespiratoryDraft.mockResolvedValueOnce(
      baseAssessment({ situation: "no_current_concern", version: 2, reviewState: "reviewed" }),
    );
    render(<RespiratoryPanel patientId={TEST_PATIENT_ID} assessmentId={TEST_ASSESSMENT_ID} />);
    await waitFor(() => expect(screen.getByTestId("respiratory-panel")).toBeTruthy());

    selectExclusive("Assessment Context", "No Current Respiratory Concern");
    selectExclusive("Comparison to Prior", "Comparison Unavailable");
    selectExclusive("Oxygen Use", "No");
    selectExclusive("Cough Type", "None");
    selectExclusive("Respiratory Support Status", "None");

    const completeButton = screen.getByTestId("respiratory-complete-review-button") as HTMLButtonElement;
    expect(completeButton.disabled).toBe(false);
    fireEvent.click(completeButton);

    await waitFor(() => expect(mocks.saveRespiratoryDraft).toHaveBeenCalled());
    expect(mocks.saveRespiratoryDraft).toHaveBeenCalledWith(
      TEST_ASSESSMENT_ID,
      expect.objectContaining({ situation: "no_current_concern", reviewState: "reviewed" }),
    );
  });

  it("surfaces a record-blocking review exception for a missing unable-to-assess reason, computed client-side on completion", async () => {
    mocks.getRespiratoryAssessment.mockResolvedValueOnce(baseAssessment());
    mocks.saveRespiratoryDraft.mockResolvedValueOnce(
      baseAssessment({
        situation: "unable_to_assess",
        reviewState: "reviewed_with_exception",
        version: 2,
        openReviewExceptions: [
          {
            id: "exc-1",
            type: "unable_to_assess",
            message: "Reason unable to assess is required.",
            blockingLevel: "record_blocking",
            fieldPath: "respiratory_unable_to_assess_reason",
          },
        ],
      }),
    );
    render(<RespiratoryPanel patientId={TEST_PATIENT_ID} assessmentId={TEST_ASSESSMENT_ID} />);
    await waitFor(() => expect(screen.getByTestId("respiratory-panel")).toBeTruthy());

    selectExclusive("Assessment Context", "Unable To Fully Assess");
    selectSingle("Reason Unable to Assess", "Patient unresponsive");
    selectExclusive("Comparison to Prior", "Comparison Unavailable");
    selectExclusive("Oxygen Use", "No");
    selectExclusive("Cough Type", "None");
    selectExclusive("Respiratory Support Status", "None");
    // Assessment Context = Unable To Fully Assess also requires Comfort /
    // Functional Impact (respiratoryProductRequirements.ts), independent
    // of this test's own "missing unable-to-assess reason" scenario.
    selectExclusive("Comfort / Functional Impact", "Unable To Assess");

    fireEvent.click(screen.getByTestId("respiratory-complete-review-button"));

    await waitFor(() => expect(screen.getByTestId("respiratory-review-exceptions")).toBeTruthy());
    const exceptionLink = within(screen.getByTestId("respiratory-review-exceptions")).getByRole("link", {
      name: "Reason unable to assess is required.",
    });
    expect(exceptionLink.getAttribute("href")).toBe("#respiratory_unable_to_assess_reason");
  });
});

describe("RespiratoryPanel — no scope leakage", () => {
  it("never renders eligibility, certification, order, or AI-action controls", async () => {
    mocks.getRespiratoryAssessment.mockResolvedValueOnce(baseAssessment());
    render(<RespiratoryPanel patientId={TEST_PATIENT_ID} assessmentId={TEST_ASSESSMENT_ID} />);
    await waitFor(() => expect(screen.getByTestId("respiratory-panel")).toBeTruthy());

    expect(screen.queryByText(/eligib/i)).toBeNull();
    expect(screen.queryByText(/certif/i)).toBeNull();
    expect(screen.queryByRole("button", { name: /order/i })).toBeNull();
    expect(screen.queryByRole("button", { name: /ai action/i })).toBeNull();
    expect(screen.queryByText(/real patient/i)).toBeNull();
  });
});
