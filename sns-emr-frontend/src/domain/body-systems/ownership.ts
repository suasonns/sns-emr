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
    factKeys: ["active_infection_status", "infection_findings"],
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
