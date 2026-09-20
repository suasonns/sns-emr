# Biller Platform Roadmap

Status: Planning artifact — future-development repository.
**Do not implement items from this document unless explicitly instructed.**

## Mission

Protect Revenue.
Protect Compliance.
Protect Auditability.
Reduce Billing Friction.

## In Scope

- Batch Billing
- Managed Billing
- DDE Workflow Concepts
- Revenue Cycle Vision
- Eligibility Concepts
- Audit Shield Billing Concepts
- Billing Readiness Concepts
- Claim Lifecycle Concepts

## Relationship to Other Roadmaps

Billing operations and DDE operations are explicitly out of scope for
the Owner Platform Roadmap. Audit Shield billing concepts here should
stay consistent with (not duplicate) the general provenance/audit
model described in `Audit-Shield-And-Compliance-Roadmap.md`.

The Biller Platform Tenant Visibility Rule below is the assignment-
based access counterpart to the Owner Platform's tenant/agency
management described in `Owner-Platform-Roadmap.md` and the tenant
examples (Love & Faith Hospice, Angela Hospice, Silva Hospice) in
`docs/production/PRODUCTION_READINESS_CLEANUP_CHECKLIST.md` — the
Owner Platform assigns billing organizations/billers, the Biller
Platform only ever operates on the tenants assigned to it.

## Future Concepts

_(Log future ideas here once they graduate from
`Future-Ideas-And-Research.md`. Each entry should note date added,
problem being solved, expected benefit, and status — see that
document's format.)_

### Biller Platform Tenant Visibility Rule

Date Added: 2026-09-16
Status: Approved Future Concept

The Biller Platform does NOT automatically have access to all tenant agencies.

Visibility is assignment-based.

==================================================

OWNER PLATFORM RESPONSIBILITIES

==================================================

SNS Tech Solutions creates tenants.

SNS Tech Solutions determines billing model.

SNS Tech Solutions assigns billing organizations.

SNS Tech Solutions assigns billers.

==================================================

EXAMPLE

==================================================

Love & Faith Hospice

Billing Model:

SNS Managed Billing

Assigned To:

North East Billing

Visible In Biller Platform:

YES

--------------------------------------------------

Angela Hospice

Billing Model:

SNS Managed Billing

Assigned To:

North East Billing

Visible In Biller Platform:

YES

--------------------------------------------------

ABC Hospice

Billing Model:

External Biller

Assigned To:

External Billing Provider

Visible In North East Billing Platform:

NO

--------------------------------------------------

XYZ Hospice

Billing Model:

Self Billing

Assigned To:

None

Visible In North East Billing Platform:

NO

==================================================

BILLER PLATFORM ACCESS

==================================================

Billers may only view:

- Agencies assigned to them

- Patients belonging to those agencies

- Billing-related data required for their job

Access is determined by:

Agency Assignment

NOT

Global Tenant Visibility

==================================================

ARCHITECTURE RULE

==================================================

Owner Platform

=

Controls Tenant Assignments

Biller Platform

=

Operates Only On Assigned Tenants

No biller should ever see tenants that are not assigned to that billing organization.

Visibility follows assignment.

Access follows assignment.

Responsibility follows assignment.

- No further entries yet.

## Change Log

| Date | Change |
|---|---|
| 2026-09-16 | Document created as part of the permanent roadmap repository. |
| 2026-09-16 | Added Biller Platform Tenant Visibility Rule to Future Concepts — access to tenant agencies is assignment-based (Owner Platform/SNS Tech Solutions creates tenants and assigns billing organizations/billers), not automatic; billers may only view agencies, patients, and billing data for tenants explicitly assigned to them. |
