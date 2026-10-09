import { describe, expect, it } from "vitest";

import {
  BODY_SYSTEMS,
  BODY_SYSTEM_LABELS,
  type BodySystemCode,
} from "./types";
import {
  OWNERSHIP_REGISTRY,
  bodyDiagramMarkerDoesNotCompleteWoundRecord,
  bradenMobilitySubscoreDoesNotCompleteMusculoskeletalReview,
  bradenNutritionSubscoreDoesNotCompleteNutritionReview,
  bradenSubscoresDoNotCompleteSystemReview,
  canReassess,
  canReassessEdemaIn,
  canReference,
  edemaIsNotOwnedByIntegumentary,
  findDuplicateOwnershipFactKeys,
  historicalEvidenceDoesNotCompleteCurrentReview,
  aiSuggestionsDoNotMarkSystemReviewed,
  resolveFactOwner,
} from "./ownership";

describe("Body Systems — canonical system list", () => {
  it("contains exactly ten unique systems in fixed order", () => {
    expect(BODY_SYSTEMS.length).toBe(10);
    expect(new Set(BODY_SYSTEMS).size).toBe(10);
    expect(BODY_SYSTEMS).toEqual([
      "neurological",
      "respiratory",
      "cardiovascular",
      "nutrition",
      "gastrointestinal",
      "genitourinary",
      "musculoskeletal",
      "integumentary",
      "infection_immunological",
      "endocrine",
    ]);
  });

  it("never includes legacy identifiers 'skin' or 'infection' as canonical systems", () => {
    expect((BODY_SYSTEMS as readonly string[]).includes("skin")).toBe(false);
    expect((BODY_SYSTEMS as readonly string[]).includes("infection")).toBe(false);
  });

  it("gives every canonical system a display label distinct from its identifier", () => {
    expect(Object.keys(BODY_SYSTEM_LABELS).sort()).toEqual([...BODY_SYSTEMS].sort());
    expect(BODY_SYSTEM_LABELS.integumentary).toBe("Integumentary");
    expect(BODY_SYSTEM_LABELS.infection_immunological).toBe("Infection / Immunological");
  });
});

describe("Body Systems — ownership registry", () => {
  it("has no fact key owned by more than one system", () => {
    expect(findDuplicateOwnershipFactKeys()).toEqual([]);
  });

  it("gives every registered fact key exactly one owner", () => {
    const seen = new Map<string, BodySystemCode>();
    for (const rule of OWNERSHIP_REGISTRY) {
      for (const factKey of rule.factKeys) {
        expect(seen.has(factKey)).toBe(false);
        seen.set(factKey, rule.owner);
      }
    }
    expect(seen.size).toBeGreaterThan(0);
  });

  it("confirms the minimum required ownership mappings from the pre-commit audit", () => {
    const expected: Array<[string, BodySystemCode]> = [
      ["orientation", "neurological"],
      ["cognition", "neurological"],
      ["dyspnea", "respiratory"],
      ["oxygen_use", "respiratory"],
      ["edema", "cardiovascular"],
      ["intake", "nutrition"],
      ["weight", "nutrition"],
      ["bowel_status", "gastrointestinal"],
      ["urinary_status", "genitourinary"],
      ["gait", "musculoskeletal"],
      ["balance", "musculoskeletal"],
      ["transfers", "musculoskeletal"],
      ["mobility", "musculoskeletal"],
      ["skin_integrity", "integumentary"],
      ["wounds", "integumentary"],
      ["pressure_injuries", "integumentary"],
      ["body_diagram_wound_markers", "integumentary"],
      ["braden", "integumentary"],
      ["active_infection_status", "infection_immunological"],
      ["diabetes", "endocrine"],
    ];
    for (const [factKey, owner] of expected) {
      expect(resolveFactOwner(factKey)).toBe(owner);
    }
  });

  it("resolves edema to cardiovascular only", () => {
    expect(resolveFactOwner("edema")).toBe("cardiovascular");
    expect(canReassess("cardiovascular", "edema")).toBe(true);
    expect(canReassess("integumentary", "edema")).toBe(false);
    expect(canReassessEdemaIn("cardiovascular")).toBe(true);
    expect(canReassessEdemaIn("integumentary")).toBe(false);
    expect(edemaIsNotOwnedByIntegumentary()).toBe(true);
  });

  it("resolves wounds, pressure injuries, and Braden to integumentary only", () => {
    for (const factKey of ["wounds", "pressure_injuries", "braden", "skin_integrity"]) {
      expect(resolveFactOwner(factKey)).toBe("integumentary");
      expect(canReassess("integumentary", factKey)).toBe(true);
      expect(canReassess("musculoskeletal", factKey)).toBe(false);
      expect(canReassess("nutrition", factKey)).toBe(false);
    }
  });

  it("resolves active infection to infection_immunological only", () => {
    expect(resolveFactOwner("active_infection_status")).toBe("infection_immunological");
    expect(canReassess("infection_immunological", "active_infection_status")).toBe(true);
    expect(canReassess("neurological", "active_infection_status")).toBe(false);
  });

  it("allows referencing a fact outside its owner but not reassessing it", () => {
    expect(canReference("integumentary", "edema")).toBe(true);
    expect(canReassess("integumentary", "edema")).toBe(false);
  });

  it("returns undefined for unregistered fact keys", () => {
    expect(resolveFactOwner("not_a_real_fact_key")).toBeUndefined();
    expect(canReference("neurological", "not_a_real_fact_key")).toBe(false);
  });
});

describe("Body Systems — non-duplication assertions", () => {
  it("never lets Braden subscores complete a system review", () => {
    expect(bradenSubscoresDoNotCompleteSystemReview()).toBe(true);
    expect(bradenMobilitySubscoreDoesNotCompleteMusculoskeletalReview()).toBe(true);
    expect(bradenNutritionSubscoreDoesNotCompleteNutritionReview()).toBe(true);
  });

  it("never lets a body-diagram marker alone complete a wound record", () => {
    expect(bodyDiagramMarkerDoesNotCompleteWoundRecord()).toBe(true);
  });

  it("never lets historical evidence mark a system reviewed", () => {
    expect(historicalEvidenceDoesNotCompleteCurrentReview()).toBe(true);
  });

  it("never lets AI suggestions mark a system reviewed", () => {
    expect(aiSuggestionsDoNotMarkSystemReviewed()).toBe(true);
  });
});
