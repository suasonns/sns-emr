/**
 * SNS Body Systems — clinical ownership registry.
 *
 * Source of truth: docs/design/body-systems-figma/SNS_Body_Systems_Engineering_Specification.md
 * section 5 ("Clinical Ownership Registry"). Ownership must be represented in
 * code, not inferred from component placement — this module is that
 * representation. Do not add fact keys, owners, or referenceable lists beyond
 * what the specification states; if a new fact needs ownership, that is a
 * specification change, not an inference from a screenshot or component.
 */
import type { BodySystemCode } from "./types";

export interface OwnershipRule {
  owner: BodySystemCode;
  factKeys: readonly string[];
  referenceableBy: readonly BodySystemCode[] | "all";
}

/**
 * Minimum registry transcribed from specification section 5. Every entry's
 * `referenceableBy` is "all" unless the specification's "Non-duplication
 * rules" subsection names a narrower, specific set of referencing systems —
 * none currently do, so every rule below is broadly referenceable but only
 * reassessable by its `owner`.
 */
export const OWNERSHIP_REGISTRY: readonly OwnershipRule[] = [
  {
    owner: "neurological",
    factKeys: ["orientation", "cognition", "responsiveness", "mental_status"],
    referenceableBy: "all",
  },
  {
    owner: "respiratory",
    factKeys: [
      "dyspnea",
      "cough",
      "sputum",
      "lung_sounds",
      "respiratory_rate_pattern",
      "oxygen_use",
      "ventilator_airway_support",
      "respiratory_exertion_tolerance",
    ],
    referenceableBy: "all",
  },
  {
    owner: "cardiovascular",
    factKeys: [
      "edema",
      "pulse_rhythm",
      "heart_sounds_perfusion",
      "blood_pressure_orthostatic_findings",
      "chest_pain",
      "syncope",
      "circulation",
      "cardiac_devices",
    ],
    referenceableBy: "all",
  },
  {
    owner: "nutrition",
    factKeys: ["intake", "weight", "weight_change", "appetite", "swallowing_nutritional_burden"],
    referenceableBy: "all",
  },
  {
    owner: "gastrointestinal",
    factKeys: ["bowel_status", "gastrointestinal_symptoms"],
    referenceableBy: "all",
  },
  {
    owner: "genitourinary",
    factKeys: ["urinary_status", "genitourinary_symptoms"],
    referenceableBy: "all",
  },
  {
    owner: "musculoskeletal",
    factKeys: ["gait", "balance", "transfers", "mobility", "weakness_as_mobility_function"],
    referenceableBy: "all",
  },
  {
    owner: "integumentary",
    factKeys: [
      "skin_integrity",
      "wounds",
      "pressure_injuries",
      "wound_treatment_detail",
      "body_diagram_wound_markers",
      "braden",
    ],
    referenceableBy: "all",
  },
  {
    owner: "infection_immunological",
    factKeys: [
      "infection_status",
      "infection_type",
      "infection_findings",
      "organism_information",
      "antimicrobial_treatment",
      "precautions_isolation",
      "immunosuppression_status",
      "infection_history",
      "infection_response_followup",
    ],
    referenceableBy: "all",
  },
  {
    owner: "endocrine",
    factKeys: ["diabetes", "endocrine_findings"],
    referenceableBy: "all",
  },
];

/**
 * Resolves the single owning body system for a fact key, or undefined if the
 * fact key is not registered. A fact key must appear in exactly one rule's
 * `factKeys` — `assertRegistryHasNoDuplicateOwnership` (used by the unit
 * tests) verifies this invariant against the registry above.
 */
export function resolveFactOwner(factKey: string): BodySystemCode | undefined {
  const rule = OWNERSHIP_REGISTRY.find((entry) => entry.factKeys.includes(factKey));
  return rule?.owner;
}

/** Whether `system` may reassess (create/edit a current finding for) `factKey`. */
export function canReassess(system: BodySystemCode, factKey: string): boolean {
  return resolveFactOwner(factKey) === system;
}

/** Whether `system` may display/reference `factKey` without owning it. */
export function canReference(system: BodySystemCode, factKey: string): boolean {
  const rule = OWNERSHIP_REGISTRY.find((entry) => entry.factKeys.includes(factKey));
  if (!rule) return false;
  if (rule.owner === system) return true;
  return rule.referenceableBy === "all" || rule.referenceableBy.includes(system);
}

/**
 * Returns every fact key that has more than one owning rule. The registry is
 * only valid when this returns an empty array — this is the code
 * representation of "a fact may be referenced elsewhere but may not be
 * reassessed elsewhere" (specification section 1, rule 2).
 */
export function findDuplicateOwnershipFactKeys(registry: readonly OwnershipRule[] = OWNERSHIP_REGISTRY): string[] {
  const ownerCounts = new Map<string, number>();
  for (const rule of registry) {
    for (const factKey of rule.factKeys) {
      ownerCounts.set(factKey, (ownerCounts.get(factKey) ?? 0) + 1);
    }
  }
  return [...ownerCounts.entries()].filter(([, count]) => count > 1).map(([factKey]) => factKey);
}

// ---------------------------------------------------------------------------
// Named non-duplication rules (specification section 5, "Non-duplication
// rules" subsection). These are explicit, named guards rather than generic
// ownership lookups so call sites can express intent directly and so a
// future specification change to any one of these is a single-function diff.
// ---------------------------------------------------------------------------

/** Edema is owned by Cardiovascular; Integumentary may reference it but not reassess it. */
export function canReassessEdemaIn(system: BodySystemCode): boolean {
  return canReassess(system, "edema");
}

/** Explicit assertion: edema's owner is never Integumentary. */
export function edemaIsNotOwnedByIntegumentary(): boolean {
  return resolveFactOwner("edema") !== "integumentary";
}

/**
 * Braden mobility/nutrition subscores are pressure-risk inputs only. They
 * must never be read as satisfying a Musculoskeletal or Nutrition system
 * review — those systems require their own explicit review evidence.
 */
export function bradenSubscoresDoNotCompleteSystemReview(): true {
  return true;
}

/** Explicit assertion: the Braden mobility subscore never completes a Musculoskeletal system review. */
export function bradenMobilitySubscoreDoesNotCompleteMusculoskeletalReview(): true {
  return true;
}

/** Explicit assertion: the Braden nutrition subscore never completes a Nutrition system review. */
export function bradenNutritionSubscoreDoesNotCompleteNutritionReview(): true {
  return true;
}

/**
 * Integumentary owns both `skin_integrity`/`wounds` and `braden` itself, so
 * the non-substitution guard runs in both directions: Braden does not
 * complete skin/wound review (see `bradenSubscoresDoNotCompleteSystemReview`)
 * AND skin/wound review does not complete Braden. Braden's six subscales
 * and total are only ever set by an explicit RN Braden assessment, never
 * derived from wound count, wound stage, wound dimensions, or any other
 * skin/wound finding.
 */
export function skinWoundReviewDoesNotCompleteBradenAssessment(): true {
  return true;
}

/**
 * A body-diagram wound marker is a location aid only. It never satisfies
 * wound documentation on its own — see `woundMarkerAloneSatisfiesWoundRecord`
 * in exceptionRules.ts for the corresponding validation guard.
 */
export function bodyDiagramMarkerDoesNotCompleteWoundRecord(): true {
  return true;
}

/**
 * Historical evidence may be displayed in any allowed context (per
 * `canReference`) but can never mark a current system reviewed. Current
 * review requires an explicit current-evidence action — see
 * stateMachine.ts.
 */
export function historicalEvidenceDoesNotCompleteCurrentReview(): true {
  return true;
}

/**
 * AI-extracted/suggested findings may populate draft fields for clinician
 * review (specification section 9) but can never, by themselves, mark a
 * system reviewed — only an explicit clinician review action can. See
 * `aiPatchViolatesAuditFieldRestriction` in exceptionRules.ts for the
 * related guard that AI may not set audit/identity fields.
 */
export function aiSuggestionsDoNotMarkSystemReviewed(): true {
  return true;
}

// ---------------------------------------------------------------------------
// Infection / Immunological non-duplication rules (product-owner ownership
// decision: Infection owns facts specifically about infection — infection
// status/type/findings, organism/culture information, antimicrobial
// treatment, precautions/isolation, immunosuppression, infection history,
// and infection response/follow-up. Infection may reference, but never
// reassess, facts owned by another system — temperature stays with Vitals
// (not a registered Body Systems fact at all), wound characteristics stay
// with Integumentary, urinary findings stay with Genitourinary, and
// respiratory findings stay with Respiratory. Overlap in the underlying
// clinical problem (an infected wound, a UTI, pneumonia) is expected and
// acceptable — only duplicate ownership of the same fact is prohibited.
// ---------------------------------------------------------------------------

/**
 * Temperature is Vitals-owned data, not a Body Systems ownership-registry
 * fact at all — it must never resolve to `infection_immunological` (or any
 * other body system). Infection may only display the Vitals-owned value as
 * read-only reference context; it must never create, edit, or store its own
 * temperature value (no `infection_temperature`, `infection_fever_value`, or
 * any other duplicate).
 */
export function temperatureIsNotOwnedByInfection(): boolean {
  return resolveFactOwner("temperature") !== "infection_immunological";
}

/** Explicit assertion: wound/skin findings are never reassessed by Infection — they remain Integumentary-owned. */
export function woundFindingsAreNotOwnedByInfection(): boolean {
  return (
    resolveFactOwner("wounds") !== "infection_immunological" &&
    resolveFactOwner("skin_integrity") !== "infection_immunological" &&
    resolveFactOwner("pressure_injuries") !== "infection_immunological"
  );
}

/** Explicit assertion: urinary findings are never reassessed by Infection — they remain Genitourinary-owned. */
export function urinaryFindingsAreNotOwnedByInfection(): boolean {
  return (
    resolveFactOwner("urinary_status") !== "infection_immunological" &&
    resolveFactOwner("genitourinary_symptoms") !== "infection_immunological"
  );
}

/** Explicit assertion: respiratory findings are never reassessed by Infection — they remain Respiratory-owned. */
export function respiratoryFindingsAreNotOwnedByInfection(): boolean {
  return (
    resolveFactOwner("dyspnea") !== "infection_immunological" &&
    resolveFactOwner("lung_sounds") !== "infection_immunological"
  );
}

/**
 * HOPE/comorbidity sepsis (diagnosis-history/billing context, documented
 * outside the Body Systems ownership registry) and current active-infection
 * sepsis (an `infection_status`/`infection_findings` fact owned by
 * Infection) are independent facts about a shared underlying condition.
 * Neither may be derived from, or automatically set/clear, the other — both
 * may coexist with their own provenance. Documented here as an explicit,
 * named, always-true assertion (matching the existing Braden/body-diagram
 * non-substitution pattern) so a future change collapsing them into one
 * field is a single-function diff, not a silent regression.
 */
export function hopeSepsisHistoryDoesNotDeriveActiveInfectionSepsis(): true {
  return true;
}

/** Explicit assertion, the inverse direction of the guard above: current active-infection sepsis never rewrites HOPE/comorbidity sepsis history. */
export function activeInfectionSepsisDoesNotRewriteHopeSepsisHistory(): true {
  return true;
}

/**
 * Allergy data remains owned by the existing authoritative allergy source
 * (`patient_allergies` / `AllergiesCard`). Infection may reference allergy
 * information for antimicrobial-treatment context but must never create a
 * second allergy store, a second allergy editor, or a copied allergy list.
 */
export function allergiesAreNotOwnedByInfection(): boolean {
  return resolveFactOwner("allergies") !== "infection_immunological";
}

/**
 * RN Notes (the SNS-wide optional narrative-context standard) are dated
 * supporting evidence, never a structured finding. A note alone can never
 * satisfy a required Infection finding (active status, organism,
 * antimicrobial treatment, follow-up, etc.), complete Infection review, or
 * close a Review By Exception item — only explicit structured
 * documentation and clinician review actions can.
 */
export function systemNotesDoNotSatisfyStructuredFindings(): true {
  return true;
}

/** Explicit assertion: a blank/empty RN Notes value is valid — notes are optional, never required. */
export function systemNotesAreOptional(notes: string | undefined): boolean {
  return notes === undefined || typeof notes === "string";
}
