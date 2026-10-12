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
 *    defines a deterministic mapping; a canonical value with no legacy
 *    equivalent (e.g. `UNABLE_TO_VERIFY`, `NOT_OBTAINED`) leaves the legacy
 *    key untouched rather than fabricating one. `mapTreatmentDecisionToLegacy`
 *    is the one exception that is written as a *total* function (every
 *    decision, including `ALREADY_IN_PLACE` and cleared/unselected, returns
 *    explicit values): the legacy `treatmentInitiated`/`treatmentDeclined`
 *    pair also feeds HOPE J2040 reporting, so a stale value left over from
 *    a previously-selected decision is a correctness bug, not a harmless
 *    gap — see `mapTreatmentDecisionToLegacy` for the per-case rationale.
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
 * facing control. Total: every decision value, including `ALREADY_IN_PLACE`
 * and cleared/unselected, returns explicit legacy values rather than
 * leaving the previous selection's legacy flags untouched — this pair also
 * feeds HOPE J2040 reporting, so a stale leftover value is a correctness
 * bug (see per-case comments below).
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
    case "ALREADY_IN_PLACE":
      // An existing treatment was not initiated *during this assessment* —
      // this is an explicit, accurate `false`, not a fabricated guess, so
      // it must still be written (otherwise a prior INITIATED/DECLINED
      // selection that the nurse later changes to ALREADY_IN_PLACE would
      // leave a stale legacy/HOPE-feeding flag behind).
      return { treatmentInitiated: false, treatmentDeclined: false };
    default:
      // Treatment Decision cleared/unselected (hospice-usability clear/undo
      // control): reset the derived legacy flags to unset rather than
      // leaving behind whatever value a previously-selected decision wrote,
      // which would otherwise let HOPE J2040 reporting and historical/audit
      // consumers see a decision the nurse no longer has selected.
      return { treatmentInitiated: undefined, treatmentDeclined: undefined };
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

/**
 * Oxygen-field consolidation (product-owner "TOO MUCH REDUNDANCY" /
 * Ticket 2 directive): `respiratory_oxygen_delivery_type`,
 * `respiratory_oxygen_liters_per_minute`, `respiratory_oxygen_delivery_mode`,
 * and `respiratory_oxygen_sat_on_o2` are legacy-only compatibility keys now
 * superseded by `oxygenTherapy.deliveryDevice`, `oxygenTherapy.flowValue`/
 * `flowUnit`, `oxygenTherapy.frequency`, and top-level `spo2Value`
 * respectively — a nurse was previously shown both the legacy and
 * canonical control for the same concept at once. These WRITE mappings
 * keep the legacy keys populated for historical/audit continuity now that
 * their separate nurse-facing controls are retired (see
 * `RespiratoryPanel.tsx`'s `LEGACY_HIDDEN_FIELD_IDS`), mirroring the
 * existing mappings above. None fabricate a value with no deterministic
 * legacy equivalent.
 */
export function mapOxygenDeliveryDeviceToLegacyType(
  device: string | undefined,
  otherDevice: string | undefined,
): string | undefined {
  switch (device) {
    case "NASAL_CANNULA":
      return "Nasal cannula";
    case "MASK":
      // The legacy vocabulary distinguishes several mask types the
      // canonical field intentionally collapsed into one "Mask" choice;
      // "Simple mask" is the closest generic equivalent, never a guess at
      // which specific legacy mask type was meant.
      return "Simple mask";
    case "OTHER":
      return otherDevice || undefined;
    default:
      // UNABLE_TO_VERIFY / unset: no deterministic legacy device.
      return undefined;
  }
}

export function mapOxygenFlowValueToLegacyLitersPerMinute(
  flowValue: number | undefined,
  flowUnit: string | undefined,
): number | undefined {
  // Only an L/min-labeled flow value has a direct legacy equivalent; never
  // fabricate a unit conversion for any other/unset flow unit.
  return flowUnit === "L_MIN" ? flowValue : undefined;
}

export function mapOxygenFrequencyToLegacyDeliveryMode(frequency: string | undefined): string | undefined {
  if (frequency === "CONTINUOUS") return "Continuous";
  if (frequency === "PRN") return "PRN";
  // SCHEDULED / OTHER: the legacy field only ever supported Continuous/PRN;
  // do not force either onto a value it never represented.
  return undefined;
}

export function mapSpo2ValueToLegacySatOnO2(
  spo2Value: number | undefined,
  condition: string | undefined,
): number | undefined {
  // The legacy field specifically meant "SpO2 while on oxygen" — only
  // mirror the canonical SpO2 Value when the canonical condition confirms
  // that same clinical context.
  return condition === "ON_OXYGEN" ? spo2Value : undefined;
}
