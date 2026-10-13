# SNS Workflow Rulebook and Infection Workflow Specification

**Status:** Proposed authoritative SNS workflow standard for RNICA implementation  
**Scope:** Global workflow rules plus the Infection body-system workflow  
**Primary objective:** Make documentation faster, clearer, and easier for hospice staff without removing clinically relevant information or duplicating work.

---

## 1. SNS workflow rulebook

### 1.1 The nurse's first question controls the workflow

Every SNS workflow must begin with the clinical question the nurse is trying to answer.

Examples:

- Cardiovascular: Is there a current cardiovascular concern?
- Respiratory: Is there a current respiratory concern?
- Infection: Is there a current infection concern?

The first interactive element must answer that question. Shared profile information, implementation notes, reference data, and secondary tools must not interrupt the first clinical decision.

### 1.2 One workflow, one owner, one source of truth

Each data element must have one authoritative owner.

- Patient-profile information is documented once and reused everywhere.
- Body-system findings are documented once within the applicable assessment.
- Workflow states may change visibility and mode, but must not create duplicate renderers, duplicate data paths, or duplicate records.

### 1.3 Never duplicate content across workflow states

The following workflow states must not each contain a separate copy of the same component:

- No Current Concern
- Existing Findings Review
- New or Worsening Findings
- Unable to Assess

A single canonical component may be displayed, summarized, edited, or hidden according to the selected state. It must not be rebuilt four times.

### 1.4 Shared information renders once

Before placing any component, classify it:

**Patient-profile information**

Examples:

- allergies;
- code status;
- demographics;
- chart-wide devices or alerts;
- other shared master-record data.

Rule: render once in the appropriate chart context and reuse the same canonical record.

**Assessment information**

Examples:

- active infection;
- infection symptoms;
- resistant organism status;
- current antibiotic therapy;
- respiratory findings;
- cardiovascular findings.

Rule: workflow state may control display or edit mode.

### 1.5 Do not replace scrolling with clicking

A workflow is not improved merely because it is shorter vertically.

Fail if the nurse must:

- switch states repeatedly to enter related data;
- open multiple screens for one clinical task;
- re-enter information already known;
- toggle categories just to add consecutive records;
- hunt for a field that could remain directly available.

### 1.6 Review and edit are different modes

**Existing Findings Review** shows a concise, readable summary of saved findings first.

- It may provide an `Edit Existing Findings` action.
- Editing must open the same canonical editor used elsewhere.
- There must not be a separate review editor and a new-findings editor.

**New or Worsening Findings** opens the canonical editor directly.

### 1.7 No Current Concern must be compact

When `No Current Concern` is selected:

- keep the overview selector visible and reversible;
- show a concise summary;
- show only approved status, notes, or follow-up controls;
- hide irrelevant detailed assessment controls;
- preserve previously saved findings;
- do not imply that hidden findings were deleted.

### 1.8 Unable to Assess must be compact and reversible

When `Unable to Assess` is selected:

- keep all overview choices visible;
- show reason unable to assess;
- show only approved status and notes fields;
- hide detailed assessment controls;
- preserve prior findings;
- allow immediate switching to another state.

### 1.9 Existing findings are preserved

Changing workflow state changes visibility, not ownership.

- Hide does not mean delete.
- Existing values must persist across state changes.
- Direct switching must not erase findings.
- Autosave must not restore stale state after a switch.

### 1.10 Every click must earn its place

A click is justified only when it:

- prevents an error;
- reveals conditionally relevant information;
- confirms a consequential action;
- protects existing documentation;
- reduces greater downstream work.

Do not add clicks solely to make the screen look cleaner.

### 1.11 Dates default from the current workflow

If a date represents an event being documented in the current workflow, default it from the known context:

- Admission RNICA: SOC date;
- other RNICA assessment: assessment date;
- visit documentation: visit date;
- HOPE event: applicable HOPE event date.

A date may remain editable when the actual event occurred on a different date.

### 1.12 GitHub may not make hospice clinical-significance decisions

GitHub may identify:

- documentation burden;
- duplicate entry;
- missing controls;
- data-binding defects;
- auto-population opportunities;
- harvesting opportunities;
- layout defects;
- validation or persistence defects.

GitHub may not independently:

- remove a clinical field;
- rank clinical importance;
- label a field low value;
- demote or hide a field for clinical reasons;
- redesign hospice practice;
- expand the ontology during RNICA completion.

Clinical-content decisions require owner approval.

### 1.13 Finish before moving forward

A body system is not complete merely because tests pass.

It is complete only when:

- each workflow state has a clear purpose;
- known duplication is removed;
- known workflow contradictions are resolved;
- saved values persist correctly;
- summary and visible findings agree;
- the owner approves the live workflow.

Known defects are not deferred to the next body system.

---

## 2. Infection workflow specification

### 2.1 Nurse's first question

The Infection workflow begins with:

> Is there a current infection concern?

The `Infection Overview` is the first workflow control.

Options:

1. No Current Infection Concern
2. Existing Infection Findings Review
3. New or Worsening Infection Findings
4. Unable to Assess

All four options remain visible and directly switchable.

### 2.2 Information hierarchy

Display order:

1. Infection Summary
2. Infection Overview
3. Workflow-specific infection content
4. Clinical Status Change
5. Notes
6. Patient Reference Information, when the Infection card is the approved place to expose it

Patient Reference Information must not interrupt the first infection decision.

### 2.3 Shared allergy profile

Allergies are chart-wide patient-profile information.

Requirements:

- Facesheet remains a primary always-visible allergy surface.
- Infection must use the same `patient_allergies` source of truth.
- Infection must not create a second allergy table, duplicate record, or duplicate API.
- Allergy information must not be rendered separately inside all four Infection states.
- If the allergy editor remains available inside Infection, render it once outside the state-gated content.
- The allergy editor must not move when the Infection state changes.

Each allergy record contains:

- Type: Medication, Food, Environmental, Other/Sensitivity
- Allergen
- Reaction
- Severity

A patient may have unlimited allergies across all categories at the same time.

The type is a property of each allergy record, not a workflow state. Quick-fill buttons may preselect the type for the next entry, but must not create separate pages or require navigation between categories.

### 2.4 Immune status

Immune Status is patient-reference information used by the infection assessment.

- Render once.
- Do not duplicate it under each Infection state.
- Do not permit Infection-state switching to clear it.

### 2.5 No Current Infection Concern

Display:

- summary: `No current infection concern identified.`
- Infection Overview;
- Clinical Status Change, when required by the approved workflow;
- Notes;
- shared allergy/immune reference only once, in its approved fixed position.

Hide:

- Active Infection editor;
- Resistant Organisms editor;
- Infection History editor;
- Antibiotic Therapy editor;
- Precautions editor;
- Temperature assessment fields, unless separately required by approved policy.

Previously saved infection findings remain preserved.

### 2.6 Existing Infection Findings Review

Purpose: review the patient's previously documented infection picture without opening the full editor immediately.

Display a concise review summary containing only saved facts, for example:

- Active infection
- Current resistant organism
- History of resistant organism
- Recurrent infection history
- Antibiotic therapy status
- Precautions
- Temperature, if documented
- Clinical status

Provide one `Edit Existing Findings` action.

Selecting it opens the canonical Infection editor. Do not create a second editor.

If no prior findings exist, display:

`No previously documented infection findings are available for review.`

Do not render empty cards or blank peer columns.

### 2.7 New or Worsening Infection Findings

Open the canonical Infection editor directly.

Editor order:

1. Active Infection
2. Resistant Organisms
3. Infection History
4. Antibiotic Therapy
5. Precautions
6. Temperature
7. Clinical Status Change
8. Notes

Preserve existing fields and options unless the owner separately approves content changes.

### 2.8 Unable to Assess

Display:

- Infection Overview;
- Reason Unable to Assess;
- Clinical Status Change, when required;
- Notes;
- shared allergy/immune reference only once, in its approved fixed position.

Hide detailed infection controls.

Do not delete prior infection findings.

### 2.9 Canonical Infection editor

There must be exactly one editor component and one canonical set of data bindings for:

- Active Infection
- Current resistant organism
- History of resistant organism
- Infection History
- Antibiotic Therapy
- Precautions
- Temperature
- Clinical Status Change
- Notes

`Edit Existing Findings` and `New or Worsening` use the same editor.

### 2.10 Summary behavior

The summary must reflect saved facts and must not contradict visible selections.

Examples:

- `No current infection concern identified.`
- `Active respiratory infection documented; currently receiving antibiotics.`
- `History of MRSA; no current active infection documented.`
- `Infection assessment unable to be completed.`
- `Infection assessment not yet documented.`

Do not invent missing values.

---

## 3. Acceptance criteria proving the workflow is easier

### 3.1 Architecture and duplication

- [ ] One Infection Overview selector exists.
- [ ] One canonical Infection editor exists.
- [ ] One allergy editor/list component exists in the Infection card, if retained there.
- [ ] Allergies are not duplicated across the four Infection states.
- [ ] Immune Status is not duplicated across the four Infection states.
- [ ] No duplicate infection data paths exist.
- [ ] No empty workflow-state renderer remains mounted and reserving space.

### 3.2 First-question test

- [ ] On opening Infection, the first interactive clinical control is `Infection Overview`.
- [ ] A nurse can document `No Current Infection Concern` without interacting with allergy controls.
- [ ] A nurse can begin documenting a new infection without navigating through patient-profile data.

### 3.3 Click-efficiency test

Using the same baseline patient, count required pointer/keyboard actions.

Scenario A: No Current Infection Concern

- [ ] Select the state and complete required status/notes without opening detailed infection controls.
- [ ] No allergy-category switching is required.
- [ ] No duplicate section must be reviewed.

Scenario B: New UTI, receiving antibiotics

- [ ] Select `New or Worsening`.
- [ ] Select UTI.
- [ ] Select antibiotic status.
- [ ] Select precautions only if applicable.
- [ ] Complete status/notes.
- [ ] No separate duplicate editor is opened.

Scenario C: Add three allergies

Add:

- Medication: Penicillin
- Food: Milk
- Environmental: Latex

Pass only when:

- [ ] all three can be entered consecutively in one fixed allergy editor;
- [ ] the nurse does not switch Infection workflow states;
- [ ] the nurse does not navigate to separate category pages;
- [ ] each saved record retains its own type;
- [ ] all three appear on the Facesheet from the same source of truth.

### 3.4 Scrolling and switching test

- [ ] The redesigned workflow requires fewer state changes than the current baseline.
- [ ] Reduced scrolling is not achieved by adding extra clicks or hidden pages.
- [ ] No task requires switching states merely to view or enter shared information.
- [ ] Shared allergy and immune data stay in a fixed position.

### 3.5 Review-versus-edit test

- [ ] Existing Findings opens as a readable summary, not the full editor.
- [ ] `Edit Existing Findings` opens the canonical editor.
- [ ] New or Worsening opens the same canonical editor directly.
- [ ] A nurse can distinguish Review from Edit without relying only on the selected tab label.

### 3.6 Reversibility and data preservation

- [ ] All four Infection states remain visible.
- [ ] Direct switching works.
- [ ] State switching does not delete infection findings.
- [ ] State switching does not delete allergies or immune status.
- [ ] Rapid switching before autosave completes preserves the final selected state.
- [ ] Save, reload, and reopen restore the same data.

### 3.7 Summary accuracy

- [ ] Summary matches the selected state.
- [ ] Summary includes meaningful saved infection findings.
- [ ] Summary never says `No Significant Findings` when active infection data exists.
- [ ] Missing data is not inferred.

### 3.8 Visual and accessibility checks

- [ ] No legacy checkbox styling remains where SNS ToggleGroup styling is approved.
- [ ] No duplicated headings appear.
- [ ] No empty peer columns appear.
- [ ] No horizontal scrolling occurs.
- [ ] Keyboard and touch interaction work.
- [ ] Focus remains predictable when state-dependent content changes.

### 3.9 Measurable pass indicators

Record and compare before versus after:

- number of Infection workflow-state switches;
- number of clicks/taps for each test scenario;
- total expanded Infection height per state;
- number of duplicate component instances;
- number of duplicate data bindings;
- number of times the same clinical fact must be entered;
- task-completion success without assistance;
- nurse-reported confusion points during field testing.

The workflow passes only when it demonstrates no increase in any burden measure and a reduction in at least one of: duplicate entry, state switching, clicks, or scrolling.

### 3.10 Functional integrity

- [ ] Autosave works.
- [ ] Reload restores values.
- [ ] Patient isolation passes.
- [ ] Admission isolation passes.
- [ ] Assessment isolation passes.
- [ ] Allergy data remain synchronized with Facesheet.
- [ ] No other body system changes.
- [ ] Temporary test data are restored to baseline.
- [ ] No console errors or failed network calls are introduced.

---

## 4. GitHub implementation handoff

GitHub must:

1. Read this specification before editing.
2. Inventory current components and data paths.
3. Identify duplicated renderers and duplicate bindings.
4. Preserve all approved clinical fields.
5. Create or retain one canonical Infection editor.
6. Render allergy/immune reference once in a fixed position.
7. Implement the four Infection states exactly as specified.
8. Run the acceptance checklist with real screenshots and measurements.
9. Return `PASS` or `NOT ACCEPTED`.
10. Stop for owner review.

GitHub must not:

- move to GI, Nutrition, or Endocrine;
- expand ontology;
- start AI work;
- remove clinical fields;
- declare completion from unit tests alone;
- defer known duplication or workflow defects.

---

## 5. Regulatory and policy boundary

This rulebook is an SNS internal workflow standard. It is not a CMS-prescribed interface.

The regulatory and payer guidance requires sufficient clinical information and documentation to support the patient's status and hospice record. The exact layout, workflow-state pattern, click limits, and render-once rules are SNS design policy intended to reduce duplicate entry and staff burden while preserving the clinical record.
