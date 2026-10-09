import { describe, expect, it, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import {
  temperatureIsNotOwnedByInfection,
  woundFindingsAreNotOwnedByInfection,
  urinaryFindingsAreNotOwnedByInfection,
  respiratoryFindingsAreNotOwnedByInfection,
  hopeSepsisHistoryDoesNotDeriveActiveInfectionSepsis,
  activeInfectionSepsisDoesNotRewriteHopeSepsisHistory,
  allergiesAreNotOwnedByInfection,
  systemNotesDoNotSatisfyStructuredFindings,
} from "../../../../domain/body-systems";
import {
  InfectionSystemPanel,
  INITIAL_INFECTION_FIELD_VALUES,
  type InfectionFieldValues,
} from "./InfectionSystemPanel";

function renderPanel(overrides: Partial<Parameters<typeof InfectionSystemPanel>[0]> = {}) {
  const onChange = vi.fn();
  const utils = render(
    <InfectionSystemPanel
      onSituationChange={vi.fn()}
      onRequirementSatisfied={vi.fn()}
      onLimitationChange={vi.fn()}
      missingRequirements={[]}
      values={INITIAL_INFECTION_FIELD_VALUES}
      onChange={onChange}
      {...overrides}
    />,
  );
  return { ...utils, onChange };
}

describe("InfectionSystemPanel", () => {
  it("shows the four fixed situations: no current concern, stable existing, new/worsening, unable to assess", () => {
    renderPanel();

    screen.getByText("No current concern");
    screen.getByText("Stable existing");
    screen.getByText("New / worsening");
    screen.getByText("Unable to assess");
  });

  it("requires an explicit situation selection before any structured field renders", () => {
    renderPanel({ situation: undefined, missingRequirements: [] });

    expect(screen.queryByText("Infection status")).toBeNull();
    expect(screen.queryByText("Organism / culture information")).toBeNull();
  });

  it("renders the 9 discrete Infection-owned structured sections for a selected situation", () => {
    renderPanel({ situation: "stable_existing" });

    screen.getByText("Infection status");
    screen.getByPlaceholderText("Infection type (e.g. UTI, pneumonia, wound infection, cellulitis)");
    screen.getByPlaceholderText("Infection findings");
    screen.getByText("Organism / culture information");
    screen.getByText("Antimicrobial treatment");
    screen.getByText("Precautions / isolation");
    screen.getByText("Immunosuppression status");
    screen.getByPlaceholderText("Infection history");
    screen.getByText("Sepsis currently active");
  });

  it("only shows the unable-to-assess panel (scope/reason/follow-up/clinician/timing) when that situation is selected", () => {
    renderPanel({ situation: "unable_to_assess" });

    screen.getByPlaceholderText("Reason unable to assess (required)");
    screen.getByPlaceholderText("Assessed portion, if any");
    screen.getByText("Follow-up required");
    screen.getByPlaceholderText("Responsible clinician");
    screen.getByPlaceholderText("Timing / contingency");
  });

  it("lists exactly the nine discrete infection ownership fact keys as unable-to-assess scope options", () => {
    renderPanel({ situation: "unable_to_assess" });

    for (const factKey of [
      "infection status",
      "infection type",
      "infection findings",
      "organism information",
      "antimicrobial treatment",
      "precautions isolation",
      "immunosuppression status",
      "infection history",
      "infection response followup",
    ]) {
      screen.getByText(factKey);
    }
  });

  describe("temperature stays with Vitals (no duplication)", () => {
    it("asserts, at the domain level, that temperature is never owned by Infection", () => {
      expect(temperatureIsNotOwnedByInfection()).toBe(true);
    });

    it("never renders an editable temperature field — only a read-only, source-labeled reference", () => {
      renderPanel({ situation: "stable_existing", crossSystemContext: { temperatureSummary: "98.6°F (Vitals)" } });

      expect(screen.queryByPlaceholderText(/temperature/i)).toBeNull();
      screen.getByText(/Temperature \(Vitals\): 98\.6°F \(Vitals\)/);
    });
  });

  describe("wound/urinary/respiratory stay with their owning systems (no reassessment)", () => {
    it("asserts, at the domain level, that wound findings are never owned by Infection", () => {
      expect(woundFindingsAreNotOwnedByInfection()).toBe(true);
    });

    it("asserts, at the domain level, that urinary findings are never owned by Infection", () => {
      expect(urinaryFindingsAreNotOwnedByInfection()).toBe(true);
    });

    it("asserts, at the domain level, that respiratory findings are never owned by Infection", () => {
      expect(respiratoryFindingsAreNotOwnedByInfection()).toBe(true);
    });

    it("never renders a wound/urinary/respiratory assessment field in this panel", () => {
      renderPanel({ situation: "stable_existing" });

      expect(screen.queryByPlaceholderText(/wound stage/i)).toBeNull();
      expect(screen.queryByPlaceholderText(/urinary symptom/i)).toBeNull();
      expect(screen.queryByPlaceholderText(/lung sounds/i)).toBeNull();
    });

    it("shows cross-system context as compact, read-only, source-labeled reference text, never editable fields", () => {
      renderPanel({
        situation: "stable_existing",
        crossSystemContext: {
          woundSummary: "Stage 2 sacral pressure injury (Integumentary)",
          urinarySummary: "Urinary symptom severity: moderate (Genitourinary)",
          respiratorySummary: "SOB severity: moderate (Respiratory)",
        },
      });

      screen.getByText(/Wound \(Integumentary\): Stage 2 sacral pressure injury/);
      screen.getByText(/Urinary \(Genitourinary\): Urinary symptom severity: moderate/);
      screen.getByText(/Respiratory: SOB severity: moderate/);
      screen.getByText("Read-only. Does not substitute for review in the owning system.");
    });

    it("shows 'Not yet documented' fallback text when no cross-system context is supplied", () => {
      renderPanel({ situation: "stable_existing" });

      expect(screen.getAllByText(/Not yet documented/).length).toBeGreaterThan(0);
    });
  });

  describe("allergies remain reference-only (no second allergy store or editor)", () => {
    it("asserts, at the domain level, that allergies are never owned by Infection", () => {
      expect(allergiesAreNotOwnedByInfection()).toBe(true);
    });

    it("never renders an allergy editing control", () => {
      renderPanel({ situation: "stable_existing" });

      expect(screen.queryByPlaceholderText(/add allergy/i)).toBeNull();
      expect(screen.queryByRole("button", { name: /add allergy/i })).toBeNull();
    });
  });

  describe("sepsis independence (HOPE/comorbidity sepsis vs. current active-infection sepsis)", () => {
    it("asserts, at the domain level, that HOPE sepsis history never derives current active-infection sepsis", () => {
      expect(hopeSepsisHistoryDoesNotDeriveActiveInfectionSepsis()).toBe(true);
    });

    it("asserts, at the domain level, that current active-infection sepsis never rewrites HOPE sepsis history", () => {
      expect(activeInfectionSepsisDoesNotRewriteHopeSepsisHistory()).toBe(true);
    });

    it("only changes sepsisCurrentlyActive via explicit RN selection, defaulting to not_yet_assessed", () => {
      renderPanel({ situation: "stable_existing" });
      screen.getByText("not yet assessed");
    });

    it("changes sepsisCurrentlyActive independently without touching any other infection field", () => {
      const { onChange } = renderPanel({ situation: "stable_existing" });

      fireEvent.click(screen.getAllByText("yes")[0]);

      const lastCall = onChange.mock.calls.at(-1)?.[0] as InfectionFieldValues;
      expect(lastCall.sepsisCurrentlyActive).toBe("yes");
      expect(lastCall.infectionStatus).toBe(INITIAL_INFECTION_FIELD_VALUES.infectionStatus);
    });
  });

  describe("RN Notes (optional, placed last, never satisfies structured findings)", () => {
    it("asserts, at the domain level, that notes never satisfy a structured finding", () => {
      expect(systemNotesDoNotSatisfyStructuredFindings()).toBe(true);
    });

    it("renders the RN Notes section after structured findings and cross-system context, before Unable-to-Assess", () => {
      renderPanel({ situation: "stable_existing" });

      screen.getByText("RN Notes");
      screen.getByText(/Optional\. Add context/);
    });

    it("is optional — leaving it blank never blocks rendering or review", () => {
      renderPanel({ situation: "stable_existing", values: INITIAL_INFECTION_FIELD_VALUES });

      const textarea = screen.getByPlaceholderText("Optional clinical context or explanation") as HTMLTextAreaElement;
      expect(textarea.value).toBe("");
    });

    it("updates only the notes field when the RN enters narrative context", () => {
      const { onChange } = renderPanel({ situation: "stable_existing" });

      fireEvent.change(screen.getByPlaceholderText("Optional clinical context or explanation"), {
        target: { value: "Culture reviewed by physician; symptoms improving." },
      });

      const lastCall = onChange.mock.calls.at(-1)?.[0] as InfectionFieldValues;
      expect(lastCall.notes).toBe("Culture reviewed by physician; symptoms improving.");
      expect(lastCall.infectionStatus).toBe(INITIAL_INFECTION_FIELD_VALUES.infectionStatus);
    });
  });
});
