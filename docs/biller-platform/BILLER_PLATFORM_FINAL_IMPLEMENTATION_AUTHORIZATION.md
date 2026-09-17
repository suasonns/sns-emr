SNS TECH SOLUTIONS
BILLER PLATFORM
FINAL IMPLEMENTATION AUTHORIZATION

STATUS

APPROVED

LOCKED

FIGMA DESIGN PHASE COMPLETE

GitHub implementation authorized.

==================================================
IMPLEMENTATION AUTHORITY
==================================================

The following Biller Platform pages are approved and locked:

1. Billing Dashboard
2. Billing Readiness
3. Claims Management
4. Denials & Appeals
5. Eligibility Monitoring & Change Detection

No architectural redesign is authorized during implementation.

Future changes must be implementation-driven enhancements validated through field testing and operational evidence.

==================================================
CORE IMPLEMENTATION RULES
==================================================

VERIFY FIRST

Before any schema, migration, API, service, or UI work:

□ Complete repository discovery
□ Complete model mapping
□ Complete route mapping
□ Complete REUSE / EXTEND / CREATE analysis
□ Verify migration lineage
□ Verify Alembic head
□ Verify ORM alignment
□ Verify no schema drift

Do not begin migrations before Discovery is complete.

==================================================
LOCKED PLATFORM ARCHITECTURE
==================================================

Parent Platform:

SNS Tech Solutions

Platform:

SNS Tech Solutions
Biller Platform

Tenant Product:

SNS Hospice Solutions

Tenant Agencies:

- Love & Faith Hospice
- Angela Hospice
- Silva Hospice
- Future Agencies

==================================================
LOCKED BRANDING
==================================================

Display:

SNS Tech Solutions
Biller Platform

Do not display:

SNS Hospice Solutions
Biller Platform

==================================================
LOCKED ACCESS MODEL
==================================================

Visibility follows assignment.

Access follows assignment.

Responsibility follows assignment.

Users may only view:

- Assigned agencies
- Assigned claims
- Assigned revenue
- Authorized DDE scope

Assignment enforcement must be server-side.

==================================================
FINANCIAL WORKSPACE VISIBILITY RULE
==================================================

Authorization states must replace the entire

financial workspace.

Unauthorized users must never see:

Revenue

Payments

Claims

Variance

ERA values

Secondary Billing

Unapplied Cash

or Financial KPIs

==================================================
LOCKED DDE MODEL
==================================================

DDE authorization belongs to an individual user.

Not the entire billing organization.

Required:

- Individual DDE authorization
- Tenant-level DDE authorization
- DDE audit history
- DDE event history

Never store plaintext credentials.

==================================================
PAGE 1
BILLING DASHBOARD
==================================================

STATUS

LOCKED

MISSION

Revenue Operations Command Center

Required Sections:

- Executive Revenue Summary
- Today's Work Queue
- Billing Priorities
- Cash Forecast
- Revenue Pipeline
- Collections Summary
- Revenue At Risk
- Denial Health Overview
- Top Denial Reasons
- Assigned Visibility
- Assigned Agency Registry
- Recent Billing Events & Releases

Required:

- DDE visibility
- Revenue calculations
- Assignment visibility
- Audit support

==================================================
PAGE 2
BILLING READINESS
==================================================

STATUS

LOCKED

MISSION

Revenue Readiness Center

Required Sections:

- Revenue Readiness Overview
- DDE Health Status
- Today's Work Queue
- Readiness Pipeline
- Revenue Unlock Forecast
- Revenue Unlock Priorities
- Readiness Breakdown
- Assignment Accountability
- Authorized Scope
- Assigned Agency Registry
- Revenue At Risk
- Activity Feed

Required:

- Immutable readiness evaluations
- Readiness conditions
- Evidence references
- Readiness actions
- DDE readiness integration
- Revenue unlock calculations
- Guided resolution

==================================================
PAGE 3
CLAIMS MANAGEMENT
==================================================

STATUS

LOCKED

MISSION

Claims Operations Workstation

Required Sections:

- Executive Claim Summary
- Claim Validation Status
- Revenue Integrity Blockers
- Batch Management Panel
- Batch Exception Queue
- Claims Work Queue
- DDE Claims Status
- Claim Lifecycle Pipeline
- Claims At Risk
- Validation Override History
- Active Claims Registry
- Claim Status Timeline

==================================================
CLAIM VALIDATION REQUIREMENTS
==================================================

Claim generation must validate:

- Certification Status
- Face-to-Face Status
- Physician Orders
- Eligibility
- NOE
- DDE Pre-Audit
- Active Revenue Integrity Blockers

Claims cannot silently move into generation if required validations fail.

==================================================
LOCKED CLAIM LIFECYCLE
==================================================

Ready To Generate

Ready To Batch

Ready To Submit

On Hold

Submitted

Accepted

Paid

Denied

==================================================
LOCKED BATCH MANAGEMENT
==================================================

Required:

- Create Batch
- Review Batch
- Approve Batch
- Submit Batch
- Rebuild Batch
- Remove From Batch
- Return To Ready Queue
- Batch Versioning
- Batch Exception Queue

Batch history is immutable.

No destructive deletion.

Every batch revision remains viewable.

==================================================
PAGE 4
DENIALS & APPEALS
==================================================

STATUS

LOCKED

MISSION

Revenue Recovery Operations Center

Required Sections:

- Executive Recovery Metrics
- Denial Work Queue
- Denial Root Cause Analysis
- DDE Denial Status
- AI Appeal Draft Assistant
- Evidence Package Builder
- Appeal Lifecycle Pipeline
- Active Appeals Registry
- Appeal Outcome Tracking

==================================================
AI APPEAL ASSISTANT
==================================================

AI may:

- Generate Appeal Drafts
- Generate Redetermination Requests
- Generate Reconsideration Requests
- Generate Supporting Arguments
- Organize Supporting Evidence

AI may NOT:

- Automatically submit appeals

Human review and approval remains mandatory.

==================================================
PAGE 5
ELIGIBILITY MONITORING & CHANGE DETECTION
==================================================

STATUS

LOCKED

MISSION

Detect eligibility changes before they become claim failures or denials.

Required Sections:

- Executive Eligibility Monitoring
- Automated Eligibility Sweep Scheduler
- Upcoming Eligibility Sweep
- Coverage Change Detection Queue
- Eligibility Work Queue
- Verification Source Hierarchy
- DDE Integration Telemetry
- AI-Assisted Coverage Impact Analyzer
- Claims & Billing Financial Impact Diagnosis
- Eligibility Lifecycle Pipeline
- Active Case Load Coverage Registry

==================================================
LOCKED ELIGIBILITY STRATEGY
==================================================

Eligibility is not a lookup process.

Eligibility is a monitoring process.

Default Workflow:

Monthly Automated Eligibility Sweep

Default Scheduler:

25th of each month

Agency configurable.

Sweep against:

All Active Census Patients

Detect:

- Coverage Terminated
- Coverage Changed
- Subscriber Changed
- Policy Replaced
- Authorization Changes
- Eligibility Failures
- Verification Failures

==================================================
VERIFICATION SOURCE HIERARCHY
==================================================

Support:

1. Waystar (Primary Clearinghouse)

2. Medicare DDE

3. Payer Portal

4. Manual Verification

Results must display verification source.

==================================================
AI COVERAGE IMPACT ANALYSIS
==================================================

For detected coverage changes evaluate:

- Claims Impact
- Readiness Impact
- DDE Impact
- Authorization Impact
- Revenue Impact
- Risk Level
- Recommended Action

==================================================
CROSS-PAGE INTEGRATION
==================================================

Eligibility findings must automatically feed:

- Billing Readiness
- Claims Validation
- Revenue At Risk
- Denials & Appeals
- CAP Calculation
- Operational Work Queues

Claims Validation must consume eligibility findings.

Readiness calculations must consume eligibility findings.

==================================================
CLINICAL BOUNDARY
==================================================

Remain Removed:

- Visits & Notes
- POC & Certifications

Billing consumes clinical outcomes.

Billing does not manage clinical workflows.

==================================================
AUDIT REQUIREMENTS
==================================================

Audit:

- Eligibility sweeps

- Coverage changes

- Claim validation

- Readiness evaluations

- DDE operations

- Appeals

- Batch creation

- Batch revisions

- Remove From Batch

- Return To Queue

- Override actions

- Revenue events

- Exports

Preserve:

Actor

Timestamp

Reason

Previous State

New State

Correlation ID

==================================================
MANDATORY DELIVERABLES
==================================================

Create:

/docs/biller-platform/BILLER_PLATFORM_DISCOVERY_REPORT.md

/docs/biller-platform/BILLER_PLATFORM_DATABASE_SCHEMA_AND_MIGRATION_PLAN.md

/docs/biller-platform/BILLER_PLATFORM_IMPLEMENTATION_TASK_BREAKDOWN.md

/docs/biller-platform/BILLER_PLATFORM_IMPLEMENTATION_VERIFICATION.md

==================================================
IMPLEMENTATION PHASES
==================================================

Phase 0

Discovery Report

Phase 1

Assignment & Access Foundation

Phase 2

DDE Authorization

Phase 3

Revenue Foundation

Phase 4

Billing Readiness Engine

Phase 5

Billing Readiness UI

Phase 6

Billing Dashboard

Phase 7

Claims Validation

Phase 8

Claims Lifecycle

Phase 9

Batch Management

Phase 10

Claims UI

Phase 11

Denials & Appeals

Phase 12

Eligibility Monitoring

Phase 13

Audit & Immutability

Phase 14

Performance & Reliability

Phase 15

Full Validation & Verification

==================================================
DO NOT DECLARE COMPLETE IF
==================================================

□ Discovery Report missing

□ Model mapping incomplete

□ Schema drift exists

□ Cross-tenant access exists

□ DDE is organization-wide instead of user-level

□ Batch history can be deleted

□ Claims disappear when removed from batch

□ Revenue calculations conflict across pages

□ Figma parity is incomplete

□ Tests leave persistent records

□ Restore testing fails

==================================================
FINAL LOCK
==================================================

Billing Dashboard

LOCKED

Billing Readiness

LOCKED

Claims Management

LOCKED

Denials & Appeals

LOCKED

Eligibility Monitoring & Change Detection

LOCKED

Assignment Visibility

LOCKED

DDE Architecture

LOCKED

Claim Validation

LOCKED

Batch Management

LOCKED

Appeal Draft Assistant

LOCKED

Monthly Eligibility Monitoring

LOCKED

SNS Tech Solutions Branding

LOCKED

Proceed to implementation.

No further redesign authorized.

---

## Status

APPROVED. LOCKED. Figma Design Phase Complete. GitHub implementation
authorized for five Biller Platform pages: Billing Dashboard, Billing
Readiness, Claims Management, Denials & Appeals (new), and Eligibility
Monitoring & Change Detection (new). Document is now complete end to
end: Implementation Authority, Core Implementation Rules, Locked
Platform Architecture/Branding/Access Model/DDE Model, all five page
specifications, Audit Requirements, Mandatory Deliverables,
Implementation Phases (0-15), Do Not Declare Complete gate, and Final
Lock. Approval/lock status does not itself authorize code changes; per
this document's own Core Implementation Rules and every prior Biller
Platform implementation document, Phase 0 repository discovery must be
complete — and reviewed/approved — before any schema, migration, API,
service, or UI work begins. As recorded in
`docs/biller-platform/BILLER_PLATFORM_DISCOVERY_REPORT.md`, Discovery
is complete for the original three-page scope, but its REUSE/EXTEND/
CREATE mappings have not yet been reviewed/approved, and that report
does not yet cover the Denials & Appeals or Eligibility Monitoring
entities newly locked here — so no implementation work is authorized
to start under this document either.

## Relationship to Other Documents

- Extends the three-page implementation authorization from
  `docs/biller-platform/BILLER_PLATFORM_FINAL_CONSOLIDATED_HANDOFF.md`
  (Billing Dashboard, Billing Readiness, Claims Management) to five
  pages, adding **Page 4: Denials & Appeals** (Revenue Recovery
  Operations Center, with a locked AI Appeal Draft Assistant that may
  generate drafts/redeterminations/reconsiderations/arguments/evidence
  organization but may **never** auto-submit an appeal — human review
  remains mandatory) and **Page 5: Eligibility Monitoring & Change
  Detection** (a new locked strategy: eligibility is a continuous
  monthly-sweep monitoring process, not an on-demand lookup, with a
  4-tier Verification Source Hierarchy — Waystar, Medicare DDE, Payer
  Portal, Manual — and mandatory Cross-Page Integration feeding
  Billing Readiness, Claims Validation, Revenue At Risk, Denials &
  Appeals, CAP Calculation, and operational work queues).
- Restates, verbatim in substance, the Locked Platform Architecture,
  Locked Branding, Locked Access Model, and Locked DDE Model already
  established in
  `docs/architecture/SNS_TECH_SOLUTIONS_PLATFORM_HIERARCHY.md`,
  `docs/biller-platform/BILLER_PLATFORM_FINAL_IMPLEMENTATION_BRIEF.md`,
  and `BILLER_PLATFORM_FINAL_CONSOLIDATED_HANDOFF.md` — no new
  architectural decisions are introduced in those sections.
  Restates the same locked Claim Lifecycle (8 stages) and Batch
  Management rules (immutable versioning, no destructive deletion)
  introduced in `BILLER_PLATFORM_FINAL_CONSOLIDATED_HANDOFF.md`.
- The AI Appeal Draft Assistant introduces a new capability not
  previously scoped in
  `docs/owner-platform/AI_OPERATIONS_CENTER_SPECIFICATION.md`; that
  document governs enterprise-wide AI infrastructure (Azure OpenAI,
  OCR, Speech, Document Intelligence) but did not previously name an
  appeal-drafting use case specific to the Biller Platform. This
  document establishes the boundary (AI drafts only, human submits)
  that any future AI Operations Center integration must respect.
  Restates the Clinical Boundary (Visits & Notes and POC &
  Certifications remain removed) first established in
  `docs/biller-platform/TENANT_BILLER_DASHBOARD_SPECIFICATION.md`'s
  Remove list.
- The new Denials & Appeals and Eligibility Monitoring pages, and their
  new entities (evidence packages, appeal lifecycle records, coverage
  change detection records, eligibility sweep schedules, verification
  source records), are **not yet reflected** in
  `docs/biller-platform/BILLER_PLATFORM_DISCOVERY_REPORT.md`'s
  25-entity discovery matrix — that report was scoped to the three
  pages locked in `BILLER_PLATFORM_FINAL_CONSOLIDATED_HANDOFF.md` at
  the time it was written. A discovery-matrix addendum covering these
  two new pages' entities will be required before Phase 0 can be
  considered complete for the full five-page scope this document
  authorizes.
- Names the same four Mandatory Deliverables already tracked across
  this document set (`BILLER_PLATFORM_DISCOVERY_REPORT.md` — created;
  `BILLER_PLATFORM_DATABASE_SCHEMA_AND_MIGRATION_PLAN.md` — created;
  `BILLER_PLATFORM_IMPLEMENTATION_TASK_BREAKDOWN.md` — created;
  `BILLER_PLATFORM_IMPLEMENTATION_VERIFICATION.md` — **not yet
  created**, a Phase 15 exit-gate deliverable per
  `BILLER_PLATFORM_FINAL_CONSOLIDATED_HANDOFF.md`) and a 16-phase plan
  (Phase 0-15) that renumbers/relabels but is materially consistent
  with the phase plan in `BILLER_PLATFORM_FINAL_CONSOLIDATED_HANDOFF.md`,
  expanded here to explicitly include Denials & Appeals (Phase 11) and
  Eligibility Monitoring (Phase 12) as their own phases.

## Change Log

| Date | Change |
|---|---|
| 2026-09-17 | Document created (partial) — Final Implementation Authorization for five Biller Platform pages: Implementation Authority, Core Implementation Rules (Verify First), Locked Platform Architecture, Locked Branding, Locked Access Model, Locked DDE Model, Page 1 (Billing Dashboard), Page 2 (Billing Readiness), Page 3 (Claims Management) with Claim Validation Requirements, Locked Claim Lifecycle, and Locked Batch Management, Page 4 (Denials & Appeals) with AI Appeal Assistant boundary, Page 5 (Eligibility Monitoring & Change Detection) with Locked Eligibility Strategy, Verification Source Hierarchy, AI Coverage Impact Analysis, and Cross-Page Integration, Clinical Boundary, and the start of Audit Requirements (cut off at "Audit: - Eligibility"). Remainder of Audit Requirements and any further sections pending. |
| 2026-09-17 | Completed the specification — added the remainder of Audit Requirements (eligibility sweeps, coverage changes, claim validation, readiness evaluations, DDE operations, appeals, batch creation/revisions/removal/return, override actions, revenue events, exports, with actor/timestamp/reason/previous-state/new-state/correlation-ID preservation), Mandatory Deliverables (four named documents), Implementation Phases (Phase 0 Discovery through Phase 15 Full Validation & Verification), Do Not Declare Complete gate, and Final Lock register covering all five pages plus Assignment Visibility, DDE Architecture, Claim Validation, Batch Management, Appeal Draft Assistant, Monthly Eligibility Monitoring, and SNS Tech Solutions Branding. Document now complete end to end. |
| 2026-09-17 | Added a Financial Workspace Visibility Rule to the Locked Access Model: unauthorized users must never see Revenue, Payments, Claims, Variance, ERA values, Secondary Billing, Unapplied Cash, or Financial KPIs — an authorization-state check must replace the entire financial workspace (not merely mask individual fields) for any user who is not authorized. |
