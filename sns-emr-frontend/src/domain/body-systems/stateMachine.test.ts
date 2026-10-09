import { describe, expect, it } from "vitest";

import type { AssessmentSituation, SystemReviewState } from "./types";
import {
  REVIEW_STATE_TRANSITIONS,
  canTransition,
  getMissingSituationRequirements,
  getSituationRequirements,
  nextReviewStateAfterReview,
  openCorrection,
  reopenReviewed,
  unableToAssessIsFullyDocumented,
} from "./stateMachine";

const ALL_STATES: SystemReviewState[] = ["not_reviewed", "in_progress", "reviewed", "reviewed_with_exception"];
const ALL_SITUATIONS: AssessmentSituation[] = [
  "no_current_concern",
  "stable_existing",
  "new_or_worsening",
  "unable_to_assess",
];

describe("Body Systems — review-state transition graph", () => {
  it("allows exactly the transitions defined in the specification graph", () => {
    const allowed = new Set(REVIEW_STATE_TRANSITIONS.map((edge) => `${edge.from}->${edge.to}`));
    for (const from of ALL_STATES) {
      for (const to of ALL_STATES) {
        expect(canTransition(from, to)).toBe(allowed.has(`${from}->${to}`));
      }
    }
  });

  it("allows not_reviewed -> in_progress", () => {
    expect(canTransition("not_reviewed", "in_progress")).toBe(true);
  });

  it("rejects not_reviewed -> reviewed directly (must pass through in_progress)", () => {
    expect(canTransition("not_reviewed", "reviewed")).toBe(false);
  });

  it("rejects not_reviewed -> reviewed_with_exception directly", () => {
    expect(canTransition("not_reviewed", "reviewed_with_exception")).toBe(false);
  });

  it("allows reviewed -> in_progress only as an explicit reopen, distinct from correction_opened", () => {
    expect(canTransition("reviewed", "in_progress")).toBe(true);
    const edge = REVIEW_STATE_TRANSITIONS.find((entry) => entry.from === "reviewed" && entry.to === "in_progress");
    expect(edge?.trigger).toBe("explicit_reopen");
    expect(reopenReviewed("reviewed")).toBe("in_progress");
    expect(() => reopenReviewed("in_progress")).toThrow();
    expect(() => reopenReviewed("not_reviewed")).toThrow();
  });

  it("opens a correction only from reviewed_with_exception", () => {
    expect(openCorrection("reviewed_with_exception")).toBe("in_progress");
    expect(() => openCorrection("reviewed")).toThrow();
    expect(() => openCorrection("not_reviewed")).toThrow();
    expect(() => openCorrection("in_progress")).toThrow();
  });

  it("computes the next review state from current evidence/exception state", () => {
    expect(nextReviewStateAfterReview("in_progress", false)).toBe("reviewed");
    expect(nextReviewStateAfterReview("in_progress", true)).toBe("reviewed_with_exception");
    expect(nextReviewStateAfterReview("reviewed_with_exception", false)).toBe("reviewed");
    expect(nextReviewStateAfterReview("reviewed_with_exception", true)).toBe("reviewed_with_exception");
    expect(nextReviewStateAfterReview("not_reviewed", false)).toBe("in_progress");
  });

  it("never lets the ordinary completion function reopen a reviewed system back to in_progress", () => {
    // nextReviewStateAfterReview only ever returns "reviewed" or
    // "reviewed_with_exception" once already past in_progress — it has no
    // code path back to "in_progress" for an already-reviewed system.
    expect(nextReviewStateAfterReview("reviewed", false)).not.toBe("in_progress");
    expect(nextReviewStateAfterReview("reviewed", true)).not.toBe("in_progress");
  });
});

describe("Body Systems — concept separation", () => {
  it("keeps assessment situations and system review states as disjoint string sets", () => {
    const situationValues = new Set<string>(ALL_SITUATIONS);
    const stateValues = new Set<string>(ALL_STATES);
    for (const situation of situationValues) {
      expect(stateValues.has(situation)).toBe(false);
    }
  });

  it("does not let choosing a situation, by itself, change the review state", () => {
    // Situation requirements are evaluated independently of review-state
    // transitions — getSituationRequirements/getMissingSituationRequirements
    // never return or imply a SystemReviewState value.
    for (const situation of ALL_SITUATIONS) {
      for (const requirement of getSituationRequirements(situation)) {
        expect((ALL_STATES as string[]).includes(requirement)).toBe(false);
      }
    }
  });
});

describe("Body Systems — situation branches", () => {
  it("defines requirements for all four assessment situations", () => {
    expect(getSituationRequirements("no_current_concern").length).toBeGreaterThan(0);
    expect(getSituationRequirements("stable_existing").length).toBeGreaterThan(0);
    expect(getSituationRequirements("new_or_worsening").length).toBeGreaterThan(0);
    expect(getSituationRequirements("unable_to_assess").length).toBeGreaterThan(0);
  });

  it("treats historical evidence alone as insufficient for stable_existing (requires current_confirmation too)", () => {
    const missing = getMissingSituationRequirements("stable_existing", ["dated_prior_reference"]);
    expect(missing).toContain("current_confirmation");
  });

  it("never marks unable_to_assess complete without every required key, even if most are present", () => {
    const almostAll = ["scope", "reason", "assessed_portion_if_any", "follow_up_responsibility"];
    expect(unableToAssessIsFullyDocumented(almostAll)).toBe(false);
    const all = [...almostAll, "timing_or_contingency"];
    expect(unableToAssessIsFullyDocumented(all)).toBe(true);
  });

  it("throws for an unknown situation rather than silently defaulting", () => {
    // @ts-expect-error intentionally invalid situation to prove no silent fallback
    expect(() => getSituationRequirements("not_a_real_situation")).toThrow();
  });
});
