import { describe, it, expect } from "vitest";
import {
  CANONICAL_PROVIDER_ROLES,
  normalizeProviderRole,
  buildProviderRoleAuditMeta,
} from "./providerRoleNormalization";

describe("normalizeProviderRole — high-confidence aliases", () => {
  it.each([
    ["attending physician", "MD"],
    ["Attending Physician", "MD"],
    ["physician", "MD"],
    ["doctor", "MD"],
    ["Doctor", "MD"],
    ["md", "MD"],
    ["MD", "MD"],
    ["nurse practitioner", "NP"],
    ["Nurse Practitioner", "NP"],
    ["np", "NP"],
    ["physician assistant", "PA"],
    ["Physician Assistant", "PA"],
    ["pa", "PA"],
  ])("normalizes %j to %j with high confidence", (input, expected) => {
    const result = normalizeProviderRole(input);
    expect(result.canonicalValue).toBe(expected);
    expect(result.confidence).toBe("high");
    expect(result.requiresConfirmation).toBe(false);
  });

  it("tags an already-canonical value distinctly from an aliased one", () => {
    expect(normalizeProviderRole("MD").normalizationMethod).toBe("already_canonical");
    expect(normalizeProviderRole("doctor").normalizationMethod).toBe("ui_alias");
  });
});

describe("normalizeProviderRole — ambiguous terms require confirmation", () => {
  it.each([
    ["provider"],
    ["clinician"],
    ["practitioner"],
    ["ordering provider"],
    ["attending"],
  ])("flags %j as ambiguous and offers MD/NP/PA candidates", (input) => {
    const result = normalizeProviderRole(input);
    expect(result.canonicalValue).toBeNull();
    expect(result.confidence).toBe("ambiguous");
    expect(result.requiresConfirmation).toBe(true);
    expect(result.candidates).toEqual([...CANONICAL_PROVIDER_ROLES]);
  });
});

describe("normalizeProviderRole — unrecognized input", () => {
  it("never auto-maps a completely unknown term", () => {
    const result = normalizeProviderRole("chaplain");
    expect(result.canonicalValue).toBeNull();
    expect(result.confidence).toBe("unrecognized");
    expect(result.requiresConfirmation).toBe(true);
  });

  it("treats blank input as unrecognized rather than throwing", () => {
    expect(() => normalizeProviderRole("")).not.toThrow();
    expect(normalizeProviderRole("").requiresConfirmation).toBe(true);
    expect(() => normalizeProviderRole(undefined)).not.toThrow();
  });
});

describe("buildProviderRoleAuditMeta", () => {
  it("preserves the original text and the resolved canonical value", () => {
    const result = normalizeProviderRole("Attending Physician");
    const meta = buildProviderRoleAuditMeta(result);
    expect(meta).toEqual({
      original_input: "Attending Physician",
      normalized_value: "MD",
      normalization_method: "ui_alias",
    });
  });

  it("uses the user-confirmed value for ambiguous input rather than null", () => {
    const result = normalizeProviderRole("provider");
    const meta = buildProviderRoleAuditMeta(result, "NP");
    expect(meta).toEqual({
      original_input: "provider",
      normalized_value: "NP",
      normalization_method: "none",
    });
  });
});
