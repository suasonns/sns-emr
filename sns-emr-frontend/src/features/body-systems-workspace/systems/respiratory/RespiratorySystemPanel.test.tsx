import { describe, expect, it, vi } from "vitest";
import { useState } from "react";
import { render, screen, fireEvent } from "@testing-library/react";
import {
  RespiratorySystemPanel,
  INITIAL_RESPIRATORY_FIELD_VALUES,
  type RespiratoryFieldValues,
} from "./RespiratorySystemPanel";

function renderPanel(overrides: Partial<Parameters<typeof RespiratorySystemPanel>[0]> = {}) {
  const onChange = vi.fn();
  const utils = render(
    <RespiratorySystemPanel
      onSituationChange={vi.fn()}
      onRequirementSatisfied={vi.fn()}
      onLimitationChange={vi.fn()}
      missingRequirements={[]}
      values={INITIAL_RESPIRATORY_FIELD_VALUES}
      onChange={onChange}
      {...overrides}
    />,
  );
  return { ...utils, onChange };
}

/** Stateful harness for tests that need the panel's own re-render-on-change loop (e.g. conditional fields). */
function StatefulHarness() {
  const [values, setValues] = useState<RespiratoryFieldValues>(INITIAL_RESPIRATORY_FIELD_VALUES);
  return (
    <RespiratorySystemPanel
      situation="stable_existing"
      onSituationChange={() => {}}
      onRequirementSatisfied={() => {}}
      onLimitationChange={() => {}}
      missingRequirements={[]}
      values={values}
      onChange={setValues}
    />
  );
}

describe("RespiratorySystemPanel", () => {
  it("shows the four fixed situations: no current concern, stable existing, new/worsening, unable to assess", () => {
    renderPanel();

    screen.getByText("No current concern");
    screen.getByText("Stable existing");
    screen.getByText("New / worsening");
    screen.getByText("Unable to assess");
  });

  it("does not show symptom-detail fields until a situation other than unable-to-assess is selected", () => {
    renderPanel();
    expect(screen.queryByText("HOPE comfort impact")).toBeNull();

    renderPanel({ situation: "stable_existing" });
    screen.getByText("HOPE comfort impact");
    screen.getByText("HOPE function impact");
  });

  it("renders both HOPE impact fields defaulted to not yet assessed", () => {
    renderPanel({ situation: "stable_existing" });
    expect(screen.getAllByText("not yet assessed").length).toBeGreaterThanOrEqual(2);
  });

  it("CRITICAL: selecting a SOB severity never changes either HOPE impact field — RN assessment is explicit only", () => {
    const values: RespiratoryFieldValues = { ...INITIAL_RESPIRATORY_FIELD_VALUES };
    const { onChange } = renderPanel({ situation: "stable_existing", values });

    fireEvent.click(screen.getByText("severe"));

    expect(onChange).toHaveBeenCalledWith(
      expect.objectContaining({
        sobSeverity: "severe",
        hopeComfortImpact: "not_yet_assessed",
        hopeFunctionImpact: "not_yet_assessed",
      }),
    );
  });

  it("only changes HOPE comfort/function impact via explicit RN selection", () => {
    const { onChange } = renderPanel({ situation: "new_or_worsening" });

    fireEvent.click(screen.getAllByText("yes")[0]);

    expect(onChange).toHaveBeenCalledWith(expect.objectContaining({ hopeComfortImpact: "yes" }));
  });

  it("only shows flow rate field for nasal cannula / mask oxygen delivery, and ventilator info only for ventilator", () => {
    render(<StatefulHarness />);
    expect(screen.queryByText("Flow rate (L/min)")).toBeNull();
    expect(screen.queryByText("Ventilator information")).toBeNull();

    fireEvent.click(screen.getByText("nasal cannula"));
    screen.getByText("Flow rate (L/min)");

    fireEvent.click(screen.getByText("ventilator"));
    screen.getByPlaceholderText("Ventilator information");
  });

  it("only shows the unable-to-assess panel (scope/reason/follow-up/clinician/timing) when that situation is selected", () => {
    renderPanel({ situation: "unable_to_assess" });

    screen.getByPlaceholderText("Reason unable to assess (required)");
    screen.getByPlaceholderText("Assessed portion, if any");
    screen.getByText("Follow-up required");
    screen.getByPlaceholderText("Responsible clinician");
    screen.getByPlaceholderText("Timing / contingency");
  });

  it("lists all eight respiratory ownership fact keys as unable-to-assess scope options", () => {
    renderPanel({ situation: "unable_to_assess" });

    for (const factKey of [
      "dyspnea",
      "cough",
      "sputum",
      "lung sounds",
      "respiratory rate pattern",
      "oxygen use",
      "ventilator airway support",
      "respiratory exertion tolerance",
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
});
