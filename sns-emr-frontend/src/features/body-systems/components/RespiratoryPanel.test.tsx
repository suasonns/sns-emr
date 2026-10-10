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
    expect(within(screen.getByRole("combobox", { name: "SOB Severity" })).getByText("Moderate")).toBeTruthy();
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
    const toggle = within(screen.getByTestId("respiratory-field-respiratory_unable_to_assess")).getByRole("checkbox");
    fireEvent.click(toggle);

    expect(screen.getByTestId("respiratory-limitation-section")).toBeTruthy();
    expect(screen.getByRole("combobox", { name: "Reason Unable to Assess" })).toBeTruthy();
    // Current evidence stays visible and editable even while limitation is open.
    expect(screen.getByTestId("respiratory-current-evidence-section")).toBeTruthy();
  });

  it("only shows the free-text 'Other reason' field once 'Other' is chosen as the reason", async () => {
    render(<RespiratoryPanel patientId={TEST_PATIENT_ID} assessmentId={TEST_ASSESSMENT_ID} />);
    await waitFor(() => expect(screen.getByTestId("respiratory-panel")).toBeTruthy());

    fireEvent.click(within(screen.getByTestId("respiratory-field-respiratory_unable_to_assess")).getByRole("checkbox"));
    expect(screen.queryByRole("textbox", { name: "Other Reason (if selected above)" })).toBeNull();

    selectSingle("Reason Unable to Assess", "Other");

    expect(screen.getByRole("textbox", { name: "Other Reason (if selected above)" })).toBeTruthy();
  });
});

describe("RespiratoryPanel — field editing", () => {
  it("records a boolean field toggle (treatment initiated) into the editable draft", async () => {
    // Intervention fields are progressively disclosed once dyspnea is
    // moderate or severe (usability-first directive section 9/15).
    mocks.getRespiratoryAssessment.mockResolvedValueOnce(
      baseAssessment({ situation: "new_or_worsening", data: { sobSeverity: "Moderate" } }),
    );
    render(<RespiratoryPanel patientId={TEST_PATIENT_ID} assessmentId={TEST_ASSESSMENT_ID} />);
    await waitFor(() => expect(screen.getByTestId("respiratory-panel")).toBeTruthy());

    const checkbox = within(screen.getByTestId("respiratory-field-respiratory_treatment_initiated")).getByRole(
      "checkbox",
    );
    expect(checkbox.getAttribute("aria-checked")).toBe("false");
    fireEvent.click(checkbox);
    expect(checkbox.getAttribute("aria-checked")).toBe("true");
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

    expect(screen.getByTestId("respiratory-completion-blockers")).toBeTruthy();
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

    fireEvent.click(within(screen.getByTestId("respiratory-field-respiratory_no_current_concern")).getByRole("checkbox"));

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

    fireEvent.click(within(screen.getByTestId("respiratory-field-respiratory_unable_to_assess")).getByRole("checkbox"));
    selectSingle("Reason Unable to Assess", "Patient unresponsive");

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
