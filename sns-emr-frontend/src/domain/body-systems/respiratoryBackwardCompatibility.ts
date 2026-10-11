/**
 * SNS Body Systems — Respiratory legacy/canonical compatibility mapping.
 *
 * The product-owner-authorized canonical fields (`treatmentDecision`,
 * `oxygenUse`, `spo2MeasurementCondition`, `ventilator.duration`) are the
 * nurse-facing source of truth. Historical records saved before those
 * fields existed only populated the legacy fields they replace
 * (`treatmentInitiated`/`treatmentDeclined`, `oxygenTherapy.inUse`,
 * `oxygenTherapy.onRoomAir`, `ventilator.shortTermVentilator`/
 * `longTermVentilator`). This module has two directions:
 *
 * 1. READ (legacy -> canonical display): `derive*Display` functions let
 *    the UI show a sensible canonical-field value for a record that was
 *    never given one. They never write to the draft or the server, and
 *    never infer a canonical value when the legacy fields are themselves
 *    absent/ambiguous (return undefined rather than guessing). A derived
 *    display value is NOT the same as the clinician having made that
 *    canonical choice, so `getMissingProductAuthorizedRequirements` must
 *    keep evaluating the real stored canonical field, not this
 *    derivation.
 * 2. WRITE (canonical -> legacy): `map*ToLegacy` functions compute the
 *    legacy compatibility keys to persist alongside a newly-entered
 *    canonical value, so the legacy keys remain populated for historical/
 *    audit continuity once their separate nurse-facing control is
 *    retired. These only set a legacy value where the specification
 *    defines a deterministic mapping; an ambiguous canonical value (e.g.
 *    `ALREADY_IN_PLACE`, `UNABLE_TO_VERIFY`, `NOT_OBTAINED`) leaves the
 *    legacy key untouched rather than fabricating one.
 */

export interface RespiratoryLegacyTreatmentValues {
  treatmentInitiated?: boolean;
  treatmentDeclined?: boolean;
}

export interface RespiratoryLegacyOxygenValues {
  type?: string;
}

export interface RespiratoryLegacyVentilatorValues {
  shortTermVentilator?: boolean;
  longTermVentilator?: boolean;
}

export type RespiratoryTreatmentDecisionDisplay = "INITIATED" | "DECLINED" | undefined;

/**
 * Derives a display-only `treatmentDecision` from the legacy boolean pair.
 * Returns undefined (never a guess) when neither or both legacy booleans
 * are set, since that combination carries no unambiguous meaning.
 */
export function deriveTreatmentDecisionDisplay(
  legacy: RespiratoryLegacyTreatmentValues,
): RespiratoryTreatmentDecisionDisplay {
  const initiated = legacy.treatmentInitiated === true;
  const declined = legacy.treatmentDeclined === true;
  if (initiated && !declined) return "INITIATED";
  if (declined && !initiated) return "DECLINED";
  return undefined;
}

export type RespiratoryOxygenDeliveryDeviceDisplay = string | undefined;

/**
 * Derives a display-only `oxygenTherapy.deliveryDevice` from the legacy
 * free-text `type` field. The legacy field was never a controlled
 * vocabulary, so this only passes the existing value through unchanged —
 * it never maps legacy text onto a new controlled value, which would risk
 * silently fabricating a clinical choice the clinician never made.
 */
export function deriveOxygenDeliveryDeviceDisplay(
  legacy: RespiratoryLegacyOxygenValues,
): RespiratoryOxygenDeliveryDeviceDisplay {
  return legacy.type ?? undefined;
}

export type RespiratoryVentilatorDurationDisplay = "SHORT_TERM" | "LONG_TERM" | undefined;

/**
 * Derives a display-only `ventilator.duration` from the legacy boolean
 * pair. Returns undefined (never a guess) when neither or both legacy
 * booleans are set.
 */
export function deriveVentilatorDurationDisplay(
  legacy: RespiratoryLegacyVentilatorValues,
): RespiratoryVentilatorDurationDisplay {
  const shortTerm = legacy.shortTermVentilator === true;
  const longTerm = legacy.longTermVentilator === true;
  if (shortTerm && !longTerm) return "SHORT_TERM";
  if (longTerm && !shortTerm) return "LONG_TERM";
  return undefined;
}

export type RespiratoryOxygenUseDisplay = "YES" | "NO" | undefined;

/**
 * Derives a display-only canonical `oxygenUse` from the legacy
 * `oxygenTherapy.inUse` boolean. `false` only becomes the canonical `NO`
 * when it is an explicit documented value (a real `boolean`), never an
 * absent/undefined default being treated as a negative answer.
 */
export function deriveOxygenUseDisplay(legacy: { inUse?: boolean }): RespiratoryOxygenUseDisplay {
  if (legacy.inUse === true) return "YES";
  if (legacy.inUse === false) return "NO";
  return undefined;
}

export type RespiratorySpo2MeasurementConditionDisplay = "ROOM_AIR" | "ON_OXYGEN" | undefined;

/**
 * Derives a display-only canonical `spo2MeasurementCondition` from the
 * legacy `onRoomAir` checkbox. `onRoomAir === false` only becomes `ON_OXYGEN`
 * when oxygen use is otherwise documented (the legacy checkbox was never a
 * generic "not on room air" signal on its own) — never fabricated from an
 * absent/undefined legacy value.
 */
export function deriveSpo2MeasurementConditionDisplay(
  legacy: { onRoomAir?: boolean },
  context: { oxygenUse?: string },
): RespiratorySpo2MeasurementConditionDisplay {
  if (legacy.onRoomAir === true) return "ROOM_AIR";
  if (legacy.onRoomAir === false && context.oxygenUse === "YES") return "ON_OXYGEN";
  return undefined;
}

/**
 * Canonical -> legacy WRITE mapping (the companion of the read-only
 * derivations above). Applied whenever the nurse sets a canonical field
 * going forward, so the legacy compatibility keys stay populated for
 * historical/audit continuity without requiring a second, separate nurse-
 * facing control. Deterministic only where the specification says so; an
 * ambiguous/non-mapping canonical value (e.g. `ALREADY_IN_PLACE`,
 * `UNABLE_TO_VERIFY`, `NOT_OBTAINED`) leaves the corresponding legacy key
 * untouched rather than fabricating a value for it.
 */
export function mapTreatmentDecisionToLegacy(
  decision: string | undefined,
): Partial<RespiratoryLegacyTreatmentValues> {
  switch (decision) {
    case "INITIATED":
      return { treatmentInitiated: true, treatmentDeclined: false };
    case "DECLINED":
      return { treatmentInitiated: false, treatmentDeclined: true };
    case "NOT_INDICATED":
      return { treatmentInitiated: false, treatmentDeclined: false };
    // ALREADY_IN_PLACE: do not fabricate `treatmentInitiated` — the legacy
    // field means "initiated during this assessment", which an existing,
    // already-in-place treatment is not.
    default:
      return {};
  }
}

export function mapOxygenUseToLegacyInUse(oxygenUse: string | undefined): boolean | undefined {
  if (oxygenUse === "YES") return true;
  if (oxygenUse === "NO") return false;
  // UNABLE_TO_VERIFY: the legacy model has no "unknown" state; do not force one.
  return undefined;
}

export function mapSpo2ConditionToLegacyRoomAir(condition: string | undefined): boolean | undefined {
  if (condition === "ROOM_AIR") return true;
  if (condition === "ON_OXYGEN") return false;
  // NOT_OBTAINED: do not fabricate a room-air value.
  return undefined;
}

export function mapVentilatorDurationToLegacy(
  duration: string | undefined,
): Partial<RespiratoryLegacyVentilatorValues> {
  if (duration === "SHORT_TERM") return { shortTermVentilator: true, longTermVentilator: false };
  if (duration === "LONG_TERM") return { shortTermVentilator: false, longTermVentilator: true };
  return {};
}
