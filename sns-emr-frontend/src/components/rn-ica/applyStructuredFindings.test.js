import { describe, expect, it } from "vitest";

import {
  applyAllNonConflicting,
  applyStructuredFindings,
  classifyConflict,
  resolveFieldConflict,
  resolveWoundReview,
  sectionsWithAppliedStructuredFields,
  summarizeConflictsByCategory,
} from "./applyStructuredFindings";

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

  it("auto-populates an untouched-default boolean `false` when initialFormData proves the whole section is pristine", () => {
    const initialFormData = { cardiovascular: { heartFailurePresent: false, heartFailureType: [] } };
    const { formData, appliedFields, conflicts } = applyStructuredFindings(
      { cardiovascular: { heartFailurePresent: false, heartFailureType: [] } },
      [findingOf()],
      initialFormData
    );

    expect(formData.cardiovascular.heartFailurePresent).toBe(true);
    expect(appliedFields.some((f) => f.path === "heartFailurePresent")).toBe(true);
    expect(conflicts).toEqual([]);
  });

  it("still records a conflict for boolean `false` even with initialFormData when the section has already been engaged (another field differs from its default)", () => {
    const initialFormData = { cardiovascular: { heartFailurePresent: false, pacemaker: false } };
    const { formData, appliedFields, conflicts } = applyStructuredFindings(
      { cardiovascular: { heartFailurePresent: false, pacemaker: true } }, // RN already documented pacemaker=true
      [findingOf()],
      initialFormData
    );

    expect(formData.cardiovascular.heartFailurePresent).toBe(false);
    expect(appliedFields.some((f) => f.path === "heartFailurePresent")).toBe(false);
    expect(conflicts.some((c) => c.path === "heartFailurePresent")).toBe(true);
  });

  it("treats a field already set to the EXACT suggested value as already-satisfied, not a conflict (regression: chunked/overlapping extraction re-detecting the same fact across multiple findings must not flood the conflict queue)", () => {
    // A field previously applied (or documented by an earlier chunk's
    // finding) already holds true -- the concept's own write value is
    // also true. This must be recognized as "nothing to do here", not a
    // disagreement requiring RN review.
    const { formData, appliedFields, conflicts } = applyStructuredFindings(
      { cardiovascular: { heartFailurePresent: true, heartFailureType: ["Systolic"] } },
      [findingOf()]
    );

    expect(formData.cardiovascular.heartFailurePresent).toBe(true);
    expect(appliedFields.some((f) => f.path === "heartFailurePresent" && f.writeKind === "already_satisfied")).toBe(true);
    expect(conflicts.some((c) => c.path === "heartFailurePresent")).toBe(false);
  });

  it("still records a conflict when the existing value DIFFERS from the suggested value (a real disagreement, not a duplicate)", () => {
    const { formData, appliedFields, conflicts } = applyStructuredFindings(
      { endocrine: { diabetes: { type: "Type 1" } } },
      [findingOf({ concept_code: "ENDO_DIABETES_TYPE2", value: "Type 2" })]
    );

    expect(formData.endocrine.diabetes.type).toBe("Type 1");
    expect(appliedFields.some((f) => f.path === "diabetes.type")).toBe(false);
    const conflict = conflicts.find((c) => c.path === "diabetes.type");
    expect(conflict).toBeDefined();
    expect(conflict.existingValue).toBe("Type 1");
    expect(conflict.suggestedValue).toBe("Type 2");
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

  it("applies Endocrine/Nutrition/Respiratory/MSK bounded value_slot concepts (RNICA Sprint 5-7/7)", () => {
    const { formData, appliedFields } = applyStructuredFindings(
      { endocrine: { diabetes: {} }, nutrition: {}, respiratory: { ventilator: {} }, musculoskeletal: { fallHistory: {} } },
      [
        findingOf({ concept_code: "ENDO_INSULIN_TYPE", value: "Lantus" }),
        findingOf({ concept_code: "ENDO_INSULIN_DOSE", value: "20 units qHS" }),
        findingOf({ concept_code: "ENDO_LAST_HBA1C_DATE", value: "2024-06-01" }),
        findingOf({ concept_code: "NUTRITION_SUPPLEMENTS", value: "Boost Glucose Control" }),
        findingOf({ concept_code: "RESP_VENTILATOR_SETTINGS", value: "BiPAP 10/5, RA" }),
        findingOf({ concept_code: "MSK_FALL_INJURIES", value: "Bruised hip, no fracture" }),
      ]
    );

    expect(formData.endocrine.diabetes.insulinType).toBe("Lantus");
    expect(formData.endocrine.diabetes.insulinDose).toBe("20 units qHS");
    expect(formData.endocrine.diabetes.lastHbA1cDate).toBe("2024-06-01");
    expect(formData.nutrition.nutritionalSupplements).toBe("Boost Glucose Control");
    expect(formData.respiratory.ventilator.ventilatorTypeAndSettings).toBe("BiPAP 10/5, RA");
    expect(formData.musculoskeletal.fallHistory.fallInjuries).toBe("Bruised hip, no fracture");
    expect(appliedFields.length).toBe(6);
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

describe("resolveFieldConflict (RN review: Accept / Reject / Modify / Merge)", () => {
  function conflictOf(overrides = {}) {
    return {
      signal_id: "sig-1",
      section: "nutrition",
      path: "dietType",
      existingValue: "Pre Dialysis",
      suggestedValue: "Diabetic Consistent Carbohydrate",
      concept_code: "NUTRITION_DIET_TYPE",
      source_type: "REFERRAL_HNP",
      ...overrides,
    };
  }

  it("accept overwrites the field with the AI-suggested value", () => {
    const formData = { nutrition: { dietType: "Pre Dialysis" } };
    const result = resolveFieldConflict(formData, conflictOf(), "accept");
    expect(result.formData.nutrition.dietType).toBe("Diabetic Consistent Carbohydrate");
    expect(result.noop).toBe(false);
  });

  it("reject keeps the existing value and performs no write (noop)", () => {
    const formData = { nutrition: { dietType: "Pre Dialysis" } };
    const result = resolveFieldConflict(formData, conflictOf(), "reject");
    expect(result.formData).toBe(formData); // exact same reference, nothing written
    expect(result.resolvedValue).toBe("Pre Dialysis");
    expect(result.noop).toBe(true);
  });

  it("modify overwrites the field with an RN-typed custom value distinct from both existing and suggested", () => {
    const formData = { nutrition: { dietType: "Pre Dialysis" } };
    const result = resolveFieldConflict(formData, conflictOf(), "modify", "Renal diet, no added salt");
    expect(result.formData.nutrition.dietType).toBe("Renal diet, no added salt");
  });

  it("merge combines existing + suggested free-text fragments into one value", () => {
    const formData = { nutrition: { dietType: "Pre Dialysis" } };
    const result = resolveFieldConflict(formData, conflictOf(), "merge");
    expect(result.formData.nutrition.dietType).toBe("Pre Dialysis, Diabetic Consistent Carbohydrate");
  });

  it("merge does not duplicate a fragment already contained in the existing value", () => {
    const formData = { nutrition: { dietType: "Pre Dialysis, Diabetic Consistent Carbohydrate" } };
    const result = resolveFieldConflict(formData, conflictOf(), "merge");
    expect(result.formData.nutrition.dietType).toBe("Pre Dialysis, Diabetic Consistent Carbohydrate");
  });

  it("merge is refused (returns null) for a boolean conflict -- there is nothing to combine", () => {
    const formData = { musculoskeletal: { contracturesPresent: false } };
    const conflict = conflictOf({
      section: "musculoskeletal",
      path: "contracturesPresent",
      existingValue: false,
      suggestedValue: true,
      concept_code: "MSK_CONTRACTURES_PRESENT",
    });
    const result = resolveFieldConflict(formData, conflict, "merge");
    expect(result).toBeNull();
  });

  it("accept still works correctly on a boolean conflict (clinical discrepancy resolved in favor of new evidence)", () => {
    const formData = { musculoskeletal: { contracturesPresent: false } };
    const conflict = conflictOf({
      section: "musculoskeletal",
      path: "contracturesPresent",
      existingValue: false,
      suggestedValue: true,
      concept_code: "MSK_CONTRACTURES_PRESENT",
    });
    const result = resolveFieldConflict(formData, conflict, "accept");
    expect(result.formData.musculoskeletal.contracturesPresent).toBe(true);
  });

  it("an unrecognized action returns null without mutating anything", () => {
    const formData = { nutrition: { dietType: "Pre Dialysis" } };
    const result = resolveFieldConflict(formData, conflictOf(), "bogus-action");
    expect(result).toBeNull();
  });
});

describe("classifyConflict (findings classification engine) -- real production patterns", () => {
  it("classifies a compound diet order fragment as Enrichment (RN review, not urgent)", () => {
    const result = classifyConflict({
      concept_code: "NUTRITION_DIET_TYPE",
      existingValue: "Pre Dialysis",
      suggestedValue: "Diabetic Consistent Carbohydrate",
    });
    expect(result).toMatchObject({ category: 4, label: "Enrichment", rnReviewRequired: true, urgent: false, queue: "rn_review" });
  });

  it("classifies a compound supplement order fragment as Enrichment", () => {
    const result = classifyConflict({
      concept_code: "NUTRITION_SUPPLEMENTS",
      existingValue: "Boost Glucose control",
      suggestedValue: "vanilla",
    });
    expect(result).toMatchObject({ category: 4, label: "Enrichment", rnReviewRequired: true });
  });

  it("classifies a vaguer restatement of an already-specific value as Already Present (auto-resolved)", () => {
    const result = classifyConflict({
      concept_code: "NUTRITION_WEIGHT_LOSS_PAST_6_MONTHS",
      existingValue: "5 % of usual body weight 1 mon",
      suggestedValue: "Weight loss documented",
    });
    expect(result).toMatchObject({ category: 2, label: "Already Present", rnReviewRequired: false, queue: "auto_resolved" });
  });

  it("classifies a whitespace/truncation-only restatement as Duplicate (auto-resolved)", () => {
    const result = classifyConflict({
      concept_code: "NUTRITION_WEIGHT_LOSS_PAST_6_MONTHS",
      existingValue: "5 % of usual body weight 1 mon",
      suggestedValue: "5% of usual body weight in 1 m",
    });
    expect(result).toMatchObject({ category: 3, label: "Duplicate", rnReviewRequired: false, queue: "auto_resolved" });
  });

  it("classifies a severity change (hemiparesis -> hemiplegia) as Clinical Discrepancy, not Enrichment", () => {
    const result = classifyConflict({
      concept_code: "NEURO_HEMIPLEGIA_RIGHT",
      existingValue: "Right hemiparesis",
      suggestedValue: "Right hemiplegia",
    });
    expect(result).toMatchObject({ category: 5, label: "Clinical Discrepancy", rnReviewRequired: true, urgent: false, queue: "rn_review" });
  });

  it("classifies a boolean flip (contractures false -> true) as Clinical Discrepancy", () => {
    const result = classifyConflict({
      concept_code: "MSK_CONTRACTURES_PRESENT",
      existingValue: false,
      suggestedValue: true,
    });
    expect(result).toMatchObject({ category: 5, label: "Clinical Discrepancy", rnReviewRequired: true, urgent: false });
  });

  it("classifies a safety-critical boolean flip (wound/pressure-injury concept) as urgent Safety-Critical", () => {
    const result = classifyConflict({
      concept_code: "SKIN_WOUND_PRESSURE_INJURY_FLAG",
      existingValue: false,
      suggestedValue: true,
    });
    expect(result).toMatchObject({ category: 6, label: "Safety-Critical", rnReviewRequired: true, urgent: true, queue: "urgent_rn_review" });
  });

  it("classifies a safety-critical concept via its registry section even without a keyword in the code", () => {
    const result = classifyConflict(
      { concept_code: "SOME_CODE_WITHOUT_KEYWORD", existingValue: "Low", suggestedValue: "High" },
      { section: "safety" }
    );
    expect(result.category).toBe(6);
    expect(result.urgent).toBe(true);
  });

  it("summarizeConflictsByCategory buckets a realistic mixed list and never leaves anything as generic 'pending'", () => {
    const conflicts = [
      { concept_code: "NUTRITION_DIET_TYPE", existingValue: "Pre Dialysis", suggestedValue: "Diabetic Consistent Carbohydrate" },
      { concept_code: "NUTRITION_WEIGHT_LOSS_PAST_6_MONTHS", existingValue: "5 % of usual body weight 1 mon", suggestedValue: "Weight loss documented" },
      { concept_code: "NUTRITION_WEIGHT_LOSS_PAST_6_MONTHS", existingValue: "5 % of usual body weight 1 mon", suggestedValue: "5% of usual body weight in 1 m" },
      { concept_code: "NEURO_HEMIPLEGIA_RIGHT", existingValue: "Right hemiparesis", suggestedValue: "Right hemiplegia" },
      { concept_code: "MSK_CONTRACTURES_PRESENT", existingValue: false, suggestedValue: true },
      { concept_code: "SKIN_WOUND_PRESSURE_INJURY_FLAG", existingValue: false, suggestedValue: true },
    ];
    const summary = summarizeConflictsByCategory(conflicts);
    expect(summary.enrichmentSuggestions).toHaveLength(1);
    expect(summary.alreadyPresent).toHaveLength(1);
    expect(summary.duplicatesAutoResolved).toHaveLength(1);
    expect(summary.clinicalDiscrepancies).toHaveLength(2); // hemiplegia + contractures
    expect(summary.safetyCritical).toHaveLength(1);
    const totalBucketed =
      summary.enrichmentSuggestions.length +
      summary.alreadyPresent.length +
      summary.duplicatesAutoResolved.length +
      summary.clinicalDiscrepancies.length +
      summary.safetyCritical.length;
    expect(totalBucketed).toBe(conflicts.length); // nothing falls through uncategorized
  });
});

describe("wound near-duplicate detection (RN Wound Review workflow)", () => {
  it("does NOT silently add a new row when the location is a close wording match to an existing wound -- routes to woundReviewItems instead", () => {
    const { formData, woundReviewItems } = applyStructuredFindings(
      { skin: { wounds: [{ location: "Coccyx", stage: "Stage 2" }] } },
      [findingOf({ concept_code: "SKIN_WOUND_PRESENT", value: "Sacral/coccyx area", source_excerpt: "wound over the sacral/coccyx area" })]
    );

    // Nothing silently written -- neither a new row nor a merge.
    expect(formData.skin.wounds).toHaveLength(1);
    expect(woundReviewItems).toHaveLength(1);
    expect(woundReviewItems[0]).toMatchObject({
      section: "skin",
      arrayPath: "wounds",
      rowField: "location",
      newValue: "Sacral/coccyx area",
      existingRowIndex: 0,
      existingValue: "Coccyx",
      concept_code: "SKIN_WOUND_PRESENT",
    });
  });

  it("still auto-adds a genuinely distinct wound location with zero word overlap -- no review needed", () => {
    const { formData, woundReviewItems } = applyStructuredFindings(
      { skin: { wounds: [{ location: "Coccyx", stage: "Stage 2" }] } },
      [findingOf({ concept_code: "SKIN_WOUND_PRESENT", value: "right heel", source_excerpt: "right heel pressure injury" })]
    );

    expect(woundReviewItems).toEqual([]);
    expect(formData.skin.wounds).toHaveLength(2);
    expect(formData.skin.wounds.map((w) => w.location)).toContain("right heel");
  });

  it("applyAllNonConflicting still surfaces the ambiguous wound match for RN review even when the signal's OTHER write (e.g. skinConditionsPresent) applies cleanly -- same partial-success pattern as field conflicts", () => {
    const signals = [
      {
        id: "sig-wound-1",
        structured_findings: [
          findingOf({ concept_code: "SKIN_WOUND_PRESENT", value: "Sacral/coccyx area", source_excerpt: "wound near sacrum/coccyx" }),
        ],
      },
    ];
    const result = applyAllNonConflicting(
      { skin: { wounds: [{ location: "Coccyx", stage: "Stage 2" }] } },
      signals
    );

    // skinConditionsPresent legitimately applies (independent, safe write) --
    // so the signal is "applied", exactly like a partially-conflicting
    // signal already is. What matters is that the AMBIGUOUS WOUND ROW
    // ITSELF was never silently written either as a duplicate row or a
    // merge -- it's still queued for an explicit RN decision.
    expect(result.appliedSignalIds).toEqual(["sig-wound-1"]);
    expect(result.skippedWoundReviewItems).toHaveLength(1);
    expect(result.skippedWoundReviewItems[0].signal_id).toBe("sig-wound-1");
    expect(result.skippedWoundReviewItems[0]).toMatchObject({ existingValue: "Coccyx", newValue: "Sacral/coccyx area" });
    // No silent write happened to the wounds array itself.
    expect(result.formData.skin.wounds).toHaveLength(1);
  });
});

describe("resolveWoundReview (RN actions: New Wound / Merge Existing / Reject / Modify)", () => {
  function woundItemOf(overrides = {}) {
    return {
      section: "skin",
      arrayPath: "wounds",
      rowField: "location",
      newRow: { location: "Sacral/coccyx area", stage: "Stage 2", dressing: "Foam" },
      newValue: "Sacral/coccyx area",
      existingRowIndex: 0,
      existingValue: "Coccyx",
      concept_code: "SKIN_WOUND_PRESENT",
      ...overrides,
    };
  }

  it('"new_wound": adds the candidate as its own independent new row, leaving the existing row untouched', () => {
    const formData = { skin: { wounds: [{ location: "Coccyx", stage: "Stage 2" }] } };
    const result = resolveWoundReview(formData, woundItemOf(), "new_wound");

    expect(result.noop).toBe(false);
    expect(result.formData.skin.wounds).toHaveLength(2);
    expect(result.formData.skin.wounds[0]).toEqual({ location: "Coccyx", stage: "Stage 2" }); // untouched
    expect(result.formData.skin.wounds[1]).toMatchObject({ location: "Sacral/coccyx area", dressing: "Foam" });
  });

  it('"merge_existing": enriches blank fields on the existing row, never overwrites already-documented fields or its validated location', () => {
    const formData = { skin: { wounds: [{ location: "Coccyx", stage: "Stage 2", dressing: "" }] } };
    const result = resolveWoundReview(formData, woundItemOf(), "merge_existing");

    expect(result.noop).toBe(false);
    expect(result.formData.skin.wounds).toHaveLength(1); // no new row
    expect(result.formData.skin.wounds[0].location).toBe("Coccyx"); // validated location preserved, not overwritten
    expect(result.formData.skin.wounds[0].stage).toBe("Stage 2"); // already documented -- untouched
    expect(result.formData.skin.wounds[0].dressing).toBe("Foam"); // blank field enriched from candidate
  });

  it('"merge_existing" never overwrites a non-blank field even if the candidate has a different value for it', () => {
    const formData = { skin: { wounds: [{ location: "Coccyx", stage: "Stage 3", dressing: "Hydrocolloid" }] } };
    const result = resolveWoundReview(formData, woundItemOf(), "merge_existing");

    expect(result.formData.skin.wounds[0].stage).toBe("Stage 3");
    expect(result.formData.skin.wounds[0].dressing).toBe("Hydrocolloid");
  });

  it('"reject": discards the candidate entirely -- no new row, no merge, form untouched', () => {
    const formData = { skin: { wounds: [{ location: "Coccyx", stage: "Stage 2" }] } };
    const result = resolveWoundReview(formData, woundItemOf(), "reject");

    expect(result.noop).toBe(true);
    expect(result.formData).toBe(formData); // literally unchanged
    expect(result.formData.skin.wounds).toHaveLength(1);
  });

  it('"modify": adds a NEW row using the RN-corrected location, distinct from both the existing row and the raw candidate wording', () => {
    const formData = { skin: { wounds: [{ location: "Coccyx", stage: "Stage 2" }] } };
    const result = resolveWoundReview(formData, woundItemOf(), "modify", "Sacrum, adjacent to coccyx");

    expect(result.formData.skin.wounds).toHaveLength(2);
    expect(result.formData.skin.wounds[0].location).toBe("Coccyx"); // untouched
    expect(result.formData.skin.wounds[1]).toMatchObject({ location: "Sacrum, adjacent to coccyx", dressing: "Foam" });
  });

  it("returns null for an unrecognized action", () => {
    const formData = { skin: { wounds: [{ location: "Coccyx" }] } };
    expect(resolveWoundReview(formData, woundItemOf(), "bogus")).toBeNull();
  });
});
