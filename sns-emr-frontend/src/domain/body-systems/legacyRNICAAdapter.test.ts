import { describe, expect, it } from "vitest";

import { BODY_SYSTEMS } from "./types";
import {
  LEGACY_RNICA_SYSTEM_KEYS,
  fromLegacyRNICASystemKey,
  legacyAdapterIsExhaustiveAndBijective,
  toLegacyRNICASystemKey,
} from "./legacyRNICAAdapter";

describe("Body Systems — legacy RNICA adapter", () => {
  it("maps canonical integumentary to legacy skin", () => {
    expect(toLegacyRNICASystemKey("integumentary")).toBe("skin");
  });

  it("maps canonical infection_immunological to legacy infection", () => {
    expect(toLegacyRNICASystemKey("infection_immunological")).toBe("infection");
  });

  it("maps every other canonical system one-to-one", () => {
    const oneToOne = BODY_SYSTEMS.filter(
      (system) => system !== "integumentary" && system !== "infection_immunological",
    );
    for (const system of oneToOne) {
      expect(toLegacyRNICASystemKey(system)).toBe(system);
    }
  });

  it("reverse-maps legacy skin and infection back to their canonical values", () => {
    expect(fromLegacyRNICASystemKey("skin")).toBe("integumentary");
    expect(fromLegacyRNICASystemKey("infection")).toBe("infection_immunological");
  });

  it("round-trips every canonical system through the legacy mapping and back", () => {
    for (const system of BODY_SYSTEMS) {
      expect(fromLegacyRNICASystemKey(toLegacyRNICASystemKey(system))).toBe(system);
    }
  });

  it("round-trips every legacy key through the canonical mapping and back", () => {
    for (const key of LEGACY_RNICA_SYSTEM_KEYS) {
      expect(toLegacyRNICASystemKey(fromLegacyRNICASystemKey(key))).toBe(key);
    }
  });

  it("does not silently map an unknown legacy key to any canonical system", () => {
    expect(() => fromLegacyRNICASystemKey("not_a_real_legacy_key")).toThrow();
    expect(() => fromLegacyRNICASystemKey("")).toThrow();
  });

  it("does not silently map an unknown canonical system to any legacy key", () => {
    // @ts-expect-error intentionally invalid canonical system to prove no silent fallback
    expect(() => toLegacyRNICASystemKey("not_a_real_system")).toThrow();
  });

  it("confirms the adapter is exhaustive and bijective over both key sets", () => {
    expect(legacyAdapterIsExhaustiveAndBijective()).toBe(true);
  });
});
