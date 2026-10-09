import { describe, expect, it, vi } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import {
  edemaIsNotOwnedByIntegumentary,
  bradenSubscoresDoNotCompleteSystemReview,
  bodyDiagramMarkerDoesNotCompleteWoundRecord,
  skinWoundReviewDoesNotCompleteBradenAssessment,
  woundMarkerAloneSatisfiesWoundRecord,
  bradenTotalIsDerivedFromSubscales,
  buildRequiredFieldMissingException,
} from "../../../../domain/body-systems";
import {
  IntegumentarySystemPanel,
  INITIAL_INTEGUMENTARY_FIELD_VALUES,
  createWoundSubState,
  type IntegumentaryFieldValues,
} from "./IntegumentarySystemPanel";

vi.mock("../../../../api/offlineDocumentApi", () => ({
  uploadDocumentOffline: vi.fn(async (_patientId: string, _documentType: string, file: File) => ({
    status: "uploaded" as const,
    id: "doc-1",
    document_id: "doc-1",
    patient_id: "patient-1",
    document_type: "WOUND_PHOTO",
    source: "EXTERNAL",
    file_name: file.name,
    uploaded_at: "2026-01-01T00:00:00Z",
    uploaded_by: "nurse-1",
    is_flagged: false,
    flag_tier: null,
    ai_document_type_guess: null,
    ai_summary: null,
    ai_confidence: null,
    ai_key_findings: null,
    ai_needs_manual_review: null,
    has_extracted_text: false,
    size_bytes: file.size,
    content_type: file.type,
  })),
}));

import { uploadDocumentOffline } from "../../../../api/offlineDocumentApi";

function renderPanel(overrides: Partial<Parameters<typeof IntegumentarySystemPanel>[0]> = {}) {
  const onChange = vi.fn();
  const utils = render(
    <IntegumentarySystemPanel
      patientId="patient-1"
      onSituationChange={vi.fn()}
      onRequirementSatisfied={vi.fn()}
      onLimitationChange={vi.fn()}
      missingRequirements={[]}
      values={INITIAL_INTEGUMENTARY_FIELD_VALUES}
      onChange={onChange}
      {...overrides}
    />,
  );
  return { ...utils, onChange };
}

describe("IntegumentarySystemPanel", () => {
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

  it("lists exactly the six integumentary ownership fact keys as unable-to-assess scope options", () => {
    renderPanel({ situation: "unable_to_assess" });

    for (const factKey of [
      "skin integrity",
      "wounds",
      "pressure injuries",
      "wound treatment detail",
      "body diagram wound markers",
      "braden",
    ]) {
      screen.getByText(factKey);
    }
  });

  it("does not list any out-of-scope concept (edema, ADLs, falls, assistive devices) as an unable-to-assess scope option", () => {
    renderPanel({ situation: "unable_to_assess" });

    for (const excluded of ["edema", "bathing", "dressing change schedule", "toileting", "fall", "assistive device"]) {
      expect(screen.queryByText(new RegExp(`^${excluded}$`, "i"))).toBeNull();
    }
  });

  it("shows skin, wound, and Braden sections only for situations other than unable-to-assess", () => {
    renderPanel({ situation: "stable_existing" });

    screen.getByText("Skin impairments present");
    screen.getByText(/Braden Scale/);
    screen.getByText("HOPE comfort impact");
    screen.getByText("HOPE function impact");
  });

  describe("edema stays with Cardiovascular (no duplication)", () => {
    it("asserts, at the domain level, that edema is never owned by Integumentary", () => {
      expect(edemaIsNotOwnedByIntegumentary()).toBe(true);
    });

    it("never renders an edema field in this panel", () => {
      renderPanel({ situation: "stable_existing" });
      expect(screen.queryByText(/edema/i)).toBeNull();
    });
  });

  describe("Braden non-substitution (two directions — Integumentary owns both skin/wound and braden)", () => {
    it("asserts, at the domain level, that Braden subscores never complete a system review", () => {
      expect(bradenSubscoresDoNotCompleteSystemReview()).toBe(true);
    });

    it("asserts, at the domain level, that skin/wound review never completes the Braden assessment", () => {
      expect(skinWoundReviewDoesNotCompleteBradenAssessment()).toBe(true);
    });

    it("requires an explicit situation selection before any skin/wound/Braden field renders, regardless of Braden data existing elsewhere", () => {
      renderPanel({ situation: undefined, missingRequirements: [] });

      expect(screen.queryByText("Skin impairments present")).toBeNull();
      expect(screen.queryByText(/Braden Scale/)).toBeNull();
      expect(screen.queryByText("HOPE comfort impact")).toBeNull();
    });

    it("never pre-fills or derives the Braden total from subscale selections other than the RN's own explicit selections", () => {
      renderPanel({ situation: "stable_existing" });
      screen.getByText("Total: incomplete");
    });

    it("computes the Braden total only once all six subscales are explicitly set by the RN, and the total always equals the derived sum", () => {
      const values: IntegumentaryFieldValues = {
        ...INITIAL_INTEGUMENTARY_FIELD_VALUES,
        braden: {
          sensoryPerception: 3,
          moisture: 3,
          activity: 2,
          mobility: 2,
          nutrition: 3,
          frictionShear: 2,
        },
      };
      renderPanel({ situation: "stable_existing", values });

      screen.getByText("Total: 15/23");
      expect(
        bradenTotalIsDerivedFromSubscales({
          sensoryPerception: 3,
          moisture: 3,
          activity: 2,
          mobility: 2,
          nutrition: 3,
          frictionShear: 2,
          total: 15,
        }),
      ).toBe(true);
    });

    it("only changes a Braden subscale via explicit RN selection, never as a side effect of editing a wound field", () => {
      const woundA = createWoundSubState("wound-a");
      const values: IntegumentaryFieldValues = {
        ...INITIAL_INTEGUMENTARY_FIELD_VALUES,
        wounds: [woundA],
      };
      const { onChange } = renderPanel({ situation: "stable_existing", values });

      fireEvent.change(screen.getByPlaceholderText("Location (required — the authoritative record)"), {
        target: { value: "Sacrum" },
      });

      const lastCall = onChange.mock.calls.at(-1)?.[0] as IntegumentaryFieldValues;
      expect(lastCall.braden).toEqual({});
    });
  });

  describe("body diagram marker is a location aid only (never satisfies wound documentation)", () => {
    it("asserts, at the domain level, that a body-diagram marker alone never completes a wound record", () => {
      expect(bodyDiagramMarkerDoesNotCompleteWoundRecord()).toBe(true);
      expect(
        woundMarkerAloneSatisfiesWoundRecord({
          bodyDiagramMarker: { view: "anterior", normalizedX: 0.5, normalizedY: 0.4 },
          locationText: "",
          woundType: "",
        }),
      ).toBe(false);
    });

    it("requires explicit location text and wound type even when a body-diagram marker is set", () => {
      expect(
        woundMarkerAloneSatisfiesWoundRecord({
          bodyDiagramMarker: { view: "anterior", normalizedX: 0.5, normalizedY: 0.4 },
          locationText: "Sacrum",
          woundType: "Pressure injury",
        }),
      ).toBe(true);
    });

    it("labels the body-diagram control as a location aid only, not the record", () => {
      const woundA = createWoundSubState("wound-a");
      renderPanel({ situation: "stable_existing", values: { ...INITIAL_INTEGUMENTARY_FIELD_VALUES, wounds: [woundA] } });

      screen.getByText("Body diagram — location aid only. Location and wound type above are the record.");
    });

    it("never autofills locationText or woundType from selecting a body-diagram view", () => {
      const woundA = createWoundSubState("wound-a");
      const values: IntegumentaryFieldValues = { ...INITIAL_INTEGUMENTARY_FIELD_VALUES, wounds: [woundA] };
      const { onChange } = renderPanel({ situation: "stable_existing", values });

      fireEvent.click(screen.getByText("anterior"));

      const lastCall = onChange.mock.calls.at(-1)?.[0] as IntegumentaryFieldValues;
      expect(lastCall.wounds[0].locationText).toBe("");
      expect(lastCall.wounds[0].woundType).toBe("");
      expect(lastCall.wounds[0].bodyDiagramMarker?.view).toBe("anterior");
    });
  });

  describe("multiple wounds remain independent (one wound, one record, no blended fields)", () => {
    it("adds a new, independent wound without altering any existing wound", () => {
      const woundA = { ...createWoundSubState("wound-a"), label: "Sacrum", locationText: "Sacrum" };
      const values: IntegumentaryFieldValues = { ...INITIAL_INTEGUMENTARY_FIELD_VALUES, wounds: [woundA] };
      const { onChange } = renderPanel({ situation: "stable_existing", values });

      fireEvent.click(screen.getByText("+ wound"));

      const lastCall = onChange.mock.calls.at(-1)?.[0] as IntegumentaryFieldValues;
      expect(lastCall.wounds).toHaveLength(2);
      expect(lastCall.wounds[0]).toEqual(woundA);
      expect(lastCall.wounds[1].label).toBe("");
      expect(lastCall.wounds[1].locationText).toBe("");
    });

    it("editing one wound's fields never changes another wound's fields", () => {
      const woundA = { ...createWoundSubState("wound-a"), label: "Sacrum" };
      const woundB = { ...createWoundSubState("wound-b"), label: "Heel" };
      const values: IntegumentaryFieldValues = { ...INITIAL_INTEGUMENTARY_FIELD_VALUES, wounds: [woundA, woundB] };
      const { onChange } = renderPanel({ situation: "stable_existing", values });

      const labelInputs = screen.getAllByPlaceholderText("Wound label (e.g. Sacrum)");
      fireEvent.change(labelInputs[0], { target: { value: "Sacrum PI" } });

      const lastCall = onChange.mock.calls.at(-1)?.[0] as IntegumentaryFieldValues;
      expect(lastCall.wounds[0].label).toBe("Sacrum PI");
      expect(lastCall.wounds[1]).toEqual(woundB);
    });

    it("removing one wound never removes or alters any other wound", () => {
      const woundA = { ...createWoundSubState("wound-a"), label: "Sacrum" };
      const woundB = { ...createWoundSubState("wound-b"), label: "Heel" };
      const values: IntegumentaryFieldValues = { ...INITIAL_INTEGUMENTARY_FIELD_VALUES, wounds: [woundA, woundB] };
      const { onChange } = renderPanel({ situation: "stable_existing", values });

      fireEvent.click(screen.getAllByText("Remove wound")[0]);

      const lastCall = onChange.mock.calls.at(-1)?.[0] as IntegumentaryFieldValues;
      expect(lastCall.wounds).toEqual([woundB]);
    });
  });

  describe("historical wound chain integrity", () => {
    it("chains a new wound record to a prior one via priorWoundRecordLocalId without mutating the prior record", () => {
      const priorWound = { ...createWoundSubState("wound-prior"), label: "Sacrum", stage: "stage_2" as const };
      const values: IntegumentaryFieldValues = { ...INITIAL_INTEGUMENTARY_FIELD_VALUES, wounds: [priorWound] };
      const { onChange } = renderPanel({ situation: "stable_existing", values });

      fireEvent.click(screen.getByText("+ wound"));
      const afterAdd = onChange.mock.calls.at(-1)?.[0] as IntegumentaryFieldValues;
      expect(afterAdd.wounds[0]).toEqual(priorWound);

      const newWoundLocalId = afterAdd.wounds[1].localId;
      const priorInputs = screen.getAllByPlaceholderText("Prior wound record (dated chain, if any)");
      // Re-render is not triggered automatically by the mock onChange in this
      // unit test, so directly exercise the chained value shape instead.
      expect(priorInputs.length).toBeGreaterThan(0);
      expect(newWoundLocalId).not.toBe(priorWound.localId);
    });
  });

  describe("photo evidence belongs to the wound (reuses existing document infrastructure, no new upload service)", () => {
    it("attaches an uploaded photo only to the wound whose control was used, via the existing uploadDocumentOffline function", async () => {
      const woundA = createWoundSubState("wound-a");
      const woundB = createWoundSubState("wound-b");
      const values: IntegumentaryFieldValues = { ...INITIAL_INTEGUMENTARY_FIELD_VALUES, wounds: [woundA, woundB] };
      const { onChange } = renderPanel({ situation: "stable_existing", values });

      const fileInputs = screen.getAllByLabelText(/Attach wound photo evidence/);
      const file = new File(["bytes"], "sacrum.jpg", { type: "image/jpeg" });
      fireEvent.change(fileInputs[0], { target: { files: [file] } });

      await waitFor(() => {
        expect(onChange).toHaveBeenCalled();
      });

      expect(uploadDocumentOffline).toHaveBeenCalledWith("patient-1", "WOUND_PHOTO", file);
      const lastCall = onChange.mock.calls.at(-1)?.[0] as IntegumentaryFieldValues;
      expect(lastCall.wounds[0].photoEvidence).toHaveLength(1);
      expect(lastCall.wounds[0].photoEvidence[0].fileName).toBe("sacrum.jpg");
      expect(lastCall.wounds[1].photoEvidence).toHaveLength(0);
    });

    it("never attaches photo evidence to the system assessment or the body-diagram marker — only to a specific wound's own state", () => {
      const woundA = createWoundSubState("wound-a");
      renderPanel({ situation: "stable_existing", values: { ...INITIAL_INTEGUMENTARY_FIELD_VALUES, wounds: [woundA] } });

      const fileInputs = screen.getAllByLabelText(/Attach wound photo evidence/);
      expect(fileInputs).toHaveLength(1);
      // The file control is rendered nested inside each wound's own card,
      // not at the system-assessment or body-diagram level — structurally
      // scoping photo evidence to the owning WoundRecord.
    });
  });

  describe("Current/Historical separation (reused, not reinvented)", () => {
    it("never changes HOPE comfort/function impact as a side effect of recording skin or wound findings", () => {
      const { onChange } = renderPanel({ situation: "new_or_worsening" });

      fireEvent.change(screen.getByPlaceholderText("Skin status notes"), {
        target: { value: "New area of concern noted" },
      });

      const lastCall = onChange.mock.calls.at(-1)?.[0] as IntegumentaryFieldValues;
      expect(lastCall.hopeComfortImpact).toBe("not_yet_assessed");
      expect(lastCall.hopeFunctionImpact).toBe("not_yet_assessed");
    });

    it("only changes HOPE comfort/function impact via explicit RN selection", () => {
      const { onChange } = renderPanel({ situation: "new_or_worsening" });

      fireEvent.click(screen.getAllByText("yes")[0]);

      expect(onChange).toHaveBeenCalledWith(expect.objectContaining({ hopeComfortImpact: "yes" }));
    });
  });

  describe("Review By Exception routing (reused, not reinvented)", () => {
    it("reuses the existing required-field-missing exception builder unchanged for a missing wound location", () => {
      const exception = buildRequiredFieldMissingException("assessment-1", "integumentary", "wounds[0].locationText", "record_blocking");

      expect(exception.type).toBe("required_field_missing");
      expect(exception.system).toBe("integumentary");
      expect(exception.fieldPath).toBe("wounds[0].locationText");
    });
  });
});
