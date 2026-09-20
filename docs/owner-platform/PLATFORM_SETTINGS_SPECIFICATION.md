==================================================

PLATFORM SETTINGS

OWNER PLATFORM

==================================================

STATUS

Approved Design Baseline

Purpose:

Platform Settings serves as the SNS Global Configuration Center.

This page controls how SNS operates as a platform.

==================================================

MISSION

==================================================

Platform Settings answers:

- How does SNS operate?

- What platform-wide rules exist?

- What AI services are enabled?

- What governance policies are active?

- What integrations are connected?

- What backup and recovery standards exist?

- What security standards are enforced?

Platform Settings does NOT manage:

- Tenants

- Users

- Revenue

- Licensing

- Billing Operations

- Clinical Workflows

Those belong elsewhere.

==================================================

APPROVED SECTIONS

==================================================

SECTION 1

PRODUCT CONFIGURATION

Purpose:

Global product configuration.

Contains:

- Platform Identity

- Feature Flags

- Tenant Provisioning Defaults

- Session Defaults

- Security Defaults

Examples:

Platform Name

Environment

Support Email

Version

Timezone

Session Timeout

Authentication Rules

==================================================

SECTION 2

AI CONFIGURATION

Purpose:

Global AI governance and resource management.

Contains:

- Foundation Models

- OCR Configuration

- Speech Configuration

- Evidence Harvester

- AI Documentation

- Clinical Intelligence

- Safety Guardrails

Examples:

AI Model

Token Limits

OCR Allocation

Speech Allocation

Safety Controls

PHI Protections

==================================================

SECTION 3

PLATFORM POLICIES

Purpose:

Platform-wide operational and governance rules.

Contains:

Access Control

Compliance Frameworks

Data Governance

Operational Policies

Examples:

HIPAA Policies

SOC2 Policies

Immutable Audit Policies

Data Residency Policies

Retention Requirements

==================================================

SECTION 4

STORAGE & RETENTION

Purpose:

Storage planning and retention governance.

Contains:

Document Storage

Retention Schedules

Storage Alerts

Lifecycle Policies

Examples:

Storage Allocation

Retention Rules

Storage Growth Monitoring

Archival Policies

==================================================

SECTION 5

BACKUP & RECOVERY

Purpose:

Platform continuity and disaster recovery.

Contains:

Backup Schedule

Recovery Objectives

Disaster Recovery

Restore Validation

Examples:

RPO

RTO

Replication Status

Last Restore Verification

Recovery Testing

==================================================

SECTION 6

INTEGRATION MANAGEMENT

Purpose:

External dependency management.

Contains:

Healthcare Integrations

AI Integrations

Communication Integrations

Platform APIs

Current Examples:

DDE

Palmetto

CGS

AWS

SendGrid

Future Examples:

Azure OpenAI

Azure Speech

Azure OCR

Azure Document Intelligence

Evidence Harvester Services

==================================================

SECTION 7

NOTIFICATION POLICIES

Purpose:

Platform-wide alert routing and escalation.

Contains:

Notification Channels

Escalation Rules

Alert Routing

Examples:

Critical Incidents

Security Events

Backup Failures

Restore Failures

Ownership Escalations

==================================================

SECTION 8

GOVERNANCE & AUDIT

Purpose:

Global governance controls.

Contains:

Change Management

Approval Requirements

Audit Configuration

Compliance Controls

Examples:

Change Approval Rules

Production Freeze Rules

Audit Requirements

Approval Requirements

==================================================

REQUIRED FUTURE ENHANCEMENTS

==================================================

1. FEATURE FLAG STATES

Current:

Enabled

Disabled

Future:

Enabled Globally

Available For Subscription

Disabled

Reason:

Products and AI services may not be available to all agencies.

Examples:

OCR

Evidence Harvester

Clinical Intelligence

AI Documentation

==================================================

2. TENANT TEMPLATE TYPES

Add:

Production Template

Training Template

Demo Template

Reason:

SNS now officially supports:

Production Agencies

Training Agencies

Demo Agencies

Provisioning should reflect this architecture.

==================================================

3. AI PLATFORM DEPENDENCIES

Display alongside active integrations:

Azure OpenAI

Azure Speech

Azure OCR

Azure Document Intelligence

Evidence Harvester Infrastructure

These are platform-critical dependencies.

==================================================

4. ENVIRONMENT GOVERNANCE

Add New Section

Environment Governance

Purpose:

Production readiness and environment visibility.

Display:

Development Environment

Production Environment

Last Restore Test

Last Production Sweep

Last Production Readiness Review

Last Security Review

Examples:

sns_emr_dev_clean

sns_emr_prod

==================================================

REMOVE

==================================================

Current:

Viewing

All Tenants (Platform-Wide)

Remove tenant context.

Reason:

Platform Settings are global.

This page is not tenant-specific.

==================================================

DESIGN RULE

==================================================

Platform Settings configures:

SNS

Platform Settings does NOT configure:

Agencies

If a setting applies only to a tenant or agency:

It does not belong here.

==================================================

PLATFORM OWNER VIEW

==================================================

When the Platform Owner opens this page they should understand:

How SNS operates.

How SNS is secured.

How SNS is governed.

How SNS backs up data.

How SNS recovers data.

How SNS manages AI.

What dependencies exist.

---

## Status

Approved Design Baseline. This document defines the target structure
of the Owner Platform "Platform Settings" page (8 approved sections
plus 4 required future enhancements and 1 removal). Approval of the
design does not by itself authorize the code/UI changes — implement
each section/enhancement only when explicitly instructed to build it.

## Relationship to Other Documents

- Section 2 (AI Configuration) and Section 6 (Integration Management)
  should stay consistent with the AI/dependency concepts in
  `docs/roadmap/AI-Clinical-Intelligence-Roadmap.md` and the FHIR/
  integration groundwork in
  `docs/architecture/CERTIFICATION_READINESS_ARCHITECTURE.md`.
- Section 5 (Backup & Recovery) and Required Future Enhancement 4
  (Environment Governance) directly track
  `docs/production/PRODUCTION_READINESS_CLEANUP_CHECKLIST.md` Section 8
  (Backup Health) and the Environment Separation Rule
  (`sns_emr_dev_clean` permanent dev vs. fresh `sns_emr_prod`) — this
  page is where those checklist results (last restore test, last
  production sweep, last readiness review, last security review)
  should surface for the Platform Owner.
- Section 8 (Governance & Audit) is the configuration counterpart to
  `docs/governance/APPROVAL_AND_ESCALATION_STRUCTURE.md` (approval/
  escalation rules) and
  `docs/owner-platform/GOVERNANCE_AND_AUDIT_CENTER_SPECIFICATION.md`
  (the reporting/monitoring counterpart) — Platform Settings defines
  the rules, the Governance & Audit Center reports on adherence to
  them.
- Required Future Enhancement 2 (Production/Training/Demo Tenant
  Template Types) formalizes tenant provisioning for the agency
  categories already established in
  `docs/production/PRODUCTION_READINESS_CLEANUP_CHECKLIST.md`
  (Love & Faith Hospice as the production validation agency; Angela
  Hospice and Silva Hospice as permanent testing/training agencies).
- Required Future Enhancement 1 (Feature Flag States: Enabled
  Globally / Available For Subscription / Disabled) is the
  configuration mechanism behind the "What features are enabled?" and
  "What AI services are enabled?" questions in
  `docs/owner-platform/BILLING_AND_LICENSING_MANAGEMENT_SCOPE.md`.
- The Design Rule ("Platform Settings configures SNS, not Agencies")
  reinforces the Owner Platform / Tenant Platform separation already
  defined in `docs/roadmap/Owner-Platform-Roadmap.md` and
  `docs/roadmap/Tenant-Platform-Roadmap.md`.

## Change Log

| Date | Change |
|---|---|
| 2026-09-16 | Document created — Platform Settings approved design baseline: Mission, 8 Approved Sections (Product Configuration, AI Configuration, Platform Policies, Storage & Retention, Backup & Recovery, Integration Management, Notification Policies, Governance & Audit), 4 Required Future Enhancements (tri-state Feature Flags, Production/Training/Demo Tenant Template Types, AI Platform Dependencies display, new Environment Governance section), removal of tenant-context "Viewing" selector, Design Rule (SNS-level only, never agency-level), and Platform Owner View summary. |
