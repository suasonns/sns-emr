/**
 * SNS Body Systems — legacy RNICA compatibility adapter.
 *
 * This is the ONLY module in this folder allowed to know about the existing
 * production RNICA.jsx / RNICACommandWorkspace.jsx runtime identifiers. No
 * other domain module may import this file or reference a legacy key
 * directly — that would let legacy naming leak back into the canonical
 * model, which is exactly what this adapter exists to prevent.
 *
 * Legacy RNICA runtime identifiers are a narrower, differently-named set
 * than the canonical `BodySystemCode` enum:
 *   - canonical `integumentary`         <-> legacy `skin`
 *   - canonical `infection_immunological` <-> legacy `infection`
 *   - every other canonical code maps one-to-one (same string both ways)
 *
 * Both mapping functions are exhaustive over their respective input types
 * and throw on unsupported input rather than silently falling back to a
 * different system — a silent fallback here would misfile a clinical fact
 * under the wrong owning system.
 */
import { BODY_SYSTEMS, type BodySystemCode } from "./types";

/**
 * The legacy RNICA runtime identifier set, as used today in
 * RNICA.jsx/RNICACommandWorkspace.jsx (e.g. `rnica-bodysystem-{key}` element
 * ids, `computeBodySystemFindings`'s switch statement). This is a read-only
 * snapshot of current runtime behavior, not a canonical domain model — see
 * the module doc comment above.
 */
export const LEGACY_RNICA_SYSTEM_KEYS = [
  "neurological",
  "respiratory",
  "cardiovascular",
  "nutrition",
  "gastrointestinal",
  "genitourinary",
  "musculoskeletal",
  "skin",
  "infection",
  "endocrine",
] as const;

export type LegacyRNICASystemKey = (typeof LEGACY_RNICA_SYSTEM_KEYS)[number];

const CANONICAL_TO_LEGACY: Record<BodySystemCode, LegacyRNICASystemKey> = {
  neurological: "neurological",
  respiratory: "respiratory",
  cardiovascular: "cardiovascular",
  nutrition: "nutrition",
  gastrointestinal: "gastrointestinal",
  genitourinary: "genitourinary",
  musculoskeletal: "musculoskeletal",
  integumentary: "skin",
  infection_immunological: "infection",
  endocrine: "endocrine",
};

const LEGACY_TO_CANONICAL: Record<LegacyRNICASystemKey, BodySystemCode> = {
  neurological: "neurological",
  respiratory: "respiratory",
  cardiovascular: "cardiovascular",
  nutrition: "nutrition",
  gastrointestinal: "gastrointestinal",
  genitourinary: "genitourinary",
  musculoskeletal: "musculoskeletal",
  skin: "integumentary",
  infection: "infection_immunological",
  endocrine: "endocrine",
};

/** Maps a canonical Body Systems identifier to its legacy RNICA runtime key. Exhaustive; no fallback. */
export function toLegacyRNICASystemKey(system: BodySystemCode): LegacyRNICASystemKey {
  const mapped = CANONICAL_TO_LEGACY[system];
  if (!mapped) {
    throw new Error(`No legacy RNICA mapping defined for canonical system "${system}".`);
  }
  return mapped;
}

/**
 * Maps a legacy RNICA runtime key to its canonical Body Systems identifier.
 * Throws on any input outside `LEGACY_RNICA_SYSTEM_KEYS` rather than
 * silently mapping an unrecognized legacy key to an arbitrary canonical
 * system.
 */
export function fromLegacyRNICASystemKey(legacyKey: string): BodySystemCode {
  if (!(LEGACY_RNICA_SYSTEM_KEYS as readonly string[]).includes(legacyKey)) {
    throw new Error(`Unrecognized legacy RNICA system key: "${legacyKey}".`);
  }
  return LEGACY_TO_CANONICAL[legacyKey as LegacyRNICASystemKey];
}

/**
 * Invariant check used by this module's tests: every canonical system has
 * exactly one legacy mapping and every legacy key has exactly one canonical
 * mapping, with no many-to-one collisions in either direction.
 */
export function legacyAdapterIsExhaustiveAndBijective(): boolean {
  const canonicalCovered = BODY_SYSTEMS.every((system) => system in CANONICAL_TO_LEGACY);
  const legacyCovered = LEGACY_RNICA_SYSTEM_KEYS.every((key) => key in LEGACY_TO_CANONICAL);
  const roundTripsFromCanonical = BODY_SYSTEMS.every(
    (system) => fromLegacyRNICASystemKey(toLegacyRNICASystemKey(system)) === system,
  );
  const roundTripsFromLegacy = LEGACY_RNICA_SYSTEM_KEYS.every(
    (key) => toLegacyRNICASystemKey(fromLegacyRNICASystemKey(key)) === key,
  );
  return canonicalCovered && legacyCovered && roundTripsFromCanonical && roundTripsFromLegacy;
}
