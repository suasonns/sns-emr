import { describe, expect, it, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { NeurologicalSystemPanel } from "./NeurologicalSystemPanel";

describe("NeurologicalSystemPanel", () => {
  it("shows the four fixed situations: no current concern, stable existing, new/worsening, unable to assess", () => {
    render(
      <NeurologicalSystemPanel
        onSituationChange={vi.fn()}
        onRequirementSatisfied={vi.fn()}
        onLimitationChange={vi.fn()}
        missingRequirements={[]}
      />,
    );

    screen.getByText("No current concern");
    screen.getByText("Stable existing");
    screen.getByText("New / worsening");
    screen.getByText("Unable to assess");
  });

  it("only shows the unable-to-assess panel (scope/reason/follow-up/clinician/timing) when that situation is selected", () => {
    render(
      <NeurologicalSystemPanel
        situation="unable_to_assess"
        onSituationChange={vi.fn()}
        onRequirementSatisfied={vi.fn()}
        onLimitationChange={vi.fn()}
        missingRequirements={[]}
      />,
    );

    screen.getByPlaceholderText("Reason unable to assess (required)");
    screen.getByPlaceholderText("Assessed portion, if any");
    screen.getByText("Follow-up required");
    screen.getByPlaceholderText("Responsible clinician");
    screen.getByPlaceholderText("Timing / contingency");
  });

  it("disables saving the limitation until a reason is entered", () => {
    render(
      <NeurologicalSystemPanel
        situation="unable_to_assess"
        onSituationChange={vi.fn()}
        onRequirementSatisfied={vi.fn()}
        onLimitationChange={vi.fn()}
        missingRequirements={[]}
      />,
    );

    expect(screen.getByText("Save limitation").hasAttribute("disabled")).toBe(true);
    fireEvent.change(screen.getByPlaceholderText("Reason unable to assess (required)"), {
      target: { value: "Patient sedated" },
    });
    expect(screen.getByText("Save limitation").hasAttribute("disabled")).toBe(false);
  });
});
