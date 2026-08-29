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

  // -------------------------------------------------------------------------
  // RNICA Completion Sprint: Skin/Wounds row-field enrichment
  // (SKIN_WOUND_PRESENT creates the row; every attribute concept below must
  // enrich that SAME row, never fabricate a second one for one wound).
  // -------------------------------------------------------------------------

  it("enriches the existing wound row's stage/type/drainage/odor/flags without creating a second row", () => {
    const { formData } = applyStructuredFindings(
      { skin: { wounds: [] } },
      [
        findingOf({ concept_code: "SKIN_WOUND_PRESENT", value: "sacrum", source_excerpt: "sacral wound" }),
        findingOf({ concept_code: "SKIN_WOUND_STAGE_2", value: true }),
        findingOf({ concept_code: "SKIN_WOUND_DRAINAGE_MODERATE", value: true }),
        findingOf({ concept_code: "SKIN_WOUND_ODOR_NONE", value: true }),
        findingOf({ concept_code: "SKIN_WOUND_PRESSURE_INJURY_FLAG", value: true }),
      ]
    );

    expect(formData.skin.wounds).toHaveLength(1);
    expect(formData.skin.wounds[0]).toMatchObject({
      location: "sacrum",
      stage: "Stage 2",
      drainage: "Moderate",
      odor: "None",
      presentAsPressureInjury: true,
    });
  });

  it("enriches the existing wound row's bounded numeric and free-text measurements", () => {
    const { formData } = applyStructuredFindings(
      { skin: { wounds: [] } },
      [
        findingOf({ concept_code: "SKIN_WOUND_PRESENT", value: "right heel", source_excerpt: "right heel wound" }),
        findingOf({ concept_code: "SKIN_WOUND_LENGTH_CM", value: 3.5 }),
        findingOf({ concept_code: "SKIN_WOUND_WIDTH_CM", value: 2 }),
        findingOf({ concept_code: "SKIN_WOUND_DRESSING", value: "foam dressing" }),
        findingOf({ concept_code: "SKIN_WOUND_CURRENT_TREATMENT", value: "cleanse and pack daily" }),
      ]
    );

    expect(formData.skin.wounds[0]).toMatchObject({
      location: "right heel",
      length: 3.5,
      width: 2,
      dressing: "foam dressing",
      currentTreatment: "cleanse and pack daily",
    });
  });

  it("never fabricates a wound row for a set_row_field concept when no wound row exists yet", () => {
    const { formData, appliedFields } = applyStructuredFindings(
      { skin: { wounds: [] } },
      [findingOf({ concept_code: "SKIN_WOUND_STAGE_2", value: true })]
    );

    expect(formData.skin.wounds).toEqual([]);
    expect(appliedFields).toEqual([]);
  });

  it("never overwrites an RN-entered wound attribute and records a conflict instead", () => {
    const { formData, conflicts } = applyStructuredFindings(
      { skin: { wounds: [{ location: "sacrum", stage: "Stage 3" }] } },
      [findingOf({ concept_code: "SKIN_WOUND_STAGE_2", value: true })]
    );

    expect(formData.skin.wounds[0].stage).toBe("Stage 3");
    expect(conflicts.some((c) => c.path.endsWith(".stage") && c.existingValue === "Stage 3")).toBe(true);
  });

  // -------------------------------------------------------------------------
  // Regression: non-row-scoped free_text_bounded/date_bounded value_slot
  // concepts (no push_draft_row, no FieldWrite of their own) were silently
  // never applied before this sprint -- only kind === "numeric" was handled.
  // -------------------------------------------------------------------------

  it("applies a non-row free_text_bounded value_slot concept that has no writes of its own", () => {
    const { formData, appliedFields } = applyStructuredFindings(
      { nutrition: {} },
      [findingOf({ concept_code: "NUTRITION_DIET_TYPE", value: "Pureed, low-sodium" })]
    );

    expect(formData.nutrition.dietType).toBe("Pureed, low-sodium");
    expect(appliedFields.some((f) => f.path === "dietType")).toBe(true);
  });

  it("applies GU catheter free-text and date value_slot fields onto plain (non-array) nested paths", () => {
    const { formData } = applyStructuredFindings(
      { genitourinary: { catheter: { irrigation: {} } } },
      [
        findingOf({ concept_code: "GU_CATHETER_SIZE", value: "16 Fr" }),
        findingOf({ concept_code: "GU_CATHETER_INSERTION_DATE", value: "2024-03-15" }),
        findingOf({ concept_code: "GU_CATHETER_IRRIGATION_SOLUTION", value: "Normal saline" }),
      ]
    );

    expect(formData.genitourinary.catheter.present).toBe(true);
    expect(formData.genitourinary.catheter.size).toBe("16 Fr");
    expect(formData.genitourinary.catheter.insertionDate).toBe("2024-03-15");
    expect(formData.genitourinary.catheter.irrigation.solution).toBe("Normal saline");
  });

  it("never overwrites an RN-entered non-row value_slot value -- records a conflict instead", () => {
    const { formData, conflicts } = applyStructuredFindings(
      { genitourinary: { catheter: { size: "18 Fr" } } },
      [findingOf({ concept_code: "GU_CATHETER_SIZE", value: "16 Fr" })]
    );

    expect(formData.genitourinary.catheter.size).toBe("18 Fr");
    expect(conflicts.some((c) => c.path === "catheter.size" && c.existingValue === "18 Fr")).toBe(true);
  });

  it("applies GI abdominalGirth and bowelFrequency free-text value_slot fields (RNICA Sprint 4/7)", () => {
    const { formData, appliedFields } = applyStructuredFindings(
      { gastrointestinal: {} },
      [
        findingOf({ concept_code: "GI_ABDOMINAL_GIRTH", value: "34 in" }),
        findingOf({ concept_code: "GI_BOWEL_FREQUENCY", value: "Every 2 days" }),
      ]
    );

    expect(formData.gastrointestinal.abdominalGirth).toBe("34 in");
    expect(formData.gastrointestinal.bowelFrequency).toBe("Every 2 days");
    expect(appliedFields.some((f) => f.path === "abdominalGirth")).toBe(true);
    expect(appliedFields.some((f) => f.path === "bowelFrequency")).toBe(true);
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

  it("never overwrites an RN-entered value even inside an otherwise-applied signal, and still surfaces the conflict", () => {
    // CV_HEART_FAILURE_SYSTOLIC writes BOTH heartFailurePresent ("set",
    // conflicts here because the RN already entered `false`) and
    // heartFailureType ("multi_add", still safely appends since it's
    // untouched). The signal as a whole is "applied" (it did write
    // something real), but the RN's explicit "No" on heartFailurePresent
    // must remain exactly as entered and be reported as a conflict.
    const signals = [
      { id: "sig-clean", structured_findings: [findingOf({ concept_code: "SKIN_WOUND_PRESENT", value: "right foot" })] },
      { id: "sig-conflict", structured_findings: [findingOf({ concept_code: "CV_HEART_FAILURE_SYSTOLIC" })] },
    ];

    const result = applyAllNonConflicting(
      { cardiovascular: { heartFailurePresent: false }, skin: { wounds: [] } },
      signals
    );

    expect(result.appliedSignalIds.sort()).toEqual(["sig-clean", "sig-conflict"]);
    expect(result.skippedSignalIds).toEqual([]);
    // RN's explicit "No" preserved exactly...
    expect(result.formData.cardiovascular.heartFailurePresent).toBe(false);
    // ...but the non-conflicting sibling write from the same signal is
    // still applied rather than discarded.
    expect(result.formData.cardiovascular.heartFailureType).toEqual(["Systolic"]);
    expect(result.formData.skin.wounds).toHaveLength(1);
    expect(result.skippedConflicts[0].signal_id).toBe("sig-conflict");
    expect(result.skippedConflicts[0].path).toBe("heartFailurePresent");
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

  it("marks a signal fully skipped when it produces a conflict and nothing applies", () => {
    const signals = [
      { id: "sig-all-conflict", structured_findings: [findingOf({ concept_code: "PERF_NYHA_CLASS_IV", value: true })] },
    ];

    const result = applyAllNonConflicting({ performanceStatus: { nyha: "II" } }, signals);

    expect(result.appliedSignalIds).toEqual([]);
    expect(result.skippedSignalIds).toEqual(["sig-all-conflict"]);
    expect(result.formData.performanceStatus.nyha).toBe("II");
  });

  it("applies a signal's non-conflicting finding even when a DIFFERENT finding bundled in the same signal conflicts", () => {
    // Regression test for a real Phase 4 admission-validation defect: a
    // harvested signal containing both a brand-new wound mention and an
    // unrelated already-set duplicate finding must not lose the wound
    // just because its sibling finding conflicts.
    const signals = [
      {
        id: "sig-mixed",
        structured_findings: [
          findingOf({ concept_code: "SKIN_WOUND_PRESENT", value: "right foot", source_excerpt: "right foot wound" }),
          findingOf({ concept_code: "CV_HEART_FAILURE_SYSTOLIC" }),
        ],
      },
    ];

    const result = applyAllNonConflicting(
      { cardiovascular: { heartFailurePresent: false }, skin: { wounds: [] } },
      signals
    );

    // The conflicting CV finding must still be preserved untouched and
    // surfaced for RN review...
    expect(result.formData.cardiovascular.heartFailurePresent).toBe(false);
    expect(result.skippedConflicts.some((c) => c.signal_id === "sig-mixed" && c.path === "heartFailurePresent")).toBe(true);

    // ...but the non-conflicting wound finding from the SAME signal must
    // still be applied rather than discarded.
    expect(result.formData.skin.wounds).toHaveLength(1);
    expect(result.formData.skin.wounds[0].location).toBe("right foot");
    expect(result.appliedSignalIds).toContain("sig-mixed");
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
