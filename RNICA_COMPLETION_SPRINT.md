# RNICA Completion Sprint — Final 43 Unmapped Clinical Fields

RNICA certification is **paused**. It resumes only after: mappings are created for
all 43 fields below (or a field is individually re-justified as excluded/judgment-only
with evidence), the Apply path is verified per field, persistence is verified, and
the real-admission validation (Loren Shields) is rerun end-to-end.

Grounded against the actual codebase (`backend/app/services/evidence/structured_findings.py`)
— not estimated blind. Effort key: **S** = reuse an existing concept, add a field-write
only (<0.5 day); **M** = new enum concept(s) following an existing pattern + apply wiring
+ tests (0.5–1.5 days); **L** = new bounded value-slot pattern (numeric/date/free-text)
+ validation + tests (2+ days).

## Symptom Impact (8 fields) — HOPE J2051

| Field | Source evidence available | Missing concept | Missing mapping | Apply destination | Effort |
|---|---|---|---|---|---|
| pain | Transcript, H&P, referral (pain severity already extracted) | **None** — `PAIN_SEVERITY_NONE/MILD/MODERATE/SEVERE` already exist | Add `symptomImpact.pain` as a 2nd field-write on the 4 existing PAIN_SEVERITY_* concepts | `formData.symptomImpact.pain` | S |
| shortnessOfBreath | Transcript, H&P, referral (SOB severity already extracted) | **None** — `RESP_SOB_NONE/MILD/MODERATE/SEVERE` already exist | Add `symptomImpact.shortnessOfBreath` as a 2nd field-write | `formData.symptomImpact.shortnessOfBreath` | S |
| nausea | Transcript, H&P, referral | **None** — `GI_NAUSEA_*` (None/Mild/Moderate/Severe) already exist | Add `symptomImpact.nausea` as a 2nd field-write | `formData.symptomImpact.nausea` | S |
| vomiting | Transcript, H&P, referral | **None** — `GI_VOMITING_*` already exist | Add `symptomImpact.vomiting` as a 2nd field-write | `formData.symptomImpact.vomiting` | S |
| diarrhea | Transcript, H&P, referral | **None** — `GI_DIARRHEA_*` already exist | Add `symptomImpact.diarrhea` as a 2nd field-write | `formData.symptomImpact.diarrhea` | S |
| constipation | Transcript, H&P, referral | **None** — `GI_CONSTIPATION_*` already exist | Add `symptomImpact.constipation` as a 2nd field-write | `formData.symptomImpact.constipation` | S |
| anxiety | Transcript, H&P (psychosocial/mental status narrative) | **New**: `PSYCH_ANXIETY_SEVERITY_NONE/MILD/MODERATE/SEVERE` (current-state, distinct from existing `PSYCH_HISTORY_ANXIETY` history flag) | Register 4 new concepts + apply wiring + tests | `formData.symptomImpact.anxiety` | M |
| agitation | Transcript, H&P (demeanor narrative) | **New**: `NEURO_AGITATION_SEVERITY_NONE/MILD/MODERATE/SEVERE` (current-state severity, distinct from existing boolean `NEURO_DEMEANOR_AGITATION` flag) | Register 4 new concepts + apply wiring + tests | `formData.symptomImpact.agitation` | M |

**Section total: 6×S + 2×M.**

## Skin / Wounds (15 fields)

Architecture note: `SKIN_WOUND_PRESENT` deliberately creates only a blank draft row
today (comment in code: *"no stage/size/drainage/treatment is ever invented"*) — this
was a real safety boundary, not an oversight, for open-ended measurements. The plan
below closes it using the same *bounded* pattern already proven safe for
`wounds[].location` (a `free_text_bounded` value slot with a max length), not open
fabrication.

| Field | Source evidence available | Missing concept | Missing mapping | Apply destination | Effort |
|---|---|---|---|---|---|
| stage | Transcript, H&P wound notes (Stage 1–4/Unstageable/DTI is a closed CMS vocabulary) | **New**: `SKIN_WOUND_STAGE_1/2/3/4/UNSTAGEABLE/DTI` | Register 6 enum concepts, wire to draft row field `stage` | `formData.skin.wounds[].stage` | M |
| woundType | Transcript, H&P (pressure/venous/arterial/diabetic/surgical/skin tear — closed vocabulary) | **New**: `SKIN_WOUND_TYPE_*` (per type) | Register enum concepts, wire to draft row field `woundType` | `formData.skin.wounds[].woundType` | M |
| drainage | Transcript, H&P (none/scant/moderate/copious — closed vocabulary) | **New**: `SKIN_WOUND_DRAINAGE_NONE/SCANT/MODERATE/COPIOUS` | Register 4 enum concepts, wire to draft row field `drainage` | `formData.skin.wounds[].drainage` | M |
| odor | Transcript, H&P (none/mild/foul — closed vocabulary) | **New**: `SKIN_WOUND_ODOR_NONE/MILD/FOUL` | Register 3 enum concepts, wire to draft row field `odor` | `formData.skin.wounds[].odor` | M |
| isNonhealingWound | Transcript, H&P (explicit clinician statement) | **New**: `SKIN_WOUND_NONHEALING` boolean | Register concept, wire to draft row field | `formData.skin.wounds[].isNonhealingWound` | S |
| isSkinTear | Transcript, H&P | **New**: `SKIN_WOUND_SKIN_TEAR` boolean | Register concept, wire to draft row field | `formData.skin.wounds[].isSkinTear` | S |
| isSurgicalWound | Transcript, H&P | **New**: `SKIN_WOUND_SURGICAL` boolean | Register concept, wire to draft row field | `formData.skin.wounds[].isSurgicalWound` | S |
| presentAsPressureInjury | Transcript, H&P | **New**: `SKIN_WOUND_PRESSURE_INJURY` boolean | Register concept, wire to draft row field | `formData.skin.wounds[].presentAsPressureInjury` | S |
| length | H&P wound-care notes with explicit cm measurement | **New**: bounded numeric value slot (cm, e.g. 0–30) on wound draft row, same pattern as `vomitingOccurrences24h` | Register concept + numeric `ValueSlot`, wire to draft row field `length` | `formData.skin.wounds[].length` | L |
| width | H&P wound-care notes with explicit cm measurement | **New**: bounded numeric value slot | Register concept + numeric `ValueSlot` | `formData.skin.wounds[].width` | L |
| depth | H&P wound-care notes with explicit cm measurement | **New**: bounded numeric value slot | Register concept + numeric `ValueSlot` | `formData.skin.wounds[].depth` | L |
| dressing | H&P wound-care notes (free text product name — no closed vocabulary) | **New**: bounded free-text value slot (`free_text_bounded`, same as `location`) | Register concept + bounded free-text slot | `formData.skin.wounds[].dressing` | M |
| dressingFrequency | H&P wound-care notes (e.g. "daily", "q3days" — semi-closed) | **New**: enum concepts for common frequencies (Daily/BID/Every 2-3 days/Weekly/PRN) | Register enum concepts | `formData.skin.wounds[].dressingFrequency` | M |
| currentTreatment | H&P wound-care notes (free text — no closed vocabulary) | **New**: bounded free-text value slot | Register concept + bounded free-text slot | `formData.skin.wounds[].currentTreatment` | M |
| periwoundCondition | H&P wound-care notes (intact/macerated/erythematous — semi-closed) | **New**: enum concepts (Intact/Macerated/Erythematous/Indurated) | Register enum concepts | `formData.skin.wounds[].periwoundCondition` | M |

**Section total: 4×S + 9×M + 3×L.** Largest group; do the boolean flags (S) and
closed-vocabulary enums (stage/type/drainage/odor/periwound/frequency, M) first —
they carry the least fabrication risk. Numeric measurements (length/width/depth, L)
go last and need an explicit clinician-stated-number safeguard (never inferred/estimated).

## Genitourinary (7 fields)

Architecture note: existing code comment explicitly lists *"catheter sizes/dates"*
under **deliberately excluded, unbounded free-text, no enumerable vocabulary** — this
was a real design boundary. Reopening these requires a bounded-value-slot approach
(dates via a validated date parser, sizes via a closed Fr-size enum), not a reversal
of the underlying safety principle.

| Field | Source evidence available | Missing concept | Missing mapping | Apply destination | Effort |
|---|---|---|---|---|---|
| size | H&P (Fr size is a closed, standard vocabulary: 10/12/14/16/18/20/22 Fr) | **New**: `GU_CATHETER_SIZE_*` per standard Fr size | Register enum concepts | `formData.genitourinary.catheter.size` | M |
| insertionDate | H&P (explicit date statement) | **New**: bounded date `ValueSlot` (reject unparseable/future dates) | Register concept + date value slot + validation | `formData.genitourinary.catheter.insertionDate` | L |
| lastChangeDate | H&P (explicit date statement) | **New**: bounded date `ValueSlot` | Register concept + date value slot | `formData.genitourinary.catheter.lastChangeDate` | L |
| irrigation.solution | H&P (normal saline / sterile water — closed vocabulary) | **New**: `GU_CATHETER_IRRIGATION_SOLUTION_*` enum | Register enum concepts | `formData.genitourinary.catheter.irrigation.solution` | M |
| irrigation.frequency | H&P (daily/BID/PRN — semi-closed) | **New**: enum concepts | Register enum concepts | `formData.genitourinary.catheter.irrigation.frequency` | M |
| irrigation.duration | H&P (free text — no closed vocabulary) | **New**: bounded free-text value slot | Register concept + bounded free-text slot | `formData.genitourinary.catheter.irrigation.duration` | M |
| catheterCare | H&P (free-text nursing instructions) | **New**: bounded free-text value slot (long-form, textarea) | Register concept + bounded free-text slot | `formData.genitourinary.catheterCare` | M |

**Section total: 5×M + 2×L.**

## Gastrointestinal (5 fields)

| Field | Source evidence available | Missing concept | Missing mapping | Apply destination | Effort |
|---|---|---|---|---|---|
| feedingTube.site | H&P (abdominal/nasal — closed vocabulary given tube type already exists) | **New**: `GI_FEEDING_TUBE_SITE_*` enum | Register enum concepts (reuses existing `GI_FEEDING_TUBE_TYPE_*` pattern) | `formData.gastrointestinal.feedingTube.site` | M |
| ostomy.condition | H&P (healthy/irritated/prolapsed — closed vocabulary) | **New**: `GI_OSTOMY_CONDITION_*` enum | Register enum concepts (reuses existing `GI_OSTOMY_TYPE_*` pattern) | `formData.gastrointestinal.ostomy.condition` | M |
| abdominalGirth | H&P (explicit cm measurement) | **New**: bounded numeric value slot | Register concept + numeric slot | `formData.gastrointestinal.abdominalGirth` | L |
| bowelFrequency | H&P (e.g. "daily", "every 2 days" — semi-closed) | **New**: enum concepts for common frequencies | Register enum concepts | `formData.gastrointestinal.bowelFrequency` | M |
| continence | H&P (continent/incontinent — closed, but note `GU_URINARY_STATUS_*` already models urinary continence; this is the separate GI/bowel field) | **New**: `GI_CONTINENCE_*` enum (reuses existing `GI_BOWEL_STATUS_CONTINENT/INCONTINENT` pattern — may just need a 2nd field-write, re-verify overlap before building new concepts) | Verify against existing `GI_BOWEL_STATUS_CONTINENT/INCONTINENT`; likely S not M | `formData.gastrointestinal.continence` | S/M (verify first) |

**Section total: ~1×S/M + 3×M + 1×L.**

## Endocrine (3 fields)

| Field | Source evidence available | Missing concept | Missing mapping | Apply destination | Effort |
|---|---|---|---|---|---|
| insulinType | H&P medication list (Lantus/Humalog/NPH/etc. — closed-ish vocabulary, can bound to common types) | **New**: `ENDO_INSULIN_TYPE_*` enum | Register enum concepts | `formData.endocrine.diabetes.insulinType` | M |
| insulinDose | H&P medication list (explicit unit dose) | **New**: bounded numeric value slot (units, e.g. 0–200) | Register concept + numeric slot | `formData.endocrine.diabetes.insulinDose` | L |
| lastHbA1cDate | H&P labs (explicit date; `ENDO_HBA1C_VALUE` already extracts the value itself) | **New**: bounded date `ValueSlot`, paired with existing `ENDO_HBA1C_VALUE` concept | Register concept + date value slot | `formData.endocrine.diabetes.lastHbA1cDate` | M (reuses existing HbA1c extraction context) |

**Section total: 2×M + 1×L.**

## Nutrition (2 fields)

| Field | Source evidence available | Missing concept | Missing mapping | Apply destination | Effort |
|---|---|---|---|---|---|
| dentures.condition | H&P (well-fitting/loose/none — closed vocabulary; `NUTR_DENTURES_UPPER/LOWER` already model presence) | **New**: `NUTR_DENTURES_CONDITION_*` enum | Register enum concepts | `formData.nutrition.dentures.condition` | M |
| nutritionalSupplements | H&P (Boost/Ensure/etc. — bounded to common product names, matches the Loren Shields H&P's own "Boost Glucose Control" language already seen live this program) | **New**: bounded free-text value slot (or small enum of common products) | Register concept + bounded slot | `formData.nutrition.nutritionalSupplements` | M |

**Section total: 2×M.**

## Respiratory (1 field)

| Field | Source evidence available | Missing concept | Missing mapping | Apply destination | Effort |
|---|---|---|---|---|---|
| ventilator.ventilatorTypeAndSettings | H&P (free-text settings; `RESP_VENTILATOR_SHORT_TERM/LONG_TERM` already model presence/duration) | **New**: bounded free-text value slot | Register concept + bounded free-text slot | `formData.respiratory.ventilator.ventilatorTypeAndSettings` | M |

**Section total: 1×M.**

## Musculoskeletal (1 field)

| Field | Source evidence available | Missing concept | Missing mapping | Apply destination | Effort |
|---|---|---|---|---|---|
| fallHistory.fallInjuries | H&P/referral fall narrative (`MSK_FALLS_LAST_90_DAYS` already models fall occurrence; injuries need their own free-text/enum) | **New**: bounded free-text or small enum (laceration/fracture/bruising/head injury/none) | Register concept(s) | `formData.musculoskeletal.fallHistory.fallInjuries` | M |

**Section total: 1×M.**

## Not in your requested groups but part of the 43 (flagged for completeness)

| Field | Source evidence available | Missing concept | Missing mapping | Apply destination | Effort |
|---|---|---|---|---|---|
| Cardiovascular: edema.pitting | H&P (pitting/non-pitting — closed vocabulary; `CV_EDEMA_SEVERITY_*`/`CV_EDEMA_LOC_*` already exist) | **New**: `CV_EDEMA_PITTING_YES/NO` | Register 2 enum concepts | `formData.cardiovascular.edema.pitting` | S |

## Sprint totals

- **S (reuse existing concept, field-write only): 11 fields**
- **M (new enum concept + wiring): 25 fields**
- **L (new bounded numeric/date value slot): 6 fields**
- **Total: 42 classified + 1 (continence) pending a quick overlap check against
  existing `GI_BOWEL_STATUS_CONTINENT/INCONTINENT` before final sizing = 43.**

Rough effort: 11×S (~0.4d avg) + 25×M (~1d avg) + 6×L (~2.5d avg) ≈ **4.4 + 25 + 15 =
~44 developer-days** of concept/apply work if done serially; parallelizable by
section since sections don't share code paths.

## Sprint execution order (risk-ascending, matches "closed vocabulary before free text before measurements")

1. **Symptom Impact** (6×S + 2×M) — fastest, highest clinical value (CMS HOPE-reportable), do first.
2. **Skin/Wounds booleans + closed enums** (4×S + 9×M) — largest single group, second priority.
3. **Genitourinary** (5×M + 2×L) — catheter detail.
4. **Gastrointestinal** (~1×S/M + 3×M + 1×L).
5. **Endocrine** (2×M + 1×L).
6. **Nutrition** (2×M).
7. **Respiratory** (1×M), **Musculoskeletal** (1×M), **Cardiovascular edema.pitting** (1×S) — smallest groups, can be bundled into one PR.
8. **Skin/Wounds numeric measurements** (length/width/depth, 3×L) — highest fabrication-risk fields, done last with an explicit "clinician-stated-number only, never estimated" safeguard and dedicated tests.

## Certification resumption criteria (must all pass before re-declaring RNICA complete)

1. All 43 fields have an implemented concept + apply mapping (or are individually
   re-justified as excluded/judgment-only, with the same rigor as this sprint doc).
2. Apply path verified per field (unit test + at least one live extraction run per section).
3. Persistence verified (reload survives, matches the pattern already proven for the
   6 fields applied to Loren Shields this program).
4. Real admission validation (Loren Shields, or an equivalent real H&P) rerun
   end-to-end in the browser, capturing before/after screenshots showing the newly
   wired fields populate correctly with provenance.
