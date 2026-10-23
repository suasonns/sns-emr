# SUPERSEDED — DO NOT IMPLEMENT

This document records earlier analysis and unresolved design questions.
It is retained only for historical reference.

The approved implementation specification is:

`SKIN_IMPAIRMENT_CONTROLLED_VALUES_FINAL.md`

If this document conflicts with the final specification, the final
specification controls.

Do not use this file to add, remove, rename, or reinterpret any
clinical control, controlled value, validation, layout, or workflow.

---

# Skin Impairment / Wound Assessment — Controlled Value & UI Content Specification

**Status:** Pre-code content specification. **Not a compliance document.** Contains zero code changes,
CSS changes, or new architecture — this is a content/behavior definition to be reviewed and approved by
the Product Owner before any further implementation work proceeds in the Skin Impairment Workspace.

**Source file traced:** `sns-emr-frontend/src/components/RNICA.jsx` (all line numbers below refer to this
file as of this writing; it is a single ~28,000-line file and line numbers will shift on any future edit).

**Scope:** every dropdown, button group, toggle, and conditional control currently implemented for the
Skin Impairment / Wound workspace (`SkinImpairmentWorkspacePage`, `WoundRecordCard`, `PatientWoundMap`,
`WoundInventoryTable`, `WoundAssessmentSummaryPanel`), plus the wound-selection model itself.

No code was changed to produce this document.

---

## 0. Current wound-selection model (today, live)

As of this writing, exactly one wound-selection mechanism exists (the prior "Current Wound Selector"
dropdown was removed per an earlier directive and is **not currently present** anywhere in the code):

1. **Wound Inventory table** (`WoundInventoryTable`, lines 14143–14204) — clicking any row calls
   `onSelectWound(w.woundId)`. This is the only full-list selector.
2. **Patient Wound Map numbered markers** (`PatientWoundMap`, lines 14054–14139) — clicking a marker
   calls `onSelectWound`. Only wounds with a matching structured anatomical-site pin get a marker; a
   wound with no location (`location` empty) renders no marker and is only reachable via the Inventory.
3. **Front/Back toggle** (same component, lines 14110–14116) — not a wound selector; switches which map
   image/marker set is displayed.

Per the Product Owner's clarification in this same exchange: the compact dropdown concept is the
**correct long-term concept** and will be **restored later, after this content spec is approved** — it is
explicitly **not** being built or removed right now. Section 9 below defines its intended future content
only; it is a mockup, not a build instruction.

---

## 1–with-15 Controlled-value specification (per control)

Each control below uses the exact 15-field format requested, immediately followed by its current-code
trace (file:line citations) so the two deliverables stay next to each other instead of duplicated in two
places.

---

### CONTROL: Wound Lifecycle Status

LABEL:
`Status`

OPTIONS:
- New
- Existing
- Treat
- Resolved
- COC

STORED VALUES:
`wound.status` — same literal strings are the stored values (no separate enum/ID exists).

DEFAULT:
`"New"` when blank (`value={wound.status || "New"}`, line 5445); the record object itself does not set a
status at creation (`makeWoundRecord` does not assign `status`, so it is `undefined` until this line's
fallback renders "New").

REQUIRED:
No. `isWoundRecordMissingRequiredDetails` (lines 5884–5905) never inspects `wound.status`.

VISIBLE WHEN:
Always, in the full `WoundRecordCard` form (not variant-restricted). Lines 5442–5450.

HIDDEN WHEN:
Never hidden.

DEPENDENCIES:
None currently wired — selecting "Resolved" does not auto-populate a resolution date or reason field;
selecting "COC" does not force a note. (See Open Questions below.)

MUTUALLY EXCLUSIVE VALUES:
All five are mutually exclusive (single-select `FormSegmented`).

COMPLETION RULE:
Not part of the completion function. A wound can be saved/considered "complete" with no status ever
chosen by the user (falls back to displaying "New").

ERROR MESSAGE:
None exists (no field-level validation message anywhere in this file; the only user-facing signal is the
assessment-level coverage panel's `unresolvedHint` strings, which do not reference status at all).

INVENTORY DISPLAY:
`WoundInventoryTable` Status column shows `w.status || "—"` (line 14178) — i.e., an em dash, not the word
"New," when the field has never been touched. **This is inconsistent with the editor's own "New" fallback
display** (see Contradiction Review, item C-1).

CLINICAL-NOTE OUTPUT:
NOT FOUND. No wound-specific narrative/note generator exists in this file; status is not echoed into any
exported text anywhere traced.

HISTORICAL BEHAVIOR:
Legacy values that don't match one of the five current options are preserved and shown read-only via the
`FormSegmented`/`FormSelect` legacy-value chip pattern (see `FormSelect`, lines 2100–2112, comment
2105–2112) — stored data is never silently rewritten or discarded.

OPEN QUESTION — PRODUCT-OWNER DECISION REQUIRED:
Is "COC" ("Change Of Condition") an admission-RNICA-appropriate value, or does it only make sense on a
follow-up/COC visit? Today it is offered identically on every visit type with no visit-type gating. Yes/No:
should `COC` be hidden when the current visit is an initial admission assessment?

---

### CONTROL: COC (Status value definition)

LABEL:
`COC` (status pill value only — not a separate field)

STORED/DISPLAYED DEFINITION (verbatim from code comment, lines 4746–4751, `WOUND_LIFECYCLE_STATUS_HELP`):
> "Change Of Condition — a clinically meaningful change (new/increased drainage, infection concern,
> increased pain, worsening measurements, new odor, new stage, treatment failure concern). Should prompt
> review."

This definition is already present in the code (not undefined/abbreviated-only) and is shown to the user
as inline help text under the Status control. No further definition work is required; retained here per
the directive's explicit instruction to either define or remove "COC."

PRODUCT-OWNER DECISION REQUIRED:
Keep this definition as the final one, or revise its wording? (No code change either way — this is a
string constant.)

---

### CONTROL: Present At Admission

LABEL:
`Present at Admission`

OPTIONS:
- Yes
- No
- Unknown

STORED VALUES:
`wound.presentAtAdmission` — literal strings above.

DEFAULT:
`""` (line 4807) — no option pre-selected.

REQUIRED:
No. Not referenced by `isWoundRecordMissingRequiredDetails`.

VISIBLE WHEN:
Always, full form, not variant-restricted. Lines 5519–5526.

HIDDEN WHEN:
Never.

DEPENDENCIES:
None. Selecting "Unknown" does not currently require or surface an explanation field.

COMPLETION RULE:
None.

ERROR MESSAGE:
None.

INVENTORY DISPLAY:
Not shown in the Inventory table (table columns are #, Location, Stage/Condition, L×W×D, Photos, Status
only).

CLINICAL-NOTE OUTPUT:
NOT FOUND.

HISTORICAL BEHAVIOR:
Standard legacy-chip preservation (see FormSelect pattern above).

PRODUCT-OWNER DECISION REQUIRED:
Should "Unknown" require a free-text explanation (per the original directive's question)? Today it does
not.

---

### CONTROL: Condition Type

LABEL:
`Condition Type`

OPTIONS (exact order as coded, lines 4225–4237):
- Skin Tear
- Moisture-Associated Skin Damage
- Rash
- Bruising
- Excoriation
- Open Lesion
- Fungating/Malignant Wound
- Surgical Wound
- Diabetic Foot Ulcer
- Venous Ulcer
- Arterial Ulcer
- Other Skin Condition

(Pressure Injury is **not** in this list — it has its own dedicated entry point, see "Add-Wound Action"
below. This 12-item list is itself labeled in a code comment, lines 4218–4224, as "the exact approved
12-item picker list" from a prior Product Owner directive dated 2026-11-19.)

STORED VALUES (enum, lines 4196–4213):
`skin_tear`, `moisture_associated_skin_damage`, `rash`, `bruising`, `excoriation`, `open_lesion`,
`malignant_fungating_wound`, `surgical_wound`, `diabetic_foot_ulcer`, `venous_ulcer`, `arterial_ulcer`,
`other_skin_condition`. Plus legacy-only enum values not offered as new-entry options:
`other_non_pressure_ulcer`, `traumatic_wound`, `ostomy_peristomal_condition`, `pressure_injury` (used
internally), `unknown_legacy` (inference fallback).

DEFAULT:
`""` for a new "Skin Condition" record (line 4794) — the record initially renders **only** this selector
until a value is chosen (lines 5365–5387); `"pressure_injury"` automatically for a "+ Pressure Injury"
record (same line), and this selector is never shown for that variant.

REQUIRED:
Yes, implicitly — a blank "other" record shows nothing else until this is set. Not explicitly checked by
`isWoundRecordMissingRequiredDetails`, but the surrounding UI makes it practically mandatory to proceed.

VISIBLE WHEN:
`variant === "other"` (lines 5512–5518).

HIDDEN WHEN:
`variant === "pressureInjury"` — value is auto-set and the selector never renders.

DEPENDENCIES:
Drives which condition-specific sub-section appears later in the same form: Skin Tear → Flap Status;
Surgical Wound → Closure Status; MASD → Moisture Source (see those controls below). Also drives which
Body Region/Anatomical Site options are offered (`allowedSiteIdsForConditionType`, line ~4516) and whether
a photo is "recommended" (`PHOTOGRAPHABLE_WOUND_CONDITION_TYPES`, lines 4243–4253).

MUTUALLY EXCLUSIVE VALUES:
Single-select; exactly one condition type per wound record.

COMPLETION RULE:
Record cannot practically proceed without one (UI-enforced, not completion-function-enforced).

ERROR MESSAGE:
None exists.

INVENTORY DISPLAY:
`WoundInventoryTable` Stage/Condition column shows `w.stage || getConditionTypeDisplayLabel(...)` (line
14168) — e.g. "Skin Tear," "Moisture-Associated Skin Damage," etc., or "Pressure Injury" for that variant.

CLINICAL-NOTE OUTPUT:
NOT FOUND.

HISTORICAL BEHAVIOR:
`LEGACY_WOUND_TYPE_TO_CONDITION_TYPE` (lines 4276–4284) maps 8 old free-text `woundType` strings
("Pressure injury," "Skin tear," "Surgical wound," "Venous ulcer," "Arterial ulcer," "Diabetic ulcer,"
"Nonhealing wound," "Other") to the new enum for inference only; `inferLegacyWoundConditionType` (lines
4291–4297) is the full fallback chain. Legacy-only enum values (`other_non_pressure_ulcer`,
`traumatic_wound`, `ostomy_peristomal_condition`) are kept for backward-read compatibility but are
deliberately **not offered** in the new-entry picker — this was itself a prior Product Owner decision
(2026-11-19), already implemented, not something this spec is proposing.

PRODUCT-OWNER DECISION REQUIRED:
None — the directive's requested 16-item list and the implemented 12-item (+ Pressure Injury) list differ
only in that the implemented list omits "Traumatic Wound," "Peristomal Skin Condition," and consolidates
naming ("Fungating/Malignant Wound" vs. the directive's "Malignant/Fungating Wound"). Confirm: should
Traumatic Wound and Peristomal Skin Condition be added back to the new-entry picker (their enum values
already exist, legacy-only today)?

---

### CONTROL: Add-Wound Actions

LABEL:
`+ Pressure Injury` and `+ Skin Condition` (two separate buttons)

OPTIONS:
Not a selector — two distinct creation actions.

STORED VALUES:
Each calls `addRecord(variant)` with `variant` = `"pressureInjury"` or `"other"` (lines 6154–6155,
6125–6129).

DEFAULT BEHAVIOR:
- `+ Pressure Injury` → `makeWoundRecord("pressureInjury")` sets `conditionType: "pressure_injury"`,
  `presentAsPressureInjury: true` immediately (lines 4794–4795) — **the user never sees or re-selects
  "Pressure Injury" from a list**, confirming the directive's explicit requirement is already met.
- `+ Skin Condition` → `makeWoundRecord("other")` sets `conditionType: ""`, `presentAsPressureInjury:
  false` — the Condition Type picker (above) is the very next thing the user sees.
- Both default `status: "New"` is not literally set (falls back to "New" only in the Status control's
  display, see above) — i.e. `status` field itself starts `undefined`, not the string `"New"`.

REQUIRED:
N/A (action, not a value).

VISIBLE WHEN:
Always, in `mapSection` of `SkinImpairmentWorkspacePage` (lines 6154–6155).

PRODUCT-OWNER DECISION REQUIRED:
None currently open for this control.

---

### CONTROL: Body Region

LABEL:
`Body Region`

OPTIONS (all 8, verbatim, lines 4402–4410):
| id | label |
|---|---|
| `head_face` | Head and Face |
| `neck` | Neck |
| `shoulder_chest_torso` | Shoulder, Chest and Torso |
| `upper_extremity` | Upper Extremity |
| `pelvis_perineum` | Pelvis and Perineal Region |
| `lower_extremity` | Lower Extremity |
| `foot_ankle` | Foot and Ankle |
| `special_sites` | Special Sites |

STORED VALUES:
`wound.bodyRegion` = the `id` column above.

DEFAULT:
`""` (line 4800).

REQUIRED:
Indirectly — the generated `wound.location` string (built from region + site + side + surface) is what
`isWoundRecordMissingRequiredDetails` actually checks (`if (!w.location) return true`, line 5886).

VISIBLE WHEN:
Opened via the "Change"/"Set Location" Dialog (today's implementation — see Section 0). Options filtered
to only regions that contain at least one site valid for the current Condition Type (`regionsWithSites`,
line 5142).

HIDDEN WHEN:
Collapsed by default behind the Dialog when a location already exists.

DEPENDENCIES:
Drives the Anatomical Site list (next control) to only that region's sites.

COMPLETION RULE:
Feeds the combined `location` string requirement above.

INVENTORY DISPLAY:
Not shown directly — only the combined `location` text is shown ("Coccyx," "Not yet documented," etc.).

HISTORICAL BEHAVIOR:
Standard legacy-chip preservation.

PRODUCT-OWNER DECISION REQUIRED:
None.

---

### CONTROL: Anatomical Site

LABEL:
`Anatomical Site`

OPTIONS:
Full `ANATOMICAL_SITE_LIBRARY` (lines 4423–4505), 61 entries total, grouped by Body Region:

**Head and Face:** Scalp/Crown, Forehead, Temporal Region, Periorbital Region, Nose, Cheek, Perioral
Region, Chin, Mandible, Ear, Occiput

**Neck:** Anterior Neck, Lateral Neck, Posterior Neck, Cervical Spine

**Shoulder, Chest and Torso:** Shoulder, Scapula, Clavicle, Sternum, Chest (Anterior), Rib Cage, Axilla,
Abdomen, Flank, Upper Back, Mid Back, Lower Back, Thoracic Spine, Lumbar Spine

**Upper Extremity:** Upper Arm, Elbow/Olecranon, Forearm, Wrist, Hand, Finger *(description required)*

**Pelvis and Perineal Region:** Sacrum, Coccyx, Ischium/Ischial Tuberosity, Buttock/Gluteal, Gluteal Cleft,
Greater Trochanter/Hip, Groin, Perineum, Perianal Region, Suprapubic

**Lower Extremity:** Thigh, Knee/Patella, Popliteal Fossa, Calf, Shin/Anterior Lower Leg, Achilles Region,
Lower Leg (General), Other Lower-Extremity Site *(description required)*

**Foot and Ankle:** Ankle/Malleolus, Heel, Dorsal Foot, Plantar Foot/Sole, Medial Foot, Lateral Foot,
Midfoot, Metatarsal Head, Great Toe, Other Toe *(description required)*, Toe Web Space *(description
required)*, Foot Amputation Stump *(description required)*, Other Foot/Ankle Site *(description required)*

**Special Sites:** Medical Device Contact Site *(description required)*, Skin Fold (Other) *(description
required)*, Peristomal Region, Periwound Region, Amputation Stump (Other) *(description required)*, Other
Anatomical Site *(description required)*

STORED VALUES:
`wound.anatomicalSite` = each entry's `id` (e.g. `coccyx`, `heel`, `scalp_crown`).

DEFAULT:
`""` (line 4801).

REQUIRED:
Same as Body Region — feeds the combined `location` string check.

VISIBLE WHEN:
Same Dialog, filtered to the current Body Region, and further filtered by Condition Type
(`allowedSiteIdsForConditionType`, line ~4516 — e.g. Diabetic Foot Ulcer/Venous Ulcer/Arterial Ulcer/
MASD/Excoriation each restrict the usable site list).

DEPENDENCIES:
- Each site has a fixed `type`: `midline`, `paired`, or `flexible` — this determines which Side options
  are offered (next control).
- Each site has a `surfaces` array (possibly empty) and/or a `forcedSurface` — this determines whether a
  Surface/Orientation selector appears at all, and if so with which options (next-next control).
- Sites flagged `descriptionRequired: true` (10 of the 61) require a free-text clarification field
  (`wound.locationClarification` — confirm exact field name during build).

PRODUCT-OWNER DECISION REQUIRED:
None — this list is already fully built; included here purely for completeness/content review per the
directive's explicit request ("provide the complete anatomical-site list").

---

### CONTROL: Side

LABEL:
`Side`

OPTIONS BY SITE TYPE (lines 4390–4399, 4535–4538):
- `midline` sites: no Side selector shown at all.
- `paired` sites: Left, Right, Bilateral.
- `flexible` sites: Left, Right, Bilateral, N/A.

STORED VALUES:
`left`, `right`, `bilateral`, `not_applicable` → `wound.side`.

DEFAULT:
`""` (line 4802).

VISIBLE WHEN:
Site type is `paired` or `flexible` (never for `midline`).

PRODUCT-OWNER DECISION REQUIRED:
None.

---

### CONTROL: Surface / Orientation

LABEL:
`Surface/Orientation`

OPTIONS (full controlled vocabulary, lines 4391–4399):
Anterior, Posterior, Medial, Lateral, Dorsal, Plantar, Palmar, Circumferential, N/A.

Per-site actual options come from that site's own `surfaces` array (e.g. Upper Arm offers Anterior,
Posterior, Medial, Lateral, Circumferential; Hand offers only Dorsal, Palmar). Sites with a
`forcedSurface` (e.g. Coccyx → `posterior`, Sternum → `anterior`) show **no selector** — the value is
silently fixed.

STORED VALUES:
`wound.surface` = one of the 9 values above.

DEFAULT:
`""` (line 4802).

VISIBLE WHEN:
Site has a non-empty `surfaces` array (i.e. no `forcedSurface`). `surfaceOptionsForSite`, lines 4540–4550.

DEPENDENCIES:
Extensions (additional contiguous locations) use the identical logic under the label `Surface` (not
`Surface/Orientation`) — lines 5327–5328. **Naming inconsistency, flagged in Contradiction Review C-2.**

PRODUCT-OWNER DECISION REQUIRED:
Should the Extension's label read "Surface/Orientation" to match the primary location field exactly?

---

### CONTROL: Pressure Injury Stage / Category

LABEL:
`Stage / Category`

OPTIONS (`PI_STAGE_OPTIONS_V2`, lines 4660–4663):
- Stage 1
- Stage 2
- Stage 3
- Stage 4
- Unstageable
- Deep Tissue Pressure Injury
- Unable to Determine

STORED VALUES:
`wound.stage` = the literal strings above.

DEFAULT:
`""` (line 4796).

REQUIRED:
Yes — `isWoundRecordMissingRequiredDetails` returns `true` if a pressure-injury wound has no stage (line
5891).

VISIBLE WHEN:
`variant === "pressureInjury"` only (line 5560ish).

DEPENDENCIES AND HIDDEN FIELDS:
- `"Unable to Determine"` → shows required `Reason Unable to Determine Stage` field
  (`wound.stageUnableToDetermineReason`); required by completion (line 5892).
- `PI_STAGES_REQUIRING_MEASUREMENT` = Stage 2, 3, 4, Unstageable → Length/Width (or
  `unableToMeasureReason`) required (line 5894).
- `PI_STAGES_REQUIRING_DEPTH` = Stage 3, 4 only → Depth (or `depthNotMeasuredReason`, with a
  legacy `unableToMeasureReason` fallback for pre-2026-10-21 records) required (line 5895).
  PRODUCT OWNER DIRECTIVE (2026-10-21) "Unstageable Depth Documentation" split Depth's
  not-measured reason out of the shared Length/Width `unableToMeasureReason` into its own
  `wound.depthNotMeasuredReason` field (options: N/A, Wound bed obscured by eschar, plus the
  same general reasons as Length/Width) so a wound may have numeric Length/Width recorded at
  the same time Depth is documented as not measured.
  Stage 2 and Unstageable never require Depth.
- Stage 1 and Deep Tissue Pressure Injury never require Length/Width/Depth at all (intact-skin findings).
- `PI_STAGES_HIDING_ADVANCED_FINDINGS` = Stage 1, Deep Tissue Pressure Injury → entire "Advanced Wound
  Findings" section is hidden (line 4680, rendered at 5646–5648).
- Exposed Structure pill options are further stage-filtered: Stage 2 → only "None observed"/"Unable to
  Determine"; Stage 3 → adds "Adipose"; Stage 4 (and all non-PI types) → full list including Fascia,
  Muscle, Tendon, Bone, Other (`exposedStructureOptionsForStage`, lines 4682–4687).

COMPLETION RULE:
Fully specified above (stage required; stage-specific measurement/depth required; Unable-to-Determine
reason required).

ERROR MESSAGE:
None — again, no inline validation text exists; only the assessment-level coverage panel's generic
`"Complete required details (stage, location, measurements) for each active impairment record"` hint
(line ~18312).

INVENTORY DISPLAY:
Shown directly as the Stage/Condition column value when `w.stage` is set (line 14168).

HISTORICAL BEHAVIOR:
Comment at lines 4651–4657 confirms a prior, more granular stage vocabulary existed (e.g. "Unstageable —
Slough/Eschar," "Medical Device Related") and such historical values are preserved read-only, never
rewritten, and simply not offered for new documentation.

PRODUCT-OWNER DECISION REQUIRED:
None — fully defined already.

---

### CONTROL: Device-Related Pressure Injury

LABEL:
`Device-Related Pressure Injury?`

OPTIONS:
No, Yes

STORED VALUES:
`wound.deviceRelated` (boolean).

DEFAULT:
`false` (line 4804).

VISIBLE WHEN:
`variant === "pressureInjury"` only (lines 5275–5278).

DEPENDENCIES:
`Yes` → shows required `Device Description (required)` free-text field (`wound.deviceDescription`).

COMPLETION RULE:
`deviceRelated === true` and `!deviceDescription` → record incomplete (line 5897).

PRODUCT-OWNER DECISION REQUIRED:
None.

---

### CONTROL: Wound Bed Visible

LABEL:
`Wound Bed Visible`

OPTIONS:
Yes, No, Partially

STORED VALUES:
`wound.woundBedVisible`.

DEFAULT:
`""` (line 4808).

VISIBLE WHEN:
`variant === "pressureInjury"` only (lines 5574–5576). **Not shown for any non-pressure condition type**,
despite the original directive listing it as a universal per-wound field.

REQUIRED:
No (not in completion function).

PRODUCT-OWNER DECISION REQUIRED:
Should "Wound Bed Visible" also apply to non-pressure wound types (Skin Tear, Surgical Wound, Diabetic
Foot Ulcer, Venous/Arterial Ulcer, etc.)? Today it is Pressure-Injury-only.

---

### CONTROL: Drainage Amount

LABEL:
`Drainage Amount`

OPTIONS:
None, Scant, Small, Moderate, Large, Unable to Assess

STORED VALUES:
`wound.drainage`.

DEFAULT:
`""` (line 4810).

VISIBLE WHEN:
Always, all variants (line 5577) — the only drainage/findings control that applies to every condition
type.

REQUIRED:
**Yes** — the only field (besides location and PI stage/measurement rules) required for every wound type,
PI or not (`if (!w.drainage) return true`, line 5901).

CONTROL TYPE:
Single-select (`FormSegmented`).

PRODUCT-OWNER DECISION REQUIRED:
None.

---

### CONTROL: Drainage Character

LABEL:
`Drainage Character`

OPTIONS:
Serous, Sanguineous, Serosanguineous, Purulent, Other, N/A

STORED VALUES:
`wound.drainageCharacter`.

DEFAULT:
`""` (line 4810).

VISIBLE WHEN:
Always, all variants (line 5578).

REQUIRED:
No — **not** required by completion, even though Drainage Amount is. (Flagged Contradiction Review C-3:
the directive asks whether "None and Present selected simultaneously" is prevented — see that section;
separately, "Drainage Amount = required but Drainage Character = not required" is itself an asymmetry
worth a product decision.)

CONTROL TYPE:
Single-select (`FormSegmented`). No dependent "Other — specify" free-text field exists today when
"Other" is chosen.

PRODUCT-OWNER DECISION REQUIRED:
1. Should Drainage Character also be required?
2. Should selecting "Other" require a free-text explanation (it currently does not)?

---

### CONTROL: Odor

LABEL:
`Odor`

OPTIONS (`WOUND_ODOR_OPTIONS`, line 4703):
None, Present, Unable to Assess

STORED VALUES:
`wound.odor`.

DEFAULT:
`""` (line 4810).

VISIBLE WHEN:
Always, all variants, no condition.

REQUIRED:
No.

BEFORE/AFTER CLEANSING OR SEVERITY SUB-QUESTION:
**Explicitly and intentionally absent.** Code comment (lines 4695–4702) documents that two earlier
approaches (a Before/After Cleansing split, and a 5-point None/Mild/Moderate/Strong-Foul/Unable-to-Assess
severity scale) were both built and then reverted per a "PRODUCT OWNER FINAL DIRECTIVE (2026-10-19)
'Integumentary Closeout'" — this is a **closed, already-decided** question, not open for re-litigation
unless the Product Owner explicitly reopens it.

HISTORICAL BEHAVIOR:
`migrateLegacyOdorValue(beforeVal, afterVal)` (lines 4711–4721) silently collapses any stale
Before/After-Cleansing or 5-point test data into the current 3-value scale on load — this only affects
unsaved/test fixtures, never a signed/locked assessment (per the function's own comment).

PRODUCT-OWNER DECISION REQUIRED:
None — already finalized.

---

### CONTROL: Surrounding Skin

LABEL:
`Surrounding Skin`

OPTIONS:
Intact, Red/Erythematous, Macerated, Fragile, Warm, Indurated, Other

STORED VALUES:
`wound.surroundingSkin`.

DEFAULT:
`""` (line 4810).

VISIBLE WHEN:
Always, all variants.

REQUIRED:
No.

CONTROL TYPE:
Single-select (`FormSegmented`). No "Other — specify" dependent field exists.

RELATIONSHIP TO REMOVED "SKIN OPEN OR INTACT" CONTROL:
`SKIN_OPEN_INTACT_OPTIONS = ["Open", "Intact"]` still exists as a constant (line 4692) but is explicitly
commented "Retained for reference only ... no longer has an editable control" (lines 4689–4691) — i.e. it
is fully retired and must **not** be reintroduced as a new generic field, confirming the directive's
Section 5 instruction is already satisfied in the current code.

PRODUCT-OWNER DECISION REQUIRED:
Should "Other" require free text? Today it does not.

---

### CONTROL: Signs of Infection Observed

LABEL:
`Signs of Infection Observed?`

OPTIONS:
No, Yes, Unable to Determine

STORED VALUES:
`wound.infectionConcern`.

DEFAULT:
`""` (line 4810).

VISIBLE WHEN:
Always.

### Dependent control: Observed Findings

LABEL:
`Observed Findings`

OPTIONS:
Redness, Warmth, Increased drainage, Purulent drainage, Odor, Induration, Other

STORED VALUES:
`wound.infectionSignsObserved` (array).

DEFAULT:
`[]` (line 4811).

VISIBLE WHEN:
`wound.infectionConcern === "Yes"` only (lines 5584–5595). Not shown for "No" or "Unable to Determine."

CONTROL TYPE:
Multi-select (`FormPillGroup`).

DEPENDENT "OTHER":
Selecting "Other" in the array → shows `Other — Specify` free text, `wound.infectionSignsOtherNotes`
(lines 5591–5595).

REQUIRED:
Neither the parent nor the child list is required by completion.

PRODUCT-OWNER DECISION REQUIRED:
Should "No infection signs with infection findings selected" even be possible? Today it is structurally
impossible (the findings list is only rendered/editable when the parent is "Yes"), so this specific
contradiction from the directive's example list **cannot occur** in the current UI. See Contradiction
Review.

---

### CONTROL: Measurement Method

LABEL:
`Measurement Method`

OPTIONS:
Ruler/Tape, Wound Tracing, Photography With Scale, Other

STORED VALUES:
`wound.measurementMethod`.

DEFAULT:
`""` (line 4810).

REQUIRED:
No — not itself required even when Length/Width/Depth are required.

PRODUCT-OWNER DECISION REQUIRED:
Should Measurement Method be required whenever a Length/Width/Depth value is entered?

---

### CONTROL: If Not Measured, Reason

LABEL:
`If Not Measured, Reason`

OPTIONS (`UNABLE_TO_MEASURE_REASON_OPTIONS`, lines 4729–4731):
Patient Discomfort, Patient Declined, Dressing/Device Not Removable, Imminent Death/Active Dying, Unable
to Reposition Safely, Not Clinically Indicated Today, Other

(Note: this differs substantially from the directive's proposed list, e.g. "Unable to visualize,"
"Caregiver declined," "Safety concern," "Diffuse area not discretely measurable," "Technical limitation"
are not present; "Imminent Death/Active Dying" and "Not Clinically Indicated Today" are present in code
but not in the directive's proposed list. **Reconciliation decision needed** — see below.)

STORED VALUES:
`wound.unableToMeasureReason`.

DEFAULT:
`""` (line 4810).

REQUIRED:
Conditionally — satisfies the Length/Width/Depth requirement as an alternative (lines 5894–5899) for both
PI and non-PI wounds.

LENGTH/WIDTH/DEPTH BEHAVIOR WHEN A REASON IS SELECTED:
**They remain visible, enabled, and editable** — selecting a reason does **not** hide, disable, or clear
them (lines 5597–5599 render unconditionally). This means a nurse could select "Patient Declined" and
still type in a Length value; nothing in the code currently flags or blocks that combination
(Contradiction Review C-4).

DEPENDENT "OTHER":
No dependent free-text field exists when "Other" is selected. (Directive calls for a required explanation
— not currently implemented.)

PRODUCT-OWNER DECISION REQUIRED:
1. Reconcile the 7-item implemented list against the directive's proposed list — which exact 7–9 values
   are final?
2. Should "Other" require free text? (Not implemented today.)
3. Should selecting any reason disable/clear Length/Width/Depth to prevent the contradictory combination
   noted above?

---

### CONTROL: Skin Tear — Flap Status

LABEL:
`Flap Status`

OPTIONS:
Flap Intact, Flap Partial Loss, Flap Complete Loss, N/A

STORED VALUES:
`wound.skinTearFlapStatus`.

VISIBLE WHEN:
`variant === "other" && conditionType === "skin_tear"` only (lines 5612–5614).

REQUIRED:
No.

PRODUCT-OWNER DECISION REQUIRED:
None.

---

### CONTROL: Surgical Wound — Closure Status

LABEL:
`Closure Status`

OPTIONS:
Closed/Approximated, Partially Open, Dehisced, Healing by Secondary Intention

(Directive's proposed list was "Approximated/Closed, Open, Dehisced, Unable to Determine" — differs in
wording and in the fourth value. **Reconciliation decision needed.**)

STORED VALUES:
`wound.surgicalClosureStatus`.

VISIBLE WHEN:
`variant === "other" && conditionType === "surgical_wound"` only (lines 5615–5617).

REQUIRED:
No.

PRODUCT-OWNER DECISION REQUIRED:
Reconcile implemented 4-value list against directive's proposed list — final values?

---

### CONTROL: MASD — Moisture Source

LABEL:
`Moisture Source`

OPTIONS:
Incontinence, Perspiration, Wound Drainage, Peristomal Output, Other

STORED VALUES:
`wound.masdMoistureSource`.

VISIBLE WHEN:
`variant === "other" && conditionType === "moisture_associated_skin_damage"` only (lines 5618–5620).

DEPENDENT "OTHER":
No dependent free-text field exists today.

PRODUCT-OWNER DECISION REQUIRED:
Should "Other" require free text?

---

### CONTROL: Advanced Wound Findings (section + 5 sub-controls)

LABEL:
`Advanced Wound Findings` (collapsible, default collapsed, "Show ▼"/"Hide ▲")

WHOLE-SECTION HIDDEN WHEN:
1. `variant === "other"` and conditionType is Rash, Bruising, Excoriation, or MASD, **or**
2. `variant === "pressureInjury"` and stage is Stage 1 or Deep Tissue Pressure Injury.

(All other condition types/stages show the section.)

#### Sub-control: Undermining Present?
OPTIONS: No, Yes, Unable to Determine — `wound.underminingPresent`.
If Yes → `Undermining Clock Start` (`wound.underminingClockStart`), `Undermining Clock End`
(`wound.underminingClockEnd`), `Max Undermining Depth (cm)` (`wound.underminingDepthCm`).

#### Sub-control: Tunneling Present?
OPTIONS: No, Yes, Unable to Determine — `wound.tunnelingPresent`.
If Yes → repeatable rows, each with `Clock Position` (`t.clockPosition`) and `Depth (cm)` (`t.depthCm`),
plus `Remove` per row and `+ Add Another Tunnel`.

#### Sub-control: Slough Present?
OPTIONS: No, Yes, Unable to Determine — `wound.sloughPresent`.
PRODUCT OWNER REVIEW (2026-10-21) "Simplify Advanced Wound Findings" removed the `Slough Estimated %`
(`wound.sloughPercentage`) and `Slough Description` (`wound.sloughDescription`) sub-fields from entry —
SNS is a hospice EMR, not a specialty wound-care platform; percentage/detailed tissue characterization is
typically provided by wound specialists/clinics/hospitals/facilities. Any pre-existing values remain in
form_data (never deleted) but are no longer shown or collected.

#### Sub-control: Eschar Present?
OPTIONS: No, Yes, Unable to Determine — `wound.escharPresent`.
PRODUCT OWNER REVIEW (2026-10-21) "Simplify Advanced Wound Findings" removed the `Eschar Estimated %`
(`wound.escharPercentage`) and `Eschar Description` (`wound.escharDescription`) sub-fields from entry, for
the same reason as Slough above. Any pre-existing values remain in form_data (never deleted) but are no
longer shown or collected.

#### Sub-control: Exposed Structure
Multi-select (`FormPillGroup`) — `wound.exposedStructure`.
- Pressure Injury: options vary by stage (Stage 2 → None observed/Unable to Determine only; Stage 3 →
  adds Adipose; Stage 4 → full list: None observed, Adipose, Fascia, Muscle, Tendon, Bone, Other, Unable
  to Determine).
- Non-pressure variants: fixed full list (same 8 values).
- "Other" selected → `Exposed Structure — Other (specify)` (`wound.exposedStructureOtherNotes`).

REQUIRED:
None of the above are required by completion.

PRODUCT-OWNER DECISION REQUIRED:
None currently — fully specified in code with clear, intentional stage-based gating.

---

### CONTROL: Photo Source

LABEL:
`Photo Source`

OPTIONS (`WOUND_PHOTO_SOURCE_OPTIONS`, line 4267):
Visiting RN, Supervising RN, Wound Specialist, Hospital Records

(Note: "Administrator Upload" was explicitly **removed** per a 2026-10-20 "Photos Are Optional Supporting
Evidence" directive — comment lines 4260–4266. The current directive's proposed list re-adds
"Administrator Upload" and "Other Clinical Source" and a separate "LVN" — **reconciliation decision
needed.**)

### CONTROL: Captured By (Role) — a distinct field from Photo Source

LABEL:
`Captured By (Role)`

OPTIONS (`WOUND_PHOTO_DISCIPLINE_OPTIONS`, line 4256):
RN, LVN, Wound Nurse, Clinical Supervisor, Physician

STORED VALUES:
`photo.source` (Photo Source) and `photo.discipline` (Captured By Role) — two separate fields by design
(comment lines 4254–4259: "WHO captured the photo is a different question from WHERE it came from").

Additional photo fields: `photo.capturedBy` (name, free text), `photo.notes` (Caption), `photo.photoDate`,
`photo.photoTime` (both display-only in current JSX — no editable date/time control found).

REQUIRED:
**Photos themselves are never required** — `recommendPhoto = photos.length === 0 &&
PHOTOGRAPHABLE_WOUND_CONDITION_TYPES.has(conditionType)` only shows a non-blocking recommendation banner
(lines 4905, 4946–4950); the coverage item's `check` always returns `true` (lines 18340–18345) and is
explicitly commented as informational-only, never `action_required`.

SORT CONTROLS:
`Newest First` / `Oldest First (Timeline)` toggle, shown only when `photos.length > 1`; default sort is
newest-first.

ADD CONTROL:
`+ Add Photo` — hidden file input, `accept="image/*"`, `capture="environment"`.

PRODUCT-OWNER DECISION REQUIRED:
Reconcile final Photo Source list — keep current 4-value list (no Administrator Upload) or restore it per
this directive's proposed list? This is a direct conflict between two different Product Owner directives
(2026-10-20 removed it; the current message's Section 4.W re-proposes it) and needs an explicit, dated
tie-breaker decision.

---

### CONTROL: Status Since Prior

LABEL:
`Status Since Prior`

OPTIONS (`WOUND_STATUS_SINCE_PRIOR_OPTIONS`, lines 4733–4736):
Initial Assessment, Stable/No Significant Change, Improving, Worsening, Newly Identified, Healing, Unable
to Compare

STORED VALUES:
`wound.statusSincePrior`.

DEFAULT:
`""` (line 4821).

VISIBLE WHEN:
Only when `wound.statusSincePrior` is already truthy (lines 5606–5611) — **a new record never shows this
control at all**, since the default is empty and nothing currently sets it. This means, as implemented
today, there is no way for a user to set this value on a new wound from the UI — it only ever displays an
already-populated (likely legacy or backend-set) value. **This is a real gap, flagged below.**

PRODUCT-OWNER DECISION REQUIRED:
Is this field intended to be user-settable on every visit? If so, the visibility rule needs to change from
"only if already set" to something like "shown whenever Status = Existing/COC," matching the directive's
intent for a nurse to document worsening/improving per numbered wound. Today it is effectively
inoperable for new documentation.

---

### CONTROL: Wound Assessment Summary (assessment-level, not per-wound)

LABEL:
`Wound Assessment Summary` (collapsed by default; label appends `" (documented)"` once any field has
content)

COMPONENT:
`WoundAssessmentSummaryPanel`, lines 14191–14257. Confirmed assessment-level: stored directly on the
Integumentary section's own `data` object (never inside any individual `wounds[]` record), rendered
exactly once from `SkinImpairmentWorkspacePage` regardless of wound count (lines 6049–6050, 6172–6176,
14192–14200 comment block).

IMPLEMENTED FIELDS:
| Field | Stored at | Notes |
|---|---|---|
| Wound Assessment Narrative | `data.woundAssessmentNarrative` | Free-text, 4-row textarea. Placeholder text references "Clinical interpretation, progression summary, family education, MD notification, treatment changes, goals of care" — **these six concepts are placeholder guidance only, not separate structured fields.** |
| Wound Specialist Referral (status) | `data.woundSpecialistReferral.status` | Options: Not Needed, Recommended, Ordered, Completed |
| Referral Date | `data.woundSpecialistReferral.date` | Shown only when status ≠ Not Needed/blank |
| Recommendation Summary | `data.woundSpecialistReferral.summary` | Free text, shown with Date |
| New Orders Received | `data.woundMdOrders.received` | Yes/No |
| Orders Narrative Summary | `data.woundMdOrders.summary` | Free text, shown only when `received === true` |

NOT FOUND AS SEPARATE STRUCTURED FIELDS (only covered by the single free-text narrative's placeholder
text):
- Overall wound status
- Worsening wounds / Improving wounds
- Family education
- MD notification (distinct from "New Orders Received")
- Goals of care

REQUIRED:
No — the whole panel is optional (`hasContent` only changes the header label, never blocks anything).

PRODUCT-OWNER DECISION REQUIRED:
The directive (and the user's earlier "PRODUCT OWNER CORRECTION" messages this session) explicitly listed
six supported narrative purposes (overall summary, worsening/improving, family education, MD notification,
new orders, specialist referral, goals of care) as things "THE NARRATIVE SHALL SUPPORT." Today, four of
those seven are supported only as placeholder guidance inside one free-text box, not as distinct
structured fields with their own stored values. **Decision needed:** should any of these five become
their own structured field (e.g., a `Family Education Provided` Yes/No + notes, an `MD Notified` Yes/No +
notes, separate from the narrative and from the already-structured referral/orders blocks)? Or is the
single free-text narrative intentionally sufficient for all of them except referral/orders?

---

## 2. Current-code trace summary (component map)

| Concern | Component | Lines |
|---|---|---|
| Workspace page / layout, add-wound buttons, detail header | `SkinImpairmentWorkspacePage` | 6081–6280 (approx.) |
| Full per-wound editor form | `WoundRecordCard` | ~5100–5900 |
| Structured location Dialog editor | `StructuredWoundLocationSelector` | ~5140–5330 |
| Completion check | `isWoundRecordMissingRequiredDetails` | 5884–5905 |
| Photo history UI | `WoundPhotoHistory` | 4883–4975 (approx.) |
| Patient Wound Map | `PatientWoundMap` | 14054–14139 |
| Wound Inventory table | `WoundInventoryTable` | 14143–14204 |
| Assessment-level summary | `WoundAssessmentSummaryPanel` | 14191–14257 |
| Coverage/completeness panel items | `SKIN_COVERAGE_ITEMS` | 18252–~18360 |

Values implemented but not currently visible anywhere in new-entry UI: `other_non_pressure_ulcer`,
`traumatic_wound`, `ostomy_peristomal_condition` (Condition Type legacy-only enum members).

Values visible but not persisted to any dependent/clinical-note output: nearly every structured field —
**no wound-specific clinical-note generator exists in this file at all.** The only text that leaves the
structured model today is the one assessment-level narrative box, user-typed.

Values duplicated elsewhere: none found — Surrounding Skin and the retired Skin Open/Intact control are
confirmed distinct, non-overlapping fields (see Surrounding Skin entry above).

Undefined abbreviations: none remain — "COC" has an inline definition already in code (see above).

---

## 3. Contradiction review (reported, not fixed)

| ID | Contradiction | Currently prevented? |
|---|---|---|
| C-1 | Inventory table shows `—` for an unset Status; the editor's own Status control shows "New" as its fallback for the same unset value. Same wound, two different displayed values depending on which screen you're looking at. | **Not prevented** — pure display inconsistency, not a data contradiction, but confusing. |
| C-2 | The primary location editor labels the surface field "Surface/Orientation"; the Extension-location sub-form uses just "Surface" for the identical control. | **Not prevented** (naming only). |
| C-3 | Drainage Amount is required for completion; Drainage Character is not, despite being presented as a co-equal pair in the same row. | **Not prevented** (asymmetric requirement, not a logical contradiction). |
| C-4 | A reason is selected under "If Not Measured, Reason" while Length/Width/Depth still have numeric values entered — both can coexist because the measurement fields are never hidden/disabled/cleared when a reason is chosen. | **Not prevented.** |
| C-5 (directive example) Pressure Injury without Stage/Category | **Prevented** — completion function blocks it (line 5891). |
| C-6 (directive example) Stage 1 with a depth requirement | **Prevented** — Stage 1 is not in `PI_STAGES_REQUIRING_DEPTH` nor `PI_STAGES_REQUIRING_MEASUREMENT`; no depth is ever required for Stage 1. |
| C-7 (directive example) Diabetic Foot Ulcer at Coccyx / Venous Ulcer at Ear | **Prevented at the site-list level** — `allowedSiteIdsForConditionType` restricts Diabetic/Venous/Arterial Ulcer and MASD/Excoriation to a condition-appropriate site subset (exact subset not enumerated by this pass; recommend a follow-up trace if the exact allowed-site list per condition type is needed for sign-off). |
| C-8 (directive example) Skin Tear with Pressure-Injury Stage | **Structurally prevented** — `wound.stage` (PI Stage/Category control) is only rendered when `variant === "pressureInjury"`; Skin Tear is always `variant === "other"`, so the Stage control never appears on a Skin Tear record in the first place. |
| C-9 (directive example) Purulent drainage with "N/A" drainage character selected simultaneously | **N/A is not a contradiction here** — Drainage Character is single-select; "Purulent" and "N/A" cannot both be the stored value at once. This example doesn't map onto the current single-select data model. |
| C-10 (directive example) "None" and "Present" selected simultaneously (Odor) | **Not possible** — single-select (`FormSegmented`); only one value can be stored. |
| C-11 (directive example) "No infection signs" with infection findings selected | **Structurally prevented** — the Observed Findings list only renders (and is only ever interactable) when Signs of Infection = "Yes" (lines 5584–5595). |
| C-12 (directive example) Measurement values plus a contradictory not-measured reason | Same as C-4 above — **not prevented.** |

---

## 4. Compact wound-selector mockup (future build, NOT authorized to code yet)

Per the Product Owner's clarification this turn: the Wound Inventory table remains the live selector
today; this mockup is for the **later-restored** compact dropdown only, after this whole document is
approved.

```
Select Wound                                    ▼
┌─────────────────────────────────────────────────┐
│ #1 — Coccyx — Pressure Injury — Stage 1          │
│ #2 — Location Needed — Pressure Injury — Stage   │
│       Required                                   │
│ #3 — Left Posterior Calf — Pressure Injury —     │
│       Stage 2                                    │
│ #4 — Left Forearm — Skin Tear                    │
│ #5 — Perineum — MASD                             │
└─────────────────────────────────────────────────┘
```

Definitions (proposed, for approval — not yet built):
- **Sort order:** active wounds first in ascending wound-number order, then resolved wounds, also
  ascending — matching the Inventory table's existing "no re-sort, preserve array order" behavior so the
  two selectors never disagree on ordering.
- **Active selection:** the row matching `selectedWoundId` is visually highlighted exactly as the
  Inventory table highlights it today (`COLORS.tealBg`), so both selectors always agree about which wound
  is "current."
- **Incomplete indicator:** any wound where `isWoundRecordMissingRequiredDetails(w)` is `true` shows the
  existing missing-detail wording inline (e.g. "Stage Required," "Location Needed") instead of its real
  Stage/Location value — reusing the already-implemented completeness function, not a new one.
- **Resolved-wound behavior:** still listed (never hidden — Inventory shows resolved wounds too), but
  visually de-emphasized (muted text) and grouped after all active wounds.
- **15+ wounds:** the list simply scrolls inside the dropdown's popover; no pagination needed at this
  volume.
- **Search threshold:** proposed only when wound count exceeds ~10, consistent with the directive's "search
  behavior for high wound counts" question — exact threshold is a Product Owner decision, not yet fixed.
- **Marker click → dropdown sync:** proposed yes — clicking a map marker updates `selectedWoundId`, which
  this dropdown would read the same way the Inventory table already does, so they'd stay in sync
  automatically with no new wiring beyond using the same state variable.
- **Dropdown selection → marker highlight:** same answer, same direction — both already key off the one
  shared `selectedWoundId`/`onSelectWound` pair that `PatientWoundMap` and `WoundInventoryTable` both use
  today, so adding this dropdown as a third consumer of that same pair is the only change needed when it
  is eventually built.
- **Keyboard behavior:** standard combobox (arrow keys to move, type-ahead to jump, Enter to select) —
  same behavior already provided by the `FormSelect`/Radix `Select` primitive used everywhere else in this
  file, so no new interaction pattern would need to be invented.

---

## 5. Product-Owner decisions required (consolidated list)

1. Should `COC` status be hidden on an initial admission assessment (vs. only follow-up/COC visits)?
2. Should selecting "Resolved" or "COC" status require an accompanying note/reason? (Currently no.)
3. Should "Unknown" for Present at Admission require a free-text explanation? (Currently no.)
4. Should Traumatic Wound and Peristomal Skin Condition be added back to the Condition Type new-entry
   picker? (Enum values already exist, legacy-only today.)
5. Should the Extension-location "Surface" label read "Surface/Orientation" to match the primary field?
6. Should Wound Bed Visible apply to non-pressure wound types, not just Pressure Injury?
7. Should Drainage Character become required (matching Drainage Amount)?
8. Should "Other" selections (Drainage Character, Surrounding Skin, MASD Moisture Source, Exposed
   Structure, If-Not-Measured-Reason) require a dependent free-text field? (None do today.)
9. Final reconciliation of the "If Not Measured, Reason" option list — 7 implemented values vs. the
   directive's proposed list; which exact set is final?
10. Should selecting an "If Not Measured" reason disable/clear Length/Width/Depth to prevent the two
    coexisting (Contradiction C-4/C-12)?
11. Final reconciliation of Surgical Wound "Closure Status" option list — implemented 4 values vs.
    directive's proposed 4 values (different wording/4th value).
12. Final reconciliation of Photo Source — current 4-value list (Administrator Upload removed 2026-10-20)
    vs. this directive's proposed list (re-adds Administrator Upload + Other Clinical Source + LVN as a
    source rather than only a captured-by-role value). This is a direct conflict between two dated
    directives and needs an explicit tie-breaker.
13. Should "Status Since Prior" become user-settable on new records (currently only displays if already
    populated, so new documentation cannot set it today)? If yes, what should the visibility rule be?
14. Should any of the five Wound Assessment Summary purposes currently covered only by free-text narrative
    placeholder guidance (overall status, worsening/improving, family education, MD notification, goals
    of care) become their own structured field with a stored value, separate from the narrative box?
15. Confirm the final Side vocabulary — code implements `left/right/bilateral/not_applicable` (4 values,
    no explicit `midline`-as-a-selectable-value since midline sites simply hide the control); directive
    proposed 5 values including a literal "Midline" option. Is a literal "Midline" selectable value ever
    needed, or is "no selector shown" the correct behavior for midline sites as implemented?

No code, CSS, or architecture changes were made while preparing this document.
