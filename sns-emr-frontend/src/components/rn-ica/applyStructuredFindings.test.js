import { describe, expect, it } from "vitest";

import { applyAllNonConflicting, applyStructuredFindings, sectionsWithAppliedStructuredFields } from "./applyStructuredFindings";

function findingOf(overrides = {}) {
  return {
    concept_code: "CV_HEART_FAILURE_SYSTOLIC",
    value: true,
    source_type: "REFERRAL_HNP",
    source_excerpt: "Systolic heart failure, chronic.",
    confidence: 0.95,
    assertion_status: "CURRENT",
    subject: "PATIENT",
    ...overrides,
  };
}

describe("applyStructuredFindings", () => {
  it("populates a truly blank (undefined) boolean-presence field", () => {
    const { formData, appliedFields, conflicts } = applyStructuredFindings(
      { cardiovascular: {} },
      [findingOf()]
    );

    expect(formData.cardiovascular.heartFailurePresent).toBe(true);
    expect(formData.cardiovascular.heartFailureType).toEqual(["Systolic"]);
    expect(appliedFields.map((f) => f.path)).toEqual(
      expect.arrayContaining(["heartFailurePresent", "heartFailureType"])
    );
    expect(conflicts).toEqual([]);
  });

  it("NEVER overwrites an RN-entered `false` on a boolean-presence field -- records a conflict instead", () => {
    const { formData, appliedFields, conflicts } = applyStructuredFindings(
      { cardiovascular: { heartFailurePresent: false } },
      [findingOf()]
    );

    // RN's explicit "no" must be preserved exactly as entered.
    expect(formData.cardiovascular.heartFailurePresent).toBe(false);
    expect(appliedFields.some((f) => f.path === "heartFailurePresent")).toBe(false);

    const conflict = conflicts.find((c) => c.path === "heartFailurePresent");
    expect(conflict).toBeDefined();
    expect(conflict.existingValue).toBe(false);
    expect(conflict.suggestedValue).toBe(true);
    expect(conflict.concept_code).toBe("CV_HEART_FAILURE_SYSTOLIC");
  });

  it("never overwrites any RN-entered value on a blank-only set field, regardless of type", () => {
    const { formData, conflicts } = applyStructuredFindings(
      { performanceStatus: { nyha: "II" } },
      [findingOf({ concept_code: "PERF_NYHA_CLASS_IV", value: true })]
    );

    expect(formData.performanceStatus.nyha).toBe("II");
    expect(conflicts.some((c) => c.path === "nyha" && c.existingValue === "II")).toBe(true);
  });

  it("splits multiple wound locations into separate draft rows, never merging them", () => {
    const { formData } = applyStructuredFindings(
      { skin: { wounds: [] } },
      [
        findingOf({ concept_code: "SKIN_WOUND_PRESENT", value: "left buttock", source_excerpt: "left buttock wound" }),
        findingOf({ concept_code: "SKIN_WOUND_PRESENT", value: "right foot", source_excerpt: "right foot wound" }),
      ]
    );

    expect(formData.skin.wounds).toHaveLength(2);
    expect(formData.skin.wounds.map((w) => w.location).sort()).toEqual(["left buttock", "right foot"]);
  });

  it("never applies a duplicate wound row for the same location twice", () => {
    const finding = findingOf({ concept_code: "SKIN_WOUND_PRESENT", value: "right foot" });
    const first = applyStructuredFindings({ skin: { wounds: [] } }, [finding]);
    const second = applyStructuredFindings(first.formData, [finding]);

    expect(second.formData.skin.wounds).toHaveLength(1);
  });

  it("routes HISTORICAL/NEGATED/UNCERTAIN findings to reviewNeeded, never applies or conflicts them", () => {
    const { formData, appliedFields, conflicts, reviewNeeded } = applyStructuredFindings(
      { cardiovascular: {} },
      [findingOf({ assertion_status: "HISTORICAL" })]
    );

    expect(formData.cardiovascular.heartFailurePresent).toBeUndefined();
    expect(appliedFields).toEqual([]);
    expect(conflicts).toEqual([]);
    expect(reviewNeeded).toHaveLength(1);
  });

  it("skips a concept code unknown to the frontend registry mirror rather than guessing", () => {
    const { formData, appliedFields, conflicts } = applyStructuredFindings(
      { cardiovascular: {} },
      [findingOf({ concept_code: "NOT_A_REAL_CONCEPT" })]
    );

    expect(appliedFields).toEqual([]);
    expect(conflicts).toEqual([]);
    expect(formData.cardiovascular).toEqual({});
  });

  it("sectionsWithAppliedStructuredFields only counts sections with an actual applied write", () => {
    const applied = [
      { section: "cardiovascular", path: "heartFailurePresent" },
      { section: "infection", path: "currentInfections" },
    ];
    expect(sectionsWithAppliedStructuredFields(applied)).toEqual(new Set(["cardiovascular", "infection"]));
    expect(sectionsWithAppliedStructuredFields([])).toEqual(new Set());
  });
});

describe("applyAllNonConflicting", () => {
  it("applies every signal when none conflict", () => {
    const signals = [
      { id: "sig-1", structured_findings: [findingOf({ concept_code: "CV_HEART_FAILURE_SYSTOLIC" })] },
      {
        id: "sig-2",
        structured_findings: [
          findingOf({ concept_code: "SKIN_WOUND_PRESENT", value: "right foot", source_excerpt: "right foot wound" }),
        ],
      },
    ];

    const result = applyAllNonConflicting({ cardiovascular: {}, skin: { wounds: [] } }, signals);

    expect(result.appliedSignalIds.sort()).toEqual(["sig-1", "sig-2"]);
    expect(result.skippedSignalIds).toEqual([]);
    expect(result.formData.cardiovascular.heartFailurePresent).toBe(true);
    expect(result.formData.skin.wounds).toHaveLength(1);
    expect(result.appliedFieldsBySignal["sig-1"].length).toBeGreaterThan(0);
  });

  it("leaves a conflicting signal's fields completely untouched and reports it skipped", () => {
    const signals = [
      { id: "sig-clean", structured_findings: [findingOf({ concept_code: "SKIN_WOUND_PRESENT", value: "right foot" })] },
      { id: "sig-conflict", structured_findings: [findingOf({ concept_code: "CV_HEART_FAILURE_SYSTOLIC" })] },
    ];

    const result = applyAllNonConflicting(
      { cardiovascular: { heartFailurePresent: false }, skin: { wounds: [] } },
      signals
    );

    expect(result.appliedSignalIds).toEqual(["sig-clean"]);
    expect(result.skippedSignalIds).toEqual(["sig-conflict"]);
    // RN's explicit "No" preserved exactly -- the conflicting signal never
    // partially wrote anything (heartFailureType, its second write, is
    // also left alone since the whole signal is skipped).
    expect(result.formData.cardiovascular.heartFailurePresent).toBe(false);
    expect(result.formData.cardiovascular.heartFailureType).toBeUndefined();
    expect(result.formData.skin.wounds).toHaveLength(1);
    expect(result.skippedConflicts[0].signal_id).toBe("sig-conflict");
  });

  it("counts a signal with only HISTORICAL/reviewNeeded findings as cleanly applied (no conflict, no write)", () => {
    const signals = [
      { id: "sig-historical", structured_findings: [findingOf({ assertion_status: "HISTORICAL" })] },
    ];

    const result = applyAllNonConflicting({ cardiovascular: {} }, signals);

    expect(result.appliedSignalIds).toEqual(["sig-historical"]);
    expect(result.skippedSignalIds).toEqual([]);
    expect(result.appliedFieldsBySignal["sig-historical"]).toEqual([]);
  });

  it("never mutates the original formData object across signals (immutability preserved)", () => {
    const original = { cardiovascular: {}, skin: { wounds: [] } };
    const signals = [
      { id: "sig-1", structured_findings: [findingOf({ concept_code: "CV_HEART_FAILURE_SYSTOLIC" })] },
    ];

    applyAllNonConflicting(original, signals);

    expect(original.cardiovascular.heartFailurePresent).toBeUndefined();
  });
});
