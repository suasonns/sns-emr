# SNS Layout Standard v1.1

**Status:** Authoritative spacing, density, grid, measurement, implementation, and acceptance standard  
**Scope:** SNS clinical documentation layouts, beginning with RNICA  
**Reference screens:** RNICA Pain & Symptom Burden and Neurological Assessment  
**Supersedes:** SNS Layout Standard v1 where this document clarifies or resolves a conflict  
**Governing references:** `SNS_DESIGN_SYSTEM_EXPORT.md` and `SNS Design System 1.0.md`

---

## 1. Purpose and boundaries

This standard optimizes hospice charting speed by reducing scrolling, pointer travel, unused width, and unnecessary vertical stacking.

This standard controls only:

- page and content measurements;
- card and section density;
- grid selection;
- row composition;
- spacing between controls;
- body-system placement;
- space-utilization acceptance rules;
- implementation verification and acceptance evidence.

This standard does **not** change workflows, field meaning, field count, clinical content, validation, compliance behavior, persistence, audit behavior, or documentation sequence. No field may be removed, renamed, recoded, hidden without existing workflow authority, or moved to another body system solely to satisfy a density target.

If density improvement conflicts with field preservation, workflow preservation, readability, accessibility, patient safety, or compliance visibility, preservation wins and the exception must be documented.

---

## 2. Rule precedence

When two layout rules appear to conflict, apply them in this order:

1. Patient safety and reversibility.
2. Preserve fields, values, workflow, validation, persistence, and audit behavior.
3. Accessibility and readable control presentation.
4. Responsive fit without horizontal clinical-form scrolling.
5. Conditional content must consume zero space when not rendered.
6. Grid-selection rules.
7. Utilization targets.
8. Exact spacing and sizing tokens.
9. Cosmetic symmetry.

A lower-priority rule must never override a higher-priority rule.

---

## 3. Measurement vocabulary

- **Viewport:** Available application area at the named screen size, excluding browser chrome.
- **Page:** The complete RNICA workspace. It uses all available viewport width and has no centered maximum-width container.
- **Primary content:** The active documentation column.
- **Utility rail:** The findings, intelligence, or status rail. It is not charting space.
- **Section:** A named clinical group such as Core Findings or Management.
- **Card:** A bordered content surface inside a section.
- **Row:** One horizontal arrangement of related fields or cards.
- **Compact control:** Checkbox, radio, chip, short segmented option, date, short number, or short select.
- **Long-form control:** Narrative, notes, multiline evidence, long instructions, or wide summary content.
- **Populated row:** A row containing at least one visible clinical control, value, label, helper, or required reading region.
- **Approved full-width exception:** Summary, Notes, Narrative, Evidence, Comparison, Table, or POC.

All measurements are in pixels.

---

## 4. Canonical spacing scale

Only these spacing values are used in routine clinical layouts:

| Token | Value | Required use |
|---|---:|---|
| Tight | 4 | Between chips, tightly related inline controls, icon and label |
| Row | 8 | Between field rows and wrapped chip lines |
| Card inset | 10 | Default internal card padding |
| Grid gutter | 12 | Between cards or grid columns |
| Section | 16 | Between major named sections |
| Major break | 24 | Between unrelated workflow regions only |

Rules:

- Values above 24 are prohibited for routine clinical spacing.
- Blank spacer rows and empty spacer elements are prohibited.
- No negative margins may be used to force conformance.
- A component-specific exception must be documented with the reason, affected component, viewport, and owner approval.

---

## 5. Page and content width

| Element | Standard |
|---|---|
| Page width | 100% of available viewport width; no maximum-width ceiling |
| Desktop page inset | 0 at shell level; 12 inside active content |
| Tablet page inset | 12 on each side |
| Primary content width | All width remaining after required navigation and utility rails |
| Primary content minimum on desktop | 448 |
| Utility rail width on desktop | 272 minimum; 336 maximum |
| RNICA navigation rail on desktop | 270 fixed |
| Horizontal overflow | Prohibited in clinical forms |

Clarifications:

- The primary content column must never be centered inside a narrower decorative wrapper.
- Utility rails are excluded from body-system density calculations.
- Body-system layouts must not assume the utility rail provides usable charting space.
- If the primary content falls below 448, responsive behavior must collapse or reposition rails before clinical controls are compressed below their usable minimums.

---

## 6. Card measurements

| Property | Exact rule |
|---|---:|
| Standard card padding | 10 on all sides |
| Dense secondary-card padding | 8 vertical, 10 horizontal |
| Banner or patient-summary padding | 12 vertical, 16 horizontal |
| Card-to-card gap | 12 |
| Section-to-section gap | 16 |
| Card border radius | 8 |
| Minimum standard card width | 260 |
| Minimum compact field-group width | 180 |
| Maximum routine card width | 420 |
| Full-width exception | Summary, Notes, Narrative, Evidence, Comparison, Table, POC |
| Minimum card height | Content-driven only |

Conflict resolution:

- **Card width and control width are separate concepts.** A card may occupy its allocated grid span while compact controls inside the card hug content.
- A card may be wider than 420 only when it is an approved full-width exception or when a documented responsive constraint requires it.
- A routine card narrower than 260 is prohibited.
- A compact field group narrower than 180 is prohibited.
- Do not enforce a blank minimum height. The former 84-pixel card minimum is retired.
- Do not stretch peer cards to equal heights if stretching creates blank space. Use `align-items: start` or equivalent behavior.

---

## 7. Row and control measurements

| Element | Exact rule |
|---|---:|
| Standard input/select/button height | 34 |
| Compact chip minimum height | 28 |
| Standard field-row gap | 8 |
| Standard field-column gap | 12 |
| Chip horizontal gap | 4 |
| Chip wrap-line gap | 4 |
| Label-to-control gap | 4 |
| Group heading-to-first-row gap | 8 |
| Standard structured-row target height | 64 maximum when content fits |
| Dense binary/short-choice row target height | 44 maximum when content fits |
| Initial empty note-field height | 46 |
| Expanded note-field height | Content-driven |
| Standard summary-card height | 64 when content fits |
| Summary with active alert/follow-up | 88 maximum before detail moves to a separate row |

Clarifications:

- Row-height values are **targets, not clipping limits**. Content must never be clipped to meet a target.
- Controls belonging to one clinical question share one row whenever their combined minimum widths and gaps fit.
- Empty notes stay at 46. Notes auto-grow only after entered or restored content requires more height.
- No reserved note-growth area may be shown.
- Labels remain adjacent to their controls and do not sit at the opposite side of a wide card.

---

## 8. Base grid

The primary content area uses a 12-column grid with 12-pixel gutters.

| Layout | Span | Width criterion | Content criterion |
|---|---:|---:|---|
| 3-column | 4 + 4 + 4 | Primary content at least 804 | Three populated peer groups; each remains at least 260 wide |
| 2-column | 6 + 6 | Primary content at least 532 | Two populated peer groups, or short fields divided into two coherent groups |
| 1-column | 12 | Any width | Approved full-width exception or multi-column layout would wrap/clutter excessively |

Thresholds:

- 804 = three 260 cards + two 12 gutters.
- 532 = two 260 cards + one 12 gutter.

### 8.1 3-column eligibility

Use 3-column only when all are true:

- exactly three visible peer groups exist, or six or more short fields divide naturally into three visible groups;
- each column has at least two visible compact controls or one clinically meaningful control group;
- expected peer-height difference is 64 or less;
- no column is expected to remain more than 40% empty;
- each card remains at least 260 wide.

If any test fails, use 2-column or 1-column.

### 8.2 2-column eligibility

Use 2-column when any is true:

- two visible peer groups exist;
- three columns would create an empty or substantially shorter third column;
- a one-column layout would create avoidable vertical stacking;
- the primary content width is 532–803;
- Management and Clinical Status Change are both visible and clinically parallel.

**Empty-peer rule:** If one peer group contains no visible content, it consumes zero space. The remaining populated group expands to 12 columns unless its content is visually clearer at a smaller content-driven width. Empty peer columns are prohibited.

### 8.3 1-column eligibility

Use 1-column when any is true:

- content is Summary, Notes, Narrative, Evidence, Comparison, Table, or POC;
- uninterrupted reading is required;
- a multi-column layout would create a peer-height difference greater than 64;
- available width is below 532;
- the control set would wrap into more than two lines at proposed column width.

### 8.4 Grid implementation behavior

- Use explicit wrappers for peer groups. Do not rely on a shared CSS auto-placement cursor across independent conceptual columns.
- Hidden or untriggered content must be removed from layout flow and consume zero height and zero columns.
- Direct grid children use `min-width: 0` or equivalent behavior.
- Long labels wrap within their own span and must not resize peer columns.
- Do not use fixed card heights, empty placeholders, or spacer elements to manufacture symmetry.

---

## 9. Field placement inside cards

| Field type | Placement |
|---|---|
| Yes/No, Present/Absent, severity chips | Inline, content-width, 4 gap |
| Date + related status | Same row, two field groups, 12 gap |
| Two related short selects | Same row, equal halves |
| Three related short findings | Same row when each receives at least 180 |
| Checkbox list up to six short labels | Inline wrap in one card |
| Checkbox list over six labels | Two balanced rows before a second card |
| Narrative or note | Full width |
| Generated summary | Full width |
| POC review/action | Full-width footer row |

Rules:

- Do not create a nested card for a single label and one short control.
- Compact controls hug content unless equal width improves comparison inside one option set.
- A short field must not occupy a full-width row when another related short field can fit beside it.
- A card containing fewer than three short controls must not occupy more than six columns unless a documented exception applies.

---

## 10. Reusable body-system template

Required vertical order:

1. Summary
2. Overview
3. Core Findings
4. Symptoms
5. Management
6. Notes
7. POC

Sections with no applicable visible fields consume zero height. Existing conditional behavior remains authoritative.

| Region | Grid placement | Height / spacing rule |
|---|---|---|
| System header | 12 columns | 44 collapsed; 64 expanded maximum when content fits |
| Header to Summary | — | 12 gap |
| Summary | 12 columns | 64 standard; 88 maximum with follow-up when content fits |
| Summary to Overview | — | 12 gap |
| Overview | 12 columns | One 34 control row plus labels; 64 maximum when content fits |
| Major section gap | — | 16 before Core Findings, Symptoms, Management, Notes, POC |
| Section heading band | 12 columns | 28 high when content fits |
| Heading to cards | — | 8 gap |
| Core Findings | 3-column at ≥804; 2-column at 532–803; 1-column below 532 | 12 gutters |
| Symptoms | 2-column at ≥532; otherwise 1-column | 12 gutters |
| Management | 2-column at ≥532 when both groups are populated; otherwise compact or 1-column | 12 gutters |
| Notes | 12 columns | 46 initial empty height |
| POC | 12 columns | 40 minimum action/footer row; 8 above and below content |

### 10.1 Neurological mapping

- Summary: full width.
- Overview: full-width compact option row.
- Core Findings: Consciousness / Orientation / Neurological Overview in three columns when eligible.
- SNS Cognitive Screen and Sleep / Responsiveness: two columns only when both satisfy peer-height and wrap rules; otherwise 1-column.
- Symptoms: Communication and Sensory / Cognitive-Behavioral Findings in two columns.
- Management: Psychiatric History and another populated peer in two columns; otherwise no empty peer reservation.
- Notes: full width, 46 empty height.
- POC: full-width footer.

### 10.2 Cardiovascular mapping

- Summary: full width.
- Overview: full-width compact option row that remains reversible.
- Core Findings: Pulse rhythm/rate/strength; pulse sites/heart sounds; edema/JVD/skin/peripheral circulation divided into balanced visible peers according to the eligibility rules.
- Symptoms: Chest pain, BP status, orthostatic finding, fatigue, dizziness, and syncope in two coherent populated columns.
- Management: Cardiac Devices / Clinical Status Change in two columns only when both contain visible content. Otherwise the populated group expands under the Empty-peer rule.
- Notes: full width, 46 empty height.
- POC: full-width footer.

The Cardiovascular Core Findings region must not cluster controls into the first portion of a wide row while leaving related fields stacked below.

---

## 11. Responsive measurement sheets

These sheets assume the listed rails are visible at the stated width. If actual shell measurements differ, calculate the grid from the measured primary-content width and apply the thresholds in Section 8. The measured container, not the nominal viewport, controls column count.

### 11.1 Desktop 1440 × 900

| Measurement | Standard |
|---|---:|
| Page width | 1440 |
| RNICA navigation rail | 270 |
| Utility rail | 336 |
| Nominal primary content width | 834 |
| Primary content internal inset | 12 each side |
| Nominal usable grid width | 810 |
| Grid columns | 12 |
| Grid gutter | 12 |
| Routine arrangement | 3 columns if all eligibility tests pass |
| Nominal 3-column card width | 262 |
| Maximum routine card width | 420 |
| Maximum full-width exception | 810 |

### 11.2 Desktop 1366 × 768

| Measurement | Standard |
|---|---:|
| Page width | 1366 |
| RNICA navigation rail | 270 |
| Utility rail | 336 |
| Nominal primary content width | 760 |
| Primary content internal inset | 12 each side |
| Nominal usable grid width | 736 |
| Grid columns | 12 |
| Grid gutter | 12 |
| Routine arrangement | 2 columns when both groups are populated |
| Nominal 2-column card width | 362 |
| Maximum routine card width | 420 |
| Maximum full-width exception | 736 |

### 11.3 Tablet 1024 × 768

At this width the utility rail moves below primary content rather than competing beside it.

| Measurement | Standard |
|---|---:|
| Page width | 1024 |
| Page inset | 12 each side |
| Usable content width | 1000 |
| Utility rail placement | Below primary content |
| Grid columns | 12 |
| Grid gutter | 12 |
| Routine arrangement | 3 columns only if all eligibility tests pass; otherwise 2 |
| Nominal 3-column widths | 325 / 326 / 325 |
| Maximum routine card width | 420 |
| Maximum full-width exception | 1000 |

### 11.4 Shared viewport measurements

| Element | 1440 / 1366 | Tablet |
|---|---:|---:|
| Standard structured-row target | 64 | 72 |
| Dense-row target | 44 | 48 |
| Card padding | 10 | 10 |
| Card gap | 12 | 12 |
| Section gap | 16 | 16 |
| Field row / column gap | 8 / 12 | 8 / 12 |
| Chip gap | 4 | 4 |
| Empty note height | 46 | 46 |
| Summary target | 64 / 88 alert | 64 / 88 alert |

---

## 12. Space-utilization rules

### 12.1 Utilization calculation

For each populated structured row:

1. Measure usable row width.
2. Subtract required label widths, visible controls, approved helper text, and standard gaps.
3. Divide remaining unused width by usable row width.
4. If unused width exceeds 40% and a related visible control is stacked below, the row fails.

Approved full-width exceptions are not subject to the 60% utilization threshold, but must still use only the height required by their content.

Approved exceptions:

- Summary
- Notes
- Narrative
- Evidence
- Comparison
- Tables
- POC

Utility rails are excluded from body-system utilization calculations.

### 12.2 Fail conditions

A layout fails if any condition exists:

1. More than 40% of a structured row is unused while a related visible control is stacked below.
2. Two or more related short controls are vertically stacked when they fit at minimum widths.
3. A grid reserves an empty column.
4. A short-control card exceeds 420 without using room for related controls and is not an approved exception.
5. Routine card padding exceeds 10.
6. Section spacing exceeds 16 except an approved 24 major break.
7. An empty note starts taller than 46.
8. A summary exceeds 88 before detail moves to a separate row, unless content would otherwise clip.
9. A body-system heading plus scope exceeds 64 when its content fits within 64.
10. A card enforces blank minimum height.
11. A label is separated from its control by avoidable empty horizontal space.
12. A 2-column row has an empty peer or a peer-height difference over 64.
13. A 3-column row has fewer than three populated peer groups.
14. A compact choice group wraps into more than two lines while wider placement is available.
15. Hidden conditional content retains space.
16. Active documentation is constrained by a centered maximum-width wrapper.
17. Peer cards are stretched to equal height solely for symmetry.
18. Horizontal clinical-form scrolling occurs.

### 12.3 Pass conditions

A layout passes only when all are true:

1. At least 60% of each populated structured row is active clinical content or required reading space.
2. Related controls share rows whenever minimum widths fit.
3. Every visible grid column contains real clinical content.
4. Card width matches content type.
5. Labels and values scan left-to-right, top-to-bottom.
6. Empty notes remain compact and grow only with content.
7. Hidden conditional content consumes zero space.
8. No clinical-form horizontal scrolling is required.
9. The system header, Summary, Overview, and first Core Findings row appear in the initial desktop viewport unless active alert content requires more space.
10. Workflow, clinical content, validation, persistence, audit behavior, and compliance content remain intact.
11. Overview choices that control conditional paths remain visible and reversible unless an approved workflow explicitly says otherwise.

---

## 13. Exception policy

An exception is valid only when all are documented:

- violated rule;
- affected screen and viewport;
- safety, accessibility, workflow, or compliance reason;
- alternative attempted;
- measured impact;
- owner approval.

Exceptions may not be created solely because current CSS or component structure is inconvenient.

---

## 14. Revision escalation rule

If a section fails three consecutive visual-density reviews for spacing, scrolling, unused width, or uneven layout:

1. Stop CSS micro-adjustments.
2. Run the formal density audit in Section 12.
3. Compare the live screen to this standard at required viewports.
4. Identify the exact failed rows and rules.
5. Change only the failed row grouping or span.
6. Return for owner review before any additional iteration.

No body-system section may receive a fourth spacing revision without a documented Layout Standard Review.

---

# GitHub Implementation and Acceptance Checklist

## A. Scope lock

- [ ] Confirm the exact section/body system in scope.
- [ ] List exact files to be changed before editing.
- [ ] Confirm no field, option, label, workflow, validation, persistence, audit, or compliance behavior will change.
- [ ] Confirm no other body system will be modified.
- [ ] Capture `git status --short`, `git diff --stat`, and `git diff --name-only` before editing.
- [ ] Separate unrelated pre-existing work from the implementation diff.

## B. Measure before implementing

- [ ] Record actual primary-content width from the live container.
- [ ] Record visible navigation and utility-rail widths.
- [ ] Record current section height in relevant workflow states.
- [ ] Capture before screenshots at 1440×900, 1366×768, and 1024×768 or the closest supported test viewport.
- [ ] Identify each visible row and classify as structured row or approved full-width exception.
- [ ] Calculate unused-width percentage for each populated structured row.
- [ ] Mark exact rows that fail the 40% rule.

## C. Grid selection

- [ ] Use 3 columns only if all Section 8.1 tests pass.
- [ ] Use 2 columns only when both peers are populated or the Empty-peer rule is applied.
- [ ] Use 1 column for approved full-width exceptions or when wrap/height rules require it.
- [ ] Use explicit peer-group wrappers.
- [ ] Ensure hidden content consumes zero height and zero columns.
- [ ] Ensure direct grid children can shrink safely (`min-width: 0` or equivalent).
- [ ] Prevent long labels from resizing peer columns.
- [ ] Do not use empty columns, blank placeholders, spacer elements, or fixed heights.

## D. Spacing and controls

- [ ] Use only 4, 8, 10, 12, 16, and approved 24 spacing values.
- [ ] Standard card padding is 10.
- [ ] Dense secondary card padding is 8 vertical / 10 horizontal.
- [ ] Grid gaps are 12.
- [ ] Section gaps are 16.
- [ ] Compact chip height is at least 28.
- [ ] Standard control height is 34.
- [ ] Labels sit within 4 of their controls.
- [ ] Related compact controls share a row when minimum widths fit.
- [ ] Option chips wrap naturally with 4 gaps.
- [ ] Peer cards use content height and do not stretch for symmetry.

## E. Summary, notes, and POC

- [ ] Summary target is 64 and alert target is 88 when content fits.
- [ ] Summary content is not clipped to meet a target.
- [ ] Empty notes begin at 46.
- [ ] Notes auto-grow only when content requires it.
- [ ] No sample text, test text, or internal implementation notes appear.
- [ ] Notes remain full width.
- [ ] POC remains a full-width footer/action row.
- [ ] No large empty block exists between Notes and POC.

## F. Conditional paths and reversibility

- [ ] Empty conditional regions consume zero space.
- [ ] Overview/path controls remain visible if needed to reverse a selection.
- [ ] Direct path switching remains available when the current workflow supports it.
- [ ] Hidden findings are not silently deleted.
- [ ] Accidental path selections can be corrected without leaving the section.
- [ ] Summary text matches the active path.
- [ ] Autosave does not restore a stale prior path after rapid switching.

## G. Responsive verification

### 1440×900

- [ ] Actual primary width measured.
- [ ] 3 columns used only if all eligibility tests pass.
- [ ] No horizontal clinical-form scrolling.
- [ ] Header, Summary, Overview, and first Core Findings row visible initially unless active alerts require more.

### 1366×768

- [ ] Actual primary width measured.
- [ ] Routine layout uses 2 columns unless measured width and eligibility rules support 3.
- [ ] No empty peer columns.
- [ ] No horizontal clinical-form scrolling.

### 1024×768

- [ ] Utility rail moves below primary content when specified by shell behavior.
- [ ] 3 columns used only if every card remains at least 260 and all eligibility tests pass.
- [ ] Otherwise use 2 columns.
- [ ] No horizontal clinical-form scrolling.

### Narrow/mobile

- [ ] Layout collapses to 1 column before controls become unusably narrow.
- [ ] No clipped labels or controls.
- [ ] No horizontal clinical-form scrolling.

## H. Density audit

For every populated structured row:

- [ ] Usable width measured.
- [ ] Used width measured.
- [ ] Unused percentage calculated.
- [ ] Unused width is 40% or less, or no related visible control is stacked below.
- [ ] Every visible column contains clinical content.
- [ ] Peer-height difference is 64 or less.
- [ ] Compact choices use no more than two wrapped lines when wider placement is available.
- [ ] Approved exceptions are labeled and excluded from the 60% threshold.

## I. Functional regression check

- [ ] All controls remain selectable.
- [ ] Keyboard navigation remains usable.
- [ ] Touch targets remain usable.
- [ ] Conditional fields appear and disappear correctly.
- [ ] Autosave works.
- [ ] Reload restores values.
- [ ] Patient isolation passes.
- [ ] Admission isolation passes.
- [ ] Assessment isolation passes.
- [ ] Audit behavior remains intact.
- [ ] No temporary test data remains.
- [ ] No console errors.
- [ ] No failed network requests caused by the change.

## J. Evidence required for owner acceptance

- [ ] Exact files changed.
- [ ] Before/after diff stat limited to the approved scope.
- [ ] Before/after screenshots at required viewports.
- [ ] Before/after section heights for each relevant conditional path.
- [ ] Density-audit table listing every row and PASS/FAIL result.
- [ ] List of any approved exceptions.
- [ ] Confirmation that no clinical content or workflow changed.
- [ ] Confirmation that no other body system changed.
- [ ] Confirmation that temporary test data was removed.
- [ ] Live demonstration, not source inspection only.

## K. Final acceptance gate

The section is accepted only when all are true:

- [ ] All checklist items applicable to the section are complete.
- [ ] Every structured row passes the utilization rules.
- [ ] Every grid meets population and width criteria.
- [ ] No empty peer column remains.
- [ ] No hidden content reserves space.
- [ ] No horizontal clinical-form scrolling occurs.
- [ ] No field, value, workflow, validation, persistence, audit, or compliance behavior regressed.
- [ ] Owner reviews the live screen and approves it.

If any required item is unchecked, status is **NOT ACCEPTED**.

---

## 15. Conflict-resolution summary

This v1.1 resolves the following v1 ambiguities:

- Card span versus compact control width.
- 60% utilization versus approved full-width exceptions.
- Empty peer behavior in 2-column rows.
- Summary and row heights as targets rather than clipping limits.
- Empty-note height versus auto-growth.
- Utility-rail exclusion from body-system density calculations.
- Nominal viewport sheets versus actual measured content width.
- Equal-height appearance versus content-driven card height.
- Three-column use versus populated-peer and height-balance requirements.
- Reversible conditional paths versus visual simplification.
- Repeated CSS iteration versus mandatory Layout Standard Review.
