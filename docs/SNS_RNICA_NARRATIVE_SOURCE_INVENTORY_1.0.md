# SNS RNICA Narrative Source Inventory 1.0 — Phase 1, Deliverable 5

**STATUS: FROZEN — ACCEPTED COMPLETE (2026-08-21)**
No further edits except factual corrections.

> **HOPE GOVERNANCE RULE**
>
> RNICA is the authoritative assessment. HOPE is not a separate
> clinician-facing form. All HOPE reporting elements originate from
> RNICA fields through approved mapping, derivation, and validation
> rules. No duplicate clinician documentation shall be required solely
> for HOPE reporting.

## INVENTORY RULE

This document records narrative/free-text generation as it actually
exists today. It does not modify any prior frozen deliverable and does
not propose new narrative features.

Source of truth: `RNICA.jsx` (`DeclineTrackerCard`, lines 2001-2162;
static field defaults, lines 304-741) and
`GET /patients/{patientId}/performance-history` (`backend/app/api/patients.py`).

## Key finding

**RNICA has exactly one computed/generated narrative in the current
implementation — a single decline-summary sentence — and it is
client-side only, never persisted, and never sent to the backend.**
Every other long-form text field in RNICA is a plain manually-typed
textarea with no calculation behind it. There is no backend narrative
generation service, no template engine, and no AI/LLM-authored text
anywhere in the current RNICA flow (the `intelligence` endpoint,
`GET /visits/rnica/{id}/intelligence`, produces separate
finding/recommendation text — documented below as a related-but-distinct
source, since it is not inserted into any RNICA narrative field
automatically).

## 1. The one generated narrative: Decline Summary (`DeclineTrackerCard`)

| Attribute | Value |
|---|---|
| Narrative Section | "Change Since Last Assessment" panel, rendered inline (not tied to one specific `form_data` path; appears wherever `DeclineTrackerCard` is mounted) |
| Component | `DeclineTrackerCard` (`RNICA.jsx:2001-2162`) |
| Computed value | `summaryText` (`RNICA.jsx:2080-2091`, `useMemo`) |
| Source Fields (current assessment) | `performanceStatus.pps`, `performanceStatus.kps`, `performanceStatus.fast`, `vitals.weight` (passed into the component as `performanceData`/`weight` props) |
| Evidence Fields (prior assessment) | `priorEntry` — most recent **other** assessment from `GET /patients/{patientId}/performance-history` (`fetchPerformanceHistory`, `RNICA.jsx:58,2012`), fields `pps`, `kps`, `fast_stage`, `weight`, `date` |
| Calculation | For each of PPS, KPS, FAST, Weight: compute `delta = current - prior` (FAST delta sign is inverted — higher stage index = more decline); classify `trend` as `decline`/`improvement`/`stable`; Weight additionally computes `pctChange = (delta / priorWeight) * 100` |
| Generated Content Dependencies | Only `trend === "decline"` rows are included in the sentence. If **no** metric declined, `summaryText` is an empty string and the whole panel/button renders nothing (`RNICA.jsx:2081,2083`) |
| Output text pattern | `"Documented decline since prior assessment on {date}: {metric} declined from {from} to {to}; weight decreased from {from} to {to} ({pct}% loss)."` — see exact template at `RNICA.jsx:2084-2090` |
| Destination | **Not auto-inserted anywhere.** A "Copy decline summary for LCD Narrative" button (`RNICA.jsx` "Copied!" label) copies `summaryText` to the OS clipboard only (`navigator.clipboard.writeText`, `handleCopy`, `RNICA.jsx:2093-2099`). The RN must manually paste it into `narrativeAndTrajectory.lcdEligibilityNarrative` (Section 25/28 area) themselves — there is no code path that writes it into `form_data` automatically |
| Persistence | **None.** `summaryText` is a `useMemo` value that exists only in the component's render tree; it is never written to `form_data`, never sent in any save/update payload, and is recomputed fresh every time the component mounts/re-renders from live API data |

## 2. Manually-authored long-form text fields (no calculation — plain user-typed narrative)

These are the only other multi-line "narrative-shaped" fields in RNICA
(`textarea` inputs with `rows >= 4`). None of them have any generated or
pre-filled content beyond a static boilerplate default on one field:

| Field | Section | Default / Placeholder | Notes |
|---|---|---|---|
| `narrativeAndTrajectory.lcdEligibilityNarrative` | Narrative & Disease Trajectory (Section 5 subsection) | Placeholder text only ("Document the patient's terminal illness, functional decline trajectory, and LCD eligibility criteria...") | Intended paste target for the Decline Summary above; not enforced or auto-populated |
| `neurological.functionalDeclineNotes` | Neurological | empty string | Free text, no source-field linkage in code |
| `neurological.notes` | Neurological | empty string | Free text |
| `skin.notes` | Skin/Wounds | empty string | Free text |
| `admissionsOrder.admissionStatement` | Admissions Order | **Static boilerplate default** (fixed legal/clinical attestation sentence, `RNICA.jsx:675` — same text for every patient) | Not computed from assessment data; it is a fixed default string set once in `defaultFormData` and then freely editable |
| `finalization.responseToInterventions.initialResponseSummary` | Finalization | empty string | Free text |

None of the fields in table 2 read any other `form_data` field as a
source — they are pure user input with no evidence-linkage in the
current code.

## 3. Related-but-not-a-RNICA-narrative: the Intelligence endpoint

`GET /visits/rnica/{assessment_id}/intelligence` (documented fully in
`SNS_RNICA_API_MAPPING_1.0` §1.6) produces `findings`, `recommendations`,
and an `evidence.assessment_text` summary string via
`build_rnica_intelligence()` / `_collect_findings()`
(`backend/app/services/rnica_intelligence.py`). This is generated text
derived from `form_data` plus `gather_patient_evidence()` (clinical-note
text), but:
- it is displayed in a separate insight/summary panel, not written into
  any `form_data` narrative field;
- it is explicitly labeled `"mode": "recommendation_only"` in its own
  output and is never persisted;
- it is not reachable unless `currentAssessmentId` is already set
  (`RNICA.jsx:5459`, `756-757`).

It is recorded here for completeness since it is the only other
text-generation code path touched by an RNICA screen, but it is not part
of the RNICA narrative/documentation record itself.

## 4. HOPE-derived evidence support (which narratives support HOPE-derived elements)

| HOPE Item(s) | Supporting narrative/evidence in RNICA | Status |
|---|---|---|
| M1190 (Skin Conditions gate), M1195/M1200 (types/treatments) | None — `skin.notes` is free text with no HOPE-item wiring | No narrative evidence link exists |
| J0050 (Death is Imminent) | None — `imminentDeath` section has no long-form narrative field; only structured yes/no + `neurological.functionalDeclineNotes` is generic, not scoped to J0050 | No dedicated narrative evidence link |
| F2000/F2100/F2200 (Advanced Care Planning) | None — ACP fields are structured (dropdowns/checkboxes), no supporting free-text justification field exists | No narrative evidence link |
| I0010 / HOPE comorbidities (I0100-I8005) | `lcdEligibilityNarrative` is the closest — it is meant to document "terminal illness, functional decline trajectory, and LCD eligibility" (placeholder text), and can be manually populated from the Decline Summary (§1) — but this is a **manual, optional** link, not a system-enforced one | Weak/manual narrative evidence link only |
| Functional decline (PPS/KPS/FAST/Weight — feeds M1190-adjacent decline documentation and LCD eligibility broadly, not a single HOPE item) | `summaryText` (Decline Summary, §1) is the only genuinely computed evidence text in RNICA, and it is explicitly a decline-trend narrative | Confirmed, but not persisted (see §1) |

No RNICA narrative field is **required** to support a HOPE item before
lock; the only field that functions as HOPE-facing narrative evidence at
all (`lcdEligibilityNarrative`) is optional and unvalidated (see
`SNS_RNICA_VALIDATION_INVENTORY_1.0` — it does not appear in the required
or conditional rule list).

## Status

**Deliverable #5 (`SNS_RNICA_NARRATIVE_SOURCE_INVENTORY_1.0`) complete.**
One computed narrative (Decline Summary) fully traced source-field to
output-text to destination; five plain manually-authored long-form
fields catalogued with their defaults; the Intelligence endpoint's
generated text recorded as a related-but-separate source. No hidden
narrative-generation code paths were found beyond these.

No changes made to any frozen artifact. No code changes are authorized
by this document.

Next: Deliverable #6 — `SNS_RNICA_AUDIT_INVENTORY_1.0`.
