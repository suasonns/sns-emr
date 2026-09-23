# RNICA HOPE / SFV Field Placement Map

**Document Status:** AUDIT BASELINE / REMEDIATION REQUIRED — this document is not implementation-complete and the system is not compliant; confirmed defects listed in its Phase 2 Executive Summary remain open. See `RNICA_PHASE3_REMEDIATION_REGISTER.md`.

## Phase 2 — Executive Summary (independent re-trace, commit `16264cf`)

**Added by the Phase 2 audit pass. Documentation only — no application
code, test, schema or migration was changed. Nothing below deletes or
supersedes the Phase 1 content that follows; it records an independent
re-derivation of the four high-risk findings plus the matrices that support
them.**

### Verdicts on Findings A-D

| Finding | Phase 1 claim | Phase 2 independent verdict | Key evidence re-derived this pass |
|---|---|---|---|
| **A — HOPE harvesting is frontend-only** | No backend service extracts RNICA field values into a HOPE payload | **PASS (confirmed)** | Full-tree backend scan found HOPE code only as: item-code constants `backend/app/domain/forms/form_registry.py:341-418`; metadata getters `:1137-1156`; submission-workflow status `backend/app/services/rnica_hope_workflow_service.py:25-200`; SFV/HUV task engine `backend/app/services/hope_phase_b_engine.py`; workflow endpoints `backend/app/api/visits.py:1358-1478`. The only code that walks `form_data` and emits item-code-keyed content is `sns-emr-frontend/src/intake/hopeReportMapper.js:462-670`. |
| **B — N0500/N0510/N0520 collision** | These medication item codes are reused as BIMS codes | **PASS (confirmed, and wider than reported)** | Nine usage sites across two contradictory semantics: BIMS at `RNICA.jsx:575, 1048-1050, 9016, 9030-9033`, `sns-emr-frontend/src/config/bodySystems.js:20`, `backend/app/services/evidence/structured_findings.py:1224-1270`, `structuredFindingRegistry.generated.js:1748-1794`; opioid/bowel at `form_registry.py:408-412`, `hopeReportMapper.js:529-530, 633-635`, `HopeReport.jsx:17-18`. |
| **C — I8005 dead export path** | `diagnoses.hopeComorbidities.other` has no UI writer | **FAIL (claim refuted)** | A dedicated "Other Medical Condition" checkbox writes that exact path at `RNICA.jsx:2668` (`setHope("other", …)` → `:2586`), tagged I8005 at `:2671`, defaulted at `:534`, inside a card that **is** dispatched (`customRenderer: "hopeComorbidities"` `:8939` → `:8376-8379`). The Phase 1 reasoning looked only at the 14-entry `HOPE_COMORBIDITY_CATEGORIES` loop and missed the checkbox rendered after it. |
| **D — Lock gate reads a path nothing writes** | `evaluate_finalization_readiness()` validates `diagnoses.clinicalNarrative*` while the live field is `finalization.clinicalNarrative` | **PARTIAL (confirmed premise, corrected consequence)** | Premise confirmed: the gate reads `diagnoses.clinicalNarrative`/`…Reviewed` (`rnica_finalization_service.py:120-121`); the only writers are inside `ClinicalNarrativeCard` (`RNICA.jsx:2029, 2038, 2140`), which no `SECTION_CONFIGS` card dispatches (`:8353` condition never satisfied). Consequence corrected: the check fails **open**, not closed — `narrative_ready = (not _has_text(narrative)) or narrative_reviewed` (`:122`), so a current-UI record with no value passes vacuously. `backend/tests/test_rnica_finalization.py:56-65, 116-119` proves a record with **no narrative at all** locks cleanly. The real defect is therefore *silent non-enforcement* of the live narrative plus an *unsatisfiable* gate for legacy records that do carry the old path. |

### Other material findings from Phase 2

- `finalization.clinicalNarrative` — the field the RN actually types into
  (`RNICA.jsx:9714`, AI writer `:10313-10322`) — is **never read** by
  `rnica_finalization_service.py`. Its only enforcement is client-side
  (`RNICA.jsx:1091-1092`).
- Eight fields are orphaned behind the undispatched `ClinicalNarrativeCard`
  (narrative, narrative-reviewed, disease trajectory, recent
  hospitalizations, recent ER visits, utilization notes, RN addendum,
  clinician clarification).
- Frontend and backend implement **different SFV trigger predicates** and
  **different due-date derivations**, and the frontend lets an SFV be
  self-attested on the triggering visit (`RNICA.jsx:9398`) — which the
  backend explicitly forbids (`hope_phase_b_engine.py:425-426`).
- The backend HOPE registry is not a reliable inventory: 13 item codes are
  exported but undeclared, and Z0400 is declared (`form_registry.py:416`)
  but never emitted.
- Several Phase 1 "missing field" rows are **refuted**: `vitals.mac`
  (`RNICA.jsx:417, 2906`), `demographics.militaryService` (`:368, 8003`),
  `pcg.healthStatus` (`:8060`), `pcg.anxietyLevel` (`:8062`),
  `pcg.ableToAdministerMeds` (`:8064`),
  `pcg.caregiverEvaluation.cognitiveAbility` (`:8086-8087`), the I8005
  checkbox, and the `chhaPoc.completed` writer (`:4113-4119`, mounted at
  `sns-emr-frontend/src/charts/PatientChart.jsx:798`) all exist and are
  writable today.

### Detailed matrices (Phase 2 deliverables, all under `docs/tenant-platform/`)

| Document | Contents |
|---|---|
| `HOPE_FIELD_TRACE_MATRIX.md` | All 55 registry item codes → frontend path → reachability → backend extraction (NONE FOUND for every one) → exporter line → test coverage |
| `SFV_LIFECYCLE_TRACE_MATRIX.md` | Every SFV/HUV trigger, due state, completion state, and the trigger-vs-completion conflation evidence |
| `ITEM_CODE_CONFLICT_MATRIX.md` | 7 item-code conflicts incl. the N0500-N0520 collision |
| `DEAD_EXPORT_PATH_ANALYSIS.md` | Unreachable export paths, dead capture paths, and the I8005 refutation |
| `LOCK_GATE_DEPENDENCY_TRACE.md` | Every path read by `evaluate_finalization_readiness()`, classified |
| `MISSING_FIELD_RECONCILIATION.md` | Fresh verification of the TABLE G "missing field" claims |
| `DUPLICATE_AUTHORITY_MATRIX.md` | 17 duplicate/conflicting write-authority rows |
| `HISTORICAL_COMPATIBILITY_RESULTS.md` | `deepMergeFormData` / `INITIAL_FORM` behaviour, code-level only |
| `RNICA_ACCEPTANCE_TEST_MATRIX.md` | Findings → tests, with honest Pass/Fail/Blocked/Not-yet-run |
| `AUTHORITY_APPLICABILITY_REGISTER.md` | 28 regulatory-framing claims, **all** NOT VERIFIED (no external source accessible) |
| `STAFF_SUPPORT_IMPACT_REGISTER.md` | RN-impact analysis and ranking of all 10 recommendations |

### Standing caveat

No external regulatory source (CMS HOPE specifications, HQRP/iQIES manuals,
California hospice licensing) was accessible in this environment. Every
regulatory framing in Phase 2 is recorded as
**NOT VERIFIED — external regulatory source not accessible this pass** and
requires human compliance/legal review. Only repository code and
configuration were verified.

---

**Type:** Documentation-only checkpoint. No UI change, no field add/remove, no
response-set change, no validation change, no exporter change.

**Purpose:** Reconcile, at the level of the individual field / response /
computed result / trigger / signature / order / workflow action, the legacy
HospiceMD comprehensive nursing assessment (14 screens, described to this
session in text; the images themselves were not available to the author of
this document) against the current SNS RNICA implementation, and assign every
field an owning screen in the final 13-screen model.

**Ground-truth rules applied**

1. Everything asserted about **SNS** comes from reading this repository at
   commit `16264cf`. Nothing about SNS is inferred from the legacy
   description.
2. Everything asserted about **legacy** comes only from the textual
   description of the 14 screenshots supplied in the directive. No legacy
   field was invented beyond that description.
3. Where the repository does not prove a fact, the row says
   `NOT VERIFIED` or `NOT FOUND IN REPOSITORY`. That is a correct outcome,
   not a defect in this document.
4. Screenshots are **not** treated as evidence of persistence, validation, or
   export anywhere in this document.

---

## 0. Primary evidence files read for this pass

```
Frontend: sns-emr-frontend/src/components/RNICA.jsx
          - SYMPTOM_IMPACT_CHECKLIST            :150-159
          - NAV_SECTIONS / LEGACY_ROUTES        :164-193
          - SIDEBAR_CONFIG (HOPE tagging)       :200-225
          - FINALIZATION_CHECK_SECTION_MAP      :232-239
          - FORM_REGISTRY (27 form sections)    :242-249
          - UPDATE_HIDDEN_ROUTE_KEYS            :251-252
          - LcdEligibilityCard                  :1601
          - LcdSupportingEvidenceCard           :1987
          - (diagnoses) clinicalNarrative card  :2015-2157
          - SecondaryDiagnosesCard              :2176
          - WoundListCard / wound row editor    :2330-2424
          - DmeStatusCard                       :2426-2494
          - HOPE_COMORBIDITY_CATEGORIES         :2496-2511
          - HopeComorbiditiesCard               :2565
          - DeclineTrackerCard                  :2715
          - AnthropometricsAutoBmiCard          :2880-2910
          - NutritionAnthropometricReferenceCard:2924-2950
          - WeightLossAutoCalcCard              :2957
          - DisciplineFrequencyOfVisitCard      :3263
          - FinalReviewDashboardCard            :6097
          - ConstipationAutoAssessCard          :6113
          - renderDemographics()                :7966-8205
          - custom-renderer dispatch            :8338-8535
          - SECTION_CONFIGS                     :8769-9768
Frontend: sns-emr-frontend/src/components/rn-ica/rnicaThirteenScreenTaxonomy.js  (whole file)
Exporter: sns-emr-frontend/src/intake/hopeReportMapper.js                        :1-716
Exporter: sns-emr-frontend/src/intake/HopeReport.jsx                             :13
Exporter: sns-emr-frontend/src/intake/ComplianceHopeBoard.jsx                    :9
Backend:  backend/app/domain/forms/form_registry.py                              :341-506
Backend:  backend/app/services/rnica_finalization_service.py                     :22-169
Backend:  backend/app/services/hope_phase_b_engine.py                            :24-220
Backend:  backend/app/services/rnica_hope_workflow_service.py                    :59-200
Backend:  backend/app/api/visits.py                                              :3611-3991
Backend:  backend/app/services/evidence/structured_findings.py                   :233-1250
Test:     sns-emr-frontend/src/intake/hopeReportMapper.test.js
Test:     backend/tests/test_rnica_finalization.py
Test:     backend/tests/test_rnica_hope_workflow.py
```

---

## 1. Legend

### Classification (allowed values only)

`HOPE` · `SFV` · `HOPE AND SFV` · `SNS CLINICAL` · `FACESHEET HARVEST` ·
`DIAGNOSIS SOURCE` · `ORDER/POC` · `REFERRAL` · `READINESS` ·
`AUDIT/SIGNATURE` · `COMPUTED RESULT` · `LEGACY DISPLAY ONLY` ·
`NOT VERIFIED`

### Status (allowed values only)

`PRESENT AND CORRECTLY PLACED` · `PRESENT BUT MISPLACED` ·
`PRESENT BUT RESPONSE SET INCOMPLETE` · `PRESENT BUT NOT HARVESTED` ·
`PRESENT BUT NOT WIRED` · `DUPLICATE OF FACESHEET` · `MISSING FROM SNS` ·
`NOT FOUND IN REPOSITORY` · `CONFLICTING` · `REQUIRES AUTHORITY REVIEW` ·
`VERIFIED COMPLETE`

### Target RNICA screen order used throughout (non-linear navigation, no gates)

| # | Screen |
|---|---|
| 1 | Evidence & Intake (target rename: *Identity & HOPE Demographics*) |
| 2 | Patient Story |
| 3 | Pain & Symptom Burden |
| 4 | Diagnosis & LCD |
| 5 | Functional Status |
| 6 | Body Systems |
| 7 | Caregiver & Support |
| 8 | Safety & Clinical Risk |
| 9 | ACP & Goals of Care |
| 10 | Orders & POC |
| 11 | Compliance & Readiness |
| 12 | AI Action Center |
| 13 | Finalization |

**Note on current code vs. this target order.** `RNICA_THIRTEEN_SCREENS`
(`rnicaThirteenScreenTaxonomy.js:25-124`) currently lists `patientStory` at
index 0 and `evidenceIntake` at index 1 — i.e. the inverse of the target
order above. The target order is documented here; **it is not applied in
code by this checkpoint.**

### Field-path convention

A path such as `vitals.pulseQuality` means key `pulseQuality` inside
`form_data.vitals`. Paths inside `SECTION_CONFIGS` are written relative to
their section, so `SECTION_CONFIGS.vitals` field `path: "pulseQuality"`
persists as `form_data.vitals.pulseQuality`. The one deliberate exception in
the codebase is the ADL card, which declares `dataSection: "musculoskeletal"`
while rendering under `performanceStatus` (`RNICA.jsx:9003`); its persisted
paths are therefore `musculoskeletal.adl.*`.

---

## 2. Executive findings (the five things that matter most)

1. **The HOPE harvest engine is a frontend module, not a backend service.**
   `sns-emr-frontend/src/intake/hopeReportMapper.js` is the only code in the
   repository that walks `form_data` and emits item-code-keyed HOPE content
   (`:554-645`). It is consumed by `HopeReport.jsx:13` and
   `ComplianceHopeBoard.jsx:9`. On the backend, every HOPE item code appears
   **only** as declarative metadata in
   `form_registry.py:341-437` (`hope_item_codes`, attached at `:506`) — no
   backend code reads a HOPE item code out of `form_data`. Backend HOPE code
   is limited to *workflow status* (`rnica_hope_workflow_service.py`) and the
   *SFV/HUV trigger engine* (`hope_phase_b_engine.py`). Consequence: HOPE
   correctness is enforced client-side only and is not re-validated
   server-side the way Lock readiness is.
2. **N0500/N0510/N0520 are exported from a form section that nothing
   writes.** The mapper reads `formData.medications.scheduledOpioid`,
   `.prnOpioid`, `.bowelRegimen` (`hopeReportMapper.js:476,529-530,633-635`),
   but `medications` is not in `FORM_REGISTRY` (`RNICA.jsx:242-249`) and no
   RNICA field writes those paths (repository-wide search returned only the
   mapper itself). Separately, RNICA's `neurological` section labels
   `hopeItems.n0500/.n0510/.n0520` as *BIMS Repetition/Recall/Temporal
   Orientation* (`RNICA.jsx:9030-9033`) — those paths are never read by the
   mapper, and CMS N0500-N0520 are opioid/bowel-regimen items, not BIMS.
   This is a genuine `CONFLICTING` item-code collision.
3. **I8005 "Other Medical Condition" is exported but has no input.** The
   mapper emits I8005 from `diagnoses.hopeComorbidities.other`
   (`hopeReportMapper.js:542`), but `HOPE_COMORBIDITY_CATEGORIES`
   (`RNICA.jsx:2496-2511`) contains exactly 14 entries and no `other` key, so
   `HopeComorbiditiesCard` never writes it. A repository-wide search for a
   writer of `hopeComorbidities.other` found none. I8005 therefore always
   exports "No" once structured comorbidities are in use.
4. **A1005/A1010 response sets are narrower than CMS HOPE.** RNICA offers
   6 race options (`RNICA.jsx:7992-7993`) and 3 ethnicity options
   (`:7994-7995`); the mapper passes them through verbatim as free text
   (`hopeReportMapper.js:571-572`) with no code lookup, unlike A0215/A1805/
   A1905 which do use official CMS code maps (`:58-122, 491-494`). The exact
   CMS A1005/A1010 code sets were not available from repository evidence and
   are recorded as `NOT VERIFIED` rather than asserted.
5. **The Lock gate reads a narrative path the UI no longer edits.**
   `evaluate_finalization_readiness()` checks
   `diagnoses.clinicalNarrative` / `diagnoses.clinicalNarrativeReviewed`
   (`rnica_finalization_service.py:120-128`), while the only narrative card
   in `SECTION_CONFIGS` is `finalization.clinicalNarrative`
   (`RNICA.jsx:9713-9716`); `SECTION_CONFIGS.diagnoses.cards`
   (`:8904-8945`) contains no `clinicalNarrative` renderer entry even though
   the dispatch branch still exists at `:8353`. Cross-referenced with
   `docs/tenant-platform/RNICA_LOCK_DEFECT_UNREACHABLE_NARRATIVE_REVIEW.md`.

---

## 3. TABLE J — Legacy sections decomposed into the 13 RNICA screens

One row per legacy screen/subsection from the 14 described screenshots.

| # | Legacy screen | Legacy subsection | Target RNICA screen(s) | Owning SNS module(s) | Decomposition note |
|---|---|---|---|---|---|
| 1 | Patient Demographics | Identity / address / phones | 1 Evidence & Intake (read-only) + Facesheet as source | `demographics` | RNICA currently owns these **editably** (`RNICA.jsx:7984-8024`) → duplicate of Facesheet. |
| 1 | Patient Demographics | Race / Ethnicity / Language | 1 Evidence & Intake | `demographics` | A1005/A1010/A1110. Response sets narrower than CMS. |
| 1 | Patient Demographics | Sidebar nav tree | n/a (navigation chrome) | `SIDEBAR_CONFIG` | Legacy nav tree ≠ clinical field; SNS equivalent is `SIDEBAR_CONFIG:200-225` + 13-screen taxonomy. |
| 2 | Vitals / Communications & Other Factors / PCG | Vitals | 3 Pain & Symptom Burden | `vitals` | Currently grouped under `evidenceIntake` (`taxonomy:36-39`). |
| 2 | Vitals / … / PCG | Communications & Other Factors | 7 Caregiver & Support (most), 1 (A0215/A1805), 9 (F2000/F2100/F2200), 8 (med-admin safety) | `demographics.livingSituation`, `demographics.pcg`, `demographics.advancedCarePlanning` | Full decomposition in §14. |
| 2 | Vitals / … / PCG | PCG block | 7 Caregiver & Support | `demographics.pcg` | Currently rendered inside `renderDemographics()` under the `caregiverAssessment` sidebar child (`RNICA.jsx:203, 8030-8123`). |
| 3 | Pain Screening / PAINAD | Pain screening, scales, PAINAD, FLACC | 3 Pain & Symptom Burden | `pain` | Correctly placed. |
| 4 | DME Device / IV Assessment | DME devices | 10 Orders & POC (owner); 5 Functional Status read-only | `safety.dmeItems` via `DmeStatusCard` | DME editable ownership currently sits in the `safety` module (`RNICA.jsx:9461`), i.e. Screen 8 — misplaced relative to target. |
| 4 | DME Device / IV Assessment | IV assessment | 6 Body Systems (or 3 with vitals) | `vitals.ivAssessment.*` | Currently inside `vitals` (`RNICA.jsx:8792-8802`). |
| 5 | PCG / Mobility / ADL | Mobility | 5 Functional Status | `musculoskeletal.mobility.*` | Editable ownership sits in `musculoskeletal` (Screen 6) → misplaced. |
| 5 | PCG / Mobility / ADL | ADL | 5 Functional Status | `musculoskeletal.adl.*` rendered under `performanceStatus` | Presentation already moved (`RNICA.jsx:9003`, `dataSection: "musculoskeletal"`); persistence still in `musculoskeletal`. |
| 6 | Diagnosis / Comorbidities | Primary/secondary diagnosis, comorbidities | 4 Diagnosis & LCD | `diagnoses` | Correctly placed. |
| 7 | KPS-PPS-FAST / LCD Eligibility | Performance scales | 5 Functional Status | `performanceStatus` | Correctly placed. |
| 7 | KPS-PPS-FAST / LCD Eligibility | LCD eligibility | 4 Diagnosis & LCD | `diagnoses.ndsEligibility.*` | Presented as "LCD Supporting Evidence" (`RNICA.jsx:8942-8943`), not "Eligibility Confirmed" — matches directive. |
| 8 | Neuro / Cardiovascular | Neurological / mental / sensory | 6 Body Systems | `neurological` | Correctly placed. |
| 8 | Neuro / Cardiovascular | Cardiovascular | 6 Body Systems | `cardiovascular` | Correctly placed. |
| 9 | Respiratory / GI | Respiratory | 6 Body Systems (+ SFV SOB owned by 3) | `respiratory` | `respiratory.sobSeverity` is flagged `sfv: true` (`RNICA.jsx:9116`) — competing SFV owner with `symptomImpact.shortnessOfBreath`. |
| 9 | Respiratory / GI | GI | 6 Body Systems (+ SFV D-G owned by 3) | `gastrointestinal` | `nausea/vomiting/diarrhea/constipation` flagged `sfv: true` (`:9180-9184`) — competing SFV owner. |
| 10 | GI / Nutrition / Endocrine / GU | Nutrition | 6 Body Systems | `nutrition` | Correctly placed. |
| 10 | GI / Nutrition / Endocrine / GU | Endocrine | 6 Body Systems | `endocrine` | Correctly placed. |
| 10 | GI / Nutrition / Endocrine / GU | Genitourinary | 6 Body Systems | `genitourinary` | Correctly placed. |
| 11 | Skin / MusculoSkeletal / Urinary | Skin / wounds / Braden | 6 Body Systems; Braden summary read-only on 8 | `skin` | Correctly placed; Braden total is not persisted (see §16 C). |
| 11 | Skin / MusculoSkeletal / Urinary | Musculoskeletal | 6 Body Systems (minus ADL/mobility) | `musculoskeletal` | ADL presentation already moved out; mobility has not. |
| 12 | Personal Care / Environmental-Safety | Personal care | 7 Caregiver & Support | `personalCare` | Correctly placed. |
| 12 | Personal Care / Environmental-Safety | Environmental / safety | 8 Safety & Clinical Risk | `safety` | Correctly placed, except DME and Supplies cards which belong to Screen 10. |
| 13 | Bereavement / Referrals / Spiritual | Bereavement | 7 Caregiver & Support | `bereavement` | Correctly placed. |
| 13 | Bereavement / Referrals / Spiritual | Spiritual | 7 Caregiver & Support | `spiritual` | Correctly placed; carries F3000. |
| 13 | Bereavement / Referrals / Spiritual | Referrals | 7 Caregiver & Support | `referrals` | Currently in `evidenceIntake.moduleKeys` (`taxonomy:37`) → relocation required (§17). |
| 14 | Narrative / Admissions Order | Clinical narrative | 13 Finalization | `finalization.clinicalNarrative` | Lock gate still reads `diagnoses.clinicalNarrative` — `CONFLICTING`. |
| 14 | Narrative / Admissions Order | Admissions order | 10 Orders & POC | `admissionsOrder` | Correctly placed. |
| — | (no legacy equivalent) | Imminent-death screening | 8 Safety & Clinical Risk | `imminentDeath` | SNS-specific HOPE J0050 screen; no legacy counterpart described. |
| — | (no legacy equivalent) | SFV module | 3 Pain & Symptom Burden (target) | `sfv` | Currently under `safetyClinicalRisk` (`taxonomy:82`). |
| — | (no legacy equivalent) | Psychosocial screening | 7 Caregiver & Support | `psychosocial` | Correctly placed. |
| — | (no legacy equivalent) | Teaching needs | 7 Caregiver & Support | `teachingNeeds` | Correctly placed. |
| — | (no legacy equivalent) | Infection / immunological | 6 Body Systems | `infection` | Correctly placed. |
| — | (no legacy equivalent) | Compliance / readiness | 11 Compliance & Readiness | none (`crossCutting`) | Backed by `evaluate_finalization_readiness()`. |
| — | (no legacy equivalent) | AI findings | 12 AI Action Center | none (`crossCutting`) | Owns no clinical field. |

---

## 4. TABLE A — Field-level legacy-to-SNS map, organized by target screen

Column key: **LS** legacy section · **LSub** legacy subsection · **Label** ·
**Code** item code · **Class** classification · **LRS** legacy response set ·
**Path** current SNS field path · **Sec** current SNS section · **Scr**
target screen · **Edit** editable authority · **RO** read-only displays ·
**HH** HOPE harvest · **SFV** SFV trigger · **Req** requiredness ·
**Cond** conditional visibility · **Val** validation source · **Pers**
persisted · **Compat** existing-data compatibility · **Status** · **Notes**.

`Pers = JSONB` means the value is stored in the RNICA assessment `form_data`
JSONB document (`backend/app/models/rnica_assessment.py`), which is how every
`SECTION_CONFIGS` path persists; there is no per-field column.
`Compat = additive` means the path already exists today and reading older
records simply yields `undefined`, which every renderer tolerates.

---

### 4.1 SCREEN 1 — Evidence & Intake (target rename: Identity & HOPE Demographics)

```
Frontend: sns-emr-frontend/src/components/RNICA.jsx:7966-8205 (renderDemographics)
Frontend: sns-emr-frontend/src/components/rn-ica/rnicaThirteenScreenTaxonomy.js:33-40
Backend:  backend/app/domain/forms/form_registry.py:341-362 (HOPE_ADMIN_ITEM_CODES)
Exporter: sns-emr-frontend/src/intake/hopeReportMapper.js:554-577
Test:     sns-emr-frontend/src/intake/hopeReportMapper.test.js
```

| LS | LSub | Label | Code | Class | LRS | Path | Sec | Scr | Edit | RO | HH | SFV | Req | Cond | Val | Pers | Compat | Status | Notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Patient Demographics | Identity | First Name | A0500A | FACESHEET HARVEST | free text | `demographics.firstName` | demographics | 1 | RNICA editable (`RNICA.jsx:7984`) | Facesheet Section-1 snapshot | `hopeReportMapper.js:565` via `splitPatientName(patient)` (Facesheet object, **not** `demographics`) | No | `required` attr (`:7984`) | always | frontend only | JSONB | additive | DUPLICATE OF FACESHEET | Exporter already prefers Facesheet; the editable RNICA copy is redundant. |
| Patient Demographics | Identity | Last Name | A0500C | FACESHEET HARVEST | free text | `demographics.lastName` | demographics | 1 | RNICA editable (`:7985`) | Facesheet snapshot | `hopeReportMapper.js:565` (from Facesheet) | No | `required` | always | frontend only | JSONB | additive | DUPLICATE OF FACESHEET | Same as above. |
| Patient Demographics | Identity | Date of Birth | A0900 | FACESHEET HARVEST | date | `demographics.dob` | demographics | 1 | RNICA editable (`:7986`) | Facesheet snapshot | `hopeReportMapper.js:570` (`demographics.dob \|\| patient.dob`) | No | `required` | always | frontend only | JSONB | additive | DUPLICATE OF FACESHEET | Exporter falls back to Facesheet, so divergence is silently resolved in favour of RNICA. |
| Patient Demographics | Identity | Gender | A0810 | FACESHEET HARVEST | Male/Female/Non-binary/Other/Declined | `demographics.gender` | demographics | 1 | RNICA editable (`:7987-7988`) | Facesheet snapshot | `hopeReportMapper.js:495,569` via `SEX_MAP` | No | `required` | always | frontend only | JSONB | additive | DUPLICATE OF FACESHEET | CMS A0810 is *sex*, not gender identity; RNICA's 5-value list includes non-binary/other. Mapping through `SEX_MAP` for unmatched values is `NOT VERIFIED`. |
| Patient Demographics | Identity | MRN | — | FACESHEET HARVEST | system id | NOT FOUND IN REPOSITORY in `demographics` | — | 1 | Facesheet (source) | Facesheet snapshot | not emitted by mapper | No | n/a | always | n/a | Facesheet record | n/a | PRESENT AND CORRECTLY PLACED | MRN is not duplicated into RNICA — correct. |
| Patient Demographics | Identity | Phone | — | FACESHEET HARVEST | tel | `demographics.phone` | demographics | 1 | RNICA editable (`:7989`) | Facesheet snapshot | not emitted | No | optional | always | frontend only | JSONB | additive | DUPLICATE OF FACESHEET | |
| Patient Demographics | Identity | Alternate Phone | — | FACESHEET HARVEST | tel | `demographics.alternatePhone` | demographics | 1 | RNICA editable (`:7990`) | Facesheet snapshot | not emitted | No | optional | always | frontend only | JSONB | additive | DUPLICATE OF FACESHEET | |
| Patient Demographics | Identity | Religion | — | SNS CLINICAL | free text | `demographics.religion` | demographics | 1 | RNICA editable (`:8000`) | — | not emitted | No | optional | always | none | JSONB | additive | PRESENT BUT MISPLACED | Belongs with Spiritual (Screen 7) per clinical ownership; duplicated concept with `spiritual.patientFaith` (`:9526`). |
| Patient Demographics | Identity | Marital Status | — | SNS CLINICAL | Single/Married/Divorced/Widowed/Separated/Domestic Partner | `demographics.maritalStatus` | demographics | 1 | RNICA editable (`:8001-8002`) | — | not emitted | No | optional | always | none | JSONB | additive | PRESENT AND CORRECTLY PLACED | |
| Vitals / Comms & Other Factors | Other Factors | Military Service (Patient/Spouse) | — | SNS CLINICAL | Yes/No/Unknown | `demographics.militaryService` | demographics | 7 | RNICA editable (`:8003-8004`) | — | not emitted | No | optional | always | none | JSONB | additive | PRESENT BUT MISPLACED | **Correction to earlier drafts: this field exists.** It belongs on Caregiver & Support per the directive's decomposition. |
| Patient Demographics | Identity | Race | A1010 | HOPE | legacy set not described in detail | `demographics.race` (array) | demographics | 1 | RNICA editable (`:7992-7993`) | — | `hopeReportMapper.js:572` — `arrayText()` passthrough, **no CMS code lookup** | No | optional | always | none | JSONB | additive | PRESENT BUT RESPONSE SET INCOMPLETE | 6 options: White, Black/African American, Asian, American Indian/Alaska Native, Native Hawaiian/Pacific Islander, Other. CMS HOPE A1010 uses a far larger discrete code set including Asian and NHPI sub-ethnicities; **the exact CMS list is NOT VERIFIED from this repository** and must be taken from CMS HOPE guidance before any change. |
| Patient Demographics | Identity | Ethnicity | A1005 | HOPE | legacy set not described in detail | `demographics.ethnicity` (array) | demographics | 1 | RNICA editable (`:7994-7995`) | — | `hopeReportMapper.js:571` — passthrough, no code lookup | No | optional | always | none | JSONB | additive | PRESENT BUT RESPONSE SET INCOMPLETE | 3 options: Hispanic/Latino, Not Hispanic/Latino, Unknown. Exact CMS A1005 set `NOT VERIFIED`. |
| Patient Demographics | Identity | Preferred Language | A1110A | HOPE | free text / picklist | `demographics.preferredLanguage` | demographics | 1 | RNICA editable (`:7997-7998`) | — | `hopeReportMapper.js:573` (`A. Preferred language`) | No | optional | always | none | JSONB | additive | PRESENT BUT RESPONSE SET INCOMPLETE | 7 fixed options + "Other" with no free-text companion field, so a language outside the list cannot be recorded. Card carries `hopeCode="A1110"` (`:7982`) but the field itself does not. |
| Patient Demographics | Identity | Needs Interpreter | A1110B | HOPE | Yes/No | `demographics.needsInterpreter` | demographics | 1 | RNICA editable (`:7999`) | — | `hopeReportMapper.js:573` (`B. Need interpreter`, `boolCode`) | No | optional | always | none | JSONB | additive | PRESENT AND CORRECTLY PLACED | Satisfies the "interpreter/communication-assistance response" requirement for A1110B only. Communication-assistance beyond interpreter is a separate gap (§15). |
| Vitals / Comms & Other Factors | Admission context | Site of Service | A0215 | HOPE | coded list | `demographics.livingSituation.siteOfService` | demographics | 1 | RNICA editable (`:8128-8140`) | — | `hopeReportMapper.js:491,556` via `SITE_OF_SERVICE_LABELS` + `LEGACY_SITE_OF_SERVICE_TO_CODE` | No | optional | always | code-map fallback (`officialCodeLookup`) | JSONB | legacy-label values remapped by `LEGACY_SITE_OF_SERVICE_TO_CODE` (`:58-75`) | PRESENT AND CORRECTLY PLACED | 10 official codes 01-09 + 99 present. |
| Vitals / Comms & Other Factors | Admission context | Admitted From | A1805 | HOPE | coded list | `demographics.livingSituation.admittedFrom` | demographics | 1 | RNICA editable (`:8141-8154`) | — | `hopeReportMapper.js:492,575` | No | optional | always | code-map fallback | JSONB | legacy remap at `:76-93` | PRESENT AND CORRECTLY PLACED | 11 official codes present (01-08, 10, 11, 99). Code 09 intentionally absent per CMS list. |
| Patient Demographics | Address | Street / City / State / ZIP / County | A0550 (ZIP only) | FACESHEET HARVEST | free text | `demographics.address.street/.city/.state/.zip/.county` | demographics | 1 | RNICA editable (`:8011-8016`) | Facesheet snapshot | ZIP only, `hopeReportMapper.js:566` | No | optional | always | none | JSONB | additive | DUPLICATE OF FACESHEET | Only ZIP is a HOPE item; the rest is duplicated Facesheet data. |
| Patient Demographics | Emergency Contact | Name / Relationship / Phone | — | FACESHEET HARVEST | free text | `demographics.emergencyContact.name/.relationship/.phone` | demographics | 1 | RNICA editable (`:8022-8024`) | Facesheet snapshot | not emitted | No | optional | always | none | JSONB | additive | DUPLICATE OF FACESHEET | |
| Patient Demographics | Payer | Payer Information | A1400 | FACESHEET HARVEST | coded multi-select | Facesheet `patient.primaryPayerType` / `.secondaryPayerType` | (not an RNICA field) | 1 | Facesheet (source) | Screen 1 read-only | `hopeReportMapper.js:511,574` via `FACESHEET_PAYER_TYPE_TO_A1400_CODE` (`:156-171`) | No | n/a | always | code map | Facesheet record | n/a | PRESENT AND CORRECTLY PLACED | Correctly harvested, not duplicated into RNICA. |
| Patient Demographics | Admission | Admission Date | A0220 | FACESHEET HARVEST | date | `patient.socDate` → fallback `admissionsOrder.levelOfCare.effectiveDate` → `completionDate` | admissionsOrder (fallback only) | 1 | Facesheet (source) | Screen 1 read-only | `hopeReportMapper.js:557` | No | n/a | always | none | Facesheet record | n/a | PRESENT AND CORRECTLY PLACED | Triple fallback chain is documented but the fallback to `completionDate` is clinically weak — flagged in §18. |
| Patient Demographics | Facility | Facility Provider Numbers (NPI/CCN/Facility ID) | A0100 | FACESHEET HARVEST | ids | `agency.npi/.ccn/.facilityId` | (agency record) | 1 | Agency config (source) | Screen 1 read-only | `hopeReportMapper.js:482-489,555` | No | n/a | always | none | agency record | n/a | PRESENT AND CORRECTLY PLACED | |
| Patient Demographics | Identity | SSN / Medicare (MBI) | A0600 | FACESHEET HARVEST | ids | `patient.ssn`, `patient.medicareNumber` | (Facesheet) | 1 | Facesheet (source) | Screen 1 read-only | `hopeReportMapper.js:567` | No | n/a | always | none | Facesheet record | n/a | PRESENT AND CORRECTLY PLACED | |
| Patient Demographics | Identity | Medicaid Number | A0700 | FACESHEET HARVEST | id | `patient.medicaidNumber` | (Facesheet) | 1 | Facesheet (source) | Screen 1 read-only | `hopeReportMapper.js:568` | No | n/a | always | none | Facesheet record | n/a | PRESENT AND CORRECTLY PLACED | |
| Patient Demographics | Care team | Attending physician | — | FACESHEET HARVEST | name | `CARE_TEAM_DISPLAY_FIELDS` (`RNICA.jsx:9771-9778`) + `Section1CareTeamGrid` (`:9810`) | (Facesheet) | 1 | Facesheet (source) | Screen 1 read-only grid | not emitted | No | n/a | always | none | Facesheet record | n/a | PRESENT AND CORRECTLY PLACED | Grid exposes Primary RN, LVN, Social Worker, Chaplain, CHHA, Volunteer, Clinical Manager. An explicit *attending physician* key is not in that list — `NOT VERIFIED` whether it is surfaced elsewhere on Screen 1. |
| Patient Demographics | Chart | Chart primary diagnosis | — | DIAGNOSIS SOURCE | ICD-10 | Facesheet chart diagnosis (read-only) vs. RNICA `diagnoses.primaryDiagnosis.*` | diagnoses | 1 (read-only) / 4 (editable) | Screen 4 owns the RNICA-entered value | Screen 1 read-only | via Screen 4 | No | `required` on Screen 4 | always | frontend only | JSONB | additive | PRESENT AND CORRECTLY PLACED | Two distinct concepts — chart dx (Facesheet) vs. RNICA-asserted principal dx — correctly separated. |
| Patient Demographics | Intake evidence | Uploaded records | — | NOT VERIFIED | n/a | NOT FOUND IN REPOSITORY as an RNICA field | — | 1 | — | — | — | No | — | — | — | — | — | NOT FOUND IN REPOSITORY | No RNICA field for uploaded-record attachment was found in `SECTION_CONFIGS` or `renderDemographics()`. Evidence ingestion exists elsewhere (`backend/app/services/evidence/`) but is not an Evidence & Intake form field. |
| Patient Demographics | Intake evidence | Referral source | — | NOT VERIFIED | n/a | NOT FOUND IN REPOSITORY | — | 1 | — | — | — | No | — | — | — | — | — | NOT FOUND IN REPOSITORY | Distinct from A1805 "Admitted From". |
| Patient Demographics | Intake evidence | Hospital documentation available | — | NOT VERIFIED | n/a | NOT FOUND IN REPOSITORY | — | 1 | — | — | — | No | — | — | — | — | — | NOT FOUND IN REPOSITORY | Closest existing data is `diagnoses.recentHospitalizations` (`RNICA.jsx:2071-2074`), which is a count, not a document-availability flag. |
| Patient Demographics | Intake evidence | Available / missing source evidence | — | NOT VERIFIED | n/a | surfaced by RNICA Intelligence rail, not a form field | — | 12 (advisory) | — | AI rail | — | No | — | — | — | — | — | NOT FOUND IN REPOSITORY | Advisory only; AI cannot satisfy a HOPE/SFV field (see §13). |
| Patient Demographics | Visit metadata | Visit / assessment metadata (created, updated, locked) | Z0350 (date only) | AUDIT/SIGNATURE | timestamps | `assessmentMeta.createdAt/.updatedAt/.lockedAt` | (assessment record) | 1 read-only / 13 authoritative | system | Screens 1, 11, 13 | `hopeReportMapper.js:479,642` (Z0350 completion date) | No | n/a | always | server | assessment columns | n/a | PRESENT AND CORRECTLY PLACED | |
| — | — | Interdisciplinary referrals (all) | — | REFERRAL | — | `referrals.*` | referrals | **7, not 1** | RNICA editable | — | not emitted | No | see §17 | always | `evaluate_finalization_readiness` (`referrals.reviewed`) | JSONB | additive | PRESENT BUT MISPLACED | Directive: referrals must not live on Evidence & Intake. Currently `taxonomy:37`. |

---
### 4.2 SCREEN 2 — Patient Story (read-only summaries only)

```
Frontend: sns-emr-frontend/src/components/rn-ica/rnicaThirteenScreenTaxonomy.js:26-33 (crossCutting, moduleKeys: [], railTarget "intelligence")
Frontend: sns-emr-frontend/src/components/rn-ica/patient-story/ (screen implementation)
```

Screen 2 owns **no** editable field. `RNICA_THIRTEEN_SCREENS[0].moduleKeys`
is `[]` and the screen is declared `crossCutting: true` with
`landingModuleKey: "demographics"` — i.e. it is a presentation surface over
data owned elsewhere. That matches the directive exactly. Every row below is
therefore a read-only projection.

| LS | LSub | Label | Code | Class | LRS | Path | Sec | Scr | Edit | RO | HH | SFV | Req | Cond | Val | Pers | Compat | Status | Notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| (cross-cutting) | Story | Why hospice / why now | — | LEGACY DISPLAY ONLY | narrative | projection of `diagnoses.primaryDiagnosis.*` + `diagnoses.diseaseTrajectory` | diagnoses | 2 (read-only) | Screen 4 | Screen 2 | via Screen 4 | No | n/a | always | n/a | JSONB (source) | additive | PRESENT AND CORRECTLY PLACED | No second editable narrative on Screen 2 — verified by empty `moduleKeys`. |
| (cross-cutting) | Story | Recent decline | — | LEGACY DISPLAY ONLY | narrative | `performanceStatus.functionalDeclineNotes` (`RNICA.jsx:8995`) + `DeclineTrackerCard` (`:2715`) | performanceStatus | 2 (read-only) | Screen 5 | Screen 2 | not emitted | No | n/a | always | n/a | JSONB | additive | PRESENT AND CORRECTLY PLACED | |
| (cross-cutting) | Story | Recent hospitalization | — | LEGACY DISPLAY ONLY | count | `diagnoses.recentHospitalizations` (`:2071-2074`), `diagnoses.recentErVisits` (`:2081-2084`), `diagnoses.utilizationNotes` (`:2092-2094`) | diagnoses | 2 (read-only) | Screen 4 | Screen 2 | not emitted | No | optional | always | n/a | JSONB | additive | PRESENT AND CORRECTLY PLACED | |
| (cross-cutting) | Story | Existing symptoms | J2051A-H | LEGACY DISPLAY ONLY | 0-3 | `symptomImpact.*` | symptomImpact | 2 (read-only) | Screen 3 | Screens 2, 11 | via Screen 3 | Source of trigger | n/a | always | n/a | JSONB | additive | PRESENT AND CORRECTLY PLACED | |
| (cross-cutting) | Story | Existing diagnosis context | I0010 | LEGACY DISPLAY ONLY | coded | `diagnoses.*` | diagnoses | 2 (read-only) | Screen 4 | Screen 2 | via Screen 4 | No | n/a | always | n/a | JSONB | additive | PRESENT AND CORRECTLY PLACED | |
| (cross-cutting) | Story | Caregiver context | — | LEGACY DISPLAY ONLY | mixed | `demographics.pcg.*` | demographics | 2 (read-only) | Screen 7 (target) | Screen 2 | not emitted | No | n/a | always | n/a | JSONB | additive | PRESENT AND CORRECTLY PLACED | |
| (cross-cutting) | Story | Living context | A1905/A1910 | LEGACY DISPLAY ONLY | coded | `demographics.livingSituation.*` | demographics | 2 (read-only) | Screen 7 (target) | Screen 2 | `hopeReportMapper.js:576-577` | No | n/a | always | n/a | JSONB | additive | PRESENT AND CORRECTLY PLACED | |
| (cross-cutting) | Story | Known risks | — | LEGACY DISPLAY ONLY | mixed | `safety.fallRiskLevel`, `skin.pressureInjuryRisk`, `bereavement.bereavementRisk` | safety/skin/bereavement | 2 (read-only) | Screens 8, 6, 7 | not emitted | No | n/a | always | n/a | JSONB | additive | PRESENT AND CORRECTLY PLACED | |
| (cross-cutting) | Story | Missing evidence | — | NOT VERIFIED | n/a | RNICA Intelligence rail (`railTarget: "intelligence"`) | none | 2/12 | none (advisory) | Screens 2, 12 | not emitted | No | n/a | always | n/a | not persisted as a field | n/a | PRESENT AND CORRECTLY PLACED | Advisory-only by design. |
| (cross-cutting) | Story | Prior-assessment comparison | — | COMPUTED RESULT | n/a | `DeclineTrackerCard` (`RNICA.jsx:2715`) via `fetchPerformanceHistory` (`:111`) | performanceStatus | 2 (read-only) / 5 | none (derived) | Screens 2, 5 | not emitted | No | n/a | requires prior assessments | server history API | not persisted | n/a | PRESENT AND CORRECTLY PLACED | |
| (cross-cutting) | Story | RNICA Intelligence findings | — | LEGACY DISPLAY ONLY | n/a | Intelligence rail panel | none | 2/12 | none | Screens 2, 12 | not emitted | No | n/a | always | n/a | not persisted | n/a | PRESENT AND CORRECTLY PLACED | |
| (cross-cutting) | Story | Eligibility / prognosis conclusion | — | LEGACY DISPLAY ONLY | — | **must not appear on Screen 2** | — | 4 | Screen 4 only | — | — | No | — | — | — | — | — | PRESENT AND CORRECTLY PLACED | Verified absent: Screen 2 has no modules, so it cannot render `lcdEligibility`. |

---

### 4.3 SCREEN 3 — Pain & Symptom Burden

```
Frontend: RNICA.jsx:8770-8805 (SECTION_CONFIGS.vitals)
Frontend: RNICA.jsx:8807-8878 (SECTION_CONFIGS.pain)
Frontend: RNICA.jsx:8880-8898 (SECTION_CONFIGS.symptomImpact)
Frontend: RNICA.jsx:9391-9418 (SECTION_CONFIGS.sfv)
Frontend: RNICA.jsx:2880-2910 (AnthropometricsAutoBmiCard)
Frontend: RNICA.jsx:150-160  (SYMPTOM_IMPACT_CHECKLIST, SYMPTOM_SEVERITY_LABEL)
Backend:  backend/app/services/hope_phase_b_engine.py:40,136-156,158-181
Backend:  backend/app/api/visits.py:3611-3706,3916-3991
Exporter: sns-emr-frontend/src/intake/hopeReportMapper.js:386-433,610-619
Test:     sns-emr-frontend/src/intake/hopeReportMapper.test.js
```

#### 4.3.1 Vitals & measurements

| LS | LSub | Label | Code | Class | LRS | Path | Sec | Scr | Edit | RO | HH | SFV | Req | Cond | Val | Pers | Compat | Status | Notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Vitals | Vital Signs | Temperature | — | SNS CLINICAL | numeric | `vitals.temperature` | vitals | 3 | RNICA editable (`:8776`) | Screen 6 (infection cross-ref) | not emitted | No | optional | always | none | JSONB | additive | PRESENT AND CORRECTLY PLACED | Duplicated concept: `infection.temperature` (`:9166`) is a second editable temperature — see §16 B. |
| Vitals | Vital Signs | Unit (F/C) | — | SNS CLINICAL | F, C | `vitals.temperatureUnit` | vitals | 3 | RNICA editable (`:8777`) | — | not emitted | No | optional | always | none | JSONB | additive | PRESENT AND CORRECTLY PLACED | |
| Vitals | Vital Signs | Pulse | — | SNS CLINICAL | numeric | `vitals.pulse` | vitals | 3 | RNICA editable (`:8778`) | Screen 6 | not emitted | No | optional | always | none | JSONB | additive | PRESENT AND CORRECTLY PLACED | |
| Vitals | Vital Signs | Pulse Quality | — | SNS CLINICAL | Strong/Weak/Thready/Bounding/Irregular | `vitals.pulseQuality` | vitals | 3 | RNICA editable (`:8779`) | — | not emitted | No | optional | always | none | JSONB | additive | CONFLICTING | A **second** `pulseQuality` exists at `cardiovascular.pulseQuality` (`:9088`) with a *different, 9-value* response set (adds Regular/Tachycardia/Bradycardia/Absent). Two editable owners, two vocabularies. See §16 B. |
| Vitals | Vital Signs | Respirations | — | SNS CLINICAL | numeric | `vitals.respirations` | vitals | 3 | RNICA editable (`:8780`) | Screen 6 | not emitted | No | optional | always | none | JSONB | additive | PRESENT AND CORRECTLY PLACED | Name-collides with `respiratory.respirations` (`:9124`), which is a *pattern* checkbox group, not a rate. Different sections, so no data collision. |
| Vitals | Vital Signs | BP Systolic | — | SNS CLINICAL | numeric | `vitals.bloodPressure.systolic` | vitals | 3 | RNICA editable (`:8781`) | — | not emitted | No | optional | always | none | JSONB | additive | PRESENT AND CORRECTLY PLACED | |
| Vitals | Vital Signs | BP Diastolic | — | SNS CLINICAL | numeric | `vitals.bloodPressure.diastolic` | vitals | 3 | RNICA editable (`:8782`) | — | not emitted | No | optional | always | none | JSONB | additive | PRESENT AND CORRECTLY PLACED | |
| Vitals | Vital Signs | **BP position (sitting/lying/standing)** | — | SNS CLINICAL | positional | NOT FOUND IN REPOSITORY | — | 3 | — | — | — | No | — | — | — | — | — | MISSING FROM SNS | Confirmed by full read of `SECTION_CONFIGS.vitals` (`:8770-8805`) and `AnthropometricsAutoBmiCard` (`:2880-2910`). Nearest related field is `cardiovascular.bpSymptoms` with an "Orthostatic" option (`:9086`), which is a finding, not a measurement position. |
| Vitals | Vital Signs | O2 Saturation % | — | SNS CLINICAL | numeric | `vitals.oxygenSaturation` | vitals | 3 | RNICA editable (`:8783`) | Screen 6 | not emitted | No | optional | always | none | JSONB | additive | CONFLICTING | Second editable saturation at `respiratory.oxygenTherapy.satOnO2` (`:9135`). |
| Vitals | Vital Signs | On Room Air | — | SNS CLINICAL | boolean | `vitals.oxygenSaturationOnRA` | vitals | 3 | RNICA editable (`:8784`) | — | not emitted | No | optional | always | none | JSONB | additive | CONFLICTING | Second editable room-air flag at `respiratory.oxygenTherapy.onRoomAir` (`:9134`). |
| Vitals | Anthropometrics | Height (in) | — | SNS CLINICAL | numeric | `vitals.height` | vitals | 3 | RNICA editable (`:2903`) | Screen 6 nutrition ref (`:2944`) | not emitted | No | optional | always | none | JSONB | additive | PRESENT AND CORRECTLY PLACED | |
| Vitals | Anthropometrics | Weight (lbs) | — | SNS CLINICAL | numeric | `vitals.weight` | vitals | 3 | RNICA editable (`:2904`) | Screen 6 nutrition ref (`:2945`); `WeightLossAutoCalcCard` input | not emitted | No | optional | always | none | JSONB | additive | PRESENT AND CORRECTLY PLACED | |
| Vitals | Anthropometrics | BMI (auto-calculated) | — | COMPUTED RESULT | numeric | `vitals.bmi` | vitals | 3 | auto-written by `AnthropometricsAutoBmiCard` (`:2883-2895`), field remains user-editable | Screen 6 nutrition ref (`:2946`) | not emitted | No | optional | requires height+weight | client-side effect | JSONB | additive | PRESENT AND CORRECTLY PLACED | Single persisted BMI; the Screen 6 nutrition reference reads the same path and does not persist its own copy — correct per §16 C. |
| Vitals | Anthropometrics | **MAC (Mid-Arm Circumference)** | — | SNS CLINICAL | numeric | `vitals.mac` | vitals | 3 | RNICA editable (`RNICA.jsx:2906`) | Screen 6 nutrition ref (`:2947`) | not emitted | No | optional | always | none | JSONB | additive | PRESENT BUT NOT HARVESTED | **Correction to earlier drafts: MAC exists.** It is rendered inside `AnthropometricsAutoBmiCard`, which is why a `SECTION_CONFIGS`-only search missed it. It is not exported to HOPE (no CMS item code applies) and not used by any LCD criterion visible in this pass. |
| Vitals | Anthropometrics | Serum albumin (reference) | — | COMPUTED RESULT | numeric | read-only mirror of `diagnoses.ndsEligibility.criteriaFacts[disease].serum_albumin` | diagnoses | 6 (nutrition ref) | Screen 4 owns | Screen 6 (`:2928,2948`) | not emitted | No | n/a | requires detected LCD disease | LCD engine | JSONB | additive | PRESENT AND CORRECTLY PLACED | Read-only cross-reference; no second persisted copy. |
| Vitals | Vital Signs | **Unable-to-assess state** | — | SNS CLINICAL | boolean/flag | NOT FOUND IN REPOSITORY for vitals | — | 3 | — | — | — | No | — | — | — | — | — | MISSING FROM SNS | Verified absent from `SECTION_CONFIGS.vitals`. An "unable to determine" *value* exists on specific pain items (`pain.verbalizesPain` value `3`, `pain.uncomfortableBecauseOfPain` value `9`) but there is no per-vital or per-section unable-to-assess state. |
| DME Device / IV Assessment | IV | Patient has IV access | — | SNS CLINICAL | boolean | `vitals.ivAssessment.hasIV` | vitals | 6 (target) | RNICA editable (`:8793`) | — | not emitted | No | optional | always | none | JSONB | additive | PRESENT BUT MISPLACED | IV assessment is a body-system/device finding; it currently rides along with vitals. |
| DME Device / IV Assessment | IV | IV Type | — | SNS CLINICAL | Peripheral/Central/PICC/Port | `vitals.ivAssessment.type` | vitals | 6 | RNICA editable (`:8794`) | — | not emitted | No | optional | always | none | JSONB | additive | PRESENT BUT MISPLACED | |
| DME Device / IV Assessment | IV | Size (gauge) | — | SNS CLINICAL | free text | `vitals.ivAssessment.size` | vitals | 6 | RNICA editable (`:8795`) | — | not emitted | No | optional | always | none | JSONB | additive | PRESENT BUT MISPLACED | |
| DME Device / IV Assessment | IV | Site/Location | — | SNS CLINICAL | free text | `vitals.ivAssessment.site` | vitals | 6 | RNICA editable (`:8796`) | — | not emitted | No | optional | always | none | JSONB | additive | PRESENT BUT MISPLACED | |
| DME Device / IV Assessment | IV | Dressing Type | — | SNS CLINICAL | Tegaderm/Gauze/Other | `vitals.ivAssessment.dressingType` | vitals | 6 | RNICA editable (`:8797`) | — | not emitted | No | optional | always | none | JSONB | additive | PRESENT BUT MISPLACED | |
| DME Device / IV Assessment | IV | Insertion Date | — | SNS CLINICAL | date | `vitals.ivAssessment.insertionDate` | vitals | 6 | RNICA editable (`:8798`) | — | not emitted | No | optional | always | none | JSONB | additive | PRESENT BUT MISPLACED | |
| DME Device / IV Assessment | IV | Last Change Date | — | SNS CLINICAL | date | `vitals.ivAssessment.lastChangeDate` | vitals | 6 | RNICA editable (`:8799`) | — | not emitted | No | optional | always | none | JSONB | additive | PRESENT BUT MISPLACED | |
| DME Device / IV Assessment | IV | Condition | — | SNS CLINICAL | Patent/Infiltrated/Phlebitis/Occluded | `vitals.ivAssessment.condition` | vitals | 6 | RNICA editable (`:8800`) | — | not emitted | No | optional | always | none | JSONB | additive | PRESENT BUT MISPLACED | |
| DME Device / IV Assessment | IV | IV Notes | — | SNS CLINICAL | free text | `vitals.ivAssessment.notes` | vitals | 6 | RNICA editable (`:8801`) | — | not emitted | No | optional | always | none | JSONB | additive | PRESENT BUT MISPLACED | |

#### 4.3.2 Pain

| LS | LSub | Label | Code | Class | LRS | Path | Sec | Scr | Edit | RO | HH | SFV | Req | Cond | Val | Pers | Compat | Status | Notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Pain Screening / PAINAD | Screening | A. Was the patient screened for pain? | J0900A | HOPE | 0 No (skip to J0905) / 1 Yes | `pain.screenedForPain` | pain | 3 | RNICA editable (`:8813-8815`) | Screen 11 | `hopeReportMapper.js:499,610` via `painScreeningResponse()` (`:190-266`) | No | optional (not `required`) | always | mapper flags incomplete → `legacyReviewItems` (`:518`) | JSONB | additive | PRESENT AND CORRECTLY PLACED | |
| Pain Screening / PAINAD | Screening | B. Date of first screening for pain | J0900B | HOPE | date | `pain.screeningDate` | pain | 3 | RNICA editable (`:8816`) | — | `hopeReportMapper.js:610` | No | optional | always | none | JSONB | additive | PRESENT AND CORRECTLY PLACED | |
| Pain Screening / PAINAD | Screening | C. Patient's pain severity was | J0900C | HOPE | 0 None/1 Mild/2 Moderate/3 Severe/9 Not rated | `pain.painSeverityCategory` | pain | 3 | RNICA editable (`:8817-8819`) | Screen 11 | `hopeReportMapper.js:499,610` | No | optional | skipped when J0900A=0 (`:238`) | mapper | JSONB | additive | PRESENT AND CORRECTLY PLACED | Mapper explicitly emits "Skipped — not screened (J0905)" when A=0 — correct CMS skip logic. |
| Pain Screening / PAINAD | Screening | D. Type of standardized pain tool used | J0900D | HOPE | 1 Numeric/2 Verbal descriptor/3 Patient visual/4 Staff observation/9 None | `pain.standardizedPainToolType` | pain | 3 | RNICA editable (`:8820-8822`) | — | `hopeReportMapper.js:499,610` | No | optional | skipped when J0900A=0 | mapper | JSONB | additive | PRESENT AND CORRECTLY PLACED | |
| Pain Screening / PAINAD | Screening | Can the patient verbalize pain? | — | SNS CLINICAL | 0 No/1 Yes reliably/2 Sometimes/3 Unable to determine | `pain.verbalizesPain` | pain | 3 | RNICA editable (`:8823-8825`) | — | not emitted | No | optional | always | none | JSONB | additive | PRESENT AND CORRECTLY PLACED | Label explicitly says "not a HOPE response" — drives scale selection (numeric vs PAINAD vs FLACC). |
| Pain Screening / PAINAD | Screening | Is the patient uncomfortable because of pain? | — | SNS CLINICAL | 0 No/1 Yes/9 Unable to determine | `pain.uncomfortableBecauseOfPain` | pain | 3 | RNICA editable (`:8826-8828`) | — | not emitted | No | optional | always | none | JSONB | additive | PRESENT AND CORRECTLY PLACED | Legacy "current discomfort due to pain". |
| Pain Screening / PAINAD | Screening | Neuropathic pain (burning/tingling/pins-and-needles/hypersensitivity)? | J0915 | HOPE | 0 No / 1 Yes | `pain.neuropathicPain` | pain | 3 | RNICA editable (`:8829-8831`) | Screen 11 | `hopeReportMapper.js:500,613`; tracked independently of J0900 (`:519-521`) | No | optional | always | mapper `neuropathicPainIncomplete` (`:501`) | JSONB | additive | PRESENT AND CORRECTLY PLACED | |
| Pain Screening / PAINAD | Assessment tool | Pain scale selected | — | SNS CLINICAL | `["Numeric (0-10)"]` | `pain.assessmentTool` | pain | 3 | RNICA editable (`:8836`) | — | not emitted | No | optional | always | none | JSONB | additive | PRESENT BUT RESPONSE SET INCOMPLETE | Single-option select. PAINAD and FLACC are rendered as separate cards (`:8854,:8863`) but cannot be *selected* here, so "nurse selection" of the tool described in the section subtitle (`:8809`) is not actually expressible in this field. |
| Pain Screening / PAINAD | Assessment tool | Current intensity | — | SNS CLINICAL | 0-10 numeric | `pain.painIntensity.current` | pain | 3 | RNICA editable (`:8837`) | Screen 2 | `hopeReportMapper.js:611` (feeds J0905 Pain Active Problem derivation) | No | optional | always | none | JSONB | additive | PRESENT AND CORRECTLY PLACED | |
| Pain Screening / PAINAD | Assessment tool | Worst in 24 hours | — | SNS CLINICAL | 0-10 | `pain.painIntensity.worst` | pain | 3 | RNICA editable (`:8838`) | — | not emitted | No | optional | always | none | JSONB | additive | PRESENT AND CORRECTLY PLACED | Legacy "recent pain". |
| Pain Screening / PAINAD | Assessment tool | Best in 24 hours | — | SNS CLINICAL | 0-10 | `pain.painIntensity.best` | pain | 3 | RNICA editable (`:8839`) | — | not emitted | No | optional | always | none | JSONB | additive | PRESENT AND CORRECTLY PLACED | |
| Pain Screening / PAINAD | Assessment tool | Acceptable level | — | SNS CLINICAL | 0-10 | `pain.painIntensity.acceptable` | pain | 3 | RNICA editable (`:8840`) | — | not emitted | No | optional | always | none | JSONB | additive | PRESENT AND CORRECTLY PLACED | |
| Pain Screening / PAINAD | Assessment tool | Comprehensive pain assessment completed | J0910A | HOPE | boolean | `pain.comprehensiveAssessmentCompleted` | pain | 3 | RNICA editable (`:8841`) | — | `hopeReportMapper.js:612` | No | optional | always | none | JSONB | additive | PRESENT AND CORRECTLY PLACED | J0910 is in `HOPE_SYMPTOM_ITEM_CODES`? **No** — `form_registry.py:382` lists J0910, so yes, declared. |
| Pain Screening / PAINAD | Assessment tool | Comprehensive pain assessment date | J0910B | HOPE | date | `pain.comprehensiveAssessmentDate` | pain | 3 | RNICA editable (`:8842`) | — | `hopeReportMapper.js:612` | No | optional | always | none | JSONB | additive | PRESENT AND CORRECTLY PLACED | |
| Pain Screening / PAINAD | Characteristics | Pain location | — | SNS CLINICAL | 8 options (Head…Generalized) | `pain.painLocation` | pain | 3 | RNICA editable (`:8847`) | — | feeds J0905 derivation (`:611`) | No | optional | always | none | JSONB | additive | PRESENT AND CORRECTLY PLACED | |
| Pain Screening / PAINAD | Characteristics | Pain character | — | SNS CLINICAL | 9 options (Sharp…Pressure) | `pain.painCharacter` | pain | 3 | RNICA editable (`:8848`) | — | not emitted | No | optional | always | none | JSONB | additive | PRESENT AND CORRECTLY PLACED | |
| Pain Screening / PAINAD | Characteristics | Aggravating factors | — | SNS CLINICAL | 7 options | `pain.aggravatingFactors` | pain | 3 | RNICA editable (`:8849`) | — | not emitted | No | optional | always | none | JSONB | additive | PRESENT AND CORRECTLY PLACED | Legacy "pain impact". |
| Pain Screening / PAINAD | Characteristics | Relieving factors | — | SNS CLINICAL | 7 options | `pain.relievingFactors` | pain | 3 | RNICA editable (`:8850`) | — | not emitted | No | optional | always | none | JSONB | additive | PRESENT AND CORRECTLY PLACED | |
| Pain Screening / PAINAD | FLACC | Face | — | SNS CLINICAL | 0/1/2 | `pain.flacc.face` | pain | 3 | RNICA editable (`:8855`) | — | not emitted | No | optional | card always rendered | none | JSONB | additive | PRESENT BUT NOT WIRED | Card title says "Pediatric / child" but there is no conditional visibility rule binding it to `verbalizesPain` or age; it renders unconditionally. |
| Pain Screening / PAINAD | FLACC | Legs | — | SNS CLINICAL | 0/1/2 | `pain.flacc.legs` | pain | 3 | RNICA editable (`:8856`) | — | not emitted | No | optional | card always rendered | none | JSONB | additive | PRESENT BUT NOT WIRED | |
| Pain Screening / PAINAD | FLACC | Activity | — | SNS CLINICAL | 0/1/2 | `pain.flacc.activity` | pain | 3 | RNICA editable (`:8857`) | — | not emitted | No | optional | card always rendered | none | JSONB | additive | PRESENT BUT NOT WIRED | |
| Pain Screening / PAINAD | FLACC | Cry | — | SNS CLINICAL | 0/1/2 | `pain.flacc.cry` | pain | 3 | RNICA editable (`:8858`) | — | not emitted | No | optional | card always rendered | none | JSONB | additive | PRESENT BUT NOT WIRED | |
| Pain Screening / PAINAD | FLACC | Consolability | — | SNS CLINICAL | 0/1/2 | `pain.flacc.consolability` | pain | 3 | RNICA editable (`:8859`) | — | not emitted | No | optional | card always rendered | none | JSONB | additive | PRESENT BUT NOT WIRED | |
| Pain Screening / PAINAD | FLACC | **FLACC total score** | — | COMPUTED RESULT | 0-10 | NOT FOUND IN REPOSITORY | — | 3 | — | — | — | No | — | — | — | — | — | MISSING FROM SNS | No total is computed or persisted for FLACC. |
| Pain Screening / PAINAD | PAINAD | Breathing | — | SNS CLINICAL | 0/1/2 | `pain.painad.breathing` | pain | 3 | RNICA editable (`:8864`) | — | not emitted | No | optional | card always rendered | none | JSONB | additive | PRESENT BUT NOT WIRED | Same unconditional-render issue as FLACC. |
| Pain Screening / PAINAD | PAINAD | Vocalization | — | SNS CLINICAL | 0/1/2 | `pain.painad.vocalization` | pain | 3 | RNICA editable (`:8865`) | — | not emitted | No | optional | card always rendered | none | JSONB | additive | PRESENT BUT NOT WIRED | |
| Pain Screening / PAINAD | PAINAD | Facial expression | — | SNS CLINICAL | 0/1/2 | `pain.painad.facialExpression` | pain | 3 | RNICA editable (`:8866`) | — | not emitted | No | optional | card always rendered | none | JSONB | additive | PRESENT BUT NOT WIRED | |
| Pain Screening / PAINAD | PAINAD | Body language | — | SNS CLINICAL | 0/1/2 | `pain.painad.bodyLanguage` | pain | 3 | RNICA editable (`:8867`) | — | not emitted | No | optional | card always rendered | none | JSONB | additive | PRESENT BUT NOT WIRED | |
| Pain Screening / PAINAD | PAINAD | Consolability | — | SNS CLINICAL | 0/1/2 | `pain.painad.consolability` | pain | 3 | RNICA editable (`:8868`) | — | not emitted | No | optional | card always rendered | none | JSONB | additive | PRESENT BUT NOT WIRED | |
| Pain Screening / PAINAD | PAINAD | **PAINAD total score** | — | COMPUTED RESULT | 0-10 | NOT FOUND IN REPOSITORY | — | 3 | — | — | — | No | — | — | — | — | — | MISSING FROM SNS | No total computed or persisted. |
| Pain Screening / PAINAD | Management | Non-Pharmacological Interventions | — | SNS CLINICAL | 9 options | `pain.nonPharmInterventions` | pain | 3 | RNICA editable (`:8873`) | — | not emitted | No | optional | always | none | JSONB | additive | PRESENT AND CORRECTLY PLACED | Legacy "pain treatment". |
| Pain Screening / PAINAD | Management | Pain Management Plan | — | SNS CLINICAL | free text | `pain.painManagementPlan` | pain | 3 | RNICA editable (`:8874`) | — | feeds J0905 derivation (`:611`) | No | optional | always | none | JSONB | additive | PRESENT AND CORRECTLY PLACED | |
| Pain Screening / PAINAD | Management | **Intervention / reassessment (post-intervention re-score)** | — | SNS CLINICAL | numeric + time | NOT FOUND IN REPOSITORY | — | 3 | — | — | — | No | — | — | — | — | — | MISSING FROM SNS | No reassessment-after-intervention field exists in `SECTION_CONFIGS.pain`. |
| Pain Screening / PAINAD | Derived | Pain Active Problem | J0905 | HOPE | Yes/No | derived from `pain.painIntensity.current \|\| pain.painManagementPlan \|\| pain.painLocation` | pain | 3 | none (derived) | Screen 11 | `hopeReportMapper.js:611` | No | n/a | always | mapper | not persisted | n/a | PRESENT BUT NOT WIRED | J0905 has **no dedicated input**; it is inferred. Declared in `form_registry.py:381`. A clinician cannot answer J0905 "No" while pain data is present. |

#### 4.3.3 Symptom Impact (J2051 A-H) and SFV

| LS | LSub | Label | Code | Class | LRS | Path | Sec | Scr | Edit | RO | HH | SFV | Req | Cond | Val | Pers | Compat | Status | Notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Pain / Symptom | Symptom Impact | A. Pain | J2051A | HOPE AND SFV | 0 None/1 Mild/2 Moderate/3 Severe | `symptomImpact.pain` | symptomImpact | 3 | RNICA editable (`:8886`, `sfv: true`) | Screens 2, 11 | `hopeReportMapper.js:617` via `symptomEntries()` (`:385-392`) | **Yes** — `_is_moderate_or_severe()` (`hope_phase_b_engine.py:140-142`) | optional | always | `getSfvStatus()` (`hopeReportMapper.js:400-433`) | JSONB | additive | PRESENT AND CORRECTLY PLACED | |
| Pain / Symptom | Symptom Impact | B. Shortness of Breath | J2051B | HOPE AND SFV | 0-3 | `symptomImpact.shortnessOfBreath` | symptomImpact | 3 | RNICA editable (`:8887`) | Screen 6 respiratory | `hopeReportMapper.js:617` | **Yes** | optional | always | `getSfvStatus()` | JSONB | additive | CONFLICTING | Competing editable owner: `respiratory.sobSeverity` (`:9116`) is also flagged `sfv: true` with a *different* vocabulary (None/Mild/Moderate/Severe/**At rest**). See §16 B. |
| Pain / Symptom | Symptom Impact | C. Anxiety | J2051C | HOPE AND SFV | 0-3 | `symptomImpact.anxiety` | symptomImpact | 3 | RNICA editable (`:8888`) | Screen 6 neuro | `hopeReportMapper.js:617` | **Yes** | optional | always | `getSfvStatus()` | JSONB | additive | CONFLICTING | `neurological.symptomsDemeanor` includes an "Anxiety" checkbox (`:9020`) — a second, ungraded anxiety input. Cross-write mappings exist (`structured_findings.py:377-380`) that write `symptomImpact.anxiety` from neuro evidence. |
| Pain / Symptom | Symptom Impact | D. Nausea | J2051D | HOPE AND SFV | 0-3 | `symptomImpact.nausea` | symptomImpact | 3 | RNICA editable (`:8889`) | Screen 6 GI | `hopeReportMapper.js:617` | **Yes** | optional | always | `getSfvStatus()` | JSONB | additive | CONFLICTING | Competing owner `gastrointestinal.nausea` (`:9180`, `sfv: true`, vocabulary None/Mild/Moderate/Severe). |
| Pain / Symptom | Symptom Impact | E. Vomiting | J2051E | HOPE AND SFV | 0-3 | `symptomImpact.vomiting` | symptomImpact | 3 | RNICA editable (`:8890`) | Screen 6 GI | `hopeReportMapper.js:617` | **Yes** | optional | always | `getSfvStatus()` | JSONB | additive | CONFLICTING | Competing owner `gastrointestinal.vomiting` (`:9181`). |
| Pain / Symptom | Symptom Impact | F. Diarrhea | J2051F | HOPE AND SFV | 0-3 | `symptomImpact.diarrhea` | symptomImpact | 3 | RNICA editable (`:8891`) | Screen 6 GI | `hopeReportMapper.js:617` | **Yes** | optional | always | `getSfvStatus()` | JSONB | additive | CONFLICTING | Competing owner `gastrointestinal.diarrhea` (`:9183`). |
| Pain / Symptom | Symptom Impact | G. Constipation | J2051G | HOPE AND SFV | 0-3 | `symptomImpact.constipation` | symptomImpact | 3 | RNICA editable (`:8892`) | Screen 6 GI | `hopeReportMapper.js:617` | **Yes** | optional | always | `getSfvStatus()` | JSONB | additive | CONFLICTING | Competing owner `gastrointestinal.constipation` (`:9184`), which is additionally auto-suggested by `ConstipationAutoAssessCard` (`:6113-6140`) writing `constipation` in the **gastrointestinal** section. |
| Pain / Symptom | Symptom Impact | H. Agitation | J2051H | HOPE AND SFV | 0-3 | `symptomImpact.agitation` | symptomImpact | 3 | RNICA editable (`:8893`) | Screen 6 neuro | `hopeReportMapper.js:617` | **Yes** | optional | always | `getSfvStatus()` | JSONB | additive | CONFLICTING | `neurological.symptomsDemeanor` "Agitation" checkbox (`:9020`); cross-write at `structured_findings.py:381-384`. |
| Pain / Symptom | Symptom Impact | Assessment Date | J2050B | HOPE AND SFV | date | `symptomImpact.assessmentDate` | symptomImpact | 3 | RNICA editable (`:8894`) | Screen 11 | `hopeReportMapper.js:403,616` | Used as SFV clock start | optional | always | `getSfvStatus()` | JSONB | additive | PRESENT AND CORRECTLY PLACED | |
| Pain / Symptom | SFV | Symptom Impact Screening Completed | J2050A | HOPE AND SFV | boolean | `sfv.symptomImpactScreeningCompleted` | sfv | 3 (target) / 8 (current) | RNICA editable (`:9396`) | Screen 11 | `hopeReportMapper.js:616` | Screening flag | optional | hidden in UPDATE assessments (`RNICA.jsx:251-252`) | `getSfvStatus()` | JSONB | additive | PRESENT BUT MISPLACED | `taxonomy:82` puts `sfv` under `safetyClinicalRisk`. |
| Pain / Symptom | SFV | Screening Date | J2050B | HOPE AND SFV | date | `sfv.symptomImpactScreeningDate` | sfv | 3 | RNICA editable (`:9397`) | Screen 11 | `hopeReportMapper.js:403,616` | Drives due-date `addDays(screeningDate, 2)` (`:408`) | optional | as above | `getSfvStatus()` | JSONB | additive | PRESENT BUT MISPLACED | |
| Pain / Symptom | SFV | In-Person SFV Completed | J2052A | HOPE AND SFV | boolean | `sfv.inPersonSfvCompleted` | sfv | 3 | RNICA editable (`:9398`) | Screen 11 | `hopeReportMapper.js:409,618` | Completion evidence | optional | as above | `getSfvStatus()` | JSONB | additive | PRESENT AND CORRECTLY PLACED | `getSfvStatus()` only reports complete when this flag is true — it does **not** infer completion from symptom presence, satisfying the directive's rule. |
| Pain / Symptom | SFV | SFV Date | J2052B | HOPE AND SFV | date | `sfv.sfvDate` | sfv | 3 | RNICA editable (`:9399`) | Screen 11 | `hopeReportMapper.js:618` | Completion evidence | optional | as above | `getSfvStatus()` | JSONB | additive | PRESENT AND CORRECTLY PLACED | |
| Pain / Symptom | SFV | Reason SFV not completed | — | SFV | free text | `sfv.reasonNotCompleted` | sfv | 3 | RNICA editable (`:9400`) | Screen 11 | not emitted | No | optional | as above | none | JSONB | additive | PRESENT BUT NOT HARVESTED | |
| Pain / Symptom | SFV | **In-person requirement statement** | J2052 | SFV | text | `getSfvStatus().note` (`hopeReportMapper.js:415-419`) | none | 3 | none (derived) | Screens 3, 11 | computed | Derived | n/a | when a J2051 item is Moderate/Severe | mapper | not persisted | n/a | PRESENT AND CORRECTLY PLACED | "Any Moderate or Severe J2051 symptom requires an in-person SFV within 2 calendar days". |
| Pain / Symptom | SFV | **SFV due date / window** | — | COMPUTED RESULT | date | `getSfvStatus().dueDate` (`:408`) | none | 3 | none (derived) | Screens 3, 11 | computed | Derived | n/a | when required | mapper | not persisted | n/a | PRESENT AND CORRECTLY PLACED | 2-calendar-day window, computed client-side only. Backend has no equivalent SFV due-date computation for the RNICA form (backend SFV/HUV tasks derive from *visit* notes, `visits.py:3916-3991`). |
| Pain / Symptom | SFV | A. Pain at SFV | J2053A | HOPE AND SFV | 0-3 | `sfv.symptomImpactAtSfv.pain` | sfv | 3 | RNICA editable (`:9403`) | — | `hopeReportMapper.js:619` | Follow-up value | optional | as above | none | JSONB | additive | PRESENT AND CORRECTLY PLACED | |
| Pain / Symptom | SFV | B. Shortness of Breath at SFV | J2053B | HOPE AND SFV | 0-3 | `sfv.symptomImpactAtSfv.shortnessOfBreath` | sfv | 3 | RNICA editable (`:9404`) | — | `hopeReportMapper.js:619` | Follow-up value | optional | as above | none | JSONB | additive | PRESENT AND CORRECTLY PLACED | |
| Pain / Symptom | SFV | C. Anxiety at SFV | J2053C | HOPE AND SFV | 0-3 | `sfv.symptomImpactAtSfv.anxiety` | sfv | 3 | RNICA editable (`:9405`) | — | `hopeReportMapper.js:619` | Follow-up value | optional | as above | none | JSONB | additive | PRESENT AND CORRECTLY PLACED | |
| Pain / Symptom | SFV | D. Nausea at SFV | J2053D | HOPE AND SFV | 0-3 | `sfv.symptomImpactAtSfv.nausea` | sfv | 3 | RNICA editable (`:9406`) | — | `hopeReportMapper.js:619` | Follow-up value | optional | as above | none | JSONB | additive | PRESENT AND CORRECTLY PLACED | |
| Pain / Symptom | SFV | E. Vomiting at SFV | J2053E | HOPE AND SFV | 0-3 | `sfv.symptomImpactAtSfv.vomiting` | sfv | 3 | RNICA editable (`:9407`) | — | `hopeReportMapper.js:619` | Follow-up value | optional | as above | none | JSONB | additive | PRESENT AND CORRECTLY PLACED | |
| Pain / Symptom | SFV | F. Diarrhea at SFV | J2053F | HOPE AND SFV | 0-3 | `sfv.symptomImpactAtSfv.diarrhea` | sfv | 3 | RNICA editable (`:9408`) | — | `hopeReportMapper.js:619` | Follow-up value | optional | as above | none | JSONB | additive | PRESENT AND CORRECTLY PLACED | |
| Pain / Symptom | SFV | G. Constipation at SFV | J2053G | HOPE AND SFV | 0-3 | `sfv.symptomImpactAtSfv.constipation` | sfv | 3 | RNICA editable (`:9409`) | — | `hopeReportMapper.js:619` | Follow-up value | optional | as above | none | JSONB | additive | PRESENT AND CORRECTLY PLACED | |
| Pain / Symptom | SFV | H. Agitation at SFV | J2053H | HOPE AND SFV | 0-3 | `sfv.symptomImpactAtSfv.agitation` | sfv | 3 | RNICA editable (`:9410`) | — | `hopeReportMapper.js:619` | Follow-up value | optional | as above | none | JSONB | additive | PRESENT AND CORRECTLY PLACED | |
| Pain / Symptom | SFV | Triggered Symptoms | — | SFV | 8 checkboxes | `sfv.triggeredSymptoms` | sfv | 3 | RNICA editable (`:9413`) | — | not emitted | Manual restatement of a derived value | optional | as above | none | JSONB | additive | CONFLICTING | This is a hand-entered duplicate of `getSfvStatus().triggeredSymptoms` (`hopeReportMapper.js:404-406`), which is derived from J2051. Two competing representations of the same trigger state. |
| Pain / Symptom | SFV | Findings | — | SFV | free text | `sfv.findings` | sfv | 3 | RNICA editable (`:9414`) | — | not emitted | No | optional | as above | none | JSONB | additive | PRESENT BUT NOT HARVESTED | |
| Pain / Symptom | SFV | Notes | — | SFV | free text | `sfv.notes` | sfv | 3 | RNICA editable (`:9415`) | — | not emitted | No | optional | as above | none | JSONB | additive | PRESENT BUT NOT HARVESTED | |
| Respiratory | SOB | Treatment Declined (when applicable) | — | SFV | boolean | `respiratory.treatmentDeclined` | respiratory | 3 (SFV context) / 6 | RNICA editable (`:9117`) | — | not emitted | No | optional | always | none | JSONB | additive | PRESENT BUT NOT HARVESTED | The only "treatment-declined" response found in the repository. No equivalent exists for pain, anxiety, nausea, vomiting, diarrhea, constipation or agitation. |
| (backend trigger) | SFV engine | Moderate/Severe trigger evaluation | J2051/J2052 | SFV | MODERATE, SEVERE | `hope_phase_b_engine.py:40` `MODERATE_OR_SEVERE`, `:140-142` `_is_moderate_or_severe()` | n/a | 3/11 | system | Screens 3, 11 | n/a | **authoritative backend trigger** | n/a | on visit-note ingestion | backend | task records | n/a | PRESENT AND CORRECTLY PLACED | Note: this backend path is driven by **visit notes** (`visits.py:3611-3706` `_extract_j2051_impacts_from_notes`, `:3916-3991`), not directly by the RNICA `symptomImpact` section. The RNICA-side trigger is client-side `getSfvStatus()`. Two independent trigger computations exist. |
| (backend trigger) | HUV | HUV1 window (days 6-15, RN only) | — | SFV | n/a | `validate_huv_visit_completion()` (`hope_phase_b_engine.py:158-181`) | n/a | 11 | system | Screen 11 | n/a | Related workflow | n/a | HUV task | backend | task records | n/a | PRESENT AND CORRECTLY PLACED | |
| (backend trigger) | HUV | HUV2 window (days 16-30, RN only) | — | SFV | n/a | `validate_huv_visit_completion()` (`:176-178`) | n/a | 11 | system | Screen 11 | n/a | Related workflow | n/a | HUV task | backend | task records | n/a | PRESENT AND CORRECTLY PLACED | |

---
### 4.4 SCREEN 4 — Diagnosis & LCD

```
Frontend: RNICA.jsx:8900-8946 (SECTION_CONFIGS.diagnoses)
Frontend: RNICA.jsx:1601-1985 (LcdEligibilityCard)
Frontend: RNICA.jsx:1987-2000 (LcdSupportingEvidenceCard)
Frontend: RNICA.jsx:2176-2320 (SecondaryDiagnosesCard)
Frontend: RNICA.jsx:2496-2563 (HOPE_COMORBIDITY_CATEGORIES, categorizeIcd10)
Frontend: RNICA.jsx:2565-2688 (HopeComorbiditiesCard)
Backend:  backend/app/domain/forms/form_registry.py:371-376 (HOPE_DIAGNOSIS_ITEM_CODES)
Backend:  backend/app/services/rnica_finalization_service.py:120-135 (narrative + lcdBaseline gates)
Exporter: sns-emr-frontend/src/intake/hopeReportMapper.js:123-136,435-455,531-552,598-609
```

| LS | LSub | Label | Code | Class | LRS | Path | Sec | Scr | Edit | RO | HH | SFV | Req | Cond | Val | Pers | Compat | Status | Notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Diagnosis / Comorbidities | Primary | ICD-10 Code | — | DIAGNOSIS SOURCE | ICD-10 | `diagnoses.primaryDiagnosis.icd10` | diagnoses | 4 | RNICA editable (`:8906`) | Screens 1, 2 | `hopeReportMapper.js:503,598` | No | **required** | always | frontend `required` | JSONB | additive | PRESENT AND CORRECTLY PLACED | Also drives LCD auto-detection (`:1602,1628`) and comorbidity auto-categorization (`:2570`). |
| Diagnosis / Comorbidities | Primary | Description | — | DIAGNOSIS SOURCE | free text | `diagnoses.primaryDiagnosis.description` | diagnoses | 4 | RNICA editable (`:8907`) | Screens 1, 2 | `hopeReportMapper.js:503,598` | No | **required** | always | frontend `required` | JSONB | additive | PRESENT AND CORRECTLY PLACED | |
| Diagnosis / Comorbidities | Primary | Onset Date | — | SNS CLINICAL | date | `diagnoses.primaryDiagnosis.onsetDate` | diagnoses | 4 | RNICA editable (`:8908`) | — | not emitted | No | optional | always | none | JSONB | additive | PRESENT BUT NOT HARVESTED | |
| Diagnosis / Comorbidities | Primary | HOPE Principal Diagnosis Category | I0010 | HOPE | 01 Cancer, 02 Dementia, 03 Neurological, 04 Stroke, 05 COPD, 06 Cardiovascular excl HF, 07 Heart Failure, 08 Liver, 09 Renal, 99 None of the above | `diagnoses.primaryDiagnosis.hopeDiagnosisCategory` | diagnoses | 4 | RNICA editable (`:8909-8921`) | Screen 11 | `hopeReportMapper.js:504-508,598` via `PRINCIPAL_DIAGNOSIS_CATEGORY_LABELS` (`:123-136`) | No | **required** | always | frontend `required` | JSONB | additive | VERIFIED COMPLETE | 10 codes, matching the mapper's label map exactly. |
| Diagnosis / Comorbidities | Prognosis | Terminal Prognosis | J0050 | HOPE | 6 months or less / More than 6 months / Undetermined | `diagnoses.terminalPrognosis` | diagnoses | 4 | RNICA editable (`:8925`) | — | **not emitted** — mapper's J0050 reads `imminentDeath.appearsThreeDaysOrLess` (`:502,609`) | No | optional | always | none | JSONB | additive | CONFLICTING | `SIDEBAR_CONFIG` tags `diagnoses` with `hope: ["I0010","J0050"]` (`:208`) and this field carries `hopeCode: "J0050"` (`:8925`), but J0050 is *Death is Imminent* (3 days), not 6-month prognosis. The exporter correctly uses the `imminentDeath` module. This field is mislabelled with a HOPE code it does not satisfy. |
| Diagnosis / Comorbidities | Secondary | Secondary diagnosis ICD-10 (repeating row) | — | DIAGNOSIS SOURCE | ICD-10 | `diagnoses.secondaryDiagnoses[].icd10` | diagnoses | 4 | RNICA editable (`SecondaryDiagnosesCard`, `:2176-2232`) | Screen 2 | `hopeReportMapper.js:360-378,603` via `diagnosisEntries()` | No | optional | always | none | JSONB array | additive | PRESENT AND CORRECTLY PLACED | |
| Diagnosis / Comorbidities | Secondary | Secondary diagnosis description (repeating row) | — | DIAGNOSIS SOURCE | free text | `diagnoses.secondaryDiagnoses[].description` | diagnoses | 4 | RNICA editable (`:2225`) | Screen 2 | `hopeReportMapper.js:603` | No | optional | always | none | JSONB array | additive | PRESENT AND CORRECTLY PLACED | |
| Diagnosis / Comorbidities | Secondary | **Related / unrelated to terminal condition** | — | SNS CLINICAL | Related / Unrelated | NOT FOUND IN REPOSITORY | — | 4 | — | — | — | No | — | — | — | — | — | MISSING FROM SNS | `SecondaryDiagnosesCard` rows carry only ICD-10 + description; no relatedness classifier was found. This is a payment-relevant hospice distinction. |
| Diagnosis / Comorbidities | Secondary | **Diagnosis source / confirmation** | — | SNS CLINICAL | source picklist | NOT FOUND IN REPOSITORY | — | 4 | — | — | — | No | — | — | — | — | — | MISSING FROM SNS | |
| Diagnosis / Comorbidities | Comorbidities | Cancer | I0100 | HOPE | checkbox Yes/No | `diagnoses.hopeComorbidities.cancer` | diagnoses | 4 | RNICA editable (`:2497,2586`) | Screen 11 | `hopeReportMapper.js:440,536-541` | No | optional | excluded when it is the principal category, except the documented cancer exception (`:2615-2617`) | clinician confirmation required (auto-detect only *suggests*) | JSONB | falls back to regex derivation when `hopeComorbidities` absent (`:456-461,544-552`) | VERIFIED COMPLETE | |
| Diagnosis / Comorbidities | Comorbidities | Heart Failure (e.g. CHF, pulmonary edema) | I0600 | HOPE | checkbox | `diagnoses.hopeComorbidities.heartFailure` | diagnoses | 4 | RNICA editable (`:2498`) | Screen 11 | `hopeReportMapper.js:441` | No | optional | principal-exclusion rule | clinician confirmation | JSONB | regex fallback `hasHeartFailure` (`:531,545`) | VERIFIED COMPLETE | |
| Diagnosis / Comorbidities | Comorbidities | Peripheral Vascular Disease / Peripheral Arterial Disease | I0900 | HOPE | checkbox | `diagnoses.hopeComorbidities.pvdPad` | diagnoses | 4 | RNICA editable (`:2499`) | Screen 11 | `hopeReportMapper.js:442` | No | optional | principal-exclusion rule | clinician confirmation | JSONB | additive | VERIFIED COMPLETE | |
| Diagnosis / Comorbidities | Comorbidities | Cardiovascular (excluding heart failure) | I0950 | HOPE | checkbox | `diagnoses.hopeComorbidities.cardiovascularExclHF` | diagnoses | 4 | RNICA editable (`:2500`) | Screen 11 | `hopeReportMapper.js:443` | No | optional | principal-exclusion rule | clinician confirmation | JSONB | additive | VERIFIED COMPLETE | |
| Diagnosis / Comorbidities | Comorbidities | Liver disease (e.g. cirrhosis) | I1101 | HOPE | checkbox | `diagnoses.hopeComorbidities.liverDisease` | diagnoses | 4 | RNICA editable (`:2501`) | Screen 11 | `hopeReportMapper.js:444` | No | optional | principal-exclusion rule | clinician confirmation | JSONB | additive | VERIFIED COMPLETE | |
| Diagnosis / Comorbidities | Comorbidities | Renal disease | I1510 | HOPE | checkbox | `diagnoses.hopeComorbidities.renalDisease` | diagnoses | 4 | RNICA editable (`:2502`) | Screen 11 | `hopeReportMapper.js:445` | No | optional | principal-exclusion rule | clinician confirmation | JSONB | additive | VERIFIED COMPLETE | |
| Diagnosis / Comorbidities | Comorbidities | Sepsis | I2102 | HOPE | checkbox | `diagnoses.hopeComorbidities.sepsis` | diagnoses | 4 | RNICA editable (`:2503`) | Screen 11 | `hopeReportMapper.js:446` | No | optional | principal-exclusion rule | clinician confirmation | JSONB | additive | VERIFIED COMPLETE | |
| Diagnosis / Comorbidities | Comorbidities | Diabetes Mellitus (DM) | I2900 | HOPE | checkbox | `diagnoses.hopeComorbidities.diabetesMellitus` | diagnoses | 4 | RNICA editable (`:2504`) | Screen 11; Screen 6 endocrine | `hopeReportMapper.js:447` | No | optional | principal-exclusion rule | clinician confirmation | JSONB | additive | VERIFIED COMPLETE | Related but separate editable field `endocrine.diabetes.type` (`:9252`). |
| Diagnosis / Comorbidities | Comorbidities | Neuropathy | I2910 | HOPE | checkbox | `diagnoses.hopeComorbidities.neuropathy` | diagnoses | 4 | RNICA editable (`:2505`) | Screen 11 | `hopeReportMapper.js:448` | No | optional | principal-exclusion rule | clinician confirmation | JSONB | additive | VERIFIED COMPLETE | |
| Diagnosis / Comorbidities | Comorbidities | Stroke | I4501 | HOPE | checkbox | `diagnoses.hopeComorbidities.stroke` | diagnoses | 4 | RNICA editable (`:2506`) | Screen 11 | `hopeReportMapper.js:449` | No | optional | principal-exclusion rule | clinician confirmation | JSONB | additive | VERIFIED COMPLETE | |
| Diagnosis / Comorbidities | Comorbidities | Dementia (including Alzheimer's) | I4801 | HOPE | checkbox | `diagnoses.hopeComorbidities.dementia` | diagnoses | 4 | RNICA editable (`:2507`) | Screen 11; Screen 5 FAST | `hopeReportMapper.js:450` | No | optional | principal-exclusion rule | clinician confirmation | JSONB | additive | VERIFIED COMPLETE | |
| Diagnosis / Comorbidities | Comorbidities | Neurological Conditions (Parkinson's, MS, ALS) | I5150 | HOPE | checkbox | `diagnoses.hopeComorbidities.neurologicalConditions` | diagnoses | 4 | RNICA editable (`:2508`) | Screen 11 | `hopeReportMapper.js:451` | No | optional | principal-exclusion rule | clinician confirmation | JSONB | additive | VERIFIED COMPLETE | |
| Diagnosis / Comorbidities | Comorbidities | Seizure Disorder | I5401 | HOPE | checkbox | `diagnoses.hopeComorbidities.seizureDisorder` | diagnoses | 4 | RNICA editable (`:2509`) | Screen 11; Screen 6 neuro | `hopeReportMapper.js:452` | No | optional | principal-exclusion rule | clinician confirmation | JSONB | additive | VERIFIED COMPLETE | Related editable field `neurological.seizureHistory` (`:9050`). |
| Diagnosis / Comorbidities | Comorbidities | Chronic Obstructive Pulmonary Disease (COPD) | I6202 | HOPE | checkbox | `diagnoses.hopeComorbidities.copd` | diagnoses | 4 | RNICA editable (`:2510`) | Screen 11 | `hopeReportMapper.js:453` | No | optional | principal-exclusion rule | clinician confirmation | JSONB | regex fallback `hasCopd` (`:532,546`) | VERIFIED COMPLETE | |
| Diagnosis / Comorbidities | Comorbidities | **Other Medical Condition** | I8005 | HOPE | checkbox | exported from `diagnoses.hopeComorbidities.other` (`hopeReportMapper.js:542`) — **no writer exists** | diagnoses | 4 | **none** | Screen 11 | `hopeReportMapper.js:542,547` | No | optional | n/a | none | never written | legacy fallback path `hasOtherMedicalCondition` (`:533,547`) is used only when `hopeComorbidities` is entirely absent (`:456-461`) | CONFLICTING | `HOPE_COMORBIDITY_CATEGORIES` has exactly 14 entries and no `other` key. Once any structured comorbidity is set, `useStructuredComorbidities` becomes true and I8005 is emitted as "No" permanently. I8005 is declared in `form_registry.py:375`. This is a real, provable gap. |
| Diagnosis / Comorbidities | Comorbidities | Comorbidity additional note | — | SNS CLINICAL | free text | `diagnoses.hopeComorbidities.*` note field (`RNICA.jsx:2680`) | diagnoses | 4 | RNICA editable | — | not emitted | No | optional | always | none | JSONB | additive | PRESENT BUT NOT HARVESTED | Exact persisted key `NOT VERIFIED` beyond the rendered label "Additional Note (optional)". |
| Diagnosis / Comorbidities | Comorbidities | Uncategorized secondary diagnoses list | — | COMPUTED RESULT | derived | `uncategorizedSecondary` (`RNICA.jsx:2581-2585`) | diagnoses | 4 | none (derived) | Screen 4 | not emitted | No | n/a | always | client | not persisted | n/a | PRESENT AND CORRECTLY PLACED | Safety net so an uncategorizable ICD-10 is not silently dropped. |
| KPS-PPS-FAST / LCD | LCD | Detected LCD disease | — | COMPUTED RESULT | disease key | `diagnoses.ndsEligibility.detectedDisease` | diagnoses | 4 | auto-written by `LcdEligibilityCard` (`:1628-1630`) | Screen 6 nutrition ref | not emitted | No | n/a | requires primary dx text | server `detectLCD()` | JSONB | additive | PRESENT AND CORRECTLY PLACED | |
| KPS-PPS-FAST / LCD | LCD | Disease-specific criterion answers | — | SNS CLINICAL | per-criterion | `diagnoses.ndsEligibility.criteriaAnswers[disease][criterionId]` | diagnoses | 4 | RNICA editable (`setCriteriaAnswer`, `:1706-1709`) | — | not emitted | No | optional | requires detected disease | server `evaluateLCD()` (`:1685`) | JSONB | additive | PRESENT BUT NOT HARVESTED | |
| KPS-PPS-FAST / LCD | LCD | Supplemental criterion facts (e.g. serum albumin) | — | SNS CLINICAL | numeric/text | `diagnoses.ndsEligibility.criteriaFacts[disease][field]` | diagnoses | 4 | RNICA editable (`setCriteriaFact`, `:1710-1713`) | Screen 6 nutrition ref (`:2928`) | not emitted | No | optional | requires detected disease | server `evaluateLCD()` | JSONB | additive | PRESENT AND CORRECTLY PLACED | |
| KPS-PPS-FAST / LCD | LCD | LCD evaluation result (eligible / not eligible, met / unmet / unknown counts) | — | COMPUTED RESULT | derived | `evaluation` (component state, `:1685`) | diagnoses | 4 | none (derived) | Screens 4, 11 | not emitted | No | n/a | requires detected disease | server LCD engine | **not persisted** | n/a | PRESENT AND CORRECTLY PLACED | Recomputed on demand; no competing persisted copy — correct per §16 C. |
| KPS-PPS-FAST / LCD | LCD | **LCD supporting evidence** | — | SNS CLINICAL | free text | `diagnoses.lcdEligibilityNarrative` | diagnoses | 4 | RNICA editable (`LcdSupportingEvidenceCard`, `:1991-1993`) | Screens 11, 13 | not emitted | No | **gates Lock** | always | `evaluate_finalization_readiness` `lcdBaseline` (`rnica_finalization_service.py:130-135`) | JSONB | additive | VERIFIED COMPLETE | Label is "LCD supporting evidence", never "Eligibility Confirmed" — matches directive. Server-side re-validated. |
| Narrative / Admissions Order | Narrative | Disease Trajectory | — | SNS CLINICAL | option set (legacy values detected by `isLegacyDiseaseTrajectoryValue`) | `diagnoses.diseaseTrajectory` | diagnoses | 13 (target) / 4 (current) | RNICA editable (`:2055`) | Screen 2 | not emitted | No | optional | always | legacy-value detection (`:2017`) | JSONB | legacy values flagged, not destroyed | PRESENT BUT MISPLACED | Directive places disease trajectory on Screen 13. |
| Narrative / Admissions Order | Narrative | Diagnoses Narrative / Clinical narrative (diagnoses copy) | — | SNS CLINICAL | free text | `diagnoses.clinicalNarrative` | diagnoses | 13 | renderer exists (`:2029,2037-2039,2126`) and dispatch branch exists (`:8353`) but **no card in `SECTION_CONFIGS.diagnoses.cards`** (`:8904-8945`) | Screen 13 | not emitted | No | **gates Lock** | unreachable | `evaluate_finalization_readiness` `narrativeReviewed` (`rnica_finalization_service.py:120-128`) | JSONB | pre-existing records may hold a value | CONFLICTING | The Lock gate reads a path the current UI cannot edit. Cross-reference `docs/tenant-platform/RNICA_LOCK_DEFECT_UNREACHABLE_NARRATIVE_REVIEW.md`. |
| Narrative / Admissions Order | Narrative | Narrative reviewed | — | READINESS | boolean | `diagnoses.clinicalNarrativeReviewed` | diagnoses | 13 | same unreachable card (`:2140`) | Screens 11, 13 | not emitted | No | **gates Lock** | unreachable | `rnica_finalization_service.py:121`; frontend warning at `RNICA.jsx:1077` | JSONB | pre-existing records may hold a value | CONFLICTING | Same defect. |
| Narrative / Admissions Order | Narrative | RN Addendum | — | SNS CLINICAL | free text | `diagnoses.rnAddendum` | diagnoses | 13 | same card (`:2148-2150`) | — | not emitted | No | optional | unreachable | none | JSONB | additive | PRESENT BUT NOT WIRED | |
| Narrative / Admissions Order | Narrative | Clinician Clarification | — | SNS CLINICAL | free text | `diagnoses.clinicianClarification` | diagnoses | 13 | same card (`:2155-2157`) | — | not emitted | No | optional | unreachable | none | JSONB | additive | PRESENT BUT NOT WIRED | |
| Diagnosis / Comorbidities | Utilization | Recent Hospitalizations (count) | — | SNS CLINICAL | integer | `diagnoses.recentHospitalizations` | diagnoses | 4 | RNICA editable (`:2071-2074`) | Screen 2 | not emitted | No | optional | on the narrative card | none | JSONB | additive | PRESENT BUT NOT WIRED | Lives on the same unreachable card as the diagnoses narrative. |
| Diagnosis / Comorbidities | Utilization | Recent Emergency Department Visits (count) | — | SNS CLINICAL | integer | `diagnoses.recentErVisits` | diagnoses | 4 | RNICA editable (`:2081-2084`) | Screen 2 | not emitted | No | optional | on the narrative card | none | JSONB | additive | PRESENT BUT NOT WIRED | |
| Diagnosis / Comorbidities | Utilization | Utilization Notes | — | SNS CLINICAL | free text | `diagnoses.utilizationNotes` | diagnoses | 4 | RNICA editable (`:2092-2094`) | Screen 2 | not emitted | No | optional | on the narrative card | none | JSONB | additive | PRESENT BUT NOT WIRED | |
| Diagnosis / Comorbidities | LCD | **Non-disease-specific LCD evidence** | — | SNS CLINICAL | structured | `diagnoses.ndsEligibility.*` (the "NDS" prefix denotes non-disease-specific) | diagnoses | 4 | RNICA editable | Screen 11 | not emitted | No | optional | always | server LCD engine | JSONB | additive | PRESENT AND CORRECTLY PLACED | |
| Diagnosis / Comorbidities | LCD | **Complications / decline supporting observations** | — | SNS CLINICAL | free text | covered by `diagnoses.lcdEligibilityNarrative` + `performanceStatus.functionalDeclineNotes` | diagnoses / performanceStatus | 4 / 5 | RNICA editable | — | not emitted | No | optional | always | none | JSONB | additive | REQUIRES AUTHORITY REVIEW | There is no discrete "complications" field; it is absorbed into free text. Whether a discrete field is required is a product decision, not a repository fact. |

---
### 4.5 SCREEN 5 — Functional Status

```
Frontend: RNICA.jsx:8948-9012 (SECTION_CONFIGS.performanceStatus)
Frontend: RNICA.jsx:9003-9010 (ADL card, dataSection: "musculoskeletal")
Frontend: RNICA.jsx:2690-2878 (DeclineTrackerCard, PPS_ORDER, FAST_ORDER)
Frontend: RNICA.jsx:2426-2494 (DmeStatusCard — read-only reference here, owned by Screen 10)
Backend:  backend/tests/test_rnica_functional_assessment_governance.py
Exporter: sns-emr-frontend/src/intake/hopeReportMapper.js — performance scales are NOT emitted
```

| LS | LSub | Label | Code | Class | LRS | Path | Sec | Scr | Edit | RO | HH | SFV | Req | Cond | Val | Pers | Compat | Status | Notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| KPS-PPS-FAST / LCD | Scales | PPS Score | M1190 (per SIDEBAR_CONFIG) | NOT VERIFIED | 100%…0% in 10% steps | `performanceStatus.pps` | performanceStatus | 5 | RNICA editable (`:8958`) | Screens 2, 4 | **not emitted by the mapper** | No | optional | always | none | JSONB | additive | CONFLICTING | `SIDEBAR_CONFIG:209` tags `performanceStatus` with `hope: ["M1190"]` and the card carries `hopeCode: "M1190"` (`:8957`), but M1190 in `HOPE_SKIN_ITEM_CODES` (`form_registry.py:402-406`) and in the mapper (`hopeReportMapper.js:625`) is **Skin Conditions**. The PPS↔M1190 association is wrong. |
| KPS-PPS-FAST / LCD | Scales | PPS Justification | — | SNS CLINICAL | free text | `performanceStatus.ppsJustification` | performanceStatus | 5 | RNICA editable (`:8959`) | — | not emitted | No | optional | always | none | JSONB | additive | PRESENT AND CORRECTLY PLACED | |
| KPS-PPS-FAST / LCD | Scales | KPS Score | — | SNS CLINICAL | 100…0 in 10s | `performanceStatus.kps` | performanceStatus | 5 | RNICA editable (`:8964`) | Screens 2, 4 | not emitted | No | optional | always | none | JSONB | additive | PRESENT AND CORRECTLY PLACED | |
| KPS-PPS-FAST / LCD | Scales | KPS Justification | — | SNS CLINICAL | free text | `performanceStatus.kpsJustification` | performanceStatus | 5 | RNICA editable (`:8965`) | — | not emitted | No | optional | always | none | JSONB | additive | PRESENT AND CORRECTLY PLACED | |
| KPS-PPS-FAST / LCD | Scales | ECOG Score | — | SNS CLINICAL | 0 Fully active … 5 Dead | `performanceStatus.ecog` | performanceStatus | 5 | RNICA editable (`:8970-8974`) | — | not emitted | No | optional | always | none | JSONB | additive | PRESENT AND CORRECTLY PLACED | Inline interpretation **is** present — each option label carries its descriptor. |
| KPS-PPS-FAST / LCD | Scales | ECOG Justification | — | SNS CLINICAL | free text | `performanceStatus.ecogJustification` | performanceStatus | 5 | RNICA editable (`:8975`) | — | not emitted | No | optional | always | none | JSONB | additive | PRESENT AND CORRECTLY PLACED | |
| KPS-PPS-FAST / LCD | Scales | FAST Stage | — | SNS CLINICAL | 1,2,3,4,5,6a-6e,7a-7f | `performanceStatus.fast` | performanceStatus | 5 | RNICA editable (`:8980`) | Screen 4 (dementia LCD) | not emitted | No | optional | always | none | JSONB | additive | PRESENT BUT RESPONSE SET INCOMPLETE | Bare stage codes with **no inline interpretation text**, unlike ECOG/NYHA. `FAST_ORDER` (`:2691`) confirms the same 16 values are used for decline comparison. |
| KPS-PPS-FAST / LCD | Scales | FAST Stage Description | — | SNS CLINICAL | free text | `performanceStatus.fastStage` | performanceStatus | 5 | RNICA editable (`:8981`) | — | not emitted | No | optional | always | none | JSONB | additive | PRESENT AND CORRECTLY PLACED | Free-text companion partially compensates for the missing inline interpretation. |
| KPS-PPS-FAST / LCD | Scales | NYHA Class | — | SNS CLINICAL | I No limitation … IV Severe limitation | `performanceStatus.nyha` | performanceStatus | 5 | RNICA editable (`:8986-8989`) | Screen 4 (HF LCD) | not emitted | No | optional | always | none | JSONB | additive | PRESENT AND CORRECTLY PLACED | Inline interpretation present. |
| KPS-PPS-FAST / LCD | Scales | NYHA Justification | — | SNS CLINICAL | free text | `performanceStatus.nyhaJustification` | performanceStatus | 5 | RNICA editable (`:8990`) | — | not emitted | No | optional | always | none | JSONB | additive | PRESENT AND CORRECTLY PLACED | |
| KPS-PPS-FAST / LCD | Scales | **Applicability / "None" state for a scale** | — | SNS CLINICAL | N/A checkbox | NOT FOUND IN REPOSITORY | — | 5 | — | — | — | No | — | — | — | — | — | MISSING FROM SNS | Verified absent: none of `pps`, `kps`, `ecog`, `fast`, `nyha` offers an explicit "not applicable" value; blank is the only way to express it, which is indistinguishable from "not yet documented". |
| KPS-PPS-FAST / LCD | Decline | Change Since Last Assessment | — | COMPUTED RESULT | derived | `DeclineTrackerCard` (`:2715`) using `PPS_ORDER` (`:2690`) and `FAST_ORDER` (`:2691`) against `fetchPerformanceHistory` | performanceStatus | 5 | none (derived) | Screens 2, 5 | not emitted | No | n/a | requires prior assessments | server history API | not persisted | n/a | PRESENT AND CORRECTLY PLACED | |
| KPS-PPS-FAST / LCD | Decline | Functional Decline Notes | — | SNS CLINICAL | free text | `performanceStatus.functionalDeclineNotes` | performanceStatus | 5 | RNICA editable (`:8995`) | Screens 2, 4 | not emitted | No | optional | always | none | JSONB | additive | PRESENT AND CORRECTLY PLACED | |
| PCG / Mobility / ADL | ADL | Bathing | — | SNS CLINICAL | 0 Independent / 1 Setup help only / 2 Supervision / 3 Limited assistance / 4 Extensive assistance / 5 Total dependence | `musculoskeletal.adl.bathing` | musculoskeletal (via `dataSection`) | 5 | RNICA editable (`:9004`) | Screen 7 personal care ("See ADL assessment") | not emitted | No | optional | always | none | JSONB | additive | PRESENT AND CORRECTLY PLACED | **Presentation** ownership already moved to Functional Status; **persistence** remains in `musculoskeletal`. |
| PCG / Mobility / ADL | ADL | Dressing | — | SNS CLINICAL | 0-5 | `musculoskeletal.adl.dressing` | musculoskeletal | 5 | RNICA editable (`:9005`) | — | not emitted | No | optional | always | none | JSONB | additive | PRESENT AND CORRECTLY PLACED | |
| PCG / Mobility / ADL | ADL | Toileting | — | SNS CLINICAL | 0-5 | `musculoskeletal.adl.toileting` | musculoskeletal | 5 | RNICA editable (`:9006`) | — | not emitted | No | optional | always | none | JSONB | additive | PRESENT AND CORRECTLY PLACED | |
| PCG / Mobility / ADL | ADL | Transferring | — | SNS CLINICAL | 0-5 | `musculoskeletal.adl.transferring` | musculoskeletal | 5 | RNICA editable (`:9007`) | — | not emitted | No | optional | always | none | JSONB | additive | PRESENT AND CORRECTLY PLACED | Concept-overlaps `musculoskeletal.mobility.transferAbility` (`:9327`), which uses a *different* 5-value assist vocabulary. |
| PCG / Mobility / ADL | ADL | Eating | — | SNS CLINICAL | 0-5 | `musculoskeletal.adl.eating` | musculoskeletal | 5 | RNICA editable (`:9008`) | — | not emitted | No | optional | always | none | JSONB | additive | PRESENT AND CORRECTLY PLACED | Legacy "feeding". |
| PCG / Mobility / ADL | ADL | Grooming | — | SNS CLINICAL | 0-5 | `musculoskeletal.adl.grooming` | musculoskeletal | 5 | RNICA editable (`:9009`) | Screen 7 aide tasks | not emitted | No | optional | always | none | JSONB | additive | PRESENT AND CORRECTLY PLACED | Grooming **is** present — six ADLs total. |
| PCG / Mobility / ADL | ADL | **Ambulation as an ADL** | — | SNS CLINICAL | 0-5 | NOT FOUND IN REPOSITORY inside `adl.*` | musculoskeletal | 5 | — | — | — | No | — | — | — | — | — | MISSING FROM SNS | Ambulation exists only as `musculoskeletal.mobility.ambulatoryStatus` (`:9325`) on a **different scale** (Independent/Supervised/Assisted/Dependent/Bedbound), so it cannot contribute to an ADL total. |
| PCG / Mobility / ADL | ADL | **Continence as an ADL** | — | SNS CLINICAL | 0-5 | NOT FOUND IN REPOSITORY inside `adl.*` | — | 5 | — | — | — | No | — | — | — | — | — | MISSING FROM SNS | Continence is captured clinically at `genitourinary.urinaryStatus` (`:9274`) and `gastrointestinal.bowelStatus` (`:9192`) — not as a scored ADL. Current SNS authority therefore does **not** include continence in the ADL set. |
| PCG / Mobility / ADL | ADL | **ADL total score** | — | COMPUTED RESULT | sum | NOT FOUND IN REPOSITORY | — | 5 | — | — | — | No | — | — | — | — | — | MISSING FROM SNS | No computation and no persisted total anywhere. |
| PCG / Mobility / ADL | ADL | **Complete-dependence count** | — | COMPUTED RESULT | count of ADLs at maximum dependence | NOT FOUND IN REPOSITORY | — | 5 | — | — | — | No | — | — | — | — | — | MISSING FROM SNS | |
| PCG / Mobility / ADL | ADL | **ADL scale definition** | — | NOT VERIFIED | SNS uses 0-5; the legacy description implies a different granularity | `SECTION_CONFIGS.performanceStatus` ADL card (`:9003`) | musculoskeletal | 5 | RNICA editable | — | — | No | — | — | — | — | — | REQUIRES AUTHORITY REVIEW | The canonical SNS scale **is 0-5** (six levels), verified directly at `:9004-9009`. No HOPE item consumes ADL values (the mapper emits none), and no LCD criterion consuming an ADL scale was found in this pass. Changing the scale would therefore be a product decision with no external consumer constraint that this repository can prove — do not "correct" it from a screenshot. |
| PCG / Mobility / ADL | Mobility | Ambulatory Status | — | SNS CLINICAL | Independent/Supervised/Assisted/Dependent/Bedbound | `musculoskeletal.mobility.ambulatoryStatus` | musculoskeletal | 5 (target) / 6 (current) | RNICA editable (`:9325`) | — | not emitted | No | optional | always | none | JSONB | additive | PRESENT BUT MISPLACED | Covers legacy "ambulation" and "bedbound/chairbound". Chairbound specifically is only expressible via `skin.braden.activity` value 2 ("Chairfast"). |
| PCG / Mobility / ADL | Mobility | Endurance | — | SNS CLINICAL | Good/Fair/Poor | `musculoskeletal.mobility.endurance` | musculoskeletal | 5 | RNICA editable (`:9326`) | — | not emitted | No | optional | always | none | JSONB | additive | PRESENT BUT MISPLACED | |
| PCG / Mobility / ADL | Mobility | Transfer Ability | — | SNS CLINICAL | Independent/Standby assist/1-person/2-person/Hoyer lift | `musculoskeletal.mobility.transferAbility` | musculoskeletal | 5 | RNICA editable (`:9327`) | — | not emitted | No | optional | always | none | JSONB | additive | PRESENT BUT MISPLACED | |
| PCG / Mobility / ADL | Mobility | Assistive Devices | — | SNS CLINICAL | Walker/Wheelchair/Cane/Crutches/Hospital bed/Hoyer lift/None | `musculoskeletal.assistiveDevices` | musculoskeletal | 5 | RNICA editable (`:9322`) | Screen 10 DME | not emitted | No | optional | always | none | JSONB | additive | PRESENT BUT MISPLACED | Assistive-device *use* ≠ DME *order*; the two lists overlap but must stay distinct (see §19). |
| PCG / Mobility / ADL | Mobility | Gait | — | SNS CLINICAL | Normal/Unsteady/Shuffling/Unable | `musculoskeletal.gait` | musculoskeletal | 5 | RNICA editable (`:9321`) | — | not emitted | No | optional | always | none | JSONB | additive | PRESENT BUT MISPLACED | |
| DME Device / IV Assessment | DME | DME per-item status (read-only summary) | — | ORDER/POC | Has/Needs/Ordered/Delivered/Declined/N/A | `safety.dmeItems[]` (`DmeStatusCard`, `:2426-2494`) | safety | 10 (owner); 5 read-only | Screen 10 (target) — **currently editable inside the `safety` module** (`:9461`) | Screen 5 | not emitted | No | optional | always | none | JSONB array | additive | PRESENT BUT MISPLACED | Directive: "DME shows only read-only summary here; DME ownership is Orders & POC". Today editable ownership is in `safety`, i.e. Screen 8 — wrong on both counts. |

---

### 4.6 SCREEN 6 — Body Systems

```
Frontend: RNICA.jsx:9014-9079  neurological
Frontend: RNICA.jsx:9081-9109  cardiovascular
Frontend: RNICA.jsx:9111-9148  respiratory
Frontend: RNICA.jsx:9150-9172  infection
Frontend: RNICA.jsx:9174-9205  gastrointestinal
Frontend: RNICA.jsx:9207-9238  nutrition
Frontend: RNICA.jsx:9240-9267  endocrine
Frontend: RNICA.jsx:9269-9305  genitourinary
Frontend: RNICA.jsx:9307-9338  musculoskeletal
Frontend: RNICA.jsx:9340-9369  skin
Frontend: RNICA.jsx:2330-2424  wound row editor + WoundListCard
Frontend: RNICA.jsx:6106-6172  ConstipationAutoAssessCard
Frontend: RNICA.jsx:2924-2955  NutritionAnthropometricReferenceCard
Frontend: RNICA.jsx:2957-3060  WeightLossAutoCalcCard
Taxonomy: rnicaThirteenScreenTaxonomy.js:61-71 (ten body-system modules)
Exporter: hopeReportMapper.js:614-615 (J2030/J2040), :625-627 (M1190/M1195/M1200)
```

#### 4.6.1 Neurological / Mental / Sensory

| LS | LSub | Label | Code | Class | LRS | Path | Sec | Scr | Edit | RO | HH | SFV | Req | Cond | Val | Pers | Compat | Status | Notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Neuro / Cardiovascular | Mental Status | Symptoms / Demeanor | — | SNS CLINICAL | Anxiety, Agitation, Peaceful, Confused, Angry, Restless, Depressed, Seizure, Combative, Sundowning, Tremors/twitching, Other | `neurological.symptomsDemeanor` | neurological | 6 | RNICA editable (`:9020`) | Screen 3 | not emitted | No (ungraded) | optional | always | none | JSONB | additive | CONFLICTING | Contains ungraded Anxiety and Agitation checkboxes that compete with graded J2051C/H on Screen 3. |
| Neuro / Cardiovascular | Mental Status | Level of Consciousness | — | SNS CLINICAL | Alert, Lethargic, Obtunded, Stuporous, Comatose, Awake, Minimally responsive, Coma | `neurological.consciousness` | neurological | 6 | RNICA editable (`:9021`) | Screen 8 (imminent death) | not emitted | No | optional | always | none | JSONB | additive | PRESENT BUT RESPONSE SET INCOMPLETE | The 8-value list contains near-synonyms (Comatose/Coma; Alert/Awake) — a vocabulary-hygiene issue, flagged not fixed. |
| Neuro / Cardiovascular | Mental Status | Oriented to Time | — | SNS CLINICAL | boolean | `neurological.orientation.time` | neurological | 6 | RNICA editable (`:9022`) | — | not emitted | No | optional | always | none | JSONB | additive | PRESENT AND CORRECTLY PLACED | |
| Neuro / Cardiovascular | Mental Status | Oriented to Place | — | SNS CLINICAL | boolean | `neurological.orientation.place` | neurological | 6 | RNICA editable (`:9023`) | — | not emitted | No | optional | always | none | JSONB | additive | PRESENT AND CORRECTLY PLACED | |
| Neuro / Cardiovascular | Mental Status | Oriented to Person | — | SNS CLINICAL | boolean | `neurological.orientation.person` | neurological | 6 | RNICA editable (`:9024`) | — | not emitted | No | optional | always | none | JSONB | additive | PRESENT AND CORRECTLY PLACED | |
| Neuro / Cardiovascular | Mental Status | Oriented to Situation | — | SNS CLINICAL | boolean | `neurological.orientation.situation` | neurological | 6 | RNICA editable (`:9025`) | — | not emitted | No | optional | always | none | JSONB | additive | PRESENT AND CORRECTLY PLACED | |
| Neuro / Cardiovascular | Mental Status | Disoriented | — | SNS CLINICAL | boolean | `neurological.orientation.disoriented` | neurological | 6 | RNICA editable (`:9026`) | — | not emitted | No | optional | always | none | JSONB | additive | CONFLICTING | Logically redundant with the four positive orientation flags and can contradict them; no cross-validation exists. |
| Neuro / Cardiovascular | BIMS | N0500 — Repetition | N0500 | NOT VERIFIED | 0-3 | `neurological.hopeItems.n0500` | neurological | 6 | RNICA editable (`:9031`) | — | **not read by the mapper** | No | optional | always | none | JSONB | additive | CONFLICTING | CMS N0500 is *Scheduled Opioid* (`hopeReportMapper.js:633`), not BIMS repetition. The RNICA label and the exporter disagree on what N0500 means. Structured-findings cross-writes to this path exist (`structured_findings.py:1224-1238`), so real data is accumulating under a contested code. |
| Neuro / Cardiovascular | BIMS | N0510 — Recall | N0510 | NOT VERIFIED | 0-3 | `neurological.hopeItems.n0510` | neurological | 6 | RNICA editable (`:9032`) | — | not read by the mapper | No | optional | always | none | JSONB | additive | CONFLICTING | CMS N0510 is *PRN Opioid* (`:634`). |
| Neuro / Cardiovascular | BIMS | N0520 — Temporal Orientation | N0520 | NOT VERIFIED | 0-3 | `neurological.hopeItems.n0520` | neurological | 6 | RNICA editable (`:9033`) | — | not read by the mapper | No | optional | always | none | JSONB | additive | CONFLICTING | CMS N0520 is *Bowel Regimen* (`:635`). |
| Neuro / Cardiovascular | BIMS | **BIMS total score** | — | COMPUTED RESULT | 0-15 | NOT FOUND IN REPOSITORY | — | 6 | — | — | — | No | — | — | — | — | — | MISSING FROM SNS | |
| Neuro / Cardiovascular | Communication | Communication | — | SNS CLINICAL | Clear, Impaired, Unable, Normal, Aphasia, Slurred speech, Speech limited to six or fewer intelligible words, Other | `neurological.communication` | neurological | 6 | RNICA editable (`:9038`) | Screen 7 | not emitted | No | optional | always | none | JSONB | additive | PRESENT AND CORRECTLY PLACED | Covers legacy "speech/communication". |
| Neuro / Cardiovascular | Communication | Hearing | — | SNS CLINICAL | Adequate/Impaired/Deaf/Hearing aid | `neurological.hearing` | neurological | 6 | RNICA editable (`:9039`) | Screen 7 | not emitted | No | optional | always | none | JSONB | additive | PRESENT AND CORRECTLY PLACED | Partially covers the legacy "hearing / sign-language need"; sign language specifically is **not** representable. |
| Neuro / Cardiovascular | Communication | Vision | — | SNS CLINICAL | Adequate/Impaired/Blind/Corrective lenses | `neurological.vision` | neurological | 6 | RNICA editable (`:9040`) | — | not emitted | No | optional | always | none | JSONB | additive | PRESENT AND CORRECTLY PLACED | |
| Neuro / Cardiovascular | Communication | Balance | — | SNS CLINICAL | Steady/Unsteady/Unable to stand/Normal/Impaired | `neurological.balance` | neurological | 6 | RNICA editable (`:9041`) | Screen 5, Screen 8 | not emitted | No | optional | always | none | JSONB | additive | CONFLICTING | Second editable balance field at `musculoskeletal.balance` (`:9329`) with a 2-value set (Normal/Impaired). |
| Neuro / Cardiovascular | Communication | Sensory Deficits | — | SNS CLINICAL | Numbness/Tingling/Decreased sensation/Phantom pain | `neurological.sensoryDeficits` | neurological | 6 | RNICA editable (`:9042`) | Screen 3 (neuropathic pain cross-ref) | not emitted | No | optional | always | none | JSONB | additive | PRESENT AND CORRECTLY PLACED | |
| Neuro / Cardiovascular | Communication | Sensory Aids | — | SNS CLINICAL | Glasses/Hearing aids/Other | `neurological.sensoryAids` | neurological | 6 | RNICA editable (`:9043`) | — | not emitted | No | optional | always | none | JSONB | additive | PRESENT AND CORRECTLY PLACED | |
| Neuro / Cardiovascular | Psychiatric | Cognition Assessment | — | SNS CLINICAL | free text | `neurological.cognition` | neurological | 6 | RNICA editable (`:9048`) | — | not emitted | No | optional | always | none | JSONB | additive | PRESENT AND CORRECTLY PLACED | |
| Neuro / Cardiovascular | Psychiatric | Delirium | — | SNS CLINICAL | boolean | `neurological.delirium` | neurological | 6 | RNICA editable (`:9049`) | — | not emitted | No | optional | always | none | JSONB | additive | PRESENT AND CORRECTLY PLACED | |
| Neuro / Cardiovascular | Psychiatric | Seizure History | — | SNS CLINICAL | boolean | `neurological.seizureHistory` | neurological | 6 | RNICA editable (`:9050`) | Screen 4 (I5401) | not emitted | No | optional | always | none | JSONB | additive | PRESENT AND CORRECTLY PLACED | |
| Neuro / Cardiovascular | Psychiatric | Psychiatric History (type) | — | SNS CLINICAL | None/Bipolar disorder/OCD/Schizophrenia/Depression/Other | `neurological.psychiatricHistoryType` | neurological | 6 | RNICA editable (`:9051`) | Screen 7 | not emitted | No | optional | always | none | JSONB | additive | CONFLICTING | Overlaps `psychosocial.psychosocialHistory` (`:9503-9506`), which separately records History of depression / anxiety / substance abuse. |
| Neuro / Cardiovascular | Psychiatric | Psychiatric History Notes | — | SNS CLINICAL | free text | `neurological.psychiatricHistory` | neurological | 6 | RNICA editable (`:9052`) | — | not emitted | No | optional | always | none | JSONB | additive | PRESENT AND CORRECTLY PLACED | |
| Neuro / Cardiovascular | Sleep/Rest | Sleep Pattern | — | SNS CLINICAL | 10 options | `neurological.sleepRest.sleepPattern` | neurological | 6 | RNICA editable (`:9057`) | — | not emitted | No | optional | always | none | JSONB | additive | PRESENT BUT RESPONSE SET INCOMPLETE | Mixes pattern descriptors with satisfaction statements ("Satisfied with sleep") in one radio group. |
| Neuro / Cardiovascular | Sleep/Rest | Average Sleep Hours | — | SNS CLINICAL | numeric | `neurological.sleepRest.averageSleepHours` | neurological | 6 | RNICA editable (`:9058`) | — | not emitted | No | optional | always | none | JSONB | additive | PRESENT AND CORRECTLY PLACED | |
| Neuro / Cardiovascular | Sleep/Rest | Nighttime Symptoms | — | SNS CLINICAL | Pain/Dyspnea/Restlessness/Confusion/Anxiety/Nausea/None | `neurological.sleepRest.nighttimeSymptoms` | neurological | 6 | RNICA editable (`:9059`) | Screen 3 | not emitted | No | optional | always | none | JSONB | additive | PRESENT AND CORRECTLY PLACED | Ungraded; does not compete with J2051 because it is explicitly nocturnal. |
| Neuro / Cardiovascular | Sleep/Rest | Sleep Aids / Current Interventions | — | SNS CLINICAL | Medication/Positioning/White noise/Warm milk-tea/Other | `neurological.sleepRest.sleepAids` | neurological | 6 | RNICA editable (`:9060`) | — | not emitted | No | optional | always | none | JSONB | additive | PRESENT AND CORRECTLY PLACED | |
| Neuro / Cardiovascular | Sleep/Rest | Response to Interventions | — | SNS CLINICAL | free text | `neurological.sleepRest.response` | neurological | 6 | RNICA editable (`:9061`) | — | not emitted | No | optional | always | none | JSONB | additive | PRESENT AND CORRECTLY PLACED | |
| Neuro / Cardiovascular | Sleep/Rest | Restfulness | — | SNS CLINICAL | Adequate/Inadequate | `neurological.sleepRest.restfulness` | neurological | 6 | RNICA editable (`:9062`) | — | not emitted | No | optional | always | none | JSONB | additive | PRESENT AND CORRECTLY PLACED | |
| Neuro / Cardiovascular | Sleep/Rest | Sleep Notes | — | SNS CLINICAL | free text | `neurological.sleepRest.notes` | neurological | 6 | RNICA editable (`:9063`) | — | not emitted | No | optional | always | none | JSONB | additive | PRESENT AND CORRECTLY PLACED | |
| Neuro / Cardiovascular | Motor | Motor Deficit Present | — | SNS CLINICAL | boolean | `neurological.motorDeficit` | neurological | 6 | RNICA editable (`:9068`) | — | not emitted | No | optional | always | none | JSONB | additive | PRESENT AND CORRECTLY PLACED | |
| Neuro / Cardiovascular | Motor | Affected Side | — | SNS CLINICAL | Left/Right/Bilateral | `neurological.affectedSide` | neurological | 6 | RNICA editable (`:9069`) | — | not emitted | No | optional | always | none | JSONB | additive | PRESENT AND CORRECTLY PLACED | |
| Neuro / Cardiovascular | Motor | Deficit Type | — | SNS CLINICAL | Hemiparesis/Hemiplegia/Paraparesis/Quadriparesis/Other | `neurological.deficitType` | neurological | 6 | RNICA editable (`:9070`) | Screen 6 MSK | not emitted | No | optional | always | none | JSONB | additive | CONFLICTING | Overlaps `musculoskeletal.paralysis` (`:9320`), a 7-value "Disability" radio covering the same clinical space. |
| Neuro / Cardiovascular | Notes | Neurological Notes | — | SNS CLINICAL | free text | `neurological.notes` | neurological | 6 | RNICA editable (`:9075`) | — | not emitted | No | optional | always | none | JSONB | additive | PRESENT AND CORRECTLY PLACED | Legacy "observations". |

#### 4.6.2 Cardiovascular

| LS | LSub | Label | Code | Class | LRS | Path | Sec | Scr | Edit | RO | HH | SFV | Req | Cond | Val | Pers | Compat | Status | Notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Neuro / Cardiovascular | CV | BP Symptoms | — | SNS CLINICAL | Orthostatic/Hypertensive/Hypotensive/Normal | `cardiovascular.bpSymptoms` | cardiovascular | 6 | RNICA editable (`:9086`) | — | not emitted | No | optional | always | none | JSONB | additive | PRESENT AND CORRECTLY PLACED | |
| Neuro / Cardiovascular | CV | Pulse Sites | — | SNS CLINICAL | Apical/Pedal/Radial/Femoral | `cardiovascular.pulseSites` | cardiovascular | 6 | RNICA editable (`:9087`) | — | not emitted | No | optional | always | none | JSONB | additive | PRESENT BUT RESPONSE SET INCOMPLETE | **Answering the directive's question directly:** pulse quality is **one shared field**, not per-site. `pulseSites` is a multi-select of *which sites were palpated*; `pulseQuality` (`:9088`) is a single radio applying to all of them. There is no `pulseQuality.apical`, `.pedal`, `.radial` or `.femoral` path anywhere in the repository. |
| Neuro / Cardiovascular | CV | Pulse Quality | — | SNS CLINICAL | Regular/Strong/Weak/Thready/Bounding/Irregular/Tachycardia/Bradycardia/Absent | `cardiovascular.pulseQuality` | cardiovascular | 6 | RNICA editable (`:9088`) | Screen 3 | not emitted | No | optional | always | none | JSONB | additive | CONFLICTING | Competing editable owner `vitals.pulseQuality` (`:8779`) with a 5-value subset. |
| Neuro / Cardiovascular | CV | Edema Present | — | SNS CLINICAL | tri-state (yes/no/unknown) | `cardiovascular.edema.present` | cardiovascular | 6 | RNICA editable (`:9089`) | — | not emitted | No | optional | always | none | JSONB | additive | PRESENT AND CORRECTLY PLACED | `triState` is the only response type in RNICA that natively expresses "not assessed". |
| Neuro / Cardiovascular | CV | Edema Location | — | SNS CLINICAL | 6 options | `cardiovascular.edema.location` | cardiovascular | 6 | RNICA editable (`:9090`) | — | not emitted | No | optional | always | none | JSONB | additive | PRESENT AND CORRECTLY PLACED | |
| Neuro / Cardiovascular | CV | Edema Severity | — | SNS CLINICAL | Trace/1+/2+/3+/4+ | `cardiovascular.edema.severity` | cardiovascular | 6 | RNICA editable (`:9091`) | — | not emitted | No | optional | always | none | JSONB | additive | PRESENT AND CORRECTLY PLACED | |
| Neuro / Cardiovascular | CV | Chest Pain Present | — | SNS CLINICAL | tri-state | `cardiovascular.chestPain.present` | cardiovascular | 6 | RNICA editable (`:9092`) | Screen 3 | not emitted | No | optional | always | none | JSONB | additive | PRESENT AND CORRECTLY PLACED | Does not compete with J2051A because it is anatomically scoped. |
| Neuro / Cardiovascular | CV | Chest Pain Type | — | SNS CLINICAL | free text | `cardiovascular.chestPain.type` | cardiovascular | 6 | RNICA editable (`:9093`) | — | not emitted | No | optional | always | none | JSONB | additive | PRESENT AND CORRECTLY PLACED | |
| Neuro / Cardiovascular | CV | Peripheral Circulation | — | SNS CLINICAL | free text | `cardiovascular.peripheralCirculation` | cardiovascular | 6 | RNICA editable (`:9094`) | — | not emitted | No | optional | always | none | JSONB | additive | PRESENT BUT RESPONSE SET INCOMPLETE | Free text where a controlled set would be expected. |
| Neuro / Cardiovascular | CV | Heart Sounds | — | SNS CLINICAL | free text | `cardiovascular.heartSounds` | cardiovascular | 6 | RNICA editable (`:9095`) | — | not emitted | No | optional | always | none | JSONB | additive | PRESENT BUT RESPONSE SET INCOMPLETE | |
| Neuro / Cardiovascular | CV | JVD (Jugular Venous Distention) | — | SNS CLINICAL | tri-state | `cardiovascular.jvd` | cardiovascular | 6 | RNICA editable (`:9096`) | — | not emitted | No | optional | always | none | JSONB | additive | PRESENT AND CORRECTLY PLACED | |
| Neuro / Cardiovascular | CV | Skin Color | — | SNS CLINICAL | free text | `cardiovascular.skinColor` | cardiovascular | 6 | RNICA editable (`:9097`) | Screen 6 skin | not emitted | No | optional | always | none | JSONB | additive | CONFLICTING | Overlaps `skin.skinStatus` values Jaundice / Cyanotic / Mottled (`:9346`). |
| Neuro / Cardiovascular | CV | Pacemaker | — | SNS CLINICAL | boolean | `cardiovascular.pacemaker` | cardiovascular | 6 | RNICA editable (`:9098`) | Screen 9 (ACP relevance) | not emitted | No | optional | always | none | JSONB | additive | PRESENT AND CORRECTLY PLACED | |
| Neuro / Cardiovascular | CV | Internal Defibrillator | — | SNS CLINICAL | boolean | `cardiovascular.internalDefibrillator` | cardiovascular | 6 | RNICA editable (`:9099`) | Screen 9 | not emitted | No | optional | always | none | JSONB | additive | PRESENT AND CORRECTLY PLACED | Clinically ACP-relevant (deactivation discussion) but correctly owned as a physical finding. |
| Neuro / Cardiovascular | CV | Varicose Veins | — | SNS CLINICAL | boolean | `cardiovascular.varicoseVeins` | cardiovascular | 6 | RNICA editable (`:9100`) | — | not emitted | No | optional | always | none | JSONB | additive | PRESENT AND CORRECTLY PLACED | |
| Neuro / Cardiovascular | CV | Central Venous Line | — | SNS CLINICAL | boolean | `cardiovascular.centralVenousLine` | cardiovascular | 6 | RNICA editable (`:9101`) | Screen 3 (IV assessment) | not emitted | No | optional | always | none | JSONB | additive | CONFLICTING | Overlaps `vitals.ivAssessment.type` value "Central" (`:8794`). |
| Neuro / Cardiovascular | CV | Cool Extremities | — | SNS CLINICAL | boolean | `cardiovascular.coolExtremities` | cardiovascular | 6 | RNICA editable (`:9102`) | Screen 8 | not emitted | No | optional | always | none | JSONB | additive | CONFLICTING | Overlaps `imminentDeath.indicators` value "Cool/cold extremities" (`:9382`). |
| Neuro / Cardiovascular | CV | Stasis Ulcer | — | SNS CLINICAL | boolean | `cardiovascular.stasisUlcer` | cardiovascular | 6 | RNICA editable (`:9103`) | Screen 6 skin | not emitted | No | optional | always | none | JSONB | additive | CONFLICTING | Overlaps the wound list `woundType` options (`:2334`). |
| Neuro / Cardiovascular | CV | Heart Failure Present | — | SNS CLINICAL | boolean | `cardiovascular.heartFailurePresent` | cardiovascular | 6 | RNICA editable (`:9104`) | Screen 4 (I0600) | not emitted | No | optional | always | none | JSONB | additive | CONFLICTING | Third representation of heart failure alongside `diagnoses.hopeComorbidities.heartFailure` (HOPE-authoritative) and the regex fallback `hasHeartFailure`. |
| Neuro / Cardiovascular | CV | Heart Failure Type | — | SNS CLINICAL | Systolic/Diastolic/Unspecified | `cardiovascular.heartFailureType` | cardiovascular | 6 | RNICA editable (`:9105`) | — | not emitted | No | optional | always | none | JSONB | additive | PRESENT AND CORRECTLY PLACED | |
| Neuro / Cardiovascular | CV | Cardiovascular Notes | — | SNS CLINICAL | free text | `cardiovascular.notes` | cardiovascular | 6 | RNICA editable (`:9106`) | — | not emitted | No | optional | always | none | JSONB | additive | PRESENT AND CORRECTLY PLACED | |

#### 4.6.3 Respiratory

| LS | LSub | Label | Code | Class | LRS | Path | Sec | Scr | Edit | RO | HH | SFV | Req | Cond | Val | Pers | Compat | Status | Notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Respiratory / GI | Respiratory | SOB Severity | J2051B (competing) | SFV | None/Mild/Moderate/Severe/At rest | `respiratory.sobSeverity` | respiratory | 6 (finding) — **SFV ownership stays Screen 3** | RNICA editable (`:9116`, `sfv: true`) | Screen 3 | feeds `sobIndicated` (`hopeReportMapper.js:527`) and J2030A (`:614`) | flagged `sfv: true` in config, but `getSfvStatus()` reads only `symptomImpact.*` | optional | always | none | JSONB | additive | CONFLICTING | Two editable SOB severities with different vocabularies. The config flags this one for SFV; the actual SFV computation ignores it. Directive requires Screen 3 ownership with Screen 6 read-only cross-reference. |
| Respiratory / GI | Respiratory | Treatment Declined (when applicable) | — | SFV | boolean | `respiratory.treatmentDeclined` | respiratory | 3/6 | RNICA editable (`:9117`) | — | not emitted | No | optional | always | none | JSONB | additive | PRESENT BUT NOT HARVESTED | See Screen 3 note — the only treatment-declined field in the system. |
| Respiratory / GI | Respiratory | Exertion Level | — | SNS CLINICAL | At rest/Minimal/Moderate/Severe exertion/With speech/Push of speech/Pursed-lip breathing/Other | `respiratory.exertionLevel` | respiratory | 6 | RNICA editable (`:9118`) | — | not emitted | No | optional | always | none | JSONB | additive | PRESENT BUT RESPONSE SET INCOMPLETE | Mixes exertion levels with breathing-pattern findings (pursed-lip) in one radio. |
| Respiratory / GI | Respiratory | Screened for shortness of breath | J2030A | HOPE | boolean | `respiratory.shortnessOfBreathScreened` | respiratory | 6 | RNICA editable (`:9119`) | Screen 11 | `hopeReportMapper.js:614` (OR'd with `sobSeverity`) | No | optional | always | none | JSONB | additive | PRESENT AND CORRECTLY PLACED | J2030 declared at `form_registry.py:384`. |
| Respiratory / GI | Respiratory | SOB screening date | J2030B | HOPE | date | `respiratory.screeningDate` | respiratory | 6 | RNICA editable (`:9120`) | — | `hopeReportMapper.js:614` | No | optional | always | none | JSONB | additive | PRESENT AND CORRECTLY PLACED | |
| Respiratory / GI | Respiratory | Treatment for shortness of breath initiated | J2040A | HOPE | boolean | `respiratory.treatmentInitiated` | respiratory | 6 | RNICA editable (`:9121`) | Screen 11 | `hopeReportMapper.js:615` | No | optional | always | none | JSONB | additive | PRESENT AND CORRECTLY PLACED | J2040 declared at `form_registry.py:385`. |
| Respiratory / GI | Respiratory | SOB treatment date | J2040B | HOPE | date | `respiratory.treatmentDate` | respiratory | 6 | RNICA editable (`:9122`) | — | `hopeReportMapper.js:615` | No | optional | always | none | JSONB | additive | PRESENT AND CORRECTLY PLACED | |
| Respiratory / GI | Respiratory | Lung Sounds | — | SNS CLINICAL | Clear/Crackles/Wheezes/Rhonchi/Diminished/Absent/Stridor/Pleural rub/Rales | `respiratory.lungSounds` | respiratory | 6 | RNICA editable (`:9123`) | — | not emitted | No | optional | always | none | JSONB | additive | PRESENT BUT RESPONSE SET INCOMPLETE | "Crackles" and "Rales" are synonyms offered as separate options. |
| Respiratory / GI | Respiratory | Respiration Pattern | — | SNS CLINICAL | 11 options | `respiratory.respirations` | respiratory | 6 | RNICA editable (`:9124`) | Screen 8 | not emitted | No | optional | always | none | JSONB | additive | CONFLICTING | Options "Cheyne-Stokes" and "Apneic episodes" duplicate `imminentDeath.indicators` values (`:9381`). "Regular" and "Normal" are duplicate synonyms. |
| Respiratory / GI | Respiratory | Cough Type | — | SNS CLINICAL | None/Productive/Non-productive/Hemoptysis/Barrel chest | `respiratory.coughType` | respiratory | 6 | RNICA editable (`:9125`) | — | not emitted | No | optional | always | none | JSONB | additive | PRESENT BUT RESPONSE SET INCOMPLETE | "Barrel chest" is a chest-wall finding, not a cough type. |
| Respiratory / GI | Respiratory | Sputum Character | — | SNS CLINICAL | free text | `respiratory.sputumCharacter` | respiratory | 6 | RNICA editable (`:9126`) | — | not emitted | No | optional | always | none | JSONB | additive | PRESENT AND CORRECTLY PLACED | |
| Respiratory / GI | Oxygen | Oxygen in Use | — | SNS CLINICAL | boolean | `respiratory.oxygenTherapy.inUse` | respiratory | 6 | RNICA editable (`:9129`) | Screen 8, Screen 10 | not emitted | No | optional | always | none | JSONB | additive | CONFLICTING | Competing editable flag `safety.oxygenInUse` (`:9437`). See §16 B. |
| Respiratory / GI | Oxygen | Delivery Type | — | SNS CLINICAL | Nasal cannula/Simple mask/Non-rebreather/Venturi mask/High flow | `respiratory.oxygenTherapy.type` | respiratory | 6 | RNICA editable (`:9130`) | Screen 10 | not emitted | No | optional | always | none | JSONB | additive | PRESENT AND CORRECTLY PLACED | |
| Respiratory / GI | Oxygen | Liters/Minute | — | SNS CLINICAL | numeric | `respiratory.oxygenTherapy.litersPerMinute` | respiratory | 6 | RNICA editable (`:9131`) | Screen 10 | not emitted | No | optional | always | none | JSONB | additive | PRESENT AND CORRECTLY PLACED | |
| Respiratory / GI | Oxygen | Hours/Day | — | SNS CLINICAL | free text | `respiratory.oxygenTherapy.hoursPerDay` | respiratory | 6 | RNICA editable (`:9132`) | — | not emitted | No | optional | always | none | JSONB | additive | PRESENT AND CORRECTLY PLACED | |
| Respiratory / GI | Oxygen | Delivery Mode | — | SNS CLINICAL | Continuous/PRN | `respiratory.oxygenTherapy.deliveryMode` | respiratory | 6 | RNICA editable (`:9133`) | Screen 10 | not emitted | No | optional | always | none | JSONB | additive | PRESENT AND CORRECTLY PLACED | |
| Respiratory / GI | Oxygen | On Room Air | — | SNS CLINICAL | boolean | `respiratory.oxygenTherapy.onRoomAir` | respiratory | 6 | RNICA editable (`:9134`) | Screen 3 | not emitted | No | optional | always | none | JSONB | additive | CONFLICTING | Competing with `vitals.oxygenSaturationOnRA` (`:8784`). |
| Respiratory / GI | Oxygen | SpO2 on O2 | — | SNS CLINICAL | numeric | `respiratory.oxygenTherapy.satOnO2` | respiratory | 6 | RNICA editable (`:9135`) | Screen 3 | not emitted | No | optional | always | none | JSONB | additive | CONFLICTING | Competing with `vitals.oxygenSaturation` (`:8783`). |
| Respiratory / GI | Ventilator | Short-Term Ventilator | — | SNS CLINICAL | boolean | `respiratory.ventilator.shortTermVentilator` | respiratory | 6 | RNICA editable (`:9138`) | Screen 9 | not emitted | No | optional | always | none | JSONB | additive | PRESENT AND CORRECTLY PLACED | |
| Respiratory / GI | Ventilator | Long-Term Ventilator | — | SNS CLINICAL | boolean | `respiratory.ventilator.longTermVentilator` | respiratory | 6 | RNICA editable (`:9139`) | Screen 9 | not emitted | No | optional | always | none | JSONB | additive | PRESENT AND CORRECTLY PLACED | ACP-relevant (F2100) but correctly owned as a device finding. |
| Respiratory / GI | Ventilator | Ventilator Type and Settings | — | SNS CLINICAL | free text | `respiratory.ventilator.ventilatorTypeAndSettings` | respiratory | 6 | RNICA editable (`:9140`) | — | not emitted | No | optional | always | none | JSONB | additive | PRESENT AND CORRECTLY PLACED | |
| Respiratory / GI | Ventilator | Tracheostomy Type | — | SNS CLINICAL | free text | `respiratory.ventilator.tracheostomyType` | respiratory | 6 | RNICA editable (`:9141`) | — | not emitted | No | optional | always | none | JSONB | additive | PRESENT AND CORRECTLY PLACED | |
| Respiratory / GI | Ventilator | Tracheostomy Size | — | SNS CLINICAL | free text | `respiratory.ventilator.tracheostomySize` | respiratory | 6 | RNICA editable (`:9142`) | — | not emitted | No | optional | always | none | JSONB | additive | PRESENT AND CORRECTLY PLACED | |
| Respiratory / GI | Notes | Respiratory Notes | — | SNS CLINICAL | free text | `respiratory.notes` | respiratory | 6 | RNICA editable (`:9145`) | — | not emitted | No | optional | always | none | JSONB | additive | PRESENT AND CORRECTLY PLACED | |

#### 4.6.4 Immunological / Infection

| LS | LSub | Label | Code | Class | LRS | Path | Sec | Scr | Edit | RO | HH | SFV | Req | Cond | Val | Pers | Compat | Status | Notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| (no legacy screen described) | Allergies | Patient Allergies | — | SNS CLINICAL | structured list | `PatientAllergies` custom renderer (dispatch `RNICA.jsx:8476`) | infection | 6 | RNICA editable via renderer; card declares `fields: []` (`:9154`) | Screen 10 | not emitted | No | optional | always | NOT VERIFIED | NOT VERIFIED — renderer sources allergies from the patient record, not `form_data.infection` | n/a | REQUIRES AUTHORITY REVIEW | The renderer function itself was not located in `RNICA.jsx` by symbol search this pass (only its dispatch site), so its persistence target is `NOT VERIFIED`. |
| (no legacy screen described) | Immune | Immunosuppressed | — | SNS CLINICAL | boolean | `infection.immunosuppressed` | infection | 6 | RNICA editable (`:9156`) | — | not emitted | No | optional | always | none | JSONB | additive | PRESENT AND CORRECTLY PLACED | |
| (no legacy screen described) | Immune | Precautions | — | SNS CLINICAL | Standard/Contact/Droplet/Airborne | `infection.precautions` | infection | 6 | RNICA editable (`:9157`) | Screen 7 teaching | not emitted | No | optional | always | none | JSONB | additive | PRESENT AND CORRECTLY PLACED | |
| (no legacy screen described) | Infection | Antibiotic-Resistant Infection (current) | — | SNS CLINICAL | None/MRSA/C. difficile/Other | `infection.antibioticResistantInfection` | infection | 6 | RNICA editable (`:9160`) | — | not emitted | No | optional | always | none | JSONB | additive | PRESENT AND CORRECTLY PLACED | |
| (no legacy screen described) | Infection | History of Resistant Infection | — | SNS CLINICAL | None/MRSA/C. difficile/Other | `infection.historyOfResistantInfections` | infection | 6 | RNICA editable (`:9161`) | — | not emitted | No | optional | always | none | JSONB | additive | PRESENT AND CORRECTLY PLACED | |
| (no legacy screen described) | Infection | Current Active Infection | — | None/Sepsis/UTI/Respiratory tract/IV site/Wound/HIV-related/Pressure area/Other | SNS CLINICAL | `infection.currentInfections` | infection | 6 | RNICA editable (`:9162`) | Screen 4 (I2102 sepsis) | not emitted | No | optional | always | none | JSONB | additive | CONFLICTING | The "Sepsis" option duplicates the authoritative HOPE comorbidity `diagnoses.hopeComorbidities.sepsis` (I2102). |
| (no legacy screen described) | Infection | Antibiotic Use | — | SNS CLINICAL | boolean | `infection.antibioticUse` | infection | 6 | RNICA editable (`:9165`) | — | not emitted | No | optional | always | none | JSONB | additive | PRESENT AND CORRECTLY PLACED | |
| (no legacy screen described) | Infection | Temperature | — | SNS CLINICAL | numeric °F | `infection.temperature` | infection | 6 | RNICA editable (`:9166`) | Screen 3 | not emitted | No | optional | always | none | JSONB | additive | CONFLICTING | Second editable temperature; `vitals.temperature` (`:8776`) is the vital-sign owner and additionally carries a unit field, which this one does not. |
| (no legacy screen described) | Infection | Recurrent Infection | — | SNS CLINICAL | boolean | `infection.recurrentInfection` | infection | 6 | RNICA editable (`:9167`) | Screen 4 (LCD decline evidence) | not emitted | No | optional | always | none | JSONB | additive | PRESENT AND CORRECTLY PLACED | |
| (no legacy screen described) | Infection | Infection History | — | SNS CLINICAL | free text | `infection.infectionHistory` | infection | 6 | RNICA editable (`:9168`) | — | not emitted | No | optional | always | none | JSONB | additive | PRESENT AND CORRECTLY PLACED | |
| (no legacy screen described) | Infection | Other Observations / Notes | — | SNS CLINICAL | free text | `infection.notes` | infection | 6 | RNICA editable (`:9169`) | — | not emitted | No | optional | always | none | JSONB | additive | PRESENT AND CORRECTLY PLACED | |

#### 4.6.5 Gastrointestinal

| LS | LSub | Label | Code | Class | LRS | Path | Sec | Scr | Edit | RO | HH | SFV | Req | Cond | Val | Pers | Compat | Status | Notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| GI / Nutrition / Endocrine / GU | GI | Constipation auto-suggestion (from Last BM date) | — | COMPUTED RESULT | derived severity | `ConstipationAutoAssessCard` (`:6113-6140`), thresholds at `:6106` | gastrointestinal | 6 | suggestion only; clinician clicks to insert (`:6134-6136`) | — | not emitted | Feeds `gastrointestinal.constipation` only when accepted | n/a | requires `lastBM`; suppressed when diarrhea is active (`:6132`) | client | not persisted (the accepted value is) | additive | PRESENT AND CORRECTLY PLACED | Correctly a suggestion, not a silent auto-write. |
| GI / Nutrition / Endocrine / GU | GI | Nausea | J2051D (competing) | SFV | None/Mild/Moderate/Severe | `gastrointestinal.nausea` | gastrointestinal | 6 (finding), SFV owned by 3 | RNICA editable (`:9180`, `sfv: true`) | Screen 3 | not emitted | flagged `sfv: true`; ignored by `getSfvStatus()` | optional | always | none | JSONB | additive | CONFLICTING | Cross-write mappings exist (`structured_findings.py:719`) that write both paths from the same evidence. |
| GI / Nutrition / Endocrine / GU | GI | Vomiting | J2051E (competing) | SFV | None/Mild/Moderate/Severe | `gastrointestinal.vomiting` | gastrointestinal | 6 | RNICA editable (`:9181`) | Screen 3 | not emitted | flagged, ignored | optional | always | none | JSONB | additive | CONFLICTING | |
| GI / Nutrition / Endocrine / GU | GI | Vomiting Occurrences (24 hours) | — | SNS CLINICAL | numeric | `gastrointestinal.vomitingOccurrences24h` | gastrointestinal | 6 | RNICA editable (`:9182`) | — | not emitted | No | optional | always | none | JSONB | additive | PRESENT AND CORRECTLY PLACED | |
| GI / Nutrition / Endocrine / GU | GI | Diarrhea | J2051F (competing) | SFV | None/Mild/Moderate/Severe | `gastrointestinal.diarrhea` | gastrointestinal | 6 | RNICA editable (`:9183`) | Screen 3 | not emitted | flagged, ignored | optional | always | none | JSONB | additive | CONFLICTING | |
| GI / Nutrition / Endocrine / GU | GI | Constipation | J2051G (competing) | SFV | None/Mild/Moderate/Severe | `gastrointestinal.constipation` | gastrointestinal | 6 | RNICA editable (`:9184`) | Screen 3 | not emitted | flagged, ignored | optional | always | `ConstipationAutoAssessCard` suggestion | JSONB | additive | CONFLICTING | |
| GI / Nutrition / Endocrine / GU | GI | Bowel Sounds | — | SNS CLINICAL | Normal/Hyperactive/Hypoactive/Absent | `gastrointestinal.bowelSounds` | gastrointestinal | 6 | RNICA editable (`:9187`) | — | not emitted | No | optional | always | none | JSONB | additive | PRESENT AND CORRECTLY PLACED | |
| GI / Nutrition / Endocrine / GU | GI | Abdomen | — | SNS CLINICAL | Soft/Firm/Tympanic/Distended/Tender/Nontender/Rigid | `gastrointestinal.abdomen` | gastrointestinal | 6 | RNICA editable (`:9188`) | — | not emitted | No | optional | always | none | JSONB | additive | PRESENT BUT RESPONSE SET INCOMPLETE | Single-select radio for characteristics that commonly co-occur (e.g. soft + distended). |
| GI / Nutrition / Endocrine / GU | GI | Ascites | — | SNS CLINICAL | boolean | `gastrointestinal.ascites` | gastrointestinal | 6 | RNICA editable (`:9189`) | Screen 4 (liver LCD) | not emitted | No | optional | always | none | JSONB | additive | PRESENT AND CORRECTLY PLACED | |
| GI / Nutrition / Endocrine / GU | GI | Abdominal Girth | — | SNS CLINICAL | free text | `gastrointestinal.abdominalGirth` | gastrointestinal | 6 | RNICA editable (`:9190`) | — | not emitted | No | optional | always | none | JSONB | additive | PRESENT AND CORRECTLY PLACED | |
| GI / Nutrition / Endocrine / GU | GI | Stool | — | SNS CLINICAL | Normal/Bloody/Colostomy/Ileostomy | `gastrointestinal.stoolCharacter` | gastrointestinal | 6 | RNICA editable (`:9191`) | — | not emitted | No | optional | always | none | JSONB | additive | PRESENT BUT RESPONSE SET INCOMPLETE | Mixes stool character with ostomy presence, duplicating `gastrointestinal.ostomy.type` (`:9201`). |
| GI / Nutrition / Endocrine / GU | GI | Bowel Status | — | SNS CLINICAL | Regular/Irregular/Impaction/Continent/Incontinent/Bowel-bladder program | `gastrointestinal.bowelStatus` | gastrointestinal | 6 | RNICA editable (`:9192`) | Screen 5 (ADL continence discussion) | not emitted | No | optional | always | none | JSONB | additive | PRESENT AND CORRECTLY PLACED | This, not an ADL item, is where bowel continence lives. |
| GI / Nutrition / Endocrine / GU | GI | Bowel Frequency | — | SNS CLINICAL | free text | `gastrointestinal.bowelFrequency` | gastrointestinal | 6 | RNICA editable (`:9193`) | — | not emitted | No | optional | always | none | JSONB | additive | PRESENT AND CORRECTLY PLACED | |
| GI / Nutrition / Endocrine / GU | GI | Last BM Date | — | SNS CLINICAL | date | `gastrointestinal.lastBM` | gastrointestinal | 6 | RNICA editable (`:9194`) | Screen 3 | not emitted | Feeds constipation auto-suggestion | optional | always | none | JSONB | additive | PRESENT AND CORRECTLY PLACED | |
| GI / Nutrition / Endocrine / GU | GI | Reason Bowel Regimen Could Not Be Initiated | N0520 (related) | SNS CLINICAL | free text | `gastrointestinal.reasonBowelRegimenNotInitiated` | gastrointestinal | 6 | RNICA editable (`:9195`) | Screen 11 | **not read** — mapper's N0520 reads `medications.bowelRegimen` (`:530,635`) | No | optional | always | none | JSONB | additive | PRESENT BUT NOT HARVESTED | The *reason* is captured but the *status* it explains has no input. |
| GI / Nutrition / Endocrine / GU | Devices | Feeding Tube Present | — | SNS CLINICAL | boolean | `gastrointestinal.feedingTube.present` | gastrointestinal | 6 | RNICA editable (`:9198`) | Screen 6 nutrition, Screen 9 | not emitted | No | optional | always | none | JSONB | additive | CONFLICTING | Overlaps `nutrition.artificialFeeding` (`:9233`), which lists PEG/NG/J-tube/Pump/TPN/None. |
| GI / Nutrition / Endocrine / GU | Devices | Tube Type | — | SNS CLINICAL | NG/PEG/PEJ/G-tube/J-tube | `gastrointestinal.feedingTube.type` | gastrointestinal | 6 | RNICA editable (`:9199`) | — | not emitted | No | optional | always | none | JSONB | additive | CONFLICTING | Same overlap; the two lists are not identical (PEJ vs Pump/TPN). |
| GI / Nutrition / Endocrine / GU | Devices | Ostomy Present | — | SNS CLINICAL | boolean | `gastrointestinal.ostomy.present` | gastrointestinal | 6 | RNICA editable (`:9200`) | — | not emitted | No | optional | always | none | JSONB | additive | PRESENT AND CORRECTLY PLACED | |
| GI / Nutrition / Endocrine / GU | Devices | Ostomy Type | — | SNS CLINICAL | Colostomy/Ileostomy/Urostomy | `gastrointestinal.ostomy.type` | gastrointestinal | 6 | RNICA editable (`:9201`) | Screen 6 GU | not emitted | No | optional | always | none | JSONB | additive | CONFLICTING | "Urostomy" also appears in `genitourinary.urinaryStatus` (`:9274`) and `genitourinary.catheter.type` (`:9281`). |
| GI / Nutrition / Endocrine / GU | Notes | GI Notes | — | SNS CLINICAL | free text | `gastrointestinal.notes` | gastrointestinal | 6 | RNICA editable (`:9202`) | — | not emitted | No | optional | always | none | JSONB | additive | PRESENT AND CORRECTLY PLACED | |

#### 4.6.6 Nutrition

| LS | LSub | Label | Code | Class | LRS | Path | Sec | Scr | Edit | RO | HH | SFV | Req | Cond | Val | Pers | Compat | Status | Notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| GI / Nutrition / Endocrine / GU | Nutrition | Anthropometric & Metabolic Reference (height, weight, BMI, MAC, serum albumin) | — | COMPUTED RESULT | read-only mirror | `NutritionAnthropometricReferenceCard` (`:2924-2955`) reading `vitals.*` and `diagnoses.ndsEligibility.criteriaFacts` | nutrition | 6 | **read-only** | Screen 6 | not emitted | No | n/a | hidden when nothing to show (`:2930`) | n/a | **not persisted** | n/a | VERIFIED COMPLETE | Exemplar of the correct cross-screen pattern: displays another screen's values without creating a second persisted copy. |
| GI / Nutrition / Endocrine / GU | Nutrition | Weight Loss Auto-Calculation | — | COMPUTED RESULT | lbs + % over ~6 months | `WeightLossAutoCalcCard` (`:2957-3060`), 183-day target (`:2991`) | nutrition | 6 | suggestion; clinician accepts into `nutrition.weightLossPastSixMonths` | Screen 4 (LCD decline) | not emitted | No | n/a | requires weight history | server history API | suggestion not persisted | additive | PRESENT AND CORRECTLY PLACED | Directly addresses the legacy "weight loss >10% / 6 months" concept by computing both the absolute loss and the percentage (`:3005-3006`). |
| GI / Nutrition / Endocrine / GU | Nutrition | Weight Loss (past 6 months) | — | SNS CLINICAL | free text ("lbs or %") | `nutrition.weightLossPastSixMonths` | nutrition | 6 | RNICA editable (`:9220`) | Screen 4 | not emitted | No | optional | always | none | JSONB | additive | PRESENT BUT RESPONSE SET INCOMPLETE | A single free-text field holding either lbs *or* % cannot be evaluated against a ">10% in 6 months" LCD threshold without parsing. The auto-calc card computes both but writes into this one string. |
| GI / Nutrition / Endocrine / GU | Nutrition | **Cachexia response** | — | SNS CLINICAL | boolean/graded | NOT FOUND IN REPOSITORY | — | 6 | — | — | — | No | — | — | — | — | — | MISSING FROM SNS | No `cachexia` path exists in any section. |
| GI / Nutrition / Endocrine / GU | Nutrition | Appetite | — | SNS CLINICAL | Good/Fair/Poor/Anorexic | `nutrition.appetite` | nutrition | 6 | RNICA editable (`:9221`) | — | not emitted | No | optional | always | none | JSONB | additive | PRESENT AND CORRECTLY PLACED | |
| GI / Nutrition / Endocrine / GU | Nutrition | Diet Type | — | SNS CLINICAL | free text | `nutrition.dietType` | nutrition | 6 | RNICA editable (`:9222`) | Screen 10 | not emitted | No | optional | always | none | JSONB | additive | PRESENT BUT RESPONSE SET INCOMPLETE | Free text where a diet-order vocabulary would be expected for POC use. |
| GI / Nutrition / Endocrine / GU | Nutrition | Fluid Intake | — | SNS CLINICAL | Adequate/Decreased/Minimal | `nutrition.fluidIntake` | nutrition | 6 | RNICA editable (`:9223`) | Screen 8 (imminent death "reduced intake") | not emitted | No | optional | always | none | JSONB | additive | CONFLICTING | Overlaps the imminent-death "Inability to swallow" / reduced-intake concept (`:9382`). |
| GI / Nutrition / Endocrine / GU | Nutrition | Swallowing Issues | — | SNS CLINICAL | Dysphagia/Aspiration risk/Pocketing/Coughing with swallowing/None | `nutrition.swallowingIssues` | nutrition | 6 | RNICA editable (`:9224`) | Screen 8 | not emitted | No | optional | always | none | JSONB | additive | PRESENT AND CORRECTLY PLACED | |
| GI / Nutrition / Endocrine / GU | Nutrition | Oral Mucosa | — | SNS CLINICAL | free text | `nutrition.oralMucosa` | nutrition | 6 | RNICA editable (`:9225`) | — | not emitted | No | optional | always | none | JSONB | additive | PRESENT AND CORRECTLY PLACED | |
| GI / Nutrition / Endocrine / GU | Nutrition | Upper Dentures | — | SNS CLINICAL | boolean | `nutrition.dentures.upper` | nutrition | 6 | RNICA editable (`:9226`) | — | not emitted | No | optional | always | none | JSONB | additive | PRESENT AND CORRECTLY PLACED | |
| GI / Nutrition / Endocrine / GU | Nutrition | Lower Dentures | — | SNS CLINICAL | boolean | `nutrition.dentures.lower` | nutrition | 6 | RNICA editable (`:9227`) | — | not emitted | No | optional | always | none | JSONB | additive | PRESENT AND CORRECTLY PLACED | |
| GI / Nutrition / Endocrine / GU | Nutrition | Nutritional Supplements | — | SNS CLINICAL | free text | `nutrition.nutritionalSupplements` | nutrition | 6 | RNICA editable (`:9228`) | Screen 10 | not emitted | No | optional | always | none | JSONB | additive | PRESENT AND CORRECTLY PLACED | |
| GI / Nutrition / Endocrine / GU | Nutrition | Nutrition Notes | — | SNS CLINICAL | free text | `nutrition.notes` | nutrition | 6 | RNICA editable (`:9229`) | — | not emitted | No | optional | always | none | JSONB | additive | PRESENT AND CORRECTLY PLACED | |
| GI / Nutrition / Endocrine / GU | Nutrition | NPO Status | — | SNS CLINICAL | Not NPO/NPO/NPO except meds/Modified-thickened liquids only | `nutrition.npoStatus` | nutrition | 6 | RNICA editable (`:9232`) | Screen 10 | not emitted | No | optional | always | none | JSONB | additive | PRESENT AND CORRECTLY PLACED | |
| GI / Nutrition / Endocrine / GU | Nutrition | Artificial Feeding / Access Devices | — | SNS CLINICAL | PEG/NG/J-tube/Pump/TPN/None | `nutrition.artificialFeeding` | nutrition | 6 | RNICA editable (`:9233`) | Screen 6 GI, Screen 9 | not emitted | No | optional | always | none | JSONB | additive | CONFLICTING | See `gastrointestinal.feedingTube.*` overlap above. |
| GI / Nutrition / Endocrine / GU | Nutrition | Oral Cavity Findings | — | SNS CLINICAL | Edentulous/Stomatitis/Thrush/Poor dentition/Normal | `nutrition.oralCavityFindings` | nutrition | 6 | RNICA editable (`:9236`) | — | not emitted | No | optional | always | none | JSONB | additive | PRESENT AND CORRECTLY PLACED | |

#### 4.6.7 Endocrine

| LS | LSub | Label | Code | Class | LRS | Path | Sec | Scr | Edit | RO | HH | SFV | Req | Cond | Val | Pers | Compat | Status | Notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| GI / Nutrition / Endocrine / GU | Endocrine | Impairment | — | SNS CLINICAL | Thyroid/Parathyroid/Pituitary/Adrenal/Pancreas/None | `endocrine.endocrineImpairment` | endocrine | 6 | RNICA editable (`:9245`) | — | not emitted | No | optional | always | none | JSONB | additive | PRESENT AND CORRECTLY PLACED | |
| GI / Nutrition / Endocrine / GU | Endocrine | Thyroid | — | SNS CLINICAL | Normal/Enlarged/Tender/Nodular/Not assessed | `endocrine.thyroid.assessment` | endocrine | 6 | RNICA editable (`:9248`) | — | not emitted | No | optional | always | none | JSONB | additive | VERIFIED COMPLETE | One of the few fields with an explicit "Not assessed" value. |
| GI / Nutrition / Endocrine / GU | Endocrine | Thyroid Notes | — | SNS CLINICAL | free text | `endocrine.thyroid.notes` | endocrine | 6 | RNICA editable (`:9249`) | — | not emitted | No | optional | always | none | JSONB | additive | PRESENT AND CORRECTLY PLACED | |
| GI / Nutrition / Endocrine / GU | Endocrine | Diabetes Type | — | SNS CLINICAL | Type 1/Type 2/Not diabetic/Unknown | `endocrine.diabetes.type` | endocrine | 6 | RNICA editable (`:9252`) | Screen 4 (I2900) | not emitted | No | optional | always | none | JSONB | additive | CONFLICTING | Overlaps HOPE-authoritative `diagnoses.hopeComorbidities.diabetesMellitus`. |
| GI / Nutrition / Endocrine / GU | Endocrine | Diabetes Dependency | — | SNS CLINICAL | Insulin-dependent/Non-insulin-dependent/Glucose-management concern/Not applicable | `endocrine.diabetes.dependency` | endocrine | 6 | RNICA editable (`:9253`) | — | not emitted | No | optional | always | none | JSONB | additive | VERIFIED COMPLETE | Has an explicit "Not applicable" value. |
| GI / Nutrition / Endocrine / GU | Endocrine | Glucose Monitoring Frequency | — | SNS CLINICAL | None/Daily/BID/TID/QID/Weekly | `endocrine.diabetes.glucoseMonitoring` | endocrine | 6 | RNICA editable (`:9254`) | Screen 10 | not emitted | No | optional | always | none | JSONB | additive | PRESENT AND CORRECTLY PLACED | |
| GI / Nutrition / Endocrine / GU | Endocrine | Last HbA1c Value | — | SNS CLINICAL | free text | `endocrine.diabetes.lastHbA1c` | endocrine | 6 | RNICA editable (`:9255`) | — | not emitted | No | optional | always | none | JSONB | additive | PRESENT AND CORRECTLY PLACED | |
| GI / Nutrition / Endocrine / GU | Endocrine | Last HbA1c Date | — | SNS CLINICAL | date | `endocrine.diabetes.lastHbA1cDate` | endocrine | 6 | RNICA editable (`:9256`) | — | not emitted | No | optional | always | none | JSONB | additive | PRESENT AND CORRECTLY PLACED | |
| GI / Nutrition / Endocrine / GU | Endocrine | Insulin Type | — | SNS CLINICAL | free text | `endocrine.diabetes.insulinType` | endocrine | 6 | RNICA editable (`:9257`) | Screen 10 | not emitted | No | optional | always | none | JSONB | additive | PRESENT AND CORRECTLY PLACED | |
| GI / Nutrition / Endocrine / GU | Endocrine | Insulin Dose | — | SNS CLINICAL | free text | `endocrine.diabetes.insulinDose` | endocrine | 6 | RNICA editable (`:9258`) | Screen 10 | not emitted | No | optional | always | none | JSONB | additive | PRESENT AND CORRECTLY PLACED | |
| GI / Nutrition / Endocrine / GU | Endocrine | Oral Hypoglycemics | — | SNS CLINICAL | Metformin/Sulfonylurea/DPP-4/SGLT2/None | `endocrine.diabetes.oralHypoglycemics` | endocrine | 6 | RNICA editable (`:9259`) | Screen 10 | not emitted | No | optional | always | none | JSONB | additive | PRESENT AND CORRECTLY PLACED | |
| GI / Nutrition / Endocrine / GU | Endocrine | Symptoms Present | — | SNS CLINICAL | 7 options | `endocrine.endocrineSymptoms` | endocrine | 6 | RNICA editable (`:9262`) | — | not emitted | No | optional | always | none | JSONB | additive | PRESENT AND CORRECTLY PLACED | |
| GI / Nutrition / Endocrine / GU | Endocrine | Current Treatment | — | SNS CLINICAL | 6 options | `endocrine.currentEndocrineMeds` | endocrine | 6 | RNICA editable (`:9263`) | Screen 10 | not emitted | No | optional | always | none | JSONB | additive | PRESENT AND CORRECTLY PLACED | |
| GI / Nutrition / Endocrine / GU | Endocrine | Other Observations / Notes | — | SNS CLINICAL | free text | `endocrine.notes` | endocrine | 6 | RNICA editable (`:9264`) | — | not emitted | No | optional | always | none | JSONB | additive | PRESENT AND CORRECTLY PLACED | |

#### 4.6.8 Genitourinary / Reproductive

| LS | LSub | Label | Code | Class | LRS | Path | Sec | Scr | Edit | RO | HH | SFV | Req | Cond | Val | Pers | Compat | Status | Notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Skin / MusculoSkeletal / Urinary | Urinary | Continence | — | SNS CLINICAL | 11 options (Continent … Nocturia) | `genitourinary.urinaryStatus` | genitourinary | 6 | RNICA editable (`:9274`) | Screen 5 | not emitted | No | optional | always | none | JSONB | additive | PRESENT BUT RESPONSE SET INCOMPLETE | Single-select radio conflating continence type, device status (Catheterized/Urostomy) and symptoms (Painful urination/Nocturia) that can co-occur. |
| Skin / MusculoSkeletal / Urinary | Urinary | Frequency | — | SNS CLINICAL | free text | `genitourinary.frequency` | genitourinary | 6 | RNICA editable (`:9275`) | — | not emitted | No | optional | always | none | JSONB | additive | PRESENT AND CORRECTLY PLACED | |
| Skin / MusculoSkeletal / Urinary | Urinary | Urine | — | SNS CLINICAL | Clear/Cloudy/Pale/Blood/Odor | `genitourinary.urineCharacteristics` | genitourinary | 6 | RNICA editable (`:9276`) | — | not emitted | No | optional | always | none | JSONB | additive | CONFLICTING | A second, longer urine-characteristics list exists at `genitourinary.catheter.urineCharacteristics` (`:9286`) with 7 different options. |
| Skin / MusculoSkeletal / Urinary | Urinary | Urine Color | — | SNS CLINICAL | free text | `genitourinary.urineColor` | genitourinary | 6 | RNICA editable (`:9277`) | — | not emitted | No | optional | always | none | JSONB | additive | CONFLICTING | Overlaps the colour values inside both characteristics lists. |
| Skin / MusculoSkeletal / Urinary | Catheter | Catheter Present | — | SNS CLINICAL | boolean | `genitourinary.catheter.present` | genitourinary | 6 | RNICA editable (`:9280`) | — | not emitted | No | optional | always | none | JSONB | additive | PRESENT AND CORRECTLY PLACED | |
| Skin / MusculoSkeletal / Urinary | Catheter | Type | — | SNS CLINICAL | None/Foley/Suprapubic/Condom/Intermittent/Urostomy | `genitourinary.catheter.type` | genitourinary | 6 | RNICA editable (`:9281`) | Screen 6 GI | not emitted | No | optional | always | none | JSONB | additive | PRESENT AND CORRECTLY PLACED | |
| Skin / MusculoSkeletal / Urinary | Catheter | Size | — | SNS CLINICAL | free text | `genitourinary.catheter.size` | genitourinary | 6 | RNICA editable (`:9282`) | — | not emitted | No | optional | always | none | JSONB | additive | PRESENT AND CORRECTLY PLACED | |
| Skin / MusculoSkeletal / Urinary | Catheter | Insertion Date | — | SNS CLINICAL | date | `genitourinary.catheter.insertionDate` | genitourinary | 6 | RNICA editable (`:9283`) | — | not emitted | No | optional | always | none | JSONB | additive | PRESENT AND CORRECTLY PLACED | |
| Skin / MusculoSkeletal / Urinary | Catheter | Last Change Date | — | SNS CLINICAL | date | `genitourinary.catheter.lastChangeDate` | genitourinary | 6 | RNICA editable (`:9284`) | — | not emitted | No | optional | always | none | JSONB | additive | PRESENT AND CORRECTLY PLACED | |
| Skin / MusculoSkeletal / Urinary | Catheter | Condition | — | SNS CLINICAL | Patent/Blocked/Leaking | `genitourinary.catheter.condition` | genitourinary | 6 | RNICA editable (`:9285`) | — | not emitted | No | optional | always | none | JSONB | additive | PRESENT AND CORRECTLY PLACED | |
| Skin / MusculoSkeletal / Urinary | Catheter | Urine Characteristics (Catheter) | — | SNS CLINICAL | 7 options | `genitourinary.catheter.urineCharacteristics` | genitourinary | 6 | RNICA editable (`:9286`) | — | not emitted | No | optional | always | none | JSONB | additive | CONFLICTING | See above. |
| Skin / MusculoSkeletal / Urinary | Catheter | Irrigation Solution | — | SNS CLINICAL | free text | `genitourinary.catheter.irrigation.solution` | genitourinary | 6 | RNICA editable (`:9287`) | Screen 10 | not emitted | No | optional | always | none | JSONB | additive | PRESENT AND CORRECTLY PLACED | |
| Skin / MusculoSkeletal / Urinary | Catheter | Irrigation Frequency | — | SNS CLINICAL | free text | `genitourinary.catheter.irrigation.frequency` | genitourinary | 6 | RNICA editable (`:9288`) | Screen 10 | not emitted | No | optional | always | none | JSONB | additive | PRESENT AND CORRECTLY PLACED | |
| Skin / MusculoSkeletal / Urinary | Catheter | Irrigation Duration | — | SNS CLINICAL | free text | `genitourinary.catheter.irrigation.duration` | genitourinary | 6 | RNICA editable (`:9289`) | — | not emitted | No | optional | always | none | JSONB | additive | PRESENT AND CORRECTLY PLACED | |
| Skin / MusculoSkeletal / Urinary | Catheter | Catheter Care | — | SNS CLINICAL | free text | `genitourinary.catheterCare` | genitourinary | 6 | RNICA editable (`:9290`) | Screen 10 | not emitted | No | optional | always | none | JSONB | additive | PRESENT AND CORRECTLY PLACED | |
| Skin / MusculoSkeletal / Urinary | Output | Output | — | SNS CLINICAL | Adequate/Decreased/Anuria/Polyuria | `genitourinary.urineOutput` | genitourinary | 6 | RNICA editable (`:9293`) | Screen 8 | not emitted | No | optional | always | none | JSONB | additive | CONFLICTING | Overlaps `imminentDeath.indicators` value "No urine output" (`:9381`). |
| Skin / MusculoSkeletal / Urinary | Output | 24-Hour Volume (if measured) | — | SNS CLINICAL | numeric | `genitourinary.twentyFourHourVolume` | genitourinary | 6 | RNICA editable (`:9294`) | — | not emitted | No | optional | always | none | JSONB | additive | PRESENT AND CORRECTLY PLACED | |
| Skin / MusculoSkeletal / Urinary | Reproductive | Concerns | — | SNS CLINICAL | 5 options | `genitourinary.reproductive.concerns` | genitourinary | 6 | RNICA editable (`:9297`) | — | not emitted | No | optional | always | none | JSONB | additive | PRESENT AND CORRECTLY PLACED | |
| Skin / MusculoSkeletal / Urinary | Reproductive | Reproductive Notes | — | SNS CLINICAL | free text | `genitourinary.reproductive.notes` | genitourinary | 6 | RNICA editable (`:9298`) | — | not emitted | No | optional | always | none | JSONB | additive | PRESENT AND CORRECTLY PLACED | |
| Skin / MusculoSkeletal / Urinary | Bladder | Interventions | — | SNS CLINICAL | Bladder training/Scheduled toileting/Pelvic floor exercises/External collection device | `genitourinary.bladderManagement` | genitourinary | 6 | RNICA editable (`:9301`) | Screen 10 | not emitted | No | optional | always | none | JSONB | additive | PRESENT AND CORRECTLY PLACED | |
| Skin / MusculoSkeletal / Urinary | Notes | GU Notes | — | SNS CLINICAL | free text | `genitourinary.notes` | genitourinary | 6 | RNICA editable (`:9302`) | — | not emitted | No | optional | always | none | JSONB | additive | PRESENT AND CORRECTLY PLACED | |

#### 4.6.9 Musculoskeletal (ADL and mobility ownership excluded — see Screen 5)

| LS | LSub | Label | Code | Class | LRS | Path | Sec | Scr | Edit | RO | HH | SFV | Req | Cond | Val | Pers | Compat | Status | Notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Skin / MusculoSkeletal / Urinary | MSK | Weakness | — | SNS CLINICAL | None/Mild/Moderate/Severe/Paralysis | `musculoskeletal.weakness` | musculoskeletal | 6 | RNICA editable (`:9312`) | Screen 5 | not emitted | No | optional | always | none | JSONB | additive | PRESENT BUT RESPONSE SET INCOMPLETE | "Paralysis" as a severity value duplicates the separate `paralysis` field (`:9320`). |
| Skin / MusculoSkeletal / Urinary | MSK | Rigidity | — | SNS CLINICAL | None/Mild/Moderate/Severe | `musculoskeletal.rigidity` | musculoskeletal | 6 | RNICA editable (`:9313`) | — | not emitted | No | optional | always | none | JSONB | additive | PRESENT AND CORRECTLY PLACED | |
| Skin / MusculoSkeletal / Urinary | MSK | Rigidity Present (severity not documented) | — | SNS CLINICAL | boolean | `musculoskeletal.rigidityPresent` | musculoskeletal | 6 | RNICA editable (`:9314`) | — | not emitted | No | optional | always | none | JSONB | additive | CONFLICTING | A boolean companion to a graded field — two paths can disagree (e.g. `rigidity: "None"` + `rigidityPresent: true`) with no cross-validation. |
| Skin / MusculoSkeletal / Urinary | MSK | Contractures | — | SNS CLINICAL | None/Mild/Moderate/Severe | `musculoskeletal.contractures` | musculoskeletal | 6 | RNICA editable (`:9315`) | — | not emitted | No | optional | always | none | JSONB | additive | PRESENT AND CORRECTLY PLACED | |
| Skin / MusculoSkeletal / Urinary | MSK | Contractures Present (severity not documented) | — | SNS CLINICAL | boolean | `musculoskeletal.contracturesPresent` | musculoskeletal | 6 | RNICA editable (`:9316`) | — | not emitted | No | optional | always | none | JSONB | additive | CONFLICTING | Same boolean/graded conflict pattern. |
| Skin / MusculoSkeletal / Urinary | MSK | Contracture Location | — | SNS CLINICAL | 6 options | `musculoskeletal.contracturesLocation` | musculoskeletal | 6 | RNICA editable (`:9317`) | — | not emitted | No | optional | always | none | JSONB | additive | PRESENT AND CORRECTLY PLACED | |
| Skin / MusculoSkeletal / Urinary | MSK | ROM Loss Location | — | SNS CLINICAL | 5 options | `musculoskeletal.romLimitations` | musculoskeletal | 6 | RNICA editable (`:9318`) | — | not emitted | No | optional | always | none | JSONB | additive | CONFLICTING | "ROM loss" also appears as an option inside `musculoskeletalIssues` (`:9319`) — presence recorded in two places. |
| Skin / MusculoSkeletal / Urinary | MSK | Issues (Joint swelling, Spasms/cramps, Amputation, Prosthesis, ROM loss, None) | — | SNS CLINICAL | 6 options | `musculoskeletal.musculoskeletalIssues` | musculoskeletal | 6 | RNICA editable (`:9319`) | Screen 10 (prosthesis → DME) | not emitted | No | optional | always | none | JSONB | additive | PRESENT AND CORRECTLY PLACED | Covers legacy swelling / spasms / amputation / prosthesis in one multi-select. |
| Skin / MusculoSkeletal / Urinary | MSK | Disability (paralysis pattern) | — | SNS CLINICAL | None/Paraplegia/Quadriplegia/R hemiplegia/L hemiplegia/R hemiparesis/L hemiparesis | `musculoskeletal.paralysis` | musculoskeletal | 6 | RNICA editable (`:9320`) | Screen 6 neuro | not emitted | No | optional | always | none | JSONB | additive | CONFLICTING | Overlaps `neurological.deficitType` + `neurological.affectedSide` (`:9069-9070`). |
| Skin / MusculoSkeletal / Urinary | MSK | Strength | — | SNS CLINICAL | Normal/Decreased/Absent | `musculoskeletal.strength` | musculoskeletal | 6 | RNICA editable (`:9328`) | Screen 5 | not emitted | No | optional | always | none | JSONB | additive | PRESENT AND CORRECTLY PLACED | |
| Skin / MusculoSkeletal / Urinary | MSK | Balance | — | SNS CLINICAL | Normal/Impaired | `musculoskeletal.balance` | musculoskeletal | 6 | RNICA editable (`:9329`) | Screen 8 | not emitted | No | optional | always | none | JSONB | additive | CONFLICTING | Competing with `neurological.balance` (`:9041`). |
| Skin / MusculoSkeletal / Urinary | MSK | Pain with Movement | — | SNS CLINICAL | None/Mild/Moderate/Severe | `musculoskeletal.painWithMovement` | musculoskeletal | 6 | RNICA editable (`:9330`) | Screen 3 | not emitted | No | optional | always | none | JSONB | additive | PRESENT AND CORRECTLY PLACED | Does not compete with J2051A — it is movement-scoped, matching `pain.aggravatingFactors` "Movement". |
| Skin / MusculoSkeletal / Urinary | Falls | Falls in Last 90 Days | — | SNS CLINICAL | integer | `musculoskeletal.fallHistory.fallsLast90Days` | musculoskeletal | 8 (target) / 6 | RNICA editable (`:9333`) | Screen 8 | not emitted | No | optional | always | none | JSONB | additive | PRESENT BUT MISPLACED | Fall history is fall-risk evidence and belongs with Screen 8's fall-risk assessment. |
| Skin / MusculoSkeletal / Urinary | Falls | Fall Injuries | — | SNS CLINICAL | free text | `musculoskeletal.fallHistory.fallInjuries` | musculoskeletal | 8 | RNICA editable (`:9334`) | Screen 8 | not emitted | No | optional | always | none | JSONB | additive | PRESENT BUT MISPLACED | |
| Skin / MusculoSkeletal / Urinary | Notes | Musculoskeletal Notes | — | SNS CLINICAL | free text | `musculoskeletal.notes` | musculoskeletal | 6 | RNICA editable (`:9335`) | — | not emitted | No | optional | always | none | JSONB | additive | PRESENT AND CORRECTLY PLACED | |

#### 4.6.10 Skin / Wounds

| LS | LSub | Label | Code | Class | LRS | Path | Sec | Scr | Edit | RO | HH | SFV | Req | Cond | Val | Pers | Compat | Status | Notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Skin / MusculoSkeletal / Urinary | Skin | Skin Conditions Present | M1190 | HOPE | boolean | `skin.skinConditionsPresent` | skin | 6 | RNICA editable (`:9345`) | Screen 11 | `hopeReportMapper.js:625` | No | optional | always | none | JSONB | additive | VERIFIED COMPLETE | The genuine M1190 owner (contradicting the `performanceStatus` M1190 tag). |
| Skin / MusculoSkeletal / Urinary | Skin | Skin Status | M1195 | HOPE | Intact, Dry, Fragile, Edematous, Bruising, Rash, Jaundice, Cyanotic, Mottled | `skin.skinStatus` | skin | 6 | RNICA editable (`:9346`) | Screen 11 | `hopeReportMapper.js:626` (`arrayText` passthrough, no code lookup) | No | optional | always | none | JSONB | additive | PRESENT BUT RESPONSE SET INCOMPLETE | **Side-by-side vs. the legacy vocabulary described in the directive:** see §15 item 15. |
| Skin / MusculoSkeletal / Urinary | Skin | Skin Turgor | — | SNS CLINICAL | Good/Fair/Poor/Tenting | `skin.skinTurgor` | skin | 6 | RNICA editable (`:9347`) | — | not emitted | No | optional | always | none | JSONB | additive | PRESENT AND CORRECTLY PLACED | |
| Skin / MusculoSkeletal / Urinary | Braden | Sensory Perception | — | SNS CLINICAL | 1 Completely limited … 4 No impairment | `skin.braden.sensoryPerception` | skin | 6 | RNICA editable (`:9350`) | Screen 8 (read-only summary) | not emitted | No | optional | always | none | JSONB | additive | PRESENT AND CORRECTLY PLACED | |
| Skin / MusculoSkeletal / Urinary | Braden | Moisture | — | SNS CLINICAL | 1-4 | `skin.braden.moisture` | skin | 6 | RNICA editable (`:9351`) | Screen 8 | not emitted | No | optional | always | none | JSONB | additive | PRESENT AND CORRECTLY PLACED | |
| Skin / MusculoSkeletal / Urinary | Braden | Activity | — | SNS CLINICAL | 1 Bedfast / 2 Chairfast / 3 Walks occasionally / 4 Walks frequently | `skin.braden.activity` | skin | 6 | RNICA editable (`:9352`) | Screens 5, 8 | not emitted | No | optional | always | none | JSONB | additive | CONFLICTING | Overlaps `musculoskeletal.mobility.ambulatoryStatus` (`:9325`) — the only place "chairbound" is expressible. |
| Skin / MusculoSkeletal / Urinary | Braden | Mobility | — | SNS CLINICAL | 1-4 | `skin.braden.mobility` | skin | 6 | RNICA editable (`:9353`) | Screens 5, 8 | not emitted | No | optional | always | none | JSONB | additive | CONFLICTING | Overlaps Screen 5 mobility fields. |
| Skin / MusculoSkeletal / Urinary | Braden | Nutrition | — | SNS CLINICAL | 1 Very poor … 4 Excellent | `skin.braden.nutrition` | skin | 6 | RNICA editable (`:9354`) | Screens 6, 8 | not emitted | No | optional | always | none | JSONB | additive | CONFLICTING | Overlaps `nutrition.appetite` (`:9221`). |
| Skin / MusculoSkeletal / Urinary | Braden | Friction & Shear | — | SNS CLINICAL | 1 Problem / 2 Potential problem / 3 No apparent problem | `skin.braden.frictionShear` | skin | 6 | RNICA editable (`:9355`) | Screen 8 | not emitted | No | optional | always | none | JSONB | additive | PRESENT AND CORRECTLY PLACED | Correctly a 3-point subscale (Braden's friction/shear has no 4th level). |
| Skin / MusculoSkeletal / Urinary | Braden | **Braden total score** | — | COMPUTED RESULT | 6-23 | NOT FOUND IN REPOSITORY | — | 6 | — | Screen 8 | — | No | — | — | — | — | — | MISSING FROM SNS | No total is computed or persisted; only the interpretive band below is captured. |
| Skin / MusculoSkeletal / Urinary | Braden | Pressure Injury Risk | — | SNS CLINICAL | Low (19-23) / Moderate (15-18) / High (≤14) | `skin.pressureInjuryRisk` | skin | 6 | RNICA editable (`:9356`) | Screens 2, 8 | not emitted | No | optional | always | none | JSONB | additive | CONFLICTING | The band labels quote numeric Braden ranges, but the underlying total is never computed, so the clinician must sum six subscales mentally and pick a band that can silently disagree with them. |
| Skin / MusculoSkeletal / Urinary | Wounds | Wound stage (repeating row) | — | SNS CLINICAL | `WOUND_STAGE_OPTIONS` (`:2330`) | `skin.wounds[].stage` | skin | 6 | RNICA editable (`:2359`) | Screen 10 (supplies) | not emitted | No | optional | per wound row | none | JSONB array | additive | PRESENT AND CORRECTLY PLACED | |
| Skin / MusculoSkeletal / Urinary | Wounds | Wound Type | — | SNS CLINICAL | `WOUND_TYPE_OPTIONS` (`:2334`) | `skin.wounds[].woundType` | skin | 6 | RNICA editable (`:2360`) | — | not emitted | No | optional | per row | none | JSONB array | additive | PRESENT AND CORRECTLY PLACED | |
| Skin / MusculoSkeletal / Urinary | Wounds | Location | — | SNS CLINICAL | free text | `skin.wounds[].location` | skin | 6 | RNICA editable (`:2361`) | — | not emitted | No | optional | per row | none | JSONB array | additive | PRESENT AND CORRECTLY PLACED | |
| Skin / MusculoSkeletal / Urinary | Wounds | Length (cm) | — | SNS CLINICAL | numeric | `skin.wounds[].length` | skin | 6 | RNICA editable (`:2362`) | — | not emitted | No | optional | per row | none | JSONB array | additive | PRESENT AND CORRECTLY PLACED | |
| Skin / MusculoSkeletal / Urinary | Wounds | Width (cm) | — | SNS CLINICAL | numeric | `skin.wounds[].width` | skin | 6 | RNICA editable (`:2363`) | — | not emitted | No | optional | per row | none | JSONB array | additive | PRESENT AND CORRECTLY PLACED | |
| Skin / MusculoSkeletal / Urinary | Wounds | Depth (cm) | — | SNS CLINICAL | numeric | `skin.wounds[].depth` | skin | 6 | RNICA editable (`:2364`) | — | not emitted | No | optional | per row | none | JSONB array | additive | PRESENT AND CORRECTLY PLACED | |
| Skin / MusculoSkeletal / Urinary | Wounds | Drainage | — | SNS CLINICAL | None/Scant/Small/Moderate/Large | `skin.wounds[].drainage` | skin | 6 | RNICA editable (`:2365`) | — | not emitted | No | optional | per row | none | JSONB array | additive | PRESENT AND CORRECTLY PLACED | |
| Skin / MusculoSkeletal / Urinary | Wounds | Odor | — | SNS CLINICAL | None/Mild/Foul | `skin.wounds[].odor` | skin | 6 | RNICA editable (`:2366`) | — | not emitted | No | optional | per row | none | JSONB array | additive | PRESENT AND CORRECTLY PLACED | |
| Skin / MusculoSkeletal / Urinary | Wounds | Periwound Condition | — | SNS CLINICAL | free text | `skin.wounds[].periwoundCondition` | skin | 6 | RNICA editable (`:2367`) | — | not emitted | No | optional | per row | none | JSONB array | additive | PRESENT AND CORRECTLY PLACED | |
| Skin / MusculoSkeletal / Urinary | Wounds | Current Treatment | M1200 (contributes) | SNS CLINICAL | free text | `skin.wounds[].currentTreatment` | skin | 6 | RNICA editable (`:2380`) | Screen 10 | `hopeReportMapper.js:627` via `deriveSkinTreatments(skin)` (`:353-358`) | No | optional | per row | none | JSONB array | additive | PRESENT AND CORRECTLY PLACED | M1200 is derived, not directly entered — exact derivation inputs `NOT VERIFIED` beyond the function name. |
| Skin / MusculoSkeletal / Urinary | Wounds | Dressing | — | SNS CLINICAL | free text | `skin.wounds[].dressing` | skin | 6 | RNICA editable (`:2381`) | Screen 10 | contributes to M1200 | No | optional | per row | none | JSONB array | additive | PRESENT AND CORRECTLY PLACED | |
| Skin / MusculoSkeletal / Urinary | Wounds | Dressing Frequency | — | SNS CLINICAL | free text | `skin.wounds[].dressingFrequency` | skin | 6 | RNICA editable (`:2382`) | Screen 10 | contributes to M1200 | No | optional | per row | none | JSONB array | additive | PRESENT AND CORRECTLY PLACED | |
| Skin / MusculoSkeletal / Urinary | Wounds | Wound Impairment | — | SNS CLINICAL | free text | `skin.woundImpairment` | skin | 6 | RNICA editable (`:9363`) | — | not emitted | No | optional | always | none | JSONB | additive | CONFLICTING | Free-text duplicate of the structured wound list. |
| Skin / MusculoSkeletal / Urinary | Wounds | Pressure-Relief Measures | M1200 (contributes) | SNS CLINICAL | 6 options | `skin.pressureReliefMeasures` | skin | 6 | RNICA editable (`:9364`) | Screen 10 | contributes to `deriveSkinTreatments` | No | optional | always | none | JSONB | additive | PRESENT AND CORRECTLY PLACED | Options overlap DME items (pressure-relief mattress, cushioned seat) — see §19. |
| Skin / MusculoSkeletal / Urinary | Wounds | Repositioning Plan | — | SNS CLINICAL | free text | `skin.repositioningPlan` | skin | 6 | RNICA editable (`:9365`) | Screen 10 | contributes to M1200 | No | optional | always | none | JSONB | additive | PRESENT AND CORRECTLY PLACED | |
| Skin / MusculoSkeletal / Urinary | Notes | Skin Notes | — | SNS CLINICAL | free text | `skin.notes` | skin | 6 | RNICA editable (`:9366`) | — | not emitted | No | optional | always | none | JSONB | additive | PRESENT AND CORRECTLY PLACED | Legacy "observations". |
| Skin / MusculoSkeletal / Urinary | Skin | **Skin assessment link (to a separate wound-care document)** | — | NOT VERIFIED | link | NOT FOUND IN REPOSITORY | — | 6 | — | — | — | No | — | — | — | — | — | NOT FOUND IN REPOSITORY | No cross-document link field found in `SECTION_CONFIGS.skin`. |
| Skin / MusculoSkeletal / Urinary | Skin | Skin treatments | M1200 | HOPE | derived list | `deriveSkinTreatments(skin)` (`hopeReportMapper.js:353-358,627`) | skin | 6 | none (derived) | Screen 11 | `hopeReportMapper.js:627` | No | n/a | always | mapper | not persisted | n/a | PRESENT AND CORRECTLY PLACED | M1200 declared at `form_registry.py:405`. |

---
### 4.7 SCREEN 7 — Caregiver & Support

```
Frontend: RNICA.jsx:8030-8123 (PCG + Caregiver Willingness & Capability, inside renderDemographics)
Frontend: RNICA.jsx:8127-8166 (Living Situation card)
Frontend: RNICA.jsx:9474-9518 psychosocial · 9520-9543 spiritual · 9545-9564 bereavement
Frontend: RNICA.jsx:9566-9608 personalCare · 9610-9655 teachingNeeds · 9688-9707 referrals
Frontend: RNICA.jsx:203 SIDEBAR_CONFIG caregiverAssessment (parent demographics, scrollTarget "pcg", cdphRequired)
Taxonomy: rnicaThirteenScreenTaxonomy.js:73-79 caregiverSupport.moduleKeys
Backend:  backend/app/services/rnica_finalization_service.py:137-143 (referralsReviewed gate)
Exporter: sns-emr-frontend/src/intake/hopeReportMapper.js:493-494,576-577,589
```

#### 4.7.1 Primary Caregiver (PCG)

| LS | LSub | Label | Code | Class | LRS | Path | Sec | Scr | Edit | RO | HH | SFV | Req | Cond | Val | Pers | Compat | Status | Notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Vitals / … / PCG | PCG | Does this patient have a Primary Caregiver? | — | SNS CLINICAL | yes — has a PCG / no — facility-based care | `demographics.pcg.hasPcg` (radio at `:8031-8034`; exact key `NOT VERIFIED` — the `onChange` target was not visible in the extracted range) | demographics | 7 | RNICA editable | Screen 2 | not emitted | No | optional | always | none | JSONB | additive | PRESENT BUT MISPLACED | Lives in `renderDemographics()`, i.e. the `demographics` module, which `taxonomy:37` assigns to Screen 1. |
| Vitals / … / PCG | PCG | Facility / Care Setting | — | SNS CLINICAL | Memory Care/Board & Care/SNF/ALF/Other facility-based care | `demographics.pcg.noPcgReason` | demographics | 7 | RNICA editable (`:8041-8052`) | — | not emitted | No | optional | shown when there is no PCG | none | JSONB | additive | CONFLICTING | Overlaps A0215 Site of Service and A1905 Living Arrangement with a third, non-CMS vocabulary. |
| Vitals / … / PCG | PCG | PCG Name | — | SNS CLINICAL | free text | `demographics.pcg.name` | demographics | 7 | RNICA editable (`:8056`) | Screen 2 | not emitted | No | optional | PCG present | none | JSONB | additive | PRESENT BUT MISPLACED | |
| Vitals / … / PCG | PCG | Relationship | — | SNS CLINICAL | free text | `demographics.pcg.relationship` | demographics | 7 | RNICA editable (`:8057`) | Screen 2 | not emitted | No | optional | PCG present | none | JSONB | additive | PRESENT BUT MISPLACED | |
| Vitals / … / PCG | PCG | Phone | — | SNS CLINICAL | tel | `demographics.pcg.phone` | demographics | 7 | RNICA editable (`:8058`) | — | not emitted | No | optional | PCG present | none | JSONB | additive | PRESENT BUT MISPLACED | Distinct from `demographics.emergencyContact.phone`; may be the same person with no linkage. |
| Vitals / … / PCG | PCG | **PCG Health Status** | — | SNS CLINICAL | Good/Fair/Poor | `demographics.pcg.healthStatus` | demographics | 7 | RNICA editable (`:8060-8061`) | — | not emitted | No | optional | PCG present | none | JSONB | additive | PRESENT BUT MISPLACED | **Correction to earlier drafts: caregiver health exists.** |
| Vitals / … / PCG | PCG | **PCG Anxiety Level** | — | SNS CLINICAL | None/Mild/Moderate/Severe | `demographics.pcg.anxietyLevel` | demographics | 7 | RNICA editable (`:8062-8063`) | — | not emitted | No | optional | PCG present | none | JSONB | additive | PRESENT BUT MISPLACED | **Correction to earlier drafts: caregiver anxiety exists.** Distinct from patient J2051C. |
| Vitals / … / PCG | PCG | **Able to Administer Medications** | — | SNS CLINICAL | Yes/No/With training | `demographics.pcg.ableToAdministerMeds` | demographics | 7 | RNICA editable (`:8064-8065`) | Screen 8 | not emitted | No | optional | PCG present | none | JSONB | additive | PRESENT BUT MISPLACED | **Correction to earlier drafts: caregiver medication-administration capability exists.** This covers "responsible medication administrator (caregiver)" but **not** "patient medication self-administration ability" — see §15. |
| Vitals / … / PCG | PCG | Willing to Provide Care | — | SNS CLINICAL | Yes/No/Ambivalent | `demographics.pcg.willingToProvideCare` | demographics | 7 | RNICA editable (`:8066-8067`) | — | not emitted | No | optional | PCG present | none | JSONB | additive | PRESENT BUT MISPLACED | |
| Vitals / … / PCG | PCG | PCG Concerns / Notes | — | SNS CLINICAL | free text | `demographics.pcg.pcgConcerns` | demographics | 7 | RNICA editable (`:8068`) | — | not emitted | No | optional | PCG present | none | JSONB | additive | PRESENT BUT MISPLACED | |
| Vitals / … / PCG | Caregiver evaluation (CDPH) | Physical Ability to Perform Care Tasks | — | SNS CLINICAL | Fully capable/Capable with limitations/Limited capability/Unable | `demographics.pcg.caregiverEvaluation.physicalAbility` | demographics | 7 | RNICA editable (`:8083-8085`) | — | not emitted | No | optional | PCG present | none | JSONB | additive | PRESENT BUT MISPLACED | Card is marked `cms="CDPH Required"` (`:8078`). |
| Vitals / … / PCG | Caregiver evaluation | **Cognitive Ability to Follow Care Instructions** | — | SNS CLINICAL | Fully understands/Understands with reinforcement/Difficulty understanding/Unable to understand | `demographics.pcg.caregiverEvaluation.cognitiveAbility` | demographics | 7 | RNICA editable (`:8086-8088`) | — | not emitted | No | optional | PCG present | none | JSONB | additive | PRESENT BUT MISPLACED | **This is the SNS equivalent of legacy "caregiver ability to participate / understand".** |
| Vitals / … / PCG | Caregiver evaluation | Emotional Readiness for Caregiving Role | — | SNS CLINICAL | Ready and engaged/Ambivalent but willing/Reluctant/Overwhelmed-resistant | `demographics.pcg.caregiverEvaluation.emotionalReadiness` | demographics | 7 | RNICA editable (`:8089-8091`) | — | not emitted | No | optional | PCG present | none | JSONB | additive | PRESENT BUT MISPLACED | |
| Vitals / … / PCG | Caregiver evaluation | Hours/Day Available for Care | — | SNS CLINICAL | 24/7, 16-23, 8-15, 4-7, <4, Not available | `demographics.pcg.caregiverEvaluation.availabilityForCare` | demographics | 7 | RNICA editable (`:8092-8094`) | — | not emitted | No | optional | PCG present | none | JSONB | additive | CONFLICTING | Overlaps A1910 Availability of Assistance (`:8163-8164`), which is the HOPE-authoritative field with a different vocabulary (24/7 available, Daytime only, Nighttime only, Limited, None). |
| Vitals / … / PCG | Caregiver evaluation | Training Needs Identified | — | SNS CLINICAL | Medication administration/Wound care/Symptom management/Emergency procedures/… | `demographics.pcg.caregiverEvaluation.trainingNeeds` | demographics | 7 | RNICA editable (`:8095-8097`) | Screen 7 teaching | not emitted | No | optional | PCG present | none | JSONB | additive | CONFLICTING | **This is the closest existing thing to the legacy "PCG education checklist"**, but it overlaps `teachingNeeds.teachingTopics` (`:9623-9637`), which is the fuller list. Two competing education checklists. |
| Vitals / … / PCG | Caregiver evaluation | Willingness Score (1-5) | — | COMPUTED RESULT (manually scored) | 1 Unwilling … 5 Fully committed | `demographics.pcg.caregiverEvaluation.willingnessScore` | demographics | 7 | RNICA editable (`:8101-8107`) | — | not emitted | No | optional | PCG present | none | JSONB | additive | CONFLICTING | Hand-scored duplicate of `pcg.willingToProvideCare` + `emotionalReadiness`; no computation ties them together. |
| Vitals / … / PCG | Caregiver evaluation | Capability Score (1-5) | — | COMPUTED RESULT (manually scored) | 1 Unable … 5 Fully capable | `demographics.pcg.caregiverEvaluation.capabilityScore` | demographics | 7 | RNICA editable (`:8108-8114`) | — | not emitted | No | optional | PCG present | none | JSONB | additive | CONFLICTING | Hand-scored duplicate of `physicalAbility` + `cognitiveAbility`. |
| Vitals / … / PCG | Caregiver evaluation | Support System Adequacy | — | SNS CLINICAL | Adequate/Inadequate/Needs reinforcement | `demographics.pcg.caregiverEvaluation.supportSystemAdequacy` | demographics | 7 | RNICA editable (`:8115-8117`) | — | not emitted | No | optional | PCG present | none | JSONB | additive | CONFLICTING | Overlaps `psychosocial.familySocialSupport` (`:9479`). |
| Vitals / … / PCG | Caregiver evaluation | Caregiver Evaluation Notes | — | SNS CLINICAL | free text | `demographics.pcg.caregiverEvaluation.evaluationNotes` | demographics | 7 | RNICA editable (`:8119-8121`) | — | not emitted | No | optional | PCG present | none | JSONB | additive | PRESENT BUT MISPLACED | |
| Vitals / … / PCG | Living | Living Arrangement | A1905 | HOPE | 1 Alone / 2 With others / 3 Congregate home / 4 Inpatient facility / 5 No permanent home | `demographics.livingSituation.livingArrangement` | demographics | 7 | RNICA editable (`:8155-8162`) | Screens 1, 2 | `hopeReportMapper.js:493,576` via `LIVING_ARRANGEMENT_LABELS` (`:94-122`) + legacy remap | No | optional | always | code-map fallback | JSONB | legacy label values remapped | PRESENT BUT MISPLACED | Correct 5-code CMS set; wrong screen per the directive. |
| Vitals / … / PCG | Living | Availability of Assistance | A1910 | HOPE | 24/7 available/Daytime only/Nighttime only/Limited/None | `demographics.livingSituation.availabilityOfAssistance` | demographics | 7 | RNICA editable (`:8163-8164`) | Screens 1, 2 | `hopeReportMapper.js:494,577` via `ASSISTANCE_MAP` | No | optional | always | `lookup()` (no legacy remap) | JSONB | additive | PRESENT BUT MISPLACED | Unlike A0215/A1805/A1905, this uses plain `lookup()` rather than `officialCodeLookup()`, so whether the emitted codes are the official CMS A1910 codes is `NOT VERIFIED`. |
| Vitals / … / Comms | Communication | **Patient ability to understand / participate in own care** | — | SNS CLINICAL | n/a | NOT FOUND IN REPOSITORY | — | 7 | — | — | — | No | — | — | — | — | — | MISSING FROM SNS | The caregiver equivalent exists (`caregiverEvaluation.cognitiveAbility`); the **patient** equivalent does not. `neurological.communication` and `neurological.cognition` describe capability but not participation in the plan of care. |
| Vitals / … / Comms | Communication | **Interpreter need beyond A1110 (offered / declined / provided)** | — | SNS CLINICAL | n/a | partially covered by `demographics.needsInterpreter` (`:7999`) and `teachingNeeds.teachingMethods` option "Interpreter used" (`:9643`) | demographics / teachingNeeds | 7 | RNICA editable | — | A1110B only | No | optional | always | none | JSONB | additive | PRESENT BUT RESPONSE SET INCOMPLETE | Need and use are captured; *offered/declined* is not. |
| Vitals / … / Comms | Communication | **Caregiver communication need** | — | SNS CLINICAL | n/a | NOT FOUND IN REPOSITORY | — | 7 | — | — | — | No | — | — | — | — | — | MISSING FROM SNS | `neurological.hearing`/`.communication` are patient-scoped. |
| Vitals / … / Comms | Communication | **Hearing / sign-language need** | — | SNS CLINICAL | n/a | partially `neurological.hearing` (`:9039`) | neurological | 7 | RNICA editable | — | not emitted | No | optional | always | none | JSONB | additive | PRESENT BUT RESPONSE SET INCOMPLETE | Sign language is not an option in `hearing`, in `preferredLanguage` (`:7998`), or in `teachingMethods`. |
| Vitals / … / Comms | Communication | **Responsible-party information** | — | SNS CLINICAL | n/a | partially `demographics.advancedCarePlanning.decisionMaker` / `.poaName` / `.poaPhone` (`:8194-8196`) | demographics | 9 (ACP) | RNICA editable | Screen 7 | not emitted | No | optional | always | none | JSONB | additive | PRESENT AND CORRECTLY PLACED | Correctly owned by ACP; Screen 7 should cross-reference read-only. |
| Vitals / … / Comms | Communication | **Patient medication self-administration ability** | — | SNS CLINICAL | n/a | NOT FOUND IN REPOSITORY | — | 8 (safety) / 7 | — | — | — | No | — | — | — | — | — | MISSING FROM SNS | Only the *caregiver* capability exists (`pcg.ableToAdministerMeds`). |
| Vitals / … / Other Factors | Other factors | **Special event / desire before dying** | — | SNS CLINICAL | n/a | NOT FOUND IN REPOSITORY | — | 7 | — | — | — | No | — | — | — | — | — | MISSING FROM SNS | Nearest: `psychosocial.patientConcerns` option "Unfinished business" (`:9489`) and `personalCare.volunteerServices` option "Legacy project" (`:9588`) — neither is a wish/desire field. |
| Vitals / … / Other Factors | Other factors | **Young children in home** | — | SNS CLINICAL | n/a | NOT FOUND IN REPOSITORY | — | 7 | — | — | — | No | — | — | — | — | — | MISSING FROM SNS | Nearest: `psychosocial.caregiverFamilyConcerns` option "Children/family coping" (`:9498`), which is a concern, not a household-composition fact. |
| Vitals / … / Other Factors | Other factors | **Pets in home** | — | SNS CLINICAL | n/a | present only as a *hazard* — `safety.homeEnvironment` option "Pets" (`:9428`) | safety | 8 | RNICA editable | Screen 7 | not emitted | No | optional | always | none | JSONB | additive | PRESENT BUT MISPLACED | Recorded as an environmental hazard rather than a caregiving/psychosocial fact. Related: `personalCare.volunteerServices` option "Pet care" (`:9588`). |

#### 4.7.2 Psychosocial

| LS | LSub | Label | Code | Class | LRS | Path | Sec | Scr | Edit | RO | HH | SFV | Req | Cond | Val | Pers | Compat | Status | Notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| (no legacy screen described) | Social support | Family/Social Support Level | — | SNS CLINICAL | Strong/Adequate/Limited/No support/Declined to answer | `psychosocial.familySocialSupport` | psychosocial | 7 | RNICA editable (`:9479`) | Screen 2 | not emitted | No | optional | always | none | JSONB | additive | VERIFIED COMPLETE | Includes an explicit "Declined to answer" value. |
| (no legacy screen described) | Social support | Primary Support Person | — | SNS CLINICAL | free text | `psychosocial.primarySupportPerson` | psychosocial | 7 | RNICA editable (`:9480`) | — | not emitted | No | optional | always | none | JSONB | additive | CONFLICTING | Third name field for what is usually the same person (`pcg.name`, `emergencyContact.name`). |
| (no legacy screen described) | Social support | Relationship | — | SNS CLINICAL | free text | `psychosocial.supportRelationship` | psychosocial | 7 | RNICA editable (`:9481`) | — | not emitted | No | optional | always | none | JSONB | additive | CONFLICTING | Same. |
| Bereavement / Referrals / Spiritual | Patient concerns | Patient Concerns (24 options incl. acceptance, coping, adherence, substance use, suicide, legal/financial, cultural, burial, advance-directive help, funeral-planning help) | — | SNS CLINICAL | None indicated, Anxiety about illness, Depression, Grief/loss, Financial concerns, Family conflict, Caregiver burden, Social isolation, Role changes, Unfinished business, Fear of dying, Loss of independence, Body image concerns, Non-acceptance of diagnosis, Potential for non-compliance, Lack of coping skills, Suicide concerns, Substance abuse concerns, History of emotional illness, Cultural concerns, Burial concerns, Anger, Want/need help with advance directives, Want/need help with funeral plans | `psychosocial.patientConcerns` | psychosocial | 7 | RNICA editable (`:9484-9493`) | Screen 2 | not emitted | No | optional | always | none | JSONB | additive | VERIFIED COMPLETE | **Every legacy psychosocial concept named in the directive — acceptance, coping, anxiety/mood, adherence, substance use, suicide, legal/financial, family strain, cultural/burial, advance-directive help, funeral-planning help — maps into this one multi-select.** Includes an explicit "None indicated" value, which is the correct pattern the functional scales lack. |
| (no legacy screen described) | Caregiver concerns | Caregiver Concerns | — | SNS CLINICAL | Anticipatory grief, Caregiver fatigue, Financial stress, Work-life balance, Children/family coping, Funeral planning, Estate/legal matters | `psychosocial.caregiverFamilyConcerns` | psychosocial | 7 | RNICA editable (`:9496-9499`) | — | not emitted | No | optional | always | none | JSONB | additive | PRESENT AND CORRECTLY PLACED | Covers legacy "family strain". |
| (no legacy screen described) | Distress | Distress Thermometer (0-10) | — | SNS CLINICAL | 0-10 | `psychosocial.distressRating` | psychosocial | 7 | RNICA editable (`:9502`) | Screen 2 | not emitted | No | optional | always | none | JSONB | additive | PRESENT AND CORRECTLY PLACED | |
| (no legacy screen described) | Distress | Psychosocial History | — | SNS CLINICAL | 6 options | `psychosocial.psychosocialHistory` | psychosocial | 7 | RNICA editable (`:9503-9506`) | Screen 6 | not emitted | No | optional | always | none | JSONB | additive | CONFLICTING | Overlaps `neurological.psychiatricHistoryType` (`:9051`). |
| (no legacy screen described) | Distress | Coping Assessment | — | SNS CLINICAL | Effective/Developing/Ineffective/Crisis | `psychosocial.copingAssessment` | psychosocial | 7 | RNICA editable (`:9507`) | — | not emitted | No | optional | always | none | JSONB | additive | PRESENT AND CORRECTLY PLACED | |
| (no legacy screen described) | Distress | Coping Notes | — | SNS CLINICAL | free text | `psychosocial.copingNotes` | psychosocial | 7 | RNICA editable (`:9508`) | — | not emitted | No | optional | always | none | JSONB | additive | PRESENT AND CORRECTLY PLACED | |
| (no legacy screen described) | Intervention | Interventions | — | SNS CLINICAL | Counseling referral/Support group/Community resources/Crisis intervention/Psychiatric evaluation | `psychosocial.interventionPlan` | psychosocial | 7 | RNICA editable (`:9511-9513`) | Screen 10 | not emitted | No | optional | always | none | JSONB | additive | CONFLICTING | "Counseling referral" and "Community resources" duplicate the `referrals` module and `personalCare.communityResources`. |
| (no legacy screen described) | Intervention | Social Work Visit Needed | — | REFERRAL | boolean | `psychosocial.socialWorkVisitNeeded` | psychosocial | 7 | RNICA editable (`:9514`) | — | not emitted | No | optional | always | none | JSONB | additive | CONFLICTING | Duplicates `referrals.socialWork.referred` (`:9693`) — the field that actually gates Lock readiness. |
| (no legacy screen described) | Notes | Psychosocial Notes | — | SNS CLINICAL | free text | `psychosocial.notes` | psychosocial | 7 | RNICA editable (`:9515`) | — | not emitted | No | optional | always | none | JSONB | additive | PRESENT AND CORRECTLY PLACED | |

#### 4.7.3 Spiritual

| LS | LSub | Label | Code | Class | LRS | Path | Sec | Scr | Edit | RO | HH | SFV | Req | Cond | Val | Pers | Compat | Status | Notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Bereavement / Referrals / Spiritual | Spiritual | Patient Active in Faith Tradition | — | SNS CLINICAL | boolean | `spiritual.patientActiveInFaithTradition` | spiritual | 7 | RNICA editable (`:9525`) | — | not emitted | No | optional | always | none | JSONB | additive | PRESENT AND CORRECTLY PLACED | |
| Bereavement / Referrals / Spiritual | Spiritual | Patient Faith Tradition | — | SNS CLINICAL | free text | `spiritual.patientFaith` | spiritual | 7 | RNICA editable (`:9526`) | — | not emitted | No | optional | always | none | JSONB | additive | CONFLICTING | Duplicates `demographics.religion` (`:8000`). |
| Bereavement / Referrals / Spiritual | Spiritual | Caregiver Active in Faith Tradition | — | SNS CLINICAL | boolean | `spiritual.caregiverActiveInFaithTradition` | spiritual | 7 | RNICA editable (`:9527`) | — | not emitted | No | optional | always | none | JSONB | additive | PRESENT AND CORRECTLY PLACED | |
| Bereavement / Referrals / Spiritual | Spiritual | Caregiver Faith Tradition | — | SNS CLINICAL | free text | `spiritual.caregiverFaith` | spiritual | 7 | RNICA editable (`:9528`) | — | not emitted | No | optional | always | none | JSONB | additive | PRESENT AND CORRECTLY PLACED | |
| Bereavement / Referrals / Spiritual | Spiritual | Spiritual Concerns | — | SNS CLINICAL | Meaning of illness, Forgiveness, Hope, Legacy, Prayer requests, Religious rituals, Afterlife concerns, Anger at God, Spiritual distress, Fear, Hopelessness | `spiritual.spiritualConcerns` | spiritual | 7 | RNICA editable (`:9529-9533`) | Screen 11 | feeds F3000 legacy indicator (`hopeReportMapper.js:509`) | No | optional | always | none | JSONB | additive | PRESENT AND CORRECTLY PLACED | Covers legacy "spiritual distress". |
| Bereavement / Referrals / Spiritual | Spiritual | Spiritual Distress Rating (0-10) | — | SNS CLINICAL | 0-10 | `spiritual.spiritualDistressRating` | spiritual | 7 | RNICA editable (`:9534`) | — | not emitted | No | optional | always | none | JSONB | additive | PRESENT AND CORRECTLY PLACED | |
| Bereavement / Referrals / Spiritual | Spiritual | Spiritual / existential concerns asked | F3000 (legacy indicator) | HOPE | boolean | `spiritual.concernsDiscussed` | spiritual | 7 | RNICA editable (`:9535`) | Screen 11 | `hopeReportMapper.js:509-510` (legacy fallback for F3000A) | No | optional | always | `askedStatus()` | JSONB | acts as the back-compat signal for records predating `concernsAskedStatus` | PRESENT AND CORRECTLY PLACED | Good existing-data-compatibility pattern: the older boolean still satisfies F3000A when the newer coded field is blank. |
| Bereavement / Referrals / Spiritual | Spiritual | F3000: Was patient and/or caregiver asked about spiritual/existential concerns? | F3000 | HOPE | 0 No / 1 Yes, and discussion occurred / 2 Yes, but refused to discuss | `spiritual.concernsAskedStatus` | spiritual | 7 | RNICA editable (`:9536-9537`) | Screen 11 | `hopeReportMapper.js:510,589` | No | optional | always | `askedStatus()`; incompleteness surfaces in `legacyReviewItems` (`:516`) | JSONB | see above | VERIFIED COMPLETE | Includes the "declined to discuss" response the directive requires. Declared at `form_registry.py:368`. |
| Bereavement / Referrals / Spiritual | Spiritual | Spiritual concerns discussion date | F3000B | HOPE | date | `spiritual.concernsDiscussedDate` | spiritual | 7 | RNICA editable (`:9538`) | — | `hopeReportMapper.js:589` | No | optional | always | none | JSONB | additive | PRESENT AND CORRECTLY PLACED | |
| Bereavement / Referrals / Spiritual | Spiritual | Chaplain Referral Needed | — | REFERRAL | boolean | `spiritual.chaplainNeeded` | spiritual | 7 | RNICA editable (`:9539`) | — | not emitted | No | optional | always | none | JSONB | additive | CONFLICTING | Duplicates `referrals.spiritualCare.referred` (`:9695`). |
| Bereavement / Referrals / Spiritual | Spiritual | Spiritual Notes | — | SNS CLINICAL | free text | `spiritual.notes` | spiritual | 7 | RNICA editable (`:9540`) | — | feeds F3000 legacy indicator (`:509`) | No | optional | always | none | JSONB | additive | PRESENT AND CORRECTLY PLACED | |

#### 4.7.4 Bereavement

| LS | LSub | Label | Code | Class | LRS | Path | Sec | Scr | Edit | RO | HH | SFV | Req | Cond | Val | Pers | Compat | Status | Notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Bereavement / Referrals / Spiritual | Bereavement | Patient Concerns | — | SNS CLINICAL | Fear of death, Unresolved grief, Existential distress, Legacy concerns, Family preparedness, **Multiple losses**, **Active grieving** | `bereavement.patientConcerns` | bereavement | 7 | RNICA editable (`:9550-9553`) | — | not emitted | No | optional | always | none | JSONB | additive | VERIFIED COMPLETE | Covers the legacy "multiple loss" and "active grieving" concepts for the patient. |
| Bereavement / Referrals / Spiritual | Bereavement | Caregiver Concerns | — | SNS CLINICAL | Anticipatory grief, Previous losses, Complicated grief history, Mental health concerns, Substance abuse history, Social isolation, Concurrent stressors, **Multiple losses**, **Active grieving** | `bereavement.caregiverConcerns` | bereavement | 7 | RNICA editable (`:9554-9558`) | — | not emitted | No | optional | always | none | JSONB | additive | VERIFIED COMPLETE | Same for the caregiver. |
| Bereavement / Referrals / Spiritual | Bereavement | Bereavement Risk Level | — | SNS CLINICAL | Low/Moderate/High | `bereavement.bereavementRisk` | bereavement | 7 | RNICA editable (`:9559`) | Screen 2 | not emitted | No | optional | always | none | JSONB | additive | PRESENT AND CORRECTLY PLACED | Manually assigned; no scoring engine, which is correct per the directive's "no new scoring" rule. |
| Bereavement / Referrals / Spiritual | Bereavement | Bereavement Visit Needed | — | REFERRAL | boolean | `bereavement.bereavementVisitNeeded` | bereavement | 7 | RNICA editable (`:9560`) | — | not emitted | No | optional | always | none | JSONB | additive | PRESENT BUT NOT WIRED | No corresponding entry in the `referrals` module, so this need never reaches the referral-review gate. |
| Bereavement / Referrals / Spiritual | Bereavement | Bereavement Notes | — | SNS CLINICAL | free text | `bereavement.notes` | bereavement | 7 | RNICA editable (`:9561`) | — | not emitted | No | optional | always | none | JSONB | additive | PRESENT AND CORRECTLY PLACED | |

#### 4.7.5 Personal Care & Support Needs

| LS | LSub | Label | Code | Class | LRS | Path | Sec | Scr | Edit | RO | HH | SFV | Req | Cond | Val | Pers | Compat | Status | Notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Personal Care / Environmental-Safety | Aide | Aide Tasks Needed (hospice-aide needs, grooming, linen change, meal prep, caregiver relief) | — | SNS CLINICAL | None, Bathing/showering, Hair care/grooming, Oral hygiene, Skin care, Dressing, Toileting assistance, Transfers/mobility, Light meal preparation, Light housekeeping, Laundry, **Linen change**, Vital signs, Range of motion exercises, **Respite for caregiver**, See ADL assessment for other needs | `personalCare.aideTasks` | personalCare | 7 | RNICA editable (`:9571-9577`) | Screen 10 (CHHA POC) | not emitted | No | optional | always | none | JSONB | additive | VERIFIED COMPLETE | Every legacy aide-task concept named in the directive is present, including linen change, meal prep, grooming and caregiver relief. The explicit "See ADL assessment for other needs" option is the deliberate cross-reference to Screen 5. |
| Personal Care / Environmental-Safety | Aide | Frequency | — | ORDER/POC | Daily/3x week/2x week/Weekly/PRN | `personalCare.aideVisitPreferences.frequency` | personalCare | 10 (target) / 7 | RNICA editable (`:9580`) | Screen 10 | not emitted | No | optional | always | none | JSONB | additive | CONFLICTING | Visit frequency is an order concept; it competes with `admissionsOrder` `disciplineFrequencyOfVisit` rows (`:3263-3300`, `:9669`). |
| Personal Care / Environmental-Safety | Aide | Preferred Time | — | SNS CLINICAL | Morning/Afternoon/Evening/Flexible | `personalCare.aideVisitPreferences.preferredTime` | personalCare | 7 | RNICA editable (`:9581`) | Screen 10 | not emitted | No | optional | always | none | JSONB | additive | PRESENT AND CORRECTLY PLACED | |
| Personal Care / Environmental-Safety | Aide | Duration | — | SNS CLINICAL | 1-4 hours | `personalCare.aideVisitPreferences.duration` | personalCare | 7 | RNICA editable (`:9582`) | Screen 10 | not emitted | No | optional | always | none | JSONB | additive | PRESENT AND CORRECTLY PLACED | |
| Bereavement / Referrals / Spiritual | Volunteer | Volunteer Services Needed (companionship, errands, respite) | — | SNS CLINICAL | None, **Companionship/visits**, **Respite care**, **Errand assistance**, Transportation, Vigil/11th hour, Pet care, Legacy project, Music/art therapy, Reading/letter writing | `personalCare.volunteerServices` | personalCare | 7 | RNICA editable (`:9585-9589`) | — | not emitted | No | optional | always | none | JSONB | additive | VERIFIED COMPLETE | Covers legacy volunteer support, companionship, errands and caregiver relief. Also covers the legacy "music/art/pet therapy" referral types that the `referrals` module lacks. |
| Personal Care / Environmental-Safety | Community | Community Resources Needed (meals, transportation) | — | SNS CLINICAL | None, **Meals on Wheels**, Adult day care, **Transportation services**, Legal aid, Financial assistance programs, Faith community support, Veteran services, Disease-specific organizations | `personalCare.communityResources` | personalCare | 7 | RNICA editable (`:9592-9596`) | — | not emitted | No | optional | always | none | JSONB | additive | VERIFIED COMPLETE | Covers legacy "community support", "meals" and "transportation". "Veteran services" pairs with `demographics.militaryService`. |
| Personal Care / Environmental-Safety | Equipment | Equipment Needed | — | ORDER/POC | 19 options (Hospital bed … E-tank) | `personalCare.equipmentSupplyNeeds` | personalCare | 10 (target) / 7 | RNICA editable (`:9599-9604`) | Screen 10 | not emitted | No | optional | always | none | JSONB | additive | CONFLICTING | Third equipment list, alongside `safety.dmeItems` (`DmeStatusCard`) and `musculoskeletal.assistiveDevices`. Directive: DME indication ≠ DME order. |
| Personal Care / Environmental-Safety | Notes | Personal Care Notes | — | SNS CLINICAL | free text | `personalCare.notes` | personalCare | 7 | RNICA editable (`:9605`) | — | not emitted | No | optional | always | none | JSONB | additive | PRESENT AND CORRECTLY PLACED | Legacy "comments". |

#### 4.7.6 Teaching Needs

| LS | LSub | Label | Code | Class | LRS | Path | Sec | Scr | Edit | RO | HH | SFV | Req | Cond | Val | Pers | Compat | Status | Notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| (no legacy screen described) | Teaching | Primary Learner | — | SNS CLINICAL | Patient/Caregiver/Both | `teachingNeeds.primaryLearner` | teachingNeeds | 7 | RNICA editable (`:9615`) | — | not emitted | No | optional | always | none | JSONB | additive | PRESENT AND CORRECTLY PLACED | |
| (no legacy screen described) | Teaching | Learning Style Preference | — | SNS CLINICAL | Visual/Auditory/Hands-on/Written materials | `teachingNeeds.learningStylePreference` | teachingNeeds | 7 | RNICA editable (`:9616`) | — | not emitted | No | optional | always | none | JSONB | additive | PRESENT AND CORRECTLY PLACED | |
| (no legacy screen described) | Teaching | Barriers to Learning | — | SNS CLINICAL | Language, Literacy, Cognitive impairment, Hearing deficit, Vision deficit, Emotional readiness, Cultural considerations, Denial of diagnosis | `teachingNeeds.barriersToLearning` | teachingNeeds | 7 | RNICA editable (`:9617-9620`) | — | not emitted | No | optional | always | none | JSONB | additive | PRESENT AND CORRECTLY PLACED | "Language" and "Hearing deficit" partially compensate for the missing caregiver-communication fields. |
| Vitals / … / Other Factors | Teaching | Teach Patient/Family/PCG — topics | — | SNS CLINICAL | **Diagnosis and disease process**, **Medication administration**, Medication side effects, Medication contraindications, Comfort pack use, Opioid use and risk, **Medication reconciliation**, **Oxygen**, **DME (durable medical equipment)**, **Infection control**, Universal precautions, **Safe use and disposal of controlled medications**, **Other education** | `teachingNeeds.teachingTopics` | teachingNeeds | 7 | RNICA editable (`:9623-9637`) | — | not emitted | No | optional | always | none | JSONB | additive | PRESENT BUT RESPONSE SET INCOMPLETE | **Directly answers the directive's teaching checklist**: diagnosis/disease process ✓, medications ✓, reconciliation ✓, oxygen ✓, DME ✓, infection control ✓, medication disposal ✓, other ✓. The one named legacy topic **absent** is *advance directives* — that appears only as a `psychosocial.patientConcerns` option ("Want/need help with advance directives"), not as a teaching topic. |
| Vitals / … / Other Factors | Teaching | Other Topic (specify) | — | SNS CLINICAL | free text | `teachingNeeds.teachingTopicsOther` | teachingNeeds | 7 | RNICA editable (`:9638`) | — | not emitted | No | optional | always | none | JSONB | additive | PRESENT AND CORRECTLY PLACED | |
| (no legacy screen described) | Teaching | Methods | — | SNS CLINICAL | Verbal instruction, Written materials provided, Demonstration, Return demonstration, Video/multimedia, Interpreter used | `teachingNeeds.teachingMethods` | teachingNeeds | 7 | RNICA editable (`:9641-9644`) | — | not emitted | No | optional | always | none | JSONB | additive | PRESENT AND CORRECTLY PLACED | |
| (no legacy screen described) | Teaching | Patient/Family Response | — | SNS CLINICAL | Verbalized understanding, Demonstrated competency, Needs reinforcement, Unable to learn at this time, Refused teaching | `teachingNeeds.patientFamilyResponse` | teachingNeeds | 7 | RNICA editable (`:9647-9650`) | — | not emitted | No | optional | always | none | JSONB | additive | VERIFIED COMPLETE | |
| (no legacy screen described) | Teaching | Follow-up Plan | — | SNS CLINICAL | free text | `teachingNeeds.followUpPlan` | teachingNeeds | 7 | RNICA editable (`:9651`) | — | not emitted | No | optional | always | none | JSONB | additive | PRESENT AND CORRECTLY PLACED | |
| (no legacy screen described) | Teaching | Teaching Notes | — | SNS CLINICAL | free text | `teachingNeeds.notes` | teachingNeeds | 7 | RNICA editable (`:9652`) | — | not emitted | No | optional | always | none | JSONB | additive | PRESENT AND CORRECTLY PLACED | |

#### 4.7.7 Referrals (relocation target — see §17)

| LS | LSub | Label | Code | Class | LRS | Path | Sec | Scr | Edit | RO | HH | SFV | Req | Cond | Val | Pers | Compat | Status | Notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Bereavement / Referrals / Spiritual | Referrals | Social Work Referral | — | REFERRAL | boolean | `referrals.socialWork.referred` | referrals | 7 | RNICA editable (`:9693`) | Screen 11 | not emitted | No | optional | always | none | JSONB | additive | PRESENT BUT MISPLACED | Currently grouped under `evidenceIntake` (`taxonomy:37`). |
| Bereavement / Referrals / Spiritual | Referrals | SW Reason | — | REFERRAL | free text | `referrals.socialWork.reason` | referrals | 7 | RNICA editable (`:9694`) | — | not emitted | No | optional | always | none | JSONB | additive | PRESENT BUT MISPLACED | |
| Bereavement / Referrals / Spiritual | Referrals | Spiritual Care Referral | — | REFERRAL | boolean | `referrals.spiritualCare.referred` | referrals | 7 | RNICA editable (`:9695`) | Screen 11 | not emitted | No | optional | always | none | JSONB | additive | PRESENT BUT MISPLACED | |
| Bereavement / Referrals / Spiritual | Referrals | SC Reason | — | REFERRAL | free text | `referrals.spiritualCare.reason` | referrals | 7 | RNICA editable (`:9696`) | — | not emitted | No | optional | always | none | JSONB | additive | PRESENT BUT MISPLACED | |
| Bereavement / Referrals / Spiritual | Referrals | Volunteer Referral | — | REFERRAL | boolean | `referrals.volunteer.referred` | referrals | 7 | RNICA editable (`:9697`) | — | not emitted | No | optional | always | none | JSONB | additive | PRESENT BUT MISPLACED | |
| Bereavement / Referrals / Spiritual | Referrals | Volunteer Type | — | REFERRAL | free text | `referrals.volunteer.type` | referrals | 7 | RNICA editable (`:9698`) | — | not emitted | No | optional | always | none | JSONB | additive | PRESENT BUT MISPLACED | |
| Bereavement / Referrals / Spiritual | Referrals | Dietitian Referral | — | REFERRAL | boolean | `referrals.dietitian.referred` | referrals | 7 | RNICA editable (`:9699`) | — | not emitted | No | optional | always | none | JSONB | additive | PRESENT BUT MISPLACED | |
| Bereavement / Referrals / Spiritual | Referrals | Dietitian Reason | — | REFERRAL | free text | `referrals.dietitian.reason` | referrals | 7 | RNICA editable (`:9700`) | — | not emitted | No | optional | always | none | JSONB | additive | PRESENT BUT MISPLACED | |
| Bereavement / Referrals / Spiritual | Referrals | Pharmacist Referral | — | REFERRAL | boolean | `referrals.pharmacist.referred` | referrals | 7 | RNICA editable (`:9701`) | — | not emitted | No | optional | always | none | JSONB | additive | PRESENT BUT MISPLACED | |
| Bereavement / Referrals / Spiritual | Referrals | Pharmacist Reason | — | REFERRAL | free text | `referrals.pharmacist.reason` | referrals | 7 | RNICA editable (`:9702`) | — | not emitted | No | optional | always | none | JSONB | additive | PRESENT BUT MISPLACED | |
| Bereavement / Referrals / Spiritual | Referrals | Referral Notes | — | REFERRAL | free text | `referrals.notes` | referrals | 7 | RNICA editable (`:9703`) | — | not emitted | No | optional | always | none | JSONB | additive | PRESENT BUT MISPLACED | |
| Bereavement / Referrals / Spiritual | Referrals | I reviewed the referral status … current and complete | — | READINESS | boolean | `referrals.reviewed` | referrals | 7 | RNICA editable (`:9704`) | Screens 11, 13 | not emitted | No | **gates Lock** | always | `evaluate_finalization_readiness` `referralsReviewed` (`rnica_finalization_service.py:137-143`) | JSONB | additive | PRESENT BUT MISPLACED | Relocation must preserve `FINALIZATION_CHECK_SECTION_MAP.referralsReviewed = "referrals"` (`RNICA.jsx:237`). |
| Bereavement / Referrals / Spiritual | Referrals | **Homemaker referral** | — | REFERRAL | boolean | NOT FOUND IN REPOSITORY | — | 7 | — | — | — | No | — | — | — | — | — | MISSING FROM SNS | Closest: `personalCare.aideTasks` "Light housekeeping"/"Laundry". |
| Bereavement / Referrals / Spiritual | Referrals | **Therapy referral (PT / OT / Speech)** | — | REFERRAL | boolean | NOT FOUND IN REPOSITORY in `referrals`; disciplines appear in `admissionsOrder` `disciplineFrequencyOfVisit` rows (`:3263-3300`) | admissionsOrder | 7 / 10 | — | — | — | No | — | — | — | — | — | MISSING FROM SNS | A therapy *visit frequency order* can be recorded, but not a therapy *referral*. |
| Bereavement / Referrals / Spiritual | Referrals | **Massage / music / pet / art therapy referral** | — | REFERRAL | boolean | NOT FOUND IN REPOSITORY in `referrals`; partially `personalCare.volunteerServices` ("Music/art therapy", "Pet care") | personalCare | 7 | — | — | — | No | — | — | — | — | — | MISSING FROM SNS | Recorded as a volunteer-service need, not a referral. |
| Bereavement / Referrals / Spiritual | Referrals | **Other referral (free text)** | — | REFERRAL | free text | NOT FOUND IN REPOSITORY | — | 7 | — | — | — | No | — | — | — | — | — | MISSING FROM SNS | `referrals.notes` is the only escape hatch. |
| Bereavement / Referrals / Spiritual | Referrals | **Referral status (pending / accepted / completed)** | — | REFERRAL | status | NOT FOUND IN REPOSITORY | — | 7 | — | — | — | No | — | — | — | — | — | MISSING FROM SNS | Every referral is a bare boolean; there is no lifecycle state. |
| Bereavement / Referrals / Spiritual | Referrals | **Referral audit history** | — | AUDIT/SIGNATURE | history | NOT FOUND IN REPOSITORY as a referral-scoped history | — | 7 / 13 | — | — | — | No | — | — | — | — | — | NOT FOUND IN REPOSITORY | General RNICA amendment/audit history exists (`FinalReviewDashboardCard`, `backend/tests/test_rnica_amendments.py`), but nothing referral-specific was found. |

---
### 4.8 SCREEN 8 — Safety & Clinical Risk

```
Frontend: RNICA.jsx:9420-9472 (SECTION_CONFIGS.safety)
Frontend: RNICA.jsx:9371-9389 (SECTION_CONFIGS.imminentDeath)
Frontend: RNICA.jsx:2426-2494 (DmeStatusCard, dispatched from the safety module at :8453)
Taxonomy: rnicaThirteenScreenTaxonomy.js:80-84
Exporter: sns-emr-frontend/src/intake/hopeReportMapper.js:502,609 (J0050)
```

| LS | LSub | Label | Code | Class | LRS | Path | Sec | Scr | Edit | RO | HH | SFV | Req | Cond | Val | Pers | Compat | Status | Notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Personal Care / Environmental-Safety | Safety | Safety Assessment Completed | — | SNS CLINICAL | boolean | `safety.safetyAssessmentCompleted` | safety | 8 | RNICA editable (`:9425`) | Screen 11 | not emitted | No | optional | always | none | JSONB | additive | PRESENT AND CORRECTLY PLACED | |
| Personal Care / Environmental-Safety | Safety | Home Environment Hazards | — | SNS CLINICAL | Adequate lighting, Handrails present, Throw rugs, Clutter/obstacles, Stairs without railing, **Pets**, Weapons/firearms, Pest infestation, Inadequate heating/cooling, Smoke detectors present | `safety.homeEnvironment` | safety | 8 | RNICA editable (`:9426-9430`) | Screen 7 | not emitted | No | optional | always | none | JSONB | additive | PRESENT BUT RESPONSE SET INCOMPLETE | Mixes protective factors (adequate lighting, handrails, smoke detectors) with hazards under a "Hazards" label, so an unchecked box is ambiguous. |
| Personal Care / Environmental-Safety | Safety | Fall Risk Assessment Completed | — | SNS CLINICAL | boolean | `safety.fallRiskAssessmentCompleted` | safety | 8 | RNICA editable (`:9431`) | Screen 11 | not emitted | No | optional | always | none | JSONB | additive | PRESENT AND CORRECTLY PLACED | |
| Personal Care / Environmental-Safety | Safety | Fall Risk Level | — | SNS CLINICAL | Low/Moderate/High | `safety.fallRiskLevel` | safety | 8 | RNICA editable (`:9432`) | Screen 2 | not emitted | No | optional | always | none | JSONB | additive | PRESENT AND CORRECTLY PLACED | Manually assigned; no scoring engine — correct per "no new scoring". Fall *history* that would justify it lives on Screen 6 (`musculoskeletal.fallHistory.*`). |
| Personal Care / Environmental-Safety | Safety | Transfer Safety | — | SNS CLINICAL | 3 graded options (`:9433-9435`) | `safety.transferSafetyLevel` | safety | 8 | RNICA editable (`:9433`) | Screen 5 | not emitted | No | optional | always | none | JSONB | additive | CONFLICTING | Overlaps `musculoskeletal.mobility.transferAbility` (`:9327`) and `musculoskeletal.adl.transferring` (`:9007`) — three representations of transfer capability. |
| Personal Care / Environmental-Safety | Safety | Firearm in Home | — | SNS CLINICAL | boolean | `safety.firearmInHome` | safety | 8 | RNICA editable (`:9436`) | — | not emitted | No | optional | always | none | JSONB | additive | CONFLICTING | Duplicates the `homeEnvironment` option "Weapons/firearms" (`:9428`). |
| Personal Care / Environmental-Safety | Safety | Oxygen in Use | — | SNS CLINICAL | boolean | `safety.oxygenInUse` | safety | 8 | RNICA editable (`:9437`) | Screen 6 | not emitted | No | optional | always | none | JSONB | additive | CONFLICTING | Duplicates `respiratory.oxygenTherapy.inUse` (`:9129`). |
| Personal Care / Environmental-Safety | Safety | Oxygen Safety Reviewed | — | SNS CLINICAL | boolean | `safety.oxygenSafetyReviewed` | safety | 8 | RNICA editable (`:9438`) | Screen 7 teaching | not emitted | No | optional | always | none | JSONB | additive | CONFLICTING | Overlaps `teachingNeeds.teachingTopics` option "Oxygen" (`:9631`). |
| Personal Care / Environmental-Safety | Safety | Incident/Occurrence Reported This Visit | — | AUDIT/SIGNATURE | boolean | `safety.incidentOccurrenceReported` | safety | 8 | RNICA editable (`:9439`) | Screen 11 | not emitted | No | optional | always | none | JSONB | additive | PRESENT AND CORRECTLY PLACED | |
| Personal Care / Environmental-Safety | Safety | Incident/Occurrence Notes | — | AUDIT/SIGNATURE | free text | `safety.incidentOccurrenceNotes` | safety | 8 | RNICA editable (`:9440`) | — | not emitted | No | optional | always | none | JSONB | additive | PRESENT AND CORRECTLY PLACED | |
| Personal Care / Environmental-Safety | Disaster | Disaster Level | — | SNS CLINICAL | Level 1 (hospice must assist; no assistance available) / Level 2 (hospice must contact; limited assistance) / Level 3 (no need to assist; adequate assistance) | `safety.disasterLevel` | safety | 8 | RNICA editable (`:9443-9447`) | — | not emitted | No | optional | always | none | JSONB | additive | VERIFIED COMPLETE | Covers legacy "disaster triage". |
| Personal Care / Environmental-Safety | Disaster | Level 1 Conditions (two or more apply) | — | SNS CLINICAL | Bed/chair-confined, Dependent on walker or cane, **Lives above ground floor**, **Requires electricity for medical equipment** | `safety.disasterLevelOneConditions` | safety | 8 | RNICA editable (`:9448-9451`) | — | not emitted | No | optional | always | none | JSONB | additive | VERIFIED COMPLETE | Directly covers the legacy "location risk" and "electrical / mobility-equipment dependence" concepts. |
| Personal Care / Environmental-Safety | Disaster | Level 2 Conditions (one applies) | — | SNS CLINICAL | same four conditions | `safety.disasterLevelTwoConditions` | safety | 8 | RNICA editable (`:9452-9455`) | — | not emitted | No | optional | always | none | JSONB | additive | CONFLICTING | The Level 1 and Level 2 lists are byte-identical; the same condition must be entered twice in two arrays and the "two or more / one applies" rule is not enforced anywhere. |
| Personal Care / Environmental-Safety | Disaster | Level 3 Conditions | — | SNS CLINICAL | Lives in facility with disaster support, Has alternate location and available helper | `safety.disasterLevelThreeConditions` | safety | 8 | RNICA editable (`:9456-9458`) | — | not emitted | No | optional | always | none | JSONB | additive | PRESENT AND CORRECTLY PLACED | Covers legacy "available assistance". |
| Personal Care / Environmental-Safety | Safety | Safety Notes | — | SNS CLINICAL | free text | `safety.notes` | safety | 8 | RNICA editable (`:9459`) | — | not emitted | No | optional | always | none | JSONB | additive | PRESENT AND CORRECTLY PLACED | |
| DME Device / IV Assessment | DME | DME per-item status | — | ORDER/POC | Has/Needs/Ordered/Delivered/Declined/N/A (`:2428`) | `safety.dmeItems[].status` (+ `specify` for Commode/Other, `:2426`) | safety | **10** | RNICA editable here today (`:9461`, dispatch `:8453`) | Screens 5, 8 | not emitted | No | optional | always | none | JSONB array | additive | PRESENT BUT MISPLACED | Correctly models "indication ≠ order" via distinct Has/Needs/Ordered/Delivered states — the directive's rule is already satisfied structurally; only the screen ownership is wrong. |
| Personal Care / Environmental-Safety | Supplies | Existing Supplies | — | ORDER/POC | Wound/Continence/Oxygen/Medication/Other supplies | `safety.supplies.existingCategories` | safety | 10 | RNICA editable (`:9463-9465`) | — | not emitted | No | optional | always | none | JSONB | additive | PRESENT BUT MISPLACED | |
| Personal Care / Environmental-Safety | Supplies | Needed Supplies | — | ORDER/POC | same five categories | `safety.supplies.neededCategories` | safety | 10 | RNICA editable (`:9466-9468`) | — | not emitted | No | optional | always | none | JSONB | additive | PRESENT BUT MISPLACED | |
| Personal Care / Environmental-Safety | Supplies | Other Supplies Notes | — | ORDER/POC | free text | `safety.supplies.otherSuppliesNotes` | safety | 10 | RNICA editable (`:9469`) | — | not emitted | No | optional | always | none | JSONB | additive | PRESENT BUT MISPLACED | |
| (no legacy screen described) | Imminent death | Appears within 3 days or less of death? | J0050 | HOPE | 0 No / 1 Yes / 9 Unable to determine | `imminentDeath.appearsThreeDaysOrLess` | imminentDeath | 8 | RNICA editable (`:9376-9378`) | Screens 2, 11 | `hopeReportMapper.js:502,609` via `YES_NO_UNABLE_MAP` | No | optional | always | `lookup()` | JSONB | additive | VERIFIED COMPLETE | The true J0050 owner. Declared at `form_registry.py:379`. |
| (no legacy screen described) | Imminent death | Indicators of Imminent Death | — | SNS CLINICAL | Mottling of extremities, Mandibular breathing, Apneic periods, Cyanosis, **No urine output**, Unresponsive, Death rattle, Cheyne-Stokes breathing, **Cool/cold extremities**, **Decreased level of consciousness**, **Inability to swallow** | `imminentDeath.indicators` | imminentDeath | 8 | RNICA editable (`:9379-9383`) | — | not emitted | No | optional | always | none | JSONB | additive | PRESENT BUT RESPONSE SET INCOMPLETE | **Against the directive's list:** decreased consciousness ✓, reduced intake (via "Inability to swallow") ✓, increased respiratory distress (via Mandibular breathing / Apneic periods / Cheyne-Stokes / Death rattle) ✓. **Absent:** *increased fatigue*, *increased agitation*, and *bowel/bladder decline* as such — "No urine output" is an endpoint, not a decline, and there is no bowel equivalent. |
| (no legacy screen described) | Imminent death | Comfort Measures in Place | — | SNS CLINICAL | boolean | `imminentDeath.comfortMeasuresInPlace` | imminentDeath | 8 | RNICA editable (`:9384`) | Screen 9 | not emitted | No | optional | always | none | JSONB | additive | CONFLICTING | Overlaps `advancedCarePlanning.codeStatus` value "Comfort Measures Only" (`:8174`). |
| (no legacy screen described) | Imminent death | Family Notified | — | SNS CLINICAL | boolean | `imminentDeath.familyNotified` | imminentDeath | 8 | RNICA editable (`:9385`) | — | not emitted | No | optional | always | none | JSONB | additive | PRESENT AND CORRECTLY PLACED | |
| (no legacy screen described) | Imminent death | Notes | — | SNS CLINICAL | free text | `imminentDeath.notes` | imminentDeath | 8 | RNICA editable (`:9386`) | — | not emitted | No | optional | always | none | JSONB | additive | PRESENT AND CORRECTLY PLACED | |
| Personal Care / Environmental-Safety | Safety | **Braden summary (read-only cross-reference)** | — | COMPUTED RESULT | derived | would read `skin.braden.*` / `skin.pressureInjuryRisk` | skin | 8 (read-only) | Screen 6 owns | — | not emitted | No | n/a | — | — | not persisted | n/a | NOT FOUND IN REPOSITORY | The directive requires a read-only Braden summary on Screen 8; no such panel was found in `SECTION_CONFIGS.safety`. There is correspondingly **no duplicate editable Braden**, which is the important half of the rule. |
| Personal Care / Environmental-Safety | Safety | **Safety-related medication-administration concern** | — | SNS CLINICAL | n/a | NOT FOUND IN REPOSITORY | — | 8 | — | — | — | No | — | — | — | — | — | MISSING FROM SNS | Only `pcg.ableToAdministerMeds` (Screen 7) touches this; there is no safety-scoped concern field (e.g. controlled-substance diversion risk). |
| Personal Care / Environmental-Safety | Safety | **Safety source links** | — | NOT VERIFIED | link | NOT FOUND IN REPOSITORY | — | 8 | — | — | — | No | — | — | — | — | — | NOT FOUND IN REPOSITORY | |

---

### 4.9 SCREEN 9 — ACP & Goals of Care

```
Frontend: RNICA.jsx:8169-8201 (Advanced Care Planning card, cms="F2000/F2100/F2200", id="advancedCarePlanning")
Frontend: RNICA.jsx:204 SIDEBAR_CONFIG advancedCarePlanning (hope: F2000/F2100/F2200, cdphRequired)
Frontend: RNICA.jsx:252 UPDATE_HIDDEN_SIDEBAR_KEYS includes advancedCarePlanning
Taxonomy: rnicaThirteenScreenTaxonomy.js:85-88 (moduleKeys: ["advancedCarePlanning"])
Backend:  backend/app/domain/forms/form_registry.py:364-369 (HOPE_PREFERENCES_ITEM_CODES)
Exporter: sns-emr-frontend/src/intake/hopeReportMapper.js:303-327,496-498,586-589
Doc:      docs/tenant-platform/RNICA_ACP_SIX_FIELD_RECONCILIATION_DECISION.md
```

| LS | LSub | Label | Code | Class | LRS | Path | Sec | Scr | Edit | RO | HH | SFV | Req | Cond | Val | Pers | Compat | Status | Notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Vitals / … / Comms | ACP | F2000: Was patient/responsible party asked about CPR preference? | F2000A | HOPE | 0 No / 1 Yes, and discussion occurred / 2 Yes, but refused to discuss | `demographics.advancedCarePlanning.cprPreferenceAskedStatus` | demographics | 9 | RNICA editable (`:8170-8172`) | Screens 11, 13 | `hopeReportMapper.js:496,586` via `askedStatus()` (`:303-327`) | No | optional | hidden on UPDATE assessments (`:252`) | incompleteness surfaces in `legacyReviewItems` (`:513`) | JSONB | `askedStatus()` falls back to `codeStatus` presence for pre-existing records | VERIFIED COMPLETE | |
| Vitals / … / Comms | ACP | Code Status | — | SNS CLINICAL | Full Code/DNR/DNR-CC/Comfort Measures Only | `demographics.advancedCarePlanning.codeStatus` | demographics | 9 | RNICA editable (`:8173-8174`) | Screens 2, 8 | back-compat indicator for F2000A | No | optional | as above | none | JSONB | additive | PRESENT AND CORRECTLY PLACED | Distinct from the HOPE "was asked" item — correctly separated per `RNICA_ACP_SIX_FIELD_RECONCILIATION_DECISION.md`. |
| Vitals / … / Comms | ACP | Code Status Discussion Date | F2000B | HOPE | date | `demographics.advancedCarePlanning.codeStatusDate` | demographics | 9 | RNICA editable (`:8175-8176`) | — | `hopeReportMapper.js:586` | No | optional | as above | none | JSONB | additive | PRESENT AND CORRECTLY PLACED | |
| Vitals / … / Comms | ACP | F2100: Was patient/responsible party asked about other life-sustaining treatments? | F2100A | HOPE | 0/1/2 | `demographics.advancedCarePlanning.lifeSustainingAskedStatus` | demographics | 9 | RNICA editable (`:8177-8179`) | Screens 11, 13 | `hopeReportMapper.js:497,587` | No | optional | as above | `legacyReviewItems` (`:514`) | JSONB | falls back to preference presence | VERIFIED COMPLETE | |
| Vitals / … / Comms | ACP | Life-Sustaining Treatment Preference | — | SNS CLINICAL | Yes — wants / No — does not want / Undecided | `demographics.advancedCarePlanning.lifeSustainingTreatmentPreference` | demographics | 9 | RNICA editable (`:8180-8182`) | Screen 6 (ventilator context) | back-compat indicator for F2100A | No | optional | as above | none | JSONB | additive | PRESENT AND CORRECTLY PLACED | |
| Vitals / … / Comms | ACP | Life-Sustaining Treatment Discussion Date | F2100B | HOPE | date | `demographics.advancedCarePlanning.lifeSustainingTreatmentPreferenceDate` | demographics | 9 | RNICA editable (`:8183-8184`) | — | `hopeReportMapper.js:587` | No | optional | as above | none | JSONB | additive | PRESENT AND CORRECTLY PLACED | |
| Vitals / … / Comms | ACP | F2200: Was patient/responsible party asked about hospitalization preference? | F2200A | HOPE | 0/1/2 | `demographics.advancedCarePlanning.hospitalizationAskedStatus` | demographics | 9 | RNICA editable (`:8185-8187`) | Screens 11, 13 | `hopeReportMapper.js:498,588` | No | optional | as above | `legacyReviewItems` (`:515`) | JSONB | falls back to preference presence | VERIFIED COMPLETE | |
| Vitals / … / Comms | ACP | Hospitalization Preference | — | SNS CLINICAL | Yes — wants / No — does not want / Undecided | `demographics.advancedCarePlanning.hospitalizationPreference` | demographics | 9 | RNICA editable (`:8188-8190`) | Screen 4 (utilization) | back-compat indicator for F2200A | No | optional | as above | none | JSONB | additive | PRESENT AND CORRECTLY PLACED | |
| Vitals / … / Comms | ACP | Hospitalization Discussion Date | F2200B | HOPE | date | `demographics.advancedCarePlanning.hospitalizationPreferenceDate` | demographics | 9 | RNICA editable (`:8191-8192`) | — | `hopeReportMapper.js:588` | No | optional | as above | none | JSONB | additive | PRESENT AND CORRECTLY PLACED | |
| Vitals / … / Comms | ACP | Decision Maker | — | SNS CLINICAL | free text | `demographics.advancedCarePlanning.decisionMaker` | demographics | 9 | RNICA editable (`:8194`) | Screen 7 | not emitted | No | optional | as above | none | JSONB | additive | PRESENT AND CORRECTLY PLACED | |
| Vitals / … / Comms | ACP | POA Name | — | SNS CLINICAL | free text | `demographics.advancedCarePlanning.poaName` | demographics | 9 | RNICA editable (`:8195`) | Screen 7 | not emitted | No | optional | as above | none | JSONB | additive | PRESENT AND CORRECTLY PLACED | |
| Vitals / … / Comms | ACP | POA Phone | — | SNS CLINICAL | tel | `demographics.advancedCarePlanning.poaPhone` | demographics | 9 | RNICA editable (`:8196`) | Screen 7 | not emitted | No | optional | as above | none | JSONB | additive | PRESENT AND CORRECTLY PLACED | |
| Vitals / … / Comms | ACP | Advance Directive on File | — | SNS CLINICAL | boolean | `demographics.advancedCarePlanning.advanceDirectiveOnFile` | demographics | 9 | RNICA editable (`:8198`) | Screen 7 | not emitted | No | optional | as above | none | JSONB | additive | PRESENT AND CORRECTLY PLACED | |
| Vitals / … / Comms | ACP | POLST on File | — | SNS CLINICAL | boolean | `demographics.advancedCarePlanning.polstOnFile` | demographics | 9 | RNICA editable (`:8199`) | — | not emitted | No | optional | as above | none | JSONB | additive | PRESENT AND CORRECTLY PLACED | |
| Vitals / … / Comms | ACP | **Goals of care (narrative)** | — | SNS CLINICAL | free text | NOT FOUND IN REPOSITORY as a discrete field | — | 9 | — | — | — | No | — | — | — | — | — | MISSING FROM SNS | The screen is named "ACP & Goals of Care" but there is no goals-of-care field; the closest is `finalization.clinicalNarrative`. |
| Vitals / … / Comms | ACP | Communication / interpreter / military / caregiver / med-safety fields | — | — | — | **must not appear here** | — | 1/7/8 | Screens 1, 7, 8 | — | — | No | — | — | — | — | — | PRESENT AND CORRECTLY PLACED | Verified absent from the ACP card (`:8169-8201`) — the directive's non-duplication rule holds. |

---
### 4.10 SCREEN 10 — Orders & POC

```
Frontend: RNICA.jsx:9657-9686 (SECTION_CONFIGS.admissionsOrder)
Frontend: RNICA.jsx:3263-3300 (DisciplineFrequencyOfVisitCard)
Frontend: RNICA.jsx:8484-8510 (disciplineFrequencyOfVisit / haAssignment dispatch)
Frontend: RNICA.jsx:189-190, 220-222 (admissionsOrder subFields + features)
Frontend: RNICA.jsx:251 UPDATE_HIDDEN_ROUTE_KEYS includes admissionsOrder
Frontend: RNICA.jsx:6702 OrdersHubCard (ordersHub module)
Taxonomy: rnicaThirteenScreenTaxonomy.js:89-92 (moduleKeys: ["admissionsOrder","ordersHub"])
Backend:  backend/app/services/rnica_finalization_service.py:35-91 (evaluate_poc_completeness), :156-167 (CHHA POC)
Test:     backend/tests/test_rnica_poc_adapter.py, test_rnica_poc_history.py, test_rnica_order_suggestions.py
```

| LS | LSub | Label | Code | Class | LRS | Path | Sec | Scr | Edit | RO | HH | SFV | Req | Cond | Val | Pers | Compat | Status | Notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Narrative / Admissions Order | Order | Admission Order Statement | — | ORDER/POC | free text | `admissionsOrder.admissionStatement` | admissionsOrder | 10 | RNICA editable (`:9662`) | Screen 13 | not emitted | No | optional | hidden on UPDATE assessments (`:251`) | none | JSONB | additive | PRESENT AND CORRECTLY PLACED | Card marked `cms="Verbal Order"` (`:9661`). |
| Narrative / Admissions Order | Order | Level of Care | — | ORDER/POC | Routine Care/General Inpatient/Continuous Care/Respite Care | `admissionsOrder.levelOfCare.level` | admissionsOrder | 10 | RNICA editable (`:9665`) | Screens 1, 11 | not emitted | No | optional | as above | none | JSONB | additive | VERIFIED COMPLETE | All four Medicare hospice levels of care present. |
| Narrative / Admissions Order | Order | Effective Date | A0220 (fallback) | ORDER/POC | date | `admissionsOrder.levelOfCare.effectiveDate` | admissionsOrder | 10 | RNICA editable (`:9666`) | Screen 1 | second fallback for A0220 (`hopeReportMapper.js:557`) | No | optional | as above | none | JSONB | additive | PRESENT AND CORRECTLY PLACED | |
| Narrative / Admissions Order | Order | LOC Justification | — | ORDER/POC | free text | `admissionsOrder.levelOfCare.justification` | admissionsOrder | 10 | RNICA editable (`:9667`) | — | not emitted | No | optional | as above | none | JSONB | additive | PRESENT AND CORRECTLY PLACED | |
| Narrative / Admissions Order | Order | Discipline (repeating row) | — | ORDER/POC | discipline picklist | `admissionsOrder.visitFrequency[].discipline` (`DisciplineFrequencyOfVisitCard`, `:3291`) | admissionsOrder | 10 | RNICA editable | Screen 11 | not emitted | No | optional | as above | none | JSONB array | additive | PRESENT AND CORRECTLY PLACED | Exact persisted array key `NOT VERIFIED`; `LEGACY_ROUTES.subFields` lists `visitFrequency` (`:190`). |
| Narrative / Admissions Order | Order | No. of Visits (repeating row) | — | ORDER/POC | numeric | `admissionsOrder.visitFrequency[].visits` (`:3297`) | admissionsOrder | 10 | RNICA editable | Screen 11 | not emitted | No | optional | as above | none | JSONB array | additive | PRESENT AND CORRECTLY PLACED | Covers legacy "visit frequency" and "discipline coverage". |
| Narrative / Admissions Order | Aide | Assigned Home Aide | — | ORDER/POC | free text | `admissionsOrder.haAssignment.assignedAide` | admissionsOrder | 10 | RNICA editable (`:9671`) | Screen 11 | not emitted | No | conditionally gates Lock | as above | `evaluate_finalization_readiness` `chhaPocCompleted` (`rnica_finalization_service.py:156-167`) | JSONB | additive | VERIFIED COMPLETE | If an aide is assigned and `notApplicable` is false, the CHHA POC must be marked complete before Lock. |
| Narrative / Admissions Order | Aide | HA Assignment N/A | — | ORDER/POC | boolean | `admissionsOrder.haAssignment.notApplicable` | admissionsOrder | 10 | RNICA editable (`:9672`) | Screen 11 | not emitted | No | gates Lock | as above | `rnica_finalization_service.py:156` | JSONB | additive | VERIFIED COMPLETE | Explicit not-applicable state — the pattern missing from the functional scales. |
| Narrative / Admissions Order | Aide | CHHA Plan of Care completed | — | READINESS | boolean | `chhaPoc.completed` (read at `rnica_finalization_service.py:159` as a **top-level** `form_data` key, not under `admissionsOrder`) | chhaPoc | 10/11 | NOT VERIFIED which UI writes it | Screens 11, 13 | not emitted | No | **gates Lock** | when an aide is assigned | server | JSONB | additive | REQUIRES AUTHORITY REVIEW | No `SECTION_CONFIGS` entry writes `chhaPoc.completed`; the writer was not located this pass. |
| Narrative / Admissions Order | POC | Initial POC Created | — | ORDER/POC | boolean | `admissionsOrder.initialPocIdg.created` | admissionsOrder | 10 | RNICA editable (`:9675`) | Screen 11 | not emitted | No | optional | as above | none | JSONB | additive | PRESENT AND CORRECTLY PLACED | Covers legacy "initial POC/IDG". |
| Narrative / Admissions Order | POC | Created Date | — | ORDER/POC | date | `admissionsOrder.initialPocIdg.createdDate` | admissionsOrder | 10 | RNICA editable (`:9676`) | — | not emitted | No | optional | as above | none | JSONB | additive | PRESENT AND CORRECTLY PLACED | |
| Narrative / Admissions Order | POC | POC/IDG Notes | — | ORDER/POC | free text | `admissionsOrder.initialPocIdg.notes` | admissionsOrder | 10 | RNICA editable (`:9677`) | — | not emitted | No | optional | as above | none | JSONB | additive | PRESENT AND CORRECTLY PLACED | |
| Narrative / Admissions Order | Verbal order | Verbal Order Read Back and Verified | — | AUDIT/SIGNATURE | boolean | `admissionsOrder.toVerification.verbalOrderReadBack` | admissionsOrder | 10 | RNICA editable (`:9680`) | Screen 11 | not emitted | No | optional | as above | none | JSONB | additive | VERIFIED COMPLETE | Declared as a feature at `SIDEBAR_CONFIG:222`. |
| Narrative / Admissions Order | Verbal order | Verified By | — | AUDIT/SIGNATURE | free text | `admissionsOrder.toVerification.verifiedBy` | admissionsOrder | 10 | RNICA editable (`:9681`) | — | not emitted | No | optional | as above | none | JSONB | additive | PRESENT AND CORRECTLY PLACED | |
| Narrative / Admissions Order | Verbal order | Prescriber on Call Contacted | — | AUDIT/SIGNATURE | boolean | `admissionsOrder.toVerification.prescriberContacted` | admissionsOrder | 10 | RNICA editable (`:9682`) | — | not emitted | No | optional | as above | none | JSONB | additive | PRESENT AND CORRECTLY PLACED | |
| Narrative / Admissions Order | Verbal order | Verification Timestamp | — | AUDIT/SIGNATURE | datetime-local | `admissionsOrder.toVerification.verificationTimestamp` | admissionsOrder | 10 | RNICA editable (`:9683`) | — | not emitted | No | optional | as above | none | JSONB | additive | PRESENT AND CORRECTLY PLACED | |
| Narrative / Admissions Order | POC | POC problems / goals / interventions / disciplines | — | ORDER/POC | structured | Plan-of-Care problem records (server-side), consumed by `evaluate_poc_completeness(problems)` (`rnica_finalization_service.py:35-91`) | (POC store, not `form_data`) | 10 | RNICA editable via per-section "Add to POC" controls (`RNICA.jsx:8697-8700`, `POC_ENABLED_SECTIONS`) | Screens 11, 13 | not emitted | No | **gates Lock** | always | server: every active problem needs goals, interventions and disciplines | separate POC store | n/a | VERIFIED COMPLETE | Covered by `backend/tests/test_rnica_poc_adapter.py` and `test_rnica_poc_history.py`. |
| Narrative / Admissions Order | Orders | Treatment / medication orders | — | ORDER/POC | structured | `OrdersHubCard` (`RNICA.jsx:6702`), API `sns-emr-frontend/src/api/ordersHub` (`:98`) | ordersHub | 10 | RNICA editable | — | not emitted | No | optional | always | `backend/app/services/physician_order_service.py` | orders store | n/a | PRESENT AND CORRECTLY PLACED | Suggestion behaviour covered by `backend/tests/test_rnica_order_suggestions.py`. Note: the mapper's N0500/N0510 opioid items do **not** read from this store. |
| Narrative / Admissions Order | Orders | **Non-covered items** | — | ORDER/POC | list | `LEGACY_ROUTES.subFields` declares `nonCoveredItems` (`:190`) and `SIDEBAR_CONFIG` repeats it (`:221`), but **no card or field for it exists in `SECTION_CONFIGS.admissionsOrder`** (`:9657-9686`) | admissionsOrder | 10 | — | — | not emitted | No | — | — | — | — | — | PRESENT BUT NOT WIRED | Declared in navigation metadata only. A separate `PatientNotificationNonCovered.jsx` exists under `src/intake/`, outside RNICA. |
| Narrative / Admissions Order | Orders | DME order | — | ORDER/POC | Ordered/Delivered states | `safety.dmeItems[].status` | safety | 10 | currently editable on Screen 8 | Screens 5, 8 | not emitted | No | optional | always | none | JSONB array | additive | PRESENT BUT MISPLACED | See Screen 8 row. |
| Narrative / Admissions Order | Orders | Oxygen order | — | ORDER/POC | derived from `respiratory.oxygenTherapy.*` | `respiratory.oxygenTherapy.type/.litersPerMinute/.deliveryMode` | respiratory | 10 | Screen 6 owns the clinical finding | Screen 10 | not emitted | No | optional | always | none | JSONB | additive | REQUIRES AUTHORITY REVIEW | Oxygen is documented as a therapy finding; whether an explicit oxygen *order* record is required is a product decision. |
| Narrative / Admissions Order | Orders | **Explicit user-approved actions** | — | AUDIT/SIGNATURE | n/a | order-suggestion acceptance flow (`backend/tests/test_rnica_order_suggestions.py`) | ordersHub | 10 | RNICA editable | Screen 12 | not emitted | No | n/a | always | server | orders store | n/a | PRESENT AND CORRECTLY PLACED | AI suggestions require explicit acceptance — consistent with the directive. |

---

### 4.11 SCREEN 11 — Compliance & Readiness

```
Frontend: RNICA.jsx:232-239 (FINALIZATION_CHECK_SECTION_MAP), :11068 (map consumption)
Frontend: RNICA.jsx:1069-1098 (Section 10/12 warning wiring)
Taxonomy: rnicaThirteenScreenTaxonomy.js:93-105 (crossCutting, railTarget "validation", landingModuleKey "finalization")
Backend:  backend/app/services/rnica_finalization_service.py:94-169 (evaluate_finalization_readiness)
Backend:  backend/app/services/rnica_hope_workflow_service.py:59-200
Exporter: sns-emr-frontend/src/intake/hopeReportMapper.js:400-433 (getSfvStatus), :512-526 (legacyReviewRequired), getHopeAdmissionStatus (imported at RNICA.jsx:123)
Test:     backend/tests/test_rnica_finalization.py, test_rnica_hope_workflow.py, test_rnica_runtime_validation.py
```

Screen 11 owns **no** editable clinical field (`moduleKeys: []`). Every row is a
readiness projection.

| LS | LSub | Label | Code | Class | LRS | Path | Sec | Scr | Edit | RO | HH | SFV | Req | Cond | Val | Pers | Compat | Status | Notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| (cross-cutting) | Readiness | Attestation ready | — | READINESS | boolean | check `attestation` ← `finalization.signatureCertification` | finalization | 11 | Screen 13 owns | Screen 11 | not emitted | No | gate | always | `rnica_finalization_service.py:103-109` | derived | n/a | VERIFIED COMPLETE | Navigates to `finalization` (`RNICA.jsx:233`). |
| (cross-cutting) | Readiness | Required signatures present | — | READINESS | boolean | check `signature` ← `finalization.clinicianSignature` | finalization | 11 | Screen 13 owns | Screen 11 | not emitted | No | gate | always | `:111-118` | derived | n/a | VERIFIED COMPLETE | |
| (cross-cutting) | Readiness | Narrative reviewed | — | READINESS | boolean | check `narrativeReviewed` ← `diagnoses.clinicalNarrative` + `.clinicalNarrativeReviewed` | diagnoses | 11 | Screen 4 map target (`RNICA.jsx:235`) | Screen 11 | not emitted | No | gate | always | `:120-128` | derived | pre-existing records may satisfy it | CONFLICTING | Reads an unreachable path — see §2 finding 5. |
| (cross-cutting) | Readiness | LCD evidence baseline available | — | READINESS | boolean | check `lcdBaseline` ← `diagnoses.lcdEligibilityNarrative` | diagnoses | 11 | Screen 4 (`RNICA.jsx:236`) | Screen 11 | not emitted | No | gate | always | `:130-135` | derived | n/a | VERIFIED COMPLETE | |
| (cross-cutting) | Readiness | Referrals reviewed | — | READINESS | boolean | check `referralsReviewed` ← `referrals.reviewed` | referrals | 11 | Screen 7 after relocation (`RNICA.jsx:237`) | Screen 11 | not emitted | No | gate | always | `:137-143` | derived | n/a | VERIFIED COMPLETE | |
| (cross-cutting) | Readiness | Goals, interventions & disciplines present | — | READINESS | boolean + incomplete labels | check `pocCompleteness` ← `evaluate_poc_completeness(poc_problems)` | (POC store) | 11 | Screen 10 | Screen 11 | not emitted | No | gate | always | `:35-91,145-150` | derived | n/a | VERIFIED COMPLETE | Deliberately **not** in `FINALIZATION_CHECK_SECTION_MAP` because it spans every section (`RNICA.jsx:229-231`). |
| (cross-cutting) | Readiness | CHHA Plan of Care completed | — | READINESS | boolean | check `chhaPocCompleted` ← `haAssignment.*` + `chhaPoc.completed` | admissionsOrder / chhaPoc | 11 | Screen 10 (`RNICA.jsx:238`) | Screen 11 | not emitted | No | gate | when an aide is assigned | `:156-167` | derived | n/a | REQUIRES AUTHORITY REVIEW | The `chhaPoc.completed` writer is unlocated — see Screen 10. |
| (cross-cutting) | Readiness | **Overall Lock readiness** | — | READINESS | boolean | `{"ready": ready, "checks": checks}` (`:169`) | n/a | 11 | system | Screens 11, 13 | not emitted | No | n/a | always | server, re-validated independently of the frontend checklist | derived | n/a | VERIFIED COMPLETE | Single readiness engine — the directive's "no second readiness engine" rule holds. |
| (cross-cutting) | HOPE | Incomplete HOPE fields | — | READINESS | item-code list | `legacyReviewRequired.items` (`hopeReportMapper.js:512-526`) — F2000, F2100, F2200, F3000, A1400, J0900, J0915 only | n/a | 11 | none (derived) | Screen 11 | n/a | No | advisory | always | client | not persisted | n/a | PRESENT BUT RESPONSE SET INCOMPLETE | Only **7** item codes are checked for completeness. A1005, A1010, A1110, A0215, A1805, A1905, A1910, I0010, I8005, J0050, J2050-J2053, M1190-M1200 and N0500-N0520 are **not** checked, so a HOPE report can be produced with those blank and no readiness warning. |
| (cross-cutting) | SFV | SFV trigger / due / completed state | J2050-J2053 | SFV | derived | `getSfvStatus(formData)` (`hopeReportMapper.js:400-433`), imported into RNICA at `:123` | n/a | 11 | none (derived) | Screens 3, 11 | n/a | Yes | advisory | always | client | not persisted | n/a | VERIFIED COMPLETE | Distinct from the backend visit-note trigger engine. |
| (cross-cutting) | HOPE | HOPE admission status | — | READINESS | derived | `getHopeAdmissionStatus` (imported at `RNICA.jsx:123`) | n/a | 11 | none (derived) | Screen 11 | n/a | No | advisory | always | client | not persisted | n/a | PRESENT AND CORRECTLY PLACED | |
| (cross-cutting) | Workflow | HOPE submission workflow state (submitted / accepted / rejected / corrected / exported-to-batch) | — | AUDIT/SIGNATURE | status | `rnica_assessments.hope_exported_to_batch_at/_by`, `hope_export_batch_id` (`backend/app/models/rnica_assessment.py:38-40`) | (assessment columns) | 11 | system | Screens 11, 13 | n/a | No | n/a | after finalization | `rnica_hope_workflow_service.py:59-200` | DB columns | migration `9d3f6b7c8a10` | VERIFIED COMPLETE | Audit action `RNICA_HOPE_EXPORTED_TO_BATCH` (`backend/app/api/visits.py:1415`, `owner_admin.py:116`). Tracks the *envelope*, not item values. |
| (cross-cutting) | Compliance | Assessment completeness / screen completion count | — | COMPUTED RESULT | counts | `FINALIZATION_CHECK_SECTION_MAP` consumption (`RNICA.jsx:11068`) | n/a | 11 | none (derived) | Screen 11 | n/a | No | n/a | always | client | not persisted | n/a | PRESENT AND CORRECTLY PLACED | No competing persisted completion counter — correct per §16 C. |
| (cross-cutting) | Compliance | Source-screen navigation | — | READINESS | routing | `FINALIZATION_CHECK_SECTION_MAP` (`RNICA.jsx:232-239`) | n/a | 11 | none | Screen 11 | n/a | No | n/a | always | client | not persisted | n/a | PRESENT AND CORRECTLY PLACED | |
| (cross-cutting) | Compliance | Amendment state | — | AUDIT/SIGNATURE | status | `FinalReviewDashboardCard` (`RNICA.jsx:6097`) | finalization | 11/13 | Screen 13 | Screen 11 | n/a | No | n/a | after lock | `backend/tests/test_rnica_amendments.py` | assessment records | n/a | PRESENT AND CORRECTLY PLACED | |
| (cross-cutting) | Compliance | Audit status | — | AUDIT/SIGNATURE | events | audit-log records (`backend/app/api/owner_admin.py:116`) | n/a | 11/13 | system | Screens 11, 13 | n/a | No | n/a | always | server | audit store | n/a | PRESENT AND CORRECTLY PLACED | |

---

### 4.12 SCREEN 12 — AI Action Center

```
Taxonomy: rnicaThirteenScreenTaxonomy.js:106-118 (crossCutting, railTarget "intelligence", moduleKeys: [])
Frontend: sns-emr-frontend/src/components/rn-ica/applyStructuredFindings.js (+ .test.js)
Frontend: sns-emr-frontend/src/components/rn-ica/structuredFindingRegistry.generated.js
Backend:  backend/app/services/evidence/structured_findings.py, note_draft_service.py
Doc:      docs/tenant-platform/RNICA_AI_GOVERNANCE.md
```

| LS | LSub | Label | Code | Class | LRS | Path | Sec | Scr | Edit | RO | HH | SFV | Req | Cond | Val | Pers | Compat | Status | Notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| (no legacy equivalent) | AI | Advisory findings | — | LEGACY DISPLAY ONLY | advisory | RNICA Intelligence rail | none | 12 | **none** | Screens 2, 12 | n/a | No | n/a | always | n/a | not persisted | n/a | PRESENT AND CORRECTLY PLACED | `moduleKeys: []` proves AI owns no clinical field. |
| (no legacy equivalent) | AI | Missing evidence / documentation gaps | — | LEGACY DISPLAY ONLY | advisory | Intelligence rail | none | 12 | none | Screens 2, 12 | n/a | No | n/a | always | n/a | not persisted | n/a | PRESENT AND CORRECTLY PLACED | Cannot satisfy a missing HOPE/SFV response — the readiness engine reads `form_data`, not AI output. |
| (no legacy equivalent) | AI | Source info / provenance | — | LEGACY DISPLAY ONLY | advisory | `structuredFindingRegistry.generated.js`, `ConceptMapping` records (`structured_findings.py`) | none | 12 | none | Screen 12 | n/a | No | n/a | always | n/a | not persisted | n/a | PRESENT AND CORRECTLY PLACED | |
| (no legacy equivalent) | AI | Suggested follow-up | — | LEGACY DISPLAY ONLY | advisory | Intelligence rail / order suggestions | none | 12 | none | Screen 12 | n/a | No | n/a | always | n/a | not persisted | n/a | PRESENT AND CORRECTLY PLACED | Acceptance is explicit (`test_rnica_order_suggestions.py`). |
| (no legacy equivalent) | AI | Freshness state | — | LEGACY DISPLAY ONLY | timestamp | Intelligence rail | none | 12 | none | Screen 12 | n/a | No | n/a | always | n/a | not persisted | n/a | NOT VERIFIED | A freshness indicator was not located in this pass. |
| (no legacy equivalent) | AI | Structured-finding application into clinical fields | — | NOT VERIFIED | field writes | `applyStructuredFindings.js`; `_fw(path, value, section=…)` mappings in `structured_findings.py` | multiple | 12 → source screens | writes into owning sections | — | indirectly (e.g. `symptomImpact.anxiety`) | writes SFV-relevant paths | n/a | on clinician acceptance | `applyStructuredFindings.test.js` | JSONB | additive | REQUIRES AUTHORITY REVIEW | AI **can** write HOPE/SFV-relevant paths (`symptomImpact.*`, `neurological.hopeItems.n0500`). Whether each write requires explicit clinician acceptance in every path is beyond what was verified this pass. |

---

### 4.13 SCREEN 13 — Finalization

```
Frontend: RNICA.jsx:9709-9731 (SECTION_CONFIGS.finalization)
Frontend: RNICA.jsx:6097-6110 (FinalReviewDashboardCard / AmendmentPanel)
Frontend: RNICA.jsx:2163 (post-lock read-only banner)
Backend:  backend/app/services/rnica_finalization_service.py:94-169
Backend:  backend/app/domain/forms/form_registry.py:414-418 (HOPE_FINALIZATION_ITEM_CODES)
Exporter: sns-emr-frontend/src/intake/hopeReportMapper.js:479,642-645
Test:     backend/tests/test_rnica_finalization.py, test_rnica_amendments.py
```

| LS | LSub | Label | Code | Class | LRS | Path | Sec | Scr | Edit | RO | HH | SFV | Req | Cond | Val | Pers | Compat | Status | Notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Narrative / Admissions Order | Narrative | Clinical narrative | — | SNS CLINICAL | free text (8 rows) | `finalization.clinicalNarrative` | finalization | 13 | RNICA editable (`:9713-9716`, card id `rnica-clinical-narrative`) | Screen 2 | not emitted | No | **`required: true`** | always | frontend `required`; **not** read by the readiness engine | JSONB | additive | CONFLICTING | This is the only active narrative, as the directive requires — but the Lock gate reads `diagnoses.clinicalNarrative` instead. |
| Narrative / Admissions Order | Narrative | **Disease trajectory** | — | SNS CLINICAL | option set | `diagnoses.diseaseTrajectory` | diagnoses | 13 | Screen 4 renderer (unreachable card) | Screen 2 | not emitted | No | optional | unreachable | legacy-value detection | JSONB | legacy values preserved | PRESENT BUT NOT WIRED | Directive places it on Screen 13; it is neither on Screen 13 nor reachable on Screen 4. |
| Narrative / Admissions Order | Amendments | Amendments / correction history | — | AUDIT/SIGNATURE | history | `FinalReviewDashboardCard` (`:9717`, `:6097`) | finalization | 13 | system + clinician amendments | Screen 11 | not emitted | No | n/a | after lock | `backend/tests/test_rnica_amendments.py` | amendment records | n/a | VERIFIED COMPLETE | |
| Narrative / Admissions Order | Completion | Signature Certification — I certify this assessment is complete and accurate | Z0500 | HOPE / AUDIT-SIGNATURE | boolean | `finalization.signatureCertification` | finalization | 13 | RNICA editable (`:9719`) | Screen 11 | `hopeReportMapper.js:644` (Z0500 attestation text) | No | **gates Lock** | always | `rnica_finalization_service.py:103-109` | JSONB | additive | VERIFIED COMPLETE | Z0500 declared at `form_registry.py:417`. |
| Narrative / Admissions Order | Completion | Clinician Signature | — | AUDIT/SIGNATURE | free text | `finalization.clinicianSignature` | finalization | 13 | RNICA editable (`:9720`, `required: true`) | Screen 11 | not emitted | No | **gates Lock** | always | `rnica_finalization_service.py:111-118` | JSONB | additive | VERIFIED COMPLETE | |
| Narrative / Admissions Order | Completion | Signature Date | Z0350 | HOPE / AUDIT-SIGNATURE | date | `finalization.signatureDate` | finalization | 13 | RNICA editable (`:9721`, `required: true`) | Screens 1, 11 | `hopeReportMapper.js:479,642` (primary source of `completionDate`) | No | required | always | frontend `required` | JSONB | falls back to `lockedAt`/`updatedAt`/`createdAt` | VERIFIED COMPLETE | Z0350 declared at `form_registry.py:415`. |
| Narrative / Admissions Order | Completion | HOPE Submission / Confirmation Number | — | AUDIT/SIGNATURE | free text | `finalization.hopeSubmissionNumber` | finalization | 13 | RNICA editable (`:9722`) | Screen 11 | not emitted | No | optional | always | none | JSONB | additive | CONFLICTING | A second, manual record of submission state alongside the authoritative DB columns (`hope_export_batch_id` etc.) managed by `rnica_hope_workflow_service.py`. |
| Narrative / Admissions Order | Completion | HOPE report already submitted — tracking not required | — | AUDIT/SIGNATURE | boolean | `finalization.hopeAlreadySubmitted` | finalization | 13 | RNICA editable (`:9723`) | Screen 11 | not emitted | No | optional | always | none | JSONB | additive | CONFLICTING | Same overlap. |
| Narrative / Admissions Order | Supervisor | Supervisor Review Required | — | AUDIT/SIGNATURE | boolean | `finalization.supervisorReview.required` | finalization | 13 | RNICA editable (`:9726`) | — | not emitted | No | optional | always | none | JSONB | additive | PRESENT BUT NOT WIRED | Not part of `evaluate_finalization_readiness()` — setting it true does not block Lock. |
| Narrative / Admissions Order | Supervisor | Reviewed By | — | AUDIT/SIGNATURE | free text | `finalization.supervisorReview.reviewedBy` | finalization | 13 | RNICA editable (`:9727`) | — | not emitted | No | optional | always | none | JSONB | additive | PRESENT BUT NOT WIRED | |
| Narrative / Admissions Order | Supervisor | Review Date | — | AUDIT/SIGNATURE | date | `finalization.supervisorReview.reviewDate` | finalization | 13 | RNICA editable (`:9728`) | — | not emitted | No | optional | always | none | JSONB | additive | PRESENT BUT NOT WIRED | |
| Narrative / Admissions Order | Completion | **Patient / PCG acknowledgment** | — | AUDIT/SIGNATURE | signature | NOT FOUND IN REPOSITORY | — | 13 | — | — | — | No | — | — | — | — | — | MISSING FROM SNS | Only the clinician signs; there is no patient or caregiver acknowledgment field. |
| Narrative / Admissions Order | Completion | Lock | — | AUDIT/SIGNATURE | action | Lock action gated by `evaluate_finalization_readiness()` | n/a | 13 | clinician action | Screen 11 | not emitted | No | n/a | when all checks pass | server | assessment record | n/a | VERIFIED COMPLETE | Post-lock read-only enforcement at `RNICA.jsx:2163`. |
| Narrative / Admissions Order | Completion | Readiness blockers (list) | — | READINESS | derived | `checks` from `evaluate_finalization_readiness()` | n/a | 13 | none (derived) | Screens 11, 13 | not emitted | No | n/a | always | server | not persisted | n/a | VERIFIED COMPLETE | |
| Narrative / Admissions Order | Completion | Z0400 (signature of persons completing the record) | Z0400 | NOT VERIFIED | signatures | declared at `form_registry.py:416`; **not emitted by the mapper** (`hopeReportMapper.js:642-645` emits only Z0350 and Z0500) | — | 13 | — | — | — | No | — | — | — | — | — | PRESENT BUT NOT HARVESTED | Declared but never produced. |

---
## 5. TABLE B — HOPE-only items (harvested for HOPE, not part of the SFV trigger chain)

| Item code | Label | SNS field path | Screen | Exporter evidence | Backend declaration | Status |
|---|---|---|---|---|---|---|
| A0050 | Type of Record | constant `"1 - Add new record"` | 1 | `hopeReportMapper.js:554` | `form_registry.py:342` | PRESENT BUT NOT WIRED (hard-coded) |
| A0100 | Facility Provider Numbers | `agency.npi/.ccn/.facilityId` | 1 | `:482-489,555` | `:343` | PRESENT AND CORRECTLY PLACED |
| A0215 | Site of Service at Admission | `demographics.livingSituation.siteOfService` | 1 | `:491,556` | `:344` | PRESENT AND CORRECTLY PLACED |
| A0220 | Admission Date | `patient.socDate` → `admissionsOrder.levelOfCare.effectiveDate` → completion date | 1 | `:557` | `:345` | PRESENT AND CORRECTLY PLACED |
| A0250 | Reason for Record | `RECORD_REASON_BY_TIMEPOINT[timepoint]` | 1 | `:558` | `:346` | PRESENT AND CORRECTLY PLACED |
| A0270 | Discharge Date | `options.discharge.dischargeDate` | 1 | `:561` | `:347` | PRESENT AND CORRECTLY PLACED (discharge timepoint only) |
| A0500 | Legal Name of Patient | Facesheet `patient.firstName/.middleInitial/.lastName` | 1 | `:481,565` | `:348` | DUPLICATE OF FACESHEET (RNICA holds an editable copy) |
| A0550 | Patient Zip Code | `demographics.address.zip` | 1 | `:566` | `:349` | DUPLICATE OF FACESHEET |
| A0600 | SSN / Medicare (MBI) | `patient.ssn`, `patient.medicareNumber` | 1 | `:567` | `:350` | PRESENT AND CORRECTLY PLACED |
| A0700 | Medicaid Number | `patient.medicaidNumber` | 1 | `:568` | `:351` | PRESENT AND CORRECTLY PLACED |
| A0810 | Sex | `demographics.gender` → `SEX_MAP` | 1 | `:495,569` | `:352` | DUPLICATE OF FACESHEET |
| A0900 | Birth Date | `demographics.dob` → `patient.dob` | 1 | `:570` | `:353` | DUPLICATE OF FACESHEET |
| A1005 | Ethnicity | `demographics.ethnicity` | 1 | `:571` | `:354` | PRESENT BUT RESPONSE SET INCOMPLETE |
| A1010 | Race | `demographics.race` | 1 | `:572` | `:355` | PRESENT BUT RESPONSE SET INCOMPLETE |
| A1110 | Language (A preferred, B interpreter) | `demographics.preferredLanguage`, `.needsInterpreter` | 1 | `:573` | `:356` | PRESENT BUT RESPONSE SET INCOMPLETE |
| A1400 | Payer Information | `patient.primaryPayerType`, `.secondaryPayerType` | 1 | `:156-171,511,574` | `:357` | PRESENT AND CORRECTLY PLACED |
| A1805 | Admitted From | `demographics.livingSituation.admittedFrom` | 1 | `:492,575` | `:358` | PRESENT AND CORRECTLY PLACED |
| A1905 | Living Arrangements | `demographics.livingSituation.livingArrangement` | 7 (target) | `:493,576` | `:359` | PRESENT BUT MISPLACED |
| A1910 | Availability of Assistance | `demographics.livingSituation.availabilityOfAssistance` | 7 (target) | `:494,577` | `:360` | PRESENT BUT MISPLACED |
| A2115 | Reason for Discharge | `options.discharge.reasonCode/.reasonLabel` | 1 | `:562` | `:361` | PRESENT AND CORRECTLY PLACED (discharge timepoint) |
| F2000 | CPR Preference | `demographics.advancedCarePlanning.cprPreferenceAskedStatus/.codeStatusDate` | 9 | `:496,586` | `:365` | VERIFIED COMPLETE |
| F2100 | Life-sustaining treatments other than CPR | `…lifeSustainingAskedStatus/.lifeSustainingTreatmentPreferenceDate` | 9 | `:497,587` | `:366` | VERIFIED COMPLETE |
| F2200 | Hospitalization preference | `…hospitalizationAskedStatus/.hospitalizationPreferenceDate` | 9 | `:498,588` | `:367` | VERIFIED COMPLETE |
| F3000 | Spiritual / Existential Concerns | `spiritual.concernsAskedStatus/.concernsDiscussedDate` | 7 | `:510,589` | `:368` | VERIFIED COMPLETE |
| I0010 | Principal Diagnosis (+ category) | `diagnoses.primaryDiagnosis.icd10/.description/.hopeDiagnosisCategory` | 4 | `:503-508,598` | `:372` | VERIFIED COMPLETE |
| I0100 | Cancer | `diagnoses.hopeComorbidities.cancer` | 4 | `:440,536-541` | (via I0000 group) | VERIFIED COMPLETE |
| I0600 | Heart Failure | `diagnoses.hopeComorbidities.heartFailure` | 4 | `:441,545` | `:373` | VERIFIED COMPLETE |
| I0900 | PVD / PAD | `diagnoses.hopeComorbidities.pvdPad` | 4 | `:442` | (group) | VERIFIED COMPLETE |
| I0950 | Cardiovascular excluding HF | `diagnoses.hopeComorbidities.cardiovascularExclHF` | 4 | `:443` | (group) | VERIFIED COMPLETE |
| I1101 | Liver disease | `diagnoses.hopeComorbidities.liverDisease` | 4 | `:444` | (group) | VERIFIED COMPLETE |
| I1510 | Renal disease | `diagnoses.hopeComorbidities.renalDisease` | 4 | `:445` | (group) | VERIFIED COMPLETE |
| I2102 | Sepsis | `diagnoses.hopeComorbidities.sepsis` | 4 | `:446` | (group) | VERIFIED COMPLETE |
| I2900 | Diabetes Mellitus | `diagnoses.hopeComorbidities.diabetesMellitus` | 4 | `:447` | (group) | VERIFIED COMPLETE |
| I2910 | Neuropathy | `diagnoses.hopeComorbidities.neuropathy` | 4 | `:448` | (group) | VERIFIED COMPLETE |
| I4501 | Stroke | `diagnoses.hopeComorbidities.stroke` | 4 | `:449` | (group) | VERIFIED COMPLETE |
| I4801 | Dementia | `diagnoses.hopeComorbidities.dementia` | 4 | `:450` | (group) | VERIFIED COMPLETE |
| I5150 | Neurological Conditions | `diagnoses.hopeComorbidities.neurologicalConditions` | 4 | `:451` | (group) | VERIFIED COMPLETE |
| I5401 | Seizure Disorder | `diagnoses.hopeComorbidities.seizureDisorder` | 4 | `:452` | (group) | VERIFIED COMPLETE |
| I6202 | COPD | `diagnoses.hopeComorbidities.copd` | 4 | `:453,546` | `:374` | VERIFIED COMPLETE |
| I8005 | Other Medical Condition | `diagnoses.hopeComorbidities.other` — **no writer** | 4 | `:542,547` | `:375` | CONFLICTING |
| J0050 | Death is Imminent | `imminentDeath.appearsThreeDaysOrLess` | 8 | `:502,609` | `:379` | VERIFIED COMPLETE |
| J0900 | Pain Screening (A-D) | `pain.screenedForPain/.screeningDate/.painSeverityCategory/.standardizedPainToolType` | 3 | `:499,610` | `:380` | VERIFIED COMPLETE |
| J0905 | Pain Active Problem | derived from `pain.painIntensity.current` / `.painManagementPlan` / `.painLocation` | 3 | `:611` | `:381` | PRESENT BUT NOT WIRED |
| J0910 | Comprehensive Pain Assessment | `pain.comprehensiveAssessmentCompleted/.comprehensiveAssessmentDate` | 3 | `:612` | `:382` | PRESENT AND CORRECTLY PLACED |
| J0915 | Neuropathic Pain | `pain.neuropathicPain` | 3 | `:500,613` | `:383` | VERIFIED COMPLETE |
| J2030 | Screening for Shortness of Breath | `respiratory.shortnessOfBreathScreened`, `.screeningDate` | 6 | `:614` | `:384` | PRESENT AND CORRECTLY PLACED |
| J2040 | Treatment for Shortness of Breath | `respiratory.treatmentInitiated`, `.treatmentDate` | 6 | `:615` | `:385` | PRESENT AND CORRECTLY PLACED |
| M1190 | Skin Conditions | `skin.skinConditionsPresent` | 6 | `:625` | `:403` | VERIFIED COMPLETE |
| M1195 | Types of Skin Conditions | `skin.skinStatus` | 6 | `:626` | `:404` | PRESENT BUT RESPONSE SET INCOMPLETE |
| M1200 | Skin Treatments | derived via `deriveSkinTreatments(skin)` | 6 | `:353-358,627` | `:405` | PRESENT AND CORRECTLY PLACED |
| N0500 | Scheduled Opioid | `medications.scheduledOpioid` — **no writer** | 10 (would be) | `:633` | `:409` | PRESENT BUT NOT WIRED |
| N0510 | PRN Opioid | `medications.prnOpioid` — **no writer** | 10 (would be) | `:634` | `:410` | PRESENT BUT NOT WIRED |
| N0520 | Bowel Regimen | `medications.bowelRegimen` — **no writer** | 10 (would be) | `:530,635` | `:411` | PRESENT BUT NOT WIRED |
| Z0350 | Date Assessment Completed | `finalization.signatureDate` (with fallbacks) | 13 | `:479,642` | `:415` | VERIFIED COMPLETE |
| Z0400 | Signature of persons completing the record | not emitted | 13 | — | `:416` | PRESENT BUT NOT HARVESTED |
| Z0500 | Attestation | `finalization.signatureCertification` | 13 | `:644` | `:417` | VERIFIED COMPLETE |

**Count: 57 HOPE-only item rows.**

---

## 6. TABLE C — SFV-only items (trigger/workflow mechanics with no HOPE item code of their own)

| Label | SNS field path / symbol | Screen | Evidence | Status |
|---|---|---|---|---|
| SFV triggered-symptom derivation | `getSfvStatus().triggeredSymptoms` | 3/11 | `hopeReportMapper.js:404-406` | VERIFIED COMPLETE |
| SFV required flag | `getSfvStatus().required` | 3/11 | `:407` | VERIFIED COMPLETE |
| SFV due date (screening date + 2 calendar days) | `getSfvStatus().dueDate` | 3/11 | `:408,31-44` | VERIFIED COMPLETE |
| SFV status label | `getSfvStatus().statusLabel` | 3/11 | `:410-414` | VERIFIED COMPLETE |
| SFV in-person requirement note | `getSfvStatus().note` | 3/11 | `:415-419` | VERIFIED COMPLETE |
| SFV triggered-symptoms manual checkbox group | `sfv.triggeredSymptoms` | 3 | `RNICA.jsx:9413` | CONFLICTING (manual duplicate of the derived value) |
| SFV findings | `sfv.findings` | 3 | `RNICA.jsx:9414` | PRESENT BUT NOT HARVESTED |
| SFV notes | `sfv.notes` | 3 | `RNICA.jsx:9415` | PRESENT BUT NOT HARVESTED |
| Reason SFV not completed | `sfv.reasonNotCompleted` | 3 | `RNICA.jsx:9400` | PRESENT BUT NOT HARVESTED |
| Backend moderate/severe predicate | `_is_moderate_or_severe()` | backend | `hope_phase_b_engine.py:40,140-142` | VERIFIED COMPLETE |
| Backend symptom-group classifier (pain vs non-pain) | `_symptom_group_from_inputs()` | backend | `:145-156` | VERIFIED COMPLETE |
| Backend SFV alert reason | `_sfv_alert_reason()` | backend | `:136-137` | VERIFIED COMPLETE |
| Backend SFV/HUV task creation | `_create_task_if_missing()`, `_get_existing_open_task()` | backend | `:184+` | VERIFIED COMPLETE |
| Backend J2051 extraction from visit notes | `_extract_j2051_impacts_from_notes()` | backend | `visits.py:3611-3706` | VERIFIED COMPLETE |
| Backend J2051 impact application to a visit | `j2051_pain_impact`, `j2051_non_pain_impact` | backend | `visits.py:3916-3991` | VERIFIED COMPLETE |
| HUV1 window validation (days 6-15, RN only) | `validate_huv_visit_completion()` | backend | `hope_phase_b_engine.py:158-175` | VERIFIED COMPLETE |
| HUV2 window validation (days 16-30, RN only) | `validate_huv_visit_completion()` | backend | `:176-181` | VERIFIED COMPLETE |
| Day-number-from-election calculation | `_day_number_from_election()` | backend | `:89-92` | VERIFIED COMPLETE |
| Treatment declined (SOB) | `respiratory.treatmentDeclined` | 3/6 | `RNICA.jsx:9117` | PRESENT BUT NOT HARVESTED |
| Treatment declined — all other symptoms | NOT FOUND IN REPOSITORY | 3 | — | MISSING FROM SNS |

**Count: 20 SFV-only rows.**

---

## 7. TABLE D — HOPE-and-SFV items

| Item code | Label | SNS field path | Screen | Exporter | SFV role | Status |
|---|---|---|---|---|---|---|
| J2050 | Symptom Impact Screening (A completed, B date) | `sfv.symptomImpactScreeningCompleted`, `.symptomImpactScreeningDate`, `symptomImpact.assessmentDate` | 3 | `hopeReportMapper.js:616` | Starts the 2-day SFV clock | PRESENT BUT MISPLACED (module under Screen 8) |
| J2051A | Pain impact | `symptomImpact.pain` | 3 | `:617` | Trigger input | PRESENT AND CORRECTLY PLACED |
| J2051B | Shortness of Breath impact | `symptomImpact.shortnessOfBreath` | 3 | `:617` | Trigger input | CONFLICTING (competing `respiratory.sobSeverity`) |
| J2051C | Anxiety impact | `symptomImpact.anxiety` | 3 | `:617` | Trigger input | CONFLICTING (competing `neurological.symptomsDemeanor`) |
| J2051D | Nausea impact | `symptomImpact.nausea` | 3 | `:617` | Trigger input | CONFLICTING (competing `gastrointestinal.nausea`) |
| J2051E | Vomiting impact | `symptomImpact.vomiting` | 3 | `:617` | Trigger input | CONFLICTING (competing `gastrointestinal.vomiting`) |
| J2051F | Diarrhea impact | `symptomImpact.diarrhea` | 3 | `:617` | Trigger input | CONFLICTING (competing `gastrointestinal.diarrhea`) |
| J2051G | Constipation impact | `symptomImpact.constipation` | 3 | `:617` | Trigger input | CONFLICTING (competing `gastrointestinal.constipation`) |
| J2051H | Agitation impact | `symptomImpact.agitation` | 3 | `:617` | Trigger input | CONFLICTING (competing `neurological.symptomsDemeanor`) |
| J2052 | Symptom Follow-up Visit (A completed, B date) | `sfv.inPersonSfvCompleted`, `sfv.sfvDate` | 3 | `:618` | Completion evidence | PRESENT AND CORRECTLY PLACED |
| J2053A-H | SFV Symptom Impact | `sfv.symptomImpactAtSfv.{pain,shortnessOfBreath,anxiety,nausea,vomiting,diarrhea,constipation,agitation}` | 3 | `:619` | Follow-up values | PRESENT AND CORRECTLY PLACED |

**Count: 11 HOPE-and-SFV item rows (covering 19 discrete item codes once J2051A-H and J2053A-H are expanded).**

---

## 8. TABLE E — Facesheet-harvest fields

| Facesheet concept | Authoritative source | RNICA duplicate (editable) | Does RNICA need a distinct HOPE response? | Target read-only display | Safe removal plan |
|---|---|---|---|---|---|
| Patient first name | Facesheet `patient.firstName` | `demographics.firstName` (`RNICA.jsx:7984`) | No — the exporter already reads Facesheet (`hopeReportMapper.js:481,565`) | Screen 1 snapshot | Render read-only from Facesheet; retain the JSONB key for historical records and stop writing it. |
| Patient last name | Facesheet `patient.lastName` | `demographics.lastName` (`:7985`) | No | Screen 1 | Same. |
| Date of birth | Facesheet `patient.dob` | `demographics.dob` (`:7986`) | A0900 is satisfied by either; Facesheet is the safer source | Screen 1 | Remove the editable copy; mapper already falls back to `patient.dob` (`:570`). |
| Sex / gender | Facesheet `patient.sex` | `demographics.gender` (`:7987`) | **Yes, partially** — A0810 needs a CMS sex code; RNICA's gender list is broader | Screen 1 | Keep a distinct A0810 response; stop treating it as a Facesheet mirror. Requires authority decision. |
| MRN | Facesheet | none | No | Screen 1 | Already correct. |
| Address (street/city/state/county) | Facesheet | `demographics.address.*` (`:8011-8016`) | No (only ZIP is a HOPE item) | Screen 1 | Remove editable street/city/state/county; keep ZIP or read it from Facesheet. |
| ZIP | Facesheet | `demographics.address.zip` (`:8015`) | A0550 is satisfied by either | Screen 1 | Prefer Facesheet; mapper currently reads only the RNICA copy (`:566`). |
| Phone / alternate phone | Facesheet | `demographics.phone`, `.alternatePhone` (`:7989-7990`) | No | Screen 1 | Remove editable copies. |
| Emergency contact | Facesheet | `demographics.emergencyContact.*` (`:8022-8024`) | No | Screen 1 | Remove editable copies. |
| Attending physician | Facesheet | none found | No | Screen 1 care-team grid (`RNICA.jsx:9810`) | Already correct; confirm the attending is actually surfaced (`NOT VERIFIED`). |
| Chart primary diagnosis | Facesheet | `diagnoses.primaryDiagnosis.*` is a **distinct** RNICA assertion, not a mirror | Yes — I0010 requires an RNICA-asserted principal diagnosis and category | Screen 1 read-only chart dx; Screen 4 editable RNICA dx | No removal — keep both, labelled distinctly. |
| Admission date | Facesheet `patient.socDate` | none (only an order effective-date fallback) | A0220 | Screen 1 | Already correct. |
| Payer context | Facesheet `patient.primaryPayerType`/`.secondaryPayerType` | none | A1400 | Screen 1 | Already correct. |
| SSN / Medicare / Medicaid | Facesheet | none | A0600 / A0700 | Screen 1 | Already correct. |
| Agency NPI / CCN / Facility ID | Agency config | none | A0100 | Screen 1 | Already correct. |
| Care team (RN, LVN, SW, Chaplain, CHHA, Volunteer, Clinical Manager) | Facesheet | none | No | Screen 1 grid (`CARE_TEAM_DISPLAY_FIELDS`, `:9771-9778`) | Already correct. |

**Count: 16 Facesheet-harvest rows; 9 of them currently have an editable RNICA duplicate.**

---
## 9. TABLE F — Duplicate editable fields (every row violates "one authoritative owner")

| # | Clinical concept | Editable owner A | Editable owner B (and C…) | Vocabularies identical? | Proposed authoritative owner | Status |
|---|---|---|---|---|---|---|
| 1 | Patient identity (name, DOB, sex, phones, address, emergency contact) | Facesheet record | `demographics.*` (`RNICA.jsx:7984-8024`) | n/a | Facesheet | DUPLICATE OF FACESHEET |
| 2 | Pulse quality | `vitals.pulseQuality` (`:8779`, 5 values) | `cardiovascular.pulseQuality` (`:9088`, 9 values) | No | Cardiovascular (Screen 6) | CONFLICTING |
| 3 | Temperature | `vitals.temperature` + `.temperatureUnit` (`:8776-8777`) | `infection.temperature` (`:9166`, °F only) | No | Vitals (Screen 3) | CONFLICTING |
| 4 | Oxygen saturation | `vitals.oxygenSaturation` (`:8783`) | `respiratory.oxygenTherapy.satOnO2` (`:9135`) | n/a (different clinical meaning, undocumented) | Vitals for the measurement; Respiratory for on-O2 value — must be labelled | CONFLICTING |
| 5 | On room air | `vitals.oxygenSaturationOnRA` (`:8784`) | `respiratory.oxygenTherapy.onRoomAir` (`:9134`) | Yes | Respiratory (Screen 6) | CONFLICTING |
| 6 | Oxygen in use | `respiratory.oxygenTherapy.inUse` (`:9129`) | `safety.oxygenInUse` (`:9437`) | Yes | Respiratory (Screen 6); Safety reads read-only | CONFLICTING |
| 7 | Shortness of breath severity | `symptomImpact.shortnessOfBreath` (`:8887`, 0-3) | `respiratory.sobSeverity` (`:9116`, 5 labels) | No | Symptom Impact (Screen 3) for J2051B; Respiratory keeps a separate, clearly non-HOPE finding | CONFLICTING |
| 8 | Nausea | `symptomImpact.nausea` (`:8889`) | `gastrointestinal.nausea` (`:9180`) | No (0-3 vs labels) | Symptom Impact (Screen 3) | CONFLICTING |
| 9 | Vomiting | `symptomImpact.vomiting` (`:8890`) | `gastrointestinal.vomiting` (`:9181`) | No | Symptom Impact (Screen 3) | CONFLICTING |
| 10 | Diarrhea | `symptomImpact.diarrhea` (`:8891`) | `gastrointestinal.diarrhea` (`:9183`) | No | Symptom Impact (Screen 3) | CONFLICTING |
| 11 | Constipation | `symptomImpact.constipation` (`:8892`) | `gastrointestinal.constipation` (`:9184`) | No | Symptom Impact (Screen 3) | CONFLICTING |
| 12 | Anxiety | `symptomImpact.anxiety` (`:8888`, graded) | `neurological.symptomsDemeanor` "Anxiety" (`:9020`, ungraded) | No | Symptom Impact (Screen 3) | CONFLICTING |
| 13 | Agitation | `symptomImpact.agitation` (`:8893`) | `neurological.symptomsDemeanor` "Agitation" (`:9020`) | No | Symptom Impact (Screen 3) | CONFLICTING |
| 14 | SFV triggered symptoms | derived `getSfvStatus().triggeredSymptoms` | `sfv.triggeredSymptoms` (`:9413`) | Same 8 symptoms | Derived value | CONFLICTING |
| 15 | ADL transfer vs mobility transfer vs transfer safety | `musculoskeletal.adl.transferring` (`:9007`) | `musculoskeletal.mobility.transferAbility` (`:9327`); `safety.transferSafetyLevel` (`:9433`) | No (three vocabularies) | Functional Status (Screen 5) | CONFLICTING |
| 16 | Ambulation / activity level | `musculoskeletal.mobility.ambulatoryStatus` (`:9325`) | `skin.braden.activity` (`:9352`) | No | Functional Status (Screen 5); Braden keeps its scored subscale | CONFLICTING |
| 17 | Balance | `neurological.balance` (`:9041`, 5 values) | `musculoskeletal.balance` (`:9329`, 2 values) | No | Neurological (Screen 6) | CONFLICTING |
| 18 | Paralysis / motor deficit pattern | `neurological.deficitType` + `.affectedSide` (`:9069-9070`) | `musculoskeletal.paralysis` (`:9320`) | No | Neurological (Screen 6) | CONFLICTING |
| 19 | Rigidity | `musculoskeletal.rigidity` (`:9313`, graded) | `musculoskeletal.rigidityPresent` (`:9314`, boolean) | No | The graded field | CONFLICTING |
| 20 | Contractures | `musculoskeletal.contractures` (`:9315`) | `musculoskeletal.contracturesPresent` (`:9316`) | No | The graded field | CONFLICTING |
| 21 | ROM loss | `musculoskeletal.romLimitations` (`:9318`) | `musculoskeletal.musculoskeletalIssues` "ROM loss" (`:9319`) | No | `romLimitations` | CONFLICTING |
| 22 | Heart failure presence | `diagnoses.hopeComorbidities.heartFailure` (HOPE) | `cardiovascular.heartFailurePresent` (`:9104`); regex fallback `hasHeartFailure` (`hopeReportMapper.js:531`) | n/a | HOPE comorbidity (Screen 4) | CONFLICTING |
| 23 | Diabetes | `diagnoses.hopeComorbidities.diabetesMellitus` | `endocrine.diabetes.type` (`:9252`) | No | HOPE comorbidity for the I2900 answer; endocrine for management detail | CONFLICTING |
| 24 | Sepsis | `diagnoses.hopeComorbidities.sepsis` | `infection.currentInfections` "Sepsis" (`:9162`) | No | HOPE comorbidity (Screen 4) | CONFLICTING |
| 25 | Seizure | `diagnoses.hopeComorbidities.seizureDisorder` | `neurological.seizureHistory` (`:9050`); `neurological.symptomsDemeanor` "Seizure" | No | HOPE comorbidity (Screen 4) | CONFLICTING |
| 26 | Feeding tube / artificial feeding | `gastrointestinal.feedingTube.present/.type` (`:9198-9199`) | `nutrition.artificialFeeding` (`:9233`) | No | Nutrition (Screen 6) | CONFLICTING |
| 27 | Ostomy / urostomy | `gastrointestinal.ostomy.type` (`:9201`) | `genitourinary.urinaryStatus` "Urostomy" (`:9274`); `genitourinary.catheter.type` "Urostomy" (`:9281`) | No | GI for bowel ostomy; GU for urinary diversion — must be disambiguated | CONFLICTING |
| 28 | Urine characteristics | `genitourinary.urineCharacteristics` (`:9276`, 5) | `genitourinary.catheter.urineCharacteristics` (`:9286`, 7); `genitourinary.urineColor` (`:9277`) | No | One shared list | CONFLICTING |
| 29 | Skin colour findings | `cardiovascular.skinColor` (`:9097`) | `skin.skinStatus` Jaundice/Cyanotic/Mottled (`:9346`) | No | Skin (Screen 6) | CONFLICTING |
| 30 | Stasis ulcer | `cardiovascular.stasisUlcer` (`:9103`) | `skin.wounds[].woundType` (`:2334,2360`) | No | Skin wound list (Screen 6) | CONFLICTING |
| 31 | Wound documentation | `skin.wounds[]` structured list (`:2388-2424`) | `skin.woundImpairment` free text (`:9363`) | n/a | Structured list | CONFLICTING |
| 32 | Central venous access | `cardiovascular.centralVenousLine` (`:9101`) | `vitals.ivAssessment.type` "Central" (`:8794`) | No | IV assessment | CONFLICTING |
| 33 | Cool extremities | `cardiovascular.coolExtremities` (`:9102`) | `imminentDeath.indicators` "Cool/cold extremities" (`:9382`) | No | Cardiovascular for the finding; imminent-death list is a screening context | CONFLICTING |
| 34 | Cheyne-Stokes / apnoea | `respiratory.respirations` (`:9124`) | `imminentDeath.indicators` (`:9381`) | No | Respiratory for the finding | CONFLICTING |
| 35 | Urine output cessation | `genitourinary.urineOutput` "Anuria" (`:9293`) | `imminentDeath.indicators` "No urine output" (`:9381`) | No | GU for the finding | CONFLICTING |
| 36 | Firearms in home | `safety.firearmInHome` (`:9436`) | `safety.homeEnvironment` "Weapons/firearms" (`:9428`) | Yes | The dedicated boolean | CONFLICTING |
| 37 | Disaster Level 1 vs Level 2 conditions | `safety.disasterLevelOneConditions` (`:9448`) | `safety.disasterLevelTwoConditions` (`:9452`) | **Identical lists** | One condition list + a computed level | CONFLICTING |
| 38 | Pets in the home | `safety.homeEnvironment` "Pets" (`:9428`) | `personalCare.volunteerServices` "Pet care" (`:9588`) | No | A dedicated household-composition field (currently missing) | CONFLICTING |
| 39 | Religion / faith tradition | `demographics.religion` (`:8000`) | `spiritual.patientFaith` (`:9526`) | No | Spiritual (Screen 7) | CONFLICTING |
| 40 | Psychiatric history | `neurological.psychiatricHistoryType` (`:9051`) | `psychosocial.psychosocialHistory` (`:9503`) | No | Psychosocial (Screen 7) | CONFLICTING |
| 41 | Support person identity | `demographics.pcg.name/.relationship` (`:8056-8057`) | `psychosocial.primarySupportPerson/.supportRelationship` (`:9480-9481`); `demographics.emergencyContact.*` (`:8022-8023`) | No | PCG (Screen 7) | CONFLICTING |
| 42 | Caregiver availability hours | `demographics.pcg.caregiverEvaluation.availabilityForCare` (`:8092`) | `demographics.livingSituation.availabilityOfAssistance` (A1910, `:8163`) | No | A1910 is HOPE-authoritative | CONFLICTING |
| 43 | Caregiver support adequacy | `demographics.pcg.caregiverEvaluation.supportSystemAdequacy` (`:8115`) | `psychosocial.familySocialSupport` (`:9479`) | No | Psychosocial (Screen 7) | CONFLICTING |
| 44 | Caregiver education / training needs | `demographics.pcg.caregiverEvaluation.trainingNeeds` (`:8095`) | `teachingNeeds.teachingTopics` (`:9623`) | No | Teaching Needs (Screen 7) | CONFLICTING |
| 45 | Social work need | `psychosocial.socialWorkVisitNeeded` (`:9514`) | `referrals.socialWork.referred` (`:9693`) | n/a | Referrals (gates Lock) | CONFLICTING |
| 46 | Chaplain need | `spiritual.chaplainNeeded` (`:9539`) | `referrals.spiritualCare.referred` (`:9695`) | n/a | Referrals | CONFLICTING |
| 47 | Counselling / community-resource referral | `psychosocial.interventionPlan` (`:9511`) | `personalCare.communityResources` (`:9592`); `referrals.*` | No | Referrals for referrals; personal care for resources | CONFLICTING |
| 48 | Equipment / DME | `safety.dmeItems[]` (`:2426-2494`) | `personalCare.equipmentSupplyNeeds` (`:9599`); `musculoskeletal.assistiveDevices` (`:9322`) | No (three lists) | DME status tracker owns the order state; the others are indications | CONFLICTING |
| 49 | Visit frequency | `admissionsOrder.visitFrequency[]` (`:3263-3300`) | `personalCare.aideVisitPreferences.frequency` (`:9580`) | No | Admissions order (Screen 10) | CONFLICTING |
| 50 | HOPE submission tracking | `finalization.hopeSubmissionNumber`, `.hopeAlreadySubmitted` (`:9722-9723`) | `rnica_assessments.hope_export_batch_id` etc. (`rnica_hope_workflow_service.py`) | n/a | The server-side workflow service | CONFLICTING |
| 51 | Clinical narrative | `finalization.clinicalNarrative` (`:9714`) | `diagnoses.clinicalNarrative` (renderer at `:2029`, no card) | n/a | Finalization (Screen 13) — Lock gate must follow | CONFLICTING |
| 52 | Orientation | `neurological.orientation.time/.place/.person/.situation` (`:9022-9025`) | `neurological.orientation.disoriented` (`:9026`) | n/a | The four positive flags | CONFLICTING |

**Count: 52 duplicate/conflicting editable-field groups.**

### 9.1 Calculated duplicates (audit item C)

| Calculation | Persisted? | Competing persisted copy? | Evidence | Status |
|---|---|---|---|---|
| BMI | Yes — `vitals.bmi` | No. `NutritionAnthropometricReferenceCard` displays it read-only without persisting. | `RNICA.jsx:2883-2895, 2946` | VERIFIED COMPLETE |
| ADL total | Not computed | n/a | — | MISSING FROM SNS |
| Complete-dependence count | Not computed | n/a | — | MISSING FROM SNS |
| Braden total | Not computed | `skin.pressureInjuryRisk` persists a **band** whose labels quote Braden ranges | `RNICA.jsx:9349-9356` | CONFLICTING |
| PAINAD total / FLACC total | Not computed | n/a | — | MISSING FROM SNS |
| BIMS total | Not computed | n/a | — | MISSING FROM SNS |
| Symptom trigger status | Not persisted (derived) | **Yes** — `sfv.triggeredSymptoms` is a manual duplicate | `hopeReportMapper.js:404-406` vs `RNICA.jsx:9413` | CONFLICTING |
| SFV due date | Not persisted (derived) | No | `hopeReportMapper.js:408` | VERIFIED COMPLETE |
| Screen completion count | Not persisted (derived) | No | `RNICA.jsx:11068` | VERIFIED COMPLETE |
| Readiness blocker count | Not persisted (derived) | No | `rnica_finalization_service.py:169` | VERIFIED COMPLETE |
| LCD evaluation result | Not persisted (recomputed) | No | `RNICA.jsx:1685` | VERIFIED COMPLETE |
| Weight-loss percentage | Not persisted as a number; accepted into a free-text field | `nutrition.weightLossPastSixMonths` holds "lbs or %" | `RNICA.jsx:3005-3006, 9220` | CONFLICTING |
| Caregiver willingness / capability scores | Persisted manually (1-5) | Duplicate the underlying qualitative fields with no computation | `RNICA.jsx:8101-8114` | CONFLICTING |
| Decline vs last assessment | Not persisted (derived from history API) | No | `RNICA.jsx:2715` | VERIFIED COMPLETE |

---
## 10. TABLE G — Missing SNS fields

| # | Missing field | Target screen | Nearest existing SNS field (if any) | Why the nearest field does not satisfy it | Status |
|---|---|---|---|---|---|
| 1 | BP position (sitting / lying / standing) | 3 | `cardiovascular.bpSymptoms` "Orthostatic" (`:9086`) | A finding, not a measurement position | MISSING FROM SNS |
| 2 | Per-vital "unable to assess" state | 3 | `triState` type on a few cardiovascular fields (`:9089`) | Not available on vitals | MISSING FROM SNS |
| 3 | FLACC total score | 3 | — | — | MISSING FROM SNS |
| 4 | PAINAD total score | 3 | — | — | MISSING FROM SNS |
| 5 | Post-intervention pain reassessment | 3 | `pain.painManagementPlan` (`:8874`) | Plan, not reassessment result | MISSING FROM SNS |
| 6 | Treatment-declined response for symptoms other than SOB | 3 | `respiratory.treatmentDeclined` (`:9117`) | SOB only | MISSING FROM SNS |
| 7 | Secondary-diagnosis related/unrelated classification | 4 | `SecondaryDiagnosesCard` rows (`:2176-2232`) | Rows carry only ICD-10 + description | MISSING FROM SNS |
| 8 | Diagnosis source / confirmation | 4 | — | — | MISSING FROM SNS |
| 9 | I8005 "Other Medical Condition" checkbox | 4 | `HOPE_COMORBIDITY_CATEGORIES` (`:2496-2511`) | 14 entries, no `other` | MISSING FROM SNS (exporter expects it) |
| 10 | Applicability / "None" state for PPS, KPS, ECOG, FAST, NYHA | 5 | blank value | Blank ≠ not applicable | MISSING FROM SNS |
| 11 | FAST inline stage interpretation | 5 | `performanceStatus.fastStage` free text (`:8981`) | Free text, clinician-supplied | MISSING FROM SNS |
| 12 | Ambulation as a scored ADL | 5 | `musculoskeletal.mobility.ambulatoryStatus` (`:9325`) | Different scale; cannot contribute to a total | MISSING FROM SNS |
| 13 | Continence as a scored ADL | 5 | `genitourinary.urinaryStatus`, `gastrointestinal.bowelStatus` | Clinical status, not an ADL score | MISSING FROM SNS (current SNS authority excludes it) |
| 14 | ADL total score | 5 | — | — | MISSING FROM SNS |
| 15 | Complete-dependence count | 5 | — | — | MISSING FROM SNS |
| 16 | BIMS total score | 6 | — | — | MISSING FROM SNS |
| 17 | Per-site pulse quality (apical / pedal / radial / femoral) | 6 | `cardiovascular.pulseSites` + single `pulseQuality` (`:9087-9088`) | Sites are recorded; quality is not site-scoped | MISSING FROM SNS |
| 18 | Braden total score | 6 | `skin.pressureInjuryRisk` band (`:9356`) | Band is chosen manually | MISSING FROM SNS |
| 19 | Cachexia response | 6 | `nutrition.appetite` "Anorexic" (`:9221`) | Appetite ≠ cachexia | MISSING FROM SNS |
| 20 | Discrete weight-loss-percentage field (>10% / 6 months) | 6 | `nutrition.weightLossPastSixMonths` free text (`:9220`) | Free text "lbs or %" is not machine-evaluable | MISSING FROM SNS |
| 21 | Skin assessment link to a separate wound document | 6 | — | — | NOT FOUND IN REPOSITORY |
| 22 | Patient ability to understand / participate in own care | 7 | `pcg.caregiverEvaluation.cognitiveAbility` (`:8086`) | Caregiver-scoped | MISSING FROM SNS |
| 23 | Interpreter offered / declined (beyond A1110B need) | 7 | `demographics.needsInterpreter` (`:7999`) | Need only | MISSING FROM SNS |
| 24 | Caregiver communication need | 7 | `neurological.hearing`/`.communication` | Patient-scoped | MISSING FROM SNS |
| 25 | Sign-language need | 7 | `neurological.hearing` (`:9039`) | No sign-language option anywhere | MISSING FROM SNS |
| 26 | Patient medication self-administration ability | 7/8 | `pcg.ableToAdministerMeds` (`:8064`) | Caregiver-scoped | MISSING FROM SNS |
| 27 | Special event / desire before dying | 7 | `psychosocial.patientConcerns` "Unfinished business" (`:9489`) | A concern, not a wish | MISSING FROM SNS |
| 28 | Young children in the home | 7 | `psychosocial.caregiverFamilyConcerns` "Children/family coping" (`:9498`) | A concern, not household composition | MISSING FROM SNS |
| 29 | Pets in the home as a caregiving/psychosocial fact | 7 | `safety.homeEnvironment` "Pets" (`:9428`) | Recorded as a hazard | MISSING FROM SNS |
| 30 | Advance directives as a teaching topic | 7 | `teachingNeeds.teachingTopics` (`:9623-9637`) | 13 topics, none is advance directives | MISSING FROM SNS |
| 31 | Homemaker referral | 7 | `personalCare.aideTasks` housekeeping/laundry (`:9574-9575`) | Aide task, not a referral | MISSING FROM SNS |
| 32 | Therapy (PT / OT / Speech) referral | 7 | `admissionsOrder` discipline-frequency rows (`:3263-3300`) | An order, not a referral | MISSING FROM SNS |
| 33 | Massage / music / pet / art therapy referral | 7 | `personalCare.volunteerServices` (`:9585-9589`) | Volunteer need, not a referral | MISSING FROM SNS |
| 34 | Other referral (free text) | 7 | `referrals.notes` (`:9703`) | Shared notes field | MISSING FROM SNS |
| 35 | Referral lifecycle status (pending / accepted / completed) | 7 | boolean `referred` flags | No status | MISSING FROM SNS |
| 36 | Referral-scoped audit history | 7/13 | general amendment history | Not referral-scoped | NOT FOUND IN REPOSITORY |
| 37 | Bereavement referral (matching `bereavement.bereavementVisitNeeded`) | 7 | `bereavement.bereavementVisitNeeded` (`:9560`) | Never reaches the referral-review gate | PRESENT BUT NOT WIRED |
| 38 | Braden read-only summary on Safety | 8 | — | — | NOT FOUND IN REPOSITORY |
| 39 | Safety-scoped medication-administration concern | 8 | `pcg.ableToAdministerMeds` | Capability, not risk | MISSING FROM SNS |
| 40 | Safety source links | 8 | — | — | NOT FOUND IN REPOSITORY |
| 41 | Imminent-death indicators: increased fatigue | 8 | `imminentDeath.indicators` (`:9379-9383`) | Not in the 11-value list | MISSING FROM SNS |
| 42 | Imminent-death indicators: increased agitation | 8 | `symptomImpact.agitation` (J2051H) | Not in the imminent-death list | MISSING FROM SNS |
| 43 | Imminent-death indicators: bowel/bladder decline | 8 | "No urine output" (`:9381`) | An endpoint, not a decline; no bowel equivalent | MISSING FROM SNS |
| 44 | Goals of care (narrative) | 9 | `finalization.clinicalNarrative` | Not goals-scoped | MISSING FROM SNS |
| 45 | Non-covered items | 10 | declared in nav metadata only (`:190,221`) | No field exists | PRESENT BUT NOT WIRED |
| 46 | `medications.scheduledOpioid` / `.prnOpioid` / `.bowelRegimen` inputs (N0500-N0520) | 10 | `ordersHub` medication orders | Different store; not read by the mapper | PRESENT BUT NOT WIRED |
| 47 | `chhaPoc.completed` writer | 10 | — | Gate exists server-side with no located writer | REQUIRES AUTHORITY REVIEW |
| 48 | Patient / PCG acknowledgment signature | 13 | `finalization.clinicianSignature` | Clinician only | MISSING FROM SNS |
| 49 | Z0400 emission | 13 | declared at `form_registry.py:416` | Not emitted by the mapper | PRESENT BUT NOT HARVESTED |
| 50 | Disease trajectory reachable UI | 13 | `diagnoses.diseaseTrajectory` (`:2055`) | Card is unreachable | PRESENT BUT NOT WIRED |
| 51 | Uploaded records / referral source / hospital documentation | 1 | — | — | NOT FOUND IN REPOSITORY |

**Count: 51 missing/unwired field rows.**

---

## 11. TABLE H — Incomplete response sets

| # | Field | Current response set | Why it is incomplete | Status |
|---|---|---|---|---|
| 1 | `demographics.race` (A1010) | White, Black/African American, Asian, American Indian/Alaska Native, Native Hawaiian/Pacific Islander, Other | CMS HOPE A1010 uses a much larger discrete code set with Asian and NHPI sub-ethnicities; the exact list is `NOT VERIFIED` from this repository | PRESENT BUT RESPONSE SET INCOMPLETE |
| 2 | `demographics.ethnicity` (A1005) | Hispanic/Latino, Not Hispanic/Latino, Unknown | Exact CMS A1005 set `NOT VERIFIED`; the mapper performs no code lookup | PRESENT BUT RESPONSE SET INCOMPLETE |
| 3 | `demographics.preferredLanguage` (A1110A) | English, Spanish, Chinese, Vietnamese, Tagalog, Korean, Other | "Other" has no free-text companion, so an unlisted language cannot be named | PRESENT BUT RESPONSE SET INCOMPLETE |
| 4 | `pain.assessmentTool` | `["Numeric (0-10)"]` | Single option; PAINAD/FLACC cannot be selected despite having their own cards | PRESENT BUT RESPONSE SET INCOMPLETE |
| 5 | `performanceStatus.fast` | 1,2,3,4,5,6a-6e,7a-7f | Bare codes with no inline interpretation, unlike ECOG/NYHA | PRESENT BUT RESPONSE SET INCOMPLETE |
| 6 | PPS/KPS/ECOG/FAST/NYHA | numeric/stage values only | No "not applicable" value | PRESENT BUT RESPONSE SET INCOMPLETE |
| 7 | `neurological.consciousness` | Alert, Lethargic, Obtunded, Stuporous, Comatose, Awake, Minimally responsive, Coma | Contains synonym pairs (Comatose/Coma, Alert/Awake) | PRESENT BUT RESPONSE SET INCOMPLETE |
| 8 | `neurological.sleepRest.sleepPattern` | 10 values | Mixes patterns with satisfaction statements | PRESENT BUT RESPONSE SET INCOMPLETE |
| 9 | `cardiovascular.peripheralCirculation` / `.heartSounds` | free text | Uncontrolled where a vocabulary is expected | PRESENT BUT RESPONSE SET INCOMPLETE |
| 10 | `respiratory.exertionLevel` | 8 values | Mixes exertion level with breathing pattern | PRESENT BUT RESPONSE SET INCOMPLETE |
| 11 | `respiratory.lungSounds` | 9 values | Crackles and Rales are synonyms | PRESENT BUT RESPONSE SET INCOMPLETE |
| 12 | `respiratory.respirations` (pattern) | 11 values | Regular/Normal duplication | PRESENT BUT RESPONSE SET INCOMPLETE |
| 13 | `respiratory.coughType` | None/Productive/Non-productive/Hemoptysis/Barrel chest | "Barrel chest" is not a cough type | PRESENT BUT RESPONSE SET INCOMPLETE |
| 14 | `gastrointestinal.abdomen` | single-select radio, 7 values | Findings commonly co-occur | PRESENT BUT RESPONSE SET INCOMPLETE |
| 15 | `gastrointestinal.stoolCharacter` | Normal/Bloody/Colostomy/Ileostomy | Mixes stool character with ostomy presence | PRESENT BUT RESPONSE SET INCOMPLETE |
| 16 | `genitourinary.urinaryStatus` | 11 values, single-select | Conflates continence type, device and symptoms | PRESENT BUT RESPONSE SET INCOMPLETE |
| 17 | `musculoskeletal.weakness` | None/Mild/Moderate/Severe/Paralysis | "Paralysis" is not a severity level | PRESENT BUT RESPONSE SET INCOMPLETE |
| 18 | `skin.skinStatus` (M1195) | Intact, Dry, Fragile, Edematous, Bruising, Rash, Jaundice, Cyanotic, Mottled | See the side-by-side in §15 item 15 | PRESENT BUT RESPONSE SET INCOMPLETE |
| 19 | `safety.homeEnvironment` | 10 values | Mixes protective factors with hazards under a "Hazards" label | PRESENT BUT RESPONSE SET INCOMPLETE |
| 20 | `imminentDeath.indicators` | 11 values | Missing increased fatigue, increased agitation, bowel/bladder decline | PRESENT BUT RESPONSE SET INCOMPLETE |
| 21 | `nutrition.weightLossPastSixMonths` | free text "lbs or %" | Not machine-evaluable against a >10% threshold | PRESENT BUT RESPONSE SET INCOMPLETE |
| 22 | `nutrition.dietType` | free text | No diet-order vocabulary for POC reuse | PRESENT BUT RESPONSE SET INCOMPLETE |
| 23 | `teachingNeeds.teachingTopics` | 13 topics | Advance directives absent | PRESENT BUT RESPONSE SET INCOMPLETE |
| 24 | `referrals.*` | boolean per discipline | No status, no homemaker/therapy/massage/music/pet/art/other | PRESENT BUT RESPONSE SET INCOMPLETE |
| 25 | `legacyReviewItems` completeness checking | F2000, F2100, F2200, F3000, A1400, J0900, J0915 | Only 7 of ~57 harvested item codes are completeness-checked | PRESENT BUT RESPONSE SET INCOMPLETE |
| 26 | `demographics.pcg.caregiverEvaluation.availabilityForCare` vs A1910 | two different hour vocabularies | Cannot be reconciled programmatically | PRESENT BUT RESPONSE SET INCOMPLETE |

**Count: 26 incomplete response sets.**

---

## 12. TABLE I — Unverified item codes and lifecycle rules

| # | Item / rule | What is unverified | Why it matters | Status |
|---|---|---|---|---|
| 1 | A1005 / A1010 CMS code sets | The authoritative CMS HOPE response sets are not present anywhere in this repository (no code map exists for them in `hopeReportMapper.js`, unlike A0215/A1805/A1905) | Any "correction" of the response sets would be guesswork | NOT VERIFIED |
| 2 | A1910 emitted codes | `ASSISTANCE_MAP` is used via plain `lookup()`, not `officialCodeLookup()`; whether its codes are the official CMS A1910 codes is unproven | HOPE submission correctness | NOT VERIFIED |
| 3 | A0810 for non-binary / other gender values | `SEX_MAP` behaviour for RNICA's non-CMS gender values is unverified | Could emit a placeholder for a real patient | NOT VERIFIED |
| 4 | N0500 / N0510 / N0520 semantics | RNICA labels them BIMS; the exporter treats them as opioid/bowel-regimen items | One of the two is wrong; both cannot be right | CONFLICTING |
| 5 | M1190 on `performanceStatus` | `SIDEBAR_CONFIG:209` and the PPS card both claim M1190, which the exporter assigns to skin | Mislabelled HOPE tagging | CONFLICTING |
| 6 | J0050 on `diagnoses.terminalPrognosis` | Card and field carry `hopeCode: "J0050"` but the exporter reads `imminentDeath` | Mislabelled HOPE tagging | CONFLICTING |
| 7 | `hopeComorbidities` note field key | The rendered "Additional Note (optional)" (`RNICA.jsx:2680`) has an unconfirmed persisted key | Cannot be mapped or migrated confidently | NOT VERIFIED |
| 8 | `demographics.pcg.hasPcg` key | The radio at `:8031-8034` has an unconfirmed `onChange` target | Conditional-visibility logic depends on it | NOT VERIFIED |
| 9 | `admissionsOrder.visitFrequency[]` row keys | Row field names inside `DisciplineFrequencyOfVisitCard` are unconfirmed beyond the rendered labels | POC/order mapping | NOT VERIFIED |
| 10 | `chhaPoc.completed` writer | The Lock gate reads it; no UI writer was located | A Lock gate that cannot be satisfied is a workflow trap | REQUIRES AUTHORITY REVIEW |
| 11 | `PatientAllergies` renderer persistence | The component body was not located; its data source and persistence target are unknown | Allergy data provenance | NOT VERIFIED |
| 12 | `deriveSkinTreatments()` inputs | The function name is confirmed; its exact input set is unconfirmed | M1200 correctness | NOT VERIFIED |
| 13 | HOPE lifecycle applicability (Admission vs HUV vs Discharge) | `HOPE_ADMISSION_ITEM_CODES` and `HOPE_HUV_ITEM_CODES` differ only by `HOPE_PREFERENCES_ITEM_CODES` (`form_registry.py:420-437`); which RNICA fields are required at which timepoint is not encoded per field | A field may be mandatory at one timepoint and not another | NOT VERIFIED |
| 14 | Whether AI structured-finding writes require explicit acceptance on every path | `applyStructuredFindings.js` exists with tests, but per-path acceptance was not traced | AI must not silently answer a HOPE/SFV item | REQUIRES AUTHORITY REVIEW |
| 15 | Attending physician on Screen 1 | Not present in `CARE_TEAM_DISPLAY_FIELDS` (`:9771-9778`); whether it is surfaced elsewhere is unconfirmed | Facesheet completeness | NOT VERIFIED |
| 16 | Freshness state on Screen 12 | Not located | AI provenance requirement | NOT VERIFIED |
| 17 | Backend SFV trigger vs frontend SFV trigger reconciliation | Two independent implementations (`hope_phase_b_engine.py` from visit notes; `getSfvStatus()` from `form_data`); no reconciliation code was found | They can disagree for the same patient | REQUIRES AUTHORITY REVIEW |
| 18 | Whether any consumer constrains the ADL 0-5 scale | No HOPE item and no located LCD criterion consumes ADL values | Changing the scale may be free, or may break an unlocated consumer | NOT VERIFIED |
| 19 | A0220 fallback to `completionDate` | The third fallback in the admission-date chain (`hopeReportMapper.js:557`) can emit the signature date as the admission date | Clinically and financially significant | REQUIRES AUTHORITY REVIEW |
| 20 | `I0000` group code | The mapper emits a group row with code `I0000` (`:603`) that is not in any `form_registry.py` list | May not be a real CMS code | NOT VERIFIED |

**Count: 20 unverified/authority-review items.**

> **Unverified does not mean optional; implementation must stop until repository or controlling specification proves the rule.**

---

## 13. AI ownership statement (Screen 12)

`RNICA_THIRTEEN_SCREENS` gives the AI Action Center `moduleKeys: []`
(`rnicaThirteenScreenTaxonomy.js:106-118`), which is the structural proof
that AI owns no clinical field. AI output is advisory and cannot satisfy a
missing HOPE or SFV response, because `evaluate_finalization_readiness()`
reads `form_data` and `getSfvStatus()` reads `formData.symptomImpact` /
`formData.sfv` — neither consults AI output. The one caveat is
`applyStructuredFindings.js` / `structured_findings.py`, which *can* write
clinical paths including `symptomImpact.*` and `neurological.hopeItems.n0500`;
per-path acceptance semantics are recorded as `REQUIRES AUTHORITY REVIEW`
(Table I #14).

---
## 14. "Communications & Other Factors" — full decomposition

The legacy screen-12 block is not a single SNS section. Every element
described in the directive is assigned below to exactly one owning screen.

| Legacy element | Target screen | Current SNS location | Status |
|---|---|---|---|
| Site of Service (A0215) | 1 Evidence & Intake | `demographics.livingSituation.siteOfService` (`RNICA.jsx:8128`) | PRESENT AND CORRECTLY PLACED |
| Admitted From (A1805) | 1 Evidence & Intake | `demographics.livingSituation.admittedFrom` (`:8141`) | PRESENT AND CORRECTLY PLACED |
| Preferred language (A1110A) | 1 Evidence & Intake | `demographics.preferredLanguage` (`:7997`) | PRESENT BUT RESPONSE SET INCOMPLETE |
| Interpreter need (A1110B) | 1 Evidence & Intake | `demographics.needsInterpreter` (`:7999`) | PRESENT AND CORRECTLY PLACED |
| Ethnicity (A1005) / Race (A1010) | 1 Evidence & Intake | `demographics.ethnicity` / `.race` (`:7992-7995`) | PRESENT BUT RESPONSE SET INCOMPLETE |
| Living Arrangements (A1905) | **7 Caregiver & Support** | `demographics.livingSituation.livingArrangement` (`:8155`) | PRESENT BUT MISPLACED |
| Availability of Assistance (A1910) | **7 Caregiver & Support** | `demographics.livingSituation.availabilityOfAssistance` (`:8163`) | PRESENT BUT MISPLACED |
| Patient ability to understand / participate in own care | 7 Caregiver & Support | — | MISSING FROM SNS |
| Interpreter offered / declined (beyond A1110) | 7 Caregiver & Support | partial: `teachingNeeds.teachingMethods` "Interpreter used" (`:9643`) | PRESENT BUT RESPONSE SET INCOMPLETE |
| Caregiver communication need | 7 Caregiver & Support | — | MISSING FROM SNS |
| Hearing / sign-language need | 7 Caregiver & Support | partial: `neurological.hearing` (`:9039`) | PRESENT BUT RESPONSE SET INCOMPLETE |
| Responsible-party information | 9 ACP & Goals of Care (owner), 7 read-only | `demographics.advancedCarePlanning.decisionMaker/.poaName/.poaPhone` (`:8194-8196`) | PRESENT AND CORRECTLY PLACED |
| Patient medication self-administration ability | 8 Safety & Clinical Risk | — | MISSING FROM SNS |
| Responsible medication administrator | 7 Caregiver & Support | `demographics.pcg.ableToAdministerMeds` (`:8064`) | PRESENT BUT MISPLACED |
| Military service (patient/spouse) | 7 Caregiver & Support | `demographics.militaryService` (`:8003`) | PRESENT BUT MISPLACED |
| Special event / desire before dying | 7 Caregiver & Support | — | MISSING FROM SNS |
| Caregiver anxiety | 7 Caregiver & Support | `demographics.pcg.anxietyLevel` (`:8062`) | PRESENT BUT MISPLACED |
| Caregiver health | 7 Caregiver & Support | `demographics.pcg.healthStatus` (`:8060`) | PRESENT BUT MISPLACED |
| Caregiver ability to participate | 7 Caregiver & Support | `demographics.pcg.caregiverEvaluation.cognitiveAbility` (`:8086`) + `.physicalAbility` (`:8083`) + `.emotionalReadiness` (`:8089`) | PRESENT BUT MISPLACED |
| Children in home | 7 Caregiver & Support | — | MISSING FROM SNS |
| Pets | 7 Caregiver & Support | `safety.homeEnvironment` "Pets" (`:9428`) | PRESENT BUT MISPLACED |
| Medication-administration capability (caregiver) | 7 Caregiver & Support | `demographics.pcg.ableToAdministerMeds` (`:8064`) | PRESENT BUT MISPLACED |
| Education needed — disease process | 7 Caregiver & Support | `teachingNeeds.teachingTopics` "Diagnosis and disease process" (`:9624`) | PRESENT AND CORRECTLY PLACED |
| Education needed — medications | 7 Caregiver & Support | `teachingNeeds.teachingTopics` medication entries (`:9625-9630`) | PRESENT AND CORRECTLY PLACED |
| Education needed — advance directives | 7 Caregiver & Support | not a teaching topic; only `psychosocial.patientConcerns` "Want/need help with advance directives" (`:9492`) | MISSING FROM SNS |
| Education needed — other | 7 Caregiver & Support | `teachingNeeds.teachingTopics` "Other education" + `.teachingTopicsOther` (`:9636-9638`) | PRESENT AND CORRECTLY PLACED |
| CPR preference (F2000) | 9 ACP & Goals of Care | `demographics.advancedCarePlanning.cprPreferenceAskedStatus` (`:8170`) | PRESENT AND CORRECTLY PLACED |
| Life-sustaining treatment (F2100) | 9 ACP & Goals of Care | `…lifeSustainingAskedStatus` (`:8177`) | PRESENT AND CORRECTLY PLACED |
| Hospitalization preference (F2200) | 9 ACP & Goals of Care | `…hospitalizationAskedStatus` (`:8185`) | PRESENT AND CORRECTLY PLACED |

**Decomposition result:** 29 elements. 11 correctly placed, 10 present but
on the wrong screen, 2 present with incomplete response sets (plus 3 HOPE
demographic items already counted as incomplete), 6 missing from SNS. The
single biggest correction to earlier drafts is that **caregiver health,
caregiver anxiety, caregiver medication-administration capability, caregiver
ability to participate and military service all already exist** — they are
misplaced, not missing.

---

## 15. Missing-field audit (detailed, per the directive's list)

For each alleged gap: screenshot evidence (as described in the directive
text — the images themselves were not viewable), repository search result,
current path if found, persistence path, target path, response set,
validation, lifecycle applicability, implementation status.

1. **Incomplete A1010 / A1005 response sets.** Described: full CMS race and
   ethnicity sets. Repo: `RNICA.jsx:7992-7995` — 6 race values, 3 ethnicity
   values; exporter passthrough at `hopeReportMapper.js:571-572`. Persisted:
   `form_data.demographics.race/.ethnicity` (JSONB arrays). Target path:
   unchanged. Response set: **must come from CMS HOPE guidance — not
   derivable from this repository.** Validation: none today. Lifecycle: HOPE
   Admission and HUV (`HOPE_ADMIN_ITEM_CODES` appears in both, `form_registry.py:420-437`).
   Status: `PRESENT BUT RESPONSE SET INCOMPLETE` / code set `NOT VERIFIED`.
2. **Communication / participation fields.** Described: patient ability to
   understand and participate. Repo: no match; `neurological.communication`
   and `.cognition` describe capability only. Target: Screen 7.
   Status: `MISSING FROM SNS`.
3. **Medication self-administration (patient).** Repo: no match.
   Status: `MISSING FROM SNS`.
4. **Responsible medication administrator.** Repo: **found** —
   `demographics.pcg.ableToAdministerMeds` (`RNICA.jsx:8064`), response set
   Yes / No / With training. Persisted: JSONB. Target screen: 7.
   Status: `PRESENT BUT MISPLACED`.
5. **Special event / desire before dying.** Repo: no match.
   Status: `MISSING FROM SNS`.
6. **Military service.** Repo: **found** — `demographics.militaryService`
   (`:8003-8004`), Yes / No / Unknown. Related: `personalCare.communityResources`
   "Veteran services" (`:9595`). Target screen: 7.
   Status: `PRESENT BUT MISPLACED`.
7. **PCG communication / health / support fields.** Repo: health **found**
   (`pcg.healthStatus`, `:8060`); anxiety **found** (`pcg.anxietyLevel`,
   `:8062`); support adequacy **found**
   (`pcg.caregiverEvaluation.supportSystemAdequacy`, `:8115`); communication
   need **not found**. Status: mixed — `PRESENT BUT MISPLACED` for three,
   `MISSING FROM SNS` for caregiver communication need.
8. **Children / pets in home.** Repo: children not found; pets found only as
   a safety hazard (`safety.homeEnvironment`, `:9428`).
   Status: `MISSING FROM SNS` / `PRESENT BUT MISPLACED`.
9. **PCG education checklist.** Repo: two competing lists —
   `pcg.caregiverEvaluation.trainingNeeds` (`:8095-8097`) and
   `teachingNeeds.teachingTopics` (13 topics, `:9623-9637`).
   Status: `CONFLICTING`, with advance directives `MISSING FROM SNS`.
10. **Mid-arm circumference.** Repo: **found** — `vitals.mac`, rendered by
    `AnthropometricsAutoBmiCard` (`RNICA.jsx:2906`) and displayed read-only
    at `:2947`. Not exported (no CMS item). Earlier drafts that called this
    missing were searching `SECTION_CONFIGS` only.
    Status: `PRESENT BUT NOT HARVESTED`.
11. **BP position.** Repo: no match in `SECTION_CONFIGS.vitals` (`:8770-8805`)
    or `AnthropometricsAutoBmiCard`. Status: `MISSING FROM SNS`.
12. **ADL scale mismatch.** Repo: canonical SNS scale is **0-5, six levels**
    (`RNICA.jsx:9004-9009`), persisted at `musculoskeletal.adl.*`, presented
    under Functional Status via `dataSection`. No HOPE item consumes ADL
    values (the mapper emits none) and no LCD criterion consuming an ADL
    scale was located. **Therefore the repository proves no external
    consumer constraint, and the scale must not be "corrected" from a
    screenshot.** Status: `REQUIRES AUTHORITY REVIEW`.
13. **ADL calculated total.** Repo: not computed, not persisted.
    Status: `MISSING FROM SNS`.
14. **Complete-dependence count.** Repo: not computed, not persisted.
    Status: `MISSING FROM SNS`.
15. **Skin-status vocabulary.** Side-by-side, legacy (as described) vs SNS
    `skin.skinStatus` (`RNICA.jsx:9346`):

    | Legacy value (described) | Present in SNS? | SNS equivalent |
    |---|---|---|
    | Cool | **No** | closest is `cardiovascular.coolExtremities` (`:9102`), a separate boolean in a different section |
    | Warm | **No** | none |
    | Diaphoretic | **No** | none anywhere in the repository |
    | Fragile | Yes | `Fragile` |
    | Edematous | Yes | `Edematous` (also `cardiovascular.edema.*`) |
    | Bruising | Yes | `Bruising` |
    | Cyanotic | Yes | `Cyanotic` |
    | — | SNS-only | `Intact` |
    | — | SNS-only | `Dry` |
    | — | SNS-only | `Rash` |
    | — | SNS-only | `Jaundice` |
    | — | SNS-only | `Mottled` |

    Result: 4 of 7 described legacy values are present; **Cool, Warm and
    Diaphoretic are absent**; SNS adds 5 values the legacy list did not have.
    This is a partial overlap, not a wholesale mismatch. Because M1195 emits
    this array verbatim (`hopeReportMapper.js:626`), any change is an
    exporter-visible change. Status: `PRESENT BUT RESPONSE SET INCOMPLETE`.
16. **Pulse quality by site.** Repo: `cardiovascular.pulseSites` records
    which sites were palpated (`:9087`); `cardiovascular.pulseQuality` is a
    single shared radio (`:9088`). No per-site quality path exists.
    Status: `MISSING FROM SNS`.
17. **Weight loss >10% / 6 months.** Repo: `WeightLossAutoCalcCard` computes
    both absolute loss and percentage over a ~183-day window
    (`RNICA.jsx:2991,3005-3006`) but writes into the free-text
    `nutrition.weightLossPastSixMonths` (`:9220`).
    Status: `PRESENT BUT RESPONSE SET INCOMPLETE`.
18. **Cachexia response.** Repo: no `cachexia` path anywhere.
    Status: `MISSING FROM SNS`.
19. **Applicability / "None" state for functional scales.** Repo: none of
    `pps`, `kps`, `ecog`, `fast`, `nyha` has one. By contrast
    `endocrine.thyroid.assessment` has "Not assessed" (`:9248`),
    `endocrine.diabetes.dependency` has "Not applicable" (`:9253`),
    `psychosocial.familySocialSupport` has "Declined to answer" (`:9479`) and
    `admissionsOrder.haAssignment.notApplicable` is an explicit N/A
    (`:9672`) — so the pattern exists in the codebase and is simply absent
    here. Status: `MISSING FROM SNS`.
20. **Comorbidities.** Repo: 14 of 15 categories implemented with ICD-10
    auto-categorization (`RNICA.jsx:2496-2563`), principal-diagnosis
    exclusion including the documented cancer exception (`:2615-2617`),
    clinician confirmation required, and a fallback derivation for records
    predating structured capture (`hopeReportMapper.js:456-461,544-552`).
    The 15th, **I8005 "Other Medical Condition", has no checkbox** while the
    exporter reads `hopeComorbidities.other` (`:542`).
    Status: 14 `VERIFIED COMPLETE`, 1 `CONFLICTING`.
21. **Communications & Other Factors decomposition.** See §14 — complete,
    29 elements assigned.

---

## 16. Duplicate-field audit

### A. Facesheet duplicates
See **Table E** (§8). Nine editable RNICA fields duplicate Facesheet data:
`firstName`, `lastName`, `dob`, `gender`, `phone`, `alternatePhone`,
`address.*`, `emergencyContact.*`. Only `gender` arguably needs a distinct
RNICA response (for a CMS A0810 sex code) and that requires an authority
decision. The exporter already prefers the Facesheet record for A0500
(`hopeReportMapper.js:481,565`), so the editable copies are, for HOPE
purposes, dead weight that can silently disagree with the chart.

### B. Cross-screen duplicates
See **Table F** (§9) — 52 groups. Every concept the directive named is
covered there: anxiety (#12), agitation (#13), SOB (#7), nausea (#8),
vomiting (#9), diarrhea (#10), constipation (#11), ADLs (#15, #16),
mobility (#15, #16), oxygen (#4, #5, #6), comorbidities (#22-#25), ACP
responses (no duplicate found — the ACP card is the sole owner), caregiver
data (#41-#44), referrals (#45-#47), DME (#48), skin risk (#29-#31),
safety findings (#33-#37), narrative fields (#51).

**ACP is the one clean area:** F2000/F2100/F2200/F3000 each have exactly one
editable owner, with a documented back-compatibility fallback rather than a
second field.

### C. Calculated duplicates
See §9.1. BMI, SFV due date, screen completion count, readiness blocker
count, LCD result and decline-vs-last-assessment are each computed in exactly
one place. The violations are: `sfv.triggeredSymptoms` (manual duplicate of a
derived value), `skin.pressureInjuryRisk` (a band quoting a total that is
never computed), `nutrition.weightLossPastSixMonths` (a computed percentage
flattened into free text) and the caregiver willingness/capability scores
(manual scores duplicating qualitative fields).

---

## 17. Referral relocation (documented, not applied)

**Current state.** `rnicaThirteenScreenTaxonomy.js:33-40`:

```js
{
  key: "evidenceIntake",
  label: "Evidence & Intake",
  moduleKeys: ["demographics", "vitals", "referrals"],
},
```

and `:73-79`:

```js
{
  key: "caregiverSupport",
  label: "Caregiver & Support",
  moduleKeys: ["caregiverAssessment", "psychosocial", "spiritual", "bereavement", "personalCare", "teachingNeeds"],
},
```

**Required relocation.** Remove `"referrals"` from
`evidenceIntake.moduleKeys`; add `"referrals"` to
`caregiverSupport.moduleKeys`.

**Fields moved** (all 12, `RNICA.jsx:9692-9705`):
`referrals.socialWork.referred`, `.socialWork.reason`,
`referrals.spiritualCare.referred`, `.spiritualCare.reason`,
`referrals.volunteer.referred`, `.volunteer.type`,
`referrals.dietitian.referred`, `.dietitian.reason`,
`referrals.pharmacist.referred`, `.pharmacist.reason`,
`referrals.notes`, `referrals.reviewed`.

**Dependencies that must survive the relocation**

1. `FINALIZATION_CHECK_SECTION_MAP.referralsReviewed = "referrals"`
   (`RNICA.jsx:237`) maps the readiness check to a **route key**, not a
   screen key. `LEGACY_ROUTES` (`:191`) and `FORM_REGISTRY` (`:248`) both
   keep `"referrals"` as a route/form-section key, and neither changes.
   The map is consumed at `RNICA.jsx:11068`. Relocation is therefore safe
   for this dependency **provided the route key is not renamed**.
2. `evaluate_finalization_readiness()` reads
   `_get(form_data, "referrals", "reviewed")`
   (`rnica_finalization_service.py:137`). The persisted path is unchanged by
   a taxonomy-only move, so the Lock gate is unaffected.
   Covered by `backend/tests/test_rnica_finalization.py`.
3. `groupRoutesIntoScreens()` (`rnicaThirteenScreenTaxonomy.js:132-158`)
   places any unclaimed module into a trailing "Other" group rather than
   dropping it, so a partial edit degrades visibly rather than silently.

**Impact:** presentation only. No schema change, no migration, no exporter
change (the mapper does not read `referrals` at all).

---

## 18. Unverified-field audit

See **Table I** (§12) for the itemised list. Summarised by the directive's
categories:

- **Codes visible but not confirmed in repository mapping:** A1005 and A1010
  have no CMS code map (Table I #1); A1910 uses a non-official lookup (#2);
  `I0000` is emitted by the mapper but is in no registry list (#20).
- **Truncated or ambiguous labels:** `demographics.pcg` "Does this patient
  have a Primary Caregiver?" persisted key (#8); the comorbidity
  "Additional Note (optional)" key (#7); discipline-frequency row keys (#9).
- **Unconfirmed CMS item codes:** N0500/N0510/N0520 (#4), M1190 on
  `performanceStatus` (#5), J0050 on `diagnoses.terminalPrognosis` (#6).
- **Unconfirmed HOPE/SFV lifecycle applicability:** which items are required
  at Admission vs HUV vs Discharge is not encoded per field (#13).
- **Legacy fields of unclear continued use:** `diagnoses.clinicalNarrative`,
  `.clinicalNarrativeReviewed`, `.rnAddendum`, `.clinicianClarification`,
  `.recentHospitalizations`, `.recentErVisits`, `.utilizationNotes`,
  `.diseaseTrajectory` — all rendered by a card that is no longer in
  `SECTION_CONFIGS.diagnoses.cards`.
- **Possibly agency-specific fields:** the Caregiver Willingness & Capability
  block is marked `cms="CDPH Required"` (`RNICA.jsx:8078`), i.e. a California
  state requirement rather than a CMS HOPE one; `safety.disasterLevel*` is
  likewise an agency/state emergency-preparedness construct.
- **Ambiguous editable ownership:** all 52 rows of Table F.
- **Untraceable persistence:** `chhaPoc.completed` (#10),
  `PatientAllergies` (#11), `medications.*` (no writer),
  `diagnoses.hopeComorbidities.other` (no writer).
- **Unclear reporting status:** Z0400 declared but never emitted;
  `vitals.mac`, `sfv.findings`, `sfv.notes`, `sfv.reasonNotCompleted`,
  `gastrointestinal.reasonBowelRegimenNotInitiated` all captured but never
  harvested.

> **Unverified does not mean optional; implementation must stop until
> repository or controlling specification proves the rule.**

---

## 19. DME, assistive devices and equipment — three overlapping lists

The directive's rule "DME indication ≠ automatic DME order" is **already
satisfied structurally** by `DmeStatusCard`, which gives every item its own
status from `["", "Has", "Needs", "Ordered", "Delivered", "Declined", "N/A"]`
(`RNICA.jsx:2428`) rather than a single boolean. The problem is that three
separate lists describe overlapping equipment with different semantics:

| List | Path | Semantics | Screen (current) | Screen (target) |
|---|---|---|---|---|
| DME status tracker | `safety.dmeItems[]` (`:2426-2494`, `:9461`) | Order/delivery lifecycle | 8 | **10** |
| Equipment/Supply Needs | `personalCare.equipmentSupplyNeeds` (`:9599-9604`, 19 items) | Indication only | 7 | 10 (as indication feeding the tracker) |
| Assistive Devices | `musculoskeletal.assistiveDevices` (`:9322`, 7 items) | Current use / functional finding | 6 | 5 (functional finding) |

Overlapping items across the lists include hospital bed, wheelchair, walker,
cane, commode and Hoyer lift. There is no code linking them, so a patient can
be recorded as *using* a walker (musculoskeletal), *needing* a walker
(personal care) and having no walker DME entry simultaneously.
Status: `CONFLICTING` (Table F #48).

---
## 20. Acceptance gate — verification checklist

| Acceptance requirement | Where satisfied | Result |
|---|---|---|
| Every legacy section appears in Table J | §3 — 36 rows covering all 14 described legacy screens plus SNS-only modules | PASS |
| Every described HOPE item is mapped or UNVERIFIED | Table B (§5, 57 rows) + Table D (§7) + Table I (§12) | PASS |
| Every described SFV item is mapped or UNVERIFIED | Table C (§6, 20 rows) + Table D (§7, 11 rows) | PASS |
| Communications & Other Factors fully decomposed | §14 — 29 elements, each assigned to exactly one screen | PASS |
| Comorbidities mapped | §4.4 (15 rows) + Table B + §15 item 20 | PASS (14 complete, I8005 CONFLICTING) |
| All 13 screens have explicit field ownership | §4.1-§4.13 | PASS |
| Facesheet duplicates identified | Table E (§8) + §16 A | PASS (9 editable duplicates) |
| Referral relocation documented | §17 with exact taxonomy edit and the three surviving dependencies | PASS |
| ADL ownership documented | §4.5, §15 item 12 — presentation on Screen 5, persistence in `musculoskeletal`, scale 0-5 confirmed, no proven external consumer | PASS |
| SFV trigger fields identified | Table C, Table D, §4.3.3 | PASS |
| HOPE-harvest fields identified | Table B with exporter line citations | PASS |
| Editable vs read-only ownership explicit | "Edit" and "RO" columns on every Table A row | PASS |
| Missing vs misplaced distinguished | `MISSING FROM SNS` vs `PRESENT BUT MISPLACED` used as distinct statuses throughout | PASS |
| No unverified item silently marked implemented | Table I (§12) + `NOT VERIFIED` / `REQUIRES AUTHORITY REVIEW` statuses | PASS |
| Existing-data compatibility addressed | "Compat" column on every Table A row; §20.1 below | PASS |
| Existing tests and exporters referenced | §0 evidence block; per-screen evidence blocks; §20.2 below | PASS |

### 20.1 Existing-data compatibility summary

- **All `SECTION_CONFIGS` paths persist into the RNICA assessment
  `form_data` JSONB document.** Adding a field is additive; reading an older
  record simply yields `undefined`, which every renderer tolerates. No
  migration is implied by any finding in this document.
- **Three documented back-compatibility fallbacks already exist and must not
  be broken:**
  1. `askedStatus(coded, legacyIndicator)` (`hopeReportMapper.js:303-327`) —
     F2000/F2100/F2200/F3000 fall back to the pre-coded booleans and
     preference values.
  2. `hasStructuredHopeComorbidities()` (`:456-461`) — records without
     `hopeComorbidities` fall back to ICD-10 regex derivation
     (`:544-552`).
  3. `officialCodeLookup()` with `LEGACY_*_TO_CODE` maps (`:58-122`) —
     A0215/A1805/A1905 records that stored legacy *labels* are remapped to
     official codes.
- **Relocating a module between screens changes no persisted path**, because
  the taxonomy maps *route keys*, not storage keys
  (`rnicaThirteenScreenTaxonomy.js:132-158`).
- **The `musculoskeletal.adl.*` / `dataSection` split is itself a
  compatibility device** — presentation moved to Functional Status without
  rewriting existing records.
- **Risk to flag:** any change to `demographics.race`, `.ethnicity` or
  `skin.skinStatus` response sets is exporter-visible, because those three
  are emitted verbatim by `arrayText()` with no code lookup
  (`hopeReportMapper.js:571-572,626`). Existing records holding retired
  labels would export the retired strings.

### 20.2 Tests and exporters referenced

```
Exporter: sns-emr-frontend/src/intake/hopeReportMapper.js         (mapRnIcaToHopeReport, getSfvStatus, getHopeAdmissionStatus)
Exporter: sns-emr-frontend/src/intake/HopeReport.jsx:13
Exporter: sns-emr-frontend/src/intake/ComplianceHopeBoard.jsx:9
Test:     sns-emr-frontend/src/intake/hopeReportMapper.test.js
Test:     sns-emr-frontend/src/intake/clinicalNarrativeBuilder.test.js
Test:     sns-emr-frontend/src/components/rn-ica/applyStructuredFindings.test.js
Test:     backend/tests/test_rnica_finalization.py            (evaluate_finalization_readiness)
Test:     backend/tests/test_rnica_hope_workflow.py           (HOPE submission workflow)
Test:     backend/tests/test_rnica_amendments.py              (amendment/correction history)
Test:     backend/tests/test_rnica_poc_adapter.py             (POC completeness)
Test:     backend/tests/test_rnica_poc_history.py
Test:     backend/tests/test_rnica_order_suggestions.py       (explicit acceptance of AI order suggestions)
Test:     backend/tests/test_rnica_runtime_validation.py
Test:     backend/tests/test_rnica_functional_assessment_governance.py
Script:   backend/scripts/backfill_loren_hope_comorbidities.py (existing comorbidity backfill precedent)
Migration:backend/alembic/versions/9d3f6b7c8a10_add_rnica_hope_workflow_columns.py
Migration:backend/alembic/versions/aa9e08e3848e_extend_rnica_hope_submission.py
```

No test was executed for this checkpoint: no code was changed.

---

## 21. Document counts

| Metric | Count |
|---|---|
| Legacy screens/sections audited (Table J rows) | 36 (covering all 14 described legacy screens) |
| Table A field-level rows | 603 |
| Total table rows in this document | 964 |
| HOPE-only item rows (Table B) | 57 |
| SFV-only rows (Table C) | 20 |
| HOPE-and-SFV item rows (Table D) | 11 (19 discrete codes once A-H suffixes are expanded) |
| Facesheet-harvest rows (Table E) | 16 (9 with an editable RNICA duplicate) |
| Duplicate/conflicting editable-field groups (Table F) | 52 |
| Calculated-duplicate rows (§9.1) | 14 |
| Missing/unwired field rows (Table G) | 51 |
| Incomplete response sets (Table H) | 26 |
| Unverified / authority-review items (Table I) | 20 |
| Communications & Other Factors elements decomposed (§14) | 29 |

---

## 22. Change control

This checkpoint changed **one file**: this document.

- No UI change.
- No field added, removed, or renamed.
- No response set changed.
- No validation changed.
- No exporter changed.
- No schema change; no migration.
- No clinical logic changed.

Every correction identified here is recorded as a finding, not applied.
