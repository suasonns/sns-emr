import { describe, it, expect, beforeEach } from "vitest";
import { deepMergeFormData } from "./RNICA.jsx";
import {
  CHANGE_OF_CONDITION_REASONS,
  stageNewUpdateAssessmentRequest,
  consumeStagedNewUpdateAssessmentRequest,
} from "../intake/NursingAssessmentBoard.jsx";

// R3 (Owner Directive, "RNICA Update/HUV Creation Workflow", clarified by
// the OWNER CLARIFICATION reframing the trigger away from HOPE/HUV
// calendar windows and toward clinical need).
//
// This suite proves the deterministic, mockable building blocks of the
// Update Assessment creation workflow:
//   1. changeOfConditionContext survives deepMergeFormData untouched (the
//      mechanism that lets it live inside the existing form_data JSON
//      contract with zero schema change).
//   2. stageNewUpdateAssessmentRequest/consumeStagedNewUpdateAssessmentRequest
//      -- the single shared staging function both entry points (the
//      Nursing Assessment history panel and VisitNotes.jsx) funnel
//      through -- validate input, never silently accept a missing reason,
//      and hand off exactly once (read-and-clear).
//   3. The reason list contains no HOPE/HUV-window wording (per the
//      OWNER CLARIFICATION's explicit removal instruction).
//
// Full component-mount behavior (RNICA's forceNewDraft load-effect bypass,
// the in-form Plan of Care card, and the "New Update Assessment" button)
// is verified by the required manual browser UAT, which exercises the
// real backend rather than a mocked one.

describe("deepMergeFormData preserves changeOfConditionContext", () => {
  const INITIAL_FORM_SAMPLE = { visitMeta: { discipline: "RN" } };

  it("preserves an extra top-level key not present in defaults", () => {
    const saved = {
      visitMeta: { discipline: "RN" },
      changeOfConditionContext: {
        source: "VISIT_NOTE_CHANGE_OF_CONDITION",
        reasonCode: "WORSENING_SYMPTOM_OR_FINDING",
      },
    };
    const merged = deepMergeFormData(INITIAL_FORM_SAMPLE, saved);
    expect(merged.changeOfConditionContext).toEqual(saved.changeOfConditionContext);
  });

  it("is a no-op pass-through when changeOfConditionContext is absent", () => {
    const merged = deepMergeFormData(INITIAL_FORM_SAMPLE, { visitMeta: { discipline: "RN" } });
    expect(merged.changeOfConditionContext).toBeUndefined();
  });
});

describe("CHANGE_OF_CONDITION_REASONS", () => {
  it("contains no HOPE/HUV calendar-window wording", () => {
    const joined = CHANGE_OF_CONDITION_REASONS.map((r) => r.label).join(" ").toLowerCase();
    expect(joined).not.toMatch(/huv/);
    expect(joined).not.toMatch(/hope update visit/);
  });

  it("always ends with an Other option", () => {
    expect(CHANGE_OF_CONDITION_REASONS[CHANGE_OF_CONDITION_REASONS.length - 1].value).toBe("OTHER");
  });
});

describe("stageNewUpdateAssessmentRequest / consumeStagedNewUpdateAssessmentRequest", () => {
  beforeEach(() => {
    sessionStorage.clear();
  });

  it("throws when patientId is missing", () => {
    expect(() => stageNewUpdateAssessmentRequest(null, { reasonCode: "NEW_SYMPTOM_OR_FINDING" })).toThrow();
  });

  it("throws when reasonCode is missing", () => {
    expect(() => stageNewUpdateAssessmentRequest("patient-1", {})).toThrow();
  });

  it('requires reasonDetail when reasonCode is "OTHER"', () => {
    expect(() => stageNewUpdateAssessmentRequest("patient-1", { reasonCode: "OTHER" })).toThrow();
    expect(() => stageNewUpdateAssessmentRequest("patient-1", { reasonCode: "OTHER", reasonDetail: "Fall at home" })).not.toThrow();
  });

  it("stages a request and resolves a human-readable reasonLabel", () => {
    const context = stageNewUpdateAssessmentRequest("patient-1", {
      reasonCode: "WORSENING_SYMPTOM_OR_FINDING",
      source: "VISIT_NOTE_CHANGE_OF_CONDITION",
      originatingVisitId: "visit-9",
      originatingVisitDate: "2026-11-01",
    });
    expect(context.reasonLabel).toBe("Worsening symptom or finding");
    expect(context.source).toBe("VISIT_NOTE_CHANGE_OF_CONDITION");
    expect(context.originatingVisitId).toBe("visit-9");
  });

  it("hands off the staged request exactly once (read-and-clear)", () => {
    stageNewUpdateAssessmentRequest("patient-2", { reasonCode: "POC_REVIEW_NEEDED" });
    const first = consumeStagedNewUpdateAssessmentRequest("patient-2");
    const second = consumeStagedNewUpdateAssessmentRequest("patient-2");
    expect(first?.reasonCode).toBe("POC_REVIEW_NEEDED");
    expect(second).toBeNull();
  });

  it("keeps separate patients' staged requests independent", () => {
    stageNewUpdateAssessmentRequest("patient-a", { reasonCode: "SKIN_WOUND_CHANGE" });
    stageNewUpdateAssessmentRequest("patient-b", { reasonCode: "FUNCTIONAL_STATUS_CHANGE" });
    expect(consumeStagedNewUpdateAssessmentRequest("patient-a")?.reasonCode).toBe("SKIN_WOUND_CHANGE");
    expect(consumeStagedNewUpdateAssessmentRequest("patient-b")?.reasonCode).toBe("FUNCTIONAL_STATUS_CHANGE");
  });
});
