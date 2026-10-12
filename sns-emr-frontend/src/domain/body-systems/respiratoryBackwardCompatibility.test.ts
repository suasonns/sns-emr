import { describe, expect, it } from "vitest";
import {
  deriveOxygenDeliveryDeviceDisplay,
  deriveOxygenUseDisplay,
  deriveSpo2MeasurementConditionDisplay,
  deriveTreatmentDecisionDisplay,
  deriveVentilatorDurationDisplay,
  mapOxygenUseToLegacyInUse,
  mapSpo2ConditionToLegacyRoomAir,
  mapTreatmentDecisionToLegacy,
  mapVentilatorDurationToLegacy,
} from "./respiratoryBackwardCompatibility";

describe("deriveTreatmentDecisionDisplay", () => {
  it("returns INITIATED when only treatmentInitiated is true", () => {
    expect(deriveTreatmentDecisionDisplay({ treatmentInitiated: true })).toBe("INITIATED");
  });

  it("returns DECLINED when only treatmentDeclined is true", () => {
    expect(deriveTreatmentDecisionDisplay({ treatmentDeclined: true })).toBe("DECLINED");
  });

  it("returns undefined when neither legacy boolean is set", () => {
    expect(deriveTreatmentDecisionDisplay({})).toBeUndefined();
  });

  it("returns undefined (never a guess) when both legacy booleans are set", () => {
    expect(deriveTreatmentDecisionDisplay({ treatmentInitiated: true, treatmentDeclined: true })).toBeUndefined();
  });
});

describe("deriveOxygenDeliveryDeviceDisplay", () => {
  it("passes through the existing legacy type value unchanged", () => {
    expect(deriveOxygenDeliveryDeviceDisplay({ type: "Nasal Cannula" })).toBe("Nasal Cannula");
  });

  it("returns undefined when the legacy type is absent", () => {
    expect(deriveOxygenDeliveryDeviceDisplay({})).toBeUndefined();
  });
});

describe("deriveVentilatorDurationDisplay", () => {
  it("returns SHORT_TERM when only shortTermVentilator is true", () => {
    expect(deriveVentilatorDurationDisplay({ shortTermVentilator: true })).toBe("SHORT_TERM");
  });

  it("returns LONG_TERM when only longTermVentilator is true", () => {
    expect(deriveVentilatorDurationDisplay({ longTermVentilator: true })).toBe("LONG_TERM");
  });

  it("returns undefined when neither legacy boolean is set", () => {
    expect(deriveVentilatorDurationDisplay({})).toBeUndefined();
  });

  it("returns undefined (never a guess) when both legacy booleans are set", () => {
    expect(deriveVentilatorDurationDisplay({ shortTermVentilator: true, longTermVentilator: true })).toBeUndefined();
  });
});

describe("deriveOxygenUseDisplay", () => {
  it("returns YES when legacy inUse is explicitly true", () => {
    expect(deriveOxygenUseDisplay({ inUse: true })).toBe("YES");
  });

  it("returns NO when legacy inUse is explicitly false", () => {
    expect(deriveOxygenUseDisplay({ inUse: false })).toBe("NO");
  });

  it("returns undefined when legacy inUse is absent (never infers NO from a default)", () => {
    expect(deriveOxygenUseDisplay({})).toBeUndefined();
  });
});

describe("deriveSpo2MeasurementConditionDisplay", () => {
  it("returns ROOM_AIR when legacy onRoomAir is true", () => {
    expect(deriveSpo2MeasurementConditionDisplay({ onRoomAir: true }, {})).toBe("ROOM_AIR");
  });

  it("returns ON_OXYGEN when onRoomAir is false and oxygen use is documented YES", () => {
    expect(deriveSpo2MeasurementConditionDisplay({ onRoomAir: false }, { oxygenUse: "YES" })).toBe("ON_OXYGEN");
  });

  it("returns undefined when onRoomAir is false but oxygen use is not documented", () => {
    expect(deriveSpo2MeasurementConditionDisplay({ onRoomAir: false }, {})).toBeUndefined();
  });

  it("returns undefined when onRoomAir is absent", () => {
    expect(deriveSpo2MeasurementConditionDisplay({}, { oxygenUse: "YES" })).toBeUndefined();
  });
});

describe("mapTreatmentDecisionToLegacy", () => {
  it("maps INITIATED to initiated=true, declined=false", () => {
    expect(mapTreatmentDecisionToLegacy("INITIATED")).toEqual({ treatmentInitiated: true, treatmentDeclined: false });
  });

  it("maps DECLINED to initiated=false, declined=true", () => {
    expect(mapTreatmentDecisionToLegacy("DECLINED")).toEqual({ treatmentInitiated: false, treatmentDeclined: true });
  });

  it("maps NOT_INDICATED to both legacy booleans false", () => {
    expect(mapTreatmentDecisionToLegacy("NOT_INDICATED")).toEqual({
      treatmentInitiated: false,
      treatmentDeclined: false,
    });
  });

  it("maps ALREADY_IN_PLACE to both legacy booleans false (not initiated during this assessment, but not left stale either)", () => {
    expect(mapTreatmentDecisionToLegacy("ALREADY_IN_PLACE")).toEqual({
      treatmentInitiated: false,
      treatmentDeclined: false,
    });
  });

  it("resets both legacy booleans to undefined when the decision is cleared, so a stale prior selection cannot linger (HOPE J2040 correctness)", () => {
    expect(mapTreatmentDecisionToLegacy(undefined)).toEqual({
      treatmentInitiated: undefined,
      treatmentDeclined: undefined,
    });
  });
});

describe("mapOxygenUseToLegacyInUse", () => {
  it("maps YES to true and NO to false", () => {
    expect(mapOxygenUseToLegacyInUse("YES")).toBe(true);
    expect(mapOxygenUseToLegacyInUse("NO")).toBe(false);
  });

  it("does not force a legacy value for UNABLE_TO_VERIFY", () => {
    expect(mapOxygenUseToLegacyInUse("UNABLE_TO_VERIFY")).toBeUndefined();
  });
});

describe("mapSpo2ConditionToLegacyRoomAir", () => {
  it("maps ROOM_AIR to true and ON_OXYGEN to false", () => {
    expect(mapSpo2ConditionToLegacyRoomAir("ROOM_AIR")).toBe(true);
    expect(mapSpo2ConditionToLegacyRoomAir("ON_OXYGEN")).toBe(false);
  });

  it("does not fabricate a legacy value for NOT_OBTAINED", () => {
    expect(mapSpo2ConditionToLegacyRoomAir("NOT_OBTAINED")).toBeUndefined();
  });
});

describe("mapVentilatorDurationToLegacy", () => {
  it("maps SHORT_TERM and LONG_TERM deterministically", () => {
    expect(mapVentilatorDurationToLegacy("SHORT_TERM")).toEqual({
      shortTermVentilator: true,
      longTermVentilator: false,
    });
    expect(mapVentilatorDurationToLegacy("LONG_TERM")).toEqual({
      shortTermVentilator: false,
      longTermVentilator: true,
    });
  });

  it("does not fabricate a legacy value for an undefined duration", () => {
    expect(mapVentilatorDurationToLegacy(undefined)).toEqual({});
  });
});
