# Patient Chart Workflow Authority

Companion document to `PATIENT_CHART_AUTHORITY_MAP.md` (current-state
ownership/dependency documentation) and the RNICA authority family
(`RNICA_REDESIGN_SOURCE_OF_TRUTH.md`,
`RNICA_SCREEN_BY_SCREEN_EVIDENCE_MATRIX.md`,
`RNICA_WORKFLOW_AUTHORITY_MAP.md`). This document is the **future
workflow authority** for the Patient Chart as a whole: it defines the
10 workflow phases a clinician moves through, what each phase owns
versus surfaces, and how each phase relates to the 20 existing
workspaces documented in `PATIENT_CHART_AUTHORITY_MAP.md`.

STATUS: FUTURE WORKFLOW AUTHORITY. NOT IMPLEMENTATION AUTHORIZATION.
CODE: BLOCKED
SCHEMA: BLOCKED
MIGRATIONS: BLOCKED
UX/IA DESIGN: NOT PERFORMED BY THIS DOCUMENT

`PATIENT_CHART_AUTHORITY_MAP.md` is not reopened by this document. Per
its own Scope Clarification, it documents current ownership and does not
dictate future navigation — this document is the future-navigation
counterpart it anticipated, and it must not contradict any authority,
producer/consumer relationship, or compliance boundary recorded there.

## Relationship to the three-layer navigation model

Per the approved architectural correction, the clinician workflow spans
three navigation layers:
1. **Patient Chart Navigation** — this document.
2. **RNICA Navigation** — `RNICA_WORKFLOW_AUTHORITY_MAP.md` (13 screens).
   "Assess" (phase 3, below) is the Patient Chart's entry point into that
   13-screen workflow; this document does not redefine RNICA's internal
   screens.
3. **Right Rail** — Errors/Warnings/HOPE/RNICA Intelligence/Structured
   Findings today; Compliance & Readiness and AI Action Center are future
   authority. This document treats the right rail as cross-phase and
   does not assign it to any single phase.

## Authority legend (same set used throughout this doc family)

- **[LOCKED PRODUCT DECISION]** Approved future-state decision (this
  document's own workflow-phase/ownership rules).
- **[REPOSITORY-DISCOVERED]** Reference to a proven current
  module/route/API, cited from `PATIENT_CHART_AUTHORITY_MAP.md` or
  fresh discovery (this document does not re-verify those citations;
  see `PATIENT_CHART_CURRENT_STATE_MAPPING.md` for that).
- **[FUTURE PRODUCT DIRECTION]** Desired capability not yet current
  functionality.
- **[NOT YET MAPPED]** Relationship between a phase and a current
  workspace that has not yet been confirmed — carried to the current
  state mapping / gap analysis documents for resolution, not assumed
  here.

## Governing principle: workflow-first, ownership-preserving

**[LOCKED PRODUCT DECISION]** The Patient Chart redesign changes how a
clinician *experiences* the chart. It does not change *who owns, produces,
or is authorized to modify* any data. Every phase below is defined by
what it **owns** (if anything) versus what it **surfaces, aggregates, or
routes to** from the workspaces that already own that data per
`PATIENT_CHART_AUTHORITY_MAP.md`. A phase that surfaces data it does not
own must not present itself as, or become, a second authority for that
data.

## Workflow phases

### 1. Patient Story
- **[LOCKED PRODUCT DECISION]** Owns nothing. Presentation layer only.
- **Purpose:** narrative-style entry point summarizing who the patient
  is — diagnosis, decline evidence, caregiver context, recent
  Intelligence findings — before the clinician acts.
- **Source workspaces (surfaced, not owned):** Facesheet, Clinical
  Assessments (RNICA), Compliance & HOPE, RNICA Intelligence.
- **Consistent with:** RNICA's own Screen 1 ("Patient Story"), which is
  also explicitly non-authoritative
  (`RNICA_REDESIGN_SOURCE_OF_TRUTH.md`). The Patient Chart phase and the
  RNICA screen share the same non-ownership rule; they are not the same
  artifact and must not be conflated into one component that silently
  becomes a second data path.

### 2. Know the Patient
- **[LOCKED PRODUCT DECISION]** Owns nothing. Aggregation/reference layer.
- **Purpose:** identity, insurance, level of care, physicians, care team,
  contacts, allergies, admission/intake status — the reference facts a
  clinician needs before assessing or documenting.
- **Source workspaces (surfaced, not owned):** Facesheet, Care Overview,
  Intake & Admission, Care Team.
- **Boundary:** must not duplicate or allow independent edits to
  Facesheet identity/insurance/diagnosis data; edits route back to
  Facesheet as sole owner.

### 3. Assess
- **[LOCKED PRODUCT DECISION]** Authority remains RNICA. This phase does
  not own assessment data itself — it is the entry point into the RNICA
  13-screen workflow, which retains its own authority package in full.
- **Purpose:** route the clinician into RNICA for admission and
  recertification clinical assessment.
- **Source workspace:** Clinical Assessments (RNICA + Nursing/Spiritual/
  Psychosocial + History).
- **Boundary:** this document does not redefine, reopen, or duplicate any
  RNICA screen, field, validation rule, or authority already established
  in the RNICA documentation family. Non-RNICA assessment types (Nursing/
  Spiritual/Psychosocial/History) are addressed by their own current
  ownership in `PATIENT_CHART_AUTHORITY_MAP.md` and are not redefined
  here.

### 4. Document Visit
- **[LOCKED PRODUCT DECISION]** Owns visit documentation.
- **Purpose:** create and manage visit notes (nursing, HHA, volunteer,
  bereavement, physician) as the record of a specific clinical encounter.
- **Source workspaces:** Visit Notes, Home Health Aide/CHHA (visit/notes
  portion), Volunteer Services (visit portion), Bereavement (visit
  portion), Physician Orders (F2F visit notes portion).
- **Boundary:** owns the visit-note record itself; does not own orders
  (Manage Treatment), POC (Plan Care), or the Final Clinical Narrative
  (RNICA Finalization, unchanged).
- **[LOCKED PRODUCT DECISION] Record integrity:** every completed visit
  note must retain: author identity; professional credentials where
  applicable; service date and time; entry date and time; authentication
  status; amendment or correction history; and a link to the applicable
  patient and visit. Restates the existing medical-record authentication/
  traceability requirement already locked for RNICA amendments
  (`RNICA_LOCK_READINESS_MATRIX.md`) for the Document Visit phase.

### 5. Manage Treatment
- **[LOCKED PRODUCT DECISION]** Manage Treatment is a workflow layer, not
  a record owner. Medication records remain owned by the Medication
  domain; physician-order records remain owned by the Physician Orders
  domain; DME records remain owned by the DME domain. This phase must not
  be read as owning "Treatment/medication/DME workflow" in a sense that
  implies record ownership — it owns only the workflow-state actions it
  initiates (e.g., a draft request), never the underlying clinical
  record.
- **Purpose:** medication administration, DME tracking, and treatment
  workflow management surfaced against records that remain owned
  elsewhere (Medication domain, DME domain, Physician Orders domain).
- **Source workspaces:** Tx / Meds / DME (workflow layer only — record
  ownership remains with the Medication and DME domains), Physician
  Orders (surfaced/read, not owned — CTI/F2F/order authority remains
  with Physician Orders per `PATIENT_CHART_AUTHORITY_MAP.md`).
- **Boundary:** may create a **draft** request and initiate treatment
  workflow actions but must not issue, approve, or sign a physician
  order, and must not use language implying that a nurse or this
  workflow layer issues, approves, or signs a physician order. Any
  action affecting an order must route to Physician Orders as owner and
  require explicit physician/authorized-user review and authorization,
  consistent with the RNICA "Orders and POC actions require explicit
  user initiation" locked decision.

### 6. Plan Care
- **[LOCKED PRODUCT DECISION]** Owns Plan of Care.
- **Purpose:** POC goals, interventions, updates, and summary as the
  authoritative care-planning record.
- **Source workspace:** Plan of Care (POC Summary, POC Goals &
  Interventions, Add/Update POC).
- **[LOCKED PRODUCT DECISION] Approval authority:** the Plan of Care
  workspace owns the POC record. The interdisciplinary team may develop
  and propose updates. Required physician approval and signature remain
  separate authenticated events from IDT proposal/development. A
  proposed POC modification must not be represented as active until the
  required written approval is recorded — consistent with the
  California hospice framework requirement that an individualized POC
  requires physician approval/signature and that proposed modifications
  require written approval before implementation.
- **Boundary:** consistent with the existing POC adapter's explicit-
  action-only behavior (no auto-generation at Lock, per
  `RNICA_LOCK_READINESS_MATRIX.md`); this phase does not change that
  behavior, only where the clinician reaches it from.

### 7. Coordinate Team
- **[LOCKED PRODUCT DECISION]** Aggregates but owns nothing.
- **Purpose:** IDG preparation/history, care team roster, and cross-
  discipline coordination surfaced from workspaces that remain the
  authoritative producers.
- **Source workspaces:** IDG (aggregator role, unchanged — see
  `PATIENT_CHART_AUTHORITY_MAP.md` "IDG Re-Framing: Evidence Aggregator,
  Not Documentation Producer"), Care Team, Communication Log.
- **Boundary:** IDG's existing non-producer role is preserved verbatim;
  this phase does not turn IDG (or itself) into a new documentation
  producer. This phase presents source-linked interdisciplinary
  information and authorized coordination actions; it does not silently
  rewrite POC, order, medication, visit-note, communication, or IDG
  source records.
- **[LOCKED PRODUCT DECISION] Review vs. signature:** review and
  signature are separate events. A review recorded by one clinician must
  not be attributed as another clinician's signature or approval.

### 8. Ensure Compliance
- **[LOCKED PRODUCT DECISION]** Presents deficiencies, readiness checks,
  due items, and source-linked validation results. Ensure Compliance
  does not create, correct, authenticate, approve, or replace the
  underlying clinical record — it owns no clinical records.
- **Purpose:** compliance/HOPE readiness status, deficiency lists, and
  audit-facing summaries.
- **Source workspaces:** Compliance & HOPE, Issues & Outcomes, Incident
  Logs (read/surface only).
- **[LOCKED PRODUCT DECISION] Deficiency structure:** every deficiency
  presented by this phase must identify: source workspace; source record
  or field; applicable rule; severity; resolution destination; and last-
  evaluated timestamp.
- **[LOCKED PRODUCT DECISION] Unsupported capability naming:** "Survey
  Readiness" must not be used unless repository discovery confirms a
  dedicated function backing it; absent that confirmation, use
  "Documentation Readiness." A survey-readiness engine must not be
  represented as operational without repository evidence and separate
  authorization.
- **Boundary:** consistent with RNICA's Compliance & Readiness screen,
  which is already the strongest "reusable" case in the RNICA package
  (`getRnicaFinalizationReadiness`/`evaluate_finalization_readiness`
  parity) — this phase must reuse that same server-verified readiness
  signal for RNICA-owned readiness, not compute a second, divergent
  readiness calculation.

### 9. Handle Transitions
- **[LOCKED PRODUCT DECISION]** Owns transition workflows only (e.g.,
  discharge, level-of-care change, revocation, death).
- **Purpose:** manage the workflow steps and required documentation
  specific to a care transition.
- **Source workspace:** Discharge Planning; reads from Facesheet
  (level of care), Compliance & HOPE (discharge-relevant HOPE items),
  Bereavement (post-death handoff).
- **Boundary:** does not own the underlying clinical/compliance data it
  reads; owns only the transition workflow state itself (e.g., which
  transition steps are complete). Transition presentation must not
  overwrite source discharge, death, bereavement, order, POC, or visit
  records.
- **[LOCKED PRODUCT DECISION] Discharge completeness:** discharge
  completion must include medical-record reconciliation and deficiency
  review before the episode is represented as administratively complete
  — consistent with the California framework's medical-record
  reconciliation and deficiency-analysis requirement at discharge.

### 10. Track & Report
- **[LOCKED PRODUCT DECISION]** Read-only analytics.
- **Purpose:** cross-patient and cross-phase reporting/analytics views.
- **Source workspaces:** all workspaces, read-only; no workspace listed
  here gains a new authoritative record from this phase.
- **Boundary:** must not expose an editable path into any clinical
  record; any apparent edit action must route to the owning phase/
  workspace, not be implemented locally.

## Global authority (restated as locked decisions)

**[LOCKED PRODUCT DECISION]** The Patient Chart, across all 10 phases,
does not determine:
- Hospice eligibility
- Certification
- Prognosis
- Terminal status

**[LOCKED PRODUCT DECISION]** The Patient Chart, across all 10 phases,
may display:
- Supporting evidence
- Documentation review status
- Compliance status
- Clinical findings

**[LOCKED PRODUCT DECISION]** RNICA remains assessment authority (phase 3,
"Assess," is a routing point into RNICA, not a redefinition of it).

**[LOCKED PRODUCT DECISION]** Finalization remains the sole Final Clinical
Narrative authority (unchanged from the RNICA authority family; no phase
in this document creates a second narrative record).

**[LOCKED PRODUCT DECISION] Correction and amendment integrity (global):**
signed or authenticated source records must not be silently overwritten.
Corrections, amendments, and addenda must preserve the original entry and
record the actor, timestamp, reason, and authentication. Denied
correction or amendment requests must retain the required written
justification. Applies across all 10 phases; restates, at the Patient
Chart level, the amendment-integrity behavior already confirmed for
RNICA (`RNICA_LOCK_READINESS_MATRIX.md` §4).

**[LOCKED PRODUCT DECISION] Access control and audit (global):** Patient
Chart access must follow role-based authorization. Every authenticated
documentation event must retain the authorized user's unique identity,
date, time, and action. The system must preserve audit visibility for
entries, corrections, amendments, addenda, signatures, and status
changes. Authorized users must be able to retrieve the complete patient
record without changing source ownership. Applies across all 10 phases.

## Phase-to-workspace ownership summary

| Phase | Owns | Surfaces (does not own) |
|---|---|---|
| 1. Patient Story | Nothing | Facesheet, Clinical Assessments (RNICA), Compliance & HOPE, RNICA Intelligence |
| 2. Know the Patient | Nothing | Facesheet, Care Overview, Intake & Admission, Care Team |
| 3. Assess | Nothing (routes to RNICA, which retains its own authority) | Clinical Assessments (RNICA + Nursing/Spiritual/Psychosocial + History) |
| 4. Document Visit | Visit documentation | Physician Orders (F2F visit-note portion only) |
| 5. Manage Treatment | Treatment/medication/DME workflow | Physician Orders (order authority remains there) |
| 6. Plan Care | Plan of Care | — |
| 7. Coordinate Team | Nothing | IDG, Care Team, Communication Log |
| 8. Ensure Compliance | Nothing | Compliance & HOPE, Issues & Outcomes, Incident Logs |
| 9. Handle Transitions | Transition workflow state only | Discharge Planning, Facesheet, Compliance & HOPE, Bereavement |
| 10. Track & Report | Nothing (read-only) | All workspaces |

## Governance notes

- This document defines **future workflow authority**. It does not
  itself verify current routes, components, services, APIs, database
  entities, or dependencies for each phase — that verification is the
  explicit purpose of `PATIENT_CHART_CURRENT_STATE_MAPPING.md` and the
  classification purpose of `PATIENT_CHART_GAP_ANALYSIS.md`, both created
  after this document per the same instruction.
- `PATIENT_CHART_SCREEN_AUTHORITY_MATRIX.md`, created alongside those two,
  translates each phase above into a screen-level authority matrix in the
  same style as `RNICA_SCREEN_AUTHORITY_MATRIX.md`.
- No phase in this document authorizes application code, schema changes,
  or migrations. No phase in this document performs or substitutes for
  UX/IA design.

## Terminology and ownership-label corrections (locked)

**[LOCKED PRODUCT DECISION]** These corrections govern future screen copy
and ownership labeling for the phases below. They are language/labeling
rules only — they do not authorize code, do not change data ownership,
and do not perform UX/IA design.

### 1. Patient Story
| Replace | With |
|---|---|
| LCD Status: Eligible | LCD Supporting Evidence Present |
| 5 of 5 clinical criteria met | 5 Supporting Evidence Criteria Identified |
| Limited life expectancy of 6 months or less | Physician certification status: [Current Status] (see below) |
| Downward trajectory | Documented functional decline |

Consistent with the existing RNICA/AI-governance prohibition on
eligibility-verdict language (`RNICA_AI_GOVERNANCE.md` §5): Patient Story
owns nothing and must not present eligibility determinations, prognosis
language, or trajectory-generation language as if the phase were an
authority for them.

**[LOCKED PRODUCT DECISION] Certification wording:** do not display
"Terminal diagnosis certified by physician" (or equivalent fact-stated
phrasing) unless the displayed value is linked to an authenticated
certification record. Use "Physician certification status: [Current
Status]" with an added "Source: Physician Certification Record" label.
If no certification record is available, use "Physician certification
status unavailable." This avoids presenting a certification as fact
without a traceable source; hospice certification remains a physician
function, and medical-record entries require authentication and
traceability.

### 2. Know the Patient
| Replace | With |
|---|---|
| Related to terminal trajectory | Hospice Related |

Removes prognosis/trajectory-implying language from a phase that owns
nothing and is not a clinical authority.

### 3. Manage Treatment
| Replace | With |
|---|---|
| Add New Order | Create Draft Order |

Add label: **Requires physician review and authorization.**

Consistent with this document's existing Manage Treatment boundary
("Orders and POC actions require explicit user initiation"; order
authority remains with Physician Orders). "Create Draft Order" makes
explicit that this phase cannot itself finalize an order. Do not use
language implying that a nurse or the workflow layer issues, approves,
or signs a physician order.

### 4. Plan Care
Add under POC Completeness: **Source: Plan Of Care.**

Ownership label only; does not change POC ownership, already assigned to
this phase.

### 5. Coordinate Team
| Replace | With |
|---|---|
| Auto Aggregator Validated | Aggregated from approved source workspaces |
| Eligible for physician batch signature | Pending physician review and signature |

Consistent with this document's existing Coordinate Team boundary
("aggregates but owns nothing") and with IDG's preserved non-producer role
(`PATIENT_CHART_AUTHORITY_MAP.md`, "IDG Re-Framing"). "Eligible for...
batch signature" is corrected because it implies a determination
Coordinate Team does not have authority to make; physician review and
signature remain the controlling, unexecuted action.

### 6. Ensure Compliance
| Replace | With |
|---|---|
| LCD Eligibility Verified | LCD Documentation Review Complete |
| Eligible | Supporting Evidence Identified |
| 5 of 5 criteria met | 5 Supporting Evidence Criteria Identified |
| Survey Readiness (unless a dedicated function is repository-confirmed) | Documentation Readiness |

Add label: **Source: Diagnosis & LCD.**

Consistent with this document's existing Ensure Compliance boundary
("displays readiness and deficiencies but owns no clinical records") and
the RNICA LCD terminology rule: this phase surfaces the same
non-verdict LCD evidence signal RNICA produces and must not restate it as
an eligibility verdict. Every deficiency this phase presents must
identify: source workspace; source record or field; applicable rule;
severity; resolution destination; and last-evaluated timestamp (see
Phase 8's deficiency-structure rule above).

### 7. Global — ownership labeling
**[LOCKED PRODUCT DECISION]** Every workflow screen should display an
ownership label where applicable, using the source workspace's name:
- Source: Facesheet
- Source: RNICA
- Source: Orders
- Source: Plan Of Care
- Source: Visit Notes
- Source: Communication Log
- Source: Diagnosis & LCD

This is the labeling mechanism by which every phase's "surfaces, does not
own" relationship (see the phase-to-workspace ownership summary above) is
made visible to the clinician at the point of use. A phase that surfaces
data without this label is not compliant with this document's ownership
rules.

## Implementation boundary

CODE: BLOCKED
SCHEMA: BLOCKED
MIGRATIONS: BLOCKED
UX/IA DESIGN: NOT PERFORMED HERE

This document, together with `PATIENT_CHART_AUTHORITY_MAP.md`, is the
authority baseline for the three documents that follow it:
`PATIENT_CHART_SCREEN_AUTHORITY_MATRIX.md`,
`PATIENT_CHART_CURRENT_STATE_MAPPING.md`, and
`PATIENT_CHART_GAP_ANALYSIS.md`.
