# RNICA Narrative Architecture Map

**Status**: Living document — authoritative design reference for the RNICA/UPDATE/RECERT/PRN/DEATH
narrative-generation engine.

**Source of truth**: `backend/app/services/rnica_narrative_v2_service.py`

**Rule going forward**: every major discovery, workflow finding, compliance interpretation, or
narrative rule change made to this engine must be reflected here. Chat/session history is not an
acceptable substitute for this document. If you change `_build_system_prompt`,
`_ASSESSMENT_TYPE_VOICE`, or `_ASSESSMENT_TYPE_FLOW`, update the relevant section below in the
same change. See Section 15 (Change Control Requirement) for the full process.

---

## Section 1 — RNICA Purpose

RNICA (RN Initial Comprehensive Assessment) is a **first-encounter nursing assessment document**,
generated immediately after a hospice RN completes an admission visit. It is produced by
`generate_rnica_narrative_v2()` from structured form data, harvested clinical evidence, and the
medication list already on file for the patient.

RNICA is explicitly **NOT**:
- A patient summary
- A chart abstract
- A clinical synopsis
- A "Documentation Insights" report
- An eligibility report or medical-necessity argument

RNICA explicitly **IS**:
- An Initial Comprehensive RN Assessment — the same kind of document a hospice RN would
  hand-write immediately after an admission visit.

**Why the distinction matters**: a patient summary reports facts *about* the patient. An RN
assessment documents what the *nurse* did — what she observed, assessed, reviewed, taught,
instructed, and planned. These read differently, are held to different documentation/compliance
standards, and serve different downstream purposes (QA review, surveyor review, IDG planning,
billing/certification support). Conflating the two produces a document that looks organized but
would not be signed by an RN as her own clinical work.

---

## Section 2 — Regulatory Foundation

RNICA's required content is not arbitrary — it exists to satisfy specific hospice regulatory
obligations. This section maps each major requirement to its source so future changes can be
evaluated against the actual standard, not just "what the note used to look like."

| Requirement | Regulatory anchor | What RNICA must do about it |
|---|---|---|
| Comprehensive assessment of the patient's condition | CMS Condition of Participation, hospice comprehensive assessment requirement (42 CFR §418.54); California hospice licensing (Health & Safety Code / Title 22 hospice regulations) | Cover physical, psychosocial, and functional status across all clinically relevant body systems (Section 6 domain map) |
| Assessment of symptoms and current medications | Same CoP; drives Section 6 pain/respiratory/GI-GU domains | Medication list reconciled against what is actually in the home; symptom burden documented per domain |
| Caregiver willingness and capability assessment | California hospice regulation requiring evaluation of the caregiver's willingness and capability to provide care | Caregiver Framework (Section 7) — presence is not sufficient; willingness/capability/competency must be documented |
| Referral needs identified | Comprehensive assessment requirement to identify need for other disciplines (social work, chaplain, aide) | Plan of care must name specific referrals tied to specific findings (Section 6 POC row), not a generic "referrals as needed" |
| Individualized plan of care based on the comprehensive assessment | CMS CoP plan-of-care requirement (42 CFR §418.56) | Section 6 POC expectations — plan must be traceable to findings documented earlier in the same note, not boilerplate |
| Terminal prognosis / disease-specific functional decline evidence | LCD (Local Coverage Determination) support expectations for hospice eligibility documentation | Performance Status Framework (Section 10) — every scored scale must appear with its clinical meaning, especially the disease-specific scale matching the terminal diagnosis |

**Important governance note**: the exact clause-level citations above (CFR subsections, specific
CDPH regulation dates) should be verified against the compliance team's authoritative regulatory
source before being relied upon in a survey response or legal context. This table exists to
anchor *why* RNICA requires what it requires, not to serve as the citation of record — if
compliance identifies a more precise or updated citation, update this table rather than treating
it as fixed.

**Explicit non-goals**: RNICA must never use this regulatory grounding to construct an eligibility
argument, meet-criteria statement, or terminal-prognosis conclusion *within the narrative itself*
(see Section 11 anti-patterns). The regulatory link explains what must be *assessed and
documented*, not what must be *argued*.

---

## Section 3 — RNICA Goals

The narrative must support all of the following objectives on every generation:

- Establish the patient's baseline (functional, symptom, cognitive, psychosocial) at the time of
  admission
- Complete a comprehensive, multi-system assessment (not a single-problem note)
- Evaluate and document current symptom burden
- Assess caregiver capability — not just caregiver presence (see Section 7)
- Review the medication list against what is actually in the home
- Initiate teaching appropriate to a first encounter (not reinforcement language)
- Establish an initial, individualized plan of care
- Evaluate safety concerns specific to this patient's deficits
- Document clinical judgment, not just findings (see Section 5)
- Support individualized interdisciplinary care planning (nursing, aide, social work, chaplain)

These map to California hospice comprehensive-assessment expectations, which require the initial
assessment to establish baseline status across physical, psychosocial, and caregiver domains and
to directly inform an individualized plan of care — not a generic checklist confirmation.

---

## Section 4 — Visit Context Framework

The engine reads `record.assessment_type` (DB column, `RNICA`/`UPDATE`/`RECERT` are wired into
real business logic in `backend/app/api/visits.py`; `PRN`/`DEATH` are narrative-engine-only
concepts today, not yet selectable in the UI/API — see Section 14) and
`form_data.visitMeta.reasonForVisit`, and builds a fully different system prompt per type via
`_build_system_prompt()`, `_ASSESSMENT_TYPE_LABELS`, `_ASSESSMENT_TYPE_VOICE`, and
`_ASSESSMENT_TYPE_FLOW`.

| Type | Purpose | Style | Included | Excluded |
|---|---|---|---|---|
| **RNICA** | First-encounter admission assessment | Admission story: why hospice now, first-time teaching, first-time caregiver introduction to hospice | Decision maker, living situation, code status, full baseline across all systems, initial POC | Comparative/decline-since-last-visit language (there is no "last visit") |
| **UPDATE** | Routine/follow-up skilled nursing visit | Check-in against a known baseline; reinforcement, not first-time | Today's findings vs. baseline, reinforcement teaching, ongoing plan | Admission framing, decision-maker/living-situation re-introduction, first-time teaching language |
| **RECERT** | Recertification assessment | Continued-care, decline-since-last-certification framing | Trend/decline language ("continues to decline," "remains"), current eligibility-relevant evidence, continued goals | Admission framing, first-time teaching language |
| **PRN** | Unscheduled, problem-focused visit | Tightly scoped single-problem note | Why called, focused exam, specific intervention + response, narrow follow-up instructions | Full comprehensive re-assessment, full POC restatement, unrelated system findings |
| **DEATH** | Death visit / pronouncement note | Entirely different document class | Pronouncement findings, family/physician notification, funeral home coordination, medication/DME disposition, bereavement initiation | Functional/performance-scale content, POC, teaching (except bereavement-related) |

**Critical rule**: the visit type must be revealed only through content, depth, and structure —
**never** through the narrative literally naming itself (e.g. "visit for initial comprehensive
assessment"). See Section 11 for the banned self-naming patterns and why this rule exists.

---

## Section 5 — RNICA Workflow Map (Clinical Reasoning Chain)

Canonical chain every clinically significant domain should attempt to follow:

```
Assessment Finding
      ↓
Nursing Judgment      (what the finding means / why it matters clinically — not just restated)
      ↓
Intervention          (what the RN did, or delegated, in response)
      ↓
Response              (what happened as a result — observable, not invented)
      ↓
Teaching               (what was taught to patient/caregiver, and whether it landed)
      ↓
Plan                   (what continues/changes going forward)
```

**Why this chain matters**: a list of findings, interventions, and teaching sitting side by side
reads as a report. The chain is what makes a note read as an RN's actual clinical reasoning during
a visit — it proves she didn't just observe things, she interpreted them and acted, and knows
whether the action worked.

**Known reality**: not every domain will have an acute intervention on every visit (e.g., a
GI/GU system that is currently stable may only warrant medication review + teaching, with no
response step because nothing acute happened). The chain is a target to reach for whenever the
domain is clinically active, not a rigid template to force onto stable systems — see Section 14
for where this currently falls short.

---

## Section 6 — Domain Map

Expected behavior per domain when the domain is clinically active this visit:

| Domain | Expected Finding | Expected Judgment | Expected Intervention | Expected Response | Expected Teaching | Expected Plan |
|---|---|---|---|---|---|---|
| **Respiratory** | Rate, effort, use of accessory muscles, dyspnea at rest/exertion, oxygen use/refusal | Why current measures are/aren't sufficient | Positioning, pacing, oxygen offered, comfort medication reviewed | Observed change (eased/unchanged) after intervention | Upright positioning, pacing, when to use PRN meds | Symptom monitoring, call-back criteria |
| **Cardiac** | Fatigue with exertion, edema, medication list | Disease trajectory context (e.g. EF, NYHA class meaning) | Medication reconciliation, monitoring parameters reviewed | Often none acute — stable chronic monitoring is valid | Signs to report (edema, chest discomfort, reduced output) | Ongoing monitoring in POC |
| **Pain** | Location, severity, current regimen effectiveness | Is current regimen adequate; interaction with other symptoms (e.g. constipation) | Repositioning, offloading, medication review | Guarding/comfort observed before vs. after | Pain-cue recognition, breakthrough dosing, escalation criteria | Ongoing pain monitoring in POC |
| **GI/GU** | Bowel pattern, constipation risk, urinary symptoms | Opioid-constipation link, infection risk | Bowel regimen review; PRN intervention if acute | Only when an acute intervention occurred this visit | Bowel tracking, when to escalate, hydration | Ongoing monitoring in POC |
| **Skin** | Wound location/stage, risk factors | Why area is vulnerable (immobility, moisture, pressure) | Offloading, barrier product, inspection | Skin status immediately after intervention (no new redness, tolerated turning) | Turning schedule, moisture management, reporting criteria | Ongoing skin monitoring in POC |
| **Neurological** | Mental status, orientation, speech, deficits from prior events (e.g. CVA) | Baseline cognitive/communication capacity | N/A unless acute change | N/A unless acute change | Communication strategies for caregivers if relevant | Reassessment at future visits |
| **Musculoskeletal** | Mobility, ROM, stiffness, transfer ability | Fall/injury risk from deficits | RN assesses; ROM/massage/repositioning-schedule is delegated to LVN/CHHA (see Section 9) | N/A for delegated tasks; in-the-moment comfort actions may have a response | Safe handling instructions to caregiver | LVN/CHHA delegation stated explicitly in POC |
| **Safety** | Fall risk, environment, transfer risk despite being bedbound | Why risk exists even without ambulation | Environmental instruction (bed position, item placement, two-person assist criteria) | Often none acute — mostly forward-looking instruction | Safe handling, when to get help | Ongoing precautions in POC |
| **Psychosocial** | Emotional state, expressed fears/concerns, family dynamics | Coping status, support adequacy | Emotional support provided, referral initiated | Patient's affect/engagement during visit | Hospice team roles (SW, chaplain) introduced | SW/chaplain referral in POC |
| **Caregiver** | Who is present, their role | Willingness, capability, competency (see Section 7) | Teaching delivered, teach-back attempted | Demonstrated understanding or need for reinforcement, task-specific | Task-specific instruction | Named in POC with what needs reinforcement |
| **Plan of Care** | All of the above, synthesized | Which needs are highest priority | Services ordered (nursing frequency, aide, SW, chaplain) | N/A | N/A | Individualized — tied back to specific findings, not generic |

---

## Section 7 — Caregiver Framework

**Core principle**: Caregiver Presence ≠ Caregiver Capability.

A narrative that only states "caregiver present" or "caregiver verbalized understanding" does not
meet the standard. The narrative must be able to express, per relevant task:

- **Willingness** — is the caregiver willing to provide the needed care?
- **Capability** — are they physically/cognitively able to perform it?
- **Competency** — did they demonstrate correct technique/understanding today (not just "asked
  questions")?
- **Need for reinforcement** — named specifically (e.g. "will need reinforcement on bowel regimen
  timing"), not a blanket statement covering everything taught.
- **Ability to safely execute the plan** — an explicit closing judgment, not implied.
- **Participation level** — did they actively take part during the visit, or only observe?

**Why mandatory**: California hospice regulation requires assessment of the caregiver's
willingness and capability to provide care, and plan-of-care documentation regarding caregiver
abilities and responsibilities. A note that never assesses this — regardless of how well it
documents the patient — does not satisfy the comprehensive-assessment requirement.

**Example of the bar** (from a verified live generation): *"Caregivers demonstrated safe
repositioning technique with cueing"* (skin domain) vs. *"were able to repeat back the sequence of
routine and PRN bowel medications"* (GI domain) vs. *"will benefit from another review after they
have used the [respiratory comfort] kit in real time"* — three different, task-specific competency
judgments in one note, not one generic sentence repeated.

---

## Section 8 — RN Actor Rules

**Rule**: the RN must remain the visible grammatical actor for every action she personally
performed. Required first-person forms include: "I observed," "I assessed," "I reviewed," "I
discussed," "I instructed," "I educated," "I established."

**Why passive chart-summary language was rejected**: passive voice erases the nurse as the actor,
making the note read as a list of facts that happened to be true rather than a record of what the
nurse did. This is the single clearest signal that separates an AI-generated summary from RN
documentation.

**Eliminated patterns** (previously present in generated output, now explicitly banned in the
system prompt):
- "Teaching was started"
- "Code status was reviewed"
- "Plan established today is for..."
- "Medications were reviewed with staff"
- "Safety teaching was reinforced"

**Exception**: passive/third-person phrasing remains correct for things the RN did not personally
do — what the patient reports, what family/caregivers report, or an objective fact that simply
exists (a lab value, a documented wound stage).

---

## Section 9 — Scope of Practice Rules

The narrative must correctly attribute who performs a task, not just that it happened.

| Role | Typical tasks in this narrative's scope |
|---|---|
| **RN** | Comprehensive assessment, clinical judgment, medication review/reconciliation, teaching, delegation, plan-of-care establishment, in-the-moment comfort actions performed *during the visit itself* (e.g. offloading a heel while assessing it, repositioning to assess breathing) |
| **LVN** | Routine passive range-of-motion stretching, massage, scheduled repositioning, other delegated hands-on tasks per POC |
| **CHHA** | Personal care, hygiene, scheduled repositioning, other delegated hands-on tasks per POC |
| **Delegated / Supervised** | Any recurring hands-on task established as an ongoing schedule (e.g. "every two hours") is LVN/CHHA-executed under the RN's instruction, not an RN task the note should claim was personally performed |

**Prohibited narrative assumption** (discovered defect, now fixed): the narrative previously wrote
that the RN personally stretched, massaged, or performed routine range-of-motion exercises as
part of her own visit. This is incorrect — these are LVN/CHHA-level recurring tasks. The
corrected pattern documents the RN's assessment of the need, followed by delegation stated in the
plan of care: *"I instructed the LVN/CHHA to provide passive range-of-motion, massage, and
repositioning every two hours as part of the plan of care."*

**Distinction to preserve**: a one-time, in-the-moment comfort action the RN performs herself while
physically present and assessing (e.g., offloading a heel during a skin check, repositioning to
observe breathing) is still correctly attributed to the RN — this is not the same as claiming
ownership of a recurring delegated care task.

---

## Section 10 — Performance Status Framework

Performance/disease-specific scales in use: **PPS, KPS, NYHA, FAST, ECOG**.

Required behavior for every scale that is scored and present in the evidence:
1. **Score** — the exact value/stage/class must appear, never invented.
2. **Meaning** — the scale's published clinical meaning must appear in the same sentence, never a
   bare score with no explanation (e.g. never "PPS 40%" alone).
3. **Clinical interpretation** — the meaning must be woven into a functional-status sentence
   describing what the patient can/cannot do, not presented as a labeled data field.
4. **Narrative integration** — scales must read as part of the ongoing story of the visit, not as
   a separate "Performance Status" block.
5. **Importance** — disease-specific scales (NYHA for heart failure, ECOG for cancer, FAST for
   dementia) must never be silently dropped in favor of only the general PPS/KPS scales; a
   reviewer specifically looks for the disease-specific scale matching the terminal diagnosis.

**Exception**: the "every scale must appear" mandate does not apply to DEATH visits (functional
status is not relevant to a pronouncement note) or to PRN visits where the scale is unrelated to
the reason for the visit. Both the prompt-level mandate and the Python-side safety-net fallback
(`missing_scale_sentences` logic) are gated to skip for these cases, so the model is never forced
to inject an irrelevant PPS/KPS sentence into a document where it would be clinically wrong.

Full scale interpretation logic (score → meaning → functional interpretation → why-it-matters →
narrative phrasing) lives in `backend/app/services/scale_interpretations.py` and
`sns-emr-frontend/src/intake/scaleInterpretations.js` — this work is considered complete and is
out of scope for further refactoring per prior direction.

---

## Section 11 — Narrative Anti-Patterns

All of the following were identified as defects in earlier iterations and are now explicitly
rejected by the system prompt. Each is documented with why it was rejected — this list is not
allowed to shrink without a corresponding architectural justification recorded here.

| Anti-pattern | Why rejected |
|---|---|
| Section headers: "HOSPICE ADMISSION OVERVIEW," "SYMPTOM BURDEN," "HOSPICE ELIGIBILITY SUMMARY," "LCD SUPPORT SECTION" | Immediately reveals AI/report authorship; real RN notes are continuous narrative, not labeled report sections |
| "Clinical picture supports...", "hospice appropriateness...", "meets criteria", "documentation supports" | The narrative must never argue eligibility directly — that is a clinical/IDG determination, not something a chart note states about itself |
| Patient-summary style ("the patient's clinical picture is one of decline") | Summarizes/interprets rather than documents; an RN observes and records, she doesn't editorialize about her own findings |
| Chart-abstraction style ("data indicates," "field," "tracked as," "recorded as") | Reads like a system describing its own database, not a clinician describing a patient |
| AI-report voice generally ("these changes," "collectively," "overall, the patient," "represents," "reflects") | The clearest tells of AI authorship; banned outright regardless of context |
| Passive RN-action voice ("teaching was started," "plan established") | See Section 7 — erases the RN as the actor |
| Self-naming the document type ("visit for an initial comprehensive assessment," "routine follow-up visit," "recertification visit") | The visit type must be inferable from content and depth alone; a real nurse never states the name of the document she's filling out inside the document itself |
| RN claiming delegated LVN/CHHA tasks as her own (stretching, massage, routine ROM) | See Section 8 — factually incorrect scope-of-practice attribution |
| Caregiver assessment reduced to "present" / "verbalized understanding" | See Section 6 — does not meet the willingness/capability/competency standard |

---

## Section 12 — Authenticity Test (Permanent Validation Standard)

Before accepting any RNICA output as production-ready, apply this test:

1. Hide the document type label, all metadata, and any headers.
2. Read only the continuous narrative text.
3. Ask: **"Would an experienced hospice RN sign this note as her own Initial Comprehensive
   Assessment, without needing to rewrite most of it?"**

If the answer is no, the narrative fails regardless of how many checklist elements are
technically present. Checklist completion (Section 2/5 elements present) is necessary but not
sufficient — the standard is whether the clinical reasoning chain (Section 4) and caregiver
judgment (Section 6) are actually demonstrated, not just mentioned.

Secondary check: a hospice RN, Clinical Manager, and QA Reviewer, each reading blind, should all
independently be able to identify: initial comprehensive assessment, baseline findings, RN
judgment, RN interventions, caregiver assessment, teaching, and plan-of-care development — from
the narrative alone.

---

## Section 13 — Resolved Findings

This section records discoveries that have already been investigated and fixed, so they are not
re-discovered or re-litigated in a future session. When an item moves out of Section 14 (Open
Gaps) because it has been resolved, add its entry here rather than deleting it.

| Finding | Root cause | Resolution | Verified |
|---|---|---|---|
| All visit types produced near-identical, admission-style narratives | `generate_rnica_narrative_v2()` never read `record.assessment_type` or `visitMeta.reasonForVisit`; `SYSTEM_PROMPT` hardcoded admission-style opening for every type | Converted to `_build_system_prompt(assessment_type_code, reason_for_visit)`, dynamic per type via `_ASSESSMENT_TYPE_LABELS`/`_ASSESSMENT_TYPE_VOICE`/`_ASSESSMENT_TYPE_FLOW` | Yes — RNICA/UPDATE/RECERT/PRN/DEATH confirmed dramatically different in length, structure, and focus for the same patient/evidence |
| Narratives self-announced their own visit type ("visit to complete initial comprehensive assessment") | No rule against literal self-naming | Added explicit "NEVER NAME THE DOCUMENT TYPE" rule; visit type must be inferable from content/depth only | Yes — grep across all 5 regenerated types confirmed zero self-naming phrases remained |
| Narrative read as an AI-generated summary rather than RN documentation (passive voice) | No rule governing grammatical actor; the RN's own actions were frequently phrased passively ("teaching was started," "plan established") | Added "RN MUST BE THE VISIBLE ACTOR" rule requiring first-person subject for RN-performed actions | Yes — first-person sentence count rose from a minority to 32/64 (50%) in a sample RNICA generation, with only 3 minor passive residues remaining |
| Caregiver assessment reduced to "present"/"verbalized understanding" | `_ASSESSMENT_TYPE_FLOW["RNICA"]` never required an explicit capability judgment | Added requirement for caregiver capability judgment (willingness/ability/competency/reinforcement-needs) to the RNICA flow guidance | Yes — regenerated narrative includes task-specific competency judgments (e.g. demonstrated safe repositioning technique vs. needing reinforcement on bowel regimen timing) |
| RNICA lacked any direct RN-performed hands-on action (teaching/instruction only) | RNICA flow guidance never required at least one hands-on RN action distinct from delegated instruction | Added requirement for at least one or two RN-performed actions (e.g. repositioning, offloading) | Yes — regenerated narrative includes "I repositioned him in bed... offloaded pressure from the right heel" |
| RN narrative claimed to personally perform stretching/massage/routine ROM | No scope-of-practice distinction between RN and LVN/CHHA tasks | Added explicit scope-of-practice rule: routine stretching/massage/repositioning-schedule is LVN/CHHA-delegated, stated in the plan of care, not an RN-performed action | Yes — regenerated narrative reads "I instructed the LVN/CHHA to provide passive range-of-motion, massage, and repositioning every two hours as part of the plan of care" |
| Stale saved narrative in a real patient record still showed old report-style headers, even though the live engine had already been rewritten | UI/DB held a previously-generated narrative that was never regenerated after the engine was fixed | Regenerated fresh output via the current engine and persisted it into the patient's `RnicaAssessment.form_data.diagnoses.clinicalNarrative` | Yes — confirms this was a stale-data issue, not an engine defect, at the time it was found |
| Kessler's regression-test FAST validation failed — `performanceStatus.fast` was blank | Traced full pipeline (source document → extraction → database → API → Performance Status → narrative → Evidence Center). Her already-uploaded source PDF (`kessler_hnp_chart_consents.pdf`) literally contains the value in its raw OCR'd text — `"KPS 30 7-E FAST PPS 30 NYHA"` — but it was never transcribed into the structured `RnicaAssessment.form_data.performanceStatus` fields. Confirmed via direct full-text search of her `PatientEvidenceRecord` rows and full JSON walk of her assessment's `form_data`. This is a data-entry/transcription gap, not a narrative-engine defect — no automated scale-extraction pipeline exists in this system today; PPS/KPS/NYHA/FAST/ECOG are RN-entered structured fields (confirmed by inspecting how Loren's reference values were populated: a manual transcription script, `backend/scripts/populate_loren_shields.py`, not an AI extraction step) | `backend/scripts/populate_kessler_performance_status_from_pdf.py` transcribes the literal source-document value into `kps=30`, `pps=30%`, `fast=7e` (each with a justification quoting the source table). NYHA intentionally left blank — not present in the source row for this dementia patient | Yes — regenerated Kessler narrative now includes "She is at FAST 7e, with advanced dementia no longer able to smile..." and `scale_clinical_evidence` returns a fully-interpreted FAST 7e entry alongside PPS/KPS; Evidence Center re-confirmed functional after the fix |
| Duplicate narrative writers — the "Build Draft from Documented Findings" button produced pre-redesign report-style headers (HOSPICE CLINICAL PICTURE / REASON FOR HOSPICE ADMISSION / EVIDENCE OF DECLINE / DISEASE-SPECIFIC SUPPORT), which are explicitly banned anti-patterns (Section 11), while narratives generated through Documentation Insights did not | `diagnoses.clinicalNarrative` is a single storage field, but had two independent writers: the frontend deterministic template (`sns-emr-frontend/src/intake/clinicalNarrativeBuilder.js` → `buildClinicalNarrative()`), wired to "Build Draft from Documented Findings", and the backend RNICA V2 engine (`generate_rnica_narrative_v2()`), reachable only via Documentation Insights' "Insert into Clinical Narrative". Whichever was clicked most recently determined what the RN saw, with no indicator of which engine produced it | Repointed "Build Draft from Documented Findings" (`ClinicalNarrativeCard.applyDraft()` in `RNICA.jsx`) to call `previewRnicaNarrativeV2()` — the same `POST /rnica/{assessment_id}/narrative-v2/preview` endpoint Documentation Insights already uses — instead of the local template. `buildClinicalNarrative()` is retained only as an offline fallback for an assessment with no `assessmentId` yet (never saved) or if the API call fails, so the button never goes fully dead; it is no longer a second active narrative-composition path. Corrected the stale docstring on `preview_rnica_narrative_v2` (`backend/app/api/visits.py`), which still described the old fixed 10-section report format | **Yes — VERIFIED_WORKING_END_TO_END, live browser, all three regression patients (2026-09-08).** Backend-only verification (direct `generate_rnica_narrative_v2()` calls) was insufficient and produced a false PASS: a live screenshot of Norma's browser session showed the button still displaying a previously-saved pre-fix legacy narrative, because an earlier in-session regeneration was never explicitly saved. Root cause traced live in-browser with instrumented network capture (`window.fetch`/`XMLHttpRequest` hooked before interaction): confirmed correct worktree/commit (`feature/production-hnp-clinical-runtime @ 65b2187`, matching the on-page build banner) and correct running processes: (1) clicked "Build Draft from Documented Findings" → "Replace with New Draft" live for Norma; network capture proved `POST /visits/rnica/cb060604.../narrative-v2/preview` → `200 OK` with the V2 JSON response body (`ai_configured: true`, `section1`/`section9` fields); (2) resulting textarea (8,678 chars) contained zero legacy headers, included PPS 20%/KPS 20/ECOG 4 with clinical interpretation, and the on-screen "Narrative Quality Gate: FAIL" banner cleared to "must be reviewed" (passing); (3) captured the autosave `PUT /visits/rnica/cb060604...` → `200 OK`; (4) hard-reloaded the page and re-navigated Nursing Assessment → RNICA record → Finalization — the identical 8,678-char V2 narrative persisted, proving it survives reload and is not just in-memory state. Repeated the same live click→network-capture→persist check for Kessler (assessment `5d39cc37...`) — confirmed `POST .../narrative-v2/preview` → `200 OK`, FAST 7e/PPS 30%/KPS 30 present with interpretation, zero legacy headers. Loren was confirmed live (PPS 40%/KPS 40/NYHA IV, zero legacy headers) earlier the same day using the identical browser click-through method. |
| **LEGACY FRONTEND NARRATIVE WRITER REMOVED** — a "reachable only when unsaved/on API failure" fallback was judged unacceptable: any code path capable of producing the banned report-style narrative is a live risk regardless of how rarely it fires | The item above only demoted `buildClinicalNarrative()` to a fallback; the function, its report-style template, and its 31 KB file still existed and were still importable/callable | Deleted `sns-emr-frontend/src/intake/clinicalNarrativeBuilder.js` and its test file entirely — no rename, no "historical reference" retention. `ClinicalNarrativeCard.applyDraft()` (`RNICA.jsx`) no longer has an `!assessmentId` branch that generates any narrative locally; V2 preview (`previewRnicaNarrativeV2()`) is the only call in the function. The shared, engine-agnostic infrastructure the old file also contained — Disease Trajectory constants/helpers, `computeNarrativeContextFingerprint()` (staleness detection), `evaluateNarrativeQualityGate()` (field-dump/leakage linter) — was extracted, unchanged, into a new module `sns-emr-frontend/src/intake/narrativeSupport.js` (with `narrativeSupport.test.js` covering it) so removing the banned writer did not regress staleness detection or the quality gate that originally caught the Norma field-dump. New unsaved-assessment UX: `handleBuildDraft()` shows a save-first message with no technical jargon ("Save the assessment before generating the clinical narrative so the draft can use the complete current documentation. All entered fields are preserved.") and a "Save Assessment" button wired to a new `saveNow()` action added to `useAssessmentAutosave()` (an explicit, awaitable version of the existing 30s background autosave, reusing the identical create/update logic) — no assessment field is read, cleared, or overwritten by this path. V2-failure behavior is unchanged (already correct): shows the error, offers Retry, never falls back to any local narrative, and never overwrites existing narrative text or RN edits. Repo-wide search confirms zero remaining references to `clinicalNarrativeBuilder`/`buildClinicalNarrative` outside this table, `narrativeSupport.js`'s explanatory doc-comment, and a historical comment in `rnica_narrative_v2_service.py` | Yes — `narrativeSupport.test.js` (14 tests, ported/adapted from the deleted file's non-legacy-writer test cases) and a new `ClinicalNarrativeCard.test.jsx` (6 tests: saved-assessment path calls only `previewRnicaNarrativeV2`; unsaved-assessment path shows the jargon-free save prompt and calls nothing; Save Assessment invokes `onSaveNow()`; V2 failure shows Retry with no fallback text ever written; existing-narrative replacement requires explicit confirmation; a successful draft writes narrative text + fingerprint + reset review status together) all pass. Full frontend suite: 276/276 passing across 19 files. `tsc -b` reports zero errors introduced by this change (pre-existing, unrelated MUI type errors in `FacilityCollectionsReportPage.tsx` confirmed present on the unmodified baseline via `git stash`). Re-ran the full live click→network-trace→save→reload verification in-browser for Loren/Norma/Kessler after this change: all three continued to show V2-only narratives with zero legacy headers and correct scale values (PPS/KPS/NYHA for Loren, PPS/KPS/ECOG for Norma, PPS/KPS/FAST for Kessler) |

---

## Section 14 — Open Gaps (Roadmap)

As of the most recent architectural audit against a live-generated RNICA narrative for a real
patient record:

1. **GI/GU chain incomplete** — when the domain is clinically stable (no acute event this visit),
   the narrative currently produces Finding → Teaching → Plan only; no intervention or response
   step, because nothing acute happened. This is clinically plausible but has not yet been
   explicitly validated against a patient with an *acute* GI/GU issue at admission, where the
   full chain should be achievable.
2. **Safety chain incomplete** — similarly, safety documentation is currently teaching/instruction
   only (forward-looking), with no RN-performed action or observed response within the visit
   itself. Real RN notes may legitimately document safety this way when no acute safety event
   occurred, but this has not been stress-tested against a patient with an active safety concern.
3. **Response documentation inconsistent** — Pain has a complete, unambiguous response step
   ("appeared less guarded... stated he was a little more comfortable"). Respiratory has a clear
   response. Skin's response is phrased as an absence-of-harm statement ("no new area of redness
   was created") rather than a positive observed improvement — functionally acceptable but weaker
   than Pain/Respiratory.
4. **Clinical judgment sometimes implied rather than stated** — Pain has an explicit, standalone
   judgment sentence connecting the finding to the reasoning ("Norco has not been providing
   enough relief... pain control and bowel management need to be handled together"). Respiratory
   and Safety currently only imply judgment through the intervention/instruction chosen, without a
   standalone reasoning sentence. Whether to add an explicit judgment requirement to the prompt,
   and how to do so without reintroducing summarizing/explanatory AI-report voice (which is
   explicitly banned per Section 11), is an open design question — not yet resolved.
5. **PRN and DEATH assessment types are narrative-engine-only** — `_ASSESSMENT_TYPE_LABELS`,
   `_ASSESSMENT_TYPE_VOICE`, and `_ASSESSMENT_TYPE_FLOW` support these two types, but
   `backend/app/api/visits.py` (`_normalize_rnica_assessment_type`) and the frontend UI do not yet
   allow a real assessment to be created with `assessment_type="PRN"` or `"DEATH"`. The engine can
   voice these documents correctly if given the value, but nothing currently produces that value
   in production. This is a known, unresolved integration gap, not a narrative-quality gap.
6. **Stale documentation reference** — `backend/app/api/visits.py` (~line 1780) still has a
   docstring on the narrative-preview endpoint describing an old 10-section report format with
   the exact banned headers from Section 11. This is dead documentation (not live code) and has
   not yet been corrected.
7. **Extending Sections 7/8/9 fixes beyond RNICA** — the caregiver-capability, RN-actor, and
   scope-of-practice corrections described in Sections 7–9 were validated and fixed against
   RNICA specifically. They live in shared prompt sections used by all five visit types, but have
   not yet been re-verified end-to-end against UPDATE/RECERT/PRN/DEATH output specifically.
8. **Norma has no ECOG value anywhere** — traced the full pipeline (source documents → harvested
   evidence → structured field → API → narrative) on 2026-09-08 while investigating the Kessler
   FAST gap above. Unlike Kessler's FAST value, a full-text search across all 7 of Norma's
   `PatientEvidenceRecord` source documents for "ECOG," "KPS," "PPS," "performance status," and
   "Karnofsky" found **zero matches** — no performance-status scale of any kind appears anywhere
   in her uploaded source material. Her cancer diagnosis is correctly on file at the patient
   level (`Patient.primary_diagnosis` = "Metastatic breast cancer, Stage IV, with bone
   metastasis"), and her structured `diagnoses.primaryDiagnosis` field on this specific RNICA
   assessment is also blank (a separate, smaller data-entry gap). Per the explicit instruction not
   to fabricate values that do not exist in source data, **no ECOG value has been created for
   her.** This is documented here as a genuine, currently-unresolved data gap, not fixed. If a
   real ECOG assessment becomes available for her (e.g. a future document upload, or an RN
   performs and documents one live), populate it the same way Kessler's FAST was populated —
   transcribed from a real, cited source, never invented.
   **CORRECTION (2026-09-08, later same day — see Discovery Log entry below)**: this item's
   conclusion is superseded, not retracted. Norma's `performanceStatus` now contains
   `kps="20"`, `pps="20%"`, `ecog="4"` — entered directly by clinical staff through the RNICA
   form as valid manual clinician documentation (confirmed by the reporting clinician). This is
   a legitimate structured finding, not a fabricated value; the earlier "genuinely absent"
   conclusion was correct **only for document-harvested evidence**, which is still true — no
   source document contains these values. See Open Gaps items 9–11 below for the systemic gaps
   this surfaced.
9. **No provenance is recorded for manually-entered structured fields** — `RnicaAssessment` has a
   working provenance mechanism, `field_provenance` (a list of `{path, value, section, signal_id,
   confidence, recorded_at, source_type, concept_code, source_excerpt}` records), populated
   automatically for document-harvested findings (confirmed for Norma: 22 entries, all
   `source_type=DOCUMENT_UPLOAD`, covering vitals/cardiovascular/GI/neuro/infection fields).
   However, `performanceStatus.*` fields (kps/pps/ecog/fast/nyha) have **zero** `field_provenance`
   entries for Norma even though they are now populated — confirming these were typed directly
   into the form and bypass the provenance pipeline entirely. There is no `source_type` value for
   `RN_MANUAL_ENTRY`, no capture of which user entered/confirmed a value, and no timestamp for
   manual saves. Any structured field a clinician types directly (not just Performance Status)
   has this same gap. **Required future behavior**: every write path that sets a structured RNICA
   field — not only the AI-harvest path — should append a `field_provenance` entry, with a new
   `source_type=RN_MANUAL_ENTRY` (or `RN_CONFIRMED_AI_FINDING` when a suggested value is accepted
   as-is), the acting user, and a save timestamp.
10. **RNICA draft saves are not audited** — traced `PATCH /rnica/{assessment_id}` →
    `update_rnica_assessment` (`backend/app/api/visits.py:1177`) end-to-end: it calls
    `db.commit()` directly with no call into the audit service anywhere in the function. By
    contrast, `lock_rnica_assessment` (same file, ~line 1333) does write an `AuditLog` row
    (`entity_type="rnica_assessment"`) when an assessment is signed/locked. Net effect: every
    draft edit — including a clinician typing in Performance Status values — is invisible to
    `AuditLog`; only the final lock/sign event is captured. This is why "who populated Norma's
    ECOG and when" could not be answered from the audit trail and had to be inferred from
    `updated_at` and the absence of a matching provenance entry. **Required future behavior**:
    `update_rnica_assessment` should write an audit entry per save (at minimum: assessment id,
    user, timestamp, and which top-level `formData` sections changed), without necessarily
    diffing every nested field.
11. ~~Two independent code paths write the one authoritative narrative field~~ — **Resolved
    2026-09-08, see Section 13.** "Build Draft from Documented Findings" now calls the backend V2
    preview endpoint instead of the local `clinicalNarrativeBuilder.js` template.

These items are the active roadmap for this narrative engine. When one is resolved, move it out
of this section into Section 13 (Resolved Findings) and update the relevant section above (do not
just delete it).

---

## Test Data Policy

All patients currently in this development environment (Loren, Norma, Kessler, and any others)
are **development and regression-test records, not production clinical data.** Test records may
be cleaned and repopulated using a documented, reproducible process when stale, conflicting,
duplicated, or obsolete test-state residue prevents reliable regression validation. Production
clinical-data retention, immutability, and amendment rules (e.g. the locked/signed-assessment
correction workflow) do not apply to disposable development fixtures — but conversely, production
system behavior must never be modeled on destructive test-data cleanup logic; the two are
intentionally separate concerns. See `docs/testing/rnica-test-patient-manifest.md` for the
current registry of test patients and their expected state.

As of 2026-09-08, no cleanup/repopulation was required — all three regression patients
(Loren/Norma/Kessler) passed validation against their existing data once the narrative-writer
conflict (Section 13) was fixed; see Section 18 (Regression Test Matrix).

---

## Section 15 — Change Control Requirement

Any future modification to the RNICA narrative engine (prompt rules, flow guidance, voice
guidance, safety-net logic, or assessment-type handling) must:

1. **Review this architecture map first** — check whether the behavior being changed is already
   documented, and whether the change conflicts with a resolved finding (Section 13) or an
   established anti-pattern (Section 11).
2. **Update this architecture map when discovery occurs** — in the same change, not as follow-up
   cleanup. A new rule with no corresponding section update is treated as incomplete work.
3. **Reference this architecture map in the PR description** — state which section(s) were
   consulted and which section(s) were updated.
4. **Record new findings before the change is considered complete** — a discovery that fixes a
   defect is not done until it is captured in Section 13 (if resolved) or Section 14 (if a
   partial/open item remains).

This is not optional process overhead — it is what allows this engine to be modified safely by
someone who was not present for the original discovery conversations.

---

## Section 16 — Discovery Log

The Architecture Map (Sections 1–15) documents the **current state** of the RNICA engine. This
log documents **how that state came to be** — chronologically, in the order discoveries were
made, including what was found, why it mattered, what was decided, and where the resolution
lives. Sections above answer "how does this work today." This log answers "why does this rule
exist" without requiring anyone to search chat history, tickets, or old conversations.

**Entries must be appended, never rewritten or deleted.** If a decision is later reversed or
superseded, add a new entry noting the change and referencing the original — do not edit history.

---

**2026-09-08**

**Finding**: The narrative engine never read `record.assessment_type` or
`visitMeta.reasonForVisit`; `SYSTEM_PROMPT` hardcoded an admission-style opening regardless of
visit type.

**Impact**: RNICA, UPDATE, and RECERT notes all sounded the same regardless of what kind of visit
actually occurred — the highest-severity defect found this cycle, since it meant the document
type had no effect on the document produced.

**Decision**: Assessment type and `reasonForVisit` became required narrative inputs.
`SYSTEM_PROMPT` was converted to `_build_system_prompt(assessment_type_code, reason_for_visit)`,
generated fresh per document. PRN and DEATH were added as new first-class narrative document
types (not yet wired into real business logic — see Section 14, item 5).

**Alternatives considered**: none — this was a missing-input bug, not a design choice with
competing options.

**Status**: Resolved.

**Reference**: Section 4 (Visit Context Framework), Section 13 (Resolved Findings, row 1).

---

**2026-09-08**

**Finding**: Even after visit-type differentiation was fixed, RNICA and UPDATE narratives
literally announced their own visit type in the opening sentence (e.g. "visit to complete initial
comprehensive assessment," "seen today for routine follow-up visit").

**Impact**: Differentiation between visit types is necessary but not sufficient — a document that
announces its own type reads as metadata-driven, not as authentic clinical documentation. This
failed the "hide the header, read the narrative" authenticity test even though the five types
were now objectively different from each other.

**Decision**: Added an explicit "NEVER NAME THE DOCUMENT TYPE OR VISIT REASON DIRECTLY" rule.
Visit type must be revealed only through content, depth, and structure.

**Alternatives considered**: a Python-side regex filter to strip self-naming phrases after
generation was considered and rejected, consistent with the existing precedent that stylistic/
voice rules are enforced prompt-only to avoid fragile regex-based sentence mangling; factual
completeness (e.g. scale-meaning safety nets) remains code-enforced, voice does not.

**Status**: Resolved.

**Reference**: Section 4, Section 11 (Narrative Anti-Patterns).

---

**2026-09-08**

**Finding**: RN actor disappeared from large portions of the generated narrative. Roughly half of
all sentences describing an RN-performed action used passive voice with no stated actor ("teaching
was started," "code status was reviewed," "plan established today is for...").

**Impact**: Generated documentation read like a chart summary — facts that happened to be true —
rather than a record of what the nurse herself did. This was identified as the clearest single
tell separating AI-report voice from RN documentation voice.

**Decision**: The RN must be visible as the grammatical actor for every RN-performed assessment,
education, planning, and intervention action ("I assessed," "I reviewed," "I instructed," "I
established"). Passive/third-person phrasing is reserved for what the RN did not personally do
(patient/caregiver reports, objective facts).

**Alternatives considered**: none — this was treated as a factual-voice defect, not a stylistic
preference.

**Status**: Resolved.

**Reference**: Section 8 (RN Actor Rules), Section 13 (Resolved Findings, row 3).

---

**2026-09-08**

**Finding**: Caregiver capability assessment was underrepresented. The narrative documented that a
caregiver was present and, at best, "verbalized understanding," but never stated a judgment about
willingness, capability, competency, or ability to safely execute the plan.

**Impact**: This does not meet the California hospice regulatory expectation that the
comprehensive assessment evaluate caregiver willingness and capability, not merely caregiver
presence (see Section 2, Regulatory Foundation).

**Decision**: A dedicated Caregiver Framework was added, requiring the narrative to state a
task-specific judgment (e.g. "demonstrated safe repositioning technique" vs. "will need
reinforcement on bowel regimen timing") rather than one generic blanket statement.

**Alternatives considered**: a single closing "caregiver assessed as capable" sentence was
considered and rejected in favor of task-specific judgments, since a single blanket statement
does not reflect that competency can differ by task (e.g. good at repositioning, needs
reinforcement on medication timing).

**Status**: Resolved.

**Reference**: Section 7 (Caregiver Framework), Section 13 (Resolved Findings, row 4).

---

**2026-09-08**

**Finding**: RNICA contained almost no direct, hands-on RN-performed action — nearly every
sentence was "I reviewed," "I instructed," or "I discussed," with the nurse telling others what to
do rather than doing anything herself.

**Impact**: A first admission visit is not teaching-only; a real RN performs some hands-on
comfort/assessment actions herself. Its absence made the note read as supervisory rather than as
a clinician's own first encounter with the patient.

**Decision**: Required at least one or two specific, observable RN-performed actions per RNICA
narrative (e.g. "repositioned him for comfort," "offloaded a heel," "performed skin inspection").

**Alternatives considered**: none — this was additive, not a competing-design decision.

**Status**: Resolved.

**Reference**: Section 6 (Domain Map), Section 13 (Resolved Findings, row 5).

---

**2026-09-08**

**Finding**: Immediately after direct RN interventions were added, the narrative began
attributing routine passive range-of-motion stretching, massage, and scheduled repositioning to
the RN herself, as something she personally performed as ongoing care.

**Impact**: This is a scope-of-practice misattribution — these are LVN/CHHA-level recurring tasks
in this care model, not RN tasks. An RN or QA reviewer would immediately flag this as inaccurate
documentation of who does what.

**Decision**: Added an explicit scope-of-practice rule distinguishing RN tasks (assessment,
judgment, delegation, in-the-moment comfort actions during the visit itself) from LVN/CHHA tasks
(routine stretching, massage, scheduled repositioning). The RN's role in this domain is now
documented as delegation stated in the plan of care ("I instructed the LVN/CHHA to provide
passive range-of-motion, massage, and repositioning every two hours..."), not as her own action.

**Alternatives considered**: none — this was a factual scope-of-practice correction raised
directly by the product owner's domain knowledge, not a stylistic judgment call.

**Status**: Resolved.

**Reference**: Section 9 (Scope of Practice Rules), Section 13 (Resolved Findings, row 6).

---

**2026-09-08**

**Finding**: A live architectural audit (Finding → Judgment → Intervention → Response → Teaching →
Plan) of a real generated RNICA narrative found the chain fully complete for Pain, mostly complete
for Respiratory and Skin, but incomplete for GI/GU and Safety — those two domains produced
Finding → Teaching → Plan only, with no RN-performed intervention or observed response, because
nothing acute occurred in those domains during the sampled visit.

**Impact**: Confirms the reasoning chain is achievable when a domain is clinically active, but has
not been stress-tested against a patient whose admission includes an acute GI/GU or safety issue.
Also confirms that "nursing judgment" is currently expressed as a standalone reasoning sentence in
some domains (Pain) but only implied through the chosen intervention in others (Respiratory,
Safety).

**Impact of over-fixing considered**: forcing an intervention/response into every domain
regardless of clinical activity would risk fabricating events that did not happen during the
visit — explicitly rejected as a direction.

**Decision**: Documented as an open gap rather than immediately patched, pending validation
against a patient record with an acute GI/GU or safety finding, and pending a decision on how to
require explicit judgment sentences without reintroducing banned AI-summary voice.

**Status**: Open (not yet resolved).

**Reference**: Section 5 (Workflow Map), Section 14 (Open Gaps, items 1–4).

---

**2026-09-08**

**Finding**: Regression-testing the three permanent validation patients found Norma's ECOG and
Kessler's FAST performance-status fields both blank in `performanceStatus`. Per instruction, a
full pipeline trace (source document → evidence extraction → database → API → Performance Status
→ narrative → Evidence Center) was performed for each before deciding whether to fix or document.

**Impact**: The two failures had different root causes despite looking identical on the surface.
Kessler's source PDF (`kessler_hnp_chart_consents.pdf`) was already uploaded and OCR'd, and its
raw extracted text literally contains the value (`"KPS 30 7-E FAST PPS 30 NYHA"`) — it was simply
never transcribed into the structured field, a data-entry gap. Norma's evidence records (all 7,
full-text searched) contain **no** ECOG/KPS/PPS/performance-status mention anywhere — a genuine
absence in her source data, not an extraction bug. This trace also surfaced that there is no
automated scale-extraction pipeline in this system at all — PPS/KPS/NYHA/FAST/ECOG are RN-entered
structured fields (confirmed by how Loren's reference values were originally populated: a manual
transcription script, not an AI extraction step).

**Decision**: Fixed Kessler via `backend/scripts/populate_kessler_performance_status_from_pdf.py`,
transcribing the literal, cited source-document values (kps=30, pps=30%, fast=7e) — nothing
fabricated, every value quotes its source. Did NOT fix Norma — no real value exists to transcribe,
and per explicit instruction, no value should be fabricated. Norma's gap is documented (Section
14, item 8) as an open, unresolved item until real ECOG source data exists.

**Alternatives considered**: inferring or estimating an ECOG value for Norma from her diagnosis
severity was considered and explicitly rejected — this would be exactly the kind of fabricated
clinical value the architecture map's authenticity standard exists to prevent.

**Status**: Kessler — Resolved. Norma — Open (by design, not an oversight).

**Reference**: Section 13 (Resolved Findings), Section 14 (Open Gaps, item 8), Section 17 (Test
Patient Registry), Section 18 (Regression Test Matrix).

---

**2026-09-08**

**Finding**: Later the same day, a report that Norma's displayed narrative still resembled a
pre-redesign report format ("HOSPICE CLINICAL PICTURE / REASON FOR HOSPICE ADMISSION / EVIDENCE
OF DECLINE / DISEASE-SPECIFIC SUPPORT") triggered a full re-investigation, since those exact
headers are banned anti-patterns (Section 11). Investigation found: (1) no new recording or
document exists for Norma — her `DocumentRecord`/`PatientEvidenceRecord` rows are unchanged since
2026-09-04, confirmed by file count, timestamps, and SHA-256 hash comparison of the session's
duplicate attachment set; (2) her `performanceStatus` had changed since the prior entry above —
`kps="20", pps="20%", ecog="4"` were now present, confirmed by the reporting clinician to be
manually entered documentation, not fabricated or test data; (3) the legacy-style headers come
from a second, independent narrative generator (`clinicalNarrativeBuilder.js`, a deterministic
frontend template wired to the "Build Draft from Documented Findings" button), not from the RNICA
V2 engine or from stale AI output; (4) manually-entered structured fields (Performance Status
here, but any field entered this way) receive **no** `field_provenance` record, unlike
document-harvested fields, which do; (5) RNICA draft saves are not written to `AuditLog` at all
(only lock/sign events are) — confirmed by reading `update_rnica_assessment` end-to-end, not
assumed.

**Impact**: The earlier same-day conclusion "Norma's ECOG is genuinely absent" was correct only
for document-harvested evidence — it did not anticipate a clinician entering the value directly
through the form afterward, a valid and expected part of the RNICA workflow. Surfaced three
systemic gaps beyond Norma specifically: no provenance for manual entries, no audit trail for
draft saves, and two independently-writable code paths for one narrative field with no in-UI
indicator of which produced the currently-displayed text.

**Decision**: Norma's manually-entered values were left untouched (not reverted, not treated as
test data). No code changes were made to the narrative engine, provenance system, or audit
pipeline in this pass — investigation and documentation only, given the imminent deployment date.
Recommended future direction: repoint "Build Draft from Documented Findings" to the backend V2
preview endpoint (ADAPTER, not RETIRE, for `clinicalNarrativeBuilder.js`); extend
`field_provenance` writes to manual-entry save paths with a new `RN_MANUAL_ENTRY` source type;
add an audit-log write to `update_rnica_assessment`.

**Alternatives considered**: building a full Source Management UI (multi-document view, soft
delete, Set Active/Archive actions) before the deployment date was proposed and explicitly
deferred — it requires a schema migration and new write paths, which conflicts with the
deployment freeze already in effect.

**Status**: Open — see Section 14, Open Gaps, items 9–11 (this entry supersedes, not retracts,
the "Norma ECOG genuinely absent" framing in the entry above; both are true for their scope:
absent from documents, present from manual entry).

**Reference**: Section 11 (Anti-Patterns), Section 14 (Open Gaps, items 8–11), Section 17 (Test
Patient Registry).

---

**2026-09-08**

**Finding**: Consolidated the narrative-generation path per explicit direction to declare the
backend RNICA V2 service the single narrative-composition engine. Also confirmed, after further
clarification, that Norma's manually-entered PPS 20%/KPS 20/ECOG 4 are legitimate RN documentation
(not test artifacts) — a manual clinical entry is a valid source type, distinct from but equal in
standing to document-harvested evidence; the earlier framing that treated a missing source
citation as a validity problem was itself a mistake to correct, not the data.

**Decision**: Repointed "Build Draft from Documented Findings" (`ClinicalNarrativeCard.applyDraft()`
in `sns-emr-frontend/src/components/RNICA.jsx`) to call `previewRnicaNarrativeV2()` — the same
`POST /rnica/{assessment_id}/narrative-v2/preview` endpoint Documentation Insights already used —
instead of the local `clinicalNarrativeBuilder.js` template. The local template is retained only
as an offline fallback (no `assessmentId` yet, or the API call fails) so the button never goes
fully dead; it is no longer a second active narrative-composition path. Corrected the stale
docstring on `preview_rnica_narrative_v2` (`backend/app/api/visits.py`), which still described the
old fixed 10-section report format. Did **not** touch Norma's manually-entered values, and did not
build a full Source Management UI, provenance redesign, or audit-framework redesign in this pass
— those remain open (Section 14, items 9–10) per explicit instruction not to expand scope before
deployment.

**Verified**: direct backend calls to `generate_rnica_narrative_v2()` for all three regression
patients — Loren (PPS/KPS/NYHA present), Norma (PPS 20%/KPS 20/ECOG 4 present, correctly reflects
her manual entry), Kessler (PPS/KPS/FAST present) — confirm free-flowing prose narratives with
zero occurrences of the banned legacy headers ("hospice clinical picture," "reason for hospice
admission," "evidence of decline," "disease-specific support"). No cleanup/repopulation of test
patient data was required — see Test Data Policy section and Section 18 (Regression Test Matrix).

**Alternatives considered**: clearing or "fixing" Norma's manually-entered values to restore a
provenance-clean state was proposed in an earlier pass and explicitly rejected — punishing valid
staff documentation for a system-design gap (missing provenance capture) was identified as the
wrong tradeoff.

**Status**: Resolved (narrative SSOT). Open (manual-entry provenance, draft-save audit — see
Section 14, items 9–10, tracked separately and intentionally not solved in this pass).

**Reference**: Section 11 (Anti-Patterns), Section 13 (Resolved Findings), Section 14 (Open Gaps,
items 9–10), Test Data Policy, `docs/testing/rnica-test-patient-manifest.md`.

---

**2026-09-08**

**Finding**: Backend-only verification of the duplicate-narrative-writer fix (direct calls to
`generate_rnica_narrative_v2()`, plus a browser-automation click-through that read the resulting
textarea in-memory but never explicitly confirmed the value was saved and reloaded) produced a
false PASS. A live screenshot of Norma's assessment in a separate, real browser session showed
"Build Draft from Documented Findings" with the *previously-saved* pre-fix legacy narrative still
displayed ("HOSPICE CLINICAL PICTURE" / "REASON FOR HOSPICE ADMISSION" / etc.) and the on-page
"Narrative Quality Gate: FAIL" banner still present, directly contradicting the "Resolved" status
already recorded in Section 13.

**Impact**: Compile success, API success, and even a browser-automation click that reads updated
state in-memory are all insufficient evidence that a fix is live for an end user — none of them
prove the result was persisted and would survive a real reload. The gap: an earlier
verification pass regenerated Norma's narrative once, observed the correct V2 text in the
textarea, and stopped there without an explicit save-then-reload check, so it could not detect
whether the update was ever durable. Investigating the screenshot as the acceptance test (per
explicit instruction) surfaced no new engine defect — the live button, when actually clicked and
network-traced, worked correctly — but it did expose that the verification method itself had a
gap.

**Decision**: Re-ran the full live-browser acceptance test with instrumented request capture
(hooked `window.fetch`/`XMLHttpRequest` before interacting) rather than trusting DOM reads or
backend logs alone: (1) confirmed the running frontend/backend processes and Git commit
(`feature/production-hnp-clinical-runtime @ 65b2187`) matched the on-page build banner and the
worktree containing the fix; (2) clicked "Build Draft from Documented Findings" → "Replace with
New Draft" live for Norma and captured the exact network request —
`POST /visits/rnica/cb060604.../narrative-v2/preview` → `200 OK`, matching the expected V2
endpoint, not `clinicalNarrativeBuilder.js`; (3) confirmed the resulting narrative (8,678 chars)
had zero legacy headers, correctly incorporated PPS 20%/KPS 20/ECOG 4 with interpretation, and the
Narrative Quality Gate banner cleared to passing; (4) captured the autosave
`PUT /visits/rnica/cb060604...` → `200 OK`; (5) hard-reloaded the page, re-navigated to the same
Finalization section, and confirmed the identical persisted text was still present — proving
durability, not just in-memory state. Repeated the click→trace→persist sequence for Kessler with
the same result (FAST 7e/PPS 30%/KPS 30 present, zero legacy headers, `200 OK` on both the preview
and autosave calls). No code changes were required — the underlying fix from the prior entry was
already correct; only the verification method was insufficient.

**Alternatives considered**: dismissing the screenshot as a stale cache or a different
worktree/build was considered and explicitly rejected without proof; Step 1 (confirm active
source tree) was performed first and ruled both out before any other explanation was accepted.

**Status**: Resolved — narrative SSOT fix now carries `VERIFIED_WORKING_END_TO_END` evidence
(live browser, instrumented network capture, save-then-reload persistence), not backend-only
evidence. See the updated "Verified" column for this finding in Section 13.

**Reference**: Section 11 (Anti-Patterns), Section 13 (Resolved Findings), Section 17 (Test
Patient Registry), Section 18 (Regression Test Matrix).

---

**2026-09-08**

**Finding**: A "reachable only when unsaved or on API failure" fallback was still judged
unacceptable — `buildClinicalNarrative()` and its 31 KB file (`clinicalNarrativeBuilder.js`)
continued to exist, remained importable, and still contained the banned report-style template
(HOSPICE CLINICAL PICTURE / REASON FOR HOSPICE ADMISSION / EVIDENCE OF DECLINE /
DISEASE-SPECIFIC SUPPORT), even though the prior entry's fix meant it could not fire for any
saved patient record in practice.

**Impact**: A latent code path capable of producing an explicitly banned anti-pattern is a live
architectural risk regardless of how narrow its reachability is today — a future refactor could
easily reintroduce a call to it, or the "unsaved assessment" condition could become reachable
again without anyone noticing. "Provably unreachable in current code" is not the same guarantee
as "does not exist."

**Decision**: Deleted `clinicalNarrativeBuilder.js` and `clinicalNarrativeBuilder.test.js`
entirely — no rename, no move to a "legacy/" folder, no retention as historical reference in
source. The engine-agnostic infrastructure the file also held — `DISEASE_TRAJECTORY_OPTIONS` /
`isLegacyDiseaseTrajectoryValue` / `getDiseaseTrajectoryLabel`, `computeNarrativeContextFingerprint()`
(staleness detection), and `evaluateNarrativeQualityGate()` (the field-dump/leakage linter that
originally caught the Norma legacy-header regression) — was extracted unchanged into a new module,
`sns-emr-frontend/src/intake/narrativeSupport.js`, with its own test file. `RNICA.jsx`'s
`ClinicalNarrativeCard.applyDraft()` no longer has an `!assessmentId` branch that generates any
narrative locally; requesting `previewRnicaNarrativeV2()` is the only way a draft narrative is ever
produced. For an assessment that has not yet been saved, `handleBuildDraft()` now shows a
save-first message using only plain clinical language — no "assessmentId," "API," "backend,"
"V2," or "fallback" appears in the user-facing text — with a "Save Assessment" button that calls
a new `saveNow()` action added to `useAssessmentAutosave()` (an explicit, awaitable version of the
same create/update logic the existing 30-second background autosave already uses); no field the RN
entered is read, cleared, or overwritten by this path. V2-failure behavior needed no change: it
already showed the error, offered Retry, and never fell back to any local narrative or overwrote
existing text.

**Alternatives considered**: keeping `buildClinicalNarrative()` behind an additional guard/feature
flag was rejected — a disabled-but-present banned template is still a latent risk and does not
meet "removed completely."

**Status**: Resolved. Verified via: (1) repository-wide search confirming zero remaining
references to `clinicalNarrativeBuilder`/`buildClinicalNarrative` outside this log, the Section 13
row above, `narrativeSupport.js`'s explanatory comment, and a historical comment in
`rnica_narrative_v2_service.py`; (2) 14/14 tests passing in the new `narrativeSupport.test.js`
(ported from the deleted file's non-legacy-writer coverage) and 6/6 new tests passing in
`ClinicalNarrativeCard.test.jsx` (saved-assessment path, unsaved-assessment save-first message with
no jargon, Save Assessment action, V2 failure/Retry with no fallback, existing-narrative replace
confirmation, and narrative+fingerprint+review-reset written together); (3) full frontend suite
276/276 passing across 19 files; (4) `tsc -b` introduces zero new errors (pre-existing, unrelated
MUI type errors in `FacilityCollectionsReportPage.tsx` confirmed present on the unmodified
baseline); (5) re-ran the full live click→network-trace→save→reload verification in-browser for
Loren, Norma, and Kessler after this change — all three continue to show V2-only narratives with
zero legacy headers and correct scale values.

**Reference**: Section 11 (Anti-Patterns), Section 13 (Resolved Findings, "LEGACY FRONTEND
NARRATIVE WRITER REMOVED"), Section 17 (Test Patient Registry), Section 18 (Regression Test
Matrix).

---

## Section 17 — Test Patient Registry

Purpose: preserve the regression patients used to discover and validate architecture decisions in
this document. These patients are not documentation templates and not narrative examples to
imitate — they are regression-test assets. A future developer who asks "why do we keep this
patient around?" should get the answer from this section, not from memory or chat history.

**Rule**: any future major workflow engine documented under the Architecture Map Policy
(`docs/engineering/architecture_map_policy.md`) must identify its reference test patients,
reference scenarios, and reference validation datasets, and record them in its own Test Patient
Registry section.

---

**Loren**

- Purpose: CHF (congestive heart failure) pathway validation.
- Validates: PPS, KPS, NYHA staging and interpretation; RNICA workflow chain (Finding → Judgment →
  Intervention → Response → Teaching → Plan); caregiver capability assessment; direct RN
  intervention documentation; scope-of-practice delegation language (LVN/CHHA musculoskeletal
  care).
- Patient ID: `3ea2f6fa-8dd9-4e3c-9b7d-009ddbe17ab0`. RNICA assessment ID:
  `1fcea12a-24c9-498b-8b9d-0fdc9fc54aa8`. (Corrected 2026-09-08: this section previously labeled
  the assessment ID as the patient ID — verified against the database while producing the Demo
  Readiness Report, `docs/planning/demo_readiness_thursday.md`.)
- Discovered/used in: nearly every discovery in Section 16 (Discovery Log) — the primary
  regression patient for this engine's development cycle.

---

**Norma**

- Purpose: cancer pathway validation.
- Validates: ECOG performance status; cancer-decline documentation; hospitalization narrative
  content; election-of-hospice workflow language.
- Patient ID: `53fe69e1-fcd5-4b49-8203-9b890b18b7d6`. RNICA assessment ID:
  `cb060604-405d-4b09-b4dc-e313542d4a31`.
- Role in this project: used only as an **authenticity benchmark** for how an experienced hospice
  RN naturally documents workflow — never as a template to copy, mirror, or structurally imitate
  (see Section 12, Authenticity Test). Narrative rules derived from Norma must be justified by the
  underlying clinical/regulatory requirement she illustrates, not by matching her wording.
- **Known data gap (found 2026-09-08, see Demo Readiness Report,
  `docs/planning/demo_readiness_thursday.md`; confirmed genuine and traced fully on 2026-09-08 —
  see Section 14, Open Gaps, item 8)**: her structured `performanceStatus.ecog` field is currently
  blank, and a full-text trace across all 7 of her uploaded source documents found **zero**
  mentions of ECOG, KPS, PPS, or any performance-status scale — this is a genuine absence in her
  source data, not an extraction or transcription bug (contrast with Kessler's FAST, which existed
  in source but was untranscribed). No value has been fabricated. Her cancer diagnosis is
  correctly present at the patient level but not on this specific RNICA assessment's
  `diagnoses.primaryDiagnosis` field. This is a data-entry gap in the demo record, not a defect in
  the narrative engine — narrative generation itself succeeds.
- **UPDATE (2026-09-08, later same day)**: `performanceStatus` is no longer blank —
  `kps="20"`, `pps="20%"`, `ecog="4"` were entered directly by clinical staff through the RNICA
  form. This is valid `RN_MANUAL_ENTRY`-class documentation, not fabricated/test data (source type
  not yet captured in `field_provenance` — see Section 14, item 9). This does not reverse the
  document-harvest finding above (still true: no source document contains these values) — it adds
  a second, equally valid source class the earlier framing hadn't accounted for. Regenerated V2
  narrative confirmed to include "She is at ECOG 4..." correctly.

---

**Kessler**

- Purpose: dementia pathway validation.
- Validates: FAST staging and interpretation; cognitive-decline documentation; dementia-specific
  assessment and safety workflow (wandering, aspiration risk, decision-making capacity).
- Patient ID: `ba24830e-19f8-4b84-bbf3-e88374a6db25`. RNICA assessment ID:
  `5d39cc37-19a2-4e83-a1dc-46c8dcefc94b`.
- **Known data gap (found 2026-09-08, see Demo Readiness Report)**: her structured
  `performanceStatus.fast` field was blank until the same day — traced to a data-entry/
  transcription gap (the value existed in her already-uploaded source PDF but was never
  transcribed), **not** a genuine absence. Fixed via
  `backend/scripts/populate_kessler_performance_status_from_pdf.py` (kps=30, pps=30%, fast=7e,
  each cited to the literal source-document table). See Section 13 (Resolved Findings) for the
  full trace. Her dementia diagnosis (ICD-10 G31.1) is correctly on file. Narrative generation
  succeeds and now includes a fully-interpreted FAST 7e entry.

---

## Section 18 — Regression Test Matrix

Purpose: the Architecture Map (Sections 1–17) explains **why** a rule exists. This matrix converts
each major discovery into a repeatable check that verifies the rule **still holds** after a
change. Architecture documentation is protected by regression testing, not just described by it.

**Any major RNICA change should be re-validated against this matrix before merge.** Where a
verification method is currently manual (regenerate narrative, inspect for required content), that
should be treated as a candidate for future automation, not as a reason to skip it.

| Rule | Validation Patient | Expected Result | Verification Method |
|---|---|---|---|
| Assessment Type Awareness (Section 4) | Loren | RNICA structurally differs from UPDATE; RNICA structurally differs from RECERT | Generate all visit types for the same patient and compare opening, structure, and section focus |
| Document Type Not Self-Named (Section 4, Section 11) | Loren | Narrative does not name its own document/visit type in the text | Generate narrative; grep for self-naming phrases (e.g. "comprehensive assessment visit," "routine follow-up visit") |
| RN Actor Visibility (Section 8) | Loren | RN remains the visible actor throughout the assessment | Narrative contains first-person assessment/review/education/planning actions ("I assessed," "I reviewed," "I instructed," "I established") |
| Caregiver Capability (Section 7) | Loren | Willingness, capability, competency, need for reinforcement, and ability to safely execute the plan are all represented | Narrative contains task-specific caregiver judgment language, not just "caregiver present" or "verbalized understanding" |
| Direct RN Intervention (Section 6, Section 13 row 5) | Loren | At least one specific, observable RN-performed hands-on action is documented | Narrative contains a concrete RN-performed action distinct from teaching/instruction |
| Scope of Practice — Musculoskeletal Delegation (Section 9) | Loren | Routine ROM/massage/repositioning attributed to LVN/CHHA via delegation in the plan of care, not to the RN as her own ongoing action | Narrative reads "I instructed the LVN/CHHA to provide..." rather than "I perform/provide..." for these tasks |
| CHF Pathway (Section 10) | Loren | PPS, KPS, and NYHA scores are present with clinical interpretation, not raw values alone | Scores appear in narrative with meaning explained, and appear correctly in the Performance Status data |
| Cancer Pathway (Section 10) | Norma | ECOG score present with interpretation; cancer-decline evidence documented | **PASS (as of 2026-09-08, manual clinician entry)** — `performanceStatus.ecog="4"`/`kps="20"`/`pps="20%"` entered by clinical staff through the RNICA form; regenerated V2 narrative confirmed to include "She is at ECOG 4..." with interpretation. Still no ECOG value in any uploaded source document (see Section 17) — passes on the manual-entry source class, not document-harvest |
| Dementia Pathway (Section 10) | Kessler | PPS, KPS, and FAST scores present with clinical interpretation; cognitive-decline documentation present | **PASS (fixed 2026-09-08)** — Score and cognitive-decline evidence present and interpreted in generated narrative ("She is at FAST 7e, with advanced dementia no longer able to smile..."); verified via `scale_clinical_evidence` output after running `backend/scripts/populate_kessler_performance_status_from_pdf.py` (see Section 13, Resolved Findings) |
| Workflow Reasoning Chain (Section 5) | Loren | Finding → Judgment → Intervention → Response → Teaching → Plan present for at least Pain, Respiratory, and Skin domains | Manual domain-by-domain audit of a generated narrative against the six-step chain |
| Authenticity Test (Section 12) | Loren, Norma, Kessler | An experienced hospice RN would sign the note as an Initial Comprehensive Assessment without rewriting most of it | Hide document type/metadata/headers and have an RN, Clinical Manager, or QA reviewer read the narrative alone |

Known gap: GI/GU and Safety domain reasoning-chain completeness (Section 14, items 1–2) does not
yet have a passing row in this matrix — it cannot be marked as a protected rule until it is
resolved. Add a row here at the same time it is resolved and logged in Section 16.

All three regression patients (Loren, Norma, Kessler) pass as of 2026-09-08. Norma's ECOG passes
via manual clinician entry rather than document harvest — this is a valid but distinct source
class (Section 14, item 9 tracks the still-open gap that this source class isn't yet captured in
`field_provenance`).

---

## Repository Standard

This document is the reference implementation of the repository-wide Architecture Map Policy
(`docs/engineering/architecture_map_policy.md`). The same structure and discipline applies to any
other major clinical workflow or AI-driven engine reaching a comparable level of iterative
discovery, including but not limited to: Documentation Insights, LCD Support, Evidence Harvester,
Recertification Reasoning Framework, Plan of Care generation, Certification Narratives, the Task
Engine, and Benefit Period Logic. Architecture knowledge belongs in version control, not in
conversation history.
