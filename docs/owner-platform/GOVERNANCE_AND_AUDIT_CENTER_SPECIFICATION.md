==================================================

GOVERNANCE & AUDIT CENTER

OWNER PLATFORM

==================================================

STATUS

Future Design Specification

DO NOT IMPLEMENT UNTIL APPROVED.

Purpose:

Replace the current "Audit Logs" concept with a Governance & Audit Center focused on authority, accountability, approvals, escalation, platform governance, auditability, and risk management.

==================================================

MISSION

==================================================

The Governance & Audit Center answers:

Who did what?

Who approved it?

Who escalated it?

What changed?

What creates risk?

What requires intervention?

Can SNS governance be trusted?

The purpose is NOT:

- Activity reporting

- User login reporting

- Analytics

- Agency performance monitoring

Those belong elsewhere.

==================================================

PRIMARY DASHBOARD

==================================================

SECTION 1

GOVERNANCE OVERVIEW

Cards:

Open Approvals

Pending Escalations

Critical Events

Security Events

Policy Exceptions

Audit Shield Alerts

Purpose:

Determine whether intervention is required.

==================================================

SECTION 2

APPROVAL CENTER

==================================================

Display:

Pending Approvals

Examples:

Staff Access Request

Role Change Request

Permission Change Request

Platform Configuration Request

Policy Exception Request

For every approval display:

- Requestor

- Date Submitted

- Current Approver

- Escalation Status

- Severity

==================================================

SECTION 3

ESCALATION CENTER

==================================================

Display:

Severity 1

Severity 2

Severity 3

Severity 4

Examples:

Workflow Issue

Security Issue

Data Integrity Concern

Audit Shield Concern

Production Risk

Display:

Escalated To

Escalation Age

Target Resolution

Required Owner Action

==================================================

SECTION 4

PLATFORM CHANGE HISTORY

==================================================

Track:

Configuration Changes

RBAC Changes

Policy Changes

AI Changes

Alert Changes

Workflow Changes

Platform Releases

Display:

Changed By

Approved By

Date

Reason

Impact

Rollback Available

==================================================

SECTION 5

AUDIT SHIELD STATUS

==================================================

Display:

Evidence Provenance

Source Attribution

Version History

Correction Tracking

Immutable Storage

Document Lineage

Status:

Healthy

Warning

Critical

Any failure automatically creates:

Severity 4 Event

==================================================

SECTION 6

CRITICAL EVENTS CENTER

==================================================

Track:

Backup Failure

Restore Failure

Tenant Isolation Failure

Audit Shield Failure

Security Incident

Production Outage

Configuration Drift

Evidence Provenance Failure

Data Integrity Failure

Purpose:

Immediate executive awareness.

==================================================

SECTION 7

AUTHENTICATION EVENTS

==================================================

Track:

Successful Logins

Failed Logins

Password Resets

Account Lockouts

MFA Events

Purpose:

Security review.

NOT primary page focus.

==================================================

SECTION 8

SECURITY GOVERNANCE

==================================================

Track:

Permission Changes

Administrative Overrides

Role Changes

Privilege Escalation

Failed Access Attempts

Locked Accounts

Account Suspensions

==================================================

SECTION 9

APPROVAL HISTORY

==================================================

Historical archive:

Approved Requests

Rejected Requests

Policy Exceptions

Emergency Approvals

Owner Decisions

Approve History must be immutable.

==================================================

SECTION 10

ESCALATION HISTORY

==================================================

Historical archive:

Closed Escalations

Resolved Risks

Past Critical Events

Root Cause Reports

Resolution Reports

==================================================

FILTERS

==================================================

Replace current filters.

Use:

All Governance Events

Approvals

Escalations

Security

Audit Shield

Authentication

Platform Changes

Critical Events

Date Range

Product

SNS Hospice Solutions

SNS Home Health

SNS Scribe

Severity

1

2

3

4

==================================================

DETAIL PANEL

==================================================

Every event should display:

Event ID

Date

User

Department

Product

Action

Severity

Risk Level

Approver

Escalation Chain

Resolution Status

Evidence

Notes

==================================================

OWNER INTERVENTION RULES

==================================================

Platform Owner should only see notifications for:

Severity 4 Events

Security Breaches

Tenant Isolation Failures

Data Integrity Failures

Restore Failures

Policy Exceptions

Approval Deadlocks

Strategic Decisions

Owner should not receive routine operational events.

==================================================

AUTOMATIC ESCALATION RULES

==================================================

Automatically escalate:

Data Integrity Risk

Backup Failure

Restore Failure

Audit Shield Failure

Evidence Provenance Failure

Security Breach

Tenant Isolation Failure

These become:

Severity 4

Owner Review Required

==================================================

DESIGN PRINCIPLE

==================================================

This page is NOT:

An Audit Log Viewer.

This page IS:

The SNS Governance Center.

The page must emphasize:

Authority

Accountability

Approvals

Escalations

Governance

Auditability

Risk

Compliance

Platform Trust

The Platform Owner opens this page to determine:

What changed?

What requires approval?

What requires escalation?

What creates risk?

Do I need to intervene?

---

## Status

Future Design Specification. **DO NOT IMPLEMENT UNTIL APPROVED.** This
document defines the intended replacement for the current "Audit Logs"
page on the Owner Platform. No code, UI, or data model changes are
authorized by this document alone.

## Relationship to Other Documents

- Consolidates and operationalizes
  `docs/governance/APPROVAL_AND_ESCALATION_STRUCTURE.md` into an Owner
  Platform UI surface: the Approval Matrix, Approval Workflows, and
  Escalation Severity Levels (1-4) defined there are the data model
  this Center displays and drives (Approval Center, Escalation Center,
  Owner Intervention Rules, Automatic Escalation Rules).
- Section 5 (Audit Shield Status) surfaces the health of the systems
  already locked in `/docs/architecture/` (`ARCHITECTURE_LOCK.md`,
  `EVIDENCE_TRACEABILITY_VISION.md`) and documented in
  `docs/architecture/CERTIFICATION_READINESS_ARCHITECTURE.md` — it
  reports on those systems, it does not redefine them.
- Section 6 (Critical Events Center) and the Automatic Escalation
  Rules directly mirror the production gating concepts in
  `docs/production/PRODUCTION_READINESS_CLEANUP_CHECKLIST.md`
  (Section 16 Production Blockers; Backup/Restore/Tenant Isolation
  verification) — a failure in any of those areas should surface here
  as a Severity 4 event.
- The Filters' "Product" dimension (SNS Hospice Solutions, SNS Home
  Health, SNS Scribe) anticipates the Future Organizational Structure
  in `docs/governance/APPROVAL_AND_ESCALATION_STRUCTURE.md` and is a
  future-development concept — not to be implemented until those
  products exist.
- Belongs under the Owner Platform per
  `docs/roadmap/Owner-Platform-Roadmap.md`'s scope (platform health,
  operational intelligence) and is explicitly distinct from
  `docs/roadmap/Analytics-And-Agency-Health-Roadmap.md` (agency usage
  analytics) and clinical/tenant workflows, which this page must never
  surface.

## Change Log

| Date | Change |
|---|---|
| 2026-09-16 | Document created — full Governance & Audit Center specification: Mission, 10-section Primary Dashboard (Governance Overview, Approval Center, Escalation Center, Platform Change History, Audit Shield Status, Critical Events Center, Authentication Events, Security Governance, Approval History, Escalation History), Filters, Detail Panel, Owner Intervention Rules, Automatic Escalation Rules, and Design Principle. Status: Future Design Specification — do not implement until approved. |
