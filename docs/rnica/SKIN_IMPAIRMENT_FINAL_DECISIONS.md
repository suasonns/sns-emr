# SUPERSEDED — DO NOT IMPLEMENT

The Product Owner has since issued the approved implementation specification:

`SKIN_IMPAIRMENT_CONTROLLED_VALUES_FINAL.md`

That file controls on every point, including anywhere it conflicts with a recommendation below (for
example, Photo Sources: this document recommended keeping Administrator Upload removed; the final
specification restores it — the final specification wins). This document is retained only as historical
reference for the reasoning that preceded the final specification.

---

# Skin Impairment — Final Decision Package

**Status:** Pure decision-reduction document. No code, CSS, markup, or architecture was touched to
produce this file. Derived entirely from `docs/rnica/SKIN_IMPAIRMENT_CONTROLLED_VALUES.md` and direct
`sns-emr-frontend/src/components/RNICA.jsx` citations already gathered — no new code exploration beyond
what that document already traced.

**Purpose:** collapse the 15 open questions in the prior spec into the 6 Product-Owner priorities below,
each as a single, decidable page. Everything not in this priority list is intentionally not repeated here
— see the full spec for the remainder.

No screenshots were captured (no UI/code work is authorized in this phase); each page instead gives a
concrete **text-based before/after example** in place of a screenshot, drawn directly from the existing
code paths.

---

## 1. Pressure Injury Workflow

**CURRENT IMPLEMENTATION**
`+ Pressure Injury` is a dedicated button, separate from the Condition Type picker (`RNICA.jsx` lines
6154–6155, 4794–4795). It auto-sets `conditionType: "pressure_injury"` and `presentAsPressureInjury: true`
the instant the record is created — the user never sees or re-picks "Pressure Injury" from a dropdown.
Once created, Stage/Category becomes required (line 5891); Length/Width/Depth become required per-stage
(`PI_STAGES_REQUIRING_MEASUREMENT`/`_DEPTH`, lines 4669/4673); Wound Bed Visible, Device-Related toggle,
and the full stage-gated Exposed Structure list are all **only** shown on this variant (lines 5574–5576,
5275–5278, 4682–4687).

**PROBLEM**
Wound Bed Visible is gated to Pressure Injury only. Clinically, Wound Bed Visible is just as relevant for
Surgical Wounds, Diabetic/Venous/Arterial Ulcers, and Fungating/Malignant Wounds — all of which can have
an open wound bed — but the control is invisible on those records today.

**RECOMMENDED RESOLUTION**
Extend Wound Bed Visible's visibility to every non-intact-skin condition type (i.e., every condition type
except Rash, Bruising, Excoriation, and MASD — the same exclusion set already used for the Advanced Wound
Findings section, lines 5646–5648). This reuses an existing exclusion list rather than inventing a new
one.

**IMPACT**
One visibility-condition change on one existing control (`wound.woundBedVisible`'s render guard). No new
field, no new stored value, no data migration — the field and its 3 options (Yes/No/Partially) already
exist and are already wired to `wound.woundBedVisible` for Pressure Injury; this only changes which
condition types can see it.

**TEXT-BASED EXAMPLE**
```
TODAY (Surgical Wound record):
  Condition Type: Surgical Wound
  Closure Status:  [Closed/Approximated ▾]
  Drainage Amount: [None ▾]
  ... (no Wound Bed Visible control appears anywhere)

PROPOSED:
  Condition Type: Surgical Wound
  Closure Status:  [Closed/Approximated ▾]
  Wound Bed Visible: [Yes ▾]        ← newly shown
  Drainage Amount:   [None ▾]
```

---

## 2. Condition Type Final List

**CURRENT IMPLEMENTATION**
The new-entry picker offers exactly 12 values (`RNICA.jsx` lines 4225–4237, confirmed "exact approved
12-item picker list" per a 2026-11-19 comment): Skin Tear, Moisture-Associated Skin Damage, Rash,
Bruising, Excoriation, Open Lesion, Fungating/Malignant Wound, Surgical Wound, Diabetic Foot Ulcer, Venous
Ulcer, Arterial Ulcer, Other Skin Condition — plus Pressure Injury via its own dedicated button (not in
this list). Three additional enum values exist in the data model but are **not offered** as new-entry
choices: `other_non_pressure_ulcer`, `traumatic_wound`, `ostomy_peristomal_condition` — legacy-read-only.

**PROBLEM**
Earlier directives in this project referenced Traumatic Wound and Peristomal Skin Condition as needed
condition types. They exist in the stored-value enum (so old data referencing them still displays
correctly) but a nurse cannot select either one for new documentation today.

**RECOMMENDED RESOLUTION**
Lock the list at the current 12 approved items (already a deliberate, dated Product Owner decision,
2026-11-19) and treat Traumatic Wound / Peristomal Skin Condition as intentionally retired from new entry,
**unless** the Product Owner explicitly overrides the 2026-11-19 decision. Default recommendation: no
change — don't reopen an already-settled list without an explicit override, since "Other Skin Condition"
already covers any residual case.

**IMPACT**
Zero, if the recommendation is accepted — no code change. If overridden, it is a 2-line addition to one
constant array (`WOUND_CONDITION_TYPES`) with no data-model change (the enum values already exist).

**TEXT-BASED EXAMPLE**
```
CURRENT PICKER (12 items):
  Skin Tear · Moisture-Associated Skin Damage · Rash · Bruising · Excoriation
  Open Lesion · Fungating/Malignant Wound · Surgical Wound · Diabetic Foot Ulcer
  Venous Ulcer · Arterial Ulcer · Other Skin Condition

NOT OFFERED (legacy-only, still valid on old records):
  Traumatic Wound · Peristomal Skin Condition · Other Non-Pressure Ulcer
```

---

## 3. Location Model

**CURRENT IMPLEMENTATION**
One Dialog-based location editor (`StructuredWoundLocationSelector`) drives four chained controls: Body
Region (8 options) → Anatomical Site (61 entries, filtered by region and by condition-type-allowed subset)
→ Side (0, 3, or 4 options depending on site type: midline/paired/flexible) → Surface/Orientation (site-
specific subset of a 9-value vocabulary, or auto-fixed via `forcedSurface` with no visible control at
all). An "Extensions" sub-form repeats the Surface control under the plain label "Surface" instead of
"Surface/Orientation."

**PROBLEM**
Only one real problem exists in this area today: the Extensions sub-form's control is labeled
inconsistently ("Surface" vs. the primary form's "Surface/Orientation") for the identical field and option
set. Everything else in the location chain (region → site → side → surface cascading logic) is already
fully built, deliberate, and has no open question.

**RECOMMENDED RESOLUTION**
Rename the Extensions sub-form's label from "Surface" to "Surface/Orientation" to match the primary
field exactly. No other change to the location model is recommended or needed.

**IMPACT**
One string label change on one existing control. No stored-value change, no new field, no visibility-rule
change.

**TEXT-BASED EXAMPLE**
```
PRIMARY LOCATION:                  EXTENSION LOCATION (today):
  Body Region: Lower Extremity        Surface: [Anterior ▾]   ← inconsistent label
  Anatomical Site: Calf
  Side: [Left ▾]
  Surface/Orientation: [Anterior ▾]

EXTENSION LOCATION (proposed):
  Surface/Orientation: [Anterior ▾]   ← now matches
```

---

## 4. Staging Model

**CURRENT IMPLEMENTATION**
A dedicated Stage/Category control (7 values: Stage 1–4, Unstageable, Deep Tissue Pressure Injury, Unable
to Determine) exists **only** for the Pressure Injury variant (`RNICA.jsx` lines 5560 area, 4660–4663).
Every non-pressure condition type (Diabetic Foot Ulcer, Venous Ulcer, Arterial Ulcer, Surgical Wound,
Skin Tear, etc.) has **no** staging/grading control of any kind — the Inventory table's "Stage/Condition"
column simply falls back to the Condition Type's display label (e.g. "Diabetic Foot Ulcer") when
`wound.stage` is empty (line 14168).

**PROBLEM**
Clinically, several non-PI condition types have their own standard staging/grading systems (e.g., Wagner
Grade for Diabetic Foot Ulcer, CEAP classification for Venous Ulcer) that are not represented anywhere in
the current model. Skin Tear already has its own narrower "Flap Status" control, and Surgical Wound has
"Closure Status" — so there's precedent for condition-specific sub-staging, but Diabetic/Venous/Arterial
Ulcers currently have no equivalent.

**RECOMMENDED RESOLUTION**
Do not add new staging/grading controls in this pass — this would be new-field work, out of scope for a
decision-reduction/content-freeze phase. Record this as a deliberate, open future-scope item: Product
Owner to decide whether Diabetic Foot Ulcer / Venous Ulcer / Arterial Ulcer need their own condition-
specific staging field (mirroring the existing Flap Status / Closure Status pattern), or whether free-text
narrative is sufficient for these three types indefinitely.

**IMPACT**
None today (no change recommended). If approved later, each new staging field follows the exact pattern
already proven for Flap Status/Closure Status: one `FormSegmented` control, visible only for its one
condition type, not required by completion.

**TEXT-BASED EXAMPLE**
```
Skin Tear (has its own sub-stage):        Diabetic Foot Ulcer (has none):
  Flap Status: [Flap Intact ▾]              Condition Type: Diabetic Foot Ulcer
                                             (no staging/grading control exists)
```

---

## 5. Photo Sources

**CURRENT IMPLEMENTATION**
`WOUND_PHOTO_SOURCE_OPTIONS` (line 4267) = Visiting RN, Supervising RN, Wound Specialist, Hospital
Records — 4 values. A 2026-10-20 "Photos Are Optional Supporting Evidence" directive explicitly **removed**
a 5th value, "Administrator Upload," per its own comment (lines 4260–4266). A separate, distinct field,
"Captured By (Role)" (`WOUND_PHOTO_DISCIPLINE_OPTIONS`, line 4256), independently covers RN, LVN, Wound
Nurse, Clinical Supervisor, Physician.

**PROBLEM**
An earlier message in this same project session asked for Photo Source to include "Administrator Upload"
and "Hospital Records" as sources — "Hospital Records" already matches; "Administrator Upload" directly
conflicts with the 2026-10-20 removal decision. This is a direct conflict between two dated Product Owner
directives with no tie-breaker yet.

**RECOMMENDED RESOLUTION**
Keep the 2026-10-20 decision as authoritative (it is the more recent, explicitly-reasoned directive) and
do **not** re-add "Administrator Upload" to Photo Source, unless the Product Owner explicitly states this
decision reverses 2026-10-20. "LVN" as a photo-captured-by role is already covered by the separate
"Captured By (Role)" field, not Photo Source — no gap exists there.

**IMPACT**
None if the recommendation is accepted (no change). If overridden, it is a 1-line addition to one constant
array with no stored-value or migration impact (adding a value never breaks reads of existing records).

**TEXT-BASED EXAMPLE**
```
Photo Source (current, 4 values):     Captured By Role (separate field, 5 values):
  Visiting RN                           RN
  Supervising RN                        LVN
  Wound Specialist                      Wound Nurse
  Hospital Records                      Clinical Supervisor
                                        Physician
  (Administrator Upload — removed 2026-10-20, not proposed to return)
```

---

## 6. Completion Logic

**CURRENT IMPLEMENTATION**
`isWoundRecordMissingRequiredDetails()` (lines 5884–5905) is the single completeness check. It requires:
Location; Stage (PI only, via its own stage-specific measurement/depth/reason rules); Length/Width (or a
documented reason) for non-PI wounds; and **Drainage Amount** (required for every wound type, PI or not —
the only clinically-descriptive field required universally). Drainage Character, Surrounding Skin, Wound
Bed Visible, Odor, Present at Admission, and Status are **not** required by this function for any wound
type.

**PROBLEM**
Drainage Amount and Drainage Character are presented as a co-equal pair in the same row of the editor, but
only Amount is required — an asymmetry a nurse is likely to find confusing (e.g., they can save a record
with "Moderate" drainage amount but no drainage character at all).

**RECOMMENDED RESOLUTION**
Add Drainage Character to the completion requirement, exactly mirroring the existing Drainage Amount
check (`if (!w.drainage) return true;` → add the equivalent `if (!w.drainageCharacter) return true;`
immediately after it). No other field is recommended for promotion to required in this pass — this keeps
the change to the one clearest asymmetry rather than expanding scope.

**IMPACT**
One added line in one existing function. No new field, no stored-value change — `wound.drainageCharacter`
already exists and is already collected; this only changes whether its absence is treated as "incomplete."
Any currently-saved record missing Drainage Character would newly show up as incomplete in the coverage
panel until updated (no data loss, no migration — display-only effect).

**TEXT-BASED EXAMPLE**
```
TODAY — considered COMPLETE:            PROPOSED — considered INCOMPLETE until fixed:
  Drainage Amount:    Moderate            Drainage Amount:    Moderate
  Drainage Character: (blank)             Drainage Character: (blank)  ← now blocks completion
```

---

## Summary table

| # | Priority | Recommended Resolution | Code Change Size |
|---|---|---|---|
| 1 | Pressure Injury Workflow | Extend Wound Bed Visible beyond PI-only | 1 visibility condition |
| 2 | Condition Type Final List | Keep 12-item list as-is (no change) | None |
| 3 | Location Model | Rename Extensions' "Surface" → "Surface/Orientation" | 1 label string |
| 4 | Staging Model | No change now; flag Diabetic/Venous/Arterial grading as future scope | None |
| 5 | Photo Sources | Keep 2026-10-20 decision; do not re-add Administrator Upload | None |
| 6 | Completion Logic | Require Drainage Character alongside Drainage Amount | 1 added line |

No code, CSS, markup, maps, or controls were added or changed while preparing this document. Awaiting
Product Owner sign-off on each of the 6 recommendations above before any implementation begins.
