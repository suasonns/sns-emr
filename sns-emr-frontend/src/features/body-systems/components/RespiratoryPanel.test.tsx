import { describe, it, expect } from "vitest";
import { render, screen, fireEvent, within } from "@testing-library/react";
import { useState } from "react";
import { RespiratoryPanel } from "./RespiratoryPanel";

// Same mocking convention as BodySystemsWorkspace.test.tsx: this repo has
// no `@testing-library/user-event`/`jest-dom`, so these tests use
// `fireEvent` + plain `screen` queries throughout.

/**
 * RespiratoryPanel is a plain controlled component now (matching every
 * other body system): `value` + `onChange(patch)`, no network, no draft
 * persistence, no loading states. This harness is a thin stateful wrapper
 * that seeds an initial draft and re-renders synchronously whenever the
 * panel reports a patch, so tests can read back the fully merged current
 * draft at any point via `getDraft()` without any `waitFor`/button click.
 */
type RespiratoryDraftLike = Record<string, unknown>;

function Harness({
  initialData,
  visitDate,
  readOnly,
  onDraftChange,
}: {
  initialData?: RespiratoryDraftLike;
  visitDate?: string;
  readOnly?: boolean;
  onDraftChange: (draft: RespiratoryDraftLike) => void;
}) {
  const [draft, setDraft] = useState<RespiratoryDraftLike>(initialData ?? {});
  return (
    <RespiratoryPanel
      value={draft as any}
      onChange={(patch: Partial<RespiratoryDraftLike>) => {
        setDraft((prev) => {
          const next = { ...prev, ...patch };
          onDraftChange(next);
          return next;
        });
      }}
      visitDate={visitDate}
      readOnly={readOnly}
    />
  );
}

function renderPanel(options: { data?: RespiratoryDraftLike; visitDate?: string; readOnly?: boolean } = {}) {
  let draft: RespiratoryDraftLike = { ...(options.data ?? {}) };
  const utils = render(
    <Harness
      initialData={options.data}
      visitDate={options.visitDate}
      readOnly={options.readOnly}
      onDraftChange={(next) => {
        draft = next;
      }}
    />,
  );
  return { ...utils, getDraft: () => draft };
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

describe("RespiratoryPanel — renders immediately from the controlled draft", () => {
  it("renders every current-evidence field immediately — no upfront selector gates them", () => {
    renderPanel();
    expect(screen.getByTestId("respiratory-panel")).toBeTruthy();
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

  it("hydrates a previously-seeded draft's fields", () => {
    renderPanel({ data: { sobSeverity: "Moderate" } });
    expect(within(screen.getByRole("radiogroup", { name: "SOB Severity" })).getByRole("radio", { name: "Moderate", checked: true })).toBeTruthy();
  });
});

describe("RespiratoryPanel — assessment limitation is explicit and non-gating", () => {
  it("shows the Assessment limitation section only once 'Unable to fully assess' is checked, without hiding current evidence", () => {
    renderPanel();

    expect(screen.queryByTestId("respiratory-limitation-section")).toBeNull();
    selectExclusive("Assessment Context", "Unable To Fully Assess");

    expect(screen.getByTestId("respiratory-limitation-section")).toBeTruthy();
    expect(screen.getByRole("combobox", { name: "Reason Unable to Assess" })).toBeTruthy();
    // Current evidence stays visible and editable even while limitation is open.
    expect(screen.getByTestId("respiratory-current-evidence-section")).toBeTruthy();
  });

  it("only shows the free-text 'Other reason' field once 'Other' is chosen as the reason", () => {
    renderPanel();

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
  it("never renders the retired 'No current respiratory concern' / 'Unable to fully assess' checkboxes as standalone controls", () => {
    renderPanel();

    expect(screen.queryByTestId("respiratory-field-respiratory_no_current_concern")).toBeNull();
    expect(screen.queryByTestId("respiratory-field-respiratory_unable_to_assess")).toBeNull();
  });

  it("derives the legacy respiratoryNoCurrentConcern/respiratoryUnableToAssess compatibility keys from the Assessment Context selection", () => {
    const { getDraft } = renderPanel();

    selectExclusive("Assessment Context", "No Current Respiratory Concern");

    const savedData = getDraft();
    expect(savedData.respiratoryNoCurrentConcern).toBe(true);
    expect(savedData.respiratoryUnableToAssess).toBe(false);
  });

  it("derives respiratoryUnableToAssess=true and clears respiratoryNoCurrentConcern when Assessment Context is Unable To Fully Assess", () => {
    const { getDraft } = renderPanel();

    selectExclusive("Assessment Context", "Unable To Fully Assess");

    const savedData = getDraft();
    expect(savedData.respiratoryUnableToAssess).toBe(true);
    expect(savedData.respiratoryNoCurrentConcern).toBe(false);
  });

  it("derives both legacy flags false when Assessment Context is Current Concerns Assessed", () => {
    const { getDraft } = renderPanel();

    selectExclusive("Assessment Context", "Current Concerns Assessed");

    const savedData = getDraft();
    expect(savedData.respiratoryNoCurrentConcern).toBe(false);
    expect(savedData.respiratoryUnableToAssess).toBe(false);
  });
});

describe("RespiratoryPanel — field editing", () => {
  it("records a canonical Treatment Decision selection into the editable draft and keeps the legacy compatibility keys in sync", () => {
    // Intervention fields are progressively disclosed once dyspnea is
    // moderate or severe (usability-first directive section 9/15).
    renderPanel({ data: { sobSeverity: "Moderate" } });

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

  it("clicking the already-selected Treatment Decision pill clears it back to unselected (hospice-usability clear/undo fix)", () => {
    renderPanel({ data: { sobSeverity: "Moderate", treatmentDecision: "INITIATED" } });

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
  it("auto-generates a treatment date (and keeps legacy flags in sync) when Treatment Decision is set to Initiated, with no nurse-facing control for it", () => {
    const { getDraft } = renderPanel({ data: { sobSeverity: "Moderate" } });

    expect(screen.queryByTestId("respiratory-field-respiratory_treatment_date")).toBeNull();

    fireEvent.click(within(screen.getByRole("radiogroup", { name: "Treatment Decision" })).getByRole("radio", {
      name: "Initiated",
    }));
    expect(screen.queryByTestId("respiratory-field-respiratory_treatment_date")).toBeNull();

    const savedData = getDraft();
    expect(savedData.treatmentInitiated).toBe(true);
    expect(savedData.treatmentDeclined).toBe(false);
    expect(typeof savedData.treatmentDate).toBe("string");
    expect((savedData.treatmentDate as string).length).toBeGreaterThan(0);
  });

  it("resets the legacy treatmentInitiated/treatmentDeclined/treatmentDate flags instead of leaving them stale when Treatment Decision is cleared", () => {
    const { getDraft } = renderPanel({
      data: {
        sobSeverity: "Moderate",
        treatmentDecision: "INITIATED",
        treatmentInitiated: true,
        treatmentDeclined: false,
        treatmentDate: "2026-01-01",
      },
    });

    const initiated = within(screen.getByRole("radiogroup", { name: "Treatment Decision" })).getByRole("radio", {
      name: "Initiated",
    });
    fireEvent.click(initiated); // clears the decision (clear/undo)

    const savedData = getDraft();
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
      (treatmentDecision) => {
        renderPanel({ data: { sobSeverity: "Moderate", treatmentDecision } });

        for (const fieldId of hiddenFieldIds) {
          expect(screen.queryByTestId(`respiratory-field-${fieldId}`)).toBeNull();
        }
      },
    );

    // FINAL PRODUCT-OWNER DIRECTIVE: the free-text "Treatment/Intervention"
    // box duplicated the authoritative Orders/Medications workflow and is
    // removed as an active control for Initiated/Already In Place.
    // Respiratory Field Redundancy Review (PRODUCT OWNER REVIEW): the
    // "Clinical Response" field that previously replaced it was itself a
    // pure duplicate of structured Respiratory data and was removed
    // entirely — no field renders in its place for either value.
    it("renders neither Treatment Narrative nor a Clinical Response field for INITIATED and ALREADY_IN_PLACE", () => {
      renderPanel({ data: { sobSeverity: "Moderate", treatmentDecision: "INITIATED" } });

      expect(screen.getByTestId("respiratory-field-respiratory_treatment_decision")).toBeTruthy();
      expect(screen.getByTestId("respiratory-field-respiratory_follow_up_need")).toBeTruthy();
      expect(screen.queryByTestId("respiratory-field-respiratory_clinical_response")).toBeNull();
      expect(screen.queryByTestId("respiratory-field-respiratory_treatment_description")).toBeNull();
    });

    it("keeps Treatment Narrative visible (as Decline Reason/Clinical Rationale) for DECLINED and NOT_INDICATED", () => {
      renderPanel({ data: { sobSeverity: "Moderate", treatmentDecision: "DECLINED" } });

      expect(screen.getByTestId("respiratory-field-respiratory_treatment_decision")).toBeTruthy();
      expect(screen.getByTestId("respiratory-field-respiratory_treatment_description")).toBeTruthy();
      expect(screen.getByTestId("respiratory-field-respiratory_follow_up_need")).toBeTruthy();
      expect(screen.queryByTestId("respiratory-field-respiratory_clinical_response")).toBeNull();
    });

    it("reuses Treatment Narrative as 'Decline Reason' for DECLINED instead of a separate field", () => {
      renderPanel({ data: { sobSeverity: "Moderate", treatmentDecision: "DECLINED" } });

      expect(screen.getByRole("textbox", { name: "Decline Reason" })).toBeTruthy();
    });
  });

  // FINAL PRODUCT-OWNER DIRECTIVE: data-ownership correction — Respiratory
  // must not let a nurse re-enter medication/order details that belong
  // exclusively to the authoritative Orders/Medications workflow.
  describe("clinical-response data-ownership correction (FINAL PRODUCT-OWNER DIRECTIVE)", () => {
    it("preserves historical Treatment/Intervention free text read-only for INITIATED/ALREADY_IN_PLACE records predating the correction", () => {
      renderPanel({
        data: {
          sobSeverity: "Moderate",
          treatmentDecision: "ALREADY_IN_PLACE",
          treatmentDescription: "Budesonide 0.5 mg BID; Duoneb QID",
        },
      });

      const legacyBlock = screen.getByTestId("respiratory-legacy-treatment-documentation");
      expect(legacyBlock.textContent).toContain("Budesonide 0.5 mg BID; Duoneb QID");
      // Never editable — no textbox renders this historical value.
      expect(screen.queryByTestId("respiratory-field-respiratory_treatment_description")).toBeNull();
    });

    it("does not render the legacy documentation block when there is no historical value", () => {
      renderPanel({ data: { sobSeverity: "Moderate", treatmentDecision: "INITIATED" } });

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
    it("never renders Comfort / Function Screening Time or Date", () => {
      renderPanel({ data: { sobSeverity: "Moderate", comfortFunctionImpact: "IMPACT_PRESENT" } });

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
    it("never renders Cough Action Decision, Description, Response, or Date/Time for a productive cough", () => {
      renderPanel({ data: { coughType: "Productive", coughActionDecision: "ACTION_TAKEN" } });

      expect(screen.queryByTestId("respiratory-field-respiratory_cough_action_decision")).toBeNull();
      expect(screen.queryByTestId("respiratory-field-respiratory_cough_action_description")).toBeNull();
      expect(screen.queryByTestId("respiratory-field-respiratory_cough_response")).toBeNull();
      expect(screen.queryByTestId("respiratory-field-respiratory_cough_action_date_time")).toBeNull();
      // Cough Type remains an active, visible assessment finding.
      expect(screen.getByTestId("respiratory-field-respiratory_cough_type")).toBeTruthy();
    });

    it("never renders Cough Decline Reason even when a decision was previously declined", () => {
      renderPanel({ data: { coughType: "Productive", coughActionDecision: "DECLINED" } });

      expect(screen.queryByTestId("respiratory-field-respiratory_cough_decline_reason")).toBeNull();
    });
  });

  // PRODUCT-OWNER DECISION ("Permanent Retirement Enforcement" / "Two
  // Authorized Removal States"): Comfort / Function Evidence is
  // RETIRED_FROM_ACTIVE_WORKFLOW (docs/governance/SNS_RETIRED_FEATURES.json,
  // id "respiratory.comfortFunctionEvidence"). It must never render, even
  // when comfortFunctionImpact is a value ("Impact Present" /
  // "Unable to Assess") that previously triggered the free-text follow-up.
  it("never renders Comfort / Function Evidence regardless of Comfort / Functional Impact value", () => {
    renderPanel({ data: { assessmentContext: "CURRENT_CONCERNS_ASSESSED", comfortFunctionImpact: "IMPACT_PRESENT" } });

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
    it("never renders a SOB Screening Date or Comfort / Function Screening Date field", () => {
      renderPanel({
        data: { shortnessOfBreathScreened: true, comfortFunctionImpact: "IMPACT_PRESENT" },
        visitDate: "2026-03-14",
      });

      expect(screen.queryByTestId("respiratory-field-respiratory_screening_date")).toBeNull();
      expect(screen.queryByTestId("respiratory-field-respiratory_comfort_function_screening_date")).toBeNull();
    });

    it("silently fills the SOB Screening Date from the visit date once SOB has been screened and the date is blank", () => {
      const { getDraft } = renderPanel({
        data: { shortnessOfBreathScreened: true },
        visitDate: "2026-03-14",
      });

      const savedData = getDraft();
      expect(savedData.screeningDate).toBe("2026-03-14");
    });

    it("does not overwrite an already-entered SOB Screening Date with the visit date", () => {
      const { getDraft } = renderPanel({
        data: { shortnessOfBreathScreened: true, screeningDate: "2026-02-01" },
        visitDate: "2026-03-14",
      });

      const savedData = getDraft();
      expect(savedData.screeningDate).toBe("2026-02-01");
    });

    it("silently fills the Comfort / Function Screening Date from the visit date once an impact is recorded and the date is blank", () => {
      const { getDraft } = renderPanel({
        data: { sobSeverity: "Moderate", comfortFunctionImpact: "IMPACT_PRESENT" },
        visitDate: "2026-03-14",
      });

      const savedData = getDraft();
      expect(savedData.comfortFunctionScreeningDate).toBe("2026-03-14");
    });

    it("leaves both screening dates unset when no visitDate prop is supplied", () => {
      const { getDraft } = renderPanel({
        data: { shortnessOfBreathScreened: true, comfortFunctionImpact: "IMPACT_PRESENT" },
      });

      const savedData = getDraft();
      expect(savedData.screeningDate).toBeUndefined();
      expect(savedData.comfortFunctionScreeningDate).toBeUndefined();
    });
  });

  // Hospice admission Treatment simplification + RNICA visit-centricity:
  // respiratory_treatment_date (HOPE J2040-B reporting-only) now prefers
  // the RNICA visit date over today's date, since the RN is documenting
  // during that visit, not necessarily on today's calendar date.
  describe("treatment date auto-generation uses the visit date when available", () => {
    it("uses the visitDate prop instead of today's date when Treatment Decision becomes Initiated", () => {
      const { getDraft } = renderPanel({ data: { sobSeverity: "Moderate" }, visitDate: "2026-03-14" });

      fireEvent.click(within(screen.getByRole("radiogroup", { name: "Treatment Decision" })).getByRole("radio", {
        name: "Initiated",
      }));

      const savedData = getDraft();
      expect(savedData.treatmentDate).toBe("2026-03-14");
    });
  });

  it("records a free-text notes entry", () => {
    renderPanel();

    const notes = screen.getByRole("textbox", { name: "Respiratory Notes" }) as HTMLTextAreaElement;
    fireEvent.change(notes, { target: { value: "Patient reports improved breathing today." } });
    expect(notes.value).toBe("Patient reports improved breathing today.");
  });
});

// ADR-004: the Documentation Coverage inventory and the Legacy
// Respiratory Workflow Alerts section are both pure, derived-from-draft
// UI (computed via `computeRespiratoryDocumentationCoverage(draft)` and
// `getRespiratoryReviewCompletion(draft)` respectively) and are unrelated
// to the removed Save Draft / Complete System Review workflow — they
// render unconditionally, with no button click required.
describe("RespiratoryPanel — documentation banners", () => {
  it("shows the Documentation Coverage and Legacy Respiratory Workflow Alerts banners when nothing has been entered yet", () => {
    renderPanel();

    expect(screen.getByTestId("respiratory-documentation-coverage")).toBeTruthy();
    expect(screen.getByTestId("respiratory-legacy-workflow-alerts")).toBeTruthy();
  });
});

describe("RespiratoryPanel — no scope leakage", () => {
  it("never renders eligibility, certification, order, or AI-action controls", () => {
    renderPanel();

    expect(screen.queryByText(/eligib/i)).toBeNull();
    expect(screen.queryByText(/certif/i)).toBeNull();
    expect(screen.queryByRole("button", { name: /order/i })).toBeNull();
    expect(screen.queryByRole("button", { name: /ai action/i })).toBeNull();
    expect(screen.queryByText(/real patient/i)).toBeNull();
  });
});
