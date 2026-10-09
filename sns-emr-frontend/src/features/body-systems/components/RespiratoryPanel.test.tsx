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

function baseAssessment(overrides: Partial<RespiratoryAssessmentDTO> = {}): RespiratoryAssessmentDTO {
  return {
    id: "sa-1",
    bodySystemsAssessmentId: "bsa-1",
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

function selectOverview(value: string) {
  const trigger = screen.getByRole("combobox", { name: "Respiratory Overview" });
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
    render(<RespiratoryPanel patientId={TEST_PATIENT_ID} />);
    expect(screen.getByRole("status").textContent).toContain("Loading Respiratory assessment");
  });

  it("renders an empty-draft form when no prior data exists", async () => {
    mocks.getRespiratoryAssessment.mockResolvedValueOnce(baseAssessment());
    render(<RespiratoryPanel patientId={TEST_PATIENT_ID} />);
    await waitFor(() => expect(screen.getByTestId("respiratory-panel")).toBeTruthy());
    expect(screen.getByRole("combobox", { name: "Respiratory Overview" })).toBeTruthy();
    // No situation chosen yet defaults to the non-"unable to assess" branch
    // (current evidence / interventions / follow-up), never the
    // Limitations section, which is gated strictly on
    // situation === "unable_to_assess".
    expect(screen.queryByTestId("respiratory-limitation-section")).toBeNull();
    expect(screen.getByTestId("respiratory-current-evidence-section")).toBeTruthy();
  });

  it("hydrates a previously-saved draft's fields", async () => {
    mocks.getRespiratoryAssessment.mockResolvedValueOnce(
      baseAssessment({
        situation: "new_or_worsening",
        data: { respiratoryOverview: "New or Worsening Respiratory Findings", sobSeverity: "Moderate" },
      }),
    );
    render(<RespiratoryPanel patientId={TEST_PATIENT_ID} />);
    await waitFor(() => expect(screen.getByTestId("respiratory-panel")).toBeTruthy());
    expect(within(screen.getByRole("combobox", { name: "Respiratory Overview" })).getByText(
      "New or Worsening Respiratory Findings",
    )).toBeTruthy();
    expect(screen.getByTestId("respiratory-current-evidence-section")).toBeTruthy();
  });

  it("shows an unauthorized message on a 401/403 response", async () => {
    mocks.getRespiratoryAssessment.mockRejectedValueOnce({ response: { status: 403 } });
    render(<RespiratoryPanel patientId={TEST_PATIENT_ID} />);
    await waitFor(() => expect(screen.getByText(/not authorized/)).toBeTruthy());
  });

  it("shows an unavailable message on a 404 response", async () => {
    mocks.getRespiratoryAssessment.mockRejectedValueOnce({ response: { status: 404 } });
    render(<RespiratoryPanel patientId={TEST_PATIENT_ID} />);
    await waitFor(() => expect(screen.getByText(/unavailable/)).toBeTruthy());
  });

  it("shows a retry control on a network error and reloads when clicked", async () => {
    mocks.getRespiratoryAssessment.mockRejectedValueOnce(new Error("network down"));
    render(<RespiratoryPanel patientId={TEST_PATIENT_ID} />);
    await waitFor(() => expect(screen.getByRole("button", { name: "Retry" })).toBeTruthy());

    mocks.getRespiratoryAssessment.mockResolvedValueOnce(baseAssessment());
    fireEvent.click(screen.getByRole("button", { name: "Retry" }));
    await waitFor(() => expect(screen.getByRole("combobox", { name: "Respiratory Overview" })).toBeTruthy());
    expect(mocks.getRespiratoryAssessment).toHaveBeenCalledTimes(2);
  });
});

describe("RespiratoryPanel — situation-conditional sections", () => {
  beforeEach(() => {
    mocks.getRespiratoryAssessment.mockResolvedValueOnce(baseAssessment());
  });

  it("shows the Limitations section, not current evidence, when Unable to Assess is selected", async () => {
    render(<RespiratoryPanel patientId={TEST_PATIENT_ID} />);
    await waitFor(() => expect(screen.getByTestId("respiratory-panel")).toBeTruthy());

    selectOverview("Unable to Assess");

    expect(screen.getByTestId("respiratory-limitation-section")).toBeTruthy();
    expect(screen.queryByTestId("respiratory-current-evidence-section")).toBeNull();
    expect(screen.getByRole("combobox", { name: "Reason Unable to Assess" })).toBeTruthy();
  });

  it("only shows the free-text 'Other reason' field once 'Other' is chosen as the reason", async () => {
    render(<RespiratoryPanel patientId={TEST_PATIENT_ID} />);
    await waitFor(() => expect(screen.getByTestId("respiratory-panel")).toBeTruthy());

    selectOverview("Unable to Assess");
    expect(screen.queryByRole("textbox", { name: "Other Reason (if selected above)" })).toBeNull();

    const reasonTrigger = screen.getByRole("combobox", { name: "Reason Unable to Assess" });
    fireEvent.click(reasonTrigger);
    fireEvent.click(screen.getByRole("option", { name: "Other" }));

    expect(screen.getByRole("textbox", { name: "Other Reason (if selected above)" })).toBeTruthy();
  });

  it("shows current evidence, interventions, and follow-up sections for a verified situation", async () => {
    render(<RespiratoryPanel patientId={TEST_PATIENT_ID} />);
    await waitFor(() => expect(screen.getByTestId("respiratory-panel")).toBeTruthy());

    selectOverview("New or Worsening Respiratory Findings");

    expect(screen.getByTestId("respiratory-current-evidence-section")).toBeTruthy();
    expect(screen.getByTestId("respiratory-intervention-section")).toBeTruthy();
    expect(screen.getByTestId("respiratory-follow-up-section")).toBeTruthy();
    expect(screen.queryByTestId("respiratory-limitation-section")).toBeNull();
  });
});

describe("RespiratoryPanel — field editing", () => {
  it("records a boolean field toggle (treatment initiated) into the editable draft", async () => {
    mocks.getRespiratoryAssessment.mockResolvedValueOnce(baseAssessment());
    render(<RespiratoryPanel patientId={TEST_PATIENT_ID} />);
    await waitFor(() => expect(screen.getByTestId("respiratory-panel")).toBeTruthy());

    selectOverview("New or Worsening Respiratory Findings");
    const checkbox = within(screen.getByTestId("respiratory-field-respiratory_treatment_initiated")).getByRole(
      "checkbox",
    );
    expect(checkbox.getAttribute("aria-checked")).toBe("false");
    fireEvent.click(checkbox);
    expect(checkbox.getAttribute("aria-checked")).toBe("true");
  });

  it("records a free-text notes entry", async () => {
    mocks.getRespiratoryAssessment.mockResolvedValueOnce(baseAssessment());
    render(<RespiratoryPanel patientId={TEST_PATIENT_ID} />);
    await waitFor(() => expect(screen.getByTestId("respiratory-panel")).toBeTruthy());

    const notes = screen.getByRole("textbox", { name: "Respiratory Notes" }) as HTMLTextAreaElement;
    fireEvent.change(notes, { target: { value: "Patient reports improved breathing today." } });
    expect(notes.value).toBe("Patient reports improved breathing today.");
  });
});

describe("RespiratoryPanel — save lifecycle", () => {
  it("saves an incomplete draft (no situation-required fields filled) successfully", async () => {
    mocks.getRespiratoryAssessment.mockResolvedValueOnce(baseAssessment());
    mocks.saveRespiratoryDraft.mockResolvedValueOnce(
      baseAssessment({ situation: "new_or_worsening", version: 2, reviewState: "reviewed_with_exception" }),
    );
    render(<RespiratoryPanel patientId={TEST_PATIENT_ID} />);
    await waitFor(() => expect(screen.getByTestId("respiratory-panel")).toBeTruthy());

    selectOverview("New or Worsening Respiratory Findings");
    fireEvent.click(screen.getByTestId("respiratory-save-button"));

    await waitFor(() =>
      expect(screen.getByTestId("respiratory-save-status").textContent).toContain("saved"),
    );
    expect(mocks.saveRespiratoryDraft).toHaveBeenCalledWith(
      TEST_PATIENT_ID,
      expect.objectContaining({ situation: "new_or_worsening", expectedVersion: 1 }),
    );
  });

  it("disables the save button until a situation is selected", async () => {
    mocks.getRespiratoryAssessment.mockResolvedValueOnce(baseAssessment());
    render(<RespiratoryPanel patientId={TEST_PATIENT_ID} />);
    await waitFor(() => expect(screen.getByTestId("respiratory-panel")).toBeTruthy());
    const saveButton = screen.getByTestId("respiratory-save-button") as HTMLButtonElement;
    expect(saveButton.disabled).toBe(true);
  });

  it("shows a failed-save message with a retry control, and retry succeeds", async () => {
    mocks.getRespiratoryAssessment.mockResolvedValueOnce(baseAssessment());
    mocks.saveRespiratoryDraft.mockRejectedValueOnce(new Error("network down"));
    render(<RespiratoryPanel patientId={TEST_PATIENT_ID} />);
    await waitFor(() => expect(screen.getByTestId("respiratory-panel")).toBeTruthy());

    selectOverview("No Current Respiratory Concern");
    fireEvent.click(screen.getByTestId("respiratory-save-button"));
    await waitFor(() => expect(screen.getByTestId("respiratory-save-status").textContent).toContain("Save failed"));

    mocks.saveRespiratoryDraft.mockResolvedValueOnce(baseAssessment({ situation: "no_current_concern", version: 2 }));
    fireEvent.click(screen.getByRole("button", { name: "Retry" }));
    await waitFor(() =>
      expect(screen.getByTestId("respiratory-save-status").textContent).toContain("saved"),
    );
  });

  it("shows a stale-version conflict message with a reload control, and reload re-hydrates", async () => {
    mocks.getRespiratoryAssessment.mockResolvedValueOnce(baseAssessment());
    mocks.saveRespiratoryDraft.mockRejectedValueOnce(new RespiratoryStaleVersionError());
    render(<RespiratoryPanel patientId={TEST_PATIENT_ID} />);
    await waitFor(() => expect(screen.getByTestId("respiratory-panel")).toBeTruthy());

    selectOverview("No Current Respiratory Concern");
    fireEvent.click(screen.getByTestId("respiratory-save-button"));
    await waitFor(() => expect(screen.getByTestId("respiratory-save-status").textContent).toContain("Save blocked"));

    mocks.getRespiratoryAssessment.mockResolvedValueOnce(
      baseAssessment({ situation: "new_or_worsening", version: 3 }),
    );
    fireEvent.click(screen.getByRole("button", { name: "Reload latest" }));
    await waitFor(() => expect(mocks.getRespiratoryAssessment).toHaveBeenCalledTimes(2));
  });

  it("surfaces a record-blocking review exception for a missing unable-to-assess reason, computed client-side on save", async () => {
    mocks.getRespiratoryAssessment.mockResolvedValueOnce(baseAssessment());
    mocks.saveRespiratoryDraft.mockResolvedValueOnce(
      baseAssessment({
        situation: "unable_to_assess",
        reviewState: "reviewed_with_exception",
        version: 2,
        data: { respiratoryOverview: "Unable to Assess" },
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
    render(<RespiratoryPanel patientId={TEST_PATIENT_ID} />);
    await waitFor(() => expect(screen.getByTestId("respiratory-panel")).toBeTruthy());

    selectOverview("Unable to Assess");
    fireEvent.click(screen.getByTestId("respiratory-save-button"));

    await waitFor(() => expect(screen.getByTestId("respiratory-review-exceptions")).toBeTruthy());
    const exceptionLink = within(screen.getByTestId("respiratory-review-exceptions")).getByRole("link", {
      name: "Reason unable to assess is required.",
    });
    expect(exceptionLink.getAttribute("href")).toBe("#respiratory_unable_to_assess_reason");
    // The link's target anchor is the owning field's own DOM id, so native
    // anchor navigation lands on the actual control — no separate JS wiring
    // needed for exception-to-field navigation.
    expect(screen.getByRole("combobox", { name: "Reason Unable to Assess" }).id).toBe(
      "respiratory_unable_to_assess_reason",
    );
  });
});

describe("RespiratoryPanel — no scope leakage", () => {
  it("never renders eligibility, certification, order, or AI-action controls", async () => {
    mocks.getRespiratoryAssessment.mockResolvedValueOnce(baseAssessment());
    render(<RespiratoryPanel patientId={TEST_PATIENT_ID} />);
    await waitFor(() => expect(screen.getByTestId("respiratory-panel")).toBeTruthy());
    selectOverview("New or Worsening Respiratory Findings");

    expect(screen.queryByText(/eligib/i)).toBeNull();
    expect(screen.queryByText(/certif/i)).toBeNull();
    expect(screen.queryByRole("button", { name: /order/i })).toBeNull();
    expect(screen.queryByRole("button", { name: /ai action/i })).toBeNull();
    expect(screen.queryByText(/real patient/i)).toBeNull();
  });
});
