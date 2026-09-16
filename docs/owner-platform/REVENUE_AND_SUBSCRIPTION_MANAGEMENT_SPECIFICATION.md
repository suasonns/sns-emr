==================================================

REVENUE & SUBSCRIPTION MANAGEMENT

OWNER PLATFORM

==================================================

STATUS

Approved Future Design Specification

Purpose:

Manage how SNS earns revenue.

Track subscriptions.

Track feature enablement.

Track AI consumption.

Track revenue-sharing agreements.

Track invoices.

This page is NOT a billing operations page.

==================================================

MISSION

==================================================

Revenue & Subscription Management answers:

- Who is subscribed?

- What are they paying for?

- What features are enabled?

- What AI services are enabled?

- What revenue sharing agreements exist?

- What invoices are outstanding?

- What revenue does SNS generate?

The page does NOT answer:

- How claims are processed

- Billing readiness

- Eligibility

- Collections

- Denials

- Payment posting

- Aging reports

- Authorization tracking

- EDI processing

Those belong to the future Biller Platform.

==================================================

CORE ARCHITECTURE RULE

==================================================

OWNER PLATFORM

Manages:

WHAT agencies pay for.

BILLER PLATFORM

Manages:

HOW claims get paid.

These responsibilities must never be mixed.

==================================================

DASHBOARD OVERVIEW

==================================================

Top Executive Cards

Display:

Monthly Recurring Revenue

Outstanding Invoices

Active Agencies

Revenue Sharing Revenue

Active AI Features

Pending Renewals

Purpose:

Executive subscription visibility.

==================================================

SECTION 1

AGENCY SUBSCRIPTIONS

==================================================

Display all agencies.

For each agency display:

Agency Name

Status

Subscription Plan

Billing Model

AI Enabled

Invoice Status

Monthly Revenue

Examples:

Love & Faith Hospice

Angela Hospice

Silva Hospice

Future Agencies

==================================================

SECTION 2

BASE SUBSCRIPTION

==================================================

Per Agency

Display:

SNS Hospice Solutions Standard

Status

Subscription Start Date

Subscription Renewal Date

Base Monthly Fee

Plan Status

Purpose:

Track the core EMR subscription.

==================================================

SECTION 3

BILLING MODULE STATUS

==================================================

Per Agency

Display:

Billing Module Enabled

Billing Provider

North East Billing

External Billing Provider

No Billing Module

Rules:

If agency uses North East Billing:

Billing Module Fee may be waived.

If agency uses external billing:

Platform Billing Access Fee may apply.

==================================================

SECTION 4

REVENUE SHARING MANAGEMENT

==================================================

Purpose:

Track North East Billing revenue sharing agreements.

Per Agency

Display:

Billing Organization

Revenue Share %

Contract Start Date

Status

Example:

Angela Hospice

Billing Organization:

North East Billing

Revenue Share:

0.20%

Future Metrics:

Billing Revenue

SNS Revenue Share

Payment Status

==================================================

SECTION 5

AI FEATURE MANAGEMENT

==================================================

Per Agency

Display:

OCR

Document Intelligence

Speech

Evidence Harvester

AI Documentation

Clinical Intelligence

Future AI Modules

Status:

Enabled

Disabled

Available For Subscription

Purpose:

Display entitlement and usage.

==================================================

SECTION 6

AI CONSUMPTION INTELLIGENCE

==================================================

Track usage first.

Pricing comes later.

Display:

OCR Documents Processed

Document Intelligence Runs

Speech Minutes

Evidence Harvest Runs

AI Documentation Requests

Clinical Intelligence Requests

Purpose:

Understand real-world consumption before pricing strategies are established.

==================================================

SECTION 7

FEATURE ENABLEMENT MATRIX

==================================================

Per Agency

Display:

EMR Standard

Billing Module

OCR

Document Intelligence

Speech

AI Documentation

Evidence Harvester

Clinical Intelligence

Future Products

SNS Home Health

SNS Scribe

Purpose:

Provide a simple subscription overview.

==================================================

SECTION 8

INVOICES & PAYMENTS

==================================================

Display:

Outstanding Invoices

Paid Invoices

Renewals

Subscription Changes

Payment Status

Purpose:

Revenue visibility.

Not claims visibility.

==================================================

SECTION 9

REVENUE INTELLIGENCE

==================================================

Track:

Base Subscription Revenue

AI Revenue

Billing Module Revenue

Revenue Sharing Revenue

Projected Monthly Revenue

Projected Annual Revenue

Purpose:

Platform financial planning.

==================================================

FUTURE COST INTELLIGENCE

==================================================

Not required immediately.

Add after production usage data exists.

Track:

OCR Cost Trend

Speech Cost Trend

Document Intelligence Cost Trend

Evidence Harvester Cost Trend

Clinical Intelligence Cost Trend

Platform Cost per Agency

Azure Consumption Trends

Purpose:

Understand cost before establishing final pricing models.

==================================================

REMOVE FROM OWNER PLATFORM

==================================================

These items belong to the future Biller Platform and must be removed from Revenue & Subscription Management:

Billing Readiness

Claims

Eligibility

Authorization Tracking

Payment Posting

Collections

Denials

EDI

Cap Monitoring

Aging Reports

Financial Monitoring

Revenue Cycle Operations

Claim Lifecycle

==================================================

DESIGN RULE

==================================================

Revenue & Subscription Management manages:

Revenue

Subscriptions

Feature Access

Licensing

AI Consumption

Revenue Sharing

Invoices

It does NOT manage:

Claims

Reimbursement

Collections

Authorizations

Patient Billing Operations

==================================================

OWNER PLATFORM VIEW

==================================================

When the Platform Owner opens this page they should immediately understand:

Who is paying?

What are they paying for?

What products are enabled?

What AI services are enabled?

How much revenue SNS generates?

What revenue-sharing agreements exist?

What invoices require attention?

==================================================

APPROVED FUTURE DIRECTION

==================================================

Owner Platform

=

Revenue & Subscription Management

Future Biller Platform

=

Billing Operations Management

Maintain strict separation.

No architecture drift allowed.

---

## Status

Approved Future Design Specification. This document defines the
target structure of the Owner Platform "Revenue & Subscription
Management" page (dashboard overview + 9 sections + future cost
intelligence + explicit removals). Approval of the design does not by
itself authorize the code/UI/data model changes — implement each
section only when explicitly instructed to build it.

## Relationship to Other Documents

- Directly builds on
  `docs/owner-platform/BILLING_AND_LICENSING_MANAGEMENT_SCOPE.md`:
  that document establishes the 7 questions Owner Platform billing
  must answer and the Do Not Build list; this document is the
  concrete page design that answers those questions (Sections 1-9)
  while enforcing the same Do Not Build boundary (Remove From Owner
  Platform list here matches it exactly) and adding the same
  subscriptions -> feature enablement -> consumption -> pricing-later
  build order (Section 6 / Future Cost Intelligence).
- The Core Architecture Rule ("Owner Platform manages WHAT agencies
  pay for; Biller Platform manages HOW claims get paid") is the same
  boundary defined in `docs/roadmap/Biller-Platform-Roadmap.md`
  (Batch Billing, Managed Billing, DDE Workflow Concepts, Revenue
  Cycle Vision, Claim Lifecycle Concepts) and
  `docs/roadmap/Owner-Platform-Roadmap.md` ("Owner Platform Does Not
  Contain: ... Billing Operations, DDE Operations").
- Section 1 (Agency Subscriptions) and Section 4 (Revenue Sharing
  Management) reference the same agencies established in
  `docs/production/PRODUCTION_READINESS_CLEANUP_CHECKLIST.md`: Love &
  Faith Hospice (first production validation agency), Angela Hospice
  and Silva Hospice (permanent synthetic testing/training agencies),
  and North East Billing as an example revenue-sharing billing
  organization.
- Section 5 (AI Feature Management) and its Enabled / Disabled /
  Available For Subscription states are the same tri-state Feature
  Flag model required in
  `docs/owner-platform/PLATFORM_SETTINGS_SPECIFICATION.md` (Required
  Future Enhancement 1) — Platform Settings defines the flag states,
  this page is where per-agency entitlement is managed against them.
- Section 7 (Feature Enablement Matrix)'s "Future Products" row (SNS
  Home Health, SNS Scribe) anticipates the Future Organizational
  Structure in
  `docs/governance/APPROVAL_AND_ESCALATION_STRUCTURE.md`.
- Section 9 (Revenue Intelligence) and Future Cost Intelligence should
  feed candidate entries into
  `docs/roadmap/Future-Ideas-And-Research.md` once enough production
  usage data exists to propose pricing changes.

## Change Log

| Date | Change |
|---|---|
| 2026-09-16 | Document created — Revenue & Subscription Management approved future design specification: Mission, Core Architecture Rule (Owner Platform = WHAT agencies pay for; Biller Platform = HOW claims get paid), Dashboard Overview, 9 sections (Agency Subscriptions, Base Subscription, Billing Module Status, Revenue Sharing Management, AI Feature Management, AI Consumption Intelligence, Feature Enablement Matrix, Invoices & Payments, Revenue Intelligence), Future Cost Intelligence (deferred until production usage data exists), an explicit Remove From Owner Platform list matching the Biller Platform's future scope, Design Rule, Owner Platform View, and Approved Future Direction statement. |
