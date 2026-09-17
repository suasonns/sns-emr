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

Scope now spans **six locked pages** (Billing Dashboard, Billing
Readiness, Claims Management, Denials & Appeals, Eligibility
Monitoring & Change Detection, and new **Payment Posting &
Reconciliation Center**), a 44-entity Discovery Deliverable list (up
from 25), a 24-phase Implementation Plan (Phase 0-23, up from 16), and
new AI-governance boundaries for both appeal drafting (Denials &
Appeals) and payment reconciliation recommendations (Payment Posting)
— in both cases AI may analyze/draft/recommend but a human must
approve every financial or appeal-submission action.

Approval/lock status does not itself authorize code changes. Per
Section 10 (Verify-First Requirement), no schema, migration, API,
service, or UI work may begin until repository discovery is complete.

**State of the four Required Technical Deliverables (Section 15) as
of this document's creation:**

- `docs/biller-platform/BILLER_PLATFORM_DISCOVERY_REPORT.md` —
  created, but scoped to the prior 25-entity list (three pages). Must
  be extended to cover the 19 additional entities introduced by this
  document for Denials & Appeals and Payment Posting & Reconciliation
  (Denial, Appeal, Appeal Version, Appeal Evidence Package, Appeal
  Lifecycle Event, Eligibility Verification, Eligibility Sweep,
  Eligibility Sweep Result, Coverage Change, Eligibility Work Item,
  Verification Source, ERA or Remittance, Payment Posting, Payment
  Match, Payment Variance, Contractual Adjustment, Unapplied Cash,
  Secondary Billing Item, Payment Work Item) before Phase 0 can be
  considered complete for this document's full six-page scope.
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
  (13-15), and Payment Posting (16-19).

## Change Log

| Date | Change |
|---|---|
| 2026-09-17 | Document created — Final Consolidated Implementation Handoff superseding all prior Biller Platform handoff documents. Full 24-section authority covering six locked pages (Billing Dashboard, Billing Readiness, Claims Management, Denials & Appeals, Eligibility Monitoring & Change Detection, and new Payment Posting & Reconciliation Center), Implementation Authority, Global Platform Architecture, Locked Branding, Billing Organization Naming, Core Mission, Clinical Boundary, Final Approved Navigation, Assignment-Based Access, DDE Architecture, Verify-First Requirement, a 44-entity Required Discovery Deliverable list, per-page missions/sections/acceptance-criteria for all six pages (including the new AI Appeal Draft Assistant and AI Reconciliation Assistant governance boundaries and the Authorization Failure Behavior / Unauthorized State Rule), Shared Data and Calculation Rules, Immutability and Correction, Audit Requirements, Required Technical Deliverables, a 24-phase Phased Implementation Plan (Phase 0-23), Test Requirements, Test Data Cleanup, Migration Rules, Unauthorized State Rule, Cross-Page Consistency, Completion Blockers, Implementation Verification Report specification, Final Locked Decisions, and Final Implementation Rule. Documentation only; no schema, migrations, tables, or models created. |
