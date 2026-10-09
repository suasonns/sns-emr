import { describe, expect, it } from "vitest";

import {
  BODY_SYSTEMS,
  BODY_SYSTEM_LABELS,
  type BodySystemCode,
} from "./types";
import {
  OWNERSHIP_REGISTRY,
  activeInfectionSepsisDoesNotRewriteHopeSepsisHistory,
  allergiesAreNotOwnedByInfection,
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
  hopeSepsisHistoryDoesNotDeriveActiveInfectionSepsis,
  aiSuggestionsDoNotMarkSystemReviewed,
  resolveFactOwner,
  respiratoryFindingsAreNotOwnedByInfection,
  skinWoundReviewDoesNotCompleteBradenAssessment,
  systemNotesAreOptional,
  systemNotesDoNotSatisfyStructuredFindings,
  temperatureIsNotOwnedByInfection,
  urinaryFindingsAreNotOwnedByInfection,
  woundFindingsAreNotOwnedByInfection,
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
      ["infection_status", "infection_immunological"],
      ["infection_type", "infection_immunological"],
      ["infection_findings", "infection_immunological"],
      ["organism_information", "infection_immunological"],
      ["antimicrobial_treatment", "infection_immunological"],
      ["precautions_isolation", "infection_immunological"],
      ["immunosuppression_status", "infection_immunological"],
      ["infection_history", "infection_immunological"],
      ["infection_response_followup", "infection_immunological"],
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

  it("resolves active infection status to infection_immunological only, and every discrete Infection fact to infection_immunological only", () => {
    const infectionFactKeys = [
      "infection_status",
      "infection_type",
      "infection_findings",
      "organism_information",
      "antimicrobial_treatment",
      "precautions_isolation",
      "immunosuppression_status",
      "infection_history",
      "infection_response_followup",
    ];
    for (const factKey of infectionFactKeys) {
      expect(resolveFactOwner(factKey)).toBe("infection_immunological");
      expect(canReassess("infection_immunological", factKey)).toBe(true);
      expect(canReassess("neurological", factKey)).toBe(false);
      expect(canReassess("integumentary", factKey)).toBe(false);
    }
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

  it("never lets skin/wound review complete the Braden assessment (Integumentary owns both, so the guard runs in both directions)", () => {
    expect(skinWoundReviewDoesNotCompleteBradenAssessment()).toBe(true);
  });

  it("never lets historical evidence mark a system reviewed", () => {
    expect(historicalEvidenceDoesNotCompleteCurrentReview()).toBe(true);
  });

  it("never lets AI suggestions mark a system reviewed", () => {
    expect(aiSuggestionsDoNotMarkSystemReviewed()).toBe(true);
  });
});

describe("Body Systems — Infection / Immunological non-duplication rules", () => {
  it("never lets temperature resolve to infection_immunological (Vitals-owned, outside the registry)", () => {
    expect(resolveFactOwner("temperature")).toBeUndefined();
    expect(temperatureIsNotOwnedByInfection()).toBe(true);
    expect(canReassess("infection_immunological", "temperature")).toBe(false);
  });

  it("never lets wound/skin findings resolve to infection_immunological — they remain Integumentary-owned", () => {
    expect(woundFindingsAreNotOwnedByInfection()).toBe(true);
    expect(resolveFactOwner("wounds")).toBe("integumentary");
    expect(canReference("infection_immunological", "wounds")).toBe(true);
    expect(canReassess("infection_immunological", "wounds")).toBe(false);
  });

  it("never lets urinary findings resolve to infection_immunological — they remain Genitourinary-owned", () => {
    expect(urinaryFindingsAreNotOwnedByInfection()).toBe(true);
    expect(resolveFactOwner("urinary_status")).toBe("genitourinary");
    expect(canReference("infection_immunological", "urinary_status")).toBe(true);
    expect(canReassess("infection_immunological", "urinary_status")).toBe(false);
  });

  it("never lets respiratory findings resolve to infection_immunological — they remain Respiratory-owned", () => {
    expect(respiratoryFindingsAreNotOwnedByInfection()).toBe(true);
    expect(resolveFactOwner("dyspnea")).toBe("respiratory");
    expect(canReference("infection_immunological", "dyspnea")).toBe(true);
    expect(canReassess("infection_immunological", "dyspnea")).toBe(false);
  });

  it("keeps HOPE/comorbidity sepsis history and current active-infection sepsis independent in both directions", () => {
    expect(hopeSepsisHistoryDoesNotDeriveActiveInfectionSepsis()).toBe(true);
    expect(activeInfectionSepsisDoesNotRewriteHopeSepsisHistory()).toBe(true);
  });

  it("never lets allergy data resolve to infection_immunological ownership", () => {
    expect(allergiesAreNotOwnedByInfection()).toBe(true);
  });

  it("never lets RN Notes satisfy a structured Infection finding, and treats blank notes as valid", () => {
    expect(systemNotesDoNotSatisfyStructuredFindings()).toBe(true);
    expect(systemNotesAreOptional(undefined)).toBe(true);
    expect(systemNotesAreOptional("")).toBe(true);
    expect(systemNotesAreOptional("Context from caregiver report.")).toBe(true);
  });
});
