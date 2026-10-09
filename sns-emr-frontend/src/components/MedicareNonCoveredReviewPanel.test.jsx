import React from "react";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { axe } from "jest-axe";

import MedicareNonCoveredReviewPanel from "./MedicareNonCoveredReviewPanel";

const mocks = vi.hoisted(() => ({
  getMedicareNonCoveredReview: vi.fn(),
  updateMedicareNonCoveredReview: vi.fn(),
  getElectionAddendumCandidates: vi.fn(),
}));

vi.mock("../api/icaAssessments", () => ({
  getMedicareNonCoveredReview: mocks.getMedicareNonCoveredReview,
  updateMedicareNonCoveredReview: mocks.updateMedicareNonCoveredReview,
  getElectionAddendumCandidates: mocks.getElectionAddendumCandidates,
}));

describe("MedicareNonCoveredReviewPanel", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mocks.getMedicareNonCoveredReview.mockResolvedValue({ medicareNonCoveredReview: null });
    mocks.getElectionAddendumCandidates.mockResolvedValue({ candidates: [] });
  });

  it("prompts to save the assessment first when no assessmentId exists yet", async () => {
    render(<MedicareNonCoveredReviewPanel assessmentId={null} locked={false} COLORS={{}} />);
    expect(screen.getByText(/Save the assessment once before/i)).toBeTruthy();
  });

  it("loads the existing review and lets the user pick a determination", async () => {
    render(<MedicareNonCoveredReviewPanel assessmentId="assessment-1" locked={false} COLORS={{}} />);
    await waitFor(() => expect(mocks.getMedicareNonCoveredReview).toHaveBeenCalledWith("assessment-1"));
    expect(await screen.findByLabelText("Determination")).toBeTruthy();
  });

  it("requires an explanation before saving when outcome is CHANGED", async () => {
    render(<MedicareNonCoveredReviewPanel assessmentId="assessment-1" locked={false} COLORS={{}} />);
    const select = await screen.findByLabelText("Determination");
    fireEvent.change(select, { target: { value: "CHANGED" } });
    expect(await screen.findByLabelText(/Explanation/)).toBeTruthy();
  });

  it("saves the review and reports success", async () => {
    mocks.updateMedicareNonCoveredReview.mockResolvedValue({
      medicareNonCoveredReview: { outcome: "NO_ITEMS_IDENTIFIED" },
    });
    render(<MedicareNonCoveredReviewPanel assessmentId="assessment-1" locked={false} COLORS={{}} />);
    const select = await screen.findByLabelText("Determination");
    fireEvent.change(select, { target: { value: "NO_ITEMS_IDENTIFIED" } });
    fireEvent.click(screen.getByRole("button", { name: /Save Medicare Review/i }));
    await waitFor(() =>
      expect(mocks.updateMedicareNonCoveredReview).toHaveBeenCalledWith(
        "assessment-1",
        expect.objectContaining({ outcome: "NO_ITEMS_IDENTIFIED" })
      )
    );
    expect(await screen.findByText("Saved.")).toBeTruthy();
  });

  it("renders a read-only summary once the assessment is locked", async () => {
    mocks.getMedicareNonCoveredReview.mockResolvedValue({
      medicareNonCoveredReview: { outcome: "NO_ITEMS_IDENTIFIED", reviewedAt: "2026-01-01T00:00:00Z" },
    });
    render(<MedicareNonCoveredReviewPanel assessmentId="assessment-1" locked COLORS={{}} />);
    expect(await screen.findByText(/Determination:/)).toBeTruthy();
    expect(screen.queryByLabelText("Determination")).toBeNull();
  });

  it("has no detectable accessibility violations (unsaved/no assessmentId)", async () => {
    const { container } = render(<MedicareNonCoveredReviewPanel assessmentId={null} locked={false} COLORS={{}} />);
    expect(await axe(container)).toHaveNoViolations();
  });

  it("has no detectable accessibility violations (editable form)", async () => {
    const { container } = render(<MedicareNonCoveredReviewPanel assessmentId="assessment-1" locked={false} COLORS={{}} />);
    await screen.findByLabelText("Determination");
    expect(await axe(container)).toHaveNoViolations();
  });

  it("has no detectable accessibility violations (locked summary)", async () => {
    mocks.getMedicareNonCoveredReview.mockResolvedValue({
      medicareNonCoveredReview: { outcome: "NO_ITEMS_IDENTIFIED", reviewedAt: "2026-01-01T00:00:00Z" },
    });
    const { container } = render(<MedicareNonCoveredReviewPanel assessmentId="assessment-1" locked COLORS={{}} />);
    await screen.findByText(/Determination:/);
    expect(await axe(container)).toHaveNoViolations();
  });
});
