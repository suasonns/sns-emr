# RNICA Body Systems — Unresolved Clinical Decisions (Owner + Hospice RN Review)

These are the only questions that cannot be resolved from the existing code, data model, HOPE/SFV
mappings, validation rules, or the authoritative sources reviewed (SAFER Guides, AHRQ, WCAG, CMS
documentation-integrity guidance, CA Title 22 hospice framework, hospice terminal-decline guidance).
Each requires an owner and/or hospice-RN decision before implementation proceeds. No item below has
been decided or implemented — this is the isolation step requested before pilot build.

## A. Cross-module field ownership (highest priority — affects Falls/Safety protection guarantee)
1. **Falls data inside Musculoskeletal.** `fallHistory.fallsLast90Days` and `fallHistory.fallInjuries`
   currently live in the Musculoskeletal body system, but the owner's own directives require Falls
   Assessment to remain a separately-owned module. Keep both fields in Musculoskeletal as
   supporting evidence, relocate them to the Falls module, or keep them in Musculoskeletal but
   display them only as a read-only link from Falls? **Needs owner decision.**
2. **Assistive devices duplication.** `assistiveDevices` (Musculoskeletal) vs. the Falls module's own
   assistive-device tracking (per owner directive, Falls owns "Assistive Devices"). Single source of
   truth, or intentionally duplicated because Musculoskeletal needs its own copy for general mobility
   context? **Needs owner decision.**
3. **Balance recorded twice.** Neurological's `balance` (Steady/Unsteady/Unable to stand/Normal/Impaired)
   and Musculoskeletal's `balance` (Normal/Impaired) are two different fields with two different value
   sets. Which one is authoritative, or are they intentionally distinct assessments (neuro balance vs.
   functional balance)? **Needs RN clinical input.**
4. **Motor deficit / hemiparesis recorded twice.** Neurological's `deficitType`/`affectedSide` and
   Musculoskeletal's `paralysis` (Right/Left hemiplegia/hemiparesis) capture the same clinical fact.
   **Needs owner/RN decision on single ownership vs. intentional cross-system evidence.**
5. **Skin color/edema recorded in two systems.** Cardiovascular's free-text `skinColor`/`edema.*` vs.
   Skin's structured `skinColorFinding`/`skinEdema.*`. Are these meant to capture different things
   (e.g., CV = perfusion-related color change, Skin = integumentary finding), or is one legacy/redundant?
   **Needs RN clinical input** — this determines whether both stay, or one becomes a read-only summary
   of the other.
6. **Temperature recorded in Vitals and Infection.** `vitals.temperature` vs. Infection's own
   `temperature` field. **Needs owner decision** — likely Infection's copy should become a read-only
   display of the Vitals value rather than a second entry point, but confirm intent first.
7. **Feeding/ostomy devices recorded in up to three places.** GI's `feedingTube.*`/`ostomy.*` and
   `stoolCharacter`'s Colostomy/Ileostomy options, plus Nutrition's `artificialFeeding`. **Needs owner
   decision** on single ownership (likely GI) with Nutrition showing a linked read-only summary.
8. **Catheter/Urostomy recorded in up to three places.** GU's `catheter.*` fields, the `urinaryStatus`
   option list ("Catheterized," "Urostomy"), and GI's `ostomy.type` ("Urostomy"). **Needs owner
   decision** on single ownership.
9. **Insulin/oral hypoglycemics recorded twice within Endocrine.** `diabetes.insulinType`/
   `.oralHypoglycemics` vs. `currentEndocrineMeds`. **Needs owner decision** — likely one should become
   a derived/read-only rollup of the other.
10. **Rigidity and Contractures each have two fields for the same concept** (`rigidity` +
    `rigidityPresent`; `contractures` + `contracturesPresent`) within Musculoskeletal alone. Confirm
    whether `*Present` are legacy fields kept for historical-data back-compat (in which case they
    should become read-only/derived, never both editable) or intentionally distinct.
11. **Swallowing/dysphagia in Nutrition vs. GI.** The owner's own directive already names this exact
    pair as a duplication risk ("do not duplicate GI swallowing findings"). **Needs a single-owner
    decision** (Nutrition's `swallowingIssues` is the only structured field today; GI has none).

## B. Control-semantics exclusivity (needs RN confirmation before any control-type conversion)
12. **Sleep Pattern** (Neurological, radio, 10 options): several options plausibly coexist (Insomnia +
    Overly drowsy; Fragmented + Lack of sleep). Confirm true mutual exclusivity or convert to
    checkboxGroup — **do not convert without this confirmation.**
13. **Level of Consciousness** (Neurological): "Alert" and "Awake" appear as separate mutually-exclusive
    options with overlapping meaning. Confirm intended distinction.
14. **Respiration Pattern** (Respiratory, checkboxGroup): "Regular"/"Normal"/"Irregular" are
    independently selectable today; very likely meant to be mutually exclusive. Confirm before any
    conversion to radio.
15. **Pulse Quality** (Cardiovascular, single radio): conflates rhythm (Regular/Irregular/Tachycardia/
    Bradycardia) with amplitude (Strong/Weak/Thready/Bounding) in one exclusive list — a patient could
    have both a rhythm finding and an amplitude finding simultaneously. Confirm whether this should
    split into two fields.
16. **Abdomen / Bowel Status** (GI, single radios): each conflates two independent clinical axes
    (Abdomen: shape vs. tenderness; Bowel Status: regularity vs. continence). Confirm split vs. keep.
17. **"Exclusive None" pattern** appears in ~10 checkbox groups across systems (e.g., Psychiatric
    History, Nighttime Symptoms, BP Symptoms, Current Active Infection, Additional Skin Findings,
    Oral Cavity Findings, Musculoskeletal Issues, Diabetes Oral Hypoglycemics). None currently enforce
    "selecting None clears other options." Confirm this UX rule is wanted (owner directive proposes
    it) and get RN sign-off on which specific groups need it — applying it everywhere by default risks
    silently altering already-charted historical data semantics.
18. **Hearing/Vision fields mix status and device** ("Hearing aid," "Corrective lenses" as options
    alongside status like "Adequate"/"Impaired"). Confirm whether device presence should split into its
    own checkbox (some of this already exists separately in `sensoryAids`) — i.e., is the device option
    inside the status radio a legacy duplicate of `sensoryAids`?

## C. Structural/behavioral gaps (no field exists yet — explicitly not fabricated)
19. **Respiratory has no "Ventilator/Tracheostomy Present" boolean** to serve as a progressive-
    disclosure trigger — today the detail fields (`ventilatorTypeAndSettings`, `tracheostomyType/Size`)
    always render. Needs an owner decision: repurpose `ventilator.shortTermVentilator`/
    `.longTermVentilator` as the trigger, or add a new explicit "present" field (would be a genuine new
    field, requiring owner sign-off under the freeze).
20. **No "Response to Treatment" field exists** in Respiratory, Endocrine, or several other systems
    despite the owner's proposed architecture calling for one in every system. Adding one is a new
    field per system and requires explicit owner approval — not done here.
21. **No renal-disease-specific fields exist anywhere in Genitourinary** (oliguria, uremic symptoms,
    hyperkalemia, pericarditis, hepatorenal syndrome, fluid overload) despite being named in the
    owner's cited hospice renal-decline guidance. Confirm whether these should be added (new fields,
    needs approval) or are intentionally out of scope for RNICA and captured elsewhere.
22. **Skin/Wounds has no Notes field**, unlike every other of the 10 body systems. Confirm intent
    (wound-level notes inside `woundList` may already satisfy this) before adding one.
23. **Pressure Injury Risk is independently selectable** rather than derived from the Braden subscale
    sum, creating a real data-integrity risk (a nurse could select "Low" while subscale scores sum to a
    high-risk range). Confirm whether this should become a read-only derived value — this is a
    behavior change, not a pure layout change, and needs explicit owner approval separate from the
    Body Systems visual redesign.

## D. Process items not resolvable from code alone
24. **Visit-type and role applicability per field** are not encoded anywhere in the current data model
    (only at the section/route level). Cannot be inventoried "per field" as requested without the
    owner defining this dimension first — it does not exist today even implicitly.
25. **Full per-field report/export/audit dependency** (beyond the fields with an explicit `hopeCode`)
    would require auditing every non-HOPE field against `hopeReportMapper.js` and every other export
    path individually. This is a large, separate verification effort; flagged rather than guessed at
    field-by-field in this pass.
26. **Required/Conditionally-Required/Recommended/Optional classification** for every field (needed
    for Nurse-Miss Prevention) does not exist today — only 3 fields in the entire RNICA form use
    `required: true`, none in Body Systems. This is the single largest remaining blocker to any
    completion-rule implementation and can only be resolved by the owner/RN defining it field-by-field
    — it cannot be inferred from existing code.

---

**Nothing above changes behavior.** These are decision points for the owner + hospice RN validation
sessions (Deliverable 5). Recommended next step per your instruction: present this package (field
inventory, journey maps, unresolved decisions) for owner and hospice RN review, then proceed to the
Respiratory pilot once that review resolves the Respiratory-relevant items above (primarily #12, #14,
#15 is not in Respiratory — actually #14 and #19–20 are the Respiratory-specific blockers).
