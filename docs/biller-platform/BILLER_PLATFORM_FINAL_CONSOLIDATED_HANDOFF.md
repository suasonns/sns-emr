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

PAGES INCLUDED

1. Billing Dashboard
2. Billing Readiness
3. Claims Management

No architectural redesign is authorized during implementation.

Future changes must be approved enhancements based on verified operational needs or field-testing evidence.

==================================================
1. GLOBAL PLATFORM ARCHITECTURE
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

LOCKED BRANDING

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

Agency classifications:

- Production
- Training
- Demo

==================================================
2. CORE BILLER PLATFORM MISSION
==================================================

The Biller Platform exists to:

- Find revenue
- Protect revenue
- Unlock revenue
- Submit compliant claims
- Recover denied revenue
- Monitor payment
- Manage DDE-related billing work
- Preserve billing evidence
- Preserve audit history
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
9. What affects cash flow?
10. What DDE issue requires attention?

==================================================
3. CLINICAL BOUNDARY
==================================================

The Biller Platform must not become a clinical chart-management platform.

DO NOT REINTRODUCE:

- Visits & Notes navigation
- POC & Certifications navigation
- Clinical chart-management screens
- Clinical note editing
- Clinical assessment editing
- Patient-care workflow management

Billing may consume clinical status outcomes such as:

- Certification complete or missing
- Face-to-face complete or missing
- Physician order signed or missing
- Required documentation complete or missing
- Clinical audit completed

Billing users may:

- See the billing consequence
- See revenue impact
- See the accountable department
- Request correction
- Assign follow-up
- Escalate
- Revalidate after correction

Billing users may not falsely complete clinical or physician responsibilities.

==================================================
4. ASSIGNMENT-BASED ACCESS
==================================================

LOCKED RULE

Visibility follows assignment.

Access follows assignment.

Responsibility follows assignment.

A biller may see only:

- Billing organizations where the user has active membership
- Agencies assigned to that billing organization
- Agencies assigned to the individual user when individual assignment applies
- Claims and billing records belonging to those agencies
- DDE operations for which the individual user is authorized

Assignment must be enforced server-side.

Client-side filtering is not sufficient.

The system must reject unauthorized access attempted through:

- URL modification
- Query parameter modification
- Request-body modification
- Browser-storage modification
- Identifier enumeration
- Cached results
- Export requests
- Background jobs
- Direct API requests

The system must not reveal whether an unassigned agency exists.

==================================================
5. DDE ARCHITECTURE
==================================================

DDE is required.

DDE is not a future enhancement.

DDE is a core Biller Platform workflow.

DDE authorization belongs to an individual person operating inside an authorized billing group.

The Biller Platform must distinguish:

1. Billing organization membership
2. Tenant assignment to billing organization
3. Individual biller assignment
4. Individual DDE authorization
5. DDE authorization for a specific assigned tenant

Do not treat DDE authorization as automatically belonging to the entire billing organization.

Do not store plaintext DDE passwords.

Do not expose DDE credentials through:

- UI
- Logs
- Exports
- Telemetry
- Error messages
- Audit events
- Database fields not specifically approved for secure secret storage

==================================================
6. APPROVED NAVIGATION
==================================================

KEEP:

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

REMOVE:

- Visits & Notes
- POC & Certifications

Do not create replacement clinical-navigation entries.

==================================================
7. APPROVED BILLING ORGANIZATION NAME
==================================================

STANDARD NAME

North East Billing Center

Use this name consistently across:

- UI
- Assigned Visibility
- Authorized Scope
- Reports
- Exports
- Audit events
- Configuration
- Figma references
- GitHub specifications
- Test fixtures where applicable

Do not alternate between:

North East Billing

and

North East Billing Center

==================================================
8. IMPLEMENTATION AUTHORITY
==================================================

The approved Figma designs are the visual authority.

This document is the architecture, workflow, security, data, calculation, and acceptance authority.

Existing verified repository functionality remains the implementation authority when it does not conflict with the locked requirements.

If a conflict exists:

1. Document the conflict.
2. Preserve working functionality.
3. Identify the exact requirement affected.
4. Use the smallest forward-only correction.
5. Do not silently redesign or reinterpret the approved workflow.

==================================================
9. VERIFY-FIRST REQUIREMENT
==================================================

Before implementation:

□ Verify repository root.
□ Verify active branch and worktree.
□ Verify clean or intentionally dirty working tree.
□ Verify database identity.
□ Verify environment-file selection.
□ Verify PostgreSQL connection target.
□ Verify current Alembic revision.
□ Verify expected Alembic head.
□ Verify migration lineage.
□ Verify ORM and database alignment.
□ Verify existing routes.
□ Verify existing authorization.
□ Verify existing tenant-assignment logic.
□ Verify existing billing models.
□ Verify existing claim models.
□ Verify existing readiness models.
□ Verify existing audit models.
□ Verify existing evidence-provenance models.
□ Verify existing DDE models or placeholders.
□ Verify current Figma implementation surface.

Do not create migrations until discovery is complete.

==================================================
10. REQUIRED DISCOVERY DELIVERABLE
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

Do not fabricate repository model names.

==================================================
GITHUB EPIC 01
BILLER PLATFORM ACCESS FOUNDATION
==================================================

PURPOSE

Establish secure assignment-based access before implementing financial or patient-linked workflows.

CHILD ISSUES

01.1 Billing organization model or extension

01.2 Billing organization membership

01.3 Tenant billing assignment

01.4 Individual tenant biller assignment

01.5 Assigned-agency selector

01.6 Assigned Agency Registry

01.7 Agency classification badges

01.8 Server-side authorization guards

01.9 Tenant-aware cache isolation

01.10 Tenant-switch audit logging

ACCEPTANCE CRITERIA

□ Users see only agencies assigned to the authorized billing organization.
□ Individual assignment is enforced where required.
□ An expired assignment removes future access.
□ Ending an assignment does not delete historical activity.
□ URL manipulation cannot expose another tenant.
□ Request-body substitution cannot expose another tenant.
□ Query-parameter substitution cannot expose another tenant.
□ Agency switching clears all previously displayed tenant data.
□ Cache keys contain tenant and permission scope.
□ Exports include only the active authorized tenant.
□ Assigned Agency Registry never displays unassigned agencies.
□ Agency classifications display Production, Training, or Demo.
□ The page displays SNS Tech Solutions and Biller Platform.
□ Tenant context displays SNS Hospice Solutions Tenant.
□ Access and agency-switch activity is audited.

DEPENDENCIES

- Repository Discovery
- Existing authentication system
- Existing tenant authority

==================================================
GITHUB EPIC 02
INDIVIDUAL DDE AUTHORIZATION
==================================================

PURPOSE

Enable DDE operations for individually authorized billers inside an authorized billing group.

CHILD ISSUES

02.1 DDE user-profile model or extension

02.2 DDE tenant authorization

02.3 DDE authorization states

02.4 DDE Authorized display

02.5 DDE permission guards

02.6 DDE status and exception audit events

02.7 DDE revocation and expiration

02.8 DDE security tests

ACCEPTANCE CRITERIA

□ DDE authorization belongs to an individual user.
□ The user has active billing-organization membership.
□ The tenant is assigned to the same billing organization.
□ The user has active DDE authorization for the tenant.
□ A user without DDE authorization may view permitted non-DDE billing information but cannot perform DDE actions.
□ Expired, suspended, or revoked DDE authorization blocks DDE operations.
□ DDE authorization changes preserve history.
□ DDE Authorized is displayed without exposing credentials.
□ No plaintext DDE password exists in the application database.
□ No DDE credential appears in logs, exports, errors, or telemetry.
□ DDE actions are attributable to a specific user.
□ DDE tenant scope cannot be bypassed.

==================================================
GITHUB EPIC 03
AUTHORITATIVE REVENUE AND BILLABLE-EPISODE MODEL
==================================================

PURPOSE

Establish one authoritative unit for revenue calculations and prevent double counting.

CHILD ISSUES

03.1 Identify authoritative billing unit

03.2 Billable-episode mapping

03.3 Monetary precision hardening

03.4 Claim and episode scope constraints

03.5 Lifecycle-state authority

03.6 Revenue calculation service

03.7 Deduplication tests

03.8 Calculation trace output

ACCEPTANCE CRITERIA

□ One authoritative billable unit exists.
□ Existing authoritative claim or billing-period models are reused when available.
□ Monetary values use fixed-precision decimal or numeric types.
□ Floating-point arithmetic is not used for money.
□ Tenant, patient, episode, and claim relationships are consistent.
□ Duplicate equivalent billable episodes are prohibited.
□ Dashboard and Readiness use the same calculation service.
□ One claim with multiple blockers is counted once in headline blocked revenue.
□ Category breakdowns disclose possible overlap.
□ Calculations expose an as-of timestamp.
□ Calculations preserve the ruleset version.
□ Calculations are reproducible and explainable.

==================================================
GITHUB EPIC 04
BILLING DASHBOARD
==================================================

PURPOSE

Implement the locked Revenue Operations Command Center.

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

CHILD ISSUES

04.1 Dashboard summary API

04.2 Ready Revenue KPI

04.3 Blocked Revenue KPI

04.4 Revenue At Risk KPI

04.5 Pending Payments KPI

04.6 Expected Weekly Collections contract

04.7 Denied Revenue KPI

04.8 Recovery Opportunities KPI

04.9 DDE Exceptions KPI

04.10 Today's Work Queue

04.11 Billing Priorities

04.12 Revenue Pipeline

04.13 Collections Summary

04.14 Denial Health

04.15 Assigned Visibility

04.16 Assigned Agency Registry

04.17 Billing Events and Releases

04.18 Empty, loading, stale, and error states

04.19 Figma parity verification

DETAILED ACCEPTANCE CRITERIA

REVENUE

□ Ready Revenue includes only ready-to-bill revenue.
□ Ready Revenue excludes submitted, paid, voided, and superseded items.
□ Blocked Revenue includes unresolved blocking conditions.
□ Revenue At Risk excludes items already classified as blocked unless overlap is explicitly displayed.
□ Pending Payments includes submitted or accepted amounts awaiting confirmed payment.
□ Denied Revenue excludes fully recovered, reversed, or closed denials.
□ Recovery Opportunities require an active recovery path.
□ Expected collections are not displayed unless an approved methodology exists.
□ If forecasting is unavailable, the UI displays unavailable rather than invented values.

DDE

□ DDE Exceptions appears in the executive summary.
□ DDE Responses Pending appears in Today's Work Queue.
□ DDE Eligibility Reviews appears in Today's Work Queue.
□ DDE Status Checks appears in Today's Work Queue.
□ DDE Exception Resolution appears in Today's Work Queue.
□ DDE risks include revenue impact.
□ DDE actions require individual authorization.

ASSIGNMENT

□ Assigned Visibility displays billing organization.
□ Assigned Visibility displays current agency.
□ Assigned Visibility displays assigned biller.
□ Assigned Visibility displays DDE authorization status.
□ Assigned Agency Registry lists only assigned agencies.
□ Tenant switching does not display stale data from the prior tenant.

UX

□ The user can determine current revenue position quickly.
□ The user can identify the highest-priority work.
□ The user can identify current agency and billing organization.
□ The user can identify whether DDE requires attention.
□ All approved sections match Figma.
□ No Owner Platform subscription or licensing information appears.

==================================================
GITHUB EPIC 05
BILLING READINESS
==================================================

PURPOSE

Implement the locked Revenue Readiness, Revenue Protection, and Revenue Unlock Center.

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

CHILD ISSUES

05.1 Immutable readiness evaluations

05.2 Readiness conditions

05.3 Evidence references

05.4 Readiness actions

05.5 Readiness status engine

05.6 Revenue Unlock calculations

05.7 DDE readiness mapping

05.8 Guided resolution

05.9 Assignment Accountability

05.10 Authorized Scope

05.11 Activity Feed

05.12 Regulatory-reference linking

05.13 Readiness API

05.14 Readiness UI

05.15 Figma parity verification

DETAILED ACCEPTANCE CRITERIA

READINESS STATES

□ Not Ready is distinct from At Risk.
□ At Risk is distinct from Blocked.
□ Awaiting External is distinct from internal work pending.
□ Ready To Bill requires all mandatory conditions.
□ Submitted is distinct from Ready To Bill.
□ Paid is the terminal displayed billing state.
□ Readiness recalculation creates a new evaluation.
□ Previous evaluations remain available.
□ Replacement evaluations reference superseded evaluations.

CONDITIONS

□ Unsigned Orders may block or place revenue at risk according to approved rules.
□ Missing Certifications are visible.
□ Missing Face-to-Face is visible.
□ Eligibility Issues are visible.
□ NOE Deficiencies are visible.
□ Timely Filing Risks are visible.
□ DDE Verification Required is visible.
□ DDE Eligibility Conflict is visible.
□ DDE Response Pending is visible.
□ DDE Status Unknown is visible.
□ DDE Submission Failure is visible.
□ Completed Clinical Audit cannot be a blocker by itself.

GUIDANCE

□ Every unresolved condition states what is wrong.
□ Every unresolved condition states why it matters.
□ Every unresolved condition shows revenue impact.
□ Every unresolved condition identifies ownership.
□ Every unresolved condition provides a resolution path.
□ The system provides direct navigation where possible.
□ Revalidation is available after correction.
□ Billing users cannot silently modify signed clinical documentation.
□ Clinical corrections remain attributable to authorized clinical users.
□ Regulation citations come only from approved references.
□ The system does not invent regulatory citations.

CALCULATIONS

□ Ready Revenue is deduplicated.
□ Partially Ready Revenue is defined and reproducible.
□ Blocked Revenue is deduplicated by billable episode.
□ Revenue At Risk excludes overriding blocked states.
□ Revenue Unlock Opportunity requires an actionable resolution path.
□ Category-level overlap is disclosed.
□ Monetary calculations use fixed precision.

AUDIT

□ Readiness evaluation is audited.
□ Condition creation is audited.
□ Condition resolution is audited.
□ Assignment and reassignment are audited.
□ Escalation is audited.
□ Evidence addition is audited.
□ DDE review is audited.
□ Manual override requires authority and reason.
□ Revenue Released records availability to progress, not payment.
□ Payment remains a separate financial event.

==================================================
GITHUB EPIC 06
CLAIMS VALIDATION INTELLIGENCE
==================================================

PURPOSE

Determine whether a claim can be generated, batched, submitted, accepted, and paid.

VALIDATION INPUTS

- Certification Status
- Face-to-Face Status
- Physician Orders
- Eligibility
- NOE
- DDE Pre-Audit
- Active Revenue Integrity Blockers

CHILD ISSUES

06.1 Claim-validation service

06.2 Certification outcome adapter

06.3 Face-to-face outcome adapter

06.4 Physician-order outcome adapter

06.5 Eligibility adapter

06.6 NOE adapter

06.7 DDE pre-audit adapter

06.8 Revenue Integrity Blockers

06.9 Validation Status UI

06.10 Claim-readiness calculation

ACCEPTANCE CRITERIA

□ Claims cannot enter Ready To Generate with unresolved hard blockers.
□ Validation consumes clinical outcomes without exposing unnecessary clinical content.
□ Missing physician orders can block generation.
□ Missing certification can block generation when required.
□ Missing face-to-face can affect readiness when applicable.
□ Eligibility must use a reviewed authoritative state.
□ NOE status participates in validation.
□ Required DDE pre-audit participates in validation.
□ The page explains which validation failed.
□ The page identifies owner and next action.
□ Revenue impact remains visible.
□ Validation results include an as-of timestamp.
□ Validation history is preserved.
□ Revalidation occurs after a resolved condition.
□ The system does not silently release a previously blocked claim.

==================================================
GITHUB EPIC 07
CLAIMS LIFECYCLE AND CLEARINGHOUSE RESPONSES
==================================================

PURPOSE

Implement the complete claim lifecycle and distinguish internal workflow from external clearinghouse or payer responses.

LOCKED DISPLAY LIFECYCLE

- Ready To Generate
- Ready To Batch
- Ready To Submit
- On Hold
- Submitted
- Accepted
- Paid
- Denied

ADDITIONAL OPERATIONAL RESPONSE STATES

- Received
- Rejected
- Returned To Provider
- Accepted With Warning
- Resubmitted
- Appealed
- Reversed
- Voided

The UI may display response states inside a primary lifecycle stage rather than expanding the locked eight-stage top pipeline.

CHILD ISSUES

07.1 Claim lifecycle model

07.2 Lifecycle transition service

07.3 Clearinghouse response ingestion

07.4 Rejected-claim workflow

07.5 Returned-to-provider workflow

07.6 Accepted-with-warning workflow

07.7 Resubmission workflow

07.8 Claim Status Timeline

07.9 Lifecycle audit history

ACCEPTANCE CRITERIA

□ Invalid lifecycle transitions are rejected.
□ Submitted does not imply accepted.
□ Accepted does not imply paid.
□ Rejected is distinct from denied.
□ Returned To Provider is distinct from denied.
□ Resubmission preserves the original submission history.
□ Claim Status Timeline preserves all transitions.
□ External response identifiers are stored when available.
□ Duplicate clearinghouse responses do not create duplicate transitions.
□ Out-of-order responses are handled without rewriting history.
□ Every manual correction records actor, reason, and timestamp.
□ Paid is not recorded until authoritative payment evidence exists.

==================================================
GITHUB EPIC 08
CLAIM BATCH MANAGEMENT
==================================================

PURPOSE

Support real hospice billing batch preparation, layered review, removal, correction, rebuild, approval, and submission.

CHILD ISSUES

08.1 Claim batch model

08.2 Claim batch version model

08.3 Claim batch membership model

08.4 Batch creation

08.5 Batch review

08.6 Batch hold

08.7 Remove From Batch

08.8 Return To Ready Queue

08.9 Rebuild Batch

08.10 Approve Batch

08.11 Submit Batch

08.12 Batch Exception Queue

08.13 Batch review checklist

08.14 Batch audit history

08.15 Claims Removed This Cycle interaction

LOCKED ACTIONS

- Remove From Batch
- Return To Ready Queue
- Rebuild Batch
- Approve Batch
- Submit Batch

ACCEPTANCE CRITERIA

BATCH CREATION

□ Only eligible claims may enter a new batch.
□ Each batch belongs to one tenant.
□ Claims from different tenants cannot enter the same batch.
□ Batch amount equals the deduplicated sum of current batch memberships.
□ Prepared By is captured.
□ Created timestamp is captured.

MULTI-LAYER REVIEW

□ Prepared By is displayed.
□ Reviewed By is displayed.
□ Submission Approval status is displayed.
□ The same user may not satisfy conflicting separation-of-duty roles when policy prohibits it.
□ Reviewer decisions are audited.
□ Approval is required before submission when configured.

REMOVE AND UNDO

□ Staff can remove an individual claim from an unsubmitted batch.
□ Removal never deletes the claim.
□ Removal never deletes the original batch version.
□ Removal requires a reason.
□ Removed By and Date Removed are captured.
□ Removed claim enters the Batch Exception Queue.
□ Removed claim receives an explicit returned status.
□ Removed claim may return to the Ready Queue only after appropriate validation.
□ Submitted or transmitted batches cannot be destructively edited.
□ Post-submission corrections use approved replacement, adjustment, void, or rebill workflow.

VERSIONING

□ Batch v1 remains preserved after v2 is created.
□ Batch v2 remains preserved after v3 is created.
□ New versions record claims added and removed.
□ New versions record the reason.
□ New versions record the actor and timestamp.
□ Batch version history is viewable.
□ No batch history is physically deleted.

REBUILD

□ Rebuild creates a new version.
□ Rebuild recalculates claim count.
□ Rebuild recalculates revenue amount.
□ Rebuild reruns required validation.
□ Rebuild Required clears only after successful rebuild.
□ Failed rebuild does not corrupt the previous valid version.

EXCEPTION QUEUE

□ Batch Exception Queue displays Claim ID.
□ Batch Exception Queue displays patient context subject to permissions.
□ Removal reason is displayed.
□ Removed By is displayed.
□ Date Removed is displayed.
□ Returned Status is displayed.
□ Exception resolution is audited.
□ "Claims Removed This Cycle" opens the filtered exception queue.

==================================================
GITHUB EPIC 09
CLAIMS MANAGEMENT UI AND WORKSPACE
==================================================

PURPOSE

Implement the approved Claims Operations Workstation.

REQUIRED SECTIONS

- Executive Claim Summary
- Claim Validation Status
- Revenue Integrity Blocker Metrics
- Batch Management Panel
- Batch Exception Queue
- Claims Work Queue
- DDE Claims Status
- Claim Lifecycle Pipeline
- Claims At Risk
- Validation Override History
- Active Claims Registry
- Claim Status Timeline

CHILD ISSUES

09.1 Claims summary API

09.2 Claims Work Queue

09.3 DDE Claims Status

09.4 Claims At Risk

09.5 Active Claims Registry

09.6 Benefit Period visibility

09.7 Validation Status

09.8 Next Action behavior

09.9 Validation Override History

09.10 Claim Status Timeline

09.11 Empty, loading, stale, and error states

09.12 Figma parity verification

CLAIMS REGISTRY REQUIRED FIELDS

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
- Assigned Biller
- Next Action where shown in approved design

ACCEPTANCE CRITERIA

□ Registry is tenant scoped.
□ Benefit Period or authoritative equivalent is displayed.
□ Financial amount uses authoritative data.
□ Priority is explainable.
□ Blocker is visible.
□ Validation Status is visible.
□ Assigned Biller is visible.
□ Next Action opens the correct workflow.
□ Patient details follow minimum-necessary access.
□ DDE status is visible.
□ Claims At Risk displays days remaining and resolution pathway.
□ Override history records released by, reason, timestamp, and audit status.
□ The UI matches approved Figma.
□ No clinical-navigation module is reintroduced.

==================================================
GITHUB EPIC 10
VALIDATION OVERRIDES AND COMPLIANCE CONTROL
==================================================

PURPOSE

Permit controlled, auditable exceptions without silently bypassing compliance.

CHILD ISSUES

10.1 Override authority matrix

10.2 Override request

10.3 Override approval

10.4 Hold release

10.5 Blocker removal

10.6 Validation release

10.7 Escalation

10.8 Override audit history

ACCEPTANCE CRITERIA

□ Overrides require a permitted actor.
□ Overrides require a documented reason.
□ Overrides record previous and resulting state.
□ Emergency submission requires approved authority.
□ An override does not delete the original blocker.
□ Original validation result remains visible.
□ The override record is immutable.
□ A released claim remains distinguishable from a normally validated claim.
□ Override events display audit status.
□ Expired or unauthorized users cannot approve overrides.
□ The system does not automatically fabricate justification.
□ Override reporting is available for authorized review.

==================================================
GITHUB EPIC 11
AUDIT, IMMUTABILITY, AND EVIDENCE
==================================================

PURPOSE

Preserve complete, attributable history across all three pages.

AUDIT EVENTS

- Page access
- Tenant selection
- Claim drill-down
- Readiness evaluation
- Condition creation
- Condition resolution
- Evidence addition
- Claim generation
- Batch creation
- Batch revision
- Batch hold
- Claim removal
- Return to Ready Queue
- Batch approval
- Batch submission
- Clearinghouse synchronization
- DDE review
- DDE exception resolution
- Override request
- Override approval
- Revenue Released event
- Claim submission
- Claim acceptance
- Payment posting
- Export

ACCEPTANCE CRITERIA

□ Actor is preserved.
□ Role is preserved.
□ Tenant is preserved.
□ Billing organization is preserved.
□ Previous state is preserved when applicable.
□ New state is preserved when applicable.
□ Reason is preserved.
□ Timestamp is preserved.
□ Correlation ID is preserved.
□ Ruleset version is preserved when applicable.
□ Evidence references are preserved.
□ Historical events cannot be rewritten.
□ Corrections create corrective events.
□ Reversals reference original events.
□ No credentials or secrets appear in audit data.
□ Patient access is auditable.
□ Export activity is auditable.

==================================================
GITHUB EPIC 12
PERFORMANCE, RELIABILITY, AND DATA QUALITY
==================================================

CHILD ISSUES

12.1 Dashboard aggregation optimization

12.2 Readiness aggregation optimization

12.3 Claims registry pagination

12.4 Billing-event pagination

12.5 Tenant-aware cache strategy

12.6 Projection or view evaluation

12.7 Stale-data handling

12.8 External-response idempotency

12.9 Concurrency control

12.10 Database index review

ACCEPTANCE CRITERIA

□ The UI does not execute one database query per card.
□ N+1 query patterns are removed.
□ Activity and registry lists are paginated.
□ Cache keys include tenant and permission scope.
□ Cache entries cannot leak across tenants.
□ Readiness recalculation is concurrency safe.
□ Batch rebuild is concurrency safe.
□ Duplicate external responses are idempotent.
□ Stale data displays Last Updated.
□ The application does not label stale DDE data as live.
□ DDE displays Unknown if no authoritative health source exists.
□ Projection tables or views remain rebuildable.
□ Immutable source records remain authoritative.

==================================================
GITHUB EPIC 13
TESTING AND PRODUCTION HYGIENE
==================================================

REQUIRED TESTS

- Unit tests
- Integration tests
- Authorization tests
- Tenant-isolation tests
- DDE authorization tests
- Revenue-calculation tests
- Deduplication tests
- Readiness-transition tests
- Claims-lifecycle tests
- Batch-version tests
- Batch-removal tests
- Override tests
- Audit tests
- UI tests
- Migration tests
- Backup tests
- Restore tests
- Figma parity tests

ACCEPTANCE CRITERIA

□ Tests use tagged, isolated fixtures.
□ Tests remove all created records during teardown.
□ Shared persistent databases contain no unexplained test artifacts.
□ Batch tests preserve revision history.
□ Tenant-isolation tests verify API and cache boundaries.
□ DDE tests verify individual authorization.
□ Revenue tests verify decimal precision.
□ Dashboard and Readiness totals agree at the same as-of point.
□ Claims removed from batches remain traceable.
□ Restore testing recovers billing history.
□ No schema drift remains after migrations.
□ Alembic current equals expected head.
□ No alembic stamp was used.
□ No historical migration was rewritten.
□ No unsafe automigration was accepted without review.

==================================================
14. PHASED IMPLEMENTATION PLAN
==================================================

ONLY ONE PHASE MAY BE ACTIVE AT A TIME.

Maintain separate sections in the implementation tracker for:

- Completed Work
- Open Defects
- Verification Evidence
- Current Phase
- Next-Phase Queue

--------------------------------------------------
PHASE 0
DISCOVERY AND BASELINE
--------------------------------------------------

Maps to:

- Repository Discovery
- Schema Discovery
- Route Discovery
- Figma Surface Discovery

Deliverables:

- BILLER_PLATFORM_DISCOVERY_REPORT.md
- REUSE / EXTEND / CREATE matrix
- Current migration verification
- Exact file-impact list

Exit Gate:

□ Migration state verified.
□ Database identity verified.
□ No unresolved schema drift.
□ Existing models mapped.
□ Protected working functionality identified.

--------------------------------------------------
PHASE 1
ACCESS AND ASSIGNMENT FOUNDATION
--------------------------------------------------

Maps to:

- Epic 01
- Initial Epic 11 audit events
- Initial Epic 13 isolation tests

Exit Gate:

□ Assigned agencies only.
□ Server-side scope enforced.
□ Agency switch protected.
□ Assigned Agency Registry operational.
□ Audit events verified.

--------------------------------------------------
PHASE 2
INDIVIDUAL DDE AUTHORIZATION
--------------------------------------------------

Maps to:

- Epic 02
- DDE permission portion of Epic 11
- DDE security tests from Epic 13

Exit Gate:

□ Individual DDE authorization operational.
□ Tenant-specific DDE authorization operational.
□ Revocation and expiration operational.
□ No DDE secrets exposed.

--------------------------------------------------
PHASE 3
AUTHORITATIVE REVENUE FOUNDATION
--------------------------------------------------

Maps to:

- Epic 03
- Revenue-event foundations from Epic 11

Exit Gate:

□ Billable unit established.
□ Decimal money handling verified.
□ Revenue deduplication verified.
□ Shared calculation authority established.

--------------------------------------------------
PHASE 4
BILLING READINESS ENGINE
--------------------------------------------------

Maps to:

- Epic 05 backend
- Readiness components of Epic 11
- Readiness calculations from Epic 03

Exit Gate:

□ Immutable evaluations operational.
□ Conditions operational.
□ Evidence references operational.
□ DDE conditions participate.
□ Guidance and revalidation operational.

--------------------------------------------------
PHASE 5
BILLING READINESS UI
--------------------------------------------------

Maps to:

- Epic 05 frontend
- Approved Billing Readiness Figma

Exit Gate:

□ All approved sections present.
□ Authorized Scope present.
□ DDE Health present.
□ Readiness cards readable.
□ Figma parity verified.

--------------------------------------------------
PHASE 6
BILLING DASHBOARD
--------------------------------------------------

Maps to:

- Epic 04
- Shared calculations from Epic 03
- Shared work queues from Epic 05

Exit Gate:

□ Revenue KPIs operational.
□ Work queues operational.
□ DDE visible.
□ Assigned agencies only.
□ Dashboard and Readiness totals agree.
□ Figma parity verified.

--------------------------------------------------
PHASE 7
CLAIMS VALIDATION
--------------------------------------------------

Maps to:

- Epic 06
- Claims portion of Epic 11

Exit Gate:

□ Validation inputs mapped.
□ Claim generation rules operational.
□ Revenue Integrity Blockers operational.
□ Validation history preserved.
□ Clinical boundary maintained.

--------------------------------------------------
PHASE 8
CLAIMS LIFECYCLE AND CLEARINGHOUSE
--------------------------------------------------

Maps to:

- Epic 07
- External-response reliability from Epic 12

Exit Gate:

□ Eight-stage lifecycle operational.
□ Rejected and RTP paths operational.
□ Resubmission history preserved.
□ Duplicate external responses handled.
□ Claim Status Timeline operational.

--------------------------------------------------
PHASE 9
BATCH MANAGEMENT
--------------------------------------------------

Maps to:

- Epic 08
- Batch audit events from Epic 11
- Concurrency from Epic 12

Exit Gate:

□ Batch creation operational.
□ Multiple review levels operational.
□ Remove From Batch operational.
□ Return To Ready Queue operational.
□ Rebuild creates new version.
□ Approval and submission operational.
□ Batch Exception Queue operational.
□ Prior batch versions remain viewable.

--------------------------------------------------
PHASE 10
CLAIMS MANAGEMENT UI
--------------------------------------------------

Maps to:

- Epic 09
- Approved Claims Management Figma

Exit Gate:

□ All approved sections present.
□ Batch actions operational.
□ DDE visible.
□ Benefit Period visible.
□ Validation Override History visible.
□ Claims Removed interaction operational.
□ Figma parity verified.

--------------------------------------------------
PHASE 11
OVERRIDES AND ESCALATION
--------------------------------------------------

Maps to:

- Epic 10
- Related audit events from Epic 11

Exit Gate:

□ Override authority enforced.
□ Reason required.
□ Original blocker preserved.
□ Released claim remains distinguishable.
□ Audit history immutable.

--------------------------------------------------
PHASE 12
AUDIT AND IMMUTABILITY HARDENING
--------------------------------------------------

Maps to:

- Epic 11

Exit Gate:

□ All required events captured.
□ Corrective history preserved.
□ No destructive business-history updates.
□ No secrets in logs.
□ Exports audited.

--------------------------------------------------
PHASE 13
PERFORMANCE AND RELIABILITY
--------------------------------------------------

Maps to:

- Epic 12

Exit Gate:

□ Query plans reviewed.
□ N+1 issues resolved.
□ Pagination operational.
□ Tenant-aware cache verified.
□ Concurrency verified.
□ Stale-data behavior verified.

--------------------------------------------------
PHASE 14
FULL VALIDATION AND CLEANUP
--------------------------------------------------

Maps to:

- Epic 13

Exit Gate:

□ Required tests pass.
□ Backup succeeds.
□ Restore succeeds.
□ Cross-tenant tests pass.
□ DDE authorization tests pass.
□ Calculation reconciliation passes.
□ No test records remain.
□ No debug artifacts remain.
□ No schema drift remains.

--------------------------------------------------
PHASE 15
IMPLEMENTATION VERIFICATION
--------------------------------------------------

CREATE:

/docs/biller-platform/BILLER_PLATFORM_IMPLEMENTATION_VERIFICATION.md

Required content:

- Completed work
- Open defects
- Verification evidence
- Files changed
- Models reused
- Models extended
- Models created
- Migrations created
- Migration head
- Constraints and indexes
- API routes
- Permission enforcement
- Revenue formulas
- DDE behavior
- Batch versioning behavior
- Clearinghouse-response behavior
- Audit events
- Test commands
- Test outcomes
- Backup outcome
- Restore outcome
- Cleanup outcome
- Storage impact
- Figma comparisons
- Known limitations
- Deferred enhancements

==================================================
15. IMPLEMENTATION COMPLETION CHECKLIST
==================================================

FOUNDATION

□ Discovery complete.
□ Entity mapping complete.
□ Database identity verified.
□ Migration lineage verified.
□ No schema drift.

SECURITY

□ Assignment enforced server-side.
□ Cross-tenant access blocked.
□ DDE authorization individually enforced.
□ Cache isolation verified.
□ Export isolation verified.

BILLING DASHBOARD

□ Approved sections implemented.
□ Revenue totals authoritative.
□ DDE visible.
□ Assigned agencies only.
□ Figma parity verified.

BILLING READINESS

□ Immutable evaluation history.
□ Readiness conditions implemented.
□ Evidence references implemented.
□ Guided corrections implemented.
□ DDE readiness integrated.
□ Revenue unlock logic verified.
□ Figma parity verified.

CLAIMS

□ Claim Validation implemented.
□ Revenue Integrity Blockers implemented.
□ Claims Work Queue implemented.
□ Eight-stage lifecycle implemented.
□ Clearinghouse response states implemented.
□ Active Claims Registry implemented.
□ Benefit Period displayed.
□ Figma parity verified.

BATCHING

□ Batch creation implemented.
□ Layered review implemented.
□ Remove From Batch implemented.
□ Return To Ready Queue implemented.
□ Rebuild Batch implemented.
□ Approve Batch implemented.
□ Submit Batch implemented.
□ Batch versions immutable.
□ Batch Exception Queue implemented.
□ Claims Removed interaction implemented.

AUDIT

□ Validation overrides audited.
□ Batch changes audited.
□ DDE events audited.
□ Revenue events audited.
□ Original history preserved.

TESTING

□ Unit tests pass.
□ Integration tests pass.
□ UI tests pass.
□ Tenant-isolation tests pass.
□ DDE tests pass.
□ Calculation tests pass.
□ Migration tests pass.
□ Backup and restore pass.
□ Test teardown verified.
□ No test artifacts remain.

==================================================
16. IMPLEMENTATION BLOCKERS
==================================================

DO NOT DECLARE IMPLEMENTATION COMPLETE IF:

- Repository discovery is incomplete
- Existing models have not been mapped
- Migration head is unknown
- Schema drift exists
- Multiple conflicting revenue formulas exist
- Dashboard and Readiness totals conflict
- DDE access is treated as organization-wide
- Cross-tenant access exists
- Batch history can be deleted
- Batch removal loses the claim
- Submitted batches can be silently edited
- Original validation blockers are overwritten
- Revenue uses floating-point arithmetic
- Mock financial values appear as live data
- Tests leave persistent artifacts
- Restore testing fails
- Approved Figma sections are missing
- Clinical navigation reappears
- Biller Platform branding does not use SNS Tech Solutions

==================================================
17. FINAL LOCKED DECISIONS
==================================================

SNS Tech Solutions Branding:
LOCKED

Biller Platform Ownership:
LOCKED

SNS Hospice Solutions Tenant Context:
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

Claim Validation Intelligence:
LOCKED

Eight-Stage Claim Lifecycle:
LOCKED

Batch Management:
LOCKED

Batch Removal and Return to Queue:
LOCKED

Immutable Batch Versioning:
LOCKED

Batch Exception Queue:
LOCKED

Validation Override History:
LOCKED

Visits & Notes Navigation Removal:
LOCKED

POC & Certifications Navigation Removal:
LOCKED

North East Billing Center Naming:
LOCKED

==================================================
FINAL IMPLEMENTATION RULE
==================================================

Do not redesign during implementation.

Do not add unrelated features.

Do not create duplicate architecture.

Do not overwrite history.

Do not leave test artifacts.

Verify first.

Implement one phase at a time.

Preserve evidence.

Preserve completed work.

Use forward-only corrections.

Future changes must be separately approved enhancements supported by verified operational need or field-testing evidence.

---

## Status

**SUPERSEDED.** As of
`docs/biller-platform/BILLER_PLATFORM_FINAL_IMPLEMENTATION_HANDOFF.md`,
this document is no longer the current Biller Platform implementation
authority. It is retained as historical record only.

APPROVED. LOCKED. Figma Design Complete. Implementation Authorized.
This is the final, consolidated authority for the Biller Platform's
first three implementation pages (Billing Dashboard, Billing
Readiness, Claims Management), superseding and unifying the scattered
requirements from the prior individual specifications into: a single
17-section architecture/security/data/calculation authority, 13
GitHub epics (01-13) with child issues and acceptance criteria, a
16-phase implementation plan (Phase 0 Discovery through Phase 15
Implementation Verification, one phase active at a time), an
implementation completion checklist, an explicit implementation
blockers list, and a final locked-decisions register. Approval/lock
status does not itself perform implementation — Phase 0 (Repository
Discovery) must be verified complete, with no schema or migrations
created, before Phase 1 or any later phase begins.

**Deliverables named by this document and their current state:**

- `docs/biller-platform/BILLER_PLATFORM_DISCOVERY_REPORT.md` —
  **not yet created**; Phase 0 exit-gate deliverable; discovery
  investigation is in progress (migration head/lineage, existing
  tenant/billing/readiness/claim models, existing routes, and an
  assignment-visibility enforcement gap have already been identified
  and are pending write-up).
- `docs/biller-platform/BILLER_PLATFORM_IMPLEMENTATION_VERIFICATION.md`
  — **not yet created**; Phase 15 exit-gate deliverable; its required
  content (completed work, models reused/extended/created, migration
  head, revenue formulas, DDE/batch/clearinghouse behavior, test and
  backup/restore outcomes, Figma comparisons, known limitations) is
  fully specified here for the first time.
- `docs/biller-platform/BILLER_PLATFORM_DATABASE_SCHEMA_AND_MIGRATION_PLAN.md`
  and `docs/biller-platform/BILLER_PLATFORM_IMPLEMENTATION_TASK_BREAKDOWN.md`
  already exist from prior sessions and remain in force; this document
  does not replace them but supersedes their phase/epic numbering
  where it conflicts, since this is the newer, more detailed, and
  explicitly "Final Consolidated" authority.

## Relationship to Other Documents

- Consolidates and supersedes the phase/epic structure previously
  established in
  `docs/biller-platform/BILLER_PLATFORM_IMPLEMENTATION_TASK_BREAKDOWN.md`
  (18 phases) with a new, more granular 16-phase plan (Phase 0-15) tied
  to 13 named GitHub epics; the Database Schema and Migration Plan
  document's forward-only migration principles remain in force and are
  reinforced by the Implementation Blockers section here.
- Restates and locks the branding, tenant-context, and "North East
  Billing Center" naming standards first established in
  `docs/architecture/SNS_TECH_SOLUTIONS_PLATFORM_HIERARCHY.md` and
  `docs/biller-platform/BILLER_PLATFORM_FINAL_IMPLEMENTATION_BRIEF.md`.
- Restates the Clinical Boundary / Clinical Separation Rule (no
  Visits & Notes or POC & Certifications navigation) first introduced
  in `docs/biller-platform/TENANT_BILLER_DASHBOARD_SPECIFICATION.md`'s
  Remove list and reaffirmed in
  `BILLER_PLATFORM_FINAL_IMPLEMENTATION_BRIEF.md` and
  `BILLER_PLATFORM_IMPLEMENTATION_HANDOFF.md`.
- Restates the Assignment-Based Access rule ("visibility follows
  assignment, access follows assignment, responsibility follows
  assignment") from `docs/roadmap/Biller-Platform-Roadmap.md`'s Biller
  Platform Tenant Visibility Rule, and substantially sharpens it with
  new, explicit anti-bypass requirements (URL/query/body/cache/export/
  background-job/enumeration attack vectors; the system must not
  reveal whether an unassigned agency exists) not previously specified
  at this level of detail.
- Expands the DDE Architecture first introduced in
  `docs/architecture/SNS_TECH_SOLUTIONS_PLATFORM_HIERARCHY.md`'s DDE
  Architecture Rule and DDE Visibility Rule into a fully specified,
  individual-level authorization model (billing org membership vs.
  tenant assignment vs. individual biller assignment vs. individual DDE
  authorization vs. per-tenant DDE authorization — five distinct
  layers) with explicit credential-security requirements (no plaintext
  DDE passwords; no DDE credentials in UI, logs, exports, telemetry,
  errors, or audit events).
- Introduces, for the first time in any Biller Platform document, the
  full Claim Batch Management data model and workflow (Claim Batch,
  Claim Batch Version, Claim Batch Membership, Batch Exception, Batch
  Review) with an explicit non-destructive versioning rule (Batch v1
  preserved after v2, v2 preserved after v3, etc.) and a Validation
  Override model distinct from the batch model — both of which must be
  added to the (not yet written) Discovery Report's logical-entity list
  and, eventually, to the Database Schema and Migration Plan.
- Introduces the eight-stage locked claim lifecycle (Ready To
  Generate → Ready To Batch → Ready To Submit → On Hold → Submitted →
  Accepted → Paid → Denied) plus additional operational clearinghouse
  response states (Received, Rejected, Returned To Provider, Accepted
  With Warning, Resubmitted, Appealed, Reversed, Voided) — more
  detailed than the simple Ready/Submitted/Accepted/Paid/Denied
  pipeline used in earlier Billing Dashboard specifications, which
  remains valid as the dashboard-level rollup view.
- The 25-entity logical-entity list in Section 10 (Required Discovery
  Deliverable) supersedes the 15-entity list originally requested for
  `BILLER_PLATFORM_DISCOVERY_REPORT.md`, adding Claim, Claim
  Validation, Claim Lifecycle Event, Claim Batch, Claim Batch Version,
  Claim Batch Membership, Batch Exception, Batch Review, Validation
  Override, and Audit Event. The pending Discovery Report must be
  written against this expanded 25-entity list.

## Change Log

| Date | Change |
|---|---|
| 2026-09-16 | Document created — Final Consolidated Implementation Handoff for Billing Dashboard, Billing Readiness, and Claims Management: Global Platform Architecture, Core Mission, Clinical Boundary, Assignment-Based Access, DDE Architecture, Approved Navigation, Billing Organization Naming Standard, Implementation Authority, Verify-First Requirement, Required Discovery Deliverable (25-entity list), 13 GitHub Epics (01 Access Foundation through 13 Testing and Production Hygiene) with child issues and acceptance criteria, 16-phase Phased Implementation Plan (Phase 0 Discovery through Phase 15 Implementation Verification), Implementation Completion Checklist, Implementation Blockers, Final Locked Decisions register, and Final Implementation Rule. |
