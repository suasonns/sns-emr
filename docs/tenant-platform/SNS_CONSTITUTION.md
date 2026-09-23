# SNS Hospice EMR Canonical Instructions (SNS Constitution)

**Status:** Standing engineering authority document — permanent project guidance, not temporary session context.
**Governs:** RNICA, HOPE, SFV, Patient Chart, Orders, Plan of Care, Compliance, Finalization, Audit, and future redesign work.
**Supersedes:** Any prior informal session-only guidance that conflicts with this document.

---

## 1. Purpose

Guide the design, implementation, review, testing, stabilization, and governance of SNS Hospice EMR.

Translate applicable hospice requirements into:

- compliant clinical workflows
- audit-ready documentation
- role-appropriate validations
- reports and exports
- reusable templates
- survey evidence
- technical specifications
- secure and traceable software behavior

These instructions support product and engineering decisions. They do not replace:

- physician certification
- individualized clinical judgment
- professional coding review
- legal advice
- payer determinations
- accreditation decisions
- official survey findings

---

## 2. Scope

These instructions apply to SNS Hospice EMR work involving:

- admissions
- election statements
- comprehensive assessments
- RNICA
- plans of care
- interdisciplinary review
- visits
- benefit periods
- certifications and recertifications
- HOPE events
- HUV events
- SFV events
- discharge
- orders
- billing-linked workflows
- signatures
- Lock
- corrections and amendments
- reports and exports
- medical-record retention
- historical-record testing
- database work
- AI-supported workflows
- audit and survey readiness

---

## 3. Definitions

### 3.1 Controlling authority

The binding or otherwise governing source that applies to the specific:

- subject
- jurisdiction
- provider type
- payer
- accreditation context
- workflow
- event
- date of service
- submission date
- correction date
- effective period

### 3.2 Product authority

The SNS authority responsible for intentional internal product decisions such as:

- workflow sequence
- screen organization
- information architecture
- terminology
- presentation ownership
- staff workflow
- visual design
- non-regulatory product behavior

### 3.3 Repository evidence

Evidence obtained from the current repository, including:

- active authority documents
- field definitions
- components
- state paths
- API contracts
- persistence paths
- validations
- exports
- readiness logic
- audit logic
- migrations
- tests

Screenshots, conversational history, and prior summaries are not repository evidence.

### 3.4 Authoritative field owner

The single persisted and editable authority for a clinical or operational concept.

Other screens may display the same concept read-only when provenance is clear.

### 3.5 Supporting evidence

Clinical information organized to support professional review.

Supporting evidence is not an automatic determination of:

- hospice eligibility
- terminal prognosis
- certification
- diagnosis selection
- coverage
- payment

---

## 4. Authority and Applicability

When guidance overlaps, determine which source governs the specific issue rather than relying on a fixed hierarchy.

For every issue:

1. Identify the subject.
2. Identify the jurisdiction.
3. Identify the provider type.
4. Identify the payer.
5. Identify the accreditation context, if applicable.
6. Identify the workflow or event.
7. Identify the relevant effective period.
8. Determine whether each source is:
   - binding law or regulation
   - federal Condition of Participation
   - state licensing requirement
   - payer requirement
   - Medicare contractor guidance
   - accreditation standard
   - technical specification
   - SNS policy
   - product recommendation
   - legacy reference only
9. Apply each authority only within its scope.
10. Check publication dates, effective dates, implementation dates, revisions, errata, superseding notices, and correction notices.

When sources conflict:

1. Identify each competing provision.
2. State the scope of each provision.
3. Explain which authority controls the specific issue and why.
4. Preserve non-controlling material as supporting or advisory context when appropriate.
5. Flag unresolved conflicts for legal, payer, accreditor, agency, coding, clinical, or compliance review.

Do not:

- convert SNS policy into law
- convert payer guidance into law
- apply an LCD outside its jurisdiction as binding
- treat accreditation guidance as a federal regulation
- treat a legacy form as proof of a current item definition

California materials separately address electronic records, authentication, authorized access, corrections, amendments, confidentiality, audit trails, backups, and record availability. Those requirements must not be conflated with CMS HOPE submission requirements.

---

## 5. Authority Citation Standard

For every compliance or regulatory conclusion, record:

- source title
- issuing organization
- jurisdiction
- document identifier
- version or revision
- publication date
- effective date
- implementation date, if different
- verification date
- page, section, item, or paragraph
- mandatory or advisory status
- applicable provider type
- applicable payer
- applicable event or workflow
- applicability limitations
- direct quotation or faithful paraphrase
- controlling-authority conclusion

Do not state that a feature is compliant unless the controlling authority and applicability are verified.

---

## 6. Source Currency and Effective-Date Control

Before relying on any source:

1. Locate the current official version.
2. Record its version and effective date.
3. Check for later revisions.
4. Check for errata or correction notices.
5. Check for replacement item sets or specifications.
6. Confirm that the source applies to the relevant event date.
7. Confirm jurisdiction and payer applicability.

Use the authority and technical specification applicable to the:

- assessment date
- visit date
- election date
- certification date
- recertification date
- submission date
- correction date
- amendment date

Do not apply the newest specification retroactively unless the controlling authority requires retroactive application.

Historical records must remain interpretable under the specification applicable to the original event.

---

## 7. SNS Product Authority

SNS clinical product authority owns intentional decisions concerning:

- screen sequence
- workflow organization
- information architecture
- staff-facing terminology
- visual hierarchy
- presentation ownership
- user experience
- non-regulatory product behavior

Repository documents and implementation describe the currently recorded state. Historical documentation does not make a prior product decision immutable.

When product authority intentionally revises a workflow:

1. Record the decision.
2. Record the rationale.
3. Identify affected staff roles.
4. Identify superseded product documents.
5. Update controlling authority documents first.
6. Update implementation second.
7. Preserve existing clinical data unless separate data changes are authorized.
8. Preserve established clinical behavior unless the behavior change is explicitly approved.
9. Document migration and historical compatibility, if required.
10. Add acceptance tests for the revised decision.

Product authority cannot override binding external requirements.

External authority does not determine internal presentation when multiple compliant designs are available.

---

## 8. Repository-First Gate

Before recommending or making a change:

1. Record:
   - repository root
   - branch
   - commit SHA
   - worktree
   - git status
   - verification date
2. Read the repository constitution.
3. Read active workstream authority documents.
4. Inspect the current implementation.
5. Search for existing:
   - fields
   - components
   - services
   - enums
   - APIs
   - models
   - migrations
   - exports
   - validations
   - readiness logic
   - audit events
   - tests
6. Trace the complete field or behavior path.
7. Classify the finding using the approved verification statuses.
8. Confirm historical-record impact.
9. Confirm whether implementation is authorized.

Do not begin implementation when the repository-first gate is incomplete.

Do not declare a field missing based only on:

- screenshots
- conversational history
- UI absence
- prior summaries
- an incomplete search

---

## 9. Verification Statuses

Use only these statuses:

- `VERIFIED_COMPLETE`
- `PRESENT_CORRECTLY_PLACED`
- `PRESENT_MISPLACED`
- `PRESENT_RESPONSE_SET_INCOMPLETE`
- `PRESENT_NOT_HARVESTED`
- `PRESENT_NOT_WIRED`
- `DUPLICATE_OF_AUTHORITATIVE_SOURCE`
- `DUPLICATE_EDITABLE_AUTHORITY`
- `MISSING_FROM_SNS`
- `NOT_APPLICABLE`
- `NOT_FOUND_IN_REPOSITORY`
- `CONFLICTING`
- `REQUIRES_AUTHORITY_REVIEW`
- `NOT_VERIFIED`
- `BLOCKED`

A field or requirement may not be marked `VERIFIED_COMPLETE` unless all applicable evidence is verified for:

- rendering
- state
- save payload
- API
- persistence
- hydration
- validation
- conditional visibility
- requiredness
- export
- readiness
- audit
- historical compatibility
- tests

`NOT_VERIFIED` is not equivalent to optional.

`NOT_FOUND_IN_REPOSITORY` is not equivalent to missing until the search scope and inspected commit are documented.

---

## 10. General Response Standards

Guidance must be:

- concise
- survey-defensible
- implementable
- source-grounded
- scope-aware
- explicit about uncertainty

Separate:

1. confirmed requirements
2. reasonable interpretations
3. SNS policy
4. product recommendations
5. unresolved questions

When controlling guidance is unclear:

1. Identify plausible interpretations.
2. Recommend the lowest-risk interim operational approach.
3. Label the approach as provisional.
4. Identify the authority needed for a final decision.
5. Do not present the provisional approach as confirmed compliance.
6. Do not implement blocking validation based only on unresolved interpretation.

Protect credentials and sensitive operational data.

Do not substitute agent output for professional review or official determinations.

---

## 11. Historical Patient Data Testing

Historical patient data may be used only when separately authorized by the organization and when the safeguards in this section are documented.

These instructions do not grant access to patient records or authorize production testing.

The current sole developer may be designated as the sole authorized test user. Sole access does not remove privacy, confidentiality, security, audit, or minimum-necessary obligations.

### 11.1 Required authorization record

Before testing, record:

- authorization reference
- approving authority
- test purpose
- approved environment
- approved user
- access start
- access end
- minimum records
- minimum fields
- expected outcome
- rollback plan
- retention deadline
- cleanup plan
- incident-escalation path

### 11.2 Environment safeguards

Use an approved environment isolated from:

- public demonstrations
- general training
- source repositories
- issue trackers
- external AI services
- production integrations unless specifically authorized
- unrelated users
- unrelated tenants

Require:

- dedicated account
- strong authentication
- least privilege
- encryption
- audit logging
- secure backups
- restricted exports
- restricted screenshots
- restricted printing
- restricted sharing
- integration controls

### 11.3 Data handling

Preserve the clinical complexity necessary to reproduce the issue while masking unnecessary identifiers.

Do not place identifiable patient data in:

- source code
- committed fixtures
- PR descriptions
- issue trackers
- external AI prompts
- public screenshots
- ordinary logs
- general training environments
- unsecured local files

### 11.4 Test record

For each test, record:

- test-case ID
- authorization reference
- masked record reference
- record version
- fields accessed
- actions performed
- expected result
- actual result
- changes made
- rollback result
- cleanup result
- post-test verification

Do not copy unnecessary identifiers into test reports.

### 11.5 Synthetic or de-identified data

If authorization or safeguards cannot be confirmed, use de-identified or synthetic data.

When synthetic data is used:

- label the data as synthetic
- document which clinical relationships were simulated
- do not claim synthetic results prove production-record compatibility
- do not claim synthetic results prove historical-record behavior

### 11.6 Incident response

If suspected exposure, unauthorized access, cross-patient data, cross-tenant data, or improper transfer is detected:

1. Stop testing.
2. Preserve necessary evidence.
3. Avoid unnecessary identifiers in incident records.
4. Follow the SNS incident-response process.
5. Do not continue until authorized.

California materials require confidentiality, protection from unauthorized use, traceable corrections and amendments, access controls, audit trails, documented authentication, regular backups, and secure electronic-record handling.

---

## 12. Eligibility and Diagnosis Review

For eligibility, terminal diagnoses, ICD-10 selection, certification, recertification, or LCD review:

1. Identify:
   - proposed principal terminal diagnosis
   - related conditions
   - coexisting conditions
   - symptoms
2. Validate the proposed principal diagnosis against applicable code restrictions.
3. Record the source, payer, jurisdiction, version, and effective date of any:
   - never-primary list
   - inappropriate-primary list
   - not-allowable list
4. Identify the applicable disease guide.
5. Identify the controlling LCD.
6. Confirm LCD jurisdiction.
7. Confirm the LCD is active for the relevant date of service.
8. Review revision and replacement status.
9. Evaluate individualized evidence, including:
   - decline over time
   - KPS
   - PPS
   - FAST
   - applicable disease-specific scales
   - ADL dependence
   - nutrition
   - symptoms
   - complications
   - hospitalizations
   - emergency utilization
   - comorbidities
   - objective measures
   - disease-specific findings
10. For recertification, evaluate:
    - continued terminal burden
    - persistent decline
    - current function
    - new complications
    - stability
    - temporary improvement
    - whether stability or improvement is adequately explained
11. Identify missing evidence.
12. Identify contradictions.
13. Identify coding concerns.
14. Recommend documentation improvements.

LCD criteria are supporting documentation guidance, not an automatic pass/fail engine.

Diagnosis alone does not establish terminal prognosis. The medical record must support the physician's clinical judgment; baseline guidelines do not independently qualify a patient.

Disease-specific criteria must be used only for the applicable condition, paired with functional impairment, ADL dependence, and relevant comorbidities.

---

## 13. Prohibition on Automated Eligibility Determination

SNS Hospice EMR may:

- collect evidence
- organize evidence
- display evidence
- validate documentation
- identify missing documentation
- link source records
- present advisory guidance
- support clinician review

SNS Hospice EMR must not independently:

- certify terminal prognosis
- determine final hospice eligibility
- replace physician judgment
- convert an LCD checklist into a guaranteed outcome
- choose the final principal terminal diagnosis without authorized review
- represent coverage as certain
- sign certification
- issue legal or survey conclusions

Computed output must be labeled:

- supporting evidence
- advisory guidance
- documentation gap
- clinician review required

unless a verified controlling authority explicitly permits a different designation.

---

## 14. HOPE, HQRP, iQIES, QIES, HUV, and SFV

Use current official CMS materials for:

- definitions
- event applicability
- timing
- item codes
- response sets
- skip patterns
- record requirements
- process measures
- submission rules
- correction rules
- technical specifications

For each item, document:

- applicable assessment or event
- applicable patient state
- item-set version
- item code
- official definition
- response set
- null, unknown, dash, skip, or not-assessed values
- conditional visibility
- requiredness
- collection timestamp
- event timestamp
- trigger state
- due state
- completed state
- submission state
- correction behavior
- export transformation
- rejection handling
- resubmission behavior
- readiness impact
- audit event
- historical-version behavior

Distinguish:

- collected
- validated
- triggered
- due
- completed
- exported
- submitted
- accepted
- rejected
- corrected
- resubmitted

An SFV trigger does not prove an SFV is due.

An SFV due state does not prove completion.

Completion does not prove submission.

Submission does not prove acceptance.

Do not infer one state from another without verified authority and implementation evidence.

---

## 15. Compliance Translation

Translate verified requirements into EMR behavior.

For each translated requirement, record:

- requirement ID
- source authority
- exact citation
- jurisdiction
- payer
- provider type
- event or workflow
- effective date
- mandatory or advisory status
- applicable roles
- data owner
- persisted field
- editable screen
- read-only displays
- controlled values
- requiredness
- timing
- validation
- warning or blocker behavior
- escalation
- signatures
- timestamps
- linked evidence
- audit event
- export or report
- correction behavior
- historical behavior
- acceptance tests

Do not convert a recommendation into a blocker unless the controlling authority requires blocking behavior or SNS product authority explicitly approves the operational control.

---

## 16. Staff-Support Priority

Prioritize recommendations in this order:

1. patient safety
2. binding legal, regulatory, and payer requirements
3. frontline staff support and workload reduction
4. data integrity and auditability
5. accessibility
6. implementation effort
7. measurable operational benefit

When multiple compliant options exist, prefer the option that:

- reduces duplicate entry
- reduces avoidable errors
- clarifies ownership
- provides guidance at the point of work
- preserves clinical judgment
- minimizes retraining
- routes users directly to correctable blockers

For each recommendation, identify:

- affected roles
- current burden
- expected support benefit
- error-prevention benefit
- accessibility impact
- adoption risk
- training requirement
- measurable success indicator

Do not move fields solely for visual neatness.

---

## 17. Checklist and Template Governance

Templates must include:

- title
- purpose
- owner
- version
- effective date
- last verified date
- jurisdiction
- payer scope
- provider scope
- source authorities
- mandatory/advisory markings
- superseded version
- review cadence

Use:

- clear headings
- checkboxes
- fill-in fields
- brief action statements
- explicit ownership
- explicit escalation

Separate:

- required documentation
- clinical actions
- communications
- diagnosis validation
- eligibility support
- orders
- signatures
- evidence
- corrections
- escalation

Do not merge requirements from different payers, jurisdictions, accreditors, or effective periods without labeling each scope.

---

## 18. Engineering Guardrails

Separate:

- UI presentation
- application behavior
- validation
- database queries
- persistence
- schema
- migration
- exporter logic
- compliance logic
- readiness logic
- audit logic

Before schema work:

1. Verify the live database state through an approved method.
2. Confirm the current model.
3. Confirm the migration chain.
4. Prove the existing schema cannot safely support the requirement.
5. Assess backward compatibility.
6. Assess historical-record compatibility.
7. Document rollback or recovery.

Use forward-only revisions.

Do not rewrite applied migration history.

Avoid duplicate enums.

Reuse existing fields and components when safe.

Prefer the smallest safe change with a specific verification step.

Keep visit types, plan-of-care logic, benefit periods, evidence links, timestamps, status values, signatures, corrections, amendments, Lock behavior, and audit events consistent across:

- frontend
- API
- persistence
- reports
- exports
- historical records

---

## 19. Data Ownership

Every clinical or operational concept must have:

- one authoritative persisted path
- one editable UI owner
- defined read-only displays
- one validation authority
- one calculation authority, when computed
- one export transformation authority
- one readiness interpretation
- one audit model

Do not create duplicate editable authorities.

Do not duplicate persisted data merely to move presentation.

Presentation ownership may change while persisted ownership remains stable.

Assessment findings must remain distinct from orders.

Referral needs must remain distinct from orders.

Read-only summaries must show provenance.

---

## 20. Full Field Trace

Before declaring a field complete, trace:

```text
UI definition
→ rendering component
→ form state
→ save payload
→ API contract
→ persistence
→ load/hydration
→ validation
→ export
→ readiness
→ audit
→ tests
```

Every link in the chain must be independently verified with file:line repository evidence before the field may be marked `VERIFIED_COMPLETE`.

---

## 21. Location and Precedence

This document lives at `docs/tenant-platform/SNS_CONSTITUTION.md`.

If another active constitution-level document exists in this repository, compare the two before acting, preserve the stronger/more specific version, and do not create competing governance documents. As of the date this file was created, no other file in `docs/tenant-platform/` matched `CONSTITUTION` or "Canonical Instructions" — this is the sole standing constitution.

This is not temporary session context. This is permanent project guidance governing RNICA, HOPE, SFV, Patient Chart, Orders, Plan of Care, Compliance, Finalization, Audit, and future redesign work.

---

## 22. Repository-First Rule (Restated)

Before ANY future implementation, the assistant must:

1. Read `SNS_CONSTITUTION.md`.
2. Perform a repository refresh (branch, commit SHA, `git status`).
3. Read active authority documents.
4. Read active workstream documents.
5. Inspect current implementation.
6. Inspect current tests.
7. Inspect current routes and APIs.

before making recommendations. Do not rely on previous conversation memory or previous session memory. Repository evidence is authoritative.

---

## 23. Mandatory Session Start Template

At the start of every future RNICA session, output:

```
SESSION REFRESH COMPLETE

Branch:
Commit SHA:
Current checkpoint:
Current screen:
Last completed screen:
Next screen:

Authority documents reviewed:

Repository files reviewed:

Open defects:

Closed defects:

Blocked items:

Implementation allowed:
YES / NO
```

No RNICA work begins until this template is completed.

---

## 24. RNICA Authority Updates — Approved Workflow Order

⚠️ **Discrepancy flag (repository-first gate):** The order below, as supplied in the source directive for this section, lists **"1. Evidence & Intake, 2. Patient Story."** This conflicts with the prior explicit "FINAL RNICA WORKFLOW PRODUCT DECISION" issued earlier in this same session, which stated **"1. Patient Story, 2. Evidence & Intake"** (with only screens 3–4 order corrected afterward, Patient Story/Evidence & Intake order was never revisited). Per Section 7, a product-authority revision must be an intentional, recorded decision — not an unnoticed inversion. This document records the order **exactly as supplied** below, but implementation must not swap screens 1 and 2 until the user confirms which order is actually intended.

Current approved order (as supplied for this constitution):

1. Evidence & Intake
2. Patient Story
3. Pain & Symptom Burden
4. Diagnosis & LCD
5. Functional Status
6. Body Systems
7. Caregiver & Support
8. Safety & Clinical Risk
9. ACP & Goals of Care
10. Orders & POC
11. Compliance & Readiness
12. AI Action Center
13. Finalization

This supersedes historical workflow sequences, subject to the discrepancy above being resolved before implementation.

---

## 25. ADL Ownership

ADLs belong to Functional Status (presentation ownership).

Preserve existing field paths. Move presentation ownership only — do not create duplicate editable ADLs.

Body Systems retains musculoskeletal findings.

---

## 26. RNICA Workflow Navigation

The horizontal workflow strip is not the final design.

- **Desktop:** dedicated vertical RNICA workflow rail.
- **Mobile:** workflow drawer/sheet.

Patient Chart navigation and RNICA workflow navigation are separate systems.

---

## 27. HOPE / SFV Screenshot Classification Rule

- Blue screenshot labels: potential HOPE items.
- Red screenshot labels: potential SFV items.

Classification requires repository verification before implementation. Screenshots are not authority by themselves.

---

## 28. Field Verification Rule (Restated)

No field may be marked `VERIFIED_COMPLETE` without UI, State, Payload, API, Persistence, Validation, Export, Readiness, Audit, Historical compatibility, and Tests all being verified.

---

## 29. Release Gate

Do not implement changes when:

- field is `NOT_VERIFIED`
- exporter unknown
- trigger unknown
- duplicate authority exists
- historical compatibility untested
- a release blocker exists

---

## 31. SFV Completion Visit Rule

**Product authority decision.**

**What is required:** the SFV completion event must occur in a different
visit record than the visit that generated the SFV trigger:

```
triggerVisitId != completionVisitId
```

The triggering assessment visit and the completion visit must be separate
documented encounters.

**What is allowed:** same nurse — allowed. Same RN — allowed. Same LVN —
allowed. Same discipline — allowed. Same patient — allowed (a patient
necessarily has both visits). Same day — allowed if timing rules permit.
Within 48 hours — allowed. An SFV completion may be performed by either RN
or LVN, and the completing clinician may be the same clinician who
performed the triggering RNICA assessment.

The requirement is **different visit instance**, not different clinician
and not different discipline. Clinician identity is not a completion
requirement; visit identity is the completion requirement.

**What fails:** a visit that satisfies both the trigger condition and the
completion condition inside the same visit record.

**Repository verification (independent re-trace, `16264cf`):**
`complete_sfv_requirement_from_visit` (`hope_phase_b_engine.py:397-438`)
already enforces exactly this rule at `:425-426` via a string comparison
of `completing_visit_id` against `requirement.trigger_reference_id`, with
no comparison against clinician/user identity or discipline beyond an
independent RN/LPN/LVN discipline gate. **Backend enforcement already
matches this decision; no backend behavior change was authorized or made.**
Full evidence: `SFV_LIFECYCLE_TRACE_MATRIX.md` §5.

**Gap closed (later pass):** the frontend's self-attested
`sfv.inPersonSfvCompleted` checkbox on the triggering RN ICA form never
called `complete_sfv_requirement_from_visit`. It has since been removed
entirely; see the completion-endpoint and frontend-placement updates
later in this section.

**Tests:** `backend/tests/test_sfv_completion_visit_separation.py`
(8 scenarios, passing) — see `RNICA_ACCEPTANCE_TEST_MATRIX.md` §2b for the
corrected exit-code evidence (initial "Blocked" status was a shell
stderr-artifact, not a real failure).

## SFV Separate-Visit and Clinician Rule (product authority, refined)

An SFV completion must be documented in a separate visit record from the
visit that generated the SFV requirement. The controlling invariant is:

```
triggerVisitId != completionVisitId
```

The completing clinician must hold a **qualifying nursing credential**:
Staff RN, on-call/covering/per-diem RN (this repository has no distinct
on-call/covering/per-diem role string — any RN-role account qualifies
regardless of shift status), LVN/LPN (including on-call/covering/
per-diem), or a Nurse Practitioner functioning under RN licensure for
this purpose. The completing clinician does not need to match the
clinician who performed the triggering RNICA assessment, and does not
need to be the originally assigned nurse. **"Appropriately authorized
clinician" does NOT mean any user with patient access, and does NOT mean
any clinician role.** Social Worker, Chaplain, Bereavement/Volunteer
Coordinator, administrative users (Administrator/DPCS/DPCS
Administrator), and Physician Assistant/physician roles are explicitly
**excluded** from SFV completion even when they otherwise have chart
access to the patient — general chart access is insufficient.

The completing clinician must always be an active employee of the same
tenant/agency as the patient — cross-tenant completion is never permitted.
The original triggering visit and the completion visit retain independent
authorship, authentication, timestamps, and audit history. Assignment does
not equal completion. Visit start does not equal completion. Completion
does not equal export. Export does not equal submission. Submission does
not equal acceptance. The server is the authoritative enforcement layer;
the frontend must present the same result and must not allow same-visit
self-attestation.

**Repository verification (this pass):** `get_authorized_patient`
(`backend/app/core/patient_access.py:61`) already enforces tenant
isolation (`Patient.tenant_id == caller.tenant_id`) and active-user status
for every caller of the visit-finalize endpoints that lead to
`_maybe_complete_open_sfv_for_visit` (`backend/app/api/visits.py:3868`).
Because that hook only runs inside an already-tenant/patient-authorized
visit-finalize request, cross-tenant and cross-patient SFV completion is
already structurally prevented today — **verified, not a gap.**

**Confirmed gap, now closed (this pass):** a dedicated SFV completion API
endpoint now exists —
`POST /visits/sfv-requirements/{sfvRequirementId}/complete`
(`backend/app/api/visits.py`), authorized via
`app.core.patient_access.can_complete_sfv`. **Corrected (2026-09-23, "SFV
AUTHORIZATION CORRECTION"):** `can_complete_sfv` no longer reuses the
RN-scope `PERFORM_RN_ASSESSMENT`/`FINALIZE_RN_DOCUMENTATION` capabilities
(those are also granted to ADMINISTRATOR/DPCS/DPCS_ADMINISTRATOR and to
physician-tier roles including PA, which are explicitly excluded from SFV
completion). It instead checks the caller's normalized role directly
against a dedicated qualifying-nursing-credential roster:

- **AUTHORIZED SFV COMPLETER ROLES:** `RN`, `LVN` (alias `LPN`), `NP`
  (Nurse Practitioner, functioning under RN licensure for this purpose),
  `CASE_MANAGER` (documented in `app.core.capabilities` as an RN-scope,
  assignment-scoped nursing role in this repository — an RN Case
  Manager, not a social-work case manager).
- **EXCLUDED NON-NURSING ROLES:** `SW` (Social Worker), `CHAPLAIN`,
  `VOLUNTEER_COORDINATOR` (this repository's closest existing role to
  Bereavement Coordinator/Volunteer), `CHHA`, `ADMINISTRATOR`, `DPCS`,
  `DPCS_ADMINISTRATOR` (administrative users), `PA` (Physician
  Assistant), `MD`/`DO`/`MEDICAL_DIRECTOR`/`ATTENDING_PHYSICIAN`/
  `HOSPICE_PHYSICIAN` (physicians), `CLINICAL_SUPERVISOR`, all
  QA/compliance roles, and every billing/intake/scheduling/platform role.

The endpoint also has structured JSON error codes, row-level locking for
concurrency (verified with a real two-thread race test, not merely
asserted), and idempotent replay against an already-`COMPLETED`
requirement. A companion read-only
`GET /visits/sfv-requirements?patientId=...` backs the frontend status
displays. No schema migration, no new lifecycle engine, and no new
on-call/permissions/audit subsystem were built — the existing
`SFVRequirement`/`Visit` models and `complete_sfv_requirement_from_visit`
service function are reused as-is. See
`docs/tenant-platform/SFV_FRONTEND_BACKEND_PARITY_MATRIX.md` for the
updated per-scenario evidence.

**Cross-cutting note (discovered, not an SFV defect):** `NP` and `PA` are
also "provider identity" roles under the platform's separate Physician
Identity Mapping gate (`app.services.physician_identity_service`) — an
NP/PA account gets zero patient visibility at all, for any purpose, until
its user record has a verified, `ACTIVE` `physician_id` linkage. This is
an existing, independent safety gate unrelated to SFV completion
authorization; it does not need to be duplicated by `can_complete_sfv`,
but it does mean a real-world NP cannot complete an SFV (or do anything
else patient-related) until that identity verification step has been
completed by an administrator.

**Known gap, now closed (this pass):** the self-attested
`sfv.inPersonSfvCompleted` checkbox and `sfvDate` field on the triggering
RN ICA form have been **removed** from `RNICA.jsx` (they never called the
backend completion path). The triggering screen now shows a read-only
`SfvStatusCard` (current follow-up status + a link to Visit Notes) and
offers no completion action. The authoritative "Complete SFV" action now
lives on the **separate qualifying follow-up visit** — a new
`SymptomFollowUpVisitSection` on the Visit Notes screen
(`sns-emr-frontend/src/components/VisitNotes.jsx`), gated on that visit
being finalized (signed/submitted) before the completion action is
offered, calling the new endpoint via the single client function
`completeSfvRequirement` (`sns-emr-frontend/src/api/sfv.ts`).

**Remaining open items (explicitly not built this pass, per product
direction to avoid over-engineering):** a formal on-call
scheduling/assignment subsystem (existing tenant/patient-access/capability
checks are reused instead); a richer multi-state SFV lifecycle beyond the
existing 4-value `status` column; a full browser-automated end-to-end
test suite (only backend API-level and frontend component-level tests
exist so far). A pre-existing, out-of-scope gap was also discovered and
documented (not fixed): `app.core.capabilities.ROLE_CAPABILITIES` has no
`LVN` entry, so `can_complete_sfv` falls back to an explicit
normalized-role check for RN/LVN to match the service layer's existing
discipline rule — fixing the capability roster itself would affect many
other endpoints and is outside SFV remediation scope.

---

## 30. Current Phase

After saving this constitution, return to `RNICA_HOPE_SFV_FIELD_PLACEMENT_MAP.md` and continue evidence verification.

Do not resume UI redesign until the field-placement audit, HOPE verification, SFV verification, and duplicate-ownership review are complete.
