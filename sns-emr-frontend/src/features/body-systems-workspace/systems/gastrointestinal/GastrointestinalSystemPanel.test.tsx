import { describe, expect, it, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import {
  GastrointestinalSystemPanel,
  INITIAL_GASTROINTESTINAL_FIELD_VALUES,
  type GastrointestinalFieldValues,
} from "./GastrointestinalSystemPanel";

function renderPanel(overrides: Partial<Parameters<typeof GastrointestinalSystemPanel>[0]> = {}) {
  const onChange = vi.fn();
  const utils = render(
    <GastrointestinalSystemPanel
      onSituationChange={vi.fn()}
      onRequirementSatisfied={vi.fn()}
      onLimitationChange={vi.fn()}
      missingRequirements={[]}
      values={INITIAL_GASTROINTESTINAL_FIELD_VALUES}
      onChange={onChange}
      {...overrides}
    />,
  );
  return { ...utils, onChange };
}

describe("GastrointestinalSystemPanel", () => {
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

  it("lists both gastrointestinal ownership fact keys as unable-to-assess scope options", () => {
    renderPanel({ situation: "unable_to_assess" });

    for (const factKey of ["bowel status", "gastrointestinal symptoms"]) {
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

  it("shows the bowel-status and symptom-detail fields only for situations other than unable-to-assess", () => {
    renderPanel({ situation: "stable_existing" });

    screen.getByPlaceholderText("Onset / source");
    screen.getByPlaceholderText("Bowel regimen response");
    screen.getByPlaceholderText("Gastrointestinal symptom description");
    screen.getByPlaceholderText("Interventions given");
    screen.getByPlaceholderText("Follow-up needs");
    screen.getByText("HOPE comfort impact");
    screen.getByText("HOPE function impact");
  });

  it("never derives HOPE comfort or function impact from bowel or symptom severity selections", () => {
    const { onChange } = renderPanel({ situation: "new_or_worsening" });

    fireEvent.click(screen.getAllByText("severe")[0]); // nausea/vomiting severity "severe"

    expect(onChange).toHaveBeenCalledWith(
      expect.objectContaining({
        nauseaVomitingSeverity: "severe",
        hopeComfortImpact: "not_yet_assessed",
        hopeFunctionImpact: "not_yet_assessed",
      }),
    );

    fireEvent.click(screen.getAllByText("severe")[1]); // abdominal pain/distension severity "severe"

    expect(onChange).toHaveBeenLastCalledWith(
      expect.objectContaining({
        abdominalPainDistensionSeverity: "severe",
        hopeComfortImpact: "not_yet_assessed",
        hopeFunctionImpact: "not_yet_assessed",
      }),
    );
  });

  it("only changes HOPE comfort/function impact via explicit RN selection", () => {
    const values: GastrointestinalFieldValues = {
      ...INITIAL_GASTROINTESTINAL_FIELD_VALUES,
      nauseaVomitingSeverity: "severe",
      abdominalPainDistensionSeverity: "severe",
    };
    const { onChange } = renderPanel({ situation: "new_or_worsening", values });

    fireEvent.click(screen.getAllByText("yes")[0]); // first "yes" toggle is HOPE comfort impact

    expect(onChange).toHaveBeenCalledWith(expect.objectContaining({ hopeComfortImpact: "yes" }));
  });
});
