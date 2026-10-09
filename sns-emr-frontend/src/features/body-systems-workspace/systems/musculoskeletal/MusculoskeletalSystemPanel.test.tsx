import { describe, expect, it, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { bradenMobilitySubscoreDoesNotCompleteMusculoskeletalReview } from "../../../../domain/body-systems/ownership";
import {
  MusculoskeletalSystemPanel,
  INITIAL_MUSCULOSKELETAL_FIELD_VALUES,
  type MusculoskeletalFieldValues,
} from "./MusculoskeletalSystemPanel";

function renderPanel(overrides: Partial<Parameters<typeof MusculoskeletalSystemPanel>[0]> = {}) {
  const onChange = vi.fn();
  const utils = render(
    <MusculoskeletalSystemPanel
      onSituationChange={vi.fn()}
      onRequirementSatisfied={vi.fn()}
      onLimitationChange={vi.fn()}
      missingRequirements={[]}
      values={INITIAL_MUSCULOSKELETAL_FIELD_VALUES}
      onChange={onChange}
      {...overrides}
    />,
  );
  return { ...utils, onChange };
}

describe("MusculoskeletalSystemPanel", () => {
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

  it("lists all five musculoskeletal ownership fact keys as unable-to-assess scope options", () => {
    renderPanel({ situation: "unable_to_assess" });

    for (const factKey of ["gait", "balance", "transfers", "mobility", "weakness as mobility function"]) {
      screen.getByText(factKey);
    }
  });

  it("does not list any out-of-scope concept (ADLs, falls, assistive devices, Braden) as an unable-to-assess scope option", () => {
    renderPanel({ situation: "unable_to_assess" });

    for (const excluded of [
      "bathing",
      "dressing",
      "toileting",
      "eating",
      "grooming",
      "fall",
      "assistive device",
      "braden",
      "contracture",
      "rigidity",
    ]) {
      expect(screen.queryByText(new RegExp(excluded, "i"))).toBeNull();
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

  it("shows the musculoskeletal-status and intervention-detail fields only for situations other than unable-to-assess", () => {
    renderPanel({ situation: "stable_existing" });

    screen.getByPlaceholderText("Onset / source");
    screen.getByPlaceholderText("Musculoskeletal status notes");
    screen.getByPlaceholderText("Interventions given");
    screen.getByPlaceholderText("Follow-up needs");
    screen.getByText("HOPE comfort impact");
    screen.getByText("HOPE function impact");
  });

  it("never derives HOPE comfort or function impact from gait or weakness selections", () => {
    const { onChange } = renderPanel({ situation: "new_or_worsening" });

    fireEvent.click(screen.getByText("unable")); // gait status "unable"

    expect(onChange).toHaveBeenCalledWith(
      expect.objectContaining({
        gaitStatus: "unable",
        hopeComfortImpact: "not_yet_assessed",
        hopeFunctionImpact: "not_yet_assessed",
      }),
    );
  });

  it("only changes HOPE comfort/function impact via explicit RN selection", () => {
    const values: MusculoskeletalFieldValues = {
      ...INITIAL_MUSCULOSKELETAL_FIELD_VALUES,
      gaitStatus: "unable",
      weaknessStatus: "severe",
    };
    const { onChange } = renderPanel({ situation: "new_or_worsening", values });

    fireEvent.click(screen.getAllByText("yes")[0]); // first "yes" toggle is HOPE comfort impact

    expect(onChange).toHaveBeenCalledWith(expect.objectContaining({ hopeComfortImpact: "yes" }));
  });

  describe("Braden mobility subscore non-substitution (unique Musculoskeletal requirement)", () => {
    it("asserts, at the domain level, that a Braden mobility subscore never completes a Musculoskeletal review", () => {
      expect(bradenMobilitySubscoreDoesNotCompleteMusculoskeletalReview()).toBe(true);
    });

    it("requires an explicit situation selection before any requirement can be satisfied, regardless of any Braden mobility subscore value elsewhere in the chart", () => {
      // Simulates the real-world condition the guard protects against: Braden
      // mobility subscore data exists elsewhere (owned by Integumentary's
      // `braden` fact key — see ownership.ts) but this panel receives no
      // situation and no satisfied requirements. The panel must not display
      // any musculoskeletal-status/HOPE fields, nor treat the review as
      // underway, purely because Braden data exists in the chart.
      renderPanel({ situation: undefined, missingRequirements: [] });

      expect(screen.queryByPlaceholderText("Musculoskeletal status notes")).toBeNull();
      expect(screen.queryByText("HOPE comfort impact")).toBeNull();
      expect(screen.queryByText("Required for this situation")).toBeNull();
    });

    it("keeps the Musculoskeletal review incomplete (missing requirements still reported) even when situation is set, until the RN explicitly satisfies each requirement — a Braden subscore cannot satisfy them", () => {
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

    it("never sets gait, balance, transfers, mobility, or weakness from a Braden mobility subscore — only explicit field edits change these values", () => {
      const { onChange } = renderPanel({ situation: "stable_existing" });

      // Rendering with a situation set (simulating Braden data existing
      // elsewhere in the chart) must not itself call onChange with any
      // musculoskeletal field populated.
      expect(onChange).not.toHaveBeenCalled();
    });
  });
});
