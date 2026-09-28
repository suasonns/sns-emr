// Presentation-only ICD-10 code formatting.
//
// icd10_master.icd10_code is stored WITHOUT the decimal point (e.g. "G301"
// for Parkinson's disease) -- see backend/scripts/import_icd10_dataset.py's
// normalize_icd10_code(). Clinicians, coders, and LCD references all expect
// the standard dotted form ("G30.1"). This helper re-inserts the decimal
// for display ONLY.
//
// Do NOT use this on any value that feeds category-matching regexes
// (categorizeIcd10/matchesCategory/HOPE_COMORBIDITY_CATEGORIES), gets
// persisted back into form state, or is sent in an export/API payload --
// those all expect the raw undotted code exactly as stored.
export function formatIcd10Code(code) {
  if (!code) return code;
  const value = String(code).trim();
  if (!value) return value;
  // Already dotted (e.g. came from `display_name` or was typed by hand) --
  // leave as-is so this stays idempotent.
  if (value.includes(".")) return value;
  // Codes of 3 characters or fewer (e.g. "I50") have no decimal portion.
  if (value.length <= 3) return value;
  return `${value.slice(0, 3)}.${value.slice(3)}`;
}
