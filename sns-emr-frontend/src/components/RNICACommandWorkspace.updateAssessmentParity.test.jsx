import React from "react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import {
  isPlanOfCareReviewGated,
  resolveChangeOfConditionSourceLabel,
  UpdateAssessmentContextBanner,
  PlanOfCareReviewPanel,
} from "./RNICA.jsx";
import { viewRnicaAllPoc } from "../api/icaAssessments";

// R3 Command Workspace parity repair (Owner Directive): proves the shared
// Update Assessment context banner and Plan of Care review gate are a
// SINGLE implementation consumed identically by RNICA.jsx's classic view
// and the prop RNICA.jsx builds for RNICACommandWorkspace -- not two
// independently maintained renderings. Because both views literally call
// these same exported functions/components, structural parity is
// guaranteed by construction; this suite locks in their observable
// behavior and the shared gating predicate/resolver they're built on.

vi.mock("../api/icaAssessments", () => ({
  viewRnicaAllPoc: vi.fn(() => Promise.resolve({ problems: [] })),
}));

const styles = { warningBox: {}, card: {} };
const COLORS = { bg: "#0F172A", border: "#1F2937", dark: "#E2E8F0" };

describe("isPlanOfCareReviewGated (shared POC save-first gate predicate)", () => {
  it("gates when there is no assessmentId", () => {
    expect(isPlanOfCareReviewGated(null)).toBe(true);
    expect(isPlanOfCareReviewGated(undefined)).toBe(true);
    expect(isPlanOfCareReviewGated("")).toBe(true);
  });

  it("does not gate once an assessmentId exists", () => {
    expect(isPlanOfCareReviewGated("c592f90d-7e04-4bb6-b84f-20280178d1cd")).toBe(false);
  });
});

describe("resolveChangeOfConditionSourceLabel (shared source-context label resolver)", () => {
  it("returns null when there is no context", () => {
    expect(resolveChangeOfConditionSourceLabel(null)).toBeNull();
  });

  it("labels the history-panel entry point", () => {
    expect(resolveChangeOfConditionSourceLabel({ source: "DIRECT_HISTORY_ACTION" })).toBe("Direct History Action");
  });

  it("labels a Visit Notes routine-visit origin", () => {
    expect(
      resolveChangeOfConditionSourceLabel({ source: "VISIT_NOTE_CHANGE_OF_CONDITION", sourceVisitType: "ROUTINE_VISIT" }),
    ).toBe("Routine RN Visit");
  });

  it("falls back to a generic RN Visit label for other full-body visit-note form types (no PRN form type exists in this repo)", () => {
    expect(
      resolveChangeOfConditionSourceLabel({ source: "VISIT_NOTE_CHANGE_OF_CONDITION", sourceVisitType: "ASSESS" }),
    ).toBe("RN Visit");
  });
});

describe("UpdateAssessmentContextBanner (shared component, both views)", () => {
  it("renders nothing when there is no changeOfConditionContext", () => {
    const { container } = render(<UpdateAssessmentContextBanner changeOfConditionContext={null} styles={styles} COLORS={COLORS} />);
    expect(container.firstChild).toBeNull();
  });

  it("renders the reason, source, and originating visit date", () => {
    render(
      <UpdateAssessmentContextBanner
        changeOfConditionContext={{
          source: "DIRECT_HISTORY_ACTION",
          reasonCode: "WORSENING_SYMPTOM_OR_FINDING",
          reasonLabel: "Worsening symptom or finding",
          reasonDetail: null,
          originatingVisitDate: "2026-11-01",
        }}
        styles={styles}
        COLORS={COLORS}
      />,
    );
    expect(screen.getByText(/Update Assessment — Change of Condition/)).toBeTruthy();
    expect(screen.getByText(/Worsening symptom or finding/)).toBeTruthy();
    expect(screen.getByText(/Source: Direct History Action/)).toBeTruthy();
    expect(screen.getByText(/2026-11-01/)).toBeTruthy();
  });
});

describe("PlanOfCareReviewPanel (shared component, both views)", () => {
  beforeEach(() => {
    viewRnicaAllPoc.mockClear();
  });

  it("shows the save-first gating message when there is no assessmentId yet", () => {
    render(<PlanOfCareReviewPanel assessmentId={null} styles={styles} COLORS={COLORS} />);
    expect(screen.getByText(/Save the Update Assessment before adding or revising/)).toBeTruthy();
    expect(viewRnicaAllPoc).not.toHaveBeenCalled();
  });

  it("delegates to the single existing MasterPocReviewCard (no duplicate POC fetch) once an assessmentId exists", async () => {
    render(<PlanOfCareReviewPanel assessmentId="c592f90d-7e04-4bb6-b84f-20280178d1cd" styles={styles} COLORS={COLORS} />);
    await waitFor(() => expect(viewRnicaAllPoc).toHaveBeenCalledTimes(1));
    expect(viewRnicaAllPoc).toHaveBeenCalledWith("c592f90d-7e04-4bb6-b84f-20280178d1cd");
  });
});
