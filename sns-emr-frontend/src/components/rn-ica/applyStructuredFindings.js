// applyStructuredFindings.js
//
// Frontend apply layer for the shared StructuredFinding contract (see
// backend app/services/evidence/structured_findings.py). Consumes the
// validated findings already attached to a harvested signal
// (sig.structured_findings, from PatientHarvestedSignal.structured_findings)
// or a transcript note draft (rec.ai_note_draft.structured_findings) and
// safely writes them into the real RNICA form fields.
//
// This is intentionally the ONLY place structured findings get applied to
// form state, so every apply -- whether triggered from an H&P/referral/
// uploaded-document signal or a voice-recording draft -- goes through the
// exact same rules:
//
//   - Only assertion_status === "CURRENT" findings are ever applied.
//     HISTORICAL / NEGATED / UNCERTAIN findings are returned in
//     `reviewNeeded` instead -- never silently applied, never silently
//     dropped.
//   - "set" writes only apply to a field that is still blank (matches the
//     existing applyIfBlank convention used elsewhere in RNICA.jsx for
//     AI-suggested symptom severities) -- a clinician's own entry is never
//     overwritten. When the field is already non-blank, the suggestion is
//     returned in `conflicts` for RN review instead of being applied.
//   - "multi_add" writes append one option to a checklist/multi-select
//     array only if it isn't already present -- this never overwrites or
//     removes anything the clinician already checked.
//   - "push_draft_row" writes append a new draft row (e.g. a wound entry)
//     only when no existing row already has the same value at the
//     concept's value_slot field, so re-applying the same evidence twice
//     (or an already-acknowledged finding) never creates a duplicate row.
//   - Every applied field is recorded with full provenance (concept_code,
//     source_type, source_excerpt, source_date, source_location,
//     confidence) so the RN can see exactly why a field was populated.
//   - A concept unknown to this frontend mirror (should not happen -- the
//     backend already validated it against the identical registry) is
//     skipped defensively rather than guessed at.

import { CONCEPT_REGISTRY } from "./structuredFindingRegistry.generated";

function isBlank(value) {
  if (value === null || value === undefined) return true;
  if (value === "") return true;
  if (Array.isArray(value) && value.length === 0) return true;
  // `false` is never treated as blank by this generic helper. RNICA
  // boolean presence fields (e.g. heartFailurePresent, contracturesPresent,
  // skinConditionsPresent) default to `false`, and an RN who has actually
  // examined the patient and left a box unchecked has made a real clinical
  // assertion -- it must never be silently flipped to `true` by an AI
  // suggestion. Top-level boolean "set" writes use isBooleanWriteBlank()
  // below instead, which can tell an untouched default apart from an
  // RN-confirmed value; every other write kind (set_row_field, bounded
  // value_slot writes) keeps this conservative "false is never blank"
  // behavior and always routes through the conflict path.
  return false;
}

// Distinguish an untouched-default boolean from an RN-entered one for a
// top-level "set" write whose value is a boolean and whose current value
// is `false`. A boolean-presence field's default is indistinguishable from
// an RN's deliberate "false" confirmation by looking at the field alone --
// both are just `false`. The reliable signal is the surrounding SECTION:
// if every field in that section still exactly matches its pristine
// INITIAL_FORM default, the RN has never engaged with the section at all,
// so this field's `false` can only be the untouched default and is safe to
// auto-populate. If ANY other field in the section already differs from
// its default, the RN has been in this section -- this boolean's `false`
// is now ambiguous (could be a deliberate confirmation or simply not yet
// reached), so it is treated conservatively as RN-entered and routed to
// `conflicts` for explicit review, never silently overwritten.
//
// `initialFormData` is optional (older/direct callers may omit it) -- with
// no baseline to compare against, this always reports "touched" so the
// safe, pre-existing conflict-routing behavior is preserved.
function isSectionUntouched(sectionData, initialSectionData) {
  if (!initialSectionData || typeof initialSectionData !== "object") return false;
  try {
    return JSON.stringify(sectionData ?? null) === JSON.stringify(initialSectionData);
  } catch {
    return false;
  }
}

function getNested(obj, path) {
  return path.split(".").reduce((cur, key) => cur?.[key], obj);
}

function setNested(obj, path, value) {
  const clone = obj ? JSON.parse(JSON.stringify(obj)) : {};
  const keys = path.split(".");
  let cur = clone;
  for (let i = 0; i < keys.length - 1; i++) {
    if (!cur[keys[i]] || typeof cur[keys[i]] !== "object") cur[keys[i]] = {};
    cur = cur[keys[i]];
  }
  cur[keys[keys.length - 1]] = value;
  return clone;
}

// Lightweight free-text similarity helpers, shared by the classification
// engine (classifyConflict, below) and the wound near-duplicate detector
// in applyStructuredFindings' push_draft_row branch -- deliberately dumb
// (word-overlap only, no semantic/clinical knowledge) so it never silently
// decides "these are the same fact"; it only ever flags "these look
// similar enough that a human should decide."
const STOPWORDS = new Set(["of", "in", "a", "an", "the", "per", "on", "at", "to", "and", "or", "documented"]);

function significantWords(str) {
  return new Set(
    String(str || "")
      .toLowerCase()
      .replace(/%/g, "") // "5%" and "5 %" must tokenize identically
      .split(/[^a-z0-9]+/)
      .filter((w) => w && !STOPWORDS.has(w))
  );
}

function jaccardOverlap(a, b) {
  if (a.size === 0 && b.size === 0) return 1;
  let intersection = 0;
  for (const w of a) if (b.has(w)) intersection++;
  const union = new Set([...a, ...b]).size;
  return union === 0 ? 1 : intersection / union;
}

// value_slot.path is written in the "wounds[].location" convention -- the
// array field name, then the row field the value is written into. Splits
// that into { arrayPath: "wounds", rowField: "location" }.
function splitDraftRowPath(valueSlotPath) {
  const match = /^(.+)\[\]\.(.+)$/.exec(valueSlotPath || "");
  if (!match) return null;
  return { arrayPath: match[1], rowField: match[2] };
}

/**
 * Apply a batch of validated StructuredFinding objects onto the full RNICA
 * formData (all sections), respecting blank-only/no-overwrite/assertion-
 * status rules.
 *
 * @param {object} formData - the full RNICA form state ({ sectionKey: {...} }).
 * @param {Array} findings - StructuredFinding dicts (already backend-validated).
 * @param {object} [initialFormData] - the pristine INITIAL_FORM defaults, used
 *   only to distinguish an untouched-default boolean from an RN-entered one
 *   (see isSectionUntouched above). Omit to always treat boolean `false`
 *   values as RN-entered (the prior, more conservative behavior).
 * @returns {{
 *   formData: object,
 *   appliedFields: Array<{section, path, value, concept_code, finding}>,
 *   conflicts: Array<{section, path, existingValue, suggestedValue, concept_code, finding}>,
 *   reviewNeeded: Array<object>,
 * }}
 */
export function applyStructuredFindings(formData, findings, initialFormData) {
  let next = formData;
  const appliedFields = [];
  const conflicts = [];
  const reviewNeeded = [];
  const woundReviewItems = [];
  // Computed lazily, once per section, from the ORIGINAL (pre-this-call)
  // formData -- never from `next`, so a boolean applied earlier in this
  // same batch never makes a later, unrelated field in the same section
  // look "touched" purely because of this run's own writes.
  const untouchedSectionCache = {};
  const sectionWasUntouched = (section) => {
    if (!(section in untouchedSectionCache)) {
      untouchedSectionCache[section] = isSectionUntouched(
        formData?.[section],
        initialFormData?.[section]
      );
    }
    return untouchedSectionCache[section];
  };

  for (const finding of findings || []) {
    if (!finding || !finding.concept_code) continue;

    const concept = CONCEPT_REGISTRY[finding.concept_code];
    if (!concept) continue; // unknown to this mirror -- never guess

    if (finding.assertion_status !== "CURRENT") {
      // HISTORICAL / NEGATED / UNCERTAIN -- keep out of current-status
      // controls entirely; surfaced separately for RN review.
      reviewNeeded.push(finding);
      continue;
    }

    for (const write of concept.writes || []) {
      const targetSection = write.section || concept.section;
      const sectionData = next[targetSection];
      if (!sectionData) continue; // section doesn't exist on this form (e.g. non-RNICA) -- skip safely

      if (write.op === "set") {
        const current = getNested(sectionData, write.path);
        // A boolean-presence field currently at its default `false`: only
        // treat it as blank/eligible-for-auto-apply when the WHOLE section
        // is still untouched (see isSectionUntouched). Any other value
        // (including a boolean already `true`, or `false` in a section the
        // RN has already engaged with) keeps the normal isBlank() rule.
        const isUntouchedBooleanDefault =
          typeof write.value === "boolean" && current === false && sectionWasUntouched(targetSection);
        // A field that is already set to the EXACT value this finding is
        // suggesting is not a conflict at all -- it's evidence the same
        // fact was already applied (very common with chunked/overlapping
        // extraction re-detecting one clinical fact from multiple chunks,
        // or the same fact mentioned in both the H&P and a later note).
        // Route it to "already applied" (counted as applied, no duplicate
        // write) instead of piling it into `conflicts` for the RN to
        // review a fact that was never actually in dispute.
        const alreadySatisfied = !isBlank(current) && current === write.value;
        const blank = isUntouchedBooleanDefault ? true : isBlank(current);
        if (alreadySatisfied) {
          appliedFields.push({ section: targetSection, path: write.path, value: write.value, concept_code: finding.concept_code, finding, writeKind: "already_satisfied" });
          continue;
        }
        if (!blank) {
          conflicts.push({
            section: targetSection,
            path: write.path,
            existingValue: current,
            suggestedValue: write.value,
            concept_code: finding.concept_code,
            finding,
          });
          continue;
        }
        next = { ...next, [targetSection]: setNested(sectionData, write.path, write.value) };
        appliedFields.push({ section: targetSection, path: write.path, value: write.value, concept_code: finding.concept_code, finding, writeKind: "scalar" });
      } else if (write.op === "multi_add") {
        const current = getNested(next[targetSection], write.path);
        const arr = Array.isArray(current) ? current : [];
        if (arr.includes(write.value)) continue; // already checked -- nothing to do, never duplicated
        const updatedArr = [...arr, write.value];
        next = { ...next, [targetSection]: setNested(next[targetSection], write.path, updatedArr) };
        appliedFields.push({ section: targetSection, path: write.path, value: write.value, concept_code: finding.concept_code, finding, writeKind: "array_member" });
      } else if (write.op === "push_draft_row") {
        const slot = concept.valueSlot;
        const split = slot ? splitDraftRowPath(slot.path) : null;
        const arrayPath = split ? split.arrayPath : write.path;
        const current = getNested(next[targetSection], arrayPath);
        const arr = Array.isArray(current) ? current : [];
        const rowValue = slot ? finding.value : null;

        // De-dupe: never add a second draft row for the same evidenced value.
        const alreadyPresent = split && arr.some((row) => row && row[split.rowField] === rowValue);
        if (alreadyPresent) continue;

        const newRow = { ...(write.value || {}) };
        if (split && rowValue !== null && rowValue !== undefined) {
          newRow[split.rowField] = rowValue;
        }

        // Not an exact duplicate of an existing row, but if its
        // identifying value (e.g. wound location -- "Coccyx" vs "Sacral/
        // coccygeal area") is a close wording match to one already on the
        // form, this might be the SAME wound described differently by a
        // separate source/extraction pass -- or it might genuinely be a
        // second, distinct wound. Never guess either way: never silently
        // add it as an independent new row, and never silently merge it
        // into the existing one. Surface it for an explicit RN decision
        // (New Wound / Merge Existing Wound / Reject / Modify) instead.
        // A location with NO similarity to anything already on the form
        // (the common case -- e.g. "Coccyx" vs "Right Heel") is clearly a
        // new, independent wound and is still added automatically, same
        // as always.
        if (split && rowValue) {
          const rowValueWords = significantWords(rowValue);
          const fuzzyMatchIdx = arr.findIndex((row) => {
            const existingRowValue = row?.[split.rowField];
            if (!existingRowValue || existingRowValue === rowValue) return false;
            return jaccardOverlap(significantWords(existingRowValue), rowValueWords) >= 0.3;
          });
          if (fuzzyMatchIdx !== -1) {
            woundReviewItems.push({
              section: targetSection,
              arrayPath,
              rowField: split.rowField,
              newRow,
              newValue: rowValue,
              existingRowIndex: fuzzyMatchIdx,
              existingValue: arr[fuzzyMatchIdx][split.rowField],
              concept_code: finding.concept_code,
              source_type: finding.source_type,
              source_excerpt: finding.source_excerpt,
              confidence: finding.confidence,
              finding,
            });
            continue;
          }
        }

        const updatedArr = [...arr, newRow];
        next = { ...next, [targetSection]: setNested(next[targetSection], arrayPath, updatedArr) };
        appliedFields.push({
          section: targetSection,
          path: `${arrayPath}[${updatedArr.length - 1}]`,
          value: newRow,
          concept_code: finding.concept_code,
          finding,
          writeKind: "scalar",
        });
      } else if (write.op === "set_row_field") {
        // Enriches an already-created draft row (e.g. the wound row
        // SKIN_WOUND_PRESENT created) with one more attribute -- it must
        // NEVER create a new row itself (that would fragment one wound
        // into multiple rows). Always targets the LAST row in the array,
        // since concepts are applied in the order the evidence was
        // extracted and a wound's attributes are documented together.
        // Blank-only, same as every other write: never overwrites a value
        // the RN (or an earlier finding) already set.
        const split = splitDraftRowPath(write.path);
        if (!split) continue;
        const current = getNested(next[targetSection], split.arrayPath);
        const arr = Array.isArray(current) ? current : [];
        if (arr.length === 0) continue; // no row exists yet to attach to -- never fabricate one
        const lastIdx = arr.length - 1;
        const lastRow = arr[lastIdx] || {};
        const existingValue = lastRow[split.rowField];
        if (!isBlank(existingValue)) {
          if (existingValue !== write.value) {
            conflicts.push({
              section: targetSection,
              path: `${split.arrayPath}[${lastIdx}].${split.rowField}`,
              existingValue,
              suggestedValue: write.value,
              concept_code: finding.concept_code,
              finding,
            });
          }
          continue;
        }
        const updatedRow = { ...lastRow, [split.rowField]: write.value };
        const updatedArr = [...arr];
        updatedArr[lastIdx] = updatedRow;
        next = { ...next, [targetSection]: setNested(next[targetSection], split.arrayPath, updatedArr) };
        appliedFields.push({
          section: targetSection,
          path: `${split.arrayPath}[${lastIdx}].${split.rowField}`,
          value: write.value,
          concept_code: finding.concept_code,
          finding,
          writeKind: "scalar",
        });
      }
    }

    // A concept's bounded secondary value (e.g. oxygen liters/min, or a
    // free_text_bounded wound row field like `dressing`) is not part of
    // `writes` -- it is the finding's own `value`, written to
    // value_slot.path, blank-only, exactly like a "set"/"set_row_field"
    // write. Skipped here for push_draft_row concepts (handled above as
    // part of the new row, e.g. SKIN_WOUND_PRESENT's `location`).
    const hasOwnRowCreatingWrite = (concept.writes || []).some((w) => w.op === "push_draft_row");
    if (concept.valueSlot && !hasOwnRowCreatingWrite) {
      const rowSplit = splitDraftRowPath(concept.valueSlot.path);
      if (rowSplit) {
        // Row-scoped secondary value (e.g. wounds[].length, wounds[].dressing)
        // -- enrich the LAST existing row only, same rule as set_row_field:
        // never fabricate a row, never overwrite a non-blank value.
        const targetSection = concept.section;
        const sectionData = next[targetSection];
        const current = sectionData ? getNested(sectionData, rowSplit.arrayPath) : null;
        const arr = Array.isArray(current) ? current : [];
        if (arr.length > 0) {
          const lastIdx = arr.length - 1;
          const lastRow = arr[lastIdx] || {};
          const existingValue = lastRow[rowSplit.rowField];
          if (isBlank(existingValue)) {
            const updatedRow = { ...lastRow, [rowSplit.rowField]: finding.value };
            const updatedArr = [...arr];
            updatedArr[lastIdx] = updatedRow;
            next = { ...next, [targetSection]: setNested(sectionData, rowSplit.arrayPath, updatedArr) };
            appliedFields.push({
              section: targetSection,
              path: `${rowSplit.arrayPath}[${lastIdx}].${rowSplit.rowField}`,
              value: finding.value,
              concept_code: finding.concept_code,
              finding,
              writeKind: "scalar",
            });
          } else if (existingValue !== finding.value) {
            conflicts.push({
              section: targetSection,
              path: `${rowSplit.arrayPath}[${lastIdx}].${rowSplit.rowField}`,
              existingValue,
              suggestedValue: finding.value,
              concept_code: finding.concept_code,
              finding,
            });
          }
        }
      } else {
        // Non-row-scoped secondary value of ANY value_slot kind (numeric,
        // free_text_bounded, or date_bounded) -- e.g. oxygen liters/min,
        // a diet-type free-text string, or a catheter insertion date.
        // Blank-only, same rule as "set": never overwrites a value already
        // present (RN-entered or from an earlier finding).
        //
        // NOTE: prior to this fix, this branch only ran for kind ===
        // "numeric" -- every free_text_bounded/date_bounded concept with
        // no row-array path and no FieldWrite (e.g. NUTRITION_DIET_TYPE,
        // GU_URINE_COLOR, RESP_TRACH_TYPE) was silently never applied.
        const targetSection = concept.section;
        const sectionData = next[targetSection];
        if (sectionData) {
          const current = getNested(sectionData, concept.valueSlot.path);
          if (isBlank(current)) {
            next = { ...next, [targetSection]: setNested(sectionData, concept.valueSlot.path, finding.value) };
            appliedFields.push({
              section: targetSection,
              path: concept.valueSlot.path,
              value: finding.value,
              concept_code: finding.concept_code,
              finding,
              writeKind: "scalar",
            });
          } else if (current !== finding.value) {
            conflicts.push({
              section: targetSection,
              path: concept.valueSlot.path,
              existingValue: current,
              suggestedValue: finding.value,
              concept_code: finding.concept_code,
              finding,
            });
          }
        }
      }
    }
  }

  return { formData: next, appliedFields, conflicts, reviewNeeded, woundReviewItems };
}

/**
 * Which RNICA form sections a set of CURRENT findings would target if
 * applied -- WITHOUT touching formData or requiring formData at all. Used
 * to drive the per-section "Ready for RN Review" status badge: a section
 * with pending unresolved structured findings needs the RN's attention
 * even before any Apply is clicked, so this must not require an apply
 * pass to know which sections are affected. Read-only, pure, safe to call
 * on every render for every pending signal.
 */
export function getPendingFindingTargetSections(findings) {
  const sections = new Set();
  for (const finding of findings || []) {
    if (!finding || !finding.concept_code) continue;
    if (finding.assertion_status && finding.assertion_status !== "CURRENT") continue;
    const concept = CONCEPT_REGISTRY[finding.concept_code];
    if (!concept) continue;
    for (const write of concept.writes || []) {
      sections.add(write.section || concept.section);
    }
    // A concept with only a value_slot and no writes (e.g. temperature,
    // or a bounded wound row field like `dressing`) still targets its own
    // section -- must count as pending too, not just concepts with writes.
    if (concept.valueSlot) {
      sections.add(concept.section);
    }
  }
  return sections;
}

// A concept "counts" toward ASSESSMENT_DRAFTED status for a section only
// when at least one of its writes actually landed a value on the real
// form (i.e. appears in `appliedFields`). EVIDENCE_FOUND-only sections
// (evidence harvested, nothing structured populated -- e.g. every finding
// routed to `conflicts` or `reviewNeeded` instead) must never be reported
// as drafted. This helper is what sectionStatuses should consult instead
// of "a note field is non-empty".
export function sectionsWithAppliedStructuredFields(appliedFields) {
  return new Set((appliedFields || []).map((f) => f.section));
}

/**
 * Bulk "Apply All Non-Conflicting" -- runs applyStructuredFindings() once
 * per pending signal (in the order given) and merges EVERY signal's
 * result into the running form state.
 *
 * applyStructuredFindings() already guarantees write-level safety on its
 * own: a "set"/"multi_add"/"push_draft_row" write is only ever committed
 * when the target field is genuinely blank (or, for multi_add/push_draft_row,
 * only adds a new option/row -- it never overwrites or removes anything).
 * Any write that would touch a non-blank field is instead recorded in
 * `conflicts` and left completely alone. Because that separation already
 * happens at the individual-write level, there is no need to roll back an
 * entire signal just because ONE of its bundled findings conflicts --
 * doing so previously discarded genuinely non-conflicting findings (e.g.
 * a new wound row) whenever they happened to be harvested in the same
 * signal as an unrelated duplicate/conflicting mention. A signal is now
 * only marked "skipped" (fully pending RN review) if it produced ZERO
 * applied fields and at least one conflict; a signal that produced BOTH
 * applied fields and conflicts is marked "applied" (its clean writes are
 * kept) while its conflicting writes are still surfaced in
 * `skippedConflicts` for individual RN review.
 *
 * @param {object} formData - the full RNICA form state.
 * @param {Array} signals - pending structured-findings signals, each with
 *   `.id` and `.structured_findings` (as returned by
 *   list_pending_structured_findings / GET .../intelligence).
 * @param {object} [initialFormData] - see applyStructuredFindings; forwarded
 *   unchanged to every per-signal apply pass so the untouched-boolean-
 *   section check is evaluated against the SAME pristine baseline for
 *   every signal in the batch, not a per-signal moving target.
 * @returns {{
 *   formData: object,
 *   appliedSignalIds: string[],
 *   skippedSignalIds: string[],
 *   appliedFields: Array,
 *   appliedFieldsBySignal: Record<string, Array>,
 *   skippedConflicts: Array,
 * }}
 */
export function applyAllNonConflicting(formData, signals, initialFormData) {
  let next = formData;
  const appliedSignalIds = [];
  const skippedSignalIds = [];
  const appliedFields = [];
  const appliedFieldsBySignal = {};
  const skippedConflicts = [];
  const skippedWoundReviewItems = [];

  for (const signal of signals || []) {
    if (!signal || !signal.id) continue;
    const {
      formData: candidate,
      appliedFields: candidateApplied,
      conflicts: candidateConflicts,
      woundReviewItems: candidateWoundReviewItems,
    } = applyStructuredFindings(next, signal.structured_findings || [], initialFormData);

    // Always merge -- applyStructuredFindings() never overwrites a
    // non-blank field itself, so merging is safe even when this signal
    // also produced conflicts for its OTHER findings.
    next = candidate;

    if (candidateConflicts.length > 0) {
      skippedConflicts.push(
        ...candidateConflicts.map((c) => ({ ...c, signal_id: signal.id }))
      );
    }
    if (candidateWoundReviewItems.length > 0) {
      skippedWoundReviewItems.push(
        ...candidateWoundReviewItems.map((w) => ({ ...w, signal_id: signal.id }))
      );
    }

    const hasUnresolved = candidateConflicts.length > 0 || candidateWoundReviewItems.length > 0;
    if (candidateApplied.length > 0) {
      // At least one finding in this signal genuinely wrote a value --
      // count the signal as applied even if some of its other findings
      // conflicted (or produced an ambiguous wound match) and are still
      // pending individual RN review.
      appliedSignalIds.push(signal.id);
      appliedFieldsBySignal[signal.id] = candidateApplied;
      appliedFields.push(...candidateApplied);
    } else if (hasUnresolved) {
      // Nothing applied and something conflicted (or an ambiguous wound
      // match needs a decision) -- this signal is entirely pending RN
      // review.
      skippedSignalIds.push(signal.id);
    } else {
      // Nothing to write (e.g. every finding was HISTORICAL/NEGATED and
      // routed to reviewNeeded) -- still counts as "cleanly reviewed",
      // not a conflict, so it's fine to mark applied/reviewed.
      appliedSignalIds.push(signal.id);
      appliedFieldsBySignal[signal.id] = [];
    }
  }

  return {
    formData: next,
    appliedSignalIds,
    skippedSignalIds,
    appliedFields,
    appliedFieldsBySignal,
    skippedConflicts,
    skippedWoundReviewItems,
  };
}

// Combine an existing free-text value with a suggested one into a single
// human-readable string, e.g. "Pre Dialysis" + "Diabetic Consistent
// Carbohydrate" -> "Pre Dialysis, Diabetic Consistent Carbohydrate". Used
// only by the RN-driven "Merge" action below -- never by automatic Apply,
// which must never guess at combining two values on its own.
function mergeTextValues(existingValue, suggestedValue) {
  const existingStr = existingValue === null || existingValue === undefined ? "" : String(existingValue);
  const suggestedStr = suggestedValue === null || suggestedValue === undefined ? "" : String(suggestedValue);
  if (!existingStr) return suggestedStr;
  if (!suggestedStr) return existingStr;
  // Never duplicate a fragment that's already part of the combined string
  // (e.g. re-merging the same conflict twice, or the suggestion already
  // being a substring of what's there).
  if (existingStr.toLowerCase().includes(suggestedStr.toLowerCase())) return existingStr;
  return `${existingStr}, ${suggestedStr}`;
}

/**
 * Resolve a single field-level conflict surfaced by applyAllNonConflicting
 * (an { section, path, existingValue, suggestedValue, concept_code, finding,
 * signal_id } entry) via an explicit RN decision. This is the ONLY place a
 * conflicting field is ever written after the fact -- Apply-All itself
 * never overwrites a non-blank field; a human must choose one of:
 *
 *   - "accept": overwrite the field with the AI-suggested value outright.
 *   - "reject": keep the existing value; nothing is written (the RN has
 *     decided the suggestion does not apply / is not correct).
 *   - "modify": overwrite the field with an RN-typed value that may differ
 *     from both the existing and suggested values.
 *   - "merge" (free-text fields only): combine existing + suggested into a
 *     single value via mergeTextValues, for cases where both are
 *     legitimate, non-contradicting fragments of the same fact.
 *
 * Never usable on boolean fields for "merge" (there's nothing to combine)
 * -- callers should not offer that action for a boolean conflict.
 *
 * @returns {{ formData: object, resolvedValue: any, path: string, section: string } | null}
 *   null if the action is invalid for this conflict (e.g. merge on a boolean).
 */
export function resolveFieldConflict(formData, conflict, action, customValue) {
  const { section, path, existingValue, suggestedValue } = conflict;
  const sectionData = formData?.[section] || {};
  let resolvedValue;
  if (action === "reject") {
    return { formData, resolvedValue: existingValue, path, section, noop: true };
  } else if (action === "accept") {
    resolvedValue = suggestedValue;
  } else if (action === "modify") {
    resolvedValue = customValue;
  } else if (action === "merge") {
    if (typeof existingValue === "boolean" || typeof suggestedValue === "boolean") return null; // merging booleans is meaningless
    resolvedValue = mergeTextValues(existingValue, suggestedValue);
  } else {
    return null;
  }
  const nextFormData = { ...formData, [section]: setNested(sectionData, path, resolvedValue) };
  return { formData: nextFormData, resolvedValue, path, section, noop: false };
}

/**
 * Resolve a single wound-review item (a candidate wound row whose location
 * fuzzily matched an existing row -- see applyStructuredFindings'
 * push_draft_row branch) via an explicit RN decision. This is the ONLY
 * place an ambiguous wound candidate is ever committed -- Apply-All never
 * silently adds it as a new row NOR silently folds it into an existing
 * one.
 *
 *   - "new_wound": the RN confirms this is a genuinely separate wound.
 *     Adds it as its own new row, exactly as an unambiguous new-location
 *     finding would have been added automatically.
 *   - "merge_existing": the RN confirms this is the SAME wound, just
 *     worded differently by a different source/extraction pass. Enriches
 *     the existing row with any blank fields the candidate provides
 *     (never overwrites a field the existing row already has a value
 *     for) -- the existing row's location text is kept as the RN has
 *     already validated it, only newly-offered attributes are folded in.
 *   - "reject": the candidate is discarded entirely -- not added as a row,
 *     not merged into anything. Nothing is written.
 *   - "modify": the RN provides a corrected location string for a NEW row
 *     (e.g. neither the existing wording nor the suggested wording was
 *     quite right) -- added as an additional, distinct row.
 *
 * @returns {{ formData: object, section: string, arrayPath: string, noop: boolean } | null}
 *   null if the action is not recognized.
 */
export function resolveWoundReview(formData, item, action, customValue) {
  const { section, arrayPath, rowField, newRow, newValue } = item;
  const sectionData = formData?.[section] || {};
  const current = getNested(sectionData, arrayPath);
  const arr = Array.isArray(current) ? current : [];

  if (action === "reject") {
    return { formData, section, arrayPath, noop: true };
  }

  if (action === "new_wound" || action === "modify") {
    const rowToAdd = { ...newRow };
    if (action === "modify") {
      rowToAdd[rowField] = customValue;
    }
    const updatedArr = [...arr, rowToAdd];
    const nextFormData = { ...formData, [section]: setNested(sectionData, arrayPath, updatedArr) };
    return { formData: nextFormData, section, arrayPath, rowIndex: updatedArr.length - 1, row: rowToAdd, noop: false };
  }

  if (action === "merge_existing") {
    const { existingRowIndex } = item;
    if (existingRowIndex == null || !arr[existingRowIndex]) return null;
    const existingRow = arr[existingRowIndex];
    // Fold in any attribute the candidate row provides that the existing
    // row doesn't already have -- never overwrite something already
    // documented, and never touch the existing row's own location text
    // (the RN has just confirmed it's the correct description of this
    // wound; the candidate's differently-worded location is discarded,
    // not written).
    const mergedRow = { ...existingRow };
    for (const [key, value] of Object.entries(newRow || {})) {
      if (key === rowField) continue; // never overwrite the validated location
      if (isBlank(mergedRow[key]) && !isBlank(value)) {
        mergedRow[key] = value;
      }
    }
    const updatedArr = [...arr];
    updatedArr[existingRowIndex] = mergedRow;
    const nextFormData = { ...formData, [section]: setNested(sectionData, arrayPath, updatedArr) };
    return { formData: nextFormData, section, arrayPath, rowIndex: existingRowIndex, row: mergedRow, noop: false };
  }

  return null;
}

// ---------------------------------------------------------------------------
// Classification engine (RN review workflow)
// ---------------------------------------------------------------------------
//
// A field-level conflict left over from applyAllNonConflicting is NOT
// automatically a "software conflict" requiring developer attention. Most
// are one of:
//
//   2. Already Present   -- the suggestion is a strictly vaguer/less
//      specific restatement of what the chart already has. Nothing new.
//   3. Duplicate          -- the same fact, re-worded/re-truncated across
//      separate extraction passes (chunking overlap, re-harvest, etc.).
//   4. Enrichment         -- multiple genuinely distinct, non-contradicting
//      fragments of ONE compound clinical order competing for a single
//      free-text field (e.g. a diet order split into base diet + texture
//      + carb-control by the extractor). Needs an RN Merge, not a silent
//      auto-combine.
//   5. Clinical Discrepancy -- two genuinely different, mutually exclusive
//      clinical facts (a boolean flip, or a severity/status change like
//      hemiparesis -> hemiplegia). Only a clinician can adjudicate.
//   6. Safety-Critical    -- any of the above, but for a concept whose
//      section/code is safety-relevant (wounds, falls, aspiration,
//      allergies, oxygen). Same actions as 4/5, but routed to an urgent
//      queue instead of the regular one.
//
// Category 1 (Auto Apply) and Category 7 (Technical Error) are NOT
// produced here -- Auto Apply already happens upstream in
// applyAllNonConflicting (any blank/already-satisfied field never reaches
// this list at all), and Technical Error is a code-path/schema defect
// (e.g. the diet/supplement one-field-many-fragments registry mismatch
// this classifier works around for now), not a per-finding classification
// -- those are tracked and fixed separately in the concept registry.
//
// IMPORTANT, and deliberately conservative: distinguishing "these two
// different strings are complementary fragments of one order" (Enrichment)
// from "these two different strings are a genuine contradiction" (Clinical
// Discrepancy) is NOT something a generic string heuristic can safely
// decide -- "Right hemiparesis" vs "Right hemiplegia" look just as
// "different" as "Pre Dialysis" vs "Diabetic Consistent Carbohydrate" by
// any edit-distance/overlap measure, but one is a contradiction and the
// other isn't. Rather than guess and silently misclassify a real clinical
// contradiction as safe-to-merge, only concepts explicitly listed here as
// "combinable" (i.e. known, by design, to describe simultaneous rather
// than mutually-exclusive facts) are ever classified as Enrichment on that
// basis. Everything else defaults to Clinical Discrepancy, which always
// requires an explicit RN decision -- the safe default.
const COMBINABLE_FREE_TEXT_CONCEPTS = new Set(["NUTRITION_DIET_TYPE", "NUTRITION_SUPPLEMENTS"]);

const SAFETY_CRITICAL_SECTIONS = new Set(["safety"]);
const SAFETY_CRITICAL_CODE_KEYWORDS = ["WOUND", "PRESSURE_INJURY", "FALL_RISK", "ASPIRATION", "ALLERGY", "OXYGEN"];

function isSafetyCriticalConcept(conceptCode, conceptEntry) {
  if (conceptEntry?.section && SAFETY_CRITICAL_SECTIONS.has(conceptEntry.section)) return true;
  const code = conceptCode || "";
  return SAFETY_CRITICAL_CODE_KEYWORDS.some((kw) => code.includes(kw));
}

/**
 * Classify a single field-level conflict (from applyAllNonConflicting's
 * skippedConflicts / structuredFieldConflicts) into the RN-facing category
 * model above, BEFORE it is ever shown to a reviewer.
 *
 * @param {object} conflict - { section, path, existingValue, suggestedValue, concept_code }
 * @param {object} [conceptEntry] - the CONCEPT_REGISTRY entry for concept_code, if available (used only for section-based safety-critical detection).
 * @returns {{ category: number, label: string, rnReviewRequired: boolean, urgent: boolean, queue: "auto_resolved"|"rn_review"|"urgent_rn_review", reason: string }}
 */
export function classifyConflict(conflict, conceptEntry) {
  const { existingValue, suggestedValue, concept_code } = conflict;
  const urgent = isSafetyCriticalConcept(concept_code, conceptEntry);
  const isBooleanConflict = typeof existingValue === "boolean" || typeof suggestedValue === "boolean";

  if (isBooleanConflict) {
    return urgent
      ? { category: 6, label: "Safety-Critical", rnReviewRequired: true, urgent: true, queue: "urgent_rn_review", reason: "Boolean safety-relevant fact disagrees between chart and source; requires clinician confirmation." }
      : { category: 5, label: "Clinical Discrepancy", rnReviewRequired: true, urgent: false, queue: "rn_review", reason: "Chart and source document disagree on a yes/no clinical fact." };
  }

  const existingStr = existingValue == null ? "" : String(existingValue).trim();
  const suggestedStr = suggestedValue == null ? "" : String(suggestedValue).trim();

  if (!existingStr || !suggestedStr) {
    // One side is empty -- applyAllNonConflicting only reaches "conflict"
    // when the field is non-blank, so this should be rare, but if it
    // happens there's nothing to compare; treat conservatively as a
    // discrepancy needing review rather than guessing.
    return { category: 5, label: "Clinical Discrepancy", rnReviewRequired: true, urgent, queue: urgent ? "urgent_rn_review" : "rn_review", reason: "Unable to compare values automatically." };
  }

  const existingLower = existingStr.toLowerCase();
  const suggestedLower = suggestedStr.toLowerCase();

  if (existingLower === suggestedLower) {
    return { category: 3, label: "Duplicate", rnReviewRequired: false, urgent: false, queue: "auto_resolved", reason: "Identical value re-detected; safe to auto-resolve." };
  }

  const existingWords = significantWords(existingStr);
  const suggestedWords = significantWords(suggestedStr);
  const overlap = jaccardOverlap(existingWords, suggestedWords);

  // High word overlap (differing only by whitespace/truncation/minor
  // rewording) = the same underlying fact restated, not a new fact.
  if (overlap >= 0.5) {
    return { category: 3, label: "Duplicate", rnReviewRequired: false, urgent: false, queue: "auto_resolved", reason: "Near-identical restatement of the same fact (high word overlap); safe to auto-resolve." };
  }

  const existingHasNumber = /\d/.test(existingStr);
  const suggestedHasNumber = /\d/.test(suggestedStr);

  // Existing already has a specific, measurable fact; the suggestion is a
  // generic restatement with no new number/detail -- adds nothing.
  if (existingHasNumber && !suggestedHasNumber) {
    return { category: 2, label: "Already Present", rnReviewRequired: false, urgent: false, queue: "auto_resolved", reason: "Suggested value is a vaguer restatement with no new specific detail than what the chart already has." };
  }

  if (urgent) {
    return { category: 6, label: "Safety-Critical", rnReviewRequired: true, urgent: true, queue: "urgent_rn_review", reason: "Safety-relevant field with a genuinely differing value; requires urgent clinician review." };
  }

  if (COMBINABLE_FREE_TEXT_CONCEPTS.has(concept_code)) {
    return { category: 4, label: "Enrichment", rnReviewRequired: true, urgent: false, queue: "rn_review", reason: "Distinct, non-contradicting fragment of a known compound order (this field type combines multiple simultaneous facts); safe to offer Merge." };
  }

  // Default, deliberately conservative: two genuinely different values on
  // a field NOT known to hold multiple simultaneous facts. Do not assume
  // they're compatible -- require an explicit clinician decision.
  return { category: 5, label: "Clinical Discrepancy", rnReviewRequired: true, urgent: false, queue: "rn_review", reason: "Two distinct values for a single-fact field; only a clinician can determine which (if either) is correct." };
}

/**
 * Group a full list of field-level conflicts by classification category,
 * for the "Nurse Queue Metrics" summary (never "16 Pending" -- always
 * broken out by what kind of review, if any, each item actually needs).
 */
export function summarizeConflictsByCategory(conflicts, conceptRegistry) {
  const summary = {
    clinicalDiscrepancies: [],
    enrichmentSuggestions: [],
    safetyCritical: [],
    alreadyPresent: [],
    duplicatesAutoResolved: [],
  };
  for (const c of conflicts) {
    const classification = classifyConflict(c, conceptRegistry?.[c.concept_code]);
    const entry = { ...c, classification };
    if (classification.category === 6) summary.safetyCritical.push(entry);
    else if (classification.category === 5) summary.clinicalDiscrepancies.push(entry);
    else if (classification.category === 4) summary.enrichmentSuggestions.push(entry);
    else if (classification.category === 2) summary.alreadyPresent.push(entry);
    else if (classification.category === 3) summary.duplicatesAutoResolved.push(entry);
  }
  return summary;
}


