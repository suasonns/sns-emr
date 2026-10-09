import { describe, expect, it, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { AISuggestionShell } from "./AISuggestionShell";
import type { AISuggestion } from "../../../domain/body-systems";

const suggestion: AISuggestion = {
  id: "sugg-1",
  extractionRunId: "run-1",
  ownerSystem: "respiratory",
  targetFieldPath: "lung_sounds",
  proposedValue: "Crackles bilateral bases",
  confidence: "low",
  sourceExcerpt: "Patient reports crackling sound when breathing.",
  disposition: "pending",
};

describe("AISuggestionShell", () => {
  it("renders an explicit empty state when there are no suggestions (Phase 1 default)", () => {
    render(<AISuggestionShell suggestions={[]} />);
    screen.getByText(/No AI suggestions in Phase 1/);
  });

  it("Accept/Edit/Reject only change local disposition — they do not mark any system reviewed", () => {
    const onDispositionChange = vi.fn();
    render(<AISuggestionShell suggestions={[suggestion]} onDispositionChange={onDispositionChange} />);

    fireEvent.click(screen.getByText("Accept"));
    expect(onDispositionChange).toHaveBeenCalledWith("sugg-1", "accepted");

    fireEvent.click(screen.getByText("Reject"));
    expect(onDispositionChange).toHaveBeenCalledWith("sugg-1", "rejected");

    // Only the two-argument disposition callback is ever invoked — no
    // review-state or assessment callback is passed to this component at all.
    expect(onDispositionChange).toHaveBeenCalledTimes(2);
  });
});
