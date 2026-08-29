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
        const blank = isUntouchedBooleanDefault ? true : isBlank(current);
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

  return { formData: next, appliedFields, conflicts, reviewNeeded };
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

  for (const signal of signals || []) {
    if (!signal || !signal.id) continue;
    const { formData: candidate, appliedFields: candidateApplied, conflicts: candidateConflicts } =
      applyStructuredFindings(next, signal.structured_findings || [], initialFormData);

    // Always merge -- applyStructuredFindings() never overwrites a
    // non-blank field itself, so merging is safe even when this signal
    // also produced conflicts for its OTHER findings.
    next = candidate;

    if (candidateConflicts.length > 0) {
      skippedConflicts.push(
        ...candidateConflicts.map((c) => ({ ...c, signal_id: signal.id }))
      );
    }

    if (candidateApplied.length > 0) {
      // At least one finding in this signal genuinely wrote a value --
      // count the signal as applied even if some of its other findings
      // conflicted and are still pending individual RN review.
      appliedSignalIds.push(signal.id);
      appliedFieldsBySignal[signal.id] = candidateApplied;
      appliedFields.push(...candidateApplied);
    } else if (candidateConflicts.length > 0) {
      // Nothing applied and something conflicted -- this signal is
      // entirely pending RN review.
      skippedSignalIds.push(signal.id);
    } else {
      // Nothing to write (e.g. every finding was HISTORICAL/NEGATED and
      // routed to reviewNeeded) -- still counts as "cleanly reviewed",
      // not a conflict, so it's fine to mark applied/reviewed.
      appliedSignalIds.push(signal.id);
      appliedFieldsBySignal[signal.id] = [];
    }
  }

  return { formData: next, appliedSignalIds, skippedSignalIds, appliedFields, appliedFieldsBySignal, skippedConflicts };
}

