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
  // NOTE: `false` is intentionally NOT treated as blank. RNICA boolean
  // presence fields (e.g. heartFailurePresent, contracturesPresent,
  // skinConditionsPresent) default to `false`, and an RN who has actually
  // examined the patient and left a box unchecked has made a real clinical
  // assertion -- it must never be silently flipped to `true` by an AI
  // suggestion. Every boolean-presence concept therefore always routes
  // through the conflict path below for explicit RN confirmation, whether
  // the field is untouched-default or RN-confirmed-false. Only a truly
  // unset field (null/undefined/""/[]) is eligible for blank-only auto-apply.
  return false;
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
 * @returns {{
 *   formData: object,
 *   appliedFields: Array<{section, path, value, concept_code, finding}>,
 *   conflicts: Array<{section, path, existingValue, suggestedValue, concept_code, finding}>,
 *   reviewNeeded: Array<object>,
 * }}
 */
export function applyStructuredFindings(formData, findings) {
  let next = formData;
  const appliedFields = [];
  const conflicts = [];
  const reviewNeeded = [];

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
        if (!isBlank(current)) {
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
        appliedFields.push({ section: targetSection, path: write.path, value: write.value, concept_code: finding.concept_code, finding });
      } else if (write.op === "multi_add") {
        const current = getNested(next[targetSection], write.path);
        const arr = Array.isArray(current) ? current : [];
        if (arr.includes(write.value)) continue; // already checked -- nothing to do, never duplicated
        const updatedArr = [...arr, write.value];
        next = { ...next, [targetSection]: setNested(next[targetSection], write.path, updatedArr) };
        appliedFields.push({ section: targetSection, path: write.path, value: write.value, concept_code: finding.concept_code, finding });
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
        });
      }
    }

    // A concept's bounded numeric secondary value (e.g. oxygen liters/min)
    // is not part of `writes` -- it is the finding's own `value`, written
    // to value_slot.path within the concept's own section, blank-only,
    // exactly like a "set" write. Skipped here for push_draft_row concepts
    // (handled above as part of the new row) and free_text_bounded
    // wound-location concepts (same reason).
    if (concept.valueSlot && concept.valueSlot.kind === "numeric") {
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

  return { formData: next, appliedFields, conflicts, reviewNeeded };
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
 * per pending signal (in the order given), but only KEEPS a signal's
 * changes if that signal produced zero conflicts. A signal that produces
 * even one conflict is left completely untouched (its writes are rolled
 * back, not partially applied) and reported in `skippedSignals` for the
 * RN to review individually -- this keeps the "never overwrite RN data"
 * guarantee intact while letting a nurse clear an entire batch of clean,
 * no-conflict findings in one click instead of clicking Apply N times.
 *
 * @param {object} formData - the full RNICA form state.
 * @param {Array} signals - pending structured-findings signals, each with
 *   `.id` and `.structured_findings` (as returned by
 *   list_pending_structured_findings / GET .../intelligence).
 * @returns {{
 *   formData: object,
 *   appliedSignalIds: string[],
 *   skippedSignalIds: string[],
 *   appliedFields: Array,
 *   appliedFieldsBySignal: Record<string, Array>,
 *   skippedConflicts: Array,
 * }}
 */
export function applyAllNonConflicting(formData, signals) {
  let next = formData;
  const appliedSignalIds = [];
  const skippedSignalIds = [];
  const appliedFields = [];
  const appliedFieldsBySignal = {};
  const skippedConflicts = [];

  for (const signal of signals || []) {
    if (!signal || !signal.id) continue;
    const { formData: candidate, appliedFields: candidateApplied, conflicts: candidateConflicts } =
      applyStructuredFindings(next, signal.structured_findings || []);

    if (candidateConflicts.length > 0) {
      // Leave this signal's fields exactly as they were -- do not merge
      // `candidate` into `next` -- and surface why for the RN.
      skippedSignalIds.push(signal.id);
      skippedConflicts.push(
        ...candidateConflicts.map((c) => ({ ...c, signal_id: signal.id }))
      );
      continue;
    }

    next = candidate;
    if (candidateApplied.length > 0) {
      appliedSignalIds.push(signal.id);
      appliedFieldsBySignal[signal.id] = candidateApplied;
      appliedFields.push(...candidateApplied);
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

