==================================================
SNS GOVERNANCE MODEL
==================================================

CORE PRINCIPLE

Highest Authority ≠ Does Everything.

The Platform Owner has authority over everything but should not be responsible for performing every operational task.

Authority and responsibility are separate concepts.

Problems escalate upward.

Work is delegated downward.

==================================================
SNS HOSPICE SOLUTIONS
APPROVAL AND ESCALATION STRUCTURE
==================================================

LEVEL 1

STAFF

Responsibilities:

- Daily Operations
- Assigned Tasks
- Workflow Execution
- Documentation Activities
- Support Activities

Escalate when:

- Access unavailable
- Workflow blocked
- Decision required
- System issue identified

==================================================
LEVEL 2

TEAM LEADS / DEPARTMENT LEADS

Examples:

- Operations Lead
- Development Lead
- Support Lead
- Training Lead
- Compliance Lead

Responsibilities:

- Review issues
- Resolve routine escalation
- Approve departmental actions
- Assign resources
- Monitor performance

Escalate when:

- Cross-department impact
- Policy conflict
- High-risk issue
- Financial impact
- Security impact

==================================================
LEVEL 3

PLATFORM ADMINISTRATORS

Responsibilities:

- Platform configuration
- Staff onboarding
- Permissions
- Security reviews
- Environment oversight
- Incident investigation

Approve:

- Staff access
- Permission changes
- Administrative actions

Escalate when:

- Executive approval required
- Policy exception required
- Significant business risk exists

==================================================
LEVEL 4

PLATFORM OWNER

Current:

Romel Suason

Responsibilities:

- Strategic direction
- Product decisions
- Governance
- Major approvals
- Financial decisions
- Risk acceptance
- Final authority

Platform Owner SHOULD NOT perform:

- Daily account management
- Routine password resets
- Routine onboarding
- Routine support
- Daily operational approvals

Platform Owner intervenes only when:

- Escalation completed
- Decision authority exceeded
- Strategic direction required
- Significant risk exists

==================================================
APPROVAL MATRIX
==================================================

STAFF ACCOUNT CREATION

Approve:

Platform Administrator

Escalate:

Platform Owner only if exception exists.

--------------------------------------------------

ROLE CHANGES

Approve:

Platform Administrator

Critical role changes:

Platform Owner

--------------------------------------------------

PERMISSION CHANGES

Standard:

Platform Administrator

Privileged Access:

Platform Owner

--------------------------------------------------

NEW PRODUCT ACCESS

Approve:

Platform Owner

--------------------------------------------------

SECURITY INCIDENTS

Investigate:

Platform Administrator

Escalate:

Platform Owner

--------------------------------------------------

SYSTEM OUTAGES

Resolve:

Operations / Development

Escalate:

Platform Owner if service risk exists.

--------------------------------------------------

POLICY CHANGES

Approve:

Platform Owner

--------------------------------------------------

PLATFORM ROADMAP CHANGES

Approve:

Platform Owner

==================================================
FUTURE ORGANIZATIONAL STRUCTURE
==================================================

SNS Hospice Solutions
Own Staff
Own Operations
Own Support
Own Development

SNS Home Health
Own Staff
Own Operations
Own Support
Own Development

SNS Scribe
Own Staff
Own Operations
Own Support
Own Development

There is NO master staff pool governing all products.

Each product manages its own staffing structure.

Platform Owner may have authority across products.

Staff membership is product-specific.

==================================================
USER MANAGEMENT DESIGN RULE
==================================================

User Management must support:

- Organizational hierarchy
- Delegated authority
- Escalation paths
- Department ownership
- Accountability chains

User Management is NOT simply account creation.

User Management is the governance center for product personnel.

==================================================
FINAL GOVERNANCE PRINCIPLE
==================================================

Problems escalate upward.

Authority escalates upward.

Routine work stays at the lowest competent level.

The Platform Owner governs the organization.

The Platform Owner does not operate the organization alone.

==================================================

APPROVAL WORKFLOWS

==================================================

PURPOSE

Approval workflows ensure decisions are made at the appropriate authority level.

The goal is not control.

The goal is accountability, auditability, delegation, and scalability.

==================================================

STAFF ONBOARDING APPROVAL

==================================================

REQUESTOR

Authorized Department Lead

REQUIRED DOCUMENTATION

□ Full Name

□ Email

□ Department

□ Job Title

□ Requested Role

□ Business Justification

APPROVER

Platform Administrator

OWNER APPROVAL REQUIRED

Only for:

□ Administrator Access

□ Elevated Access

□ Cross-Department Access

□ Exception Requests

==================================================

ROLE CHANGE APPROVAL

==================================================

REQUIRED DOCUMENTATION

□ Current Role

□ Requested Role

□ Business Justification

□ Requestor

APPROVER

Platform Administrator

OWNER APPROVAL REQUIRED

□ Administrative Roles

□ Executive Roles

□ Security-Sensitive Roles

==================================================

SECURITY EVENT APPROVAL

==================================================

REQUIRED DOCUMENTATION

□ Event Description

□ Impact Assessment

□ Investigation Notes

□ Recommendation

APPROVER

Platform Administrator

OWNER APPROVAL REQUIRED

□ High Severity

□ Critical Severity

□ Policy Exception

==================================================

POLICY CHANGE APPROVAL

==================================================

REQUIRED DOCUMENTATION

□ Existing Policy

□ Proposed Change

□ Business Reason

□ Risk Assessment

APPROVER

Platform Owner

==================================================

PLATFORM CHANGE APPROVAL

==================================================

REQUIRED DOCUMENTATION

□ Feature Description

□ Business Purpose

□ Platform Impact

□ Rollback Plan

APPROVER

Platform Owner

==================================================

ROADMAP CHANGE APPROVAL

==================================================

REQUIRED DOCUMENTATION

□ Problem Being Solved

□ Expected Benefit

□ Platform Impact

□ Future Maintenance Impact

APPROVER

Platform Owner

==================================================

ESCALATION SEVERITY LEVELS

==================================================

SEVERITY 1

LOW

Examples:

□ User Question

□ Training Issue

□ Minor Configuration Issue

Target Resolution

5 Business Days

Escalation

Department Lead

--------------------------------------------------

SEVERITY 2

MEDIUM

Examples:

□ Workflow Issue

□ Non-Critical Alert

□ Documentation Friction

□ User Access Issue

Target Resolution

3 Business Days

Escalation

Platform Administrator

--------------------------------------------------

SEVERITY 3

HIGH

Examples:

□ Service Disruption

□ Security Concern

□ Workflow Failure

□ Failed Production Process

Target Resolution

1 Business Day

Escalation

Platform Administrator

Owner Notified

--------------------------------------------------

SEVERITY 4

CRITICAL

Examples:

□ Data Integrity Risk

□ Data Loss Risk

□ Backup Failure

□ Restore Failure

□ Tenant Isolation Failure

□ Security Breach

□ Production Outage

Target Resolution

Immediate Response

Escalation

Platform Owner

Required

==================================================

ESCALATION TIMELINES

==================================================

LOW

Initial Review

Within 5 Business Days

--------------------------------------------------

MEDIUM

Initial Review

Within 3 Business Days

--------------------------------------------------

HIGH

Initial Review

Within 1 Business Day

--------------------------------------------------

CRITICAL

Immediate Review

Immediate Escalation

Immediate Notification

==================================================

REQUIRED ESCALATION DOCUMENTATION

==================================================

Every escalation must contain:

□ Date

□ Requestor

□ Severity

□ Description

□ Business Impact

□ Evidence

□ Resolution Recommendation

==================================================

OWNER INTERVENTION RULE

==================================================

Platform Owner becomes involved when:

□ Escalation authority exceeded

□ Financial risk exists

□ Strategic decision required

□ Security risk exists

□ Data integrity risk exists

□ Production stability risk exists

Platform Owner does NOT participate in:

□ Routine support

□ Routine onboarding

□ Routine password resets

□ Routine staff management

==================================================

FINAL GOVERNANCE RULE

==================================================

Problems are solved at the lowest competent level.

Issues escalate upward only when:

□ Authority is exceeded

□ Risk increases

□ Impact increases

□ Governance requires it

The purpose of escalation is resolution.

The purpose of authority is governance.

Higher authority reviews, approves, governs, and intervenes.

Higher authority does not perform every operational task.

---

## Status

Planning artifact — governance model, not an implemented feature. This
document defines the organizational approval/escalation structure and
the User Management design rule it implies. It does not authorize any
code changes on its own.

## Relationship to Other Documents

- Formalizes the "SNS Governance Rule" principle (authority exists to
  approve/escalate/override/govern, not to perform every operational
  task; authority and responsibility are distinct) as the platform's
  standing governance model.
- The User Management Design Rule here should be checked against
  `docs/roadmap/Owner-Platform-Roadmap.md` before building or changing
  any user/staff management feature — user management is the
  governance center for product personnel, not simple account
  creation.
- The Approval Matrix governs who may approve items referenced
  elsewhere in the roadmap/production documentation, including
  Section 12 (Production Approval), Section 17 (Production Sign-Off
  Criteria), and the Production Data Migration Strategy in
  `docs/production/PRODUCTION_READINESS_CLEANUP_CHECKLIST.md` —
  platform roadmap changes and policy changes require Platform Owner
  approval; routine account/permission actions do not.
- The Future Organizational Structure section (SNS Hospice Solutions,
  SNS Home Health, SNS Scribe as separate staffing pools under one
  Platform Owner) is a future-development concept per the roadmap
  repository's rule: it is not to be implemented unless explicitly
  instructed.

## Change Log

| Date | Change |
|---|---|
| 2026-09-16 | Document created — SNS Governance Model core principle, four-level Approval and Escalation Structure (Staff, Team/Department Leads, Platform Administrators, Platform Owner), Approval Matrix, Future Organizational Structure (SNS Hospice Solutions / SNS Home Health / SNS Scribe as separate per-product staffing pools), User Management Design Rule, and Final Governance Principle. |
| 2026-09-16 | Added Approval Workflows section — per-workflow required documentation and approvers for Staff Onboarding, Role Change, Security Event, Policy Change, Platform Change, and Roadmap Change approvals; four-level Escalation Severity Levels (Low/Medium/High/Critical) with examples, target resolution times, and escalation paths; Escalation Timelines; Required Escalation Documentation; Owner Intervention Rule; and Final Governance Rule. |
