/**
 * UI normalization layer for physician-order `ordered_by_provider_role`
 * entry.
 *
 * The backend (`app.services.physician_order_service.VALID_PROVIDER_ROLES`)
 * accepts only the canonical values MD, NP, and PA and rejects everything
 * else -- that contract is intentionally unchanged (see
 * docs/rnica-poc-lock-no-autogen-disposition.md and the physician-order
 * provider-role contract test in
 * backend/tests/test_physician_orders_lifecycle.py). Clinical staff,
 * however, naturally type "attending physician", "doctor", "nurse
 * practitioner", etc. This module bridges that gap entirely in the UI:
 * unambiguous clinical terminology is normalized automatically; genuinely
 * ambiguous terms ("provider", "clinician", "practitioner", "attending")
 * are surfaced to the user for explicit confirmation before anything is
 * submitted. The database and API never see anything but MD/NP/PA, and
 * the original free-text entry is preserved as audit metadata, never as
 * the authoritative role.
 */

export const CANONICAL_PROVIDER_ROLES = Object.freeze(["MD", "NP", "PA"]);

// High-confidence aliases: unambiguous clinical terminology that maps to
// exactly one canonical role. Matching is case-insensitive and tolerant of
// surrounding whitespace and punctuation (see _normalizeKey).
const HIGH_CONFIDENCE_ALIASES = {
  md: "MD",
  "m.d.": "MD",
  "m.d": "MD",
  physician: "MD",
  "attending physician": "MD",
  "attending md": "MD",
  doctor: "MD",
  "medical doctor": "MD",

  np: "NP",
  "n.p.": "NP",
  "nurse practitioner": "NP",

  pa: "PA",
  "p.a.": "PA",
  "physician assistant": "PA",
  "physician associate": "PA",
};

// Ambiguous terms: real clinical vocabulary, but they don't identify a
// single credential (any of MD/NP/PA could be "the provider" or "the
// attending"). These must never be auto-mapped -- always require explicit
// user confirmation.
const AMBIGUOUS_TERMS = new Set([
  "provider",
  "clinician",
  "practitioner",
  "ordering provider",
  "attending",
  "ordering practitioner",
]);

function _normalizeKey(rawInput) {
  return String(rawInput ?? "")
    .trim()
    .toLowerCase()
    .replace(/\s+/g, " ");
}

/**
 * Normalize a free-text provider-role entry.
 *
 * @param {string} rawInput - the exact text the user typed.
 * @returns {{
 *   originalInput: string,
 *   canonicalValue: string|null,
 *   confidence: "high"|"ambiguous"|"unrecognized",
 *   requiresConfirmation: boolean,
 *   candidates: string[],
 *   normalizationMethod: "ui_alias"|"already_canonical"|"none",
 * }}
 *
 * - confidence "high": exactly one canonical role recognized -> safe to
 *   auto-apply without further prompting.
 * - confidence "ambiguous": recognized as clinical terminology, but it does
 *   not identify a single credential -> caller MUST prompt the user to pick
 *   from `candidates` before saving.
 * - confidence "unrecognized": no known mapping at all -> caller should
 *   ask the user to pick explicitly (candidates lists all canonical roles)
 *   or re-enter; never silently guess.
 */
export function normalizeProviderRole(rawInput) {
  const originalInput = String(rawInput ?? "");
  const key = _normalizeKey(originalInput);

  if (CANONICAL_PROVIDER_ROLES.includes(key.toUpperCase())) {
    const canonicalValue = key.toUpperCase();
    return {
      originalInput,
      canonicalValue,
      confidence: "high",
      requiresConfirmation: false,
      candidates: [canonicalValue],
      normalizationMethod: "already_canonical",
    };
  }

  if (Object.prototype.hasOwnProperty.call(HIGH_CONFIDENCE_ALIASES, key)) {
    const canonicalValue = HIGH_CONFIDENCE_ALIASES[key];
    return {
      originalInput,
      canonicalValue,
      confidence: "high",
      requiresConfirmation: false,
      candidates: [canonicalValue],
      normalizationMethod: "ui_alias",
    };
  }

  if (AMBIGUOUS_TERMS.has(key)) {
    return {
      originalInput,
      canonicalValue: null,
      confidence: "ambiguous",
      requiresConfirmation: true,
      candidates: [...CANONICAL_PROVIDER_ROLES],
      normalizationMethod: "none",
    };
  }

  return {
    originalInput,
    canonicalValue: null,
    confidence: "unrecognized",
    requiresConfirmation: true,
    candidates: [...CANONICAL_PROVIDER_ROLES],
    normalizationMethod: "none",
  };
}

/**
 * Build the audit-metadata payload for a normalization decision. Callers
 * attach this to the order-creation request (e.g. as
 * `ordered_by_provider_role_source`) so the original user-entered text is
 * preserved for troubleshooting/audit even though only the canonical value
 * is ever stored as the authoritative role.
 */
export function buildProviderRoleAuditMeta(normalizationResult, confirmedValue) {
  return {
    original_input: normalizationResult.originalInput,
    normalized_value: confirmedValue ?? normalizationResult.canonicalValue,
    normalization_method: normalizationResult.normalizationMethod,
  };
}
