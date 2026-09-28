# RNICA Neurological & Cardiovascular Workflow Correction

Status: Artifacts 1-3 delivered; Artifact 4 (implementation) delivered for the
**presentation-only subset only** (no field IDs, database paths, HOPE
mappings, SFV mappings, POC bindings, or stored option values changed).
Everything requiring a new field or a changed/consolidated option vocabulary
is listed in "Open Schema Questions" and is **not implemented** pending
owner approval, per the directive's Section 15 ("GitHub is not authorized to
decide which new fields to add / which values are clinically equivalent").

## Why this split

Reading `structuredFindingRegistry.generated.js` (AI/evidence-harvesting
layer) confirms every current option string (e.g. `pulseQuality: "Tachycardia"`,
`edema.location: "Unilateral LE"`, `heartFailureType: "Systolic"`) is a live
write target for evidence harvesting, cross-checked by
`applyStructuredFindings.test.js`. Renaming, splitting, or regrouping an
option set (e.g. replacing `pulseQuality`'s flat 9-option list with grouped
Rhythm/Quality/Rate/Site controls, or `heartFailureType`'s Systolic/Diastolic
removal) requires regenerating that registry and its tests in the same
change -- this is exactly the kind of schema change the directive says must
be listed separately and approved first, not decided unilaterally during a
presentation pass.

---

## Artifact 1: Existing Field Matrix

### Neurological (`sectionKey: "neurological"`)

| Display Label | Field ID (path) | Stored Type | Current Controlled Values | Select Type | HOPE | SFV | POC | Report/Export | Historical Concern | Proposed Group | Proposed Trigger | Decision |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Level of Consciousness | `consciousness` | string | Alert, Lethargic, Obtunded, Stuporous, Comatose, Awake, Minimally responsive, Coma | single (radio) | none | none | card-level | none found | Alert/Awake and Lethargic/Obtunded/Stuporous/Comatose/Coma overlap in meaning | Cognitive Status | none | **Keep as-is now**; consolidation is a schema question (see below) |
| Oriented to Time/Place/Person/Situation | `orientation.time/.place/.person/.situation` | boolean x4 | n/a (checkbox) | multi (independent checkboxes) | none | none | card-level | none found | none | Cognitive Status | none | Keep; add derived read-only "Oriented x N" summary (presentation only) |
| Disoriented | `orientation.disoriented` | boolean | n/a | checkbox | none | none | card-level | none found | **Conflicts with the 4 oriented-to-X checkboxes today** | Cognitive Status | none | **Fixed this pass**: mutually exclusive at the interaction layer |
| Cognition Assessment | `cognition` | string (free text) | n/a | input | none | none | card-level | used by `computeBodySystemFindings` | none | Cognitive Status | none | Keep |
| Symptoms / Demeanor | `symptomsDemeanor` | array | Anxiety, Agitation, Peaceful, Confused, Angry, Restless, Depressed, Seizure, Combative, Sundowning, Tremors/twitching, Other | multi (checkboxGroup) | none | none | card-level | none found | Peaceful mixed into abnormal-symptom multiselect | Emotional/Behavioral Symptoms | none | Keep now; regrouping Peaceful into a separate demeanor field is a schema question |
| Delirium | `delirium` | boolean | n/a | checkbox | none | none | card-level | none found | none | Emotional/Behavioral Symptoms | none | Keep |
| Seizure History | `seizureHistory` | boolean | n/a | checkbox | none | none | card-level | none found | none | Emotional/Behavioral Symptoms | none | Keep |
| Psychiatric History | `psychiatricHistoryType` | array | None, Bipolar disorder, OCD, Schizophrenia, Depression, Other | multi (checkboxGroup) | none | none | card-level | none found | none | Emotional/Behavioral Symptoms | **Fixed this pass**: notes now hide unless a non-empty selection exists | Keep values; a None/History-present/Unknown gate is a schema question |
| Psychiatric History Notes | `psychiatricHistory` | string | n/a | textarea | none | none | card-level | none found | none | Emotional/Behavioral Symptoms | psychiatricHistoryType has a value | Keep |
| N0500 Repetition / N0510 Recall / N0520 Temporal Orientation | `hopeItems.n0500/.n0510/.n0520` | string ("0"-"3") | CMS BIMS values | single (select) | **N0500, N0510, N0520 -- official, exported via `hopeReportMapper.js`/`HopeReport.jsx`** | none | card-level | **Yes -- official HOPE export** | none | Dementia Findings (BIMS) | none | **Do not touch values/labels** |
| Motor Deficit Present | `motorDeficit` | boolean | n/a | checkbox | none | none | card-level | none found | none | Neuromuscular Function | none | Keep |
| Affected Side | `affectedSide` | string | Left, Right, Bilateral | single (radio) | none | none | card-level | none found | none | Neuromuscular Function | **Fixed this pass**: hidden until Motor Deficit Present is checked | Keep values |
| Deficit Type | `deficitType` | array | Hemiparesis, Hemiplegia, Paraparesis, Quadriparesis, Other | multi (checkboxGroup) | none | none | card-level | none found | none | Neuromuscular Function | **Fixed this pass**: hidden until Motor Deficit Present is checked | Keep values |
| Balance | `balance` | string | Steady, Unsteady, Unable to stand, Normal, Impaired | single (radio) | none | none | card-level | none found | **Steady/Normal and Unsteady/Impaired overlap** | Neuromuscular Function | none | **Keep as-is now**; consolidation is a schema question |
| Communication | `communication` | string | Clear, Impaired, Unable, Normal, Aphasia, Slurred speech, Speech limited to six or fewer intelligible words, Other | single (radio) | none | none | card-level | none found | **Clear/Normal overlap; Unable/nonverbal ambiguity** | Sensory Function | none | **Keep as-is now**; consolidation is a schema question |
| Hearing | `hearing` | string | Adequate, Impaired, Deaf, Hearing aid | single (radio) | none | none | card-level | none found | "Hearing aid" mixed into hearing-status list (device vs. status) | Sensory Function | none | **Keep as-is now**; splitting device from status is a schema question |
| Vision | `vision` | string | Adequate, Impaired, Blind, Corrective lenses | single (radio) | none | none | card-level | none found | same pattern as Hearing | Sensory Function | none | **Keep as-is now**; schema question |
| Sensory Deficits | `sensoryDeficits` | array | Numbness, Tingling, Decreased sensation, Phantom pain | multi (checkboxGroup) | none | none | card-level | none found | none | Sensory Function | always-visible today; a "Present/None" gate is a schema question | Keep values |
| Sensory Aids | `sensoryAids` | array | Glasses, Hearing aids, Other | multi (checkboxGroup) | none | none | card-level | none found | none | Sensory Function | none | Keep |
| Sleep Pattern | `sleepRest.sleepPattern` | string | Normal, Insomnia, Hypersomnia, Fragmented, Somnolence, None identified, Overly drowsy, Excessive sleep, Lack of sleep, Satisfied with sleep | single (radio) | none | none | card-level | none found | several overlapping/duplicate meanings in one list | Symptom Impact (Sleep & Rest) | none | **Keep as-is now**; consolidation is a schema question |
| Average Sleep Hours, Nighttime Symptoms, Sleep Aids, Response, Restfulness, Sleep Notes | `sleepRest.*` | mixed | see card | mixed | none | none | card-level | none found | none | Symptom Impact (Sleep & Rest) | always-visible today; a "sleep concern?" gate is a schema question | Keep values |
| Clinical Status Change | `clinicalStatusChange` | string | Stable/No Change, Improving, Symptom Well-Managed, Declining, New Symptom Since Prior Assessment, Not Applicable | single (radio) | none | none | card-level | none found | Directive wants "Symptom well-managed" removed from a *change* list -- it is already a distinct hospice-wide field shared by all 10 systems, not neuro-specific | Clinical Status Change | none | **Not touched this pass** -- shared field across all 10 body systems; changing it is a cross-system schema decision, out of scope for a Neuro/Cardio-only pass |
| Notes | `notes` | string | n/a | textarea | none | none | card-level | none found | none | Notes | none | Keep |

### Cardiovascular (`sectionKey: "cardiovascular"`)

| Display Label | Field ID (path) | Stored Type | Current Controlled Values | Select Type | HOPE | SFV | POC | Report/Export | Historical Concern | Proposed Group | Proposed Trigger | Decision |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Pulse Sites | `pulseSites` | array | Apical, Pedal, Radial, Femoral | multi (checkboxGroup) | none | none | card-level | StructuredFinding writes (`CV_PULSE_SITE_*`) | Directive wants site separated from rhythm/quality/rate | Pulse & Circulation | none | **Keep as-is now**; regrouping is a schema question |
| Pulse Quality | `pulseQuality` | string | Regular, Strong, Weak, Thready, Bounding, Irregular, Tachycardia, Bradycardia, Absent | single (radio) | none | none | card-level | StructuredFinding writes (`CV_PULSE_*`, 9 concepts) | Mixes rhythm (Regular/Irregular), quality (Strong/Weak/Thready/Bounding), and rate (Tachycardia/Bradycardia) in one flat list | Pulse & Circulation | none | **Keep as-is now**; splitting into Rhythm/Quality/Rate is a schema question requiring registry regeneration |
| Peripheral Circulation, Heart Sounds, Skin Color | `peripheralCirculation`, `heartSounds`, `skinColor` | string (free text) | n/a | input | none | none | card-level | none found | Directive wants controlled values in place of free text | Pulse & Circulation | none | **Keep as-is now**; converting to controlled options is a schema question |
| JVD | `jvd` | string (triState) | Yes/No/Not Assessed | single | none | none | card-level | StructuredFinding writes (`CV_JVD_*`) | none | Pulse & Circulation | none | Keep |
| Cool Extremities, Varicose Veins, Stasis Ulcer | `coolExtremities`, `varicoseVeins`, `stasisUlcer` | boolean | n/a | checkbox | none | none | card-level | StructuredFinding writes | Directive wants Stasis Ulcer linked to Skin/Wound, not owned here | Pulse & Circulation | none | **Not touched this pass**; a Skin/Wound cross-link is a schema/navigation question |
| Edema Present | `edema.present` | string (triState) | Yes/No/Not Assessed | single | none | none | card-level | StructuredFinding writes | none | Circulation & Perfusion | none | Keep |
| Edema Location | `edema.location` | array | Bilateral lower extremities, Unilateral LE, Sacral, Periorbital, Upper extremities, Generalized | multi (checkboxGroup) | none | none | card-level | StructuredFinding writes (`CV_EDEMA_LOC_*`, uses "Unilateral LE" as one value, not split Left/Right) | Directive wants explicit Left/Right split instead of "Unilateral LE" | Circulation & Perfusion | **Fixed this pass**: hidden until Edema Present = Yes | Keep values; the Left/Right split is a schema question (registry uses "Unilateral LE" literal today) |
| Edema Severity | `edema.severity` | string | Trace, 1+, 2+, 3+, 4+ | single (radio) | none | none | card-level | StructuredFinding writes (`CV_EDEMA_SEVERITY_*`) | none | Circulation & Perfusion | **Fixed this pass**: hidden until Edema Present = Yes | Keep |
| Chest Pain Present | `chestPain.present` | string (triState) | Yes/No/Not Assessed | single | none | none | card-level | StructuredFinding writes (`CV_CHEST_PAIN_*`) | none | Cardiovascular Symptoms | none | Keep |
| Chest Pain Type | `chestPain.type` | string (free text) | n/a | input | none | none | card-level | none found | Directive wants controlled status options instead of free text | Cardiovascular Symptoms | **Fixed this pass**: hidden until Chest Pain Present = Yes | Keep now; controlled-value conversion is a schema question |
| BP Symptoms | `bpSymptoms` | array | Orthostatic, Hypertensive, Hypotensive, Normal | multi (checkboxGroup) | none | none | card-level | StructuredFinding writes (`CV_BP_*`, all 4 as independent `multi_add`) | **Real conflict**: Normal can coexist with Orthostatic/Hypertensive/Hypotensive in the stored array today | Cardiovascular Symptoms | none | **Flagged, not changed this pass** -- converting to a single-select or to a Vitals-sourced read-only display is a schema question |
| Fatigue, Dizziness | `fatigue`, `dizziness` | string | None, Mild, Moderate, Severe | single (radio) | none | none | card-level | new this session, no StructuredFinding writer yet | none | Cardiovascular Symptoms | none | Keep (added this session as directed) |
| Syncope | `syncope` | string (triState) | Yes/No/Not Assessed | single | none | none | card-level | none yet | none | Cardiovascular Symptoms | none | Keep |
| Dyspnea Related to Cardiac Condition | `cardiacDyspnea` | boolean | n/a | checkbox | none | none | card-level | none found | Directive says causation should not be nurse-guessed and should read from Respiratory | Cardiovascular Symptoms | none | **Flagged, not changed this pass** -- read-only cross-reference to Respiratory is a schema/UI question |
| Heart Failure Present / Type | `heartFailurePresent`, `heartFailureType` | boolean / array | n/a / Systolic, Diastolic, Unspecified | checkbox / multi | I0600-adjacent (comorbidity, not this field) | none | card-level | StructuredFinding writes (`CV_HEART_FAILURE_*`) | Directive says remove Systolic/Diastolic entirely | Cardiovascular Symptoms (already demoted from "disease" category this session) | none | **Already demoted this session**; full removal of the Systolic/Diastolic sub-classification is a schema question (registry writes to it today) |
| Pacemaker, Internal Defibrillator, Central Venous Line | `pacemaker`, `internalDefibrillator`, `centralVenousLine` | boolean | n/a | checkbox | none | none | card-level | StructuredFinding writes | Directive wants central line moved out of "cardiac devices" | Cardiac Devices | none | **Not touched this pass**; re-homing central line to IV/Line workflow is a schema/navigation question |
| Clinical Status Change | `clinicalStatusChange` | string | shared 6-option set | single (radio) | none | none | card-level | none found | none | Clinical Status Change | none | Not touched (shared cross-system field, see Neuro note above) |
| Notes | `notes` | string | n/a | textarea | none | none | card-level | none found | none | Notes | none | Keep |

---

## Artifact 2: Before/After Workflow Map

### Neurological

| | Current visible order (post this-session CSS/regroup fix) | Proposed order per directive |
|---|---|---|
| Order | Cognitive Status -> Emotional/Behavioral Symptoms -> Dementia Findings (BIMS) -> Neuromuscular Function -> Sensory Function -> Symptom Impact (Sleep & Rest) -> Clinical Status Change -> Notes | Overview (**new field**) -> Consciousness & Orientation -> Communication & Sensory -> Cognitive/Behavioral (**new gate field**) -> Sleep & Rest (**new gate field**) -> Motor & Balance (**new gate field**) -> HOPE Cognitive Items (conditional on diagnosis/pathway -- **new visibility rule**) -> Change Since Prior (**new option set**) -> Notes -> Add to POC |
| Conditional branches implemented today | None at the card level (all cards always render); field-level: none until this pass | Overview answer branches every subsequent section; Motor/Sleep/Cognitive gates hide entire groups; BIMS/Dementia card conditional on diagnosis or pathway |
| Conditional branches added this pass | Affected Side/Deficit Type hidden until Motor Deficit Present; Psychiatric History Notes hidden until a history type is selected; Orientation vs. Disoriented made mutually exclusive | (same, subset of proposed) |
| Navigation behavior | Sidebar accordion, unchanged | Unchanged |
| Completion behavior | Card-count based ("0/10" etc., existing `RNICA_WORKFLOW` logic, untouched) | Directive wants Not Started/In Progress/Review Required/Ready state -- **not implemented this pass**, requires defining "required" per field, which is a schema/policy question |

### Cardiovascular

| | Current visible order (post this-session fix) | Proposed order per directive |
|---|---|---|
| Order | Circulation & Perfusion (core) -> Cardiovascular Symptoms -> Cardiac Devices -> Clinical Status Change -> Notes | Overview (**new field**) -> Current Symptoms (**new gate field**) -> Pulse & Circulation (**new gate field**) -> Edema (already gated this pass) -> Devices (**new gate field**) -> Change Since Prior -> Notes -> Add to POC |
| Conditional branches added this pass | Edema Location/Severity hidden until Edema Present = Yes; Chest Pain Type hidden until Chest Pain Present = Yes | (subset of proposed) |
| Not implemented this pass | Overview gate, Current Symptoms gate, Pulse & Circulation gate, BP-from-Vitals read-only display, orthostatic-symptom reframe, Devices gate, disease-classification removal | All require new fields or removed/changed option values -- schema questions below |

---

## Artifact 3: Control Conflict Report

| # | Location | Conflict | Status |
|---|---|---|---|
| 1 | Neurological | `orientation.disoriented` checkbox can be checked at the same time as `orientation.time/.place/.person/.situation` | **Fixed this pass** -- selecting one now clears the other |
| 2 | Neurological | `consciousness` options overlap: Alert/Awake, Lethargic/Obtunded/Stuporous/Minimally responsive/Comatose/Coma | Flagged; not fixed (schema question -- which legacy values collapse into which bucket) |
| 3 | Neurological | `communication` options overlap: Clear/Normal; Unable/"speech limited to six or fewer words" ambiguity | Flagged; not fixed (schema question) |
| 4 | Neurological | `balance` options overlap: Steady/Normal, Unsteady/Impaired | Flagged; not fixed (schema question) |
| 5 | Cardiovascular | `bpSymptoms` checkbox group allows "Normal" to coexist with Orthostatic/Hypertensive/Hypotensive in the same stored array | Flagged; not fixed (schema question -- StructuredFinding registry writes each independently today) |
| 6 | Cardiovascular | `pulseQuality` single-select mixes rhythm/quality/rate concepts (e.g., Regular vs. Tachycardia are different axes forced into one control) | Flagged; not fixed (schema question) |
| 7 | Cardiovascular | Edema location used "Unilateral LE" as one value instead of separate Left/Right | Flagged; not fixed (schema question -- registry already writes this exact string) |

---

## Open Schema Questions (require explicit owner approval before implementation)

For each item below, implementing it means adding a new field and/or changing
an existing option set (which also means regenerating
`structuredFindingRegistry.generated.js` and updating
`applyStructuredFindings.test.js`). None of these are implemented yet.

1. **Neurological/Cardiovascular Overview screening question** (a brand-new field per system: "No significant concern / stable / new-or-worsening / unable to assess"). Does not exist today in any form.
2. **Consciousness consolidation**: collapse 8 existing values into 5 presented choices. Which legacy value maps to which new bucket (e.g., does "Awake" become "Alert", or stay distinct? does "Obtunded" become "Drowsy/Lethargic" or "Unresponsive/Comatose"?).
3. **Communication consolidation**: collapse 8 existing values into ~7 non-overlapping choices, deciding whether "Clear" and "Normal" are the same stored value going forward.
4. **Balance consolidation**: collapse 5 existing values (Steady/Unsteady/Unable to stand/Normal/Impaired) into a non-overlapping set.
5. **Motor Deficit + Deficit Type -> single "Motor Finding" control** merging two fields into one, adding new values (Generalized weakness, Focal weakness, Paraplegia, Quadriplegia, Tremor) not currently in the schema.
6. **Sleep, Cognitive/Behavioral, Motor/Balance, Sensory-symptom "concern?" gate fields** -- 4 new boolean/select fields per the directive's workflow, none of which exist today.
7. **Psychiatric history reframed** from a 6-option checkboxGroup to a 3-option gate (None documented/History present/Unknown) plus the existing types nested under it.
8. **Change Since Prior Assessment**: replace the existing 6-option `clinicalStatusChange` set with a different 7-option set that drops "Symptom Well-Managed" -- this field is shared verbatim across all 10 body systems (added this session at owner direction), so changing it here affects every other system too.
9. **Cardiovascular BP**: read BP from Vitals instead of the `bpSymptoms` checkbox array; replace with a single orthostatic-symptom Yes/No/Unable question. Requires confirming Vitals has position/timing data available for "Current BP / Position / Source: Vitals" display.
10. **Cardiovascular pulse**: split `pulseQuality` into Rhythm/Quality/Rate/Site controls -- requires deciding the exact new value set and regenerating the StructuredFinding registry entries (`CV_PULSE_*`) that currently write single flat values.
11. **Edema location**: split "Unilateral LE" into separate Left/Right values -- the registry currently writes the combined string; splitting requires a migration decision for existing stored "Unilateral LE" records (keep as legacy display value vs. force re-selection).
12. **Heart Failure Type removal**: fully removing Systolic/Diastolic/Unspecified (vs. this session's demotion to a symptom-level flag) -- the StructuredFinding registry (`CV_HEART_FAILURE_SYSTOLIC`/`_DIASTOLIC`) actively writes these values from evidence harvesting today.
13. **Central Venous Line re-homing** to an IV/Line or Treatment/DME workflow -- requires confirming that workflow exists and can own this field, or scoping a new one.
14. **Stasis Ulcer cross-link to Skin/Wound** as read-only, instead of an independent Cardiovascular checkbox.
15. **Cardiac Dyspnea causation**: replace the `cardiacDyspnea` checkbox with a read-only pull from Respiratory's `sobSeverity`, only surfacing a "cardiac relationship" when the source record/clinician has already established it -- needs a defined source for that relationship (new field, or Diagnosis-linked).
16. **Completion state model** (Not Started/In Progress/Review Required/Ready) replacing the existing card-count-based workflow completion logic -- a cross-system change, not Neuro/Cardio-specific.

Recommendation: approve/reject these individually (or in batches) so each can be
implemented with its matching StructuredFinding registry update and test
coverage in the same change, per the directive's own guardrail against
converting fields without verifying storage behavior.
