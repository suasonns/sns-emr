# Patient Chart Authority Map

Companion document to `RNICA_REDESIGN_SOURCE_OF_TRUTH.md`,
`RNICA_SCREEN_BY_SCREEN_EVIDENCE_MATRIX.md`, and
`RNICA_WORKFLOW_AUTHORITY_MAP.md`. Those three documents define the
**RNICA workspace** only. This document defines the **Patient Chart**
that RNICA lives inside — every workspace, its data authority, its
producers/consumers, and how IDG, Compliance, AI, and the Calendar
draw evidence across workspace boundaries.

STATUS: DISCOVERY + AUTHORITY LABELING. NOT IMPLEMENTATION AUTHORIZATION.
CODE: BLOCKED
SCHEMA: BLOCKED
MIGRATIONS: BLOCKED

None of the three RNICA documents above are reopened by this artifact.

## Authority Legend (same seven labels used throughout this doc family)

- **[REPOSITORY-DISCOVERED]** Proven current field, behavior, model,
  endpoint, or cross-module read.
- **[LOCKED PRODUCT DECISION]** Approved future-state decision.
- **[REGULATORY / CLINICAL AUTHORITY]** Controlling CMS/HOPE/CDPH/clinical
  documentation principle.
- **[DESIGN REQUIREMENT]** Figma presentation/interaction requirement.
- **[FUTURE PRODUCT DIRECTION]** Desired capability not yet established
  as current functionality.
- **[NOT BUILT / NOT CONNECTED]** Explicit discovery non-finding.
- **[OPEN DEFECT]** Existing defect, documented separately, not repaired
  here.

## Revised Architecture

**[REPOSITORY-DISCOVERED]** The patient chart is not `Patient Chart →
RNICA → IDG`. It is a flat set of workspaces that IDG, Compliance, and
the Calendar draw from independently:

```
Patient Chart
 ├─ Facesheet
 ├─ Care Overview
 ├─ Intake & Admission
 ├─ Clinical Assessments (RNICA + Nursing/Spiritual/Psychosocial + History)
 ├─ Visit Notes
 ├─ Tx / Meds / DME
 ├─ Physician Orders (incl. CTI, F2F)
 ├─ IDG
 ├─ Plan of Care (POC)
 ├─ Home Health Aide (CHHA)
 ├─ Volunteer Services
 ├─ Bereavement
 ├─ Compliance & HOPE
 ├─ Issues & Outcomes
 ├─ Incident Logs
 ├─ Documents & Images
 ├─ Communication Log
 ├─ Discharge Planning
 ├─ Care Team
 ├─ Faxes
 └─ Visit Calendar
```

**[REPOSITORY-DISCOVERED]** This exact 20-workspace list, in this order,
is the current left patient-chart navigation
(`sns-emr-frontend/src/charts/PatientChartSidebar.jsx:33-110`, array
`navSections`). Sub-items under each parent (e.g., "Add New Visit" / "My
Visit Notes" / "Visit History" under Visit Notes) are confirmed in the
same file and match the screenshots.

---

## Per-Workspace Authority

Each workspace below is defined on the eight requested fields: Purpose,
Data Authority, Evidence Produced, Evidence Consumed, AI Consumer,
Compliance Consumer, IDG Consumer, Calendar Dependencies. Any field with
no repository finding is marked **[NOT BUILT / NOT CONNECTED]** rather
than left blank or assumed.

### Facesheet
- **Purpose [REPOSITORY-DISCOVERED]:** authoritative patient
  identity/insurance/diagnosis/physician record.
- **Data Authority [DESIGN REQUIREMENT]:** sole owner of demographic,
  insurance, and diagnosis identity data; no other workspace may
  silently duplicate or override it.
- **Evidence Produced [REPOSITORY-DISCOVERED]:** identity, address,
  insurance, authorization, place of service, level of care, contacts,
  physicians, diagnoses (primary/secondary/comorbidities), allergies
  (`sns-emr-frontend/src/api/facesheet.ts`,
  `backend/app/models/patient_facesheet.py`).
- **Evidence Consumed [NOT BUILT / NOT CONNECTED]:** none — Facesheet is
  a pure producer.
- **AI Consumer [REPOSITORY-DISCOVERED]:** RNICA diagnosis section and
  LCD evaluation read Facesheet diagnosis data; no independent AI engine
  asserts new Facesheet facts.
- **Compliance Consumer [REPOSITORY-DISCOVERED]:** Compliance & HOPE
  (diagnosis/eligibility fields).
- **IDG Consumer [NOT BUILT / NOT CONNECTED]:** no confirmed direct
  Facesheet read inside `IDGMeetingPatientReview`.
- **Calendar Dependencies [NOT BUILT / NOT CONNECTED]:** none found.

### Care Overview
- **Purpose [REPOSITORY-DISCOVERED]:** cross-discipline census/summary
  presentation (`sns-emr-frontend/src/pages/CareOverviewPage.tsx`,
  `CareOverviewDataPage.tsx`).
- **Data Authority [DESIGN REQUIREMENT]:** presentation layer only, same
  rule as Patient Story — owns no data of its own.
- **Evidence Produced [NOT BUILT / NOT CONNECTED]:** none — aggregation
  only.
- **Evidence Consumed [REPOSITORY-DISCOVERED]:** other workspaces, for
  display.
- **AI Consumer [NOT BUILT / NOT CONNECTED]:** none found.
- **Compliance Consumer [NOT BUILT / NOT CONNECTED]:** none found.
- **IDG Consumer [NOT BUILT / NOT CONNECTED]:** none found.
- **Calendar Dependencies [NOT BUILT / NOT CONNECTED]:** none found.

### Intake & Admission (Consent & Notifications, Chart Completion
Checklist, Staff Assignment)
- **Purpose [REPOSITORY-DISCOVERED]:** admission readiness, consent, and
  staff assignment tracking.
- **Data Authority [DESIGN REQUIREMENT]:** sole owner of admission
  consent/readiness state.
- **Evidence Produced [REPOSITORY-DISCOVERED]:** admission status
  (`backend/app/services/admission/admission_service.py`,
  `admission_status_engine.py`), consent records, staff assignment.
- **Evidence Consumed [NOT BUILT / NOT CONNECTED]:** none found.
- **AI Consumer [NOT BUILT / NOT CONNECTED]:** none found.
- **Compliance Consumer [REPOSITORY-DISCOVERED]:** Finalization/Admission
  readiness gate (`RNICA_WORKFLOW_AUTHORITY_MAP.md` Screen 2).
- **IDG Consumer [NOT BUILT / NOT CONNECTED]:** no confirmed IDG
  consumption of the Chart Completion Checklist.
- **Calendar Dependencies [NOT BUILT / NOT CONNECTED]:** none found.

### Clinical Assessments (RNICA, Nursing/Spiritual/Psychosocial
Assessment, Assessment History)
- **Purpose [REPOSITORY-DISCOVERED]:** the comprehensive nursing/
  discipline assessment record and its longitudinal history.
- **Data Authority [LOCKED PRODUCT DECISION]:** `finalization.clinicalNarrative`
  is the sole nurse-facing Clinical Narrative — restated per
  `RNICA_CLINICAL_NARRATIVE_FINAL_DECISION.md`, not reopened.
- **Evidence Produced [REPOSITORY-DISCOVERED]:** the full RNICA
  assessment record (`sns-emr-frontend/src/components/RNICA.jsx`), plus
  MSW/Chaplain assessments and Assessment History.
- **Evidence Consumed [REPOSITORY-DISCOVERED]:** Facesheet diagnosis,
  Documents & Images (evidence-harvesting input).
- **AI Consumer [REPOSITORY-DISCOVERED]:** RN ICA Intelligence and
  Structured Findings read this workspace's data — this is the **only**
  workspace with a confirmed structured-findings/intelligence pipeline
  today.
- **Compliance Consumer [REPOSITORY-DISCOVERED]:** HOPE reporting
  (`intake/hopeReportMapper.js`), LCD evaluation (`api/eligibility.js`).
- **IDG Consumer [REPOSITORY-DISCOVERED]:** RN discipline note content
  within `IDGReview`/`idg_completeness.py`.
- **Calendar Dependencies [NOT BUILT / NOT CONNECTED]:** none found.

### Visit Notes (Add New Visit, My Visit Notes, Visit History)
- **Purpose [REPOSITORY-DISCOVERED]:** point-of-care visit
  documentation.
- **Data Authority [DESIGN REQUIREMENT]:** sole owner of visit note
  content.
- **Evidence Produced [REPOSITORY-DISCOVERED]:** visit note records
  (`sns-emr-frontend/src/api/visitNotes.js` — `createVisitNote`,
  `listAssignableStaff`).
- **Evidence Consumed [NOT BUILT / NOT CONNECTED]:** none found.
- **AI Consumer [NOT BUILT / NOT CONNECTED]:** no confirmed AI/structured-
  findings pipeline reads Visit Notes today.
- **Compliance Consumer [NOT BUILT / NOT CONNECTED]:** none confirmed.
- **IDG Consumer [NOT BUILT / NOT CONNECTED]:** visit activity is
  referenced in cross-discipline-prep display counts only; no confirmed
  formal ingestion into `IDGMeetingPatientReview`.
- **Calendar Dependencies [NOT BUILT / NOT CONNECTED]:** no confirmed
  reconciliation against a scheduled Visit Calendar (see below).

### Tx / Meds / DME (Add New Order, Current Medications, Medication
History, DME Orders)
- **Purpose [REPOSITORY-DISCOVERED]:** medication list, allergy list, and
  medication safety management.
- **Data Authority [DESIGN REQUIREMENT]:** sole owner of medication data;
  IDG review reads it, it does not own it.
- **Evidence Produced [REPOSITORY-DISCOVERED]:**
  (`sns-emr-frontend/src/api/medications.js` — `listMedications`,
  `addMedication`, `discontinueMedication`, `checkMedicationSafety`,
  `listPatientAllergies`).
- **Evidence Consumed [NOT BUILT / NOT CONNECTED]:** none found.
- **AI Consumer [NOT BUILT / NOT CONNECTED]:** none confirmed.
- **Compliance Consumer [NOT BUILT / NOT CONNECTED]:** none confirmed
  beyond POC linkage.
- **IDG Consumer [REPOSITORY-DISCOVERED]:** **medication list review and
  medication reconciliation** — an explicit, named step in the
  `IDGMeetingPatientReview` workflow
  (`backend/app/models/IDG_DOMAIN_MODEL.md`).
- **Calendar Dependencies [NOT BUILT / NOT CONNECTED]:** none found.

### Physician Orders (Add New MD Order, CTI/Cert-Recert, F2F Visit Notes,
Order History)
- **Purpose [REGULATORY / CLINICAL AUTHORITY]:** physician order
  lifecycle and CMS certification documentation (CTI, F2F).
- **Data Authority [DESIGN REQUIREMENT]:** sole owner of order and
  certification content.
- **Evidence Produced [REPOSITORY-DISCOVERED]:**
  (`sns-emr-frontend/src/api/physicianOrders.js` — `createPhysicianOrder`,
  `submitPhysicianOrder`, `approvePhysicianOrder`,
  `executePhysicianOrder`, `cancelPhysicianOrder`).
- **Evidence Consumed [NOT BUILT / NOT CONNECTED]:** none found.
- **AI Consumer [NOT BUILT / NOT CONNECTED]:** none confirmed.
- **Compliance Consumer [REPOSITORY-DISCOVERED]:** POC/Compliance
  readiness checks.
- **IDG Consumer [REPOSITORY-DISCOVERED]:** **batch-signature queue** —
  `IDGMeetingPatientReview.review_status = REVIEWED` plus
  `PhysicianOrder.signature_status = UNSIGNED`
  (`backend/app/models/IDG_DOMAIN_MODEL.md`;
  `idg_physician_review_service.py`).
- **Calendar Dependencies [NOT BUILT / NOT CONNECTED]:** none found.

### IDG (Add New IDG, IDG History)
- **Purpose [REPOSITORY-DISCOVERED]:** three separate entities, not one
  — see `backend/app/models/IDG_DOMAIN_MODEL.md`:
  1. **PatientIDGReview** (`idg_review.py` / `idg_reviews`) — patient-chart
     clinical documentation. Belongs to one patient. Not a meeting.
  2. **IDGMeeting** (`idg_meeting.py` / `idg_meetings`) — the recurring
     (typically 14-day) interdisciplinary meeting.
  3. **IDGMeetingPatientReview** (`idg_meeting_patient_review.py`) — the
     temporary in-meeting review workspace for one patient.
- **Data Authority [REPOSITORY-DISCOVERED]:** IDG owns its own review/
  meeting/signature-eligibility records; it does not own POC, Medication,
  or Order data — it reviews them.
- **Evidence Produced [REPOSITORY-DISCOVERED]:** IDG review notes,
  meeting minutes, review/defer status, batch-signature eligibility.
- **Evidence Consumed [REPOSITORY-DISCOVERED]:** POC, Medication List,
  Medication Reconciliation, Pending Orders (all named in
  `IDG_DOMAIN_MODEL.md`); RN/MSW/MD/SC discipline notes
  (`idg_completeness.py`).
- **Evidence Consumed [NOT BUILT / NOT CONNECTED]:** CHHA, Bereavement,
  Documents, Incident Logs, Communication Log (beyond a display count),
  Visit Calendar — none of these are named in `IDG_DOMAIN_MODEL.md` or
  `idg_completeness.py`. Treat any claim that IDG already reviews these
  as **[FUTURE PRODUCT DIRECTION]**, not current behavior.
- **AI Consumer [NOT BUILT / NOT CONNECTED]:** no confirmed AI harvesting
  of IDG content itself (IDG is a consumer of RNICA's AI output, not a
  producer of AI-assertable evidence).
- **Compliance Consumer [REPOSITORY-DISCOVERED]:** IDG review and POC
  review are CMS hospice conditions of participation
  (**[REGULATORY / CLINICAL AUTHORITY]**).
- **IDG Consumer:** n/a (this is the workspace itself).
- **Calendar Dependencies [NOT BUILT / NOT CONNECTED]:** `IDGMeeting`
  has its own recurring schedule rule
  (`idg_group_schedule_rule.py`), but no confirmed link to a patient
  Visit Calendar.
- **Critical rule [REPOSITORY-DISCOVERED], restated for redesign
  clarity:** Review and Signature are always separate events.
  `recorded_by_user_id` (who clicked) is tracked separately from
  `physician_user_id` and `reviewed_by_physician_directly` — the audit
  trail must never falsely attribute a facilitator/RN-recorded review to
  the physician.

### Plan of Care (POC Summary, POC Goals & Interventions, Add/Update POC,
POC History)
- **Purpose [REGULATORY / CLINICAL AUTHORITY]:** individualized plan of
  care required by CMS hospice conditions of participation.
- **Data Authority [DESIGN REQUIREMENT]:** sole owner of POC content and
  physician-approval state.
- **Evidence Produced [REPOSITORY-DISCOVERED]:**
  (`backend/app/models/poc.py`, `plan_of_care.py`,
  `plan_of_care_version.py`, `poc_physician_approval.py`; RNICA
  section-linked POC problems via `api/icaAssessments.js`).
- **Evidence Consumed [REPOSITORY-DISCOVERED]:** RNICA assessment
  findings that generate POC problems.
- **AI Consumer [NOT BUILT / NOT CONNECTED]:** none confirmed beyond the
  RNICA structured-findings-to-POC-problem link.
- **Compliance Consumer [REPOSITORY-DISCOVERED]:** RNICA Screen 10
  POC/CHHA readiness checks.
- **IDG Consumer [REPOSITORY-DISCOVERED]:** explicit "Review POC" step
  (`services/poc_review_gate.py`).
- **Calendar Dependencies [NOT BUILT / NOT CONNECTED]:** none found.

### Home Health Aide / CHHA (Assignment, Visits, Notes History, CC Visit)
- **Purpose [REPOSITORY-DISCOVERED]:** home health aide assignment and
  visit-outcome documentation.
- **Data Authority [DESIGN REQUIREMENT]:** sole owner of CHHA visit/task
  content.
- **Evidence Produced [REPOSITORY-DISCOVERED]:**
  (`backend/app/models/chha_visit_outcome.py`,
  `chha_visit_task_result.py`, `chha_poc.py`;
  `sns-emr-frontend/src/api/chhaVisits.js`).
- **Evidence Consumed [NOT BUILT / NOT CONNECTED]:** none found.
- **AI Consumer [NOT BUILT / NOT CONNECTED]:** none confirmed.
- **Compliance Consumer [REPOSITORY-DISCOVERED]:** RNICA Screen 10
  POC/CHHA readiness checks.
- **IDG Consumer [NOT BUILT / NOT CONNECTED]:** CHHA is not named in
  `IDG_DOMAIN_MODEL.md`'s review checklist — treat any "IDG reviews CHHA"
  claim as **[FUTURE PRODUCT DIRECTION]**.
- **Calendar Dependencies [NOT BUILT / NOT CONNECTED]:** no confirmed
  reconciliation of CHHA visits against a schedule.

### Volunteer Services
- **Purpose [REPOSITORY-DISCOVERED]:** volunteer scheduling
  (`sns-emr-frontend/src/pages/VolunteerSchedulingDataPage.tsx`).
- **Data Authority [DESIGN REQUIREMENT]:** sole owner of volunteer
  scheduling data.
- **Evidence Produced [REPOSITORY-DISCOVERED]:** volunteer scheduling
  records.
- **Evidence Consumed [NOT BUILT / NOT CONNECTED]:** none found.
- **AI Consumer [NOT BUILT / NOT CONNECTED]:** none found.
- **Compliance Consumer [NOT BUILT / NOT CONNECTED]:** none found.
- **IDG Consumer [NOT BUILT / NOT CONNECTED]:** none found.
- **Calendar Dependencies [NOT BUILT / NOT CONNECTED]:** volunteer visits
  are cited by Owner as a calendar-relevant discipline, but no confirmed
  schedule/reconciliation code exists.

### Bereavement (Initial Assessment, Bereavement POC, Post-Death
Assessment, Letters Tracker, Post-Death Support)
- **Purpose [REGULATORY / CLINICAL AUTHORITY]:** CMS-required
  bereavement services for a defined post-death period.
- **Data Authority [DESIGN REQUIREMENT]:** sole owner of bereavement
  assessment/POC content.
- **Evidence Produced [REPOSITORY-DISCOVERED]:**
  (`backend/app/models/bereavement_poc.py`;
  `sns-emr-frontend/src/pages/BereavementPage.tsx`,
  `BereavementDataPage.tsx`).
- **Evidence Consumed [NOT BUILT / NOT CONNECTED]:** none found.
- **AI Consumer [NOT BUILT / NOT CONNECTED]:** none found.
- **Compliance Consumer [NOT BUILT / NOT CONNECTED]:** none confirmed
  beyond its own regulatory requirement.
- **IDG Consumer [NOT BUILT / NOT CONNECTED]:** not named in
  `IDG_DOMAIN_MODEL.md`.
- **Calendar Dependencies [NOT BUILT / NOT CONNECTED]:** none found.

### Compliance & HOPE (LCD Eligibility, HOPE-Admission/HUV1/HUV2/
Discharge, Decline of Status)
- **Purpose [REGULATORY / CLINICAL AUTHORITY]:** HOPE (CMS) and LCD
  (Medicare coverage determination) external regulatory requirements.
- **Data Authority [DESIGN REQUIREMENT]:** this workspace is itself a
  consumer of Facesheet/Clinical Assessments/Orders data, not a producer
  of new clinical facts.
- **Evidence Produced [REPOSITORY-DISCOVERED]:** HOPE assessment
  records, LCD eligibility evaluation (`api/eligibility.js`),
  decline-of-status tracking (`backend/app/api/compliance.py`).
- **Evidence Consumed [REPOSITORY-DISCOVERED]:** Facesheet, Clinical
  Assessments, Orders.
- **AI Consumer [NOT BUILT / NOT CONNECTED]:** none confirmed.
- **Compliance Consumer:** n/a (this is the workspace itself).
- **IDG Consumer [REPOSITORY-DISCOVERED]:** HOPE status feeds
  Finalization/Lock readiness, which IDG discussion references.
- **Calendar Dependencies [NOT BUILT / NOT CONNECTED]:** none found.

### Issues & Outcomes
- **Purpose [REPOSITORY-DISCOVERED]:** issue/outcome tracking (nav
  confirmed; dedicated backend model not traced this pass).
- **Data Authority [DESIGN REQUIREMENT]:** presumed sole owner of its own
  entries, pending further verification.
- **Evidence Produced / Consumed / AI / Compliance / IDG / Calendar
  [NOT BUILT / NOT CONNECTED]:** no confirmed cross-workspace
  consumption found this pass — flagged for future verification, not a
  negative finding of non-existence.

### Incident Logs
- **Purpose [REPOSITORY-DISCOVERED]:** incident occurrence documentation
  (`sns-emr-frontend/src/pages/IncidentOccurrencePage.tsx`,
  `IncidentOccurrenceDataPage.tsx`).
- **Data Authority [DESIGN REQUIREMENT]:** sole owner of incident
  records.
- **Evidence Produced [REPOSITORY-DISCOVERED]:** incident occurrence
  records.
- **Evidence Consumed / AI Consumer / Compliance Consumer / IDG
  Consumer / Calendar Dependencies [NOT BUILT / NOT CONNECTED]:** no
  confirmed cross-workspace consumption found this pass.

### Documents & Images (All Documents, Intake Docs, Other Files)
- **Purpose [REPOSITORY-DISCOVERED]:** uploaded document/image storage
  (`backend/app/api/documents.py`).
- **Data Authority [DESIGN REQUIREMENT]:** sole owner of uploaded
  document content.
- **Evidence Produced [REPOSITORY-DISCOVERED]:** uploaded document
  records.
- **Evidence Consumed [NOT BUILT / NOT CONNECTED]:** none found.
- **AI Consumer [REPOSITORY-DISCOVERED]:** referenced as an evidence
  source on RNICA Screen 2 (Evidence & Intake).
- **Compliance Consumer [NOT BUILT / NOT CONNECTED]:** none confirmed.
- **IDG Consumer [NOT BUILT / NOT CONNECTED]:** no confirmed direct IDG
  document review step in `IDG_DOMAIN_MODEL.md`.
- **Calendar Dependencies [NOT BUILT / NOT CONNECTED]:** none found.

### Communication Log
- **Purpose [REPOSITORY-DISCOVERED]:** cross-discipline communication
  entries (`sns-emr-frontend/src/pages/CommunicationLogPage.tsx`,
  `CommunicationLogDataPage.tsx`).
- **Data Authority [DESIGN REQUIREMENT]:** sole owner of communication
  entry content.
- **Evidence Produced [REPOSITORY-DISCOVERED]:** communication entries;
  a display-only count is surfaced in the RNICA cross-discipline-prep
  panel ("0 communication entry(ies)" in the provided screenshots).
- **Evidence Consumed [NOT BUILT / NOT CONNECTED]:** none found.
- **AI Consumer [NOT BUILT / NOT CONNECTED]:** none found.
- **Compliance Consumer [NOT BUILT / NOT CONNECTED]:** none found.
- **IDG Consumer [NOT BUILT / NOT CONNECTED]:** display count only, no
  confirmed formal ingestion into `IDGMeetingPatientReview`.
- **Calendar Dependencies [NOT BUILT / NOT CONNECTED]:** none found.

### Discharge Planning
- **Purpose [REPOSITORY-DISCOVERED]:** discharge planning workspace
  (nav-confirmed; dedicated backend model not traced this pass).
- **Data Authority / Evidence Produced / Consumed / AI / Compliance /
  IDG / Calendar [NOT BUILT / NOT CONNECTED]:** not traced this pass.

### Care Team
- **Purpose [REPOSITORY-DISCOVERED]:** active care team assignment
  display (visible in the provided screenshots' "Active Care Team"
  panel).
- **Data Authority [DESIGN REQUIREMENT]:** presentation of assignment
  data owned elsewhere (staff assignment, per Intake & Admission).
- **Evidence Produced [NOT BUILT / NOT CONNECTED]:** presentation only.
- **Evidence Consumed [REPOSITORY-DISCOVERED]:** staff assignment data.
- **AI Consumer / Compliance Consumer / IDG Consumer / Calendar
  Dependencies [NOT BUILT / NOT CONNECTED]:** none found.

### Faxes
- **Purpose [REPOSITORY-DISCOVERED]:** fax send/history tracking
  (`sns-emr-frontend/src/api/ordersHub.js` — `sendFax`, `getFaxHistory`).
- **Data Authority [DESIGN REQUIREMENT]:** sole owner of fax
  send/history records.
- **Evidence Produced [REPOSITORY-DISCOVERED]:** fax send/history
  records.
- **Evidence Consumed / AI Consumer / Compliance Consumer / IDG
  Consumer / Calendar Dependencies [NOT BUILT / NOT CONNECTED]:** not
  traced beyond Orders Hub this pass.

### Visit Calendar
- **Purpose [FUTURE PRODUCT DIRECTION]:** intended to track RN/LVN/MSW/
  Chaplain/HHA/Volunteer/Physician visit history, missed visits,
  frequency compliance, and visit timing, and to let the system validate
  "was a documented visit actually performed."
- **Data Authority [NOT BUILT / NOT CONNECTED]:** no owner exists yet —
  there is no dedicated backend model, schedule table, or reconciliation
  service. The nav entry exists (`PatientChartSidebar.jsx:109`,
  `key: 'visit-calendar'`) with no child items and no confirmed page
  component wired to it.
- **Evidence Produced [NOT BUILT / NOT CONNECTED]:** none — no
  `VisitSchedule`/`scheduled_visit`/calendar model found.
- **Evidence Consumed [NOT BUILT / NOT CONNECTED]:** none — no code
  reconciles a scheduled visit against a completed Visit Note today.
- **AI Consumer [NOT BUILT / NOT CONNECTED]:** none.
- **Compliance Consumer [NOT BUILT / NOT CONNECTED]:** none today, though
  **[REGULATORY / CLINICAL AUTHORITY]** CMS hospice visit-frequency
  requirements (e.g., RN supervisory visit cadence) are a real external
  requirement regardless of whether this repository automates the check.
- **IDG Consumer [NOT BUILT / NOT CONNECTED]:** not named in
  `IDG_DOMAIN_MODEL.md`.
- **Calendar Dependencies:** n/a (this is the workspace itself).
- **Explicit correction:** do not design Figma screens that assume
  schedule-vs-completion reconciliation already exists — it does not.

---

## IDG Re-Framing: Evidence Aggregator, Not Documentation Producer

**[REPOSITORY-DISCOVERED]** IDG is already the largest cross-workspace
consumer found in this discovery pass: it reads POC, Medication List,
Medication Reconciliation, and Pending Orders as named review steps
(`IDG_DOMAIN_MODEL.md`), plus RN/MSW/MD/SC discipline notes
(`idg_completeness.py`), plus `PhysicianOrder.signature_status` for
batch-signing eligibility.

**[LOCKED PRODUCT DECISION]** For future architecture, IDG should be
modeled as an **Evidence Aggregator** — a workspace whose primary role is
consuming and reconciling evidence produced elsewhere in the chart — not
as a **Documentation Producer** that happens to also read other
workspaces. This reframing does not change any current IDG code,
schema, or entity boundaries defined in `IDG_DOMAIN_MODEL.md` (the three
entities — `PatientIDGReview`, `IDGMeeting`, `IDGMeetingPatientReview` —
remain unchanged and are not reopened here).

**[FUTURE PRODUCT DIRECTION]** Candidate additional IDG evidence sources,
none of which are confirmed as currently wired
(see Cross-Workspace Consumer Summary below): CHHA documentation,
Communication Logs (beyond a display count), uploaded Documents,
external clinical reports, and Visit Calendar reconciliation. Formally
wiring any of these into `IDGMeetingPatientReview` is future scope, not
authorized by this document.

## AI Expansion: Deferred by Decision, Not by Gap

**[LOCKED PRODUCT DECISION]** The current state — where Structured
Findings, RNICA Intelligence, Compliance Validation, and HOPE Integration
exist only inside Clinical Assessments (RNICA), while Visit Notes,
Physician Orders, Medications, IDG, CHHA, Communication Logs, Documents,
Visit Calendar, Bereavement, and Volunteer Services remain AI-independent
— is treated as an **architectural advantage**, not a defect to close
immediately. It allows Data Authority, Evidence Authority, and Consumer
Authority to be defined chart-wide (this document) before any
chart-wide Intelligence Architecture is designed.

**[DESIGN REQUIREMENT]** Do not design or authorize a chart-wide AI/
evidence-harvesting engine until a future, separately authorized
Intelligence Architecture document defines: which workspaces the engine
reads, what it may assert, how conflicting evidence across workspaces is
resolved, and how its output is attributed (consistent with the
Load/Save/Lock-refresh-only, no-continuous-AI-claim discipline already
locked for RNICA in `RNICA_REDESIGN_SOURCE_OF_TRUTH.md`).

**[NOT BUILT / NOT CONNECTED]** No chart-wide AI harvesting engine, and
no per-workspace AI engine outside Clinical Assessments, exists in the
repository today. This is stated as a discovery fact, not a request to
build one.

---

## Cross-Workspace Consumer Summary

| Consumer | Confirmed inputs [REPOSITORY-DISCOVERED] | Not confirmed this pass |
|---|---|---|
| IDG (`IDGMeetingPatientReview`) | POC, Medication List, Medication Reconciliation, Pending Orders | CHHA, Bereavement, Documents, Incident Logs, Communication Log (beyond a display count) |
| IDG (`IDGReview` completeness) | RN/MSW/MD/SC discipline notes present & non-empty | Cross-references into Visit Notes/Orders content |
| IDG (batch-signature queue) | `IDGMeetingPatientReview.review_status`, `PhysicianOrder.signature_status` | — |
| Compliance & HOPE / Lock readiness | Facesheet diagnosis, Clinical Assessments (HOPE fields), ACP fields, POC/CHHA completeness, referral review | Visit Calendar (not built) |
| RNICA Intelligence / AI | Structured findings from Clinical Assessments only | Other workspaces are not asserted by AI |
| Patient Story (presentation layer) | Facesheet, Clinical Assessments, Care Team, Communication Log (counts) | — |

## Governance Notes

1. **[DESIGN REQUIREMENT]** No workspace listed above is an authoritative
   owner of another workspace's data. IDG, Compliance, and Patient Story
   are consumers/reviewers, never silent overwriters.
2. **[OPEN DEFECT — separate from RNICA's own lock defect]** The absence
   of a real Visit Calendar / visit-frequency-reconciliation capability
   means IDG and Compliance currently cannot programmatically answer
   "was a documented visit actually performed on schedule" — that
   determination, if made today, is manual.
3. **[DESIGN REQUIREMENT]** Any Figma design for IDG, Compliance &
   Readiness, or a future Calendar workspace must be traceable to a row
   in this table. Do not design a new IDG evidence source without adding
   it here first.
4. **[FUTURE PRODUCT DIRECTION]** Building a real Visit Calendar with
   schedule-vs-completion reconciliation, and formally wiring CHHA,
   Bereavement, Documents, Incident Logs, and Issues & Outcomes into the
   IDG review checklist, are both candidate future scope — neither is
   authorized by this document.

## Implementation Boundary

This document defines discovery and cross-workspace data authority for
Figma and future planning only. It does not authorize code, schema,
migrations, a Visit Calendar build, or any change to `IDGMeetingPatientReview`,
`IDGReview`, or related IDG services. A separate, explicitly authorized
implementation plan is required before any of this is built.
