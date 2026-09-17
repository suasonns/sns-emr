BILLER PLATFORM IMPLEMENTATION HANDOFF

STATUS

APPROVED

FIGMA DESIGN PHASE COMPLETE

GitHub implementation authorized.

The following pages are LOCKED and should move into implementation:

1. Billing Dashboard
2. Billing Readiness
3. Claims Management

No architectural redesign is authorized during implementation.

Future changes must be implemented as enhancements after field testing.

==================================================
GLOBAL PLATFORM RULE
==================================================

Platform Owner:

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
REQUIRED IMPLEMENTATION PROCESS
==================================================

Before implementation:

1. Complete Phase 0 Repository Discovery
2. Create Discovery Report
3. Map logical entities to existing models
4. Classify each entity:

REUSE
EXTEND
CREATE

5. Verify migration head
6. Verify migration lineage
7. Verify ORM/database alignment
8. Verify no schema drift

Do not begin migrations before discovery is complete.

==================================================
PAGE 1
BILLING DASHBOARD
==================================================

STATUS

LOCKED

IMPLEMENT

Approved Sections:

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

DDE Integration

Assignment-based visibility

Revenue calculations

Audit logging

==================================================
PAGE 2
BILLING READINESS
==================================================

STATUS

LOCKED

IMPLEMENT

Approved Sections:

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

Immutable readiness evaluations

Revenue unlock calculations

Evidence references

Readiness condition tracking

DDE readiness integration

Audit history

==================================================
PAGE 3
CLAIMS MANAGEMENT
==================================================

STATUS

LOCKED

IMPLEMENT

The Claims Management page has been enhanced to reflect real-world hospice billing workflows reviewed against production billing operations.

==================================================
REQUIRED CLAIMS SECTIONS
==================================================

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
CLAIMS VALIDATION RULE
==================================================

Claims page is not a registry only.

Claims page must answer:

Can this claim move forward?

Why is this claim blocked?

What is missing?

Who owns the fix?

What revenue is affected?

What should happen next?

Validation includes:

- Certification Status
- Face-to-Face Status
- Physician Orders
- Eligibility Verification
- NOE Verification
- DDE Verification

==================================================
BATCH MANAGEMENT RULE
==================================================

Batching is a required workflow.

Support:

- Ready To Batch
- Batch Review
- Rebuild Batch
- Batch Hold
- Batch Approval
- Submission Approval

Display:

- Batch Version
- Claims In Batch
- Revenue In Batch
- Prepared By
- Reviewed By
- Submission Approval Status

==================================================
BATCH REVISION RULE
==================================================

DO NOT implement destructive batch deletion.

Implement:

Batch Revision

Example:

Batch v1

12 Claims

↓

Batch v2

11 Claims

↓

Batch v3

10 Claims

Audit preserved.

Every change remains traceable.

==================================================
REMOVE FROM BATCH RULE
==================================================

Required actions:

- Remove From Batch
- Return To Ready Queue
- Rebuild Batch
- Approve Batch
- Submit Batch

Removed claims must enter:

Batch Exception Queue

Do not disappear.

==================================================
BATCH EXCEPTION QUEUE RULE
==================================================

Track:

- Claim ID
- Patient
- Removal Reason
- Removed By
- Date Removed
- Returned Status

Examples:

Missing Orders

Eligibility Failure

Certification Failure

NOE Defect

DDE Validation Failure

==================================================
VALIDATION OVERRIDE HISTORY
==================================================

Track:

- Override Action
- Released By
- Reason
- Timestamp
- Audit Status

Required examples:

Validation Released

Blocker Removed

Override Approved

Hold Released

Reason must be captured.

Audit trail must be immutable.

==================================================
CLAIM LIFECYCLE
==================================================

Approved lifecycle:

Ready To Generate

Ready To Batch

Ready To Submit

On Hold

Submitted

Accepted

Paid

Denied

Do not collapse stages.

==================================================
CLAIMS REGISTRY
==================================================

Required columns:

Claim ID

Patient

Payer

Benefit Period

Service Date

Amount

Status

Priority

Claim Readiness

Validation Status

Assigned Biller

Benefit Period visibility is required.

==================================================
DDE RULE
==================================================

Implement:

- Verification Required
- Eligibility Conflict
- Response Pending
- Submission Failure
- Status Unknown

DDE problems affect readiness.

DDE problems affect claims progression.

DDE problems affect revenue.

==================================================
ASSIGNMENT RULE
==================================================

Visibility follows assignment.

Access follows assignment.

Responsibility follows assignment.

Users only see:

Assigned Agencies

Assigned Claims

Authorized DDE Scope

==================================================
CLINICAL SEPARATION RULE
==================================================

Do NOT reintroduce:

Visits & Notes

POC & Certifications

as standalone navigation modules.

Claims page consumes clinical validation outcomes.

Claims page does not manage clinical workflows.

==================================================
AUDIT RULE
==================================================

Audit:

- Claim creation
- Claim validation
- Claim release
- Batch creation
- Batch rebuild
- Remove from batch
- Return to queue
- Submission approval
- Claim submission
- DDE review
- Override actions

Preserve:

Actor

Timestamp

Reason

Previous State

New State

Correlation ID

==================================================
IMPLEMENTATION DELIVERABLES
==================================================

Required Documents:

/docs/biller-platform/BILLER_PLATFORM_DISCOVERY_REPORT.md

/docs/biller-platform/BILLER_PLATFORM_DATABASE_SCHEMA_AND_MIGRATION_PLAN.md

/docs/biller-platform/BILLER_PLATFORM_IMPLEMENTATION_TASK_BREAKDOWN.md

/docs/biller-platform/BILLER_PLATFORM_IMPLEMENTATION_VERIFICATION.md

==================================================
FINAL LOCK
==================================================

Billing Dashboard

LOCKED

Billing Readiness

LOCKED

Claims Management

LOCKED

SNS Tech Solutions Branding

LOCKED

Assignment Visibility

LOCKED

DDE Integration

LOCKED

Batch Management Workflow

LOCKED

Batch Revision Workflow

LOCKED

No architectural redesign authorized during implementation.

Proceed to GitHub implementation.

---

## Status

APPROVED. Figma design phase complete for Billing Dashboard, Billing
Readiness, and (newly added in this handoff) Claims Management —
GitHub implementation is authorized for all three pages. This document
does not itself perform implementation; it is the handoff record.
Per the Required Implementation Process above and
`docs/biller-platform/BILLER_PLATFORM_IMPLEMENTATION_TASK_BREAKDOWN.md`,
Phase 0 Repository Discovery must be complete — and no schema or
migrations created — before any implementation work begins.

**Outstanding required deliverables at time of this handoff:**

- `docs/biller-platform/BILLER_PLATFORM_DISCOVERY_REPORT.md` —
  **not yet created**; discovery investigation is in progress
  (migration head/lineage, existing tenant/billing/readiness models,
  existing routes, and an assignment-visibility enforcement gap have
  already been identified and are pending write-up).
- `docs/biller-platform/BILLER_PLATFORM_IMPLEMENTATION_VERIFICATION.md`
  — **not yet created**; net-new deliverable introduced by this
  handoff, not present in the prior Database Schema/Migration Plan or
  Task Breakdown documents.
- `docs/biller-platform/BILLER_PLATFORM_DATABASE_SCHEMA_AND_MIGRATION_PLAN.md`
  and `docs/biller-platform/BILLER_PLATFORM_IMPLEMENTATION_TASK_BREAKDOWN.md`
  already exist (created previously) and remain in force; this handoff
  does not modify them.

## Relationship to Other Documents

- Authorizes implementation of the two pages already locked in
  `docs/biller-platform/BILLER_PLATFORM_FINAL_IMPLEMENTATION_BRIEF.md`
  (Billing Dashboard, Billing Readiness) and adds a third locked page,
  **Claims Management**, with a full new specification (Executive
  Claim Summary, Claim Validation Status, Revenue Integrity Blockers,
  Batch Management Panel, Batch Exception Queue, Claims Work Queue,
  DDE Claims Status, Claim Lifecycle Pipeline, Claims At Risk,
  Validation Override History, Active Claims Registry, Claim Status
  Timeline) not previously documented in any prior Biller Platform
  file.
- Restates the Clinical Separation Rule (Visits & Notes and POC &
  Certifications must not be reintroduced as standalone navigation)
  first established in
  `docs/biller-platform/TENANT_BILLER_DASHBOARD_SPECIFICATION.md`'s
  Remove list and restated in
  `BILLER_PLATFORM_FINAL_IMPLEMENTATION_BRIEF.md`'s Removed Navigation
  section.
- Restates the Assignment Rule ("visibility follows assignment, access
  follows assignment, responsibility follows assignment") established
  in `docs/roadmap/Biller-Platform-Roadmap.md`'s Biller Platform Tenant
  Visibility Rule and reiterated across
  `TENANT_BILLER_DASHBOARD_SPECIFICATION.md`,
  `BILLER_PLATFORM_LOCKED_SPECIFICATIONS.md`, and
  `BILLER_PLATFORM_FINAL_IMPLEMENTATION_BRIEF.md`.
- Restates the Required Implementation Process (Phase 0 discovery,
  entity mapping, REUSE/EXTEND/CREATE classification, migration
  head/lineage verification, ORM/database alignment, no-schema-drift
  verification) already defined in
  `docs/biller-platform/BILLER_PLATFORM_DATABASE_SCHEMA_AND_MIGRATION_PLAN.md`
  and `BILLER_PLATFORM_IMPLEMENTATION_TASK_BREAKDOWN.md`; this handoff
  does not relax that gate.
- Introduces the Batch Revision Rule (no destructive batch deletion;
  versioned batches — v1/v2/v3 — with full audit trail) and the Batch
  Exception Queue Rule (removed claims are tracked, never dropped) as
  new, net-new requirements specific to Claims Management; these have
  no prior counterpart in the Billing Dashboard or Billing Readiness
  specifications and must be accounted for in the (not yet created)
  Discovery Report and Database Schema/Migration Plan updates when
  Claims Management implementation begins.
- Names a fourth required deliverable,
  `BILLER_PLATFORM_IMPLEMENTATION_VERIFICATION.md`, not previously
  named in any prior document — its scope (presumably a post-
  implementation verification/acceptance record) is not yet defined
  and should be clarified before it is authored.

## Change Log

| Date | Change |
|---|---|
| 2026-09-16 | Document created — Biller Platform Implementation Handoff: Global Platform Rule, Required Implementation Process, Page 1 (Billing Dashboard) and Page 2 (Billing Readiness) implementation authorization, and new Page 3 (Claims Management) full specification (Required Claims Sections, Claims Validation Rule, Batch Management Rule, Batch Revision Rule, Remove From Batch Rule, Batch Exception Queue Rule, Validation Override History, Claim Lifecycle, Claims Registry, DDE Rule, Assignment Rule, Clinical Separation Rule, Audit Rule), Implementation Deliverables list, and Final Lock. Noted two outstanding required deliverables: the in-progress Discovery Report and the net-new Implementation Verification document. |
