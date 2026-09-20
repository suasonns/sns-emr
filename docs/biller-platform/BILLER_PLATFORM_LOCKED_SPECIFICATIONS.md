==================================================

SNS TECH SOLUTIONS

BILLER PLATFORM

FINAL LOCKED SPECIFICATION

==================================================

STATUS

LOCKED

APPROVED

Architecture Complete

No Further Redesign Authorized

Future Changes Must Be Enhancements Only

==================================================

GLOBAL PLATFORM HIERARCHY

==================================================

SNS Tech Solutions

├── Owner Platform

├── Biller Platform

├── AI Operations Center

├── Revenue & Subscription Management

├── Governance & Audit Center

└── Platform Settings

--------------------------------------------------

SNS Hospice Solutions

├── Love & Faith Hospice

├── Angela Hospice

├── Silva Hospice

└── Future Hospice Agencies

==================================================

BRANDING RULE

==================================================

ALL BILLER PLATFORM SCREENS

Must display:

SNS Tech Solutions

Biller Platform

Do NOT display:

SNS Hospice Solutions

Biller Platform

==================================================

TENANT CONTEXT RULE

==================================================

Display:

SNS Hospice Solutions Tenant

Current Agency:

Angela Hospice (Training)

Examples:

Love & Faith Hospice (Production)

Angela Hospice (Training)

Silva Hospice (Demo)

==================================================

BILLING DASHBOARD

LOCKED SPECIFICATION

==================================================

MISSION

The Billing Dashboard answers:

- Where is the money?

- What money is blocked?

- What money is at risk?

- What should be worked first?

- What affects cash flow?

- What can be recovered today?

Platform:

SNS Tech Solutions

Biller Platform

==================================================

SECTION 1

EXECUTIVE REVENUE SUMMARY

==================================================

Display:

Ready Revenue

Blocked Revenue

Revenue At Risk

Pending Payments

Expected Weekly Collections

Denied Revenue

Recovery Opportunities

DDE Exceptions

Each KPI displays:

Revenue Amount

Patient Count

Trend

==================================================

SECTION 2

TODAY'S WORK QUEUE

==================================================

Display:

Claims Ready To Submit

NOEs Due Today

Orders Awaiting Signature

Denials Awaiting Appeal

Eligibility Reviews

Payment Posting Queue

DDE Responses Pending

DDE Eligibility Reviews

DDE Status Checks

DDE Exception Resolution

==================================================

SECTION 3

BILLING PRIORITIES

==================================================

Priority 1

Unsigned Orders

--------------------------------------------------

Priority 2

NOEs Near Deadline

--------------------------------------------------

Priority 3

Denied Claims

--------------------------------------------------

Priority 4

Missing Face-to-Face

--------------------------------------------------

Priority 5

Eligibility Risks

Each displays:

Revenue Impact

Patient Count

Required Action

==================================================

SECTION 4

CASH FORECAST

==================================================

Display:

This Week

This Month

Delayed Revenue

Recovery Opportunities

Projected Total

==================================================

SECTION 5

REVENUE PIPELINE

==================================================

Display:

Ready

Submitted

Accepted

Paid

Denied

Each stage displays:

Claim Count

Revenue Amount

==================================================

SECTION 6

COLLECTIONS SUMMARY

==================================================

Display:

Payments Posted

Pending Clearinghouse

Credit Balances

Follow-Up Required

Expected Weekly Release

==================================================

SECTION 7

REVENUE AT RISK ANALYSIS

==================================================

Display:

Unsigned Orders

Delayed NOE Submissions

Face-to-Face Deficiencies

Eligibility Problems

Documentation Gaps

--------------------------------------------------

DDE Risks

DDE Eligibility Conflict

DDE Verification Required

DDE Status Unknown

DDE Response Pending

DDE Submission Failure

Each displays:

Patients

Revenue Impact

Urgency

Resolution Track

==================================================

SECTION 8

DENIAL HEALTH OVERVIEW

==================================================

Display:

Denied Claims Active

Estimated Recovery

Average Aging

Historical Success Rate

==================================================

SECTION 9

TOP DENIAL REASONS

==================================================

Display:

Reason Code

Claim Count

Revenue Impact

Current Resolution Status

==================================================

SECTION 10

ASSIGNED VISIBILITY

==================================================

Display:

Billing Organization

Current Agency

Assigned Biller

DDE Authorized

Examples:

North East Billing Center

Current Agency:

Angela Hospice

Assigned Biller:

Alex

DDE Authorized:

YES

==================================================

SECTION 11

ASSIGNED AGENCY REGISTRY

==================================================

Display:

Assigned Agencies Only

Examples:

Love & Faith Hospice

(Production)

Angela Hospice

(Training)

Silva Hospice

(Demo)

This section was renamed from:

Tenant Agency Registry

to:

Assigned Agency Registry

==================================================

SECTION 12

RECENT BILLING EVENTS & RELEASES

==================================================

Display:

Revenue Released

Claim Released

Payment Posted

NOE Received

Appeal Drafted

Eligibility Cleared

Order Correction

DDE Events

Examples:

Order Signed

Revenue Released:

$34,200

--------------------------------------------------

Certification Completed

Revenue Released:

$14,200

==================================================

BILLING READINESS

LOCKED SPECIFICATION

==================================================

MISSION

Billing Readiness is:

Revenue Readiness Center

Revenue Protection Center

Revenue Unlock Center

It answers:

Why can't I bill?

What is missing?

Who owns the fix?

How much revenue is affected?

What revenue becomes available when resolved?

==================================================

SECTION 1

REVENUE READINESS SUMMARY

==================================================

Display:

Ready Revenue

Partially Ready Revenue

Blocked Revenue

Revenue At Risk

Revenue Unlock Opportunity

==================================================

SECTION 2

TODAY'S WORK QUEUE

==================================================

Display:

Orders Awaiting Signature

Certifications Awaiting Completion

Face-to-Face Missing

Eligibility Reviews

NOEs

DDE Verification Required

DDE Eligibility Reviews

DDE Exception Queue

---

## Status

LOCKED / APPROVED. **Content is partial** — the source specification
was cut off mid-Section 2 of the Billing Readiness locked
specification. Everything above (Global Platform Hierarchy, Branding
Rule, Tenant Context Rule, the full Billing Dashboard locked
specification Sections 1-12, and Billing Readiness Sections 1-2) is
captured verbatim as locked/approved. The remainder of Billing
Readiness is pending and should be appended when supplied. Locked
status governs naming/structure/scope; it does not by itself authorize
code, UI, or data model changes — implement only when explicitly
instructed.

## Relationship to Other Documents

- Reaffirms and applies
  `docs/architecture/SNS_TECH_SOLUTIONS_PLATFORM_HIERARCHY.md`: the
  Biller Platform belongs to SNS Tech Solutions, not SNS Hospice
  Solutions, and every screen must display "SNS Tech Solutions Biller
  Platform" branding — never "SNS Hospice Solutions Biller Platform".
- Locks in the tenant-agency classification (Production / Training /
  Demo) already established for Love & Faith Hospice, Angela Hospice,
  and Silva Hospice in
  `docs/production/PRODUCTION_READINESS_CLEANUP_CHECKLIST.md`
  (Permanent Testing and Training Agencies; Production Data Migration
  Strategy) and displays it directly in the Tenant Context Rule and
  Section 11 (Assigned Agency Registry).
- Supersedes/finalizes the draft in
  `docs/biller-platform/TENANT_BILLER_DASHBOARD_SPECIFICATION.md`:
  this document is the LOCKED, approved version of that dashboard
  (renumbered/refined into 12 sections, with DDE-specific queues and
  risks added throughout per the DDE Architecture Rule and DDE
  Visibility Rule in `SNS_TECH_SOLUTIONS_PLATFORM_HIERARCHY.md`), plus
  a new locked Billing Readiness specification.
- Section 11's rename from "Tenant Agency Registry" to "Assigned
  Agency Registry" reinforces the assignment-based visibility model in
  `docs/roadmap/Biller-Platform-Roadmap.md`'s Biller Platform Tenant
  Visibility Rule — billers see only agencies assigned to their
  billing organization, never a global tenant list.
- The Billing Readiness section's mission (Revenue Readiness /
  Protection / Unlock Center) is the Biller Platform's counterpart to
  the "Billing Readiness Concepts" already listed in scope in
  `docs/roadmap/Biller-Platform-Roadmap.md`.

## Change Log

| Date | Change |
|---|---|
| 2026-09-16 | Document created — Biller Platform Final Locked Specification (partial): Global Platform Hierarchy, Branding Rule, Tenant Context Rule, full Billing Dashboard locked specification (Sections 1-12: Executive Revenue Summary, Today's Work Queue, Billing Priorities, Cash Forecast, Revenue Pipeline, Collections Summary, Revenue At Risk Analysis with DDE Risks, Denial Health Overview, Top Denial Reasons, Assigned Visibility, Assigned Agency Registry, Recent Billing Events & Releases), and the start of the Billing Readiness locked specification (Mission, Section 1 Revenue Readiness Summary, Section 2 Today's Work Queue). Remainder of Billing Readiness pending. |
