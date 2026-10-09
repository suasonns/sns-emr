import { describe, it, expect } from "vitest";
import {
  computeDiagnosisVerificationChecklist,
  isContributingConditionIncomplete,
  summarizeContributingConditions,
  findExactDuplicateContributingCondition,
  findProbableDuplicateContributingConditions,
  findContributingConditionCrossReferences,
  CONTRIBUTING_CONDITION_STATUS_OPTIONS,
} from "./diagnosisLogic";

// Disease & LCD Workflow Specification, Phase 1 / Option A -- Contributing
// Conditions. These tests cover the pure derivation/validation helpers
// only (duplicate detection, incompleteness, cross-reference notices,
// verification checklist); they intentionally do not touch Primary
// Diagnosis / Secondary Diagnoses / HOPE Comorbidities behavior, which is
// unchanged and out of scope for this feature.

function makeCondition(overrides = {}) {
  return {
    id: "c1",
    icdCode: "C50.911",
    icdDescription: "Malignant neoplasm of breast",
    contributionStatus: "",
    clinicalRationale: "",
    sourceType: "CLINICIAN_ENTERED",
    active: true,
    ...overrides,
  };
}

describe("isContributingConditionIncomplete", () => {
  it("is incomplete with no diagnosis selected", () => {
    expect(isContributingConditionIncomplete(makeCondition({ icdCode: "", icdDescription: "" }))).toBe(true);
  });

  it("is incomplete with no contribution status", () => {
    expect(isContributingConditionIncomplete(makeCondition({ contributionStatus: "" }))).toBe(true);
  });

  it("requires a rationale when status is CONTRIBUTES_TO_TERMINAL_PROGNOSIS", () => {
    expect(
      isContributingConditionIncomplete(
        makeCondition({ contributionStatus: "CONTRIBUTES_TO_TERMINAL_PROGNOSIS", clinicalRationale: "" }),
      ),
    ).toBe(true);
    expect(
      isContributingConditionIncomplete(
        makeCondition({ contributionStatus: "CONTRIBUTES_TO_TERMINAL_PROGNOSIS", clinicalRationale: "Documented in H&P." }),
      ),
    ).toBe(false);
  });

  it("requires a rationale when status is CONTRIBUTES_TO_CLINICAL_BURDEN", () => {
    expect(
      isContributingConditionIncomplete(
        makeCondition({ contributionStatus: "CONTRIBUTES_TO_CLINICAL_BURDEN", clinicalRationale: "   " }),
      ),
    ).toBe(true);
  });

  it("does NOT require a rationale for the two non-rationale statuses", () => {
    expect(
      isContributingConditionIncomplete(
        makeCondition({ contributionStatus: "DOES_NOT_MATERIALLY_CONTRIBUTE", clinicalRationale: "" }),
      ),
    ).toBe(false);
    expect(
      isContributingConditionIncomplete(
        makeCondition({ contributionStatus: "UNABLE_TO_DETERMINE", clinicalRationale: "" }),
      ),
    ).toBe(false);
  });
});

describe("summarizeContributingConditions", () => {
  it("returns an empty list when there are none (a valid state)", () => {
    expect(summarizeContributingConditions({ contributingConditions: [] })).toEqual([]);
    expect(summarizeContributingConditions({})).toEqual([]);
  });

  it("excludes soft-removed (active: false) rows", () => {
    const data = {
      contributingConditions: [
        makeCondition({ id: "a", contributionStatus: "UNABLE_TO_DETERMINE" }),
        makeCondition({ id: "b", active: false }),
      ],
    };
    expect(summarizeContributingConditions(data)).toHaveLength(1);
  });

  it("appends the status short label when present", () => {
    const data = { contributingConditions: [makeCondition({ contributionStatus: "CONTRIBUTES_TO_CLINICAL_BURDEN" })] };
    const [summary] = summarizeContributingConditions(data);
    expect(summary).toContain("Clinical Burden");
  });
});

describe("findExactDuplicateContributingCondition", () => {
  const conditions = [
    makeCondition({ id: "a", icdCode: "E11.9" }),
    makeCondition({ id: "b", icdCode: "I50.9" }),
  ];

  it("blocks an exact ICD-10 match (case/whitespace-insensitive)", () => {
    expect(findExactDuplicateContributingCondition(conditions, " e11.9 ")?.id).toBe("a");
  });

  it("excludes the row currently being edited", () => {
    expect(findExactDuplicateContributingCondition(conditions, "E11.9", "a")).toBeNull();
  });

  it("ignores soft-removed rows", () => {
    const withRemoved = [...conditions, makeCondition({ id: "c", icdCode: "J44.9", active: false })];
    expect(findExactDuplicateContributingCondition(withRemoved, "J44.9")).toBeNull();
  });

  it("returns null when there is no match", () => {
    expect(findExactDuplicateContributingCondition(conditions, "C50.911")).toBeNull();
  });
});

describe("findProbableDuplicateContributingConditions", () => {
  it("warns (non-blocking) when two different codes share a HOPE category", () => {
    // E08.9 and E10.9 both categorize as diabetesMellitus but are distinct codes.
    const conditions = [makeCondition({ id: "a", icdCode: "E08.9" })];
    const matches = findProbableDuplicateContributingConditions(conditions, "E10.9");
    expect(matches.map((c) => c.id)).toEqual(["a"]);
  });

  it("returns an empty list for a code with no HOPE category mapping", () => {
    const conditions = [makeCondition({ id: "a", icdCode: "Z99.9" })];
    expect(findProbableDuplicateContributingConditions(conditions, "Z00.0")).toEqual([]);
  });
});

describe("findContributingConditionCrossReferences", () => {
  it("flags overlap with an existing Secondary Diagnosis", () => {
    const data = { secondaryDiagnoses: [{ icd10: "I50.9", description: "Heart failure" }] };
    expect(findContributingConditionCrossReferences(data, "i50.9").inSecondaryDiagnoses).toBe(true);
  });

  it("flags overlap with a checked HOPE comorbidity category", () => {
    const data = { hopeComorbidities: { heartFailure: true } };
    const result = findContributingConditionCrossReferences(data, "I50.9");
    expect(result.hopeCategory?.key).toBe("heartFailure");
    expect(result.hopeCategoryChecked).toBe(true);
  });

  it("never flags overlap when the HOPE category is not checked", () => {
    const result = findContributingConditionCrossReferences({}, "I50.9");
    expect(result.hopeCategoryChecked).toBe(false);
  });
});

describe("computeDiagnosisVerificationChecklist — Contributing Conditions item", () => {
  it("is met when there are zero contributing conditions (valid state)", () => {
    const checklist = computeDiagnosisVerificationChecklist({ contributingConditions: [] });
    const item = checklist.find((c) => c.label === "Contributing conditions reviewed");
    expect(item.met).toBe(true);
  });

  it("is unmet when an active condition is incomplete", () => {
    const checklist = computeDiagnosisVerificationChecklist({
      contributingConditions: [makeCondition({ contributionStatus: "" })],
    });
    expect(checklist.find((c) => c.label === "Contributing conditions reviewed").met).toBe(false);
  });

  it("ignores soft-removed incomplete rows", () => {
    const checklist = computeDiagnosisVerificationChecklist({
      contributingConditions: [makeCondition({ contributionStatus: "", active: false })],
    });
    expect(checklist.find((c) => c.label === "Contributing conditions reviewed").met).toBe(true);
  });

  it("is met when every active condition is fully documented", () => {
    const checklist = computeDiagnosisVerificationChecklist({
      contributingConditions: [
        makeCondition({ contributionStatus: "UNABLE_TO_DETERMINE" }),
        makeCondition({ id: "c2", contributionStatus: "CONTRIBUTES_TO_TERMINAL_PROGNOSIS", clinicalRationale: "See H&P." }),
      ],
    });
    expect(checklist.find((c) => c.label === "Contributing conditions reviewed").met).toBe(true);
  });

  it("supports a large (50+) condition list without error", () => {
    const many = Array.from({ length: 60 }, (_, i) => makeCondition({ id: `c${i}`, contributionStatus: "UNABLE_TO_DETERMINE" }));
    const checklist = computeDiagnosisVerificationChecklist({ contributingConditions: many });
    expect(checklist.find((c) => c.label === "Contributing conditions reviewed").met).toBe(true);
    expect(summarizeContributingConditions({ contributingConditions: many })).toHaveLength(60);
  });
});

describe("CONTRIBUTING_CONDITION_STATUS_OPTIONS", () => {
  it("exposes exactly the four controlled statuses", () => {
    expect(CONTRIBUTING_CONDITION_STATUS_OPTIONS.map((o) => o.value)).toEqual([
      "CONTRIBUTES_TO_TERMINAL_PROGNOSIS",
      "CONTRIBUTES_TO_CLINICAL_BURDEN",
      "DOES_NOT_MATERIALLY_CONTRIBUTE",
      "UNABLE_TO_DETERMINE",
    ]);
  });
});
