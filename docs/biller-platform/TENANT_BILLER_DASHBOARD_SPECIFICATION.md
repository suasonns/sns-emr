==================================================

TENANT BILLER DASHBOARD

BILLER PLATFORM

==================================================

STATUS

Approved Design Baseline

Platform:

Biller Platform

User Types:

- Billing Staff

- Billing Managers

- Revenue Cycle Staff

- Collections Staff

- Payment Posting Staff

==================================================

ARCHITECTURE PRINCIPLE

==================================================

This dashboard belongs to:

TENANT BILLER PLATFORM

NOT

OWNER PLATFORM

NOT

SNS TECH SOLUTIONS OWNER PORTAL

This dashboard operates on:

Assigned Agency Billing Operations

Visibility is assignment-based.

==================================================

MISSION

==================================================

When a biller logs in, the dashboard must answer:

1. What money is available?

2. What money is blocked?

3. What money is at risk?

4. What should I work on first?

5. What can I submit today?

6. What can I recover today?

7. What will impact collections?

8. What will impact cash flow?

The dashboard is a:

Revenue Operations Command Center

NOT

A Claim Statistics Dashboard.

==================================================

ASSIGNMENT-BASED VISIBILITY

==================================================

Billers only see agencies assigned to them.

Example:

North East Billing

Assigned Agencies:

- Love & Faith Hospice

- Angela Hospice

- ABC Hospice

Visible:

YES

--------------------------------------------------

Not Assigned:

- XYZ Hospice

- External Billing Agencies

- Self-Billing Agencies

Visible:

NO

==================================================

OWNER PLATFORM RELATIONSHIP

==================================================

Owner Platform Responsibilities:

- Create Tenant

- Classify Tenant

- Assign Billing Model

- Assign Billing Organization

- Assign Revenue Share

- Enable Managed Billing

--------------------------------------------------

Biller Platform Responsibilities:

- Claims

- Eligibility

- Payment Posting

- NOE

- Denials

- Appeals

- Collections

- Revenue Cycle Operations

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

Each KPI should display:

Revenue Amount

Claim Count

Trend

Purpose:

Immediate financial visibility.

==================================================

SECTION 2

BILLING PRIORITIES CENTER

==================================================

Most Important Operational Section

Display:

Priority 1

Unsigned Orders

Potential Revenue

Affected Patients

--------------------------------------------------

Priority 2

NOEs Near Deadline

Potential Revenue

Affected Patients

--------------------------------------------------

Priority 3

Denied Claims

Potential Recovery

Affected Claims

--------------------------------------------------

Priority 4

Missing Face-to-Face

Potential Revenue Impact

--------------------------------------------------

Priority 5

Eligibility Risks

Potential Revenue Impact

Purpose:

Direct immediate biller attention.

==================================================

SECTION 3

TODAY'S BILLER WORK QUEUE

==================================================

Display:

Claims Ready To Submit

NOEs Due Today

Orders Awaiting Signature

Denials Awaiting Appeal

Eligibility Checks Required

Payment Posting Backlog

Purpose:

Daily workflow management.

==================================================

SECTION 4

REVENUE LIFECYCLE PIPELINE

==================================================

Display:

Ready

Submitted

Accepted

Paid

Denied

Each stage shows:

Claim Count

Revenue Amount

Potential Revenue

Purpose:

Visualize revenue movement.

Claim counts alone are insufficient.

==================================================

SECTION 5

REVENUE AT RISK CENTER

==================================================

Display:

NOE Deadlines

Missing Certifications

Unsigned Orders

Face-to-Face Issues

Eligibility Risks

Timely Filing Risks

For each item:

Volume

Revenue Impact

Risk Description

Urgency

Resolution Path

Purpose:

Identify reimbursement risks before revenue loss occurs.

==================================================

SECTION 6

DENIAL RECOVERY CENTER

==================================================

Display:

Open Denials

Potential Recovery Value

Average Denial Age

Appeal Success Rate

Top Denial Reasons

Most Recoverable Claims

Recovery Probability

Purpose:

Transform denials into recovery opportunities.

==================================================

SECTION 7

COLLECTIONS COMMAND CENTER

==================================================

Display:

Payments Posted Today

Pending Payments

Credit Balance Issues

Accounts Requiring Follow-Up

Expected Weekly Collections

Expected Monthly Collections

Purpose:

Collections visibility.

==================================================

SECTION 8

CASH FORECAST

==================================================

Display:

Expected This Week

Expected This Month

Potential Delayed Revenue

Potential Recovery Revenue

Projected Monthly Collections

Purpose:

Forward-looking revenue forecasting and cash-flow visibility.

==================================================

SECTION 9

ASSIGNED VISIBILITY PANEL

==================================================

Display:

Billing Organization

Assigned Agencies

Current Agency Context

Example:

Billing Organization:

North East Billing

Assigned Agencies:

- Love & Faith Hospice

- ABC Hospice

- Angela Hospice

Current View:

Angela Hospice

Purpose:

Reinforce assignment-based visibility and compliance requirements.

==================================================

SECTION 10

SYSTEM ACTIVITY FEED

==================================================

Display:

Claims Submitted

Payments Posted

NOEs Filed

Appeals Filed

Claim Rejections

Eligibility Checks

Order Verifications

Purpose:

Operational awareness and audit tracking.

Examples:

Claim Submitted

Payment Posted

Eligibility Recheck

NOE Triggered

Appeal Submitted

Order Verification

==================================================

KEEP EXISTING SIDEBAR

==================================================

Keep:

Billing Readiness

Claims

Denials & Appeals

Eligibility

Payment Posting

NOE Tracking

CAP Calculation

Aging Report

Credit Balance Report

Facility Collections

Reports

Settings

These remain operational billing functions.

==================================================

FUTURE AI BILLING INTELLIGENCE

==================================================

Future Enhancement

Not Required For Initial Release

Future Features:

OCR Claim Review

Missing Documentation Detection

Denial Pattern Analysis

Revenue Risk Prediction

AI Billing Assistant

Claim Readiness Review

Appeal Recommendations

Revenue Recovery Recommendations

==================================================

REMOVE

==================================================

Do NOT include:

Agency Health Scores

Platform Revenue

Tenant Subscription Management

Feature Licensing

Revenue Sharing Management

AI Cost Intelligence

Cross-Tenant Executive Reporting

Owner Platform Revenue Metrics

These belong to:

Owner Platform

Revenue & Subscription Management

AI Operations Center

Analytics

==================================================

SUCCESS CRITERIA

==================================================

A biller opening the dashboard must immediately know:

- Where the money is

- What money is blocked

- What money is at risk

- What needs attention first

- What revenue can be recovered

- What affects collections

- What affects cash flow

==================================================

SECTION 11

AUTHORIZED SCOPE

==================================================

Display:

Billing Organization

Assigned Agencies

Current Agency

HIPAA Access Scope

Purpose:

Show users exactly which agencies they are authorized to access.

This section reinforces:

Minimum Necessary Access

Assignment-Based Visibility

HIPAA Compliance

Examples:

North East Billing

Assigned Agencies:

- Love & Faith Hospice

- ABC Hospice

- Angela Hospice

Viewing:

Angela Hospice (Training)

==================================================

FINAL APPROVAL

==================================================

STATUS:

APPROVED

Architecture:

Tenant Biller Dashboard

Single Agency Billing Operations

Assignment-Based Visibility

Revenue Operations Command Center

No architecture drift permitted.

Visibility follows assignment.

Access follows assignment.

Responsibility follows assignment.

---

## Status

Approved Design Baseline. Complete specification (Sections 1-11 plus
Keep Existing Sidebar, Future AI Billing Intelligence, Remove list,
Success Criteria, and Final Approval). Approval of the design does not
by itself authorize the code/UI/data model changes — implement each
section only when explicitly instructed to build it.

## Relationship to Other Documents

- Directly implements the assignment-based access model from
  `docs/roadmap/Biller-Platform-Roadmap.md`'s Biller Platform Tenant
  Visibility Rule: this dashboard only ever shows agencies explicitly
  assigned to the logged-in billing organization (e.g. North East
  Billing sees Love & Faith Hospice, Angela Hospice, ABC Hospice, but
  never XYZ Hospice or agencies on external/self billing).
- The Owner Platform Relationship section restates the boundary from
  `docs/owner-platform/BILLING_AND_LICENSING_MANAGEMENT_SCOPE.md` and
  `docs/owner-platform/REVENUE_AND_SUBSCRIPTION_MANAGEMENT_SPECIFICATION.md`:
  Owner Platform creates/classifies tenants and assigns billing
  model/organization/revenue share; this dashboard owns everything
  downstream of that assignment (claims, eligibility, payment posting,
  NOE, denials, appeals, collections, revenue cycle operations) —
  responsibilities must never be mixed.
- Belongs to the future Biller Platform scope defined in
  `docs/roadmap/Biller-Platform-Roadmap.md` (Batch Billing, Managed
  Billing, DDE Workflow Concepts, Revenue Cycle Vision, Claim
  Lifecycle Concepts) — this is the first concrete page specification
  under that roadmap area.
- References the same tenant examples established in
  `docs/production/PRODUCTION_READINESS_CLEANUP_CHECKLIST.md` (Love &
  Faith Hospice as first production validation agency; Angela Hospice
  as a permanent synthetic testing/training agency).

## Change Log

| Date | Change |
|---|---|
| 2026-09-16 | Document created — Tenant Biller Dashboard approved design baseline (partial): Architecture Principle, Mission, Assignment-Based Visibility, Owner Platform Relationship, and Sections 1-7 (Executive Revenue Summary, Billing Priorities Center, Today's Biller Work Queue, Revenue Lifecycle Pipeline, Revenue At Risk Center, Denial Recovery Center, Collections Command Center). Section 8 onward pending. |
| 2026-09-16 | Completed the specification — added Section 8 (Cash Forecast), Section 9 (Assigned Visibility Panel), Section 10 (System Activity Feed), Keep Existing Sidebar (operational billing functions to retain), Future AI Billing Intelligence (deferred), an explicit Remove list (Agency Health Scores, Platform Revenue, Tenant Subscription Management, etc. — reserved for Owner Platform pages), Success Criteria, Section 11 (Authorized Scope / HIPAA minimum-necessary-access panel), and Final Approval. Document now complete end to end. |
