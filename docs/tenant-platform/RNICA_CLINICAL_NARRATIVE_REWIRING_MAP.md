# RNICA Clinical Narrative — Rewiring Map

**STATUS: DISCOVERY AND CORRECTION PLANNING ONLY**
**NO CODE. NO SCHEMA. NO MIGRATIONS. NO FIGMA HANDOFF YET.**

This document replaces any prior implication that both narrative fields are
symmetrical, permanent, co-equal UI inputs. Per the locked product decision
(`RNICA_CLINICAL_NARRATIVE_ARCHITECTURAL_CORRECTION.md`), the placement of
`diagnoses.clinicalNarrative` is incorrect and the field is not defended here.
This document exists to explain every dependency attached to it so the Owner
can assign each dependency's correct future destination.

---

## 0. Critical Finding — Read This First

**`diagnoses.clinicalNarrative` (and the entire card it lives in) is currently
unreachable dead code in the running application. It is not merely
"incorrectly placed" — it is not rendered by any current code path.**

Evidence:
- The Diagnoses section's card list is `SECTION_CONFIGS.diagnoses.cards`
  (`RNICA.jsx:8890-8935`). It contains exactly six cards: **Primary
  Diagnosis, Terminal Prognosis, Secondary Diagnoses, LCD Eligibility,
  Comorbidities and Co-existing Conditions, LCD Supporting Evidence.** None
  of these six card objects has `customRenderer: "clinicalNarrative"`.
- The renderer (`renderGenericSection`, `RNICA.jsx:8221`) iterates
  `resolvedCards` — which for the Diagnoses section is exactly
  `SECTION_CONFIGS.diagnoses.cards` unmodified (`RNICA.jsx:8224-8228`; the
  `uiProfile` filter only applies to the `spiritual` section).
- The conditional branch `if (sectionKey === "diagnoses" && card.customRenderer
  === "clinicalNarrative")` (`RNICA.jsx:8343-8356`), which is the only place
  `<ClinicalNarrativeCard>` is ever referenced, therefore **never matches any
  card in the current cards array and never executes.**
- Both call sites of `renderGenericSection` (`RNICA.jsx:11293`,
  `RNICA.jsx:11308`) pass the same `SECTION_CONFIGS[route.formSection]` —
  there is no separate pilot-only or alternate Diagnoses card list that
  includes this card.
- Consequently, **`diagnoses.diseaseTrajectory`, `diagnoses.rnAddendum`, and
  `diagnoses.clinicianClarification` — which are also only rendered inside
  this same dead `ClinicalNarrativeCard` (`RNICA.jsx:2013-2170`) — are
  currently unreachable too.** The "Build Draft from Documented Findings"
  button and `buildClinicalNarrative()` template renderer (`RNICA.jsx:2027-2032`,
  `sns-emr-frontend/src/intake/clinicalNarrativeBuilder.js:109`) are also
  unreachable — `buildClinicalNarrative` has exactly one call site in the
  entire codebase, and it is inside this dead card.

**Operational consequence this creates today (not a future risk — a present
one):** any existing/historical RNICA record that already has
`diagnoses.clinicalNarrative` text with `clinicalNarrativeReviewed !== true`
(set via direct API, a test fixture, or an earlier build before this card
became unreachable) will show the soft warning
`diagnoses.clinicalNarrativeReviewed` (`RNICA.jsx:1076-1077`) and fail the
backend `narrativeReviewed` Lock-readiness check
(`rnica_finalization_service.py:120-127`) — **with no UI control anywhere in
the current build that lets a nurse check the "reviewed" box to clear it.**
This is a real, present workflow-blocking bug for any record in that state,
independent of any future redesign decision.

Given this, the Owner's decision to remove `diagnoses.clinicalNarrative`
from the future Diagnosis Workspace is **not a removal of a working nurse
feature** — the feature has not been reachable by a nurse through the
current UI. It is closer to removing orphaned code and a latent Lock bug
than to removing an active workflow.

The Owner's list of Diagnosis Workspace fields to retain (Primary Diagnosis,
Secondary Diagnoses, Comorbidities, HOPE Diagnosis Category, Disease
Trajectory, LCD Supporting Evidence, LCD Eligibility Narrative, Recent
Hospitalizations, Recent Emergency Room Visits, Utilization Notes, RN
Addendum, Clinician Clarification) is the correct **future** state list —
but it should be understood that **Disease Trajectory, RN Addendum, and
Clinician Clarification are also not currently reachable in the UI today**
and would need to be **revived** (given a working card/renderer entry),
not merely "retained," if they are to actually appear for nurses. This is
flagged explicitly so the future implementation plan scopes that correctly.

*(Recent Hospitalizations, Recent Emergency Room Visits, and Utilization
Notes were not located as existing fields in `diagnoses.*` in this repository
under any name searched; if the Owner intends these as new fields, that is a
distinct addition, not a rewiring of an existing field, and is out of scope
for this document.)*

---

## PART 1 — `diagnoses.clinicalNarrative` Explained

1. **What exact information is the nurse currently expected to enter?**
   Per the field's intended design (not its current reachability): free-text
   documentation of the RN's clinical findings and disease trajectory,
   scoped to the Diagnoses section, either typed manually or seeded from the
   "Build Draft from Documented Findings" deterministic template. **In the
   currently running application, no nurse can enter anything into this
   field — the input control does not render (see Part 0).**

2. **Why did the repository originally place the field in Diagnoses?**
   The in-code comments (`RNICA.jsx:480-486`, `2002-2011`) describe intent:
   pairing a clinical-findings narrative with Disease Trajectory
   classification as "Section 10," deliberately distinct from the LCD
   eligibility narrative in the same section. This reads as a repository
   design choice to co-locate a findings synthesis with diagnosis/trajectory
   data, not a citation of any external requirement.

3. **Does any regulation, CMS requirement, HOPE requirement, or hospice
   requirement explicitly require a narrative in the Diagnoses section?**
   **NO EXTERNAL COMPLIANCE REQUIREMENT FOUND FOR DIAGNOSIS-SECTION
   PLACEMENT.** Direct evidence: the validation comment at `RNICA.jsx:1069-1071`
   states outright — *"The frozen master map does not cite a HOPE code for
   this narrative (unlike the hard-blocking Diagnoses/Pain/etc. items
   above)."* No `hopeCode` or `cms` prop is attached to the (non-existent)
   card definition, and no HOPE/CMS reference to `clinicalNarrative` was
   found anywhere in the backend.

4. **Was the current placement a repository design choice rather than an
   external compliance requirement?** Yes — confirmed by #2 and #3 above.

5. **Every frontend component that reads or writes the field:**
   - `ClinicalNarrativeCard` (`RNICA.jsx:2013-2170`) — reads/writes via
     `updateField("clinicalNarrative", ...)`. **Dead/unreachable (Part 0).**
   - `validateRNICA` (`RNICA.jsx:1076-1077`) — reads only, produces the soft
     warning.
   - `FINALIZATION_CHECK_SECTION_MAP` (`RNICA.jsx:232-238`) — maps the
     `narrativeReviewed` readiness-check key to the `"diagnoses"` section for
     navigation purposes (used to jump the nurse to a section when a
     finalization check fails — itself unreachable in practice since the UI
     it would navigate to cannot display the field).

6. **Every backend service that reads or writes the field:**
   - `rnica_finalization_service.py:120-127` — reads `diagnoses.clinicalNarrative`
     and `diagnoses.clinicalNarrativeReviewed` for the `narrativeReviewed`
     Lock-readiness check.
   - `rnica_amendment.py:78` (model column comment only, not a query) —
     documents that `section_reference` may point at
     `"diagnoses.clinicalNarrative"`.
   - No write path was found in any backend service (no evidence/harvest
     service, no AI service, no HOPE or POC service writes this field).

7. **Every validation rule connected to the field:**
   Exactly one — the soft client warning at `RNICA.jsx:1076-1077`
   (`diagnoses.clinicalNarrativeReviewed`). This is a warning, not a hard
   error.

8. **Every lock-readiness rule connected to the field:**
   Exactly one — the backend `narrativeReviewed` check
   (`rnica_finalization_service.py:120-127`). Logic: `ready = (not
   has_text(narrative)) or reviewed`.

9. **Every reviewed-state rule connected to the field:**
   `clinicalNarrativeReviewed` boolean, reset to `false` automatically
   whenever the narrative text changes (`RNICA.jsx:2029-2039`, inside the
   dead card). No other reviewed-state mechanism references it.

10. **Every amendment reference connected to the field:**
    `rnica_amendment.py:78` documents the field as a valid
    `section_reference` value. `backend/tests/test_rnica_amendments.py:36,190,203`
    exercise an amendment with `section_reference =
    "section_10_clinical_narrative"` against `diagnoses.clinicalNarrative`
    content.

11. **Every audit dependency connected to the field:**
    Amendment records referencing it are captured in the amendment audit
    trail (test evidence above). No separate audit-log entry keyed
    specifically to this field was found outside the amendment system.

12. **Every AI, rules-engine, structured-findings, or draft-generation
    dependency connected to the field:**
    Only the deterministic (non-AI) `buildClinicalNarrative()` template
    renderer (`clinicalNarrativeBuilder.js:109`), invoked solely from the
    dead card (`RNICA.jsx:2028`). `rnica_intelligence.py:68` reads
    `diagnoses.diseaseTrajectory` (a sibling field in the same dead card,
    not `clinicalNarrative` itself) as one input string for its findings
    heuristics. No structured-findings or AI-harvesting path targets
    `diagnoses.clinicalNarrative`.

13. **Every dashboard, IDG, POC, HOPE, billing, export, and reporting
    consumer:** None found. It is absent from
    `clinical_note_validation_engine.py`'s `RN_ICA_REQUIRED_FIELD_GROUPS`
    (confirmed by direct inspection — only `finalization.clinicalNarrative`,
    `diagnoses.lcdEligibilityNarrative`, `diagnoses.diseaseTrajectory`, and
    `diagnoses.primaryDiagnosis` are listed there), so it has no path into
    `dashboard_service.py` or `idg_engine.py`. No HOPE, POC, or billing
    service references it.

14. **What fails if the field is no longer actively authored in Diagnoses?**
    Nothing currently authored would be lost, because nothing can currently
    be authored there (Part 0). The only thing that changes is: (a) the
    `narrativeReviewed` Lock check permanently becomes a pass (since the
    field can never be non-empty going forward if the field is removed),
    and (b) future amendments can no longer reference
    `"diagnoses.clinicalNarrative"` as a section (existing ones are
    unaffected if the amendment table/history is preserved).

15. **Classification of each failure:**

    | Item | Classification |
    |---|---|
    | `narrativeReviewed` Lock check becoming a permanent pass | Stale-code failure (the check is already effectively decorative today since the field is unreachable) |
    | Loss of amendment `section_reference` target for *future* amendments | Workflow failure (minor) — only affects new amendments that would have targeted this section |
    | Historical records with existing `diagnoses.clinicalNarrative` text | Historical-data issue — must be preserved read-only, not a live failure |
    | Any compliance/billing/HOPE/POC/dashboard/IDG failure | **No actual failure** — no such consumer exists |

---

## PART 2 — `finalization.clinicalNarrative` Explained

1. **What exact information is the nurse expected to enter?**
   A whole-chart synthesis narrative, written or reviewed at the end of the
   assessment: findings, changes/decline, interventions and response,
   risks, and the plan (per its own placeholder text,
   `RNICA.jsx:9699-9700`).

2. **Why does the field belong in Finalization?**
   Its own UI copy assumes the rest of the chart is already documented
   ("Synthesize the completed whole-patient assessment findings..."), and
   it sits immediately before the attestation/signature fields
   (`signatureCertification`, `clinicianSignature`) in the same section.

3. **Every hard validation connected to it:**
   `RNICA.jsx:1091-1092` — hard client error, "Clinical narrative is
   required before attestation," if empty. This is a true block, unlike the
   diagnoses field's soft warning.

4. **Every compliance-blocking rule connected to it:**
   `clinical_note_validation_engine.py:380-405` (`RN_ICA_REQUIRED_FIELD_GROUPS`,
   entry labeled "Clinical Narrative," section "Finalization") — when an
   RNICA-workflow `ClinicalNote` is validated, a missing value produces
   `rn_ica_required_missing:finalization.clinicalNarrative` and a
   compliance-blocking item (`_validate_required_rn_ica_sections()`,
   `clinical_note_validation_engine.py:934-985`).

5. **Every attestation and signature dependency:**
   It is one of the client-side hard gates that must be satisfied before
   the nurse can complete `signatureCertification` and
   `clinicianSignature` in the same Finalization section.

6. **Every AI transcript or draft-insertion dependency:**
   `handleInsertAiNarrative` (`RNICA.jsx:9698-9720`) — blank-only-write
   auto-fill from a visit recording's transcript. Confirmed live (not
   gated behind any dead card).

7. **Every dashboard or IDG readiness consumer:**
   Via `clinical_note_validation_engine.py`'s compliance-blocking result,
   persisted to `note.content["_validation"]`
   (`_persist_validation_result_to_note`) and read through
   `get_note_validation_flags()`, consumed by `dashboard_service.py` (5 call
   sites) and `idg_engine.py` (3 call sites, e.g. `red_flags`,
   `needs_clarification` checks feeding IDG readiness).

8. **Every audit dependency:** `_write_audit_log` /
   `audit_flags` in `clinical_note_validation_engine.py` records
   `rn_ica_required_missing` when the field is absent on a validated note.

9. **Every lock dependency:** (a) the RNICA client hard-error attestation
   gate (#3), and (b) the `compliance_blocking_items` /
   `finalization_allowed` flag produced by the clinical-note validation
   engine when the assessment is represented as an RN-discipline
   `ClinicalNote`.

10. **What fails if it is missing?** The nurse cannot complete attestation
    in the RNICA UI (hard error), and — separately, when routed through the
    `ClinicalNote` compliance path — the note is flagged as
    `rn_ica_required_missing` and blocked from being treated as
    finalization-ready by that engine.

11. **Which requirements are internal product rules?** All of them. The
    hard client error, the compliance-blocking field-group entry, and the
    AI-draft target are all product-defined; none cite an external CMS/HOPE
    code.

12. **Which requirements are externally required, per repository evidence?**
    None found. No `hopeCode`/`cms` tag is attached to this field or its
    card definition either.

13. **Can this field become the sole future nurse-facing Clinical Narrative
    without losing a legitimate clinical or compliance requirement?** Yes,
    on current evidence — it already carries every real (product-level)
    compliance and attestation obligation that exists for a "Clinical
    Narrative" in this system. The only things not automatically carried
    over are the *diagnoses-specific* mechanisms unique to the dead card
    (see Part 5).

---

## PART 3 — Dependency-by-Destination Matrix

| Dependency | File:Line | Current Purpose | Current Trigger | Current Output | Current Consequence | External Compliance Requirement | Product Rule | Must Survive | Correct Future Destination | Rewiring Required | Historical Data Impact | Tests Required | Repository Evidence |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `ClinicalNarrativeCard` UI (clinicalNarrative textarea) | `RNICA.jsx:2013-2170` | Free-text findings/trajectory input | N/A — unreachable | None (dead) | None (dead) | NO | NO (never reached, so not even an active product rule today) | NO | remove as redundant | NO (already unreachable) | None (nothing renders it) | Confirm removal doesn't affect anything else that imports the component | `RNICA.jsx:8343-8356` dispatch never matches |
| `narrativeReviewed` Lock check | `rnica_finalization_service.py:120-127` | Blocks Lock if narrative present-but-unreviewed | Lock/finalization readiness evaluation | `checks["narrativeReviewed"]` ready/blocked flag | Currently blocks Lock only for historical/API-set records with text + unreviewed | NOT VERIFIED (no HOPE code cited; treat as internal) | YES (internal readiness gate) | Only for historical records already in that state | finalization narrative review control (or removed if attestation gate is judged sufficient) | YES | Must not silently unblock historically-blocked records without explicit reconciliation | Regression test on existing locked/unlockable fixtures | `rnica_finalization_service.py:120-127`, `backend/tests/test_rnica_finalization.py:130-141` |
| `clinicalNarrativeReviewed` checkbox/state | `RNICA.jsx:2033,2039,2137-2142` (dead) | Reviewed-state toggle, resets on edit | User checkbox click | Boolean flag | Feeds `narrativeReviewed` check | NO | YES (internal) | NO (only meaningful if diagnoses field survives) | remove as redundant, or migrate concept to a finalization review control if the Owner wants an explicit "narrative reviewed" state on the new field | NO (unreachable today) | Preserve historical boolean values as read-only | None new | `RNICA.jsx:2033-2039` |
| "Build Draft from Documented Findings" button + `buildClinicalNarrative()` | `RNICA.jsx:2020-2032`, `clinicalNarrativeBuilder.js:109` | Deterministic template draft generator | Button click (dead) | Populates `clinicalNarrative` text | None (dead) | NO | YES (internal UX aid) | Only if the Owner wants the template feature revived | finalization.clinicalNarrative | YES (retarget `updateField` call and its data source references) | None (never wrote data) | New test if revived | `RNICA.jsx:2028` sole call site |
| Amendment `section_reference = "diagnoses.clinicalNarrative"` | `rnica_amendment.py:78`; `test_rnica_amendments.py:190,203` | Labels an amendment as concerning this field | Amendment creation (RN/clinician correction) | Stored string in `section_reference` column | Existing amendments keep this exact string permanently | NO | YES (internal labeling) | YES (existing rows) | audit history (read-only; no rewrite of past rows) | NO for existing rows; YES for the *option list* offered on new amendments going forward | Do not rewrite existing `section_reference` values | Regression test confirming old amendments still display/query correctly | `rnica_amendment.py:78` |
| `FINALIZATION_CHECK_SECTION_MAP["narrativeReviewed"] = "diagnoses"` | `RNICA.jsx:235` | Navigates nurse to a section when this check fails | Finalization checklist "go to section" click | Section-key string used for navigation | Currently navigates to a section that cannot display the relevant control | NO | YES (internal navigation aid) | NO as currently mapped | Repoint to `"finalization"` if the check is repointed there, or delete the map entry if the check itself is removed | YES (one-line map value change) | None | Manual click-through test | `RNICA.jsx:232-238` |
| `diseaseTrajectory` field/selector | `RNICA.jsx:2016,2045-2055` (dead) | Disease-course classification, feeds `buildClinicalNarrative` template and `rnica_intelligence.py` heuristics | N/A — unreachable | None currently persisted via UI | `rnica_intelligence.py:68` reads an always-empty value today | NO | YES (Owner has explicitly asked to retain this in Diagnosis Workspace) | YES (per Owner's retained list) | disease trajectory (stays in Diagnosis Workspace, but needs a **live** card, since it is currently dead) | YES — needs a working `customRenderer` entry added to `SECTION_CONFIGS.diagnoses.cards`, not merely "kept" | None (never persisted) | New test once revived | `RNICA.jsx:2045-2055`, `8890-8935` (absence) |
| `rnAddendum` / `clinicianClarification` | `RNICA.jsx:2149-2157` (dead) | Pre-lock working notes on Diagnoses | N/A — unreachable | None currently persisted via UI | None | NO | YES (Owner has asked to retain both) | YES (per Owner's retained list) | RN Addendum / Clinician Clarification (stay in Diagnosis Workspace, but need a **live** card) | YES — same as Disease Trajectory above | None | New test once revived | `RNICA.jsx:2149-2157` |

---

## PART 4 — Specific Items Explained

**1. `narrativeReviewed`**
- *Why does it exist?* To ensure a nurse-authored diagnoses-section
  narrative is not left "stale" (unreviewed after being drafted or edited)
  when the assessment locks.
- *What does it prove?* That if diagnoses-section narrative text exists, a
  human has confirmed it reflects current findings.
- *Real compliance requirement or internal mechanism?* Internal — no
  external code citation found (see Part 1, #3).
- *Could final attestation replace it?* Yes, functionally — the Finalization
  attestation gate already requires `finalization.clinicalNarrative` to be
  present before signature, which is a stronger (hard, not soft) gate
  serving the same underlying goal ("don't sign without a reviewed
  narrative").
- *Could it be relocated to Finalization?* Yes, technically (the check only
  needs a form-data path and a boolean flag); but since
  `finalization.clinicalNarrative` has no analogous "reviewed" checkbox
  today (it's always freshly required, not "reviewed once and reused"), a
  literal relocation would be a new control, not a straight move.
- *What would need to change?* Either (a) remove this check entirely and
  rely on the attestation hard-error, or (b) add a new reviewed-state
  control to `finalization.clinicalNarrative` — an explicit product decision
  the Owner has not yet made and this document does not make it either.

**2. `clinicalNarrativeReviewed`**
- *Why is a separate reviewed checkbox required?* To let the same nurse (or
  a later reviewer) mark that the diagnoses-section narrative text has been
  checked after being drafted/edited.
- *Does the nurse review the nurse's own narrative?* As designed, yes — no
  second-reviewer role distinction was found in this code path.
- *Does any external requirement demand this exact checkbox?* No.
- *What happens when the narrative changes?* The checkbox is force-reset to
  `false` (`RNICA.jsx:2033,2039`).
- *Should the future review control apply to `finalization.clinicalNarrative`
  instead?* Not resolved here — this is exactly the kind of decision Part 5
  Option A/B are structured to let the Owner make, since it depends on
  whether the Owner wants a "reviewed" state on the finalization field or
  considers the hard-required-before-attestation rule sufficient on its own.

**3. "Build Draft from Documented Findings"**
- *What information does it use?* `buildClinicalNarrative(fullFormData, {})`
  — reads across the whole in-progress form (not just Diagnoses) to
  generate a template narrative (`clinicalNarrativeBuilder.js:109`).
- *What field does it currently populate?* `diagnoses.clinicalNarrative` —
  but only inside the dead card, so it currently populates nothing in the
  running app.
- *Why was the target placed in Diagnoses?* Same repository-design-choice
  answer as Part 1, #2 — no requirement found; it was written as a
  companion to the (also dead) Disease Trajectory field.
- *Can the exact draft-generation behavior target
  `finalization.clinicalNarrative` instead?* Yes, mechanically — the
  template function already reads the whole form, so it is at least as
  well-suited (arguably better-suited, since it already synthesizes
  cross-section data) to populating a whole-chart synthesis field in
  Finalization as it ever was to populating a Diagnoses-only field.
- *What functionality or evidence would be lost?* None — the function is
  never currently invoked by any user.

**4. Amendment section reference**
- *Why do existing amendments reference `diagnoses.clinicalNarrative`?*
  Because at the time those amendments were created (via direct API/test,
  not the currently-dead UI, or from a build where the card was still
  live), the amendment system offered that string as a valid
  `section_reference` value.
- *Can future amendments reference `finalization.clinicalNarrative`
  instead?* Yes — `section_reference` is a free-form `String(128)` column
  (`rnica_amendment.py`), not an enum tied to a fixed field list.
- *How will historical amendment references remain readable and
  auditable?* By leaving existing rows' `section_reference` values
  untouched — no rewrite, no backfill, no reinterpretation. Only the
  *option offered when creating new amendments* changes going forward.

**5. Lock readiness — full breakdown, no generic "compliance" label**

| Type | Item | Field | File:Line |
|---|---|---|---|
| Client hard error | Clinical narrative required before attestation | `finalization.clinicalNarrative` | `RNICA.jsx:1091-1092` |
| Client warning (soft) | Clinical narrative documented but not yet reviewed | `diagnoses.clinicalNarrative` / `diagnoses.clinicalNarrativeReviewed` | `RNICA.jsx:1076-1077` |
| Server readiness check | `narrativeReviewed` | `diagnoses.clinicalNarrative` / `diagnoses.clinicalNarrativeReviewed` | `rnica_finalization_service.py:120-127` |
| Server readiness check | `lcdBaseline` | `diagnoses.lcdEligibilityNarrative` | `rnica_finalization_service.py:130-134` |
| Clinical-note compliance blocker | `rn_ica_required_missing:finalization.clinicalNarrative` | `finalization.clinicalNarrative` | `clinical_note_validation_engine.py:380-405, 934-985` |
| Attestation requirement | `signatureCertification`, `clinicianSignature` | `finalization.*` | `RNICA.jsx` Finalization section fields |

**6. Clinical-note validation engine**
`finalization.clinicalNarrative` is already the canonical "Clinical
Narrative" entry in `RN_ICA_REQUIRED_FIELD_GROUPS`
(`clinical_note_validation_engine.py:380-405`) because that engine's field
group is explicitly labeled `"Clinical Narrative"` / section `"Finalization"`
and its `paths` list is `["finalization.clinicalNarrative",
"assessment_summary", "nursing_summary"]` — `diagnoses.clinicalNarrative` is
not present in any field group in that file. Downstream consumers of that
compliance result: `dashboard_service.py` (5 call sites via
`get_note_validation_flags()`) and `idg_engine.py` (3 call sites, gating
`red_flags`/`needs_clarification` readiness signals).

**7. AI visit-recording insertion**
Confirmed current target: `finalization.clinicalNarrative`, via
`handleInsertAiNarrative` (`RNICA.jsx:9698-9720`), blank-only-write.
Keeping `finalization.clinicalNarrative` as the sole future nurse-facing
narrative **fully preserves this functionality** — it is already targeting
the correct field and requires no change.

---

## PART 5 — Corrected Future Workflow Options

### Option A
One active nurse-facing Clinical Narrative: `finalization.clinicalNarrative`.
All legitimate dependencies repointed to the Finalization workflow.
`diagnoses.clinicalNarrative` becomes historical/read-only legacy data.

- **Requirements preserved:** Attestation hard-error, AI transcript
  insertion, compliance-blocking check (all already on this field).
- **Requirements removed:** The diagnoses-scoped `narrativeReviewed`
  soft-warning/Lock-check pairing (superseded by the stronger attestation
  hard-error); the never-reachable "Build Draft" button in its current
  location (could be rebuilt targeting Finalization instead, or dropped).
- **Rewiring required:** Remove/repoint `narrativeReviewed` check;
  repoint `FINALIZATION_CHECK_SECTION_MAP` entry or delete it; decide
  fate of `buildClinicalNarrative()` (retarget vs. retire).
- **Historical-data impact:** `diagnoses.clinicalNarrative` and
  `clinicalNarrativeReviewed` values preserved as read-only fields on
  existing records; not merged into `finalization.clinicalNarrative`.
- **Audit impact:** None on existing audit rows; new locks stop referencing
  the diagnoses check.
- **Amendment impact:** Existing `section_reference` values untouched; new
  amendments no longer offer `"diagnoses.clinicalNarrative"` as a target.
- **AI impact:** None — AI insertion already targets the correct field.
- **Validation impact:** One soft warning removed; hard error unchanged.
- **Lock impact:** One redundant server check removed (the one already
  effectively decorative today); attestation gate unchanged.
- **Risks:** Must explicitly resolve any *existing* locked-or-lockable
  record currently blocked by the stale `narrativeReviewed` check before
  or during this change, so removing the check doesn't silently paper over
  a record that a human should still look at.
- **Recommendation:** This option matches the Owner's locked decision and
  requires the least new construction, since `finalization.clinicalNarrative`
  already carries every real requirement.

### Option B
One active Clinical Narrative in Finalization, plus a distinct
diagnosis-specific field only if a separate legitimate clinical purpose is
proven; that field must not be called "Clinical Narrative" and must not
duplicate the whole-chart synthesis.

- **Requirements preserved:** Everything in Option A, plus whatever narrow,
  named purpose is defined for the new diagnosis-specific field (e.g., a
  disease-trajectory-specific clinical note, distinct from a synthesis).
- **Requirements removed:** Same as Option A for the narrative itself; the
  *concept* of a diagnoses-section clinical note is not removed, only
  renamed/re-scoped.
- **Rewiring required:** Same as Option A, plus defining and building a
  new, narrowly-scoped field (not a rewiring of the existing dead field,
  since its purpose/name changes).
- **Historical-data impact:** Same as Option A.
- **Audit / amendment / AI / validation / lock impact:** Same as Option A
  for the narrative; a new field would need its own (likely minimal) rules
  defined separately, out of scope for this document.
- **Risks:** Risk of recreating the same ambiguity if the new field's scope
  isn't kept genuinely distinct from a synthesis narrative.
- **Recommendation:** Only pursue if a real, separate clinical need is
  identified (e.g., the Owner's "RN Addendum"/"Clinician Clarification"
  fields already may serve this narrower purpose — see Part 0's note that
  these are Owner-retained fields that also need to be revived, not newly
  invented).

### Option C
Not proposed. No repository or compliance evidence was found supporting a
third structural approach beyond A/B; recommending one would not be
evidence-based per this document's constraints.

**No option preserves two nurse-authored whole-chart narratives merely
because two fields currently exist in the codebase.**

---

## PART 6 — Historical Preservation

The correction must preserve, unchanged and un-merged:
- Existing `diagnoses.clinicalNarrative` values (read-only going forward).
- Existing `finalization.clinicalNarrative` values.
- Existing `clinicalNarrativeReviewed` values.
- Existing amendment `section_reference` values (including
  `"diagnoses.clinicalNarrative"` / `"section_10_clinical_narrative"`
  strings).
- Existing audit history.
- Existing locked RNICA records.
- Existing validation results (including any prior
  `rn_ica_required_missing` audit flags already recorded).

Must not: delete historical narrative data; overwrite one narrative with
the other; automatically merge narratives; rewrite historical migrations;
use `alembic stamp`.

A forward-only preservation strategy (schema/migration design) is explicitly
**out of scope for this document** and must be produced under a separately
authorized implementation-planning deliverable, per the locked correction's
Section 3 requirements.

---

## Final Required Answers

1. **What exact compliance requirement is attached to
   `diagnoses.clinicalNarrative`?** None found. It has one internal
   product-level soft warning and one internal server readiness check;
   no external CMS/HOPE citation exists.
2. **Is that requirement external or internally created?** Internally
   created (product rule), not external.
3. **What exact compliance requirement is attached to
   `finalization.clinicalNarrative`?** One internal hard client
   validation error, plus one internal compliance-blocking field-group
   entry in `clinical_note_validation_engine.py`. No external CMS/HOPE
   citation exists for this field either.
4. **Which narrative is already treated as the canonical RNICA Clinical
   Narrative by the compliance engine?** `finalization.clinicalNarrative`
   (confirmed: it is the only one of the two present in
   `RN_ICA_REQUIRED_FIELD_GROUPS`).
5. **Which existing dependencies should move to Finalization?** The
   `narrativeReviewed` readiness concept (if retained in any form) and the
   "Build Draft from Documented Findings" generator, per Part 3/4 — subject
   to the Owner's choice on whether a reviewed-state control is even
   wanted on the finalization field.
6. **Which existing dependencies should remain tied to diagnosis-specific
   information?** Disease Trajectory, RN Addendum, and Clinician
   Clarification — per the Owner's retained list — but all three require a
   **new, live** card/renderer entry, since none is currently reachable.
7. **Which dependencies are redundant and may be removed later?** The dead
   `ClinicalNarrativeCard` component itself (once its live-reachable
   sub-fields, if any, are relocated to a working card); the
   `clinicalNarrativeReviewed` checkbox concept, if the Owner decides the
   Finalization attestation gate is sufficient on its own.
8. **Can the redesigned RNICA show only one nurse-facing Clinical Narrative
   in Finalization?** Yes — `finalization.clinicalNarrative` already
   carries every real (product-defined) requirement found in this
   repository; no external requirement was found anywhere that depends on
   a second, diagnoses-section narrative.
9. **What exact rewiring would that require?** (a) Remove or repoint the
   `narrativeReviewed` server check and its `FINALIZATION_CHECK_SECTION_MAP`
   entry; (b) decide the fate of `buildClinicalNarrative()`/"Build Draft"
   (retire or retarget to Finalization); (c) stop offering
   `"diagnoses.clinicalNarrative"` as a new-amendment target while
   preserving existing amendment rows; (d) build live cards for Disease
   Trajectory, RN Addendum, and Clinician Clarification if those are to
   actually reach nurses, since they are currently dead code riding on the
   same removed card.
10. **What historical information must remain accessible?** All items
    listed in Part 6 — as read-only legacy data, never deleted, never
    auto-merged, never used to silently overwrite
    `finalization.clinicalNarrative`.

---

## Final Status

| | |
|---|---|
| Placement decision made by this document | **NO** — this document explains dependencies only |
| Product decision authority | Owner (per `RNICA_CLINICAL_NARRATIVE_ARCHITECTURAL_CORRECTION.md`) |
| New finding requiring Owner attention | `diagnoses.clinicalNarrative`, `diseaseTrajectory`, `rnAddendum`, and `clinicianClarification` are all currently unreachable dead UI — "retain" for these three (excluding the narrative) means "revive," not "keep as-is" |
| Figma handoff | **NOT AUTHORIZED YET** |
| Code | BLOCKED |
| Schema | BLOCKED |
| Migrations | BLOCKED |
| Implementation | BLOCKED |

---

## Cross-References

- `docs/tenant-platform/RNICA_CLINICAL_NARRATIVE_ARCHITECTURAL_CORRECTION.md`
- `docs/tenant-platform/RNICA_NARRATIVE_FIELDS_ANALYSIS.md`
- `docs/tenant-platform/RNICA_NARRATIVE_PLACEMENT_DECISION.md`
- `docs/tenant-platform/RNICA_SECTION_BREAKDOWN.md`
