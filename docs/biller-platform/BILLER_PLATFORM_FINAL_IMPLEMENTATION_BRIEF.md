==================================================

SNS TECH SOLUTIONS

BILLER PLATFORM

FINAL IMPLEMENTATION BRIEF

==================================================

STATUS

APPROVED

LOCKED

Figma Approved

Implementation Authorized

No Architectural Redesigns Permitted

==================================================

FINAL PLATFORM MISSION

==================================================

The Biller Platform exists to manage:

Revenue

Claims

Eligibility

NOE

DDE Operations

Denials

Appeals

Collections

Payment Posting

Revenue Readiness

Revenue Recovery

Revenue Protection

The Biller Platform is NOT:

A clinical documentation platform.

A chart review platform.

A visit management platform.

A certification management platform.

==================================================

FINAL BRANDING STANDARD

==================================================

ALL PAGES MUST DISPLAY

SNS Tech Solutions

Biller Platform

Do NOT display:

SNS Hospice Solutions

Biller Platform

==================================================

TENANT CONTEXT STANDARD

==================================================

Display:

SNS Hospice Solutions Tenant

Current Agency:

Angela Hospice (Training)

Agency statuses:

Production

Training

Demo

==================================================

FINAL BILLING ORGANIZATION NAMING STANDARD

==================================================

LOCKED STANDARD

Use:

North East Billing Center

Do NOT mix:

North East Billing

and

North East Billing Center

The system standard name is:

North East Billing Center

Apply this naming consistently across:

Assigned Visibility

Authorized Scope

Audit Events

Reports

Exports

Future Biller Pages

Future Figma Designs

Future GitHub Specifications

==================================================

FINAL APPROVED NAVIGATION

==================================================

Dashboard

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

==================================================

REMOVED NAVIGATION

==================================================

REMOVE

Visits & Notes

Reason:

Clinical workflow page.

Not a billing workflow.

--------------------------------------------------

REMOVE

POC & Certifications

Reason:

Clinical workflow page.

Not a billing workflow.

==================================================

CLINICAL STATUS RULE

==================================================

Clinical information may influence billing.

Clinical workflow pages do not belong in the Biller Platform.

Examples:

Missing Certification

Missing Face-to-Face

Unsigned Orders

Clinical Audit Status

Documentation Deficiencies

These are surfaced through:

Billing Readiness

Revenue Unlock Priorities

Revenue At Risk

Assignment Accountability

Work Queue

Do NOT create standalone clinical navigation.

==================================================

BILLING DASHBOARD

==================================================

STATUS

LOCKED

Required Sections:

Executive Revenue Summary

Today's Work Queue

Billing Priorities

Cash Forecast

Revenue Pipeline

Collections Summary

Revenue At Risk

Denial Health Overview

Top Denial Reasons

Assigned Visibility

Assigned Agency Registry

Recent Billing Events & Releases

==================================================

BILLING READINESS

==================================================

STATUS

LOCKED

Required Sections:

Revenue Readiness Overview

DDE Health Status

Today's Work Queue

Readiness Pipeline

Revenue Unlock Forecast

Revenue Unlock Priorities

Readiness Breakdown

Assignment Accountability

Authorized Scope

Assigned Agency Registry

Revenue At Risk Analysis

Activity Feed

==================================================

DDE ARCHITECTURE

==================================================

DDE is REQUIRED.

DDE is NOT future functionality.

DDE belongs to:

SNS Tech Solutions

Biller Platform

Required DDE Visibility:

DDE Exceptions

DDE Responses Pending

DDE Eligibility Reviews

DDE Verification Required

DDE Eligibility Conflict

DDE Status Unknown

DDE Submission Failure

DDE Response Pending

DDE Resolution Tracking

==================================================

ASSIGNMENT RULE

==================================================

Visibility follows assignment.

Access follows assignment.

Responsibility follows assignment.

Billers only see:

Assigned Agencies

Assigned Work

Authorized DDE Scope

==================================================

AUTHORIZED SCOPE

==================================================

Must display:

Billing Organization

Current Agency

Assigned Biller

DDE Authorized

Assigned Agencies

Example:

North East Billing Center

Current Agency:

Angela Hospice

Assigned Biller:

Alex

DDE Authorized:

YES

==================================================

FINAL IMPLEMENTATION CHECKLIST

==================================================

BRANDING

□ SNS Tech Solutions displayed

□ Biller Platform displayed

--------------------------------------------------

NAVIGATION

□ Visits & Notes removed

□ POC & Certifications removed

--------------------------------------------------

DDE

□ DDE Health Status displayed

□ DDE Exceptions displayed

□ DDE Readiness integrated

--------------------------------------------------

ASSIGNMENT

□ Assigned Agency Registry active

□ Agencies filtered by assignment

□ DDE authorization respected

--------------------------------------------------

READINESS

□ Revenue Unlock Priorities active

□ Assignment Accountability active

□ Revenue At Risk active

--------------------------------------------------

DASHBOARD

□ Executive Revenue Summary active

□ Billing Priorities active

□ Revenue Pipeline active

□ Collections Summary active

==================================================

FINAL LOCK

==================================================

Billing Dashboard

APPROVED

LOCKED

--------------------------------------------------

Billing Readiness

APPROVED

LOCKED

--------------------------------------------------

Navigation

APPROVED

LOCKED

--------------------------------------------------

DDE Architecture

APPROVED

LOCKED

--------------------------------------------------

SNS Tech Solutions Branding

APPROVED

LOCKED

--------------------------------------------------

North East Billing Center Naming Standard

APPROVED

LOCKED

Future changes must be enhancements only.

No additional architecture redesign authorized.

---

## Status

APPROVED. LOCKED. Final Implementation Brief — this document is the
single consolidated authority for Biller Platform branding, navigation,
DDE architecture, assignment rules, and the required sections of the
Billing Dashboard and Billing Readiness pages. It restates and locks
decisions already made across prior Biller Platform documents into one
implementation-ready checklist. Approval/lock status does not itself
authorize code changes — implementation still proceeds only when
explicitly instructed, and per
`docs/biller-platform/BILLER_PLATFORM_IMPLEMENTATION_TASK_BREAKDOWN.md`
no schema or migrations are created until Phase 0 discovery
(`BILLER_PLATFORM_DISCOVERY_REPORT.md`) is complete.

## Relationship to Other Documents

- Consolidates and locks:
  `docs/biller-platform/BILLER_PLATFORM_LOCKED_SPECIFICATIONS.md`
  (Billing Dashboard and Billing Readiness locked section lists),
  `docs/biller-platform/TENANT_BILLER_DASHBOARD_SPECIFICATION.md`
  (Keep Existing Sidebar / Remove list, now amended to remove Visits &
  Notes and POC & Certifications), and
  `docs/biller-platform/BILLING_DASHBOARD_IMPLEMENTATION_SPECIFICATION.md`
  / `BILLING_READINESS_IMPLEMENTATION_SPECIFICATION.md` (data models,
  calculation rules, permission matrices already defined there).
- Restates the Clinical Status Rule first introduced as a sidebar
  correction in `TENANT_BILLER_DASHBOARD_SPECIFICATION.md`'s Remove
  list: Visits & Notes and POC & Certifications are permanently removed
  from Biller Platform navigation; clinical blockers surface only
  through Billing Readiness, Revenue Unlock Priorities, Revenue At
  Risk, Assignment Accountability, and Work Queue.
- Restates the branding hierarchy from
  `docs/architecture/SNS_TECH_SOLUTIONS_PLATFORM_HIERARCHY.md`: all
  Biller Platform pages must display "SNS Tech Solutions / Biller
  Platform", never "SNS Hospice Solutions / Biller Platform".
- Introduces a new, locked naming standard not previously codified:
  the billing organization used in prior examples must be referred to
  consistently as "North East Billing Center" (not "North East
  Billing") across all Biller Platform surfaces, audit events,
  reports, exports, and future specifications. Earlier documents
  (`BILLER_PLATFORM_LOCKED_SPECIFICATIONS.md`,
  `TENANT_BILLER_DASHBOARD_SPECIFICATION.md`,
  `docs/roadmap/Biller-Platform-Roadmap.md`) use "North East Billing"
  in their examples and are superseded by this naming standard going
  forward; they are not being retroactively edited by this commit.
- Elevates DDE from a documented future/architectural capability (see
  `docs/architecture/SNS_TECH_SOLUTIONS_PLATFORM_HIERARCHY.md`'s DDE
  Architecture Rule and DDE Visibility Rule) to a required,
  non-deferrable part of the Billing Dashboard and Billing Readiness
  pages — consistent with the discovery finding (in-progress
  `BILLER_PLATFORM_DISCOVERY_REPORT.md`) that no DDE models, routes,
  or UI currently exist in the repository; DDE remains a CREATE item.
- The Final Implementation Checklist operationalizes this brief as
  acceptance criteria for the corresponding phases in
  `docs/biller-platform/BILLER_PLATFORM_IMPLEMENTATION_TASK_BREAKDOWN.md`.

## Change Log

| Date | Change |
|---|---|
| 2026-09-16 | Document created — Final Implementation Brief: Final Platform Mission, Final Branding Standard, Tenant Context Standard, Final Billing Organization Naming Standard (locks "North East Billing Center"), Final Approved Navigation, Removed Navigation (Visits & Notes, POC & Certifications), Clinical Status Rule, locked Billing Dashboard and Billing Readiness required sections, DDE Architecture (required, not future), Assignment Rule, Authorized Scope, Final Implementation Checklist, and Final Lock. |
