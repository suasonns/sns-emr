THIS DOCUMENT REPLACES ALL EARLIER PARTIAL BILLER PLATFORM HANDOFFS.

DO NOT PATCH OR MERGE FRAGMENTS FROM EARLIER VERSIONS.

==================================================
SNS TECH SOLUTIONS
BILLER PLATFORM
FINAL CONSOLIDATED IMPLEMENTATION HANDOFF
==================================================

STATUS

APPROVED
LOCKED
FIGMA DESIGN COMPLETE
IMPLEMENTATION AUTHORIZED

APPROVED PAGES

1. Billing Dashboard
2. Billing Readiness
3. Claims Management
4. Denials & Appeals
5. Eligibility Monitoring & Change Detection
6. Payment Posting & Reconciliation Center
7. NOE Compliance & Revenue Protection Center
8. CAP Compliance & Financial Exposure Center
9. AR & Collections Intelligence Center
10. Credit Balance Resolution & Compliance Center
11. Room & Board Billing & Reimbursement Center (Biller Platform) / Room & Board Financial Reconciliation Center (SNS Hospice Solutions Tenant Platform) — shared data model, two platform-specific views
12. Executive Billing Intelligence Center — replaces the existing Biller Platform Reports page (same "Reports" navigation item)

No architectural redesign is authorized during implementation.

Future changes must be separately approved enhancements supported by verified operational need or field-testing evidence.

==================================================
1. IMPLEMENTATION AUTHORITY
==================================================

The approved Figma designs are the visual authority.

This document is the authority for:

- Architecture
- Platform boundaries
- Branding
- Navigation
- Permissions
- Tenant isolation
- Billing assignments
- DDE authorization
- Workflow behavior
- Revenue calculations
- Data models
- Auditability
- Immutability
- AI governance
- Acceptance criteria
- Testing
- Production hygiene

Existing verified repository functionality remains authoritative when it does not conflict with this document.

If a conflict is found:

1. Document the conflict.
2. Preserve verified working functionality.
3. Identify the affected requirement.
4. Determine REUSE, EXTEND, or CREATE.
5. Use the smallest safe forward-only correction.
6. Do not silently reinterpret the approved design.
7. Do not redesign during implementation.

==================================================
2. GLOBAL PLATFORM ARCHITECTURE
==================================================

PARENT COMPANY

SNS Tech Solutions

SNS TECH SOLUTIONS PLATFORMS

- Owner Platform
- Biller Platform
- AI Operations Center
- Revenue & Subscription Management
- Governance & Audit Center
- Platform Settings

TENANT PRODUCT

SNS Hospice Solutions

TENANT AGENCIES

- Love & Faith Hospice
- Angela Hospice
- Silva Hospice
- Future Hospice Agencies

==================================================
3. LOCKED BRANDING
==================================================

All Biller Platform pages must display:

SNS Tech Solutions
Biller Platform

Do not display:

SNS Hospice Solutions
Biller Platform

Tenant context must display:

SNS Hospice Solutions Tenant

Current Agency:
<Agency Name> (<Agency Classification>)

AGENCY CLASSIFICATIONS

- Production
- Training
- Demo

==================================================
4. BILLING ORGANIZATION NAMING
==================================================

LOCKED STANDARD NAME

North East Billing Center

Use this exact name consistently in:

- User interface
- Assigned Visibility
- Authorized Scope
- Reports
- Exports
- Audit events
- Configuration
- Documentation
- Figma references
- GitHub specifications
- Approved test fixtures

Do not alternate between:

North East Billing

and:

North East Billing Center

==================================================
5. CORE BILLER PLATFORM MISSION
==================================================

The Biller Platform exists to:

- Find revenue
- Protect revenue
- Unlock revenue
- Submit compliant claims
- Track reimbursement
- Recover denied revenue
- Monitor eligibility continuously
- Reconcile payments
- Manage DDE-related billing work
- Preserve billing evidence
- Preserve immutable operational history
- Support assigned tenant agencies

The Biller Platform must answer:

1. Where is the money?
2. What revenue is ready?
3. What revenue is blocked?
4. What revenue is at risk?
5. What should staff work on first?
6. Who owns the correction?
7. What can be submitted?
8. What can be recovered?
9. What payment has arrived?
10. What payment does not reconcile?
11. What affects cash flow?
12. What DDE issue requires attention?
13. What eligibility change affects billing?
14. What evidence supports the billing decision?

==================================================
6. CLINICAL BOUNDARY
==================================================

The Biller Platform must not become a clinical chart-management platform.

REMAIN REMOVED FROM BILLER NAVIGATION

- Visits & Notes
- POC & Certifications

DO NOT ADD

- Clinical note editing
- Visit management
- Plan-of-care management
- Certification-management workflows
- Clinical assessment editing
- Patient-care workflow management

Billing may consume verified clinical outcomes such as:

- Certification complete or missing
- Face-to-face complete or missing
- Physician order signed or missing
- Required documentation complete or missing
- Clinical audit completed
- Supporting evidence available or missing

Billing users may:

- See the billing consequence
- See revenue impact
- See accountable department
- Request correction
- Assign follow-up
- Escalate
- Add billing evidence
- Revalidate after correction
- Navigate to an authorized source location

Billing users may not:

- Falsely complete clinical responsibilities
- Falsely complete physician responsibilities
- Silently modify signed clinical documentation
- Replace clinical authorship
- Override protected clinical records without approved authority

==================================================
7. FINAL APPROVED NAVIGATION
==================================================

KEEP

- Dashboard
- Billing Readiness
- Claims
- Denials & Appeals
- Eligibility
- Payment Posting
- NOE Tracking
- CAP Calculation
- Aging Report
- Credit Balance Report
- Facility Collections
- Reports
- Settings

REMOVE

- Visits & Notes
- POC & Certifications

Do not create replacement clinical-navigation entries.

==================================================
8. ASSIGNMENT-BASED ACCESS
==================================================

LOCKED RULE

Visibility follows assignment.

Access follows assignment.

Responsibility follows assignment.

A Biller Platform user may see only:

- Billing organizations where the user has active membership
- Agencies assigned to the authorized billing organization
- Agencies assigned to the individual user when required
- Claims and billing data belonging to those agencies
- DDE operations for which the individual user is authorized

Assignment enforcement must occur server-side.

Client-side filtering alone is prohibited.

The system must reject unauthorized access attempted through:

- URL modification
- Query parameter modification
- Request-body modification
- Browser-storage modification
- Client-state modification
- Identifier enumeration
- Direct API calls
- Export requests
- Background jobs
- Cached results

The system must not reveal whether an unassigned tenant exists.

==================================================
9. DDE ARCHITECTURE
==================================================

DDE is required.

DDE is not a future enhancement.

DDE is a core SNS Tech Solutions Biller Platform capability.

DDE authorization belongs to an individual person operating within an authorized billing group.

The system must distinguish:

1. Billing organization membership
2. Tenant assignment to billing organization
3. Individual biller assignment
4. Individual DDE authorization
5. DDE authorization for the specific assigned tenant

Do not treat DDE authorization as automatically belonging to the entire billing organization.

DDE access remains within the billing-group operating context.

DDE user authorization and billing-organization membership are related but separate controls.

DO NOT STORE PLAINTEXT DDE CREDENTIALS.

Do not expose DDE credentials through:

- UI
- Logs
- Exports
- Telemetry
- Error messages
- Audit events
- Unapproved database fields

==================================================
10. VERIFY-FIRST REQUIREMENT
==================================================

Before any schema, migration, API, service, or UI work:

□ Verify repository root.
□ Verify active branch.
□ Verify worktree.
□ Verify working-tree state.
□ Verify database identity.
□ Verify environment-file selection.
□ Verify PostgreSQL connection target.
□ Verify current Alembic revision.
□ Verify expected Alembic head.
□ Verify migration lineage.
□ Verify ORM and database alignment.
□ Verify no schema drift.
□ Verify existing routes.
□ Verify existing frontend components.
□ Verify existing authorization.
□ Verify existing tenant-assignment logic.
□ Verify existing billing models.
□ Verify existing claim models.
□ Verify existing readiness models.
□ Verify existing eligibility models.
□ Verify existing payment and remittance models.
□ Verify existing denial and appeal models.
□ Verify existing evidence and provenance models.
□ Verify existing audit models.
□ Verify existing DDE structures or placeholders.
□ Verify approved Figma implementation surface.

Do not create database migrations until discovery is complete.

Do not guess model names.

Do not create duplicate architecture.

Do not use alembic stamp.

Do not rewrite historical migrations.

Do not accept unsafe automigrations.

Do not create schema drift.

Use forward-only corrective migrations.

==================================================
11. REQUIRED DISCOVERY DELIVERABLE
==================================================

CREATE:

/docs/biller-platform/BILLER_PLATFORM_DISCOVERY_REPORT.md

For each logical entity, classify:

- REUSE
- EXTEND
- CREATE

LOGICAL ENTITIES

- Billing Organization
- Billing Organization Membership
- Tenant Billing Assignment
- Individual Tenant Biller Assignment
- Individual DDE User Profile
- DDE Tenant Authorization
- Billable Episode
- Claim
- Claim Validation
- Claim Lifecycle Event
- Claim Batch
- Claim Batch Version
- Claim Batch Membership
- Batch Exception
- Batch Review
- Validation Override
- Readiness Evaluation
- Readiness Condition
- Readiness Evidence Reference
- Readiness Action
- Billing Work Item
- Revenue Event
- DDE Operational Event
- Denial
- Appeal
- Appeal Version
- Appeal Evidence Package
- Appeal Lifecycle Event
- Eligibility Verification
- Eligibility Sweep
- Eligibility Sweep Result
- Coverage Change
- Eligibility Work Item
- Verification Source
- ERA or Remittance
- Payment Posting
- Payment Match
- Payment Variance
- Contractual Adjustment
- Unapplied Cash
- Secondary Billing Item
- Payment Work Item
- NOE Compliance Record
- NOE Risk Assessment
- NOE Filing Event
- NOE Work Item
- CAP Exposure Record
- CAP Forecast Scenario
- CAP Agency Utilization Snapshot
- CAP Work Item
- AR Aging Snapshot
- AR Recovery Work Item
- AR Collections Activity
- Credit Balance Case
- Credit Cause Record
- CMS-838 Filing Case
- Credit Resolution Work Item
- Room & Board Case
- Room & Board Service Month
- Room & Board Claim
- Payer Remittance
- Payment Allocation
- SNF Payable
- SNF Payment
- Hospice-Funded Advance
- Room & Board Reconciliation Record
- Room & Board Financial Support Schedule
- Report Definition
- Report Configuration
- Saved Report Configuration
- Generated Report
- Generated Report Version
- Report Schedule
- Report Schedule Run
- Executive Report Package
- Executive Package Membership
- Report Source Snapshot
- Report Source Health
- Report Delivery
- Report Audit Event
- Report Authorization Scope
- Regulatory Reference
- Audit Event

DISCOVERY MATRIX COLUMNS

- Logical Requirement
- Existing Model
- Existing Table
- Existing Fields
- Existing Constraints
- Existing Indexes
- Existing API
- Existing UI
- Decision
- Reason
- Files Affected
- Migration Required
- Verification Evidence

Do not fabricate repository object names.

==================================================
PAGE 1
BILLING DASHBOARD
==================================================

STATUS

LOCKED

MISSION

Revenue Operations Command Center

REQUIRED SECTIONS

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
- DDE operational visibility

EXECUTIVE REVENUE SUMMARY

Display:

- Ready Revenue
- Blocked Revenue
- Revenue At Risk
- Pending Payments
- Expected Weekly Collections
- Denied Revenue
- Recovery Opportunities
- DDE Exceptions

Each KPI must display, where applicable:

- Revenue amount
- Claim count
- Trend
- As-of timestamp
- Current tenant scope

TODAY'S WORK QUEUE

Display:

- Claims Ready To Submit
- NOEs Due Today
- Orders Awaiting Signature
- Denials Awaiting Appeal
- Eligibility Reviews
- Payment Posting Queue
- DDE Responses Pending
- DDE Eligibility Reviews
- DDE Status Checks
- DDE Exception Resolution

REVENUE PIPELINE

Display:

- Ready
- Submitted
- Accepted
- Paid
- Denied

Each stage must show:

- Claim count
- Revenue amount

CASH FORECAST

Do not invent forecast values.

If no approved forecasting methodology exists:

- Display unavailable
- State why unavailable
- Do not fabricate confidence percentages

ASSIGNED VISIBILITY

Display:

- Billing organization
- Current agency
- Assigned biller
- DDE authorization status
- Assigned agencies
- Agency classification

ASSIGNED AGENCY REGISTRY

Use:

Assigned Agency Registry

Do not use:

Tenant Agency Registry

REVENUE RELEASED EVENTS

Revenue Released means revenue has become available to progress through billing.

Revenue Released does not mean payment was received.

Keep separate event types for:

- Revenue Released
- Claim Submitted
- Claim Accepted
- Payment Received

BILLING DASHBOARD ACCEPTANCE CRITERIA

□ All data is scoped to the current authorized agency.
□ Assigned Agency Registry shows assigned agencies only.
□ Ready Revenue excludes submitted, paid, voided, and superseded items.
□ Blocked Revenue is deduplicated by authoritative billable unit.
□ Revenue At Risk does not silently double-count blocked revenue.
□ Pending Payments excludes paid, voided, and closed items.
□ Denied Revenue excludes fully recovered or reversed denials.
□ Recovery Opportunities require an active recovery path.
□ DDE Exceptions are visible.
□ DDE actions require individual authorization.
□ No mock financial value appears as production data.
□ Last-updated timestamp is visible.
□ Empty, loading, stale, and error states exist.
□ UI matches approved Figma.

==================================================
PAGE 2
BILLING READINESS
==================================================

STATUS

LOCKED

MISSION

Revenue Readiness Center

Revenue Protection Center

Revenue Unlock Center

The page must answer:

- Why can this revenue not progress?
- What is missing?
- Who owns the fix?
- How much revenue is affected?
- What should be fixed first?
- What revenue becomes available after correction?
- Does DDE create a blocker?
- What evidence supports the determination?

REQUIRED SECTIONS

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

READINESS PIPELINE

Display:

- Not Ready
- In Progress
- Awaiting External
- Ready To Bill
- Submitted
- Paid

READINESS CONDITIONS

Include:

- Unsigned Order
- Missing Certification
- Missing Face-to-Face
- Eligibility Issue
- NOE Deficiency
- Timely Filing Risk
- Documentation Gap
- DDE Verification Required
- DDE Eligibility Conflict
- DDE Status Unknown
- DDE Response Pending
- DDE Submission Failure

Completed Clinical Audit must not become a blocker merely because the audit occurred.

READINESS EVALUATION RULE

Readiness evaluations are immutable historical records.

Recalculation must:

1. Preserve the original evaluation.
2. Create a new evaluation.
3. Record the ruleset version.
4. Preserve source evidence.
5. Link replacement to the superseded evaluation.
6. Preserve actor, timestamp, and reason.

GUIDED RESOLUTION

Every unresolved condition must display:

- Plain-language issue
- Why the issue matters
- Revenue impact
- Owner
- Urgency
- Required action
- Navigation target where available
- Evidence reference where available
- Revalidation action

RECOMMENDED ACTIONS

- Take Me There
- Assign
- Escalate
- Add Evidence
- Revalidate
- Not Now

ASSIGNMENT ACCOUNTABILITY

Display team-level accountability:

- Clinical Team
- Billing Team
- Physician
- Medical Records
- Administrator
- External Party when applicable

Display:

- Open issues
- Revenue held
- Past-due items

Do not create employee performance scores.

BILLING READINESS ACCEPTANCE CRITERIA

□ Not Ready is distinct from At Risk.
□ At Risk is distinct from Blocked.
□ Awaiting External is distinct from internal work pending.
□ Ready To Bill requires all mandatory conditions.
□ Submitted is distinct from Ready To Bill.
□ Paid is the terminal displayed state.
□ Readiness recalculation preserves prior evaluations.
□ Every open blocker identifies ownership.
□ Every open blocker includes revenue impact.
□ Every open blocker includes a resolution path.
□ DDE conditions affect readiness.
□ DDE Submission Failure may block progression.
□ Billing users cannot falsely complete clinical obligations.
□ Evidence remains traceable.
□ Manual override requires reason and authority.
□ UI matches approved Figma.

==================================================
PAGE 3
CLAIMS MANAGEMENT
==================================================

STATUS

LOCKED

MISSION

Claims Operations Workstation

REQUIRED SECTIONS

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

CLAIM GENERATION VALIDATION

Before a claim enters Ready To Generate, verify:

- Certification status
- Face-to-face status
- Physician orders
- Eligibility
- NOE
- DDE pre-audit when required
- Active Revenue Integrity Blockers

Claims cannot silently move into generation when a required validation fails.

The system must show:

- Failed validation
- Owner
- Revenue impact
- Required action
- Verification time
- Evidence source

LOCKED PRIMARY CLAIM LIFECYCLE

- Ready To Generate
- Ready To Batch
- Ready To Submit
- On Hold
- Submitted
- Accepted
- Paid
- Denied

ADDITIONAL RESPONSE STATES

Support without necessarily expanding the top visual pipeline:

- Received
- Rejected
- Returned To Provider
- Accepted With Warning
- Resubmitted
- Appealed
- Reversed
- Voided

Rejected is not the same as denied.

Returned To Provider is not the same as denied.

Submitted does not mean accepted.

Accepted does not mean paid.

BATCH MANAGEMENT

Required actions:

- Create Batch
- Review Batch
- Hold Batch
- Remove From Batch
- Return To Ready Queue
- Rebuild Batch
- Approve Batch
- Submit Batch

BATCH VERSIONING

Do not implement destructive batch deletion.

Example:

Batch v1
12 claims

Batch v2
11 claims

Batch v3
10 claims

Every version must preserve:

- Batch identifier
- Version
- Claims included
- Claims added
- Claims removed
- Revenue total
- Change reason
- Prepared By
- Reviewed By
- Approved By
- Timestamp
- Submission status

REMOVE FROM BATCH

Staff must be able to remove an individual claim from an unsubmitted batch.

Removal must:

- Require a reason
- Preserve original batch version
- Create a new batch version
- Record actor and timestamp
- Place removed claim in Batch Exception Queue
- Give removed claim an explicit returned status
- Prevent claim loss
- Require revalidation before return to Ready Queue

A submitted or transmitted batch cannot be silently edited.

Post-submission corrections must use an approved replacement, correction, adjustment, void, or rebill workflow.

BATCH EXCEPTION QUEUE

Display:

- Claim ID
- Patient context subject to permission
- Removal reason
- Removed By
- Date Removed
- Returned status
- Revenue impact
- Current owner
- Resolution action

"Claims Removed This Cycle" must open the Batch Exception Queue filtered to the relevant batch cycle.

VALIDATION OVERRIDE HISTORY

Display:

- Original blocker
- Override action
- Released By
- Approved By
- Reason
- Previous state
- Resulting state
- Timestamp
- Audit status

An override does not delete the original blocker.

A released claim must remain distinguishable from a normally validated claim.

ACTIVE CLAIMS REGISTRY

Required fields:

- Claim ID
- Patient
- Payer
- Benefit Period or approved billing-period equivalent
- Service Date
- Amount
- Status
- Priority
- Claim Readiness
- Validation Status
- Blocker
- Assigned Biller
- Next Action where shown in Figma

CLAIMS ACCEPTANCE CRITERIA

□ Hard blockers prevent Ready To Generate.
□ Claim validation consumes clinical outcomes without exposing unnecessary clinical content.
□ Claim lifecycle rejects invalid transitions.
□ Clearinghouse responses are idempotent.
□ Out-of-order responses do not rewrite history.
□ Batch creation includes one tenant only.
□ Only eligible claims enter a new batch.
□ Removed claims remain traceable.
□ Rebuild creates a new version.
□ Prior batch versions remain viewable.
□ Submission requires configured approval.
□ Override history is immutable.
□ Benefit Period or equivalent is visible.
□ DDE status is visible.
□ UI matches approved Figma.

==================================================
PAGE 4
DENIALS & APPEALS
==================================================

STATUS

LOCKED

MISSION

Revenue Recovery Operations Center

REQUIRED SECTIONS

- Executive Recovery Metrics
- Denial Work Queue
- Denial Root Cause Analysis
- DDE Denial Status
- AI Appeal Draft Assistant
- Evidence Package Builder
- Appeal Lifecycle Pipeline
- Active Appeals Registry
- Appeal Outcome Tracking
- Appeal Deadline Risk

EXECUTIVE RECOVERY METRICS

Display:

- Total Denied Revenue
- Recoverable Revenue
- Revenue Recovered
- Active Appeals
- Pending Review
- Appeal Deadlines
- Overturn Rate
- Average Resolution Time

WORK QUEUE CATEGORIES

- Appeal Required
- Deadline Approaching
- Missing Evidence
- Waiting On Physician
- Waiting On Medical Records
- Ready To File
- DDE Verification Required
- Reopening Eligible
- Remittance Mismatch

AI APPEAL DRAFT ASSISTANT

AI may:

- Generate appeal drafts
- Generate redetermination drafts
- Generate reconsideration drafts
- Generate supporting argument summaries
- Organize supporting evidence
- Create timeline summaries
- Identify missing evidence
- Suggest approved regulatory references

AI may not:

- Automatically submit an appeal
- Invent evidence
- Invent regulatory citations
- Sign on behalf of a human
- Mark a draft as approved
- Bypass human review

Human review and approval are mandatory.

AI-generated appeal content must be visibly labeled:

AI Draft
Human Review Required

EVIDENCE PACKAGE BUILDER

Display:

- Required evidence
- Evidence found
- Evidence missing
- Source location
- Page or structured record reference where available
- Package completeness
- Reviewer status

APPEAL LIFECYCLE

Display:

- Denial Received
- Under Review
- Evidence Gathering
- Draft Generated
- Human Review
- Approved For Filing
- Submitted
- Decision Received
- Recovered
- Upheld
- Partially Recovered

APPEAL DEADLINE RISK

Display:

- Filing deadline
- Days remaining
- Urgency
- Revenue at risk
- Current owner
- Required action

DENIALS AND APPEALS ACCEPTANCE CRITERIA

□ Denied revenue is distinguished from recoverable revenue.
□ Appeal deadline is visible.
□ Deadline risk is prioritized.
□ Root cause is recorded.
□ DDE denial conditions are visible.
□ AI output is draft only.
□ AI does not submit appeals.
□ Human approval is required.
□ Supporting evidence remains traceable.
□ Missing evidence is identified.
□ Appeal versions remain preserved.
□ Appeal submission is audited.
□ Decision outcomes remain preserved.
□ UI matches approved Figma.

==================================================
PAGE 5
ELIGIBILITY MONITORING & CHANGE DETECTION
==================================================

STATUS

LOCKED

MISSION

Detect eligibility and coverage changes before they become claim failures, denials, or revenue loss.

Eligibility is not merely a lookup process.

Eligibility is a continuous monitoring process.

REQUIRED SECTIONS

- Executive Eligibility Monitoring
- Automated Eligibility Sweep Status & Scheduler
- Manual Run Sweep
- Upcoming Eligibility Sweep
- Coverage Change Detection Queue
- Eligibility Work Queue
- Verification Source Hierarchy
- DDE Integration Telemetry
- AI-Assisted Coverage Impact Analyzer
- Claims & Billing Financial Impact Diagnosis
- Eligibility Lifecycle Pipeline
- Active Case Load Coverage Registry

AUTOMATED ELIGIBILITY MONITORING

Default schedule:

25th of each month

Schedule must be agency configurable.

The scheduled sweep applies to:

All Active Census Patients

The system must also support:

Run Sweep Now

The system may run additional approved event-driven checks for:

- New admission
- Payer update
- Recent verification failure
- New authorization requirement
- Inpatient transition
- Recertification event
- Other approved high-risk event

A manual sweep must require appropriate authorization and be audited.

UPCOMING ELIGIBILITY SWEEP

Display:

- Next scheduled date
- Patients scheduled
- High-risk patients
- Prior lookup failures
- Recent payer changes
- Expiring coverage
- Benefit-period considerations where relevant

COVERAGE CHANGE DETECTION

Detect and classify:

- Coverage Terminated
- Coverage Changed
- Primary Payer Changed
- Secondary Payer Changed
- Subscriber Changed
- Policy Replaced
- Plan Type Changed
- Managed Medicare Change
- Managed Medicaid Change
- Authorization Requirement Changed
- Eligibility Failure
- Verification Failure
- Duplicate Coverage
- Hospice Eligibility Conflict

COVERAGE CHANGE QUEUE

Display:

- Patient
- Previous payer
- Current payer
- Change type
- Effective date
- Verification source
- Revenue impact
- Claims affected
- Current owner
- Required action

VERIFICATION SOURCE HIERARCHY

Support:

1. Waystar or configured automated clearinghouse
2. Medicare DDE
3. Payer Portal
4. Manual Verification
5. Other approved verification source

Waystar must remain configuration-dependent until SNS Tech Solutions has a confirmed subscription, available product package, contract, credentials, technical specification, and approved integration.

Do not present Waystar as connected in production until verified.

Do not fabricate real-time integration status.

Every result must preserve its actual verification source.

AI COVERAGE IMPACT ANALYZER

AI may evaluate:

- Claims impact
- Readiness impact
- DDE impact
- Authorization impact
- Revenue impact
- Risk level
- Suggested next action

AI may not autonomously modify:

- Payer identity
- Subscriber information
- Authorization determination
- NOE
- Claim
- Patient financial record

Human verification remains required before authoritative modifications are propagated.

AUTOMATED WORK-ITEM CREATION

Approved coverage changes must create applicable work items:

- Eligibility Review Required
- Claim Rebuild Required
- Authorization Review Required
- DDE Review Required
- Billing Readiness Review Required
- Payer Information Review Required
- Secondary Coverage Review Required

Generated work items must appear in:

- Eligibility Work Queue
- Billing Readiness
- Claims Validation
- Operational Work Queues

Work-item creation must be auditable and idempotent.

ELIGIBILITY LIFECYCLE

Display:

- Initial Verification
- Monthly Verification
- Coverage Change
- Manual Review
- Resolved
- Billing Released

CROSS-PAGE INTEGRATION

Eligibility findings must feed:

- Billing Readiness
- Claims Validation
- Revenue At Risk
- Denials & Appeals
- CAP Calculation where applicable
- Operational Work Queues

ELIGIBILITY ACCEPTANCE CRITERIA

□ Monthly schedule defaults to the 25th.
□ Schedule is agency configurable.
□ Sweep runs only for the authorized agency.
□ Manual Run Sweep requires permission.
□ Duplicate sweeps do not create duplicate work items.
□ Previous and current coverage are preserved.
□ Verification source is preserved.
□ Waystar status is not fabricated.
□ DDE findings are visible.
□ Coverage changes create applicable work items.
□ AI analysis requires human verification before authoritative change.
□ Eligibility findings propagate to approved downstream workflows.
□ Sweep, change, review, and resolution are audited.
□ UI matches approved Figma.

==================================================
PAGE 6
PAYMENT POSTING & RECONCILIATION CENTER
==================================================

STATUS

LOCKED

MISSION

Process ERAs, reconcile payments, detect variances, route secondary billing, resolve unapplied cash, and preserve payment-posting accountability.

The page must function as a Payment Posting Operations Center.

It must not function solely as an ERA registry.

REQUIRED SECTIONS

- Executive Payment Metrics
- Posting Lifecycle Pipeline
- Payment Posting Work Queue
- Queue Breakdown by Status Category
- AI Reconciliation Assistant
- Payment Variance Analysis
- Secondary Billing Pipeline
- Unapplied Cash Queue
- Remittance Breakdown by Payer
- Posting Audit Visibility

EXECUTIVE PAYMENT METRICS

Display:

- Total Payments MTD
- ERAs Received
- Auto Posted
- Manual Review
- Variances
- Unapplied Cash
- Secondary Billing Ready

Metrics must use authoritative payment and remittance data.

POSTING LIFECYCLE

Display:

- ERA Received
- Auto-Match
- Manual Review
- Posted
- Variance Review
- Completed

PAYMENT POSTING WORK QUEUE

Required categories:

- Manual Match Required
- Underpayment Review
- Overpayment Review
- Missing ERA
- Secondary Billing Required
- Adjustment Review
- Posting Exception
- Unmatched Payment

Queue items should include:

- Claim
- Payer
- Expected amount
- Paid amount
- Variance amount
- Variance percent
- Reason
- Owner
- Required action
- Age

AI RECONCILIATION ASSISTANT

AI may:

- Identify likely underpayments
- Identify likely overpayments
- Explain posting variances
- Explain contractual adjustments
- Identify posting exceptions
- Recommend reconciliation actions
- Recommend recovery work items
- Recommend secondary-billing routing
- Draft reconciliation notes

AI may not:

- Automatically post payments
- Automatically write off balances
- Automatically apply contractual adjustments
- Automatically approve refunds
- Automatically change patient responsibility
- Automatically alter financial records without approved human action

Human approval is required for financial actions.

Replace the ambiguous action label:

Apply Recommendations

with actions that accurately represent human-controlled workflow, such as:

- Review Recommendations
- Create Work Items
- Approve Selected Actions
- Dismiss Recommendation

PAYMENT VARIANCE ANALYSIS

Display:

- Expected amount
- Paid amount
- Variance amount
- Variance percent
- Variance reason
- Contract or rate source where available
- Review status
- Resolution action

Potential variance types include:

- Contract mismatch
- Timely filing adjustment
- Benefit exhaustion
- Coding denial
- Contractual adjustment
- Duplicate payment
- Overpayment
- Underpayment
- Missing authorization effect
- Payer processing error

SECONDARY BILLING PIPELINE

Display:

- Ready For Secondary
- Awaiting Response
- Submitted
- Paid

Secondary billing must preserve linkage to:

- Primary claim
- Primary remittance
- Primary payment
- Remaining balance
- Secondary payer
- Secondary claim
- Secondary remittance

UNAPPLIED CASH QUEUE

Display:

- Received date
- Payer or source
- Amount
- Days outstanding
- Match status
- Owner
- Resolution action

AUTO-GENERATED PAYMENT WORK ITEMS

Automatically create applicable work items for:

- Underpayment Detected
- Overpayment Detected
- Variance Review Required
- Secondary Billing Ready
- Posting Exception
- Unmatched Payment
- Missing ERA
- Unapplied Cash Aging Threshold Reached

Work-item creation must be:

- Audited
- Idempotent
- Tenant scoped
- Traceable to the source remittance or payment

AUTHORIZATION FAILURE BEHAVIOR

LOCKED SECURITY RULE

If authorization fails, replace the entire financial workspace.

Do not display:

- Payment totals
- Revenue values
- ERA counts
- Variance amounts
- Secondary-billing data
- Unapplied cash
- Financial work queues
- Financial registry rows
- AI financial analysis

Display only:

- Access Denied
- Safe explanation
- Authorized agency options where allowed
- Switch Agency action where allowed
- Audit or correlation identifier
- Safe navigation destination

Do not simultaneously display:

You are not authorized

and:

Financial data

CROSS-PAGE INTEGRATION

Payment findings must feed:

- Billing Dashboard
- Revenue calculations
- Denials & Appeals
- Revenue Recovery Workflows
- Secondary Billing
- Operational Work Queues

PAYMENT POSTING ACCEPTANCE CRITERIA

□ ERA lifecycle is operational.
□ Auto-match and manual review remain distinguishable.
□ Variances use authoritative data.
□ Underpayments create reviewable work.
□ Overpayments create reviewable work.
□ AI recommendations require human action.
□ Payment posting is never performed automatically by AI.
□ Secondary billing retains primary-payment linkage.
□ Unapplied cash remains traceable.
□ Duplicate ERA ingestion is idempotent.
□ Unauthorized access hides the entire financial workspace.
□ Payment and adjustment actions are audited.
□ UI matches approved Figma.

==================================================
PAGE 7
NOE COMPLIANCE & REVENUE PROTECTION CENTER
==================================================

STATUS

LOCKED

MISSION

Prevent non-reimbursable hospice days by proactively monitoring NOE deadlines, filing compliance, DDE submission status, and operational risk.

REQUIRED SECTIONS

- Executive NOE Compliance Overview
- Active NOE Risk Screening Queue
- AI NOE Risk Analyzer
- Compliance Timeline (5-Day Rule)
- NOE Action Item Work Queue
- Agency Compliance Tracking
- Filing Delay Root Cause Analysis
- Auto-Generated Work Tasks

EXECUTIVE METRICS

- Active NOEs
- Filed On Time
- At Risk (< 3 Days)
- Average Days Remaining
- Late / Missed
- Revenue At Risk
- Compliance Rate

NOE RISK QUEUE

Display:

- Patient
- Election Date
- Age
- Days Remaining
- Risk Level
- Revenue At Risk
- Assigned Biller
- Pipeline Status

AI NOE RISK ANALYZER

AI may:

- Analyze filing risk
- Estimate revenue exposure
- Identify likely causes
- Create correction plans
- Create work items
- Recommend escalation paths

AI may NOT:

- Submit NOEs
- Bypass validation
- Override signatures
- Override DDE rules
- Auto-complete compliance actions

Human review remains required.

AUTO WORK ITEM CREATION

Generate work items for:

- NOE Due Within 72 Hours
- NOE Due Within 48 Hours
- NOE Due Within 24 Hours
- Missing Physician Signature
- Missing Clinical Documentation
- DDE Submission Failure
- Election Statement Discrepancy

WORK QUEUES

Route generated items into:

- NOE Work Queue
- Billing Readiness
- Claims Validation
- Operational Billing Queues

NOE COMPLIANCE ACCEPTANCE CRITERIA

□ NOE risk monitoring operational.
□ 5-Day Rule timeline operational.
□ Revenue-at-risk calculation operational.
□ Auto-generated NOE work items operational.
□ Agency compliance tracking operational.
□ Filing delay root cause analysis operational.
□ DDE submission monitoring operational.
□ AI recommendations require human approval.
□ No automatic compliance submission by AI.
□ Figma parity verified.

==================================================
PAGE 8
CAP COMPLIANCE & FINANCIAL EXPOSURE CENTER
==================================================

STATUS

LOCKED

MISSION

Monitor aggregate hospice cap exposure, identify operational risk factors, support leadership review, and forecast potential Medicare cap liability using approved operational estimates.

IMPORTANT

This page is not an official CAP calculator.

Official CAP determinations remain dependent on:

- NGS PS&R Reports
- Official Medicare Cap Reports
- Approved reimbursement sources

SNS provides monitoring, forecasting, exposure analysis, and operational review support only.

REQUIRED SECTIONS

- Executive CAP Exposure Overview
- CAP Accumulation & Limit Proximity Forecast
- Multi-Agency CAP Exposure Matrix
- AI Compliance Risk Projections
- CAP Driver Analysis
- Operational Scenario Modeling
- CAP Work Queue
- Historical CAP Reconciliation Logs

EXECUTIVE METRICS

Display:

- CAP Year
- Beneficiaries
- Allowed CAP
- Collected Amount
- Available Space
- Utilization
- Overall Risk

MULTI-AGENCY ANALYSIS

Display:

- Agency
- Beneficiary Count
- Collected Revenue
- Projected Allowed Amount
- Utilization
- Risk Status

AI CAP ANALYSIS

AI may:

- Identify potential exposure indicators
- Analyze utilization trends
- Estimate forecasted risk
- Prioritize review activities
- Generate monitoring reports

AI may NOT:

- Determine official Medicare cap liability
- Certify compliance
- Produce official refund calculations
- Replace official PS&R reports

Human review remains required.

OPERATIONAL SCENARIO MODELING

Purpose:

Forecast operational impact only.

All scenario outputs must display:

Forecasting Tool Only
Not Clinical Guidance
Not Admission Guidance
Not Eligibility Guidance
Not Official CAP Determination

CAP WORK QUEUE

Support:

- Recertification Audits
- High LOS Reviews
- Live Discharge Reviews
- Intake Screening Follow-Up
- Aggregate Overage Investigation

CAP ACCEPTANCE CRITERIA

□ Exposure forecasting operational.
□ Multi-agency analysis operational.
□ Historical CAP review operational.
□ AI compliance projections operational.
□ CAP work queue operational.
□ Official source disclaimer visible.
□ Forecasting outputs clearly identified as estimates.
□ No official CAP determination produced by AI.
□ Figma parity verified.

==================================================
PAGE 9
AR & COLLECTIONS INTELLIGENCE CENTER
==================================================

STATUS

LOCKED
FIGMA APPROVED
IMPLEMENTATION AUTHORIZED

==================================================
MISSION
==================================================

Monitor outstanding accounts receivable, identify collection risk, prioritize recovery activities, reduce write-offs, protect timely filing opportunities, and improve collection performance.

This page is not a traditional aging report.

This page is an operational collections and revenue recovery center.

It must answer:

- What money is still outstanding?
- What money is becoming dangerous?
- Which accounts require action?
- Which payer is causing delays?
- Which agency is underperforming?
- What should be worked first?
- What is approaching write-off risk?
- What is approaching timely filing risk?

==================================================
REQUIRED SECTIONS
==================================================

- Executive AR Summary
- Recovery Prioritization Queue
- Top Collection Risks
- AI Collections Assistant
- Payer Aging Analysis Matrix
- Agency Performance & Aging Summary
- Aging Work Queue
- Historical Collections & Write-Off Ledger

==================================================
EXECUTIVE AR SUMMARY
==================================================

Display:

- Total Outstanding
- Claims Outstanding
- Average Days Outstanding
- 120+ Day Balance
- Collection Rate
- Write-Off Risk
- MTD Recovered

Requirements:

- Values must be tenant scoped
- Values must be agency scoped
- Values must use authoritative AR data
- Values must include an as-of timestamp

==================================================
RECOVERY PRIORITIZATION QUEUE
==================================================

Display:

- Patient
- Payer
- Balance
- Days Outstanding
- Aging Bucket
- Risk Level
- Assigned Owner
- Next Action

Aging Buckets:

- 0-30
- 31-60
- 61-90
- 91-120
- 120+

Risk Levels:

- Low
- Medium
- High
- Critical

Examples of Next Action:

- Timely Filing Appeal
- Payer Follow-Up
- Verify Secondary Liability
- Resubmit Corrected Claim
- Follow-Up On Remittance

Queue must sort by recoverability and urgency.

==================================================
TOP COLLECTION RISKS
==================================================

Display:

- Patient
- Balance
- Days Outstanding
- Deadline
- Risk
- Revenue Impact

Examples:

- Approaching Timely Filing Limit
- Claim Aging Beyond 120 Days
- Secondary Billing Delay
- Outstanding Appeal
- Missing Remittance

==================================================
AI COLLECTIONS ASSISTANT
==================================================

MISSION

Analyze outstanding AR and identify collection opportunities.

AI MAY:

- Identify collection risks
- Identify payer patterns
- Detect timely filing risks
- Recommend recovery actions
- Recommend follow-up workflows
- Draft collection work-item plans
- Draft recovery strategies

AI MAY NOT:

- Write off balances
- Modify receivables
- Adjust accounts
- Change financial values
- Close AR accounts
- Authorize write-offs
- Perform collection actions

Human approval remains mandatory.

Replace automated language with recommendation language.

Preferred actions:

- Generate Collection Strategy
- Generate Recovery Recommendations
- Generate Collection Work Plan

Avoid:

- Auto Collection Execution
- Automated Write-Offs

==================================================
PAYER AGING ANALYSIS MATRIX
==================================================

Display:

- Payer
- 0-30
- 31-60
- 61-90
- 91-120
- 120+
- Total Outstanding
- Average Days Outstanding

Examples:

- Medicare
- Medicaid
- BCBS
- UnitedHealthcare
- Humana

Purpose:

Identify payer-specific collection risk.

==================================================
AGENCY PERFORMANCE & AGING SUMMARY
==================================================

Display:

- Agency
- Outstanding AR
- Outstanding Claims
- Average Days Outstanding
- 120+ Day Balance
- Collection Percentage
- Risk Trend

Purpose:

Identify collection performance issues by agency.

==================================================
AGING WORK QUEUE
==================================================

Required Categories:

- Timely Filing Risk
- Payer Follow-Up
- Appeal Required
- Write-Off Review
- Secondary Billing
- Collection Escalation

Display:

- Task
- Owner
- Balance
- Aging
- Priority
- Impact

==================================================
HISTORICAL COLLECTIONS & WRITE-OFF LEDGER
==================================================

Display:

- Month
- Collected Amount
- Outstanding Balance
- Write-Off Amount
- Collection Rate

Purpose:

Enable trend analysis.

Preserve historical values.

==================================================
AUTO WORK ITEM CREATION
==================================================

Automatically generate work items for:

- Timely Filing Risk
- High-Risk AR
- Appeal Required
- Secondary Billing Follow-Up
- Payer Follow-Up
- Collection Escalation
- Exceptional Aging Event
- 120+ Day Recovery Review

Generated items must appear in:

- Aging Work Queue
- Revenue Recovery Queues
- Operational Billing Queues

Generated work items must be:

- Auditable
- Tenant Scoped
- Idempotent

==================================================
ASSIGNMENT MODEL
==================================================

Visibility follows assignment.

Users may only see:

- Assigned agencies
- Assigned AR records
- Authorized payer activity

All collections data must remain tenant scoped.

==================================================
AUDIT REQUIREMENTS
==================================================

Audit:

- Collection work-item creation
- Collection assignment
- Collection resolution
- Timely filing escalation
- Recovery workflow actions
- Follow-up actions
- Write-off reviews
- Secondary billing follow-up
- Export actions

Preserve:

- Actor
- Timestamp
- Reason
- Previous State
- New State
- Correlation ID

==================================================
ACCEPTANCE CRITERIA
==================================================

□ AR aging analysis operational.
□ Executive AR Summary operational.
□ Recovery Prioritization Queue operational.
□ Top Collection Risks operational.
□ AI Collections Assistant operational.
□ Payer Aging Matrix operational.
□ Agency Aging Analysis operational.
□ Aging Work Queue operational.
□ Historical Collections Ledger operational.
□ Auto-generated recovery work items operational.
□ Tenant isolation enforced.
□ Assignment visibility enforced.
□ AI recommendations require human approval.
□ No automatic write-offs.
□ No automatic financial adjustments.
□ Audit trail operational.
□ Figma parity verified.

==================================================
IMPLEMENTATION NOTES
==================================================

This page is a collections intelligence center.

Do not implement as a passive aging report.

Prioritize:

1. Recovery Prioritization Queue
2. Timely Filing Risk Detection
3. Aging Work Queue
4. Payer Risk Analysis
5. Agency Risk Analysis
6. Automated Recovery Work Item Creation

These workflows are more important than static reporting.

==================================================
FINAL STATUS
==================================================

AR & Collections Intelligence Center

LOCKED
IMPLEMENTATION AUTHORIZED

No further redesign required.

==================================================
PAGE 10
CREDIT BALANCE RESOLUTION & COMPLIANCE CENTER
==================================================

STATUS

LOCKED
IMPLEMENTATION AUTHORIZED

MISSION

Identify, investigate, monitor, resolve, and document patient and payer credit balances while supporting CMS-838 compliance and refund management workflows.

This page is not a reporting screen.

This page is a Credit Balance Resolution & Compliance Center.

==================================================
REQUIRED SECTIONS
==================================================

- Executive Credit Exposure
- Credit Resolution Queue
- Credit Cause Analysis
- AI Credit Resolution Assistant
- CMS-838 Compliance Center
- Credit Aging Analysis
- Multi-Agency Credit Exposure
- Auto-Created Work Items & Tasks

==================================================
EXECUTIVE CREDIT EXPOSURE
==================================================

Display:

- Total Credits
- Claims With Credits
- Patients Affected
- CMS-838 Cases
- Refunds Pending
- Average Credit Age
- Compliance Risk

==================================================
CREDIT RESOLUTION QUEUE
==================================================

Display:

- Patient
- Payer
- Credit Amount
- Age
- Primary Cause
- Refund Required
- Assigned Biller
- Status

Examples:

- Duplicate Payment
- Payer Overpayment
- COB Issue
- Billing Adjustment
- Rate Change

==================================================
CREDIT CAUSE ANALYSIS
==================================================

Display:

- Duplicate Payments
- Payer Overpayments
- COB Errors
- Billing Adjustments
- Rate Changes

Purpose:

Identify root causes of unresolved credits.

==================================================
AI CREDIT RESOLUTION ASSISTANT
==================================================

AI MAY:

- Identify credit risk
- Identify probable causes
- Recommend review actions
- Draft resolution recommendations
- Create investigation work-item recommendations
- Generate CMS-838 preparation recommendations

AI MAY NOT:

- Determine official compliance outcomes
- Issue refunds
- Adjust balances
- Close credit cases
- Submit CMS-838 filings
- Perform financial transactions

Required language:

- Potential Resolution Candidate
- Likely Resolution Path
- Recommended Review
- Estimated Compliance Concern

Human approval remains mandatory.

==================================================
CMS-838 COMPLIANCE CENTER
==================================================

Display:

- Case ID
- Patient
- Credit Amount
- Age
- Filing Deadline
- Filing Status

Track:

- Candidate Cases
- Draft Cases
- Submitted Cases
- Accepted Cases
- Follow-Up Cases

==================================================
CREDIT AGING ANALYSIS
==================================================

Display:

- 0-30 Days
- 31-60 Days
- 61-90 Days
- 91+ Days

Metrics:

- Count
- Amount
- Percent Of Total

==================================================
MULTI-AGENCY CREDIT EXPOSURE
==================================================

Display:

- Agency
- Credit Exposure
- Credit Cases
- Compliance Status

Purpose:

Identify operational risk by agency.

==================================================
AUTO-CREATED WORK ITEMS
==================================================

Create work items for:

- Refund Processing
- COB Investigation
- CMS-838 Filing Review
- Payer Recoupment Review
- Adjustment Review

Work items must be:

- Auditable
- Tenant Scoped
- Traceable
- Idempotent

==================================================
CREDIT BALANCE LIFECYCLE
==================================================

Display:

- Credit Identified
- Investigation
- Validation
- Refund Review
- CMS-838 Review
- Resolved
- Closed

Rules:

- Resolved does not automatically mean Closed
- Refund issued does not automatically close the investigation
- CMS-838 review may be required before closure

Full lifecycle history must be auditable.

==================================================
REFUND GOVERNANCE
==================================================

Refunds require:

- Credit Validation
- Human Review
- Approval Authority

The platform may:

- Recommend refunds
- Flag refunds
- Generate refund work items

The platform may NOT:

- Automatically issue refunds
- Automatically approve refunds
- Automatically close refund cases

All refund decisions remain human-authorized.

==================================================
CMS-838 WORKFLOW
==================================================

Stages:

- Candidate
- Under Review
- Draft Prepared
- Ready For Filing
- Submitted
- Accepted
- Follow-Up Required
- Closed

All stages must be auditable.

Historical filings must remain viewable.

==================================================
AUTHORIZATION FAILURE BEHAVIOR
==================================================

If the user lacks authorization:

Do not display:

- Credit amounts
- Refund values
- CMS-838 data
- Patient-specific credit details
- Compliance status

Replace entire workspace with:

- Access Denied
- Authorized Agency Selection
- Safe Navigation Options

No financial or patient information may be displayed.

==================================================
ACCEPTANCE CRITERIA
==================================================

□ Credit Resolution Queue operational.
□ Credit Cause Analysis operational.
□ CMS-838 Compliance Center operational.
□ Credit Aging Analysis operational.
□ Multi-Agency Exposure operational.
□ Auto-created work items operational.
□ AI recommendations require human approval.
□ No automated compliance conclusions.
□ No automated refunds.
□ No automated balance adjustments.
□ Audit history operational.
□ Credit Balance Lifecycle enforced (Resolved ≠ Closed; refund issuance does not auto-close; CMS-838 review may gate closure).
□ Refund Governance enforced (no automatic issuance, approval, or closure).
□ CMS-838 Workflow stages operational and auditable; historical filings remain viewable.
□ Authorization Failure Behavior enforced (entire workspace replaced; no financial or patient data exposed to unauthorized users).
□ Figma parity verified.

==================================================
FINAL STATUS
==================================================

Credit Balance Resolution & Compliance Center

APPROVED
LOCKED
IMPLEMENTATION AUTHORIZED

==================================================
PAGE 11
ROOM & BOARD BILLING & REIMBURSEMENT CENTER
+
ROOM & BOARD FINANCIAL RECONCILIATION CENTER
==================================================

STATUS

LOCKED
FIGMA APPROVED
IMPLEMENTATION AUTHORIZED

==================================================
CRITICAL ARCHITECTURE RULE
==================================================

THIS IS A SHARED DATA WORKFLOW.

DO NOT CREATE TWO SEPARATE SYSTEMS.

ONE AUTHORITATIVE DATA MODEL

TWO SEPARATE USER EXPERIENCES

1. SNS TECH SOLUTIONS
   BILLER PLATFORM

   PAGE:
   Room & Board Billing & Reimbursement Center

2. SNS HOSPICE SOLUTIONS
   TENANT PLATFORM

   PAGE:
   Room & Board Financial Reconciliation Center

BOTH PAGES MUST READ FROM THE SAME
AUTHORITATIVE RECORDS.

DO NOT DUPLICATE:

- Patients
- Facilities
- Service Months
- Claims
- Reimbursements
- Payment Allocations
- SNF Payables
- SNF Payments
- Reconciliation Records

==================================================
BUSINESS PURPOSE
==================================================

This workflow exists for dual-eligible hospice patients
residing in SNFs or facilities where:

- Hospice bills Medi-Cal
- Hospice bills Medi-Cal Managed Care Plans
- Hospice bills HMO plans responsible for room and board

AND

- Hospice pays the SNF

Often before reimbursement arrives.

The system must answer:

- Did Medi-Cal pay us?
- Did the HMO pay us?
- When did they pay?
- What exact amount did they pay?
- What month did the payment cover?
- Have we paid the SNF?
- When did we pay the SNF?
- How much did we pay?
- What reimbursement remains outstanding?
- How much has hospice advanced?

==================================================
SHARED AUTHORITATIVE RECORDS
==================================================

Required:

- RoomBoardCase
- ServiceMonth
- RoomBoardClaim
- PayerRemittance
- PaymentAllocation
- SNFPayable
- SNFPayment
- HospiceFundedAdvance
- ReconciliationRecord
- FinancialSupportSchedule

==================================================
MASTER ROOM & BOARD CASE STATUS
==================================================

- Eligibility Review
- Case Setup Required
- Ready For Monthly Billing
- Billing In Progress
- Awaiting Reimbursement
- Partially Reimbursed
- Reimbursement Received
- SNF Payment Pending
- SNF Partially Paid
- SNF Paid
- Reconciliation Required
- Fully Reconciled
- Dispute Or Appeal
- Closed

==================================================
BILLER PLATFORM PAGE
==================================================

PAGE NAME

Room & Board Billing & Reimbursement Center

OWNER

SNS Tech Solutions
Biller Platform

MISSION

Bill payers.

Track reimbursement.

Track exact payment dates.

Track exact payment amounts.

Track service-month coverage.

Work delays, denials, variances, and appeals.

==================================================
BILLER EXECUTIVE KPI CARDS
==================================================

- Active R&B Cases
- Ready To Bill
- Submitted
- Awaiting Medi-Cal
- Awaiting HMO
- Received This Month
- No Payment Reported
- Short / Partial Payments
- Oldest Outstanding

==================================================
MONTHLY BILLING QUEUE
==================================================

Display:

- Patient
- Facility
- Payer
- Service Month
- Expected Amount
- Status

Statuses:

- Draft
- Ready To Bill
- Submitted
- Returned
- Rejected
- Denied
- Resubmitted
- Hold
- Failed Validation
- Billing Complete

==================================================
CLAIM VALIDATION STATUS
==================================================

- Not Evaluated
- Passed
- Passed With Warning
- Blocked
- Correction Required
- Revalidation Required

==================================================
PAYER REIMBURSEMENT QUEUE
==================================================

Display:

- Patient
- Payer
- Claimed Amount
- Amount Received
- Exact Payment Date
- Remaining Balance
- Status

Statuses:

- Not Yet Billed
- Submitted
- Payer Processing
- Pending Payment
- No Payment
- Partially Paid
- Paid In Full
- Short Paid
- Denied
- Appealed
- Under Review
- Reimbursement Complete

==================================================
PAYMENT ALLOCATION
==================================================

Statuses:

- Unallocated
- Partially Allocated
- Fully Allocated
- Allocation Review
- Allocation Disputed
- Allocation Corrected
- Allocation Reversed

Required Fields:

- Payment Reference
- Payer
- Total Received
- Amount Allocated
- Amount Unallocated
- Allocation Status

==================================================
PAYER FOLLOW-UP QUEUE
==================================================

Display:

- Patient
- Payer
- Days Outstanding
- Next Action

Statuses:

- Follow-Up Due
- Scheduled
- Contacted
- Awaiting Response
- Escalation Required
- Provider Dispute
- Appeal Required
- Resolved

==================================================
SERVICE MONTH MATRIX
==================================================

Required.

Track:

- Patient
- Facility
- Payer
- Month
- Expected
- Received
- Exact Reimbursement Date
- Status

Every service month must be independently tracked.

==================================================
TENANT PAGE
==================================================

PAGE NAME

Room & Board Financial Reconciliation Center

OWNER

SNS Hospice Solutions
Agency Financial Operations

MISSION

Track SNF payments.

Track hospice-funded advances.

Track reimbursement exposure.

Track reimbursement delays.

Provide annual reporting support.

==================================================
TENANT EXECUTIVE KPI CARDS
==================================================

- R&B Patients
- SNF Paid
- SNF Payable
- Medi-Cal Received
- HMO Received
- Outstanding Reimbursement
- Hospice Advances
- Average Delay
- Awaiting Medi-Cal
- Awaiting HMO

==================================================
HOSPICE-FUNDED PASS-THROUGH ADVANCES
==================================================

Display:

- Patient
- Facility
- Payer
- SNF Paid
- Exact SNF Payment Date
- Reimbursement Received
- Exact Reimbursement Date
- Advance Status

Statuses:

- Advance Open
- Partially Reimbursed Advance
- Fully Reimbursed Advance
- Advance Under Review
- Advance Disputed
- Advance Closed

==================================================
FACILITY SNF DISBURSEMENTS
==================================================

Display:

- Facility
- Active Patients
- Invoiced
- Amount Paid
- Exact Payment Date
- Outstanding Amount

The system must answer:

- Have we paid the SNF?
- When did we pay?
- How much did we pay?

==================================================
PAYER REIMBURSEMENT AGING
==================================================

Track separately:

- 0-30
- 31-60
- 61-90
- 91-120
- 121-180
- 181+

Display by:

- Medicare
- Medi-Cal
- HMO
- Managed Care Plans

==================================================
SERVICE MONTH RECONCILIATION LEDGER
==================================================

Required Fields:

- Patient
- Facility
- Payer
- Service Month
- Expected
- Received
- Exact Reimbursement Date
- SNF Paid
- Exact SNF Payment Date
- Current Status

Statuses:

- Matched
- Partial
- Discrepancy
- Payer Hold
- Awaiting Reimbursement
- Rejected
- Appealed
- Reconciled

==================================================
SNF PAYABLE STATUS
==================================================

- Not Established
- Invoice Received
- Under Review
- Approved For Payment
- Scheduled
- Partially Paid
- Paid In Full
- Disputed
- Adjustment Required
- Closed

==================================================
SNF PAYMENT STATUS
==================================================

- Not Paid
- Scheduled
- Processing
- Partially Paid
- Paid In Full
- Failed
- Reissued
- Voided
- Reconciled

Every payment must preserve:

- Exact Amount
- Exact Payment Date
- Check Number
- EFT Reference
- Payment Method

==================================================
RECONCILIATION STATUS
==================================================

- Not Ready
- Pending
- In Reconciliation
- Matched
- Partial Match
- Payer Variance
- Facility Variance
- Missing Payer Payment
- Missing SNF Payment
- Adjustment Review
- Fully Reconciled
- Closed

==================================================
ANNUAL REPORTING SUPPORT
==================================================

Required Section

Annual Cost Reporting Summary

Support Schedule Fields:

- Fiscal Year
- Patient
- Facility
- Payer
- Service Month
- Expected Reimbursement
- Amount Billed
- Amount Received
- Exact Reimbursement Date
- Payer Reference
- Amount Paid To SNF
- Exact SNF Payment Date
- Outstanding Reimbursement
- Outstanding Payable
- Hospice-Funded Advance
- Adjustment Amount
- Dispute Status
- Evidence References

IMPORTANT

This is supporting documentation.

Do not represent this as an official completed Medicare Cost Report.

==================================================
AUDIT REQUIREMENTS
==================================================

Audit:

- Case Creation
- Eligibility Verification
- Setup Completion
- Claim Validation
- Claim Submission
- Claim Correction
- Reimbursement Receipt
- Reimbursement Allocation
- Allocation Correction
- SNF Payable Creation
- SNF Payable Approval
- SNF Payment
- SNF Payment Void
- Reconciliation
- Reconciliation Reopen
- Dispute Creation
- Appeal Creation
- Export
- Financial Report Generation

Preserve:

- Actor
- Role
- Agency
- Patient
- Facility
- Payer
- Service Month
- Previous State
- New State
- Exact Amount
- Reason
- Timestamp
- Correlation ID

==================================================
AUTHORIZATION RULES
==================================================

BILLER PLATFORM

Users may only see:

- Assigned Agencies
- Assigned Payers
- Assigned Reimbursement Activity

TENANT PLATFORM

Users may only see:

- Their Agency
- Their Financial Records

If authorization fails:

Do not display:

- Payment Amounts
- Reimbursement Amounts
- SNF Payments
- Financial Metrics
- Patient Financial Records

Replace the entire workspace with:

Access Denied

==================================================
AI GOVERNANCE
==================================================

AI MAY:

- Identify Missing Reimbursements
- Recommend Follow-Up
- Identify Allocation Patterns
- Suggest Disputes
- Draft Appeals
- Draft Payer Correspondence
- Summarize Reconciliation History

AI MAY NOT:

- Submit Claims
- Record Payments
- Allocate Payments Automatically
- Approve Payables
- Issue SNF Payments
- Modify Financial Records
- Close Cases

Human approval required.

==================================================
ACCEPTANCE CRITERIA
==================================================

□ Shared data architecture implemented.
□ Biller and Tenant views read same records.
□ Exact reimbursement amounts tracked.
□ Exact reimbursement dates tracked.
□ Exact SNF payment amounts tracked.
□ Exact SNF payment dates tracked.
□ Service-month reconciliation operational.
□ Hospice-funded advance tracking operational.
□ Payment allocation operational.
□ Payer aging operational.
□ SNF payable lifecycle operational.
□ Reconciliation lifecycle operational.
□ Annual reporting support operational.
□ Audit history operational.
□ Cross-tenant isolation verified.
□ Authorization enforced.
□ Figma parity verified.

==================================================
EPIC SUMMARY
ROOM & BOARD BILLING & REIMBURSEMENT
+
ROOM & BOARD FINANCIAL RECONCILIATION
==================================================

STATUS

LOCKED
IMPLEMENTATION AUTHORIZED

BUSINESS OWNER

SNS Hospice Solutions

TECHNICAL OWNER

SNS Tech Solutions

PRIORITY

HIGH

RATIONALE

This workflow supports:

- Medi-Cal Room & Board reimbursement
- Managed Care / HMO Room & Board reimbursement
- SNF pass-through payments
- Hospice-funded advances
- Service-month reconciliation
- Financial visibility
- Agency cash exposure
- Financial reporting support
- Annual cost-report supporting schedules

THIS IS NOT FACILITY COLLECTIONS.

THIS IS ROOM & BOARD REIMBURSEMENT RECONCILIATION.

==================================================
EPIC IMPLEMENTATION CHECKLIST
==================================================

ARCHITECTURE

□ Shared source of truth
□ No duplicated Room & Board data
□ Biller/Tenant separation maintained

DATABASE

□ Schema implemented
□ Migrations verified
□ Constraints added
□ Indexes added

BILLER PLATFORM

□ KPI cards operational
□ Billing Queue operational
□ Reimbursement Queue operational
□ Payment Allocation operational
□ Service Month Matrix operational

TENANT PLATFORM

□ Exposure Dashboard operational
□ SNF Payment Ledger operational
□ Advance Tracking operational
□ Reconciliation Ledger operational
□ Reporting Summary operational

FINANCIAL

□ Exact reimbursement amount tracked
□ Exact reimbursement date tracked
□ Exact SNF payment amount tracked
□ Exact SNF payment date tracked
□ Outstanding exposure calculated
□ Hospice-funded advances calculated

RECONCILIATION

□ Matched status operational
□ Partial status operational
□ Variance status operational
□ Reopen workflow operational

AUDIT

□ Full audit trail operational
□ History immutable

SECURITY

□ Tenant isolation verified
□ Biller authorization verified
□ Agency authorization verified
□ Unauthorized users cannot view data

REPORTING

□ Annual support schedule operational
□ Export operational
□ Cost-report support verified

FIGMA

□ Biller parity verified
□ Agency parity verified
□ Lifecycle parity verified
□ Status parity verified

==================================================
IMPLEMENTATION MANDATE
==================================================

DO NOT BUILD THIS AS A COLLECTIONS MODULE.

DO NOT BUILD THIS AS A STANDALONE TENANT FEATURE.

IMPLEMENT ONE AUTHORITATIVE ROOM & BOARD DOMAIN.

Expose:

1. Operational Billing View
   (Biller Platform)

2. Financial Reconciliation View
   (Tenant Platform)

Both must read the exact same records.

==================================================
ROOM & BOARD IMPLEMENTATION MILESTONES
==================================================

MILESTONE 1 — REPOSITORY DISCOVERY

GOAL

Identify existing models.

Classify:

- REUSE
- EXTEND
- CREATE

Discovery Targets:

- Patient
- Facility
- Payer
- Claim
- Payment
- Remittance
- Payment Posting
- Adjustments
- Work Items
- Audit Events
- Financial Reports

Deliverable:

ROOM_BOARD_DISCOVERY_REPORT.md

Exit Criteria:

□ All logical entities mapped
□ Existing schema reviewed
□ Existing routes reviewed
□ Existing UI reviewed
□ Existing payment infrastructure reviewed

--------------------------------------------------
MILESTONE 2 — SHARED ROOM & BOARD DATA FOUNDATION
--------------------------------------------------

Database Objects:

- RoomBoardCase
- ServiceMonth
- RoomBoardClaim
- PayerRemittance
- PaymentAllocation
- SNFPayable
- SNFPayment
- HospiceFundedAdvance
- ReconciliationRecord
- FinancialSupportSchedule

RoomBoardCase

Fields: id, agency_id, patient_id, facility_id, payer_id,
case_status, created_at, updated_at

Purpose: Master Room & Board workflow.

ServiceMonth

Fields: id, room_board_case_id, service_month, service_year,
expected_reimbursement, status

Purpose: Month-by-month reimbursement tracking.

RoomBoardClaim

Fields: id, service_month_id, payer_id, claim_number,
amount_billed, status, submitted_at, processed_at

Purpose: Track every Medi-Cal/HMO submission.

PayerRemittance

Fields: id, payer_id, payment_reference, payment_amount,
payment_date, check_number, eft_reference, received_date

Purpose: Track exact reimbursement received.

PaymentAllocation

Fields: id, payer_remittance_id, service_month_id,
allocated_amount, allocation_status, allocated_at

Purpose: Support one-to-many allocations.

SNFPayable

Fields: id, facility_id, patient_id, service_month_id,
invoice_amount, approved_amount, status, invoice_date, due_date

Purpose: Track hospice obligation to SNF.

SNFPayment

Fields: id, snf_payable_id, amount_paid, payment_date,
check_number, eft_reference, status

Purpose: Answer: When did we pay? How much did we pay?

HospiceFundedAdvance

Fields: id, service_month_id, snf_paid_amount,
payer_reimbursed_amount, outstanding_exposure, advance_status

Statuses:

- Advance Open
- Partially Reimbursed
- Fully Reimbursed
- Closed

ReconciliationRecord

Fields: id, service_month_id, expected_amount, received_amount,
snf_paid, variance, status, reconciled_at

Statuses:

- Pending
- Matched
- Partial
- Variance
- Reopened
- Closed

FinancialSupportSchedule

Fields: id, fiscal_year, agency_id, generated_at, generated_by

Purpose: Annual reporting support.

--------------------------------------------------
MILESTONE 3 — BILLER PLATFORM
--------------------------------------------------

Page: Room & Board Billing & Reimbursement Center

Owner: SNS Tech Solutions / Biller Platform

Required Components:

- Executive KPI Cards
- Monthly Billing Queue
- Claim Validation Queue
- Payer Reimbursement Queue
- Payment Allocation Queue
- Payer Follow-Up Queue
- Service-Month Matrix
- Audit Feed

Acceptance:

□ Claims can be tracked
□ Service months tracked
□ Payment dates recorded
□ Payment amounts recorded
□ Follow-up queue operational
□ Allocation engine operational

--------------------------------------------------
MILESTONE 4 — TENANT PLATFORM
--------------------------------------------------

Page: Room & Board Financial Reconciliation Center

Owner: SNS Hospice Solutions

Components:

- Executive Exposure Dashboard
- Hospice-Funded Advances
- SNF Disbursement Ledger
- Reimbursement Aging
- Service Month Reconciliation Ledger
- Annual Reporting Summary

Acceptance:

□ SNF payments visible
□ Exact SNF payment dates visible
□ Outstanding reimbursement visible
□ Hospice advances visible
□ Service-month history visible

--------------------------------------------------
MILESTONE 5 — SHARED RECONCILIATION ENGINE
--------------------------------------------------

Rules:

- Expected - Received = Outstanding
- Received - SNF Paid = Reconciled
- Variance = Mismatch

Statuses:

- Matched
- Partial
- Short Paid
- Denied
- Appealed
- Reconciled
- Closed

Acceptance:

□ Reconciliation automated
□ Variance identification operational
□ Reopen supported

--------------------------------------------------
MILESTONE 6 — AUDIT FRAMEWORK
--------------------------------------------------

Audit:

- Claim Created
- Claim Submitted
- Claim Corrected
- Payment Received
- Allocation Created
- Allocation Modified
- SNF Payable Approved
- SNF Payment Issued
- Reconciliation Completed
- Reconciliation Reopened
- Report Generated

Store:

- Actor
- Role
- Agency
- Patient
- Facility
- Service Month
- Amount
- Old Value
- New Value
- Reason
- Timestamp

--------------------------------------------------
MILESTONE 7 — REPORTING SUPPORT
--------------------------------------------------

Generate: Room & Board Reconciliation Schedule

Columns:

- Patient
- Facility
- Payer
- Month
- Expected
- Received
- Payment Date
- SNF Paid
- SNF Payment Date
- Outstanding
- Advance
- Status

Important:

Supporting Schedule — NOT an Official Medicare Cost Report.

==================================================
FINAL STATUS
==================================================

Room & Board Billing & Reimbursement Center
(Biller Platform)

LOCKED

AND

Room & Board Financial Reconciliation Center
(Tenant Platform)

LOCKED
IMPLEMENTATION AUTHORIZED

No further redesign authorized.

==================================================
PAGE 12
EXECUTIVE BILLING INTELLIGENCE CENTER
==================================================

STATUS

APPROVED
LOCKED
FIGMA APPROVED
IMPLEMENTATION AUTHORIZED

==================================================
CRITICAL REPLACEMENT DIRECTIVE
==================================================

THIS DESIGN REPLACES THE EXISTING BILLER PLATFORM REPORTS PAGE.

Existing route shown in the current application:

/billing/reports

Use the repository's existing authoritative Reports route and routing conventions.

DO NOT:

- Create a second Reports page
- Create a parallel Executive Intelligence route
- Keep the old snapshot-card Reports page accessible
- Leave obsolete Reports components mounted
- Maintain duplicate reporting calculations
- Preserve the former "dashboard of dashboards" implementation

The existing Reports navigation item must open:

Executive Billing Intelligence Center

The replacement must preserve appropriate existing route guards, authentication, tenant assignment checks, and navigation behavior.

Before deleting any existing code:

1. Inspect the current Reports route.
2. Inspect existing Reports components.
3. Inspect existing report services and APIs.
4. Identify reusable export, audit, authorization, and reporting infrastructure.
5. Classify existing code as REUSE, EXTEND, REPLACE, or RETIRE.
6. Preserve working shared functionality.
7. Remove obsolete components only after replacement verification passes.

==================================================
PAGE OWNER AND BRANDING
==================================================

Owner: SNS Tech Solutions

Platform: Biller Platform

Page Name: Executive Billing Intelligence Center

Navigation Label: Reports

Do not display:

SNS Hospice Solutions
External Billing Services

Tenant context must identify:

- Current assigned agency
- Agency classification
- Reporting scope

==================================================
PAGE MISSION
==================================================

Replace the passive Reports page with an executive billing intelligence,
analytics, compliance, report-generation, scheduling, export,
source-health, and audit workspace.

The page must answer:

- What is the current financial position?
- What revenue remains outstanding?
- What revenue is at risk?
- What revenue has been denied?
- What revenue may be recovered?
- Which payer is creating delays?
- Which assigned agency requires attention?
- What compliance exposure exists?
- What Room & Board exposure exists?
- Which reports are available?
- Which reports are scheduled?
- Which reports were generated?
- Are the underlying data sources current?
- Who generated, downloaded, or scheduled each report?

The page must not duplicate operational work queues from source modules.

==================================================
REQUIRED PAGE SECTIONS
==================================================

1. Executive Financial Summary
2. Revenue Trend
3. Revenue Pipeline
4. Financial Risk Portfolio
5. Payer Performance
6. Agency Comparison
7. Compliance and Revenue Protection
8. Room & Board Financial Exposure Summary
9. Report Library
10. Custom Report Builder
11. Scheduled Reports
12. Saved Configurations
13. Generated Report History
14. Executive Report Package Verification
15. Data Source Health
16. AI Executive Insights
17. Platform Activity Audit Trail

All sections must match the approved Figma hierarchy.

==================================================
AGENCY SCOPE
==================================================

Supported scopes:

- Current Agency
- All Assigned Agencies

When Current Agency is selected:

- Executive totals include only the selected agency.
- Agency Comparison is informational only.
- Comparison results must not alter current-agency totals.

Display on Agency Comparison:

Comparison View Only
Not Included in Current Agency Totals

When All Assigned Agencies is selected:

- Include only agencies within the user's authorized assignment scope.
- Display included agency classifications.
- Do not silently combine Production, Training, and Demo data.
- Training and Demo agencies must remain visibly labeled.

Users must never access an unassigned agency through filters, URLs,
exports, report configurations, or direct API requests.

==================================================
TOP REPORTING CONTROLS
==================================================

Required controls:

- Agency Scope
- Reporting Period
- As-of Date
- Comparison Period
- Advanced Filters
- Apply Settings
- Generate Report
- Schedule
- Export Executive Package

Reporting period options should follow existing application conventions
and may include:

- Current Month
- Previous Month
- Current Quarter
- Previous Quarter
- Year to Date
- Previous Fiscal Year
- Custom Date Range

All metrics must visibly reflect the selected scope and period.

==================================================
EXECUTIVE FINANCIAL SUMMARY
==================================================

Required KPIs:

- Revenue Ready
- Revenue Submitted
- Revenue Received
- Outstanding AR
- Revenue At Risk
- Denied Revenue
- Recoverable Revenue
- Room & Board Advances

Each KPI must display:

- Authoritative amount
- Trend when available
- Reporting period
- As-of timestamp
- Drill-down destination

Required drill-down mappings:

- Revenue Ready → Billing Readiness
- Revenue Submitted → Claims Management
- Revenue Received → Payment Posting and Reconciliation
- Outstanding AR → AR and Collections Intelligence Center
- Revenue At Risk → Billing Readiness filtered to Revenue At Risk
- Denied Revenue → Denials and Appeals
- Recoverable Revenue → Denials and Appeals filtered to recovery opportunities
- Room & Board Advances → Room & Board Billing and Reimbursement Center

Drill-down must preserve:

- Agency scope
- Reporting period
- As-of date
- Comparison period
- Payer filter
- Applicable status filter

Do not implement separate conflicting KPI formulas on the Reports page.

Use the same authoritative calculation services as source modules.

==================================================
REVENUE TREND
==================================================

Display:

- Recognized Revenue
- Cash Collections

Required chart support:

- Reporting-period labels
- Dollar units
- Accessible legend
- Exact-value tooltips
- Selected agency scope
- Selected comparison period
- Last refreshed time

Do not rely on color alone to identify chart series.

Do not recreate static Figma chart values.

Use authoritative reporting-period data.

==================================================
REVENUE PIPELINE
==================================================

Required stages:

- Ready
- Submitted
- Accepted
- Payment Pending
- Paid
- Denied
- Appealed
- Recovered

Each stage must display:

- Revenue amount
- Claim count where supported
- Average days in stage
- Change from comparison period where supported

Submitted must remain distinct from Accepted.

Accepted must remain distinct from Paid.

Denied, Appealed, and Recovered must remain distinct.

==================================================
FINANCIAL RISK PORTFOLIO
==================================================

Required risk categories:

- Billing Blockers
- Eligibility
- NOE Deadline
- Denials
- Timely Filing
- Payment Variance
- Credit Balance
- CAP Exposure
- Room & Board Exposure
- DDE Exceptions

Each category must display:

- Financial amount
- Case count
- Risk level
- Trend where available
- Source module
- Drill-down action

Do not duplicate source-module work queues here.

==================================================
PAYER PERFORMANCE
==================================================

Required fields:

- Payer
- Average Payment Delay
- Payment or Collection Performance
- Denial Cases
- Denied Amount
- Performance Status

Where authoritative data supports it, also provide:

- Submitted Amount
- Billed Amount
- Received Amount
- Outstanding Amount
- Short-Payment Amount
- Recovery Amount
- Denial Rate

Support configured payer categories such as:

- Medicare
- Medi-Cal
- Medi-Cal Managed Care
- HMO
- Commercial
- Other configured payers

Payer drill-down must preserve selected filters.

==================================================
AGENCY COMPARISON
==================================================

Required disclaimer when Current Agency is selected:

Comparison View Only
Not Included in Current Agency Totals

Required fields:

- Agency
- Agency classification
- Revenue Ready
- Revenue Received
- Outstanding AR
- Revenue At Risk
- Denied Revenue
- NOE Compliance
- Performance status or trend

The comparison is agency-level operational intelligence.

Do not:

- Rank employees
- Score employee performance
- Include unassigned agencies
- Silently combine Production, Training, and Demo totals

==================================================
COMPLIANCE AND REVENUE PROTECTION
==================================================

Required indicators:

- NOE Compliance
- NOEs at Risk
- Eligibility Changes
- Claims Blocked
- DDE Exceptions
- CAP Exposure or Not Configured
- Credit Balance Cases
- Appeal Deadlines

Required state distinction:

- Verified zero
- Data available
- Current
- Stale
- Partial
- Unavailable
- Not Configured
- Access Denied

Not Configured must never be treated as zero risk.

==================================================
ROOM & BOARD FINANCIAL EXPOSURE
==================================================

Required metrics:

- Active Room & Board Cases
- Medi-Cal Received
- HMO Received
- Outstanding Reimbursement
- SNF Paid
- SNF Payable
- Hospice-Funded Advances
- Average Delay

Where supported, add:

- Awaiting Medi-Cal
- Awaiting HMO
- Oldest Outstanding Service Month

Use the shared Room & Board domain.

Do not create report-only Room & Board data or alternate calculations.

==================================================
REPORT LIBRARY
==================================================

Required categories:

- Revenue
- Claims
- Readiness
- Denials and Appeals
- Eligibility
- Payment Posting
- NOE
- CAP
- AR and Collections
- Credit Balance
- Room & Board
- Compliance
- Archived

Each report must display:

- Report name
- Description
- Source module
- Available format
- Last generated date
- Generate action
- Schedule action
- View history action

Do not display report formats that are not implemented.

==================================================
CUSTOM REPORT BUILDER
==================================================

Required controls:

- Report Name
- Report Type
- Agency Scope
- Reporting Period
- As-of Date
- Comparison Period
- Payer Segment
- Compliance Level
- Status Filter
- Aging Bucket
- Data Detail Modules
- Include Detail Rows
- Include Executive Summary
- Include Evidence Index
- File Format
- Sensitivity Level
- Estimated Row Count
- Minimum-Necessary Warning

Required actions:

- Preview Report
- Generate Report
- Save Configuration
- Schedule Report

Report generation and export must not be combined into one ambiguous action.

Preview must display:

- Agency scope
- Reporting period
- Filters
- Included sections
- Sensitivity level
- Estimated row count
- Source-health warnings

==================================================
SCHEDULED REPORTS
==================================================

Required fields:

- Report Name
- Schedule or Frequency
- Reporting Period
- Format
- Next Run
- Last Run
- Last Result
- Authorized Recipient or Destination
- Created By
- Status

Required statuses:

- Active
- Paused
- Failed
- Disabled

Required actions:

- View
- Edit
- Pause
- Resume
- Run Now
- Disable

Scheduled delivery must not send reports to unauthorized recipients.

==================================================
SAVED CONFIGURATIONS
==================================================

Required fields:

- Configuration Name
- Reporting Scope
- Output Mode
- Filters
- Created By
- Created Date
- Last Used
- Shared or Private
- Status

Required actions:

- Run
- Edit
- Duplicate
- Archive

Saved configurations store filters and layout preferences.

Saved configurations do not represent frozen financial results.

==================================================
GENERATED REPORT HISTORY
==================================================

Required fields:

- Report ID
- Report Name
- Agency Scope
- Reporting Period
- As-of Timestamp
- Generated By
- Generated Date
- Format
- Row Count
- Source Status
- Audit Status

Required actions:

- View
- Download
- Regenerate
- Audit Record

Rules:

- View and Download use the original immutable generated snapshot.
- Regenerate creates a new report from current source data.
- Regenerate must not replace or modify the original report.
- Every generation and download must be audited.

==================================================
EXECUTIVE REPORT PACKAGE
==================================================

Allow authorized users to assemble a package from selected reports.

Display:

- Included reports
- Agency scope
- Reporting period
- Output scope
- Data sensitivity
- Included detail level
- Package status
- Generated By
- Generation date

Required action:

Generate Executive Package

Human review is required before generating a package containing
protected financial or patient-level detail.

Additional approval is required when configured by organizational policy.

Do not impose universal dual-signature approval unless the organization
explicitly configures that requirement.

==================================================
DATA SOURCE HEALTH
==================================================

Required fields:

- Source Module
- Source Status
- Last Successful Refresh
- Freshness
- Error Reference
- Source Action
- Report Availability

Required statuses:

- Current
- Stale
- Unavailable
- Partial
- Not Configured

Required report effects:

- Report Available
- Report Available with Warning
- Report Blocked Due to Missing Source

Do not convert Unavailable, Stale, Partial, or Not Configured into zero.

Refresh or synchronization actions must be source-aware, permissioned,
tenant scoped, safe, and audited.

==================================================
AI EXECUTIVE INSIGHTS
==================================================

AI MAY:

- Summarize verified financial trends
- Highlight potential revenue risk
- Identify payer delays
- Identify growing AR exposure
- Identify denial trends
- Identify operational risk concentrations
- Recommend leadership review
- Recommend relevant reports
- Draft executive summaries

AI MAY NOT:

- Invent missing values
- Treat unavailable data as zero
- Certify financial statements
- Produce official cost reports
- Determine official CAP liability
- Approve write-offs
- Modify financial records
- Rank employees

Every AI insight must display:

- Agency scope
- As-of date
- Source modules
- Human Review Required

Use recommendation language:

- Potential Risk
- Observed Trend
- Recommended Review
- Possible Revenue Impact

==================================================
PLATFORM ACTIVITY AUDIT TRAIL
==================================================

Track:

- Report preview
- Report generation
- Report download
- Schedule creation
- Schedule modification
- Scheduled execution
- Saved-configuration change
- Executive-package generation
- Source-data refresh
- Export failure
- Recipient selection
- Agency-scope selection
- Audit-record access

Required fields:

- Actor
- Actor role
- Action
- Report or resource
- Agency scope
- Reporting period
- Timestamp
- Result
- Correlation ID

Audit history must be append-only.

==================================================
AUTHORIZATION FAILURE
==================================================

Authorization failure must replace the entire protected Reports workspace.

Do not display protected cards, charts, tables, reports, schedules, or
report history beneath an access warning.

Unauthorized users must not see:

- Financial totals
- Agency totals
- Patient counts
- Claim counts
- Payer performance
- Report history
- Saved configurations
- Scheduled reports
- Export information
- Unassigned tenant existence

Display only:

- Access Denied
- Safe explanation
- Authorized agency options where permitted
- Switch Agency
- Safe navigation
- Correlation ID

==================================================
LOADING, EMPTY, ERROR, AND STALE STATES
==================================================

Loading:

- Use skeletons preserving approved layout.
- Do not retain prior-agency data during agency switching.

Empty:

Support:

- No generated reports
- No scheduled reports
- No saved configurations
- No data for selected period

Error:

Display:

- Plain-language explanation
- Retry action
- Correlation ID

Do not display raw:

- Failed to fetch
- Network Error
- Stack trace
- Endpoint information

Stale:

Display:

- Last updated
- Source-health warning
- Refresh or Regenerate action

==================================================
REPOSITORY DISCOVERY REQUIREMENTS
==================================================

Before implementation, inspect:

- Existing /billing/reports route
- Existing Reports component tree
- Existing report APIs and services
- Existing export infrastructure
- Existing scheduled-job infrastructure
- Existing report configuration models
- Existing generated-file storage
- Existing audit infrastructure
- Existing tenant and agency authorization
- Existing shared financial calculation services
- Existing source-health infrastructure

Classify each relevant component as REUSE, EXTEND, REPLACE, or RETIRE.

Do not create a duplicate reporting engine when reusable infrastructure
already exists.

Do not create migrations before model discovery and schema mapping are
complete.

==================================================
REQUIRED LOGICAL ENTITIES
==================================================

Map to existing models before creating anything:

- Report Definition
- Report Configuration
- Saved Report Configuration
- Generated Report
- Generated Report Version
- Report Schedule
- Report Schedule Run
- Executive Report Package
- Executive Package Membership
- Report Source Snapshot
- Report Source Health
- Report Delivery
- Report Audit Event
- Report Authorization Scope

For each entity document: Existing Model, Existing Table, Decision,
Reason, Fields, Relationships, Constraints, Indexes, Migration
Required, Repository Evidence.

==================================================
IMPLEMENTATION ACCEPTANCE CRITERIA
==================================================

REPLACEMENT

□ Existing Reports page is replaced.
□ Existing Reports navigation opens Executive Billing Intelligence Center.
□ No parallel Reports page exists.
□ Obsolete snapshot-card implementation is retired after verification.
□ Existing reusable infrastructure is preserved.

SCOPE AND SECURITY

□ Current Agency totals include only current agency data.
□ Comparison data does not alter current-agency totals.
□ All Assigned Agencies includes assigned agencies only.
□ Production, Training, and Demo are visibly separated.
□ Authorization is enforced server-side.
□ Unauthorized state replaces the protected workspace.

FINANCIAL CONSISTENCY

□ Shared authoritative source calculations are used.
□ Reports page does not maintain alternate KPI formulas.
□ Same agency and as-of date reconcile with source modules.
□ Unavailable data is not represented as zero.
□ Refresh timestamps are visible.

REPORT OPERATIONS

□ Report Library is operational.
□ Report Builder is operational.
□ Preview is operational.
□ Report generation is operational.
□ Scheduled Reports are operational.
□ Saved Configurations are operational.
□ Generated Report History is operational.
□ Executive Package generation is operational.
□ Data Source Health is operational.

IMMUTABILITY

□ Generated reports remain immutable snapshots.
□ Regeneration creates a new report.
□ Historical reports are not rewritten.
□ Audit history is append-only.

AI GOVERNANCE

□ AI uses verified sources.
□ AI does not invent metrics.
□ AI does not certify financial conclusions.
□ Human review requirement is visible.

UI

□ Approved 17 sections are implemented.
□ No section-heading overlap exists.
□ Chart units and labels are visible.
□ Room & Board naming is correct.
□ Report History actions are clear.
□ Report Builder controls match approved Figma.
□ Responsive layout remains readable.
□ Figma parity is verified.

==================================================
IMPLEMENTATION BLOCKERS
==================================================

DO NOT DECLARE COMPLETE IF:

- Old Reports page remains accessible
- A second parallel Reports route is created
- Snapshot cards remain the primary Reports page
- Agency scope leaks data
- Comparison figures alter current-agency totals
- Training or Demo data is silently mixed with Production
- Reports use conflicting financial formulas
- Unavailable data appears as zero
- Generated reports can be overwritten
- Schedules can deliver to unauthorized recipients
- Authorization failure leaves financial data visible
- AI invents missing values
- Audit history is incomplete
- Report actions are not permission controlled
- Figma parity is incomplete
- Tests leave persistent artifacts

==================================================
REQUIRED VERIFICATION REPORT
==================================================

Update:

/docs/biller-platform/BILLER_PLATFORM_IMPLEMENTATION_VERIFICATION.md

Add: Executive Billing Intelligence Center Replacement Verification

Include:

- Existing Reports route identified
- Existing components reviewed
- REUSE / EXTEND / REPLACE / RETIRE decisions
- Files changed
- Models reused
- Models added
- Migrations added
- APIs added or changed
- Permissions enforced
- Source calculations reused
- Old page retirement evidence
- Agency-scope tests
- Report generation tests
- Schedule tests
- Export tests
- Immutable-history tests
- Audit tests
- Figma comparison
- Known limitations
- Confirmation no duplicate Reports page exists
- Confirmation no test artifacts remain

==================================================
FINAL STATUS
==================================================

Executive Billing Intelligence Center

APPROVED
LOCKED
READY FOR GITHUB IMPLEMENTATION

THIS PAGE REPLACES THE EXISTING BILLER PLATFORM REPORTS PAGE.

Proceed with repository discovery first.

Do not create schema or migrations until existing reporting models,
services, routes, exports, schedules, and audit infrastructure are
mapped.

==================================================
12. SHARED DATA AND CALCULATION RULES
==================================================

MONETARY VALUES

- Use fixed-precision decimal or numeric types.
- Never use floating-point arithmetic.
- Use one authoritative monetary source.
- Preserve currency.
- Preserve source transaction.
- Preserve reversals and corrections.

HEADLINE TOTALS

- Deduplicate by authoritative claim, billable episode, remittance, or payment unit.
- Do not count one claim multiple times because multiple blockers exist.
- Category totals may overlap only when the UI clearly discloses overlap.
- Every total must include an as-of timestamp.

REVENUE STATES

Keep distinct:

- Ready Revenue
- Blocked Revenue
- Revenue At Risk
- Revenue Released
- Submitted Revenue
- Accepted Revenue
- Paid Revenue
- Denied Revenue
- Recoverable Revenue
- Recovered Revenue
- Delayed Revenue

==================================================
13. IMMUTABILITY AND CORRECTION
==================================================

Do not delete or rewrite:

- Readiness evaluations
- Readiness conditions
- Claim lifecycle history
- Batch versions
- Batch membership history
- Batch exceptions
- Validation overrides
- DDE events
- Eligibility sweep history
- Coverage-change history
- Appeal versions
- Evidence-package history
- Payment events
- Variance history
- Revenue events
- Audit history

When a prior result is wrong:

1. Preserve the original.
2. Record correction reason.
3. Create a corrective or superseding record.
4. Link the new record to the original.
5. Recalculate current state.
6. Preserve actor and timestamp.

==================================================
14. AUDIT REQUIREMENTS
==================================================

Audit:

- Page access
- Agency selection
- Agency switching
- Exports
- Eligibility sweeps
- Coverage changes
- Eligibility manual review
- Claim validation
- Readiness evaluation
- Evidence addition
- Condition resolution
- DDE operations
- Claim generation
- Batch creation
- Batch review
- Batch revision
- Remove From Batch
- Return To Ready Queue
- Batch approval
- Batch submission
- Clearinghouse responses
- Denial creation
- Appeal draft generation
- Appeal approval
- Appeal submission
- Payment matching
- Payment posting
- Variance resolution
- Adjustment approval
- Secondary billing
- Unapplied cash resolution
- Manual overrides
- Revenue events

Every audit record must preserve:

- Actor
- Actor role
- Tenant
- Billing organization
- Action
- Source object
- Previous state when applicable
- New state when applicable
- Reason
- Timestamp
- Correlation ID
- Ruleset version when applicable
- Evidence reference when applicable

Never log credentials or secrets.

==================================================
15. REQUIRED TECHNICAL DELIVERABLES
==================================================

CREATE AND MAINTAIN:

/docs/biller-platform/BILLER_PLATFORM_DISCOVERY_REPORT.md

/docs/biller-platform/BILLER_PLATFORM_DATABASE_SCHEMA_AND_MIGRATION_PLAN.md

/docs/biller-platform/BILLER_PLATFORM_IMPLEMENTATION_TASK_BREAKDOWN.md

/docs/biller-platform/BILLER_PLATFORM_IMPLEMENTATION_VERIFICATION.md

==================================================
16. PHASED IMPLEMENTATION PLAN
==================================================

ONLY ONE PHASE MAY BE ACTIVE AT A TIME.

Maintain separate sections for:

- Completed Work
- Open Defects
- Verification Evidence
- Current Phase
- Next-Phase Queue

PHASE 0
Repository and Database Discovery

PHASE 1
Assignment and Access Foundation

PHASE 2
Individual DDE Authorization

PHASE 3
Authoritative Revenue Foundation

PHASE 4
Billing Readiness Engine

PHASE 5
Billing Readiness UI

PHASE 6
Billing Dashboard

PHASE 7
Claims Validation

PHASE 8
Claims Lifecycle and Clearinghouse Responses

PHASE 9
Batch Management

PHASE 10
Claims Management UI

PHASE 11
Denials and Appeals Engine

PHASE 12
Denials and Appeals UI

PHASE 13
Eligibility Monitoring Foundation

PHASE 14
Eligibility Scheduler and Sweep Processing

PHASE 15
Eligibility Monitoring UI

PHASE 16
Payment Posting and ERA Foundation

PHASE 17
Payment Reconciliation and Variance Engine

PHASE 18
Secondary Billing and Unapplied Cash

PHASE 19
Payment Posting UI

PHASE 20
Audit and Immutability Hardening

PHASE 21
Performance and Reliability

PHASE 22
Full Validation, Cleanup, Backup, and Restore

PHASE 23
Implementation Verification

==================================================
17. TEST REQUIREMENTS
==================================================

UNIT TESTS

- Revenue calculations
- Deduplication
- Readiness rules
- Claim validation
- Lifecycle transitions
- Batch versioning
- Remove From Batch
- Return To Ready Queue
- Override authority
- Appeal versioning
- Eligibility change comparison
- Eligibility work-item creation
- ERA matching
- Variance calculations
- Secondary-billing routing
- DDE condition mapping

INTEGRATION TESTS

- Assigned tenant access
- Unassigned tenant denial
- Tenant switching
- DDE-authorized user
- Non-DDE-authorized user
- Eligibility sweep
- Coverage-change propagation
- Readiness recalculation
- Claim generation
- Batch rebuild
- Clearinghouse response
- Appeal evidence package
- Payment posting
- Unapplied cash
- Cross-page total consistency
- Audit persistence

SECURITY TESTS

- URL manipulation
- Request-body substitution
- Query-parameter substitution
- Identifier enumeration
- Browser-storage tampering
- Cross-tenant cache
- Export scope
- Background-job scope
- Unauthorized financial workspace
- DDE scope bypass
- Secret leakage

UI TESTS

- Approved sections render
- Responsive layout
- Loading state
- Empty state
- Error state
- Stale-data warning
- Agency classification badge
- Authorized Scope
- Assigned Agency Registry
- DDE Health
- Batch actions
- Eligibility schedule
- Payment authorization replacement state
- Figma parity

==================================================
18. TEST DATA CLEANUP
==================================================

All test-created data must be:

- Tagged
- Isolated
- Traceable
- Removed during teardown

Tests must not leave:

- Test claims
- Test batches
- Test payments
- Test ERAs
- Test denials
- Test appeals
- Test eligibility sweeps
- Test coverage changes
- Test DDE events
- Test audit artifacts
- Test work items
- Debug records
- Temporary uploads

After test execution:

□ Verify teardown completed.
□ Verify no unexplained records remain.
□ Verify no orphaned records remain.
□ Verify no test files remain.
□ Verify database growth.
□ Document cleanup evidence.

==================================================
19. MIGRATION RULES
==================================================

For every migration:

PRE-MIGRATION

□ Verify database identity.
□ Verify current revision.
□ Verify expected head.
□ Verify single migration lineage.
□ Verify backup.
□ Capture affected row counts.
□ Review generated SQL.
□ Review locking risk.
□ Review data-rewrite risk.

POST-MIGRATION

□ Verify upgrade.
□ Verify ORM alignment.
□ Verify constraints.
□ Verify indexes.
□ Compare row counts.
□ Verify no records disappeared.
□ Verify tenant isolation.
□ Run focused tests.
□ Run schema-drift verification.
□ Remove test artifacts.
□ Record evidence.

PRODUCTION REPAIR

Do not use downgrade as the primary repair mechanism.

Do not use alembic stamp.

Use a forward-only corrective migration.

==================================================
20. UNAUTHORIZED STATE RULE
==================================================

When authorization fails, protected content must not render behind or below the warning.

Unauthorized state must replace the protected workspace.

This applies to:

- Dashboard
- Billing Readiness
- Claims
- Denials & Appeals
- Eligibility
- Payment Posting
- NOE Compliance
- CAP Compliance
- AR & Collections
- Credit Balance Resolution
- Room & Board Billing & Reimbursement (Biller Platform) / Room & Board Financial Reconciliation (Tenant Platform)
- Executive Billing Intelligence Center (Reports)
- All future Biller Platform pages

The unauthorized response must not expose:

- Financial totals
- Patient identifiers
- Claim information
- Agency financial information
- DDE details
- Payment information
- Denial information
- Eligibility results
- Existence of an unassigned tenant

==================================================
21. CROSS-PAGE CONSISTENCY
==================================================

The following must use shared authoritative sources:

- Ready Revenue
- Blocked Revenue
- Revenue At Risk
- Pending Payments
- Denied Revenue
- Recoverable Revenue
- DDE exception count
- Eligibility status
- Claim readiness
- Assigned agencies
- Current agency
- Assigned biller
- DDE authorization

Acceptance:

□ Same tenant and as-of point produce consistent totals.
□ Refresh timing is visible.
□ No page uses a hidden alternate formula.
□ Dashboard links open matching filtered workflows.
□ Eligibility changes update downstream workflows.
□ Payment posting updates dashboard revenue state.
□ Denial recovery updates recovery totals.
□ Resolving readiness updates Claims and Dashboard.

==================================================
22. COMPLETION BLOCKERS
==================================================

DO NOT DECLARE COMPLETE IF:

- Repository discovery is incomplete
- Logical entity mapping is incomplete
- Migration head is unknown
- Schema drift exists
- Duplicate models were created unnecessarily
- Revenue formulas conflict across pages
- Dashboard and Readiness totals conflict
- DDE is organization-wide instead of individually authorized
- Cross-tenant access exists
- Unauthorized financial data renders
- Batch history can be deleted
- Removed claims disappear
- Submitted batches can be silently edited
- Eligibility sources are fabricated
- Waystar is shown as connected without verification
- AI submits appeals automatically
- AI posts payments automatically
- Original blockers are overwritten
- Revenue uses floating-point arithmetic
- Mock financial values appear as production data
- Tests leave persistent artifacts
- Backup verification fails
- Restore verification fails
- Approved Figma sections are missing
- Clinical navigation returns
- Biller Platform branding does not use SNS Tech Solutions

==================================================
23. IMPLEMENTATION VERIFICATION REPORT
==================================================

CREATE:

/docs/biller-platform/BILLER_PLATFORM_IMPLEMENTATION_VERIFICATION.md

REQUIRED CONTENT

- Completed Work
- Open Defects
- Verification Evidence
- Current Phase
- Next-Phase Queue
- Files Changed
- Models Reused
- Models Extended
- Models Created
- Migrations Created
- Current Migration Head
- Constraints Added
- Indexes Added
- API Routes
- Permission Enforcement
- Revenue Formulas
- DDE Authorization
- DDE Readiness Mapping
- Claims Lifecycle
- Batch Versioning
- Clearinghouse Response Handling
- Appeal Draft Governance
- Eligibility Scheduler
- Eligibility Source Handling
- Coverage-Change Propagation
- Payment Matching
- Payment Variance Logic
- Secondary Billing
- Unapplied Cash
- Audit Events
- Tests Executed
- Test Results
- Backup Result
- Restore Result
- Test Cleanup Result
- Storage Impact
- Figma Comparison
- Cross-Page Reconciliation
- Cross-Tenant Isolation
- Known Limitations
- Deferred Enhancements

FINAL DECLARATIONS

□ No alembic stamp used.
□ No unsafe automigration accepted without review.
□ No historical migration rewritten.
□ No cross-tenant access found.
□ No unauthorized financial rendering found.
□ No test artifacts remain.
□ No mock values presented as live data.
□ All six pages match approved Figma.
□ DDE authorization is individually enforced.
□ Eligibility monitoring is scheduler enabled.
□ Payment AI requires human approval.
□ Appeal AI requires human approval.
□ Branding displays SNS Tech Solutions.
□ Assigned Agency Registry contains assigned agencies only.

==================================================
24. FINAL LOCKED DECISIONS
==================================================

SNS Tech Solutions Branding:
LOCKED

Biller Platform Ownership:
LOCKED

SNS Hospice Solutions Tenant Context:
LOCKED

North East Billing Center Naming:
LOCKED

Assignment-Based Visibility:
LOCKED

Individual DDE Authorization:
LOCKED

Billing Dashboard:
LOCKED

Billing Readiness:
LOCKED

Claims Management:
LOCKED

Denials & Appeals:
LOCKED

Eligibility Monitoring & Change Detection:
LOCKED

Payment Posting & Reconciliation Center:
LOCKED

NOE Compliance & Revenue Protection Center:
LOCKED

Claim Validation Intelligence:
LOCKED

Claim Lifecycle:
LOCKED

Batch Management:
LOCKED

Batch Removal and Return to Queue:
LOCKED

Immutable Batch Versioning:
LOCKED

AI Appeal Draft Governance:
LOCKED

Monthly Eligibility Monitoring:
LOCKED

Eligibility Work-Item Creation:
LOCKED

AI Reconciliation Governance:
LOCKED

Payment Authorization Replacement State:
LOCKED

NOE Compliance Monitoring:
LOCKED

AI NOE Risk Governance:
LOCKED

CAP Compliance & Financial Exposure Center:
LOCKED

AI CAP Risk Governance:
LOCKED

AR & Collections Intelligence Center:
LOCKED

AI Collections Governance:
LOCKED

Credit Balance Resolution & Compliance Center:
LOCKED

AI Credit Resolution Governance:
LOCKED

Room & Board Billing & Reimbursement Center (Biller Platform) /
Room & Board Financial Reconciliation Center (Tenant Platform):
LOCKED

AI Room & Board Governance:
LOCKED

Executive Billing Intelligence Center (Reports Replacement):
LOCKED

AI Executive Insights Governance:
LOCKED

Visits & Notes Removal:
LOCKED

POC & Certifications Removal:
LOCKED

==================================================
FINAL IMPLEMENTATION RULE
==================================================

Do not redesign during implementation.

Do not add unrelated features.

Do not create duplicate architecture.

Do not overwrite history.

Do not fabricate external connectivity.

Do not allow AI to perform unapproved financial or appeal actions.

Do not expose unassigned tenant information.

Do not leave test artifacts.

Verify first.

Implement one phase at a time.

Preserve evidence.

Preserve completed work.

Keep open defects separate.

Use forward-only corrections.

Future changes must be approved enhancements supported by verified implementation findings, field testing, or operational evidence.

---

## Status

APPROVED. LOCKED. Figma Design Complete. Implementation Authorized.
**This document explicitly replaces all earlier partial Biller
Platform handoff documents and is the sole current authority for
Biller Platform implementation.** Per its own header instruction, do
not patch or merge fragments from earlier versions into this file —
each of those earlier documents (see Relationship section below)
remains on disk as a superseded historical record, marked as such, but
is no longer authoritative.

Scope now spans **twelve locked pages** (Billing Dashboard, Billing
Readiness, Claims Management, Denials & Appeals, Eligibility
Monitoring & Change Detection, Payment Posting & Reconciliation
Center, NOE Compliance & Revenue Protection Center, CAP Compliance &
Financial Exposure Center, AR & Collections Intelligence Center,
Credit Balance Resolution & Compliance Center, Room & Board Billing &
Reimbursement Center (Biller Platform) / Room & Board Financial
Reconciliation Center (Tenant Platform), and new **Page 12: Executive
Billing Intelligence Center**), an 83-entity Discovery Deliverable
list (up from 69, adding Report Definition, Report Configuration,
Saved Report Configuration, Generated Report, Generated Report
Version, Report Schedule, Report Schedule Run, Executive Report
Package, Executive Package Membership, Report Source Snapshot, Report
Source Health, Report Delivery, Report Audit Event, and Report
Authorization Scope), the existing 24-phase Implementation Plan
(Phase 0-23), and an eighth AI-governance boundary (AI Executive
Insights) alongside the AI Appeal Draft Assistant (Denials & Appeals),
AI Reconciliation Assistant (Payment Posting), AI NOE Risk Analyzer
(NOE Compliance), AI CAP Analysis (CAP Compliance), AI Collections
Assistant (AR & Collections), AI Credit Resolution Assistant (Credit
Balance Resolution), and AI Room & Board Governance (Room & Board) —
in all eight cases AI may analyze/estimate/forecast/recommend/
summarize but a human must approve every compliance, financial,
refund, collections, allocation, payment, appeal-submission, or
executive-package action; AI Executive Insights is additionally and
explicitly barred from inventing missing values, treating unavailable
data as zero, certifying financial statements, producing official
cost reports, determining official CAP liability, approving
write-offs, modifying financial records, or ranking employees.

Page 12 is also the first page in this document framed as an explicit
**replacement of existing, already-shipped functionality** rather than
a new page: it replaces the existing Biller Platform Reports page at
the existing `/billing/reports` route (same navigation label,
"Reports"), and its Critical Replacement Directive forbids creating a
second/parallel Reports page, forbids keeping the old snapshot-card
Reports page accessible, and requires classifying existing Reports
code as REUSE, EXTEND, REPLACE, or RETIRE before any deletion — old
components may only be removed after replacement verification passes.
Its own Required Verification Report addendum ("Executive Billing
Intelligence Center Replacement Verification") must be added to
`docs/biller-platform/BILLER_PLATFORM_IMPLEMENTATION_VERIFICATION.md`
(Section 23), which has not yet been created.

Approval/lock status does not itself authorize code changes. Per
Section 10 (Verify-First Requirement), no schema, migration, API,
service, or UI work may begin until repository discovery is complete.

**State of the four Required Technical Deliverables (Section 15) as
of this document's creation:**

- `docs/biller-platform/BILLER_PLATFORM_DISCOVERY_REPORT.md` —
  created, but scoped to the original 25-entity list (three pages).
  Must be extended to cover the 58 additional entities introduced by
  this document for Denials & Appeals, Payment Posting &
  Reconciliation, NOE Compliance & Revenue Protection, CAP Compliance
  & Financial Exposure, AR & Collections Intelligence, Credit
  Balance Resolution & Compliance, Room & Board Billing &
  Reimbursement / Financial Reconciliation, and Executive Billing
  Intelligence Center (Denial, Appeal, Appeal Version, Appeal Evidence
  Package, Appeal Lifecycle Event, Eligibility Verification,
  Eligibility Sweep, Eligibility Sweep Result, Coverage Change,
  Eligibility Work Item, Verification Source, ERA or Remittance,
  Payment Posting, Payment Match, Payment Variance, Contractual
  Adjustment, Unapplied Cash, Secondary Billing Item, Payment Work
  Item, NOE Compliance Record, NOE Risk Assessment, NOE Filing Event,
  NOE Work Item, CAP Exposure Record, CAP Forecast Scenario, CAP
  Agency Utilization Snapshot, CAP Work Item, AR Aging Snapshot, AR
  Recovery Work Item, AR Collections Activity, Credit Balance Case,
  Credit Cause Record, CMS-838 Filing Case, Credit Resolution Work
  Item, RoomBoardCase, ServiceMonth, RoomBoardClaim, PayerRemittance,
  PaymentAllocation, SNFPayable, SNFPayment, HospiceFundedAdvance,
  ReconciliationRecord, FinancialSupportSchedule, Report Definition,
  Report Configuration, Saved Report Configuration, Generated Report,
  Generated Report Version, Report Schedule, Report Schedule Run,
  Executive Report Package, Executive Package Membership, Report
  Source Snapshot, Report Source Health, Report Delivery, Report Audit
  Event, and Report Authorization Scope) before Phase 0 can be
  considered complete for this document's full twelve-page scope. A
  standalone `ROOM_BOARD_DISCOVERY_REPORT.md` is separately required
  per Page 11's own Milestone 1 (Repository Discovery) before any Room &
  Board schema work begins.
- `docs/biller-platform/BILLER_PLATFORM_DATABASE_SCHEMA_AND_MIGRATION_PLAN.md`
  — created (prior session), scoped to the original entity set; will
  need a corresponding addendum once the expanded discovery matrix is
  approved.
- `docs/biller-platform/BILLER_PLATFORM_IMPLEMENTATION_TASK_BREAKDOWN.md`
  — created (prior session), with its own phase numbering; this
  document's Section 16 (24-phase plan, Phase 0-23) is the newer,
  more detailed authority and should be treated as superseding that
  file's phase numbering specifically, per Section 1's conflict-
  resolution rule (document the conflict, preserve verified work,
  use the smallest safe forward-only correction).
- `docs/biller-platform/BILLER_PLATFORM_IMPLEMENTATION_VERIFICATION.md`
  — **not yet created**; Phase 23 exit-gate deliverable, fully
  specified in Section 23 above.

## Relationship to Other Documents

- **Supersedes** the following four documents as the canonical Biller
  Platform implementation authority (each has been marked "Superseded"
  in its own Status section, pointing back here, but remains on disk
  as historical record per this session's established convention of
  never deleting prior dictated content):
  - `docs/biller-platform/BILLER_PLATFORM_FINAL_IMPLEMENTATION_BRIEF.md`
    (3 pages, no Denials & Appeals / Eligibility / Payment Posting)
  - `docs/biller-platform/BILLER_PLATFORM_IMPLEMENTATION_HANDOFF.md`
    (3 pages, first introduced Claims Management)
  - `docs/biller-platform/BILLER_PLATFORM_FINAL_CONSOLIDATED_HANDOFF.md`
    (3 pages, 25-entity list, 13 epics, 16-phase plan)
  - `docs/biller-platform/BILLER_PLATFORM_FINAL_IMPLEMENTATION_AUTHORIZATION.md`
    (5 pages, added Denials & Appeals and Eligibility Monitoring, plus
    the Financial Workspace Visibility Rule now restated and expanded
    here as the Authorization Failure Behavior / Unauthorized State
    Rule in Page 6 and Section 20)
- Restates and expands the branding, tenant-context, "North East
  Billing Center" naming, Clinical Boundary, and Assignment-Based
  Access rules first established in
  `docs/architecture/SNS_TECH_SOLUTIONS_PLATFORM_HIERARCHY.md` and
  carried through every prior Biller Platform handoff document — no
  change to those underlying decisions, only consolidation.
- Adds **Page 6: Payment Posting & Reconciliation Center** for the
  first time in any Biller Platform document — a full ERA/payment-
  matching/variance/secondary-billing/unapplied-cash operations center
  with its own AI Reconciliation Assistant (recommend-only; human
  approval required for all financial actions) and the same
  Authorization Failure Behavior pattern (replace the entire financial
  workspace on authorization failure) that was previously captured as
  a standalone "Financial Workspace Visibility Rule" fragment appended
  to `BILLER_PLATFORM_FINAL_IMPLEMENTATION_AUTHORIZATION.md`'s Locked
  Access Model — that fragment's true source section (Page 6,
  Authorization Failure Behavior) is now clear from this document.
- Expands the Denials & Appeals AI Appeal Draft Assistant boundary
  (from `BILLER_PLATFORM_FINAL_IMPLEMENTATION_AUTHORIZATION.md`) with
  explicit "AI may / AI may not" lists and a mandatory "AI Draft /
  Human Review Required" visible label — the same governance pattern
  is now applied to the new AI Reconciliation Assistant on Payment
  Posting.
- The 44-entity Discovery Deliverable list in Section 11 supersedes
  the 25-entity list from
  `BILLER_PLATFORM_FINAL_CONSOLIDATED_HANDOFF.md` §10, adding all
  Denials & Appeals and Payment Posting entities. The existing
  `BILLER_PLATFORM_DISCOVERY_REPORT.md` must be extended against this
  new list before Phase 0 is complete for the full six-page scope.
- The 24-phase Implementation Plan (Section 16, Phase 0-23) supersedes
  the 16-phase plan in `BILLER_PLATFORM_FINAL_CONSOLIDATED_HANDOFF.md`
  and the 18-phase breakdown in
  `BILLER_PLATFORM_IMPLEMENTATION_TASK_BREAKDOWN.md`, adding dedicated
  phases for Denials and Appeals (11-12), Eligibility Monitoring
  (13-15), and Payment Posting (16-19). NOE Compliance & Revenue
  Protection Center work is scoped within existing phases (NOE
  entities and UI fall under the Claims/Readiness-adjacent phases;
  this document does not introduce dedicated NOE phase numbers, and
  that gap should be resolved in the next Implementation Task
  Breakdown addendum).
- **Adds Page 7: NOE Compliance & Revenue Protection Center** — a
  proactive NOE-deadline/filing-compliance monitoring page with an AI
  NOE Risk Analyzer governed under the same recommend-only pattern as
  the AI Appeal Draft Assistant and AI Reconciliation Assistant (AI
  may analyze risk, estimate exposure, and create work items; AI may
  not submit NOEs, bypass validation, or override signatures/DDE
  rules). Adds four entities to the Required Discovery Deliverable
  list: NOE Compliance Record, NOE Risk Assessment, NOE Filing Event,
  NOE Work Item.
- **Adds Page 8: CAP Compliance & Financial Exposure Center** — an
  operational monitoring/forecasting page for aggregate hospice cap
  exposure, explicitly not an official CAP calculator (official
  determinations remain dependent on NGS PS&R Reports and official
  Medicare Cap Reports). Its AI CAP Analysis boundary follows the same
  recommend-only pattern as the other three AI assistants, with an
  additional explicit prohibition on AI producing official Medicare
  cap liability determinations, compliance certifications, or refund
  calculations. Adds four entities to the Required Discovery
  Deliverable list: CAP Exposure Record, CAP Forecast Scenario, CAP
  Agency Utilization Snapshot, CAP Work Item.
- **Adds Page 9: AR & Collections Intelligence Center** — an
  operational collections and revenue-recovery center (explicitly not
  a passive/traditional aging report), prioritizing the Recovery
  Prioritization Queue, timely-filing risk detection, and automated
  recovery-work-item creation over static reporting. Its AI
  Collections Assistant follows the same recommend-only pattern as the
  other four AI assistants (draft-only recovery strategies and
  work-item plans; no automatic write-offs, receivable adjustments, or
  collection actions). Adds three entities to the Required Discovery
  Deliverable list: AR Aging Snapshot, AR Recovery Work Item, AR
  Collections Activity.
- **Adds Page 10: Credit Balance Resolution & Compliance Center** — a
  credit-balance investigation/resolution/CMS-838-compliance center
  (explicitly not a reporting screen), with a full Credit Balance
  Lifecycle (Credit Identified → Investigation → Validation → Refund
  Review → CMS-838 Review → Resolved → Closed, where Resolved does not
  automatically mean Closed and refund issuance does not automatically
  close the investigation), a Refund Governance rule (recommend/flag/
  generate-work-item only; no automatic issuance, approval, or case
  closure), a CMS-838 Workflow (Candidate → Under Review → Draft
  Prepared → Ready For Filing → Submitted → Accepted → Follow-Up
  Required → Closed, fully auditable with historical filings remaining
  viewable), and an Authorization Failure Behavior rule matching the
  Payment Posting pattern (replace the entire workspace; no financial
  or patient data exposed to unauthorized users). Its AI Credit
  Resolution Assistant follows the same recommend-only pattern as the
  other five AI assistants, with required non-conclusive language
  ("Potential Resolution Candidate", "Likely Resolution Path",
  "Recommended Review", "Estimated Compliance Concern") and an
  explicit prohibition on determining official compliance outcomes,
  issuing refunds, adjusting balances, closing credit cases, or
  submitting CMS-838 filings. Adds four entities to the Required
  Discovery Deliverable list: Credit Balance Case, Credit Cause
  Record, CMS-838 Filing Case, Credit Resolution Work Item.
- **Adds Page 11: Room & Board Billing & Reimbursement Center
  (Biller Platform) / Room & Board Financial Reconciliation Center
  (SNS Hospice Solutions Tenant Platform)** — a single shared-data-
  model workflow for dual-eligible hospice patients in SNFs/
  facilities, exposed as two platform-specific views (Biller
  operational billing/reimbursement view; Tenant financial exposure/
  reconciliation view) that must read from the same authoritative
  records (RoomBoardCase, ServiceMonth, RoomBoardClaim,
  PayerRemittance, PaymentAllocation, SNFPayable, SNFPayment,
  HospiceFundedAdvance, ReconciliationRecord,
  FinancialSupportSchedule) — an explicit Critical Architecture Rule
  forbids building two separate systems or duplicating patients,
  facilities, service months, claims, reimbursements, allocations,
  payables, payments, or reconciliation records across the two
  platforms. Includes a 7-milestone Room & Board Implementation
  Milestones plan (Repository Discovery producing a standalone
  `ROOM_BOARD_DISCOVERY_REPORT.md`; Shared Data Foundation; Biller
  Platform page; Tenant Platform page; Shared Reconciliation Engine;
  Audit Framework; Reporting Support) and an Epic Summary
  (Business Owner: SNS Hospice Solutions; Technical Owner: SNS Tech
  Solutions; Priority: HIGH) explicitly distinguishing this workflow
  from Facility Collections ("THIS IS NOT FACILITY COLLECTIONS. THIS
  IS ROOM & BOARD REIMBURSEMENT RECONCILIATION."). Its AI Room &
  Board Governance follows the same recommend-only pattern as the
  other six AI assistants (may identify missing reimbursements,
  recommend follow-up, identify allocation patterns, suggest disputes,
  draft appeals/correspondence, summarize reconciliation history; may
  not submit claims, record payments, allocate payments automatically,
  approve payables, issue SNF payments, modify financial records, or
  close cases). The Annual Reporting Support (Financial Support
  Schedule) is explicitly not an official completed Medicare Cost
  Report. Adds ten entities to the Required Discovery Deliverable
  list: RoomBoardCase, ServiceMonth, RoomBoardClaim, PayerRemittance,
  PaymentAllocation, SNFPayable, SNFPayment, HospiceFundedAdvance,
  ReconciliationRecord, FinancialSupportSchedule. 16 UI design
  reference screenshots for this and other already-documented pages
  were saved to session storage as implementation reference (light-
  theme JSX/Tailwind versions to follow before implementation begins).
- **Adds Page 12: Executive Billing Intelligence Center** — a
  **replacement** of the existing Biller Platform Reports page at the
  existing `/billing/reports` route, not a net-new nav item ("Reports"
  was already an approved Section 7 nav label). Governed by a
  Critical Replacement Directive: no parallel/second Reports page, no
  continued access to the old snapshot-card implementation once
  replaced, and every existing Reports-related file classified as
  REUSE, EXTEND, REPLACE, or RETIRE (distinct from the REUSE/EXTEND/
  CREATE scheme used for net-new pages) before any deletion. Specifies
  17 required sections (Top Reporting Controls, Executive Financial
  Summary with drill-down mappings, Revenue Trend, Revenue Pipeline,
  Financial Risk Portfolio, Payer Performance, Agency Comparison,
  Compliance and Revenue Protection, Room & Board Financial Exposure,
  Report Library, Custom Report Builder, Scheduled Reports, Saved
  Configurations, Generated Report History, Executive Report Package,
  Data Source Health, AI Executive Insights, and Platform Activity
  Audit Trail), Agency Scope rules, Authorization Failure behavior
  (full workspace replacement, consistent with prior pages), and
  Loading/Empty/Error/Stale states. AI Executive Insights follows the
  same recommend-only governance pattern as the other seven AI
  assistants, with additional explicit prohibitions on inventing
  missing values, treating unavailable data as zero, certifying
  financial statements, producing official cost reports, determining
  official CAP liability, approving write-offs, modifying financial
  records, or ranking employees. Adds 14 entities to the Required
  Discovery Deliverable list: Report Definition, Report Configuration,
  Saved Report Configuration, Generated Report, Generated Report
  Version, Report Schedule, Report Schedule Run, Executive Report
  Package, Executive Package Membership, Report Source Snapshot,
  Report Source Health, Report Delivery, Report Audit Event, and
  Report Authorization Scope. Requires its own addendum to a not-yet-
  created `BILLER_PLATFORM_IMPLEMENTATION_VERIFICATION.md` (Section
  23) documenting Reports-replacement verification before any old
  Reports code may be retired.

## Change Log

| Date | Change |
|---|---|
| 2026-09-17 | Document created — Final Consolidated Implementation Handoff superseding all prior Biller Platform handoff documents. Full 24-section authority covering six locked pages (Billing Dashboard, Billing Readiness, Claims Management, Denials & Appeals, Eligibility Monitoring & Change Detection, and new Payment Posting & Reconciliation Center), Implementation Authority, Global Platform Architecture, Locked Branding, Billing Organization Naming, Core Mission, Clinical Boundary, Final Approved Navigation, Assignment-Based Access, DDE Architecture, Verify-First Requirement, a 44-entity Required Discovery Deliverable list, per-page missions/sections/acceptance-criteria for all six pages (including the new AI Appeal Draft Assistant and AI Reconciliation Assistant governance boundaries and the Authorization Failure Behavior / Unauthorized State Rule), Shared Data and Calculation Rules, Immutability and Correction, Audit Requirements, Required Technical Deliverables, a 24-phase Phased Implementation Plan (Phase 0-23), Test Requirements, Test Data Cleanup, Migration Rules, Unauthorized State Rule, Cross-Page Consistency, Completion Blockers, Implementation Verification Report specification, Final Locked Decisions, and Final Implementation Rule. Documentation only; no schema, migrations, tables, or models created. |
| 2026-09-17 | Added Page 7: NOE Compliance & Revenue Protection Center (Executive NOE Compliance Overview, Active NOE Risk Screening Queue, AI NOE Risk Analyzer, Compliance Timeline / 5-Day Rule, NOE Action Item Work Queue, Agency Compliance Tracking, Filing Delay Root Cause Analysis, Auto-Generated Work Tasks, and NOE Compliance Acceptance Criteria). Updated Approved Pages to seven; added NOE Compliance Record, NOE Risk Assessment, NOE Filing Event, and NOE Work Item to the Required Discovery Deliverable list (now 48 entities); added NOE Compliance to the Section 20 Unauthorized State Rule page list; added NOE Compliance & Revenue Protection Center and AI NOE Risk Governance to Section 24 Final Locked Decisions. Documentation only; no schema, migrations, tables, or models created. The existing BILLER_PLATFORM_DISCOVERY_REPORT.md still needs a follow-up addendum for all newly-introduced entities across Pages 4-7 before Phase 0 can be considered complete for the full seven-page scope. |
| 2026-09-17 | Added Page 8: CAP Compliance & Financial Exposure Center (Executive CAP Exposure Overview, CAP Accumulation & Limit Proximity Forecast, Multi-Agency CAP Exposure Matrix, AI Compliance Risk Projections, CAP Driver Analysis, Operational Scenario Modeling, CAP Work Queue, Historical CAP Reconciliation Logs, and CAP Acceptance Criteria). This page is explicitly an operational monitoring/forecasting tool only — it is not an official CAP calculator, and official CAP determinations remain dependent on NGS PS&R Reports, official Medicare Cap Reports, and other approved reimbursement sources; the AI CAP Analysis boundary explicitly forbids AI from determining official Medicare cap liability, certifying compliance, or producing official refund calculations. Updated Approved Pages to eight; added CAP Exposure Record, CAP Forecast Scenario, CAP Agency Utilization Snapshot, and CAP Work Item to the Required Discovery Deliverable list (now 52 entities); added CAP Compliance to the Section 20 Unauthorized State Rule page list; added CAP Compliance & Financial Exposure Center and AI CAP Risk Governance to Section 24 Final Locked Decisions. Documentation only; no schema, migrations, tables, or models created. The existing BILLER_PLATFORM_DISCOVERY_REPORT.md still needs a follow-up addendum for all newly-introduced entities across Pages 4-8 before Phase 0 can be considered complete for the full eight-page scope. |
| 2026-09-17 | Added Page 9: AR & Collections Intelligence Center (Executive AR Summary, Recovery Prioritization Queue, Top Collection Risks, AI Collections Assistant, Payer Aging Analysis Matrix, Agency Performance & Aging Summary, Aging Work Queue, Historical Collections & Write-Off Ledger, Auto Work Item Creation, Assignment Model, Audit Requirements, Acceptance Criteria, Implementation Notes, and Final Status). Explicitly framed as an operational collections and revenue recovery center, not a passive/traditional aging report — Implementation Notes direct that Recovery Prioritization Queue, Timely Filing Risk Detection, Aging Work Queue, Payer/Agency Risk Analysis, and Automated Recovery Work Item Creation take priority over static reporting. AI Collections Assistant follows the same recommend-only governance pattern as the other four AI assistants (may identify risks/patterns and draft recovery strategies and work-item plans; may not write off balances, modify receivables/accounts, change financial values, or perform collection actions) and the specification directs replacing automated-sounding action labels (e.g. "Auto Collection Execution", "Automated Write-Offs") with recommendation language (e.g. "Generate Collection Strategy", "Generate Recovery Recommendations"). Updated Approved Pages to nine; added AR Aging Snapshot, AR Recovery Work Item, and AR Collections Activity to the Required Discovery Deliverable list (now 55 entities); added AR & Collections to the Section 20 Unauthorized State Rule page list; added AR & Collections Intelligence Center and AI Collections Governance to Section 24 Final Locked Decisions. Documentation only; no schema, migrations, tables, or models created. The existing BILLER_PLATFORM_DISCOVERY_REPORT.md still needs a follow-up addendum for all newly-introduced entities across Pages 4-9 before Phase 0 can be considered complete for the full nine-page scope. |
| 2026-09-17 | Added Page 10: Credit Balance Resolution & Compliance Center (Executive Credit Exposure, Credit Resolution Queue, Credit Cause Analysis, AI Credit Resolution Assistant, CMS-838 Compliance Center, Credit Aging Analysis, Multi-Agency Credit Exposure, Auto-Created Work Items, Credit Balance Lifecycle, Refund Governance, CMS-838 Workflow, Authorization Failure Behavior, Acceptance Criteria, and Final Status — APPROVED / LOCKED / IMPLEMENTATION AUTHORIZED). Explicitly framed as a resolution/compliance center, not a reporting screen. Credit Balance Lifecycle (Credit Identified → Investigation → Validation → Refund Review → CMS-838 Review → Resolved → Closed) establishes that Resolved does not automatically mean Closed and refund issuance does not automatically close the investigation. Refund Governance and CMS-838 Workflow require human authorization and full auditability with historical filings remaining viewable. Authorization Failure Behavior mirrors the Payment Posting pattern (replace the entire workspace on authorization failure; no financial or patient credit data exposed). AI Credit Resolution Assistant follows the same recommend-only governance pattern as the other five AI assistants, using required non-conclusive language and an explicit prohibition on determining compliance outcomes, issuing refunds, adjusting balances, closing credit cases, or submitting CMS-838 filings. Updated Approved Pages to ten; added Credit Balance Case, Credit Cause Record, CMS-838 Filing Case, and Credit Resolution Work Item to the Required Discovery Deliverable list (now 59 entities); added Credit Balance Resolution to the Section 20 Unauthorized State Rule page list; added Credit Balance Resolution & Compliance Center and AI Credit Resolution Governance to Section 24 Final Locked Decisions. Documentation only; no schema, migrations, tables, or models created. The existing BILLER_PLATFORM_DISCOVERY_REPORT.md still needs a follow-up addendum for all newly-introduced entities across Pages 4-10 before Phase 0 can be considered complete for the full ten-page scope. |
| 2026-09-17 | Added Page 11: Room & Board Billing & Reimbursement Center (Biller Platform) / Room & Board Financial Reconciliation Center (SNS Hospice Solutions Tenant Platform) — a single shared-data-model workflow, two platform-specific views, governed by an explicit Critical Architecture Rule against duplicated data or two separate systems. Includes Business Purpose, Shared Authoritative Records, Master Room & Board Case Status, full Biller Platform page spec (KPI cards, Monthly Billing Queue, Claim Validation Status, Payer Reimbursement Queue, Payment Allocation, Payer Follow-Up Queue, Service Month Matrix), full Tenant page spec (KPI cards, Hospice-Funded Pass-Through Advances, Facility SNF Disbursements, Payer Reimbursement Aging, Service Month Reconciliation Ledger, SNF Payable/Payment Status, Reconciliation Status, Annual Reporting Support), Audit Requirements, Authorization Rules (with Access Denied full-workspace-replacement behavior), AI Governance, Acceptance Criteria, an Epic Summary (Business Owner: SNS Hospice Solutions; Technical Owner: SNS Tech Solutions; Priority: HIGH; explicitly distinguished from Facility Collections) with its own Epic Implementation Checklist and Implementation Mandate, and a 7-milestone Room & Board Implementation Milestones plan (Repository Discovery → Shared Data Foundation → Biller Platform → Tenant Platform → Shared Reconciliation Engine → Audit Framework → Reporting Support) with field-level schemas for all ten new entities. Updated Approved Pages to eleven; added RoomBoardCase, ServiceMonth, RoomBoardClaim, PayerRemittance, PaymentAllocation, SNFPayable, SNFPayment, HospiceFundedAdvance, ReconciliationRecord, and FinancialSupportSchedule to the Required Discovery Deliverable list (now 69 entities); added Room & Board Billing & Reimbursement / Financial Reconciliation to the Section 20 Unauthorized State Rule page list; added Room & Board Billing & Reimbursement Center (Biller Platform) / Room & Board Financial Reconciliation Center (Tenant Platform) and AI Room & Board Governance to Section 24 Final Locked Decisions. 16 UI design reference screenshots (covering this and other already-documented pages) saved to session storage as implementation reference pending a future light-theme JSX/Tailwind resend. Documentation only; no schema, migrations, tables, or models created. A standalone ROOM_BOARD_DISCOVERY_REPORT.md is separately required per Page 11's own Milestone 1 before any Room & Board schema work begins. The existing BILLER_PLATFORM_DISCOVERY_REPORT.md still needs a follow-up addendum for all newly-introduced entities across Pages 4-11 before Phase 0 can be considered complete for the full eleven-page scope. |
| 2026-09-17 | Added Page 12: Executive Billing Intelligence Center — an explicit replacement of the existing Biller Platform Reports page at the existing `/billing/reports` route (not a net-new nav item), governed by a Critical Replacement Directive prohibiting any parallel Reports page and requiring REUSE/EXTEND/REPLACE/RETIRE classification of existing Reports code before deletion. Specifies 17 required sections (Top Reporting Controls, Executive Financial Summary with drill-down mappings, Revenue Trend, Revenue Pipeline, Financial Risk Portfolio, Payer Performance, Agency Comparison, Compliance and Revenue Protection, Room & Board Financial Exposure, Report Library, Custom Report Builder, Scheduled Reports, Saved Configurations, Generated Report History, Executive Report Package, Data Source Health, AI Executive Insights, and Platform Activity Audit Trail), Agency Scope rules, Authorization Failure behavior (full workspace replacement), Loading/Empty/Error/Stale states, Repository Discovery Requirements, Implementation Acceptance Criteria, Implementation Blockers, and Required Verification Report update instructions. AI Executive Insights follows the same recommend-only governance pattern as the other seven AI assistants, with additional prohibitions on inventing missing values, treating unavailable data as zero, certifying financial statements, producing official cost reports, determining official CAP liability, approving write-offs, modifying financial records, or ranking employees. Updated Approved Pages to twelve; added Report Definition, Report Configuration, Saved Report Configuration, Generated Report, Generated Report Version, Report Schedule, Report Schedule Run, Executive Report Package, Executive Package Membership, Report Source Snapshot, Report Source Health, Report Delivery, Report Audit Event, and Report Authorization Scope to the Required Discovery Deliverable list (now 83 entities); added Executive Billing Intelligence Center (Reports) to the Section 20 Unauthorized State Rule page list; added Executive Billing Intelligence Center (Reports Replacement) and AI Executive Insights Governance to Section 24 Final Locked Decisions. Documentation only; no schema, migrations, tables, or models created. The existing BILLER_PLATFORM_DISCOVERY_REPORT.md still needs a follow-up addendum for all newly-introduced entities across Pages 4-12 before Phase 0 can be considered complete for the full twelve-page scope. Page 12 additionally requires a new BILLER_PLATFORM_IMPLEMENTATION_VERIFICATION.md (not yet created) documenting Reports-replacement verification before old Reports code may be retired. |
