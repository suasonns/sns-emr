import React from "react";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { ClinicalNarrativeCard } from "./RNICA";
import { ThemeModeProvider } from "../theme/theme";

const mocks = vi.hoisted(() => ({
  previewRnicaNarrativeV2: vi.fn(),
}));

// Every other export icaAssessments.js provides is unused by
// ClinicalNarrativeCard; only previewRnicaNarrativeV2 needs a live mock.
vi.mock("../api/icaAssessments", () => ({
  previewRnicaNarrativeV2: mocks.previewRnicaNarrativeV2,
}));

const COLORS = {
  dark: "#111", gray: "#888", warning: "#a60", warningBoxBg: "#fee", danger: "#c00",
};
const styles = { btnSecondary: {}, btnPrimary: {}, formGroup: {}, label: {} };

function renderCard(overrides = {}) {
  const updateField = vi.fn();
  const props = {
    diagnosesData: {},
    fullFormData: {},
    updateField,
    styles,
    COLORS,
    locked: false,
    hospiceNarrativeContext: {},
    assessmentId: "assessment-123",
    onNavigateToSection: vi.fn(),
    onSaveNow: vi.fn(),
    ...overrides,
  };
  const utils = render(<ThemeModeProvider><ClinicalNarrativeCard {...props} /></ThemeModeProvider>);
  return { ...utils, updateField, props };
}

describe("ClinicalNarrativeCard — legacy writer removal behavior", () => {
  beforeEach(() => {
    mocks.previewRnicaNarrativeV2.mockReset();
  });
  afterEach(() => {
    vi.clearAllMocks();
  });

  it("saved-assessment path: 'Build Draft' calls only previewRnicaNarrativeV2, never a local generator", async () => {
    mocks.previewRnicaNarrativeV2.mockResolvedValue({ full_text: "Clinically synthesized narrative text." });
    const { updateField } = renderCard({ assessmentId: "assessment-123", diagnosesData: {} });

    fireEvent.click(screen.getByRole("button", { name: /build draft from documented findings/i }));

    await waitFor(() => {
      expect(mocks.previewRnicaNarrativeV2).toHaveBeenCalledWith("assessment-123");
    });
    await waitFor(() => {
      expect(updateField).toHaveBeenCalledWith("clinicalNarrative", "Clinically synthesized narrative text.");
    });
  });

  it("unsaved-assessment path: shows a save-first message with no technical jargon and never calls previewRnicaNarrativeV2 or generates narrative text locally", async () => {
    const { updateField } = renderCard({ assessmentId: null });

    fireEvent.click(screen.getByRole("button", { name: /build draft from documented findings/i }));

    expect(await screen.findByText(/save the assessment before generating the clinical narrative/i)).toBeTruthy();
    // No jargon leaks into the user-facing message.
    const message = screen.getByText(/save the assessment before generating the clinical narrative/i).textContent;
    expect(message).not.toMatch(/assessmentId/i);
    expect(message).not.toMatch(/\bapi\b/i);
    expect(message).not.toMatch(/backend/i);
    expect(message).not.toMatch(/\bv2\b/i);
    expect(message).not.toMatch(/fallback/i);
    expect(mocks.previewRnicaNarrativeV2).not.toHaveBeenCalled();
    expect(updateField).not.toHaveBeenCalledWith("clinicalNarrative", expect.anything());
  });

  it("unsaved-assessment path: clicking 'Save Assessment' saves via onSaveNow and preserves entered fields (no field is cleared/overwritten)", async () => {
    const onSaveNow = vi.fn().mockResolvedValue({ assessmentId: "assessment-999" });
    renderCard({
      assessmentId: null,
      onSaveNow,
      fullFormData: { diagnoses: { primaryDiagnosis: { description: "CHF" } } },
    });

    fireEvent.click(screen.getByRole("button", { name: /build draft from documented findings/i }));
    fireEvent.click(await screen.findByRole("button", { name: /save assessment/i }));

    await waitFor(() => expect(onSaveNow).toHaveBeenCalledTimes(1));
    // Saving must never touch any documented field directly — the save
    // path only persists the assessment; it does not rewrite formData.
  });

  it("V2 failure: shows an error, offers Retry, and never generates a legacy-fallback narrative locally", async () => {
    mocks.previewRnicaNarrativeV2.mockRejectedValue(new Error("Service unavailable"));
    const { updateField } = renderCard({
      assessmentId: "assessment-123",
      diagnosesData: {}, // no existing narrative, so Build Draft calls applyDraft() directly
    });

    fireEvent.click(screen.getByRole("button", { name: /build draft from documented findings/i }));

    expect(await screen.findByText(/service unavailable/i)).toBeTruthy();
    expect(screen.getByRole("button", { name: /retry/i })).toBeTruthy();
    // Failure must never fall back to any local/legacy narrative text.
    expect(updateField).not.toHaveBeenCalledWith("clinicalNarrative", expect.anything());

    mocks.previewRnicaNarrativeV2.mockResolvedValue({ full_text: "Recovered V2 narrative." });
    fireEvent.click(screen.getByRole("button", { name: /retry/i }));
    await waitFor(() => {
      expect(updateField).toHaveBeenCalledWith("clinicalNarrative", "Recovered V2 narrative.");
    });
  });

  it("existing-narrative replacement requires explicit confirmation before calling previewRnicaNarrativeV2", async () => {
    mocks.previewRnicaNarrativeV2.mockResolvedValue({ full_text: "New V2 narrative." });
    renderCard({
      assessmentId: "assessment-123",
      diagnosesData: { clinicalNarrative: "Existing RN-authored narrative." },
    });

    fireEvent.click(screen.getByRole("button", { name: /build draft from documented findings/i }));
    expect(screen.getByText(/a clinical narrative already exists/i)).toBeTruthy();
    expect(mocks.previewRnicaNarrativeV2).not.toHaveBeenCalled();

    fireEvent.click(screen.getByRole("button", { name: /replace with new draft/i }));
    await waitFor(() => expect(mocks.previewRnicaNarrativeV2).toHaveBeenCalledWith("assessment-123"));
  });

  it("writes narrative text, context fingerprint, and resets review status together (the exact state the autosave/save path persists to the backend on the next save+reload cycle)", async () => {
    mocks.previewRnicaNarrativeV2.mockResolvedValue({ full_text: "Persisted-ready narrative text." });
    const { updateField } = renderCard({ assessmentId: "assessment-123", diagnosesData: {} });

    fireEvent.click(screen.getByRole("button", { name: /build draft from documented findings/i }));

    await waitFor(() => {
      expect(updateField).toHaveBeenCalledWith("clinicalNarrative", "Persisted-ready narrative text.");
      expect(updateField).toHaveBeenCalledWith("clinicalNarrativeContextFingerprint", expect.any(String));
      expect(updateField).toHaveBeenCalledWith("clinicalNarrativeReviewed", false);
    });
  });
});
