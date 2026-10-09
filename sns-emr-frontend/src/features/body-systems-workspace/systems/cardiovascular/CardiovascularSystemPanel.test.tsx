import { describe, expect, it, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import {
  CardiovascularSystemPanel,
  INITIAL_CARDIOVASCULAR_FIELD_VALUES,
  type CardiovascularFieldValues,
} from "./CardiovascularSystemPanel";

function renderPanel(overrides: Partial<Parameters<typeof CardiovascularSystemPanel>[0]> = {}) {
  const onChange = vi.fn();
  const utils = render(
    <CardiovascularSystemPanel
      onSituationChange={vi.fn()}
      onRequirementSatisfied={vi.fn()}
      onLimitationChange={vi.fn()}
      missingRequirements={[]}
      values={INITIAL_CARDIOVASCULAR_FIELD_VALUES}
      onChange={onChange}
      {...overrides}
    />,
  );
  return { ...utils, onChange };
}

describe("CardiovascularSystemPanel", () => {
  it("shows the four fixed situations: no current concern, stable existing, new/worsening, unable to assess", () => {
    renderPanel();

    screen.getByText("No current concern");
    screen.getByText("Stable existing");
    screen.getByText("New / worsening");
    screen.getByText("Unable to assess");
  });

  it("only shows the unable-to-assess panel (scope/reason/follow-up/clinician/timing) when that situation is selected", () => {
    renderPanel({ situation: "unable_to_assess" });

    screen.getByPlaceholderText("Reason unable to assess (required)");
    screen.getByPlaceholderText("Assessed portion, if any");
    screen.getByText("Follow-up required");
    screen.getByPlaceholderText("Responsible clinician");
    screen.getByPlaceholderText("Timing / contingency");
  });

  it("lists all eight cardiovascular ownership fact keys as unable-to-assess scope options", () => {
    renderPanel({ situation: "unable_to_assess" });

    for (const factKey of [
      "edema",
      "pulse rhythm",
      "heart sounds perfusion",
      "blood pressure orthostatic findings",
      "chest pain",
      "syncope",
      "circulation",
      "cardiac devices",
    ]) {
      screen.getByText(factKey);
    }
  });

  it("disables saving the limitation until a reason is entered", () => {
    renderPanel({ situation: "unable_to_assess" });

    expect(screen.getByText("Save limitation").hasAttribute("disabled")).toBe(true);
    fireEvent.change(screen.getByPlaceholderText("Reason unable to assess (required)"), {
      target: { value: "Patient declined exam" },
    });
    expect(screen.getByText("Save limitation").hasAttribute("disabled")).toBe(false);
  });

  it("shows the symptom-detail fields only for situations other than unable-to-assess", () => {
    renderPanel({ situation: "stable_existing" });

    screen.getByPlaceholderText("Onset / source");
    screen.getByPlaceholderText("Edema location");
    screen.getByPlaceholderText("Chest pain description");
    screen.getByText("HOPE comfort impact");
    screen.getByText("HOPE function impact");
  });

  it("never derives HOPE comfort or function impact from chest pain or edema severity", () => {
    const { onChange } = renderPanel({ situation: "new_or_worsening" });

    fireEvent.click(screen.getAllByText("severe")[0]); // edema severity "severe"

    expect(onChange).toHaveBeenCalledWith(
      expect.objectContaining({
        edemaSeverity: "severe",
        hopeComfortImpact: "not_yet_assessed",
        hopeFunctionImpact: "not_yet_assessed",
      }),
    );

    fireEvent.click(screen.getAllByText("severe")[1]); // chest pain severity "severe"

    expect(onChange).toHaveBeenLastCalledWith(
      expect.objectContaining({
        chestPainSeverity: "severe",
        hopeComfortImpact: "not_yet_assessed",
        hopeFunctionImpact: "not_yet_assessed",
      }),
    );
  });

  it("only changes HOPE comfort/function impact via explicit RN selection", () => {
    const values: CardiovascularFieldValues = {
      ...INITIAL_CARDIOVASCULAR_FIELD_VALUES,
      chestPainSeverity: "severe",
      edemaSeverity: "severe",
    };
    const { onChange } = renderPanel({ situation: "new_or_worsening", values });

    fireEvent.click(screen.getAllByText("yes")[0]); // first "yes" toggle is HOPE comfort impact

    expect(onChange).toHaveBeenCalledWith(expect.objectContaining({ hopeComfortImpact: "yes" }));
  });
});
