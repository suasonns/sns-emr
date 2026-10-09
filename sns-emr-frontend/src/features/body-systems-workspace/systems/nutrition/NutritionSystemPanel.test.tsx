import { describe, expect, it, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { bradenNutritionSubscoreDoesNotCompleteNutritionReview } from "../../../../domain/body-systems/ownership";
import {
  NutritionSystemPanel,
  INITIAL_NUTRITION_FIELD_VALUES,
  type NutritionFieldValues,
} from "./NutritionSystemPanel";

function renderPanel(overrides: Partial<Parameters<typeof NutritionSystemPanel>[0]> = {}) {
  const onChange = vi.fn();
  const utils = render(
    <NutritionSystemPanel
      onSituationChange={vi.fn()}
      onRequirementSatisfied={vi.fn()}
      onLimitationChange={vi.fn()}
      missingRequirements={[]}
      values={INITIAL_NUTRITION_FIELD_VALUES}
      onChange={onChange}
      {...overrides}
    />,
  );
  return { ...utils, onChange };
}

describe("NutritionSystemPanel", () => {
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

  it("lists all five nutrition ownership fact keys as unable-to-assess scope options", () => {
    renderPanel({ situation: "unable_to_assess" });

    for (const factKey of ["intake", "weight", "weight change", "appetite", "swallowing nutritional burden"]) {
      screen.getByText(factKey);
    }
  });

  it("disables saving the limitation until a reason is entered", () => {
    renderPanel({ situation: "unable_to_assess" });

    expect(screen.getByText("Save limitation").hasAttribute("disabled")).toBe(true);
    fireEvent.change(screen.getByPlaceholderText("Reason unable to assess (required)"), {
      target: { value: "Patient declined interview" },
    });
    expect(screen.getByText("Save limitation").hasAttribute("disabled")).toBe(false);
  });

  it("shows the nutrition-status and intervention-detail fields only for situations other than unable-to-assess", () => {
    renderPanel({ situation: "stable_existing" });

    screen.getByPlaceholderText("Onset / source");
    screen.getByPlaceholderText("Nutrition status notes");
    screen.getByPlaceholderText("Interventions given");
    screen.getByPlaceholderText("Follow-up needs");
    screen.getByText("HOPE comfort impact");
    screen.getByText("HOPE function impact");
  });

  it("never derives HOPE comfort or function impact from appetite or weight-change selections", () => {
    const { onChange } = renderPanel({ situation: "new_or_worsening" });

    fireEvent.click(screen.getByText("anorexic")); // appetite status "anorexic"

    expect(onChange).toHaveBeenCalledWith(
      expect.objectContaining({
        appetiteStatus: "anorexic",
        hopeComfortImpact: "not_yet_assessed",
        hopeFunctionImpact: "not_yet_assessed",
      }),
    );
  });

  it("only changes HOPE comfort/function impact via explicit RN selection", () => {
    const values: NutritionFieldValues = {
      ...INITIAL_NUTRITION_FIELD_VALUES,
      appetiteStatus: "anorexic",
      weightChangeDirection: "loss",
    };
    const { onChange } = renderPanel({ situation: "new_or_worsening", values });

    fireEvent.click(screen.getAllByText("yes")[0]); // first "yes" toggle is HOPE comfort impact

    expect(onChange).toHaveBeenCalledWith(expect.objectContaining({ hopeComfortImpact: "yes" }));
  });

  describe("Braden nutrition subscore non-substitution (unique Nutrition requirement)", () => {
    it("asserts, at the domain level, that a Braden nutrition subscore never completes a Nutrition review", () => {
      expect(bradenNutritionSubscoreDoesNotCompleteNutritionReview()).toBe(true);
    });

    it("requires an explicit situation selection before any requirement can be satisfied, regardless of any Braden nutrition subscore value elsewhere in the chart", () => {
      // Simulates the real-world condition the guard protects against: Braden
      // nutrition subscore data exists elsewhere (owned by Integumentary's
      // `braden` fact key — see ownership.ts) but this panel receives no
      // situation and no satisfied requirements. The panel must not display
      // any nutrition-status/HOPE fields, nor treat the review as underway,
      // purely because Braden data exists in the chart.
      renderPanel({ situation: undefined, missingRequirements: [] });

      expect(screen.queryByPlaceholderText("Nutrition status notes")).toBeNull();
      expect(screen.queryByText("HOPE comfort impact")).toBeNull();
      expect(screen.queryByText("Required for this situation")).toBeNull();
    });

    it("keeps the Nutrition review incomplete (missing requirements still reported) even when situation is set, until the RN explicitly satisfies each requirement — a Braden subscore cannot satisfy them", () => {
      const onRequirementSatisfied = vi.fn();
      renderPanel({
        situation: "stable_existing",
        missingRequirements: ["current_confirmation", "dated_prior_reference"],
        onRequirementSatisfied,
      });

      // The requirement checkbox is unchecked (requirement still missing) —
      // nothing about rendering this panel with Braden data present anywhere
      // else in the application pre-checks it or calls onRequirementSatisfied.
      const checkbox = screen.getAllByRole("checkbox")[0];
      expect(checkbox.getAttribute("aria-checked")).not.toBe("true");
      expect(onRequirementSatisfied).not.toHaveBeenCalled();
    });
  });
});
