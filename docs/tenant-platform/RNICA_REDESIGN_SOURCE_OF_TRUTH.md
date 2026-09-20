# RNICA Redesign Source of Truth

**VERSION:** 1.1, authority-labeled Figma input package
**STATUS:** AUTHORITATIVE DESIGN INPUT. NOT IMPLEMENTATION AUTHORIZATION.
**CODE:** BLOCKED
**SCHEMA:** BLOCKED
**MIGRATIONS:** BLOCKED
**CURRENT DEFECT REPAIR:** BLOCKED UNDER THIS DOCUMENT

Companion document: `RNICA_SCREEN_BY_SCREEN_EVIDENCE_MATRIX.md` (names the
supporting discovery document(s) for every screen's underlying content).

## 1. Purpose

This document defines the approved future RNICA information architecture
and nurse workflow for Figma. It translates the approved discovery package
and locked decisions into a workflow-first design specification without
treating repository structure as design authority.

Figma must design from patient context, clinical evidence, nurse
workflow, hospice workflow, visible compliance readiness, and honest AI
assistance. Figma must not recreate current RNICA navigation, current
card placement, repository structure, React component structure, database
structure, or a HospiceMD-style chart hierarchy.

## 2. Authority Legend

- **[REPOSITORY-DISCOVERED]** Proven current field, behavior, dependency,
  validation, trigger, consumer, or non-connection.
- **[LOCKED PRODUCT DECISION]** Approved future-state decision that may
  supersede current repository placement.
- **[REGULATORY / CLINICAL AUTHORITY]** Controlling assessment,
  plan-of-care, documentation, or terminal-status principle. This label
  does not imply that the current repository already implements the
  requirement.
- **[DESIGN REQUIREMENT]** Figma presentation/interaction requirement
  preserving the approved authorities.
- **[FUTURE PRODUCT DIRECTION]** Desired capability not established as
  current functionality.
- **[NOT BUILT / NOT CONNECTED]** Explicit discovery non-finding. Figma
  must not represent this as operational.
- **[OPEN DEFECT]** Existing defect documented separately and not repaired
  by this redesign artifact.

## 3. Global Locked Decisions

- **[LOCKED PRODUCT DECISION]** `finalization.clinicalNarrative` is the
  sole authoritative nurse-facing Clinical Narrative.
- **[LOCKED PRODUCT DECISION]** Diagnosis shows no Clinical Narrative,
  Clinical Diagnosis Narrative, Final Assessment Narrative, Clinical
  Synthesis Narrative, or Attestation Narrative.
- **[LOCKED PRODUCT DECISION]** Historical `diagnoses.clinicalNarrative`,
  review-state values, amendments, audit history, and locked records are
  preserved without automatic merge or overwrite.
- **[OPEN DEFECT]** Historical/API-created records with a populated
  Diagnosis narrative and an untrue review flag may be unable to lock
  because the current review control is unreachable.
- **[LOCKED PRODUCT DECISION]** PPS and KPS are always visible.
- **[LOCKED PRODUCT DECISION]** FAST appears only for dementia,
  Alzheimer's disease, or dementia-related diagnosis.
- **[LOCKED PRODUCT DECISION]** ECOG appears only for cancer, oncology
  diagnosis, metastatic disease, or hematologic malignancy.
- **[LOCKED PRODUCT DECISION]** NYHA appears only for CHF, heart failure,
  or cardiomyopathy.
- **[LOCKED PRODUCT DECISION]** Hidden scales are not rendered as
  disabled, placeholder, or "Not Applicable" controls.
- **[DESIGN REQUIREMENT]** Preserve HOPE, POC, Validation, Structured
  Findings, RNICA Intelligence, Autosave, Lock, Amendments, Audit Trail,
  Required Fields, and LCD Narrative.

## 4. Global Capability Boundaries

- **[REPOSITORY-DISCOVERED]** Intelligence refreshes on load, Save, and
  Lock, not live typing.
- **[REPOSITORY-DISCOVERED]** RNICA Intelligence is a deterministic
  recommendation-only rules/heuristics engine.
- **[NOT BUILT / NOT CONNECTED]** Dedicated Patient Story engine,
  Explanation Engine, CTI integration, F2F integration, Survey Readiness,
  and RNICA Billing Readiness are not established as current RNICA
  capabilities.
- **[REPOSITORY-DISCOVERED]** POC, HOPE, Validation, Structured Findings,
  Autosave, Lock, Amendments, and audit events are wired.
- **[DESIGN REQUIREMENT]** The UI must distinguish saved intelligence from
  in-progress edits and must not imply continuous AI analysis when none
  exists.
- **[DESIGN REQUIREMENT]** Hospice eligibility evidence must be shown as
  documentation support, not an automatic substitute for physician
  judgment.

---

# Screen 1. Patient Story

**Purpose**
- **[DESIGN REQUIREMENT]** Give the nurse a patient-first orientation
  before entering the assessment workflow.

**Why the nurse comes here**
- **[DESIGN REQUIREMENT]** Review patient/admission context, terminal
  diagnosis, decline evidence, caregiver context, and current risks in one
  place.

**Always visible**
- **[REPOSITORY-DISCOVERED]** Patient identity and admission context
  already exist as read-only/prefilled context.
- **[REPOSITORY-DISCOVERED]** Primary diagnosis, disease/terminal-
  prognosis content, caregiver fields, intelligence findings, and
  missing-evidence output exist in separate current areas.
- **[DESIGN REQUIREMENT]** Present those sources as a read-only
  orientation summary with provenance links.

**Conditionally visible**
- **[DESIGN REQUIREMENT]** Prior-assessment decline comparison,
  hospitalization/utilization evidence, and risk summaries appear only
  when source data exists.

**AI content**
- **[REPOSITORY-DISCOVERED]** Intelligence summary, findings,
  recommendations, missing evidence, and prior-assessment comparison may
  be presented.
- **[FUTURE PRODUCT DIRECTION]** A generated narrative Patient Story is
  not current functionality.

**Compliance content**
- **[DESIGN REQUIREMENT]** Show source evidence and review state. Do not
  label the summary as certification or an eligibility determination.

**Required actions**
- **[DESIGN REQUIREMENT]** Review and navigate to source sections when
  correction is needed. Do not require a new duplicate "story approval"
  field unless separately authorized.

**Completion criteria**
- **[DESIGN REQUIREMENT]** Identity, diagnosis, admission context, decline
  evidence, caregiver context, risk findings, missing evidence, and source
  links are reachable from the screen.

**Do not show**
- **[NOT BUILT / NOT CONNECTED]** No claimed Patient Story engine,
  billing-readiness result, CTI result, F2F result, or survey-readiness
  result.

**Do not touch**
- **[DESIGN REQUIREMENT]** Source authorities remain in their existing
  clinical/admission domains. The Patient Story does not become a new
  data authority.

**Pass:** The screen is an evidence-linked summary and clearly identifies
stale/saved intelligence.

**Fail:** The screen creates new authoritative data, hides provenance, or
implies automated eligibility/certification.

---

# Screen 2. Evidence & Intake

**Purpose**
- **[DESIGN REQUIREMENT]** Consolidate admission evidence and intake
  verification needed before clinical synthesis.

**Always visible**
- **[REPOSITORY-DISCOVERED]** Demographics, vitals, referral information,
  admission context, living situation, and records/evidence status
  available to the workflow.

**Conditionally visible**
- **[DESIGN REQUIREMENT]** Missing-source alerts and source-specific
  detail appear only when applicable.

**AI content**
- **[REPOSITORY-DISCOVERED]** Evidence harvesting and missing-evidence
  output may be surfaced with source provenance.

**Compliance content**
- **[REGULATORY / CLINICAL AUTHORITY]** Initial/comprehensive assessment
  findings must support individualized planning and be retained in the
  clinical record.
- **[REPOSITORY-DISCOVERED]** `referrals.reviewed` is a server-readiness
  requirement.

**Required actions**
- **[DESIGN REQUIREMENT]** Review intake evidence and resolve missing
  required intake/referral documentation.

**Completion criteria**
- All configured required intake fields and referral-review requirements
  are satisfied; unresolved missing evidence remains visible.

**Do not show**
- Lock/signature controls or unsupported billing/eligibility
  determinations.

**Do not touch**
- Admission scoping, prefill provenance, referral review, and source
  evidence.

**Pass:** Required data and evidence status are explicit.
**Fail:** Missing intake evidence is hidden or inferred as complete.

---

# Screen 3. Functional Status

**Purpose**
- **[DESIGN REQUIREMENT]** Document functional status and disease-
  relevant performance scales without presenting irrelevant scales.

**Always visible**
- **[LOCKED PRODUCT DECISION]** PPS and KPS.

**Conditionally visible**
- **[LOCKED PRODUCT DECISION]** FAST, ECOG, and NYHA only under their
  authorized diagnosis conditions.

**AI content**
- **[DESIGN REQUIREMENT]** Show functional decline evidence and missing-
  status prompts only when supported by current data or validation.

**Compliance content**
- **[REPOSITORY-DISCOVERED]** PPS/KPS warning and HOPE M1190 association
  remain wired.
- **[REGULATORY / CLINICAL AUTHORITY]** Functional status is supporting
  evidence, not an automatic eligibility result.

**Required actions / Completion criteria**
- Complete PPS and KPS; complete any diagnosis-applicable scale; provide
  required justification where configured.

**Do not show**
- Disabled, placeholder, "N/A," or irrelevant scales.

**Do not touch**
- Field keys, score semantics, structured-finding mappings, and HOPE
  mapping.

**Pass:** Only relevant scales render and values persist correctly.
**Fail:** Irrelevant scales render or hidden scales are represented as
disabled.

---

# Screen 4. Pain & Symptom Burden

**Purpose**
- **[REPOSITORY-DISCOVERED]** Combine Pain Assessment and Symptom Impact
  while preserving HOPE items and existing derivation behavior.

**Always visible**
- Pain screening, current burden, pain tool/mode, neuropathic pain, and
  J2051 symptom-impact summary.

**Conditionally visible**
- PAINAD/FLACC/verbal detail according to current assessment mode;
  advanced detail only when applicable.

**AI content**
- **[REPOSITORY-DISCOVERED]** Pain threshold findings/recommendations and
  missing evidence from the Intelligence output.

**Compliance content**
- **[REPOSITORY-DISCOVERED]** J0900, J0915, and J2051 mappings and
  validation remain visible.

**Required actions / Completion criteria**
- Complete hard-required pain fields and review all applicable symptom-
  impact items.

**Do not show**
- Derived values as if independently clinician-entered; technical engine
  details as primary workflow copy.

**Do not touch**
- Blank-only auto-derivation. It must never overwrite a manual entry.

**Pass:** Manual values remain authoritative and HOPE gaps are actionable.
**Fail:** Derived values overwrite clinical input or required mappings
disappear.

---

# Screen 5. Diagnosis & LCD

**Purpose**
- Document terminal diagnosis, related diagnoses/comorbidities, prognosis
  evidence, and LCD support.

**Always visible**
- **[REPOSITORY-DISCOVERED]** Primary diagnosis, secondary diagnoses,
  comorbidities, HOPE diagnosis category, terminal prognosis, LCD
  supporting evidence, and LCD eligibility narrative.

**Conditionally visible**
- **[REPOSITORY-DISCOVERED]** Disease-specific LCD guidance after
  diagnosis detection.
- **[LOCKED PRODUCT DECISION]** Disease Trajectory, RN Addendum, and
  Clinician Clarification require approved clinical definition before
  being revived as live controls.

**AI content**
- **[REPOSITORY-DISCOVERED]** LCD detect/config/evaluate chain and
  diagnosis-related intelligence inputs.

**Compliance content**
- LCD evidence must support individualized documentation and must not be
  presented as a conclusive automated eligibility decision.

**Required actions / Completion criteria**
- Complete required diagnosis/HOPE fields and the LCD narrative; resolve
  visible validation issues.

**Do not show**
- **[LOCKED PRODUCT DECISION]** Any Clinical Narrative in Diagnosis.

**Do not touch**
- LCD narrative, diagnosis authority, field paths consumed by
  HOPE/validation/POC/Intelligence.

**Pass:** Diagnosis and evidence are traceable; no duplicate narrative
exists.
**Fail:** Diagnosis contains a Clinical Narrative or LCD output is framed
as physician certification.

---

# Screen 6. Body Systems

**Purpose**
- **[REPOSITORY-DISCOVERED]** Preserve all ten body-system assessment
  domains while reducing navigation burden.

**Always visible**
- Access to Neurological, Cardiovascular, Respiratory, Infection,
  Gastrointestinal, Nutrition, Endocrine, Genitourinary, Musculoskeletal,
  and Skin/Wounds.

**Conditionally visible**
- Detail cards, repeatable wounds, oxygen/ventilator details,
  catheter/feeding/ostomy details, and other dependent controls only when
  applicable.

**AI content**
- Show structured findings and Intelligence findings only for supported
  inputs; do not imply all systems feed Intelligence.

**Compliance content**
- Preserve HOPE-coded neurological and skin/performance mappings and all
  safety-relevant warnings.

**Required actions / Completion criteria**
- Applicable systems are reviewed; required/warning states remain
  visible; "not assessed" must not be silently treated as normal.

**Do not show**
- Large empty irrelevant subsections by default.

**Do not touch**
- Paths consumed by Intelligence, structured findings, Symptom Impact
  derivation, and HOPE mappings.

**Pass:** Every existing system remains reachable and clinically
significant findings stay visible.
**Fail:** Collapsing removes data access or suppresses warnings.

---

# Screen 7. Caregiver & Support

**Purpose**
- Group caregiver capability, living support, psychosocial, spiritual,
  personal-care, and teaching-needs content around care feasibility.

**Always visible**
- **[REPOSITORY-DISCOVERED]** Caregiver assessed/no-caregiver state,
  willingness, medication capability, availability/support, concerns, and
  evaluation fields.

**Conditionally visible**
- No-caregiver reason, detailed caregiver evaluation, referrals,
  teaching, spiritual, and personal-care detail when applicable.

**AI content**
- **[REPOSITORY-DISCOVERED]** Existing caregiver-adjacent recommendation
  text may be labeled as a recommendation.
- **[NOT BUILT / NOT CONNECTED]** No dedicated caregiver intelligence or
  caregiver-assessment backend integration may be claimed.

**Compliance content**
- Preserve caregiver and support documentation needed to plan safe care.

**Required actions / Completion criteria**
- Record caregiver availability/capability or the no-caregiver condition
  and required reason; keep unresolved support concerns visible.

**Do not show**
- A fabricated caregiver risk score.

**Do not touch**
- Existing caregiver field paths and conditional no-caregiver logic.

**Pass:** Support capability and gaps are explicit.
**Fail:** Missing caregiver support is presented as adequate or a
nonexistent score is shown.

---

# Screen 8. Safety & Clinical Risk

**Purpose**
- Surface immediate clinical/safety risks and connect each risk to its
  source evidence.

**Always visible**
- **[REPOSITORY-DISCOVERED]** Fall risk, oxygen safety, home/disaster
  safety, imminent-death screening, psychosocial concerns, and relevant
  mobility/cognitive findings.

**Conditionally visible**
- Disaster detail, suicide-concern documentation, imminent-death
  indicators, and escalation content only when triggered.

**AI content**
- **[REPOSITORY-DISCOVERED]** Pain, oxygen, fall, delirium, imminent-
  death, mobility, and psychosocial threshold findings.

**Compliance content**
- Preserve suicide-concern note warning and all source evidence.

**Required actions / Completion criteria**
- Review triggered risks, complete associated documentation, and retain
  unresolved risks as visible actions.

**Do not show**
- A formal numeric clinical risk score; discovery found threshold
  findings, not a scoring engine.

**Do not touch**
- `fallRiskLevel`, `oxygenInUse`, mobility, neurological, psychosocial,
  and imminent-death input paths used by Intelligence or warning logic.

**Pass:** Risks show source, severity/priority when provided, and next
documentation action.
**Fail:** Advisory findings are represented as diagnoses or source
evidence is hidden.

---

# Screen 9. ACP & Goals of Care

**Purpose**
- Make treatment preferences and advance-care-planning requirements
  independently visible rather than buried under Demographics.

**Always visible**
- CPR preference asked status, code status, life-sustaining-treatment
  asked status/preference, hospitalization asked status/preference,
  decision maker, directive/POLST status.

**Conditionally visible**
- Date, decision-maker, POA, directive, and document detail when
  applicable.

**AI content**
- Missing required ACP documentation only. No separate ACP AI engine is
  claimed.

**Compliance content**
- **[REPOSITORY-DISCOVERED]** Preserve the six hard-required ACP fields
  and associated HOPE mappings.

**Required actions / Completion criteria**
- Complete the six hard-required ACP values and applicable supporting
  detail.

**Do not show**
- ACP as a nested, easy-to-miss demographic substep; a claimed goals-of-
  care engine.

**Do not touch**
- Field keys, hard-error validation, and HOPE code mappings.

**Pass:** Required ACP status is visible before Finalization.
**Fail:** ACP can remain hidden until lock failure.

---

# Screen 10. Orders & POC

**Purpose**
- Convert assessed needs into explicit orders, goals, interventions,
  disciplines, and plan-of-care readiness while preserving user-triggered
  behavior.

**Always visible**
- Admissions Order content, POC completeness, goals, interventions,
  discipline coverage, and explicit RNICA-to-POC actions that currently
  exist.

**Conditionally visible**
- CHHA/HHA requirements, order-from-suggestion action, and discipline-
  specific detail when applicable.

**AI content**
- Existing recommendations may support an explicit user action;
  recommendations must not automatically create orders.

**Compliance content**
- **[REPOSITORY-DISCOVERED]** POC completeness and conditional CHHA POC
  checks remain visible before Finalization.
- **[REGULATORY / CLINICAL AUTHORITY]** The individualized POC is based on
  assessment findings and includes goals/outcomes, services/frequency,
  symptoms, pain management, safety, supplies/equipment, treatments/
  orders, and patient limitations/needs.

**Required actions / Completion criteria**
- Complete required admission-order items, goals/interventions/discipline
  coverage, and conditional CHHA POC requirements.

**Do not show**
- Automatic order creation or automatic POC mutation.

**Do not touch**
- POC adapter calls, rule-key deduplication, explicit-action requirement,
  and readiness checks.

**Pass:** The nurse sees exactly what blocks POC readiness and explicitly
initiates mutations.
**Fail:** Recommendations silently create clinical orders.

---

# Screen 11. Compliance & Readiness

**Purpose**
- Present one actionable view of validation, HOPE, evidence gaps,
  referrals, POC, and readiness before Finalization.

**Always visible**
- Client errors/warnings, server-required fields, finalization readiness
  checks, HOPE status/gaps, referral review, POC completeness, CHHA
  readiness, and source navigation.

**Conditionally visible**
- Only applicable checks and workflow actions; passed checks may collapse
  but remain reviewable.

**AI content**
- Missing evidence and recommendations are advisory and visually
  separated from hard blockers.

**Compliance content**
- Every enforced blocker must be represented; no truncation or
  suppression.

**Required actions / Completion criteria**
- Resolve hard blockers; warnings remain visible with their actual
  severity; readiness mirrors server truth.

**Do not show**
- RNICA Billing Readiness, CTI, F2F, Survey Readiness, or dedicated
  QA/QAPI status as working integrations.

**Do not touch**
- Validation field set, finalization check conditions, HOPE lifecycle
  semantics, and lock-time server recheck.

**Pass:** A nurse can navigate from every blocker to its source.
**Fail:** A hidden or differently worded second blocker list appears only
after Lock.

---

# Screen 12. AI Action Center

**Purpose**
- Present existing Intelligence outputs and workflow actions honestly,
  with freshness and source evidence.

**Always visible**
- Priority summary, findings, recommendations, missing evidence,
  structured-finding signals, last refresh state, and Save/refresh
  guidance.

**Conditionally visible**
- Caregiver, safety, symptom, and diagnosis recommendations only when
  returned by the existing output.

**AI content**
- This is the primary presentation of current RNICA Intelligence.

**Compliance content**
- Clearly distinguish advisory output from required validation and
  finalization blockers.

**Required actions / Completion criteria**
- No blanket acknowledgment requirement. Actions are completed only
  through their authoritative source workflow.

**Do not show**
- Live-typing status, LLM claims, Explanation Engine, formal risk score,
  Patient Story generation, billing readiness, CTI/F2F/survey
  intelligence.

**Do not touch**
- Intelligence output contract, evidence harvesting, structured findings,
  and recommendation-only safety boundary.

**Pass:** Freshness and source are explicit.
**Fail:** Stale output appears live or recommendations appear
mandatory/automated.

---

# Screen 13. Finalization

**Purpose**
- Complete the whole-chart Clinical Narrative, review readiness, attest,
  sign, lock, and access post-lock amendments/audit history.

**Always visible**
- **[LOCKED PRODUCT DECISION]** One Clinical Narrative at
  `finalization.clinicalNarrative`.
- Readiness status, signature certification, clinician signature, Lock,
  autosave/save state, amendment access, and audit/history context.

**Conditionally visible**
- HOPE actions/status, supervisor review, CHHA/POC/referral blockers,
  legacy read-only narrative provenance, and amendment workflow when
  applicable.

**AI content**
- Existing visit-recording insertion remains blank-only. Any revived
  "Build Draft from Documented Findings" behavior targets Finalization
  only and requires separate implementation authorization.

**Compliance content**
- Signature certification and clinician signature remain manual. Lock
  rechecks server readiness and writes the existing audit event.

**Required actions / Completion criteria**
- Complete the Clinical Narrative, resolve blockers, manually attest,
  sign, and successfully lock.

**Do not show**
- A second narrative, Diagnosis narrative, automatic attestation,
  automatic signature, or automatic lock.

**Do not touch**
- Canonical narrative authority, attestation, signature, Lock endpoint
  behavior, readiness recheck, amendments, mandatory denial reason, and
  audit trail.

**Pass:** Exactly one active narrative exists and successful Lock follows
server validation.
**Fail:** Duplicate narrative, bypassed readiness, auto-attestation, or
loss of amendment/audit access.

---

## 5. Figma Handoff Gate

Figma handoff is ready only when:

- every requirement has an authority label;
- every screen identifies current capability boundaries;
- protected workflows are represented;
- non-built/non-connected capabilities are not shown as operational;
- the Clinical Narrative decision is implemented exactly;
- conditional scale visibility is implemented exactly;
- advisory Intelligence is separated from compliance blockers;
- evidence provenance is visible;
- dark/light/mobile/older-nurse usability are reviewed;
- the final Anti-HospiceMD test passes;
- clinical, compliance, product, and Owner approvals are recorded.

## 6. Implementation Boundary

This document defines Figma requirements only. It does not authorize
code, APIs, schemas, migrations, production data repair, removal of
legacy fields, or implementation of future product-direction
capabilities. Approved Figma and a separate implementation plan are
required before GitHub implementation.
