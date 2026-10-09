import { describe, expect, it } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { BODY_SYSTEM_LABELS, BODY_SYSTEMS } from "../../../domain/body-systems";
import { BodyShieldShell } from "./BodyShieldShell";

describe("BodyShieldShell", () => {
  it("renders all ten systems, in fixed BODY_SYSTEMS order, always visible", () => {
    render(
      <BodyShieldShell patientId="patient-1" visitId="visit-1" bodySystemsAssessmentId="assessment-1" />,
    );

    const registryLabels = BODY_SYSTEMS.map((system) => BODY_SYSTEM_LABELS[system]);
    for (const label of registryLabels) {
      expect(screen.getAllByText(label).length).toBeGreaterThan(0);
    }
  });

  it("supports switching between Admission, Routine RN, and Recertification visit modes without hiding any system", () => {
    render(
      <BodyShieldShell patientId="patient-1" visitId="visit-1" bodySystemsAssessmentId="assessment-1" />,
    );

    fireEvent.mouseDown(screen.getByRole("tab", { name: "Admission / Comprehensive" }));
    screen.getByText("Establish current baseline.");
    for (const system of BODY_SYSTEMS) {
      expect(screen.getAllByText(BODY_SYSTEM_LABELS[system]).length).toBeGreaterThan(0);
    }

    fireEvent.mouseDown(screen.getByRole("tab", { name: "Recertification" }));
    screen.getByText("Compare dated current evidence with dated prior-period evidence.");
  });

  it("selecting Neurological shows the pilot panel; selecting Cardiovascular, Nutrition, Gastrointestinal, Genitourinary, Musculoskeletal, and Integumentary show their pilot panels; selecting a non-pilot system shows the Phase 2 placeholder", () => {
    render(
      <BodyShieldShell patientId="patient-1" visitId="visit-1" bodySystemsAssessmentId="assessment-1" />,
    );

    fireEvent.click(screen.getAllByText("Neurological")[0]);
    screen.getByText("Situation");

    fireEvent.click(screen.getAllByText("Cardiovascular")[0]);
    fireEvent.click(screen.getByText("Stable existing"));
    screen.getByText("Edema severity");

    fireEvent.click(screen.getAllByText("Nutrition")[0]);
    fireEvent.click(screen.getByText("Stable existing"));
    screen.getByText("Swallowing / nutritional burden");

    fireEvent.click(screen.getAllByText("Gastrointestinal")[0]);
    fireEvent.click(screen.getByText("Stable existing"));
    screen.getByText("Bowel pattern");

    fireEvent.click(screen.getAllByText("Genitourinary")[0]);
    fireEvent.click(screen.getByText("Stable existing"));
    screen.getByText("Catheter status");

    fireEvent.click(screen.getAllByText("Musculoskeletal")[0]);
    fireEvent.click(screen.getByText("Stable existing"));
    screen.getByText("Weakness (mobility/function impact)");

    fireEvent.click(screen.getAllByText("Integumentary")[0]);
    fireEvent.click(screen.getByText("Stable existing"));
    screen.getByText("Skin impairments present");

    fireEvent.click(screen.getAllByText("Infection / Immunological")[0]);
    screen.getByText(/Phase 2 scope/);
  });
});
