GLOBAL ARCHITECTURE RULE

SNS TECH SOLUTIONS PLATFORM HIERARCHY

STATUS

LOCKED

APPLIES TO:

- GitHub Specifications

- Figma Designs

- Product Architecture

- Future Product Development

==================================================

MASTER BRAND HIERARCHY

==================================================

The parent company is:

SNS Tech Solutions

All governance, management, analytics, revenue, AI, and billing platforms belong to:

SNS Tech Solutions

==================================================

SNS TECH SOLUTIONS PLATFORMS

==================================================

The following platforms belong to SNS Tech Solutions:

SNS Tech Solutions

Owner Platform

SNS Tech Solutions

Biller Platform

SNS Tech Solutions

AI Operations Center

SNS Tech Solutions

Revenue & Subscription Management

SNS Tech Solutions

Governance & Audit Center

SNS Tech Solutions

Platform Settings

These platforms are enterprise-level systems.

They are NOT tenant applications.

==================================================

TENANT APPLICATIONS

==================================================

Under SNS Tech Solutions sit product applications.

Current:

SNS Hospice Solutions

Future:

SNS Home Health

SNS Scribe

Future SNS Products

==================================================

TENANT AGENCIES

==================================================

Tenant agencies operate within:

SNS Hospice Solutions

Examples:

Love & Faith Hospice

Angela Hospice

Silva Hospice

ABC Hospice

Future Hospice Agencies

These agencies are tenants.

They are NOT platforms.

==================================================

CORRECT BRANDING

==================================================

CORRECT:

SNS Tech Solutions

Owner Platform

--------------------------------------------------

CORRECT:

SNS Tech Solutions

Biller Platform

--------------------------------------------------

CORRECT:

SNS Tech Solutions

AI Operations Center

--------------------------------------------------

CORRECT:

SNS Tech Solutions

Revenue & Subscription Management

==================================================

INCORRECT BRANDING

==================================================

INCORRECT:

SNS Hospice Solutions

Owner Platform

--------------------------------------------------

INCORRECT:

SNS Hospice Solutions

Biller Platform

--------------------------------------------------

INCORRECT:

SNS Hospice Solutions

AI Operations Center

==================================================

BILLER PLATFORM RULE

==================================================

The Biller Platform belongs to:

SNS Tech Solutions

The Biller Platform services agencies operating within:

SNS Hospice Solutions

Example:

SNS Tech Solutions

Biller Platform

Current Agency:

Angela Hospice (Training)

SNS Hospice Solutions Tenant

==================================================

OWNER PLATFORM RULE

==================================================

The Owner Platform governs:

Tenant Creation

Tenant Classification

Subscriptions

Revenue Sharing

Feature Licensing

AI Entitlements

Billing Assignments

Platform Governance

The Owner Platform does NOT operate hospice agencies.

==================================================

AI OPERATIONS CENTER RULE

==================================================

The AI Operations Center belongs to:

SNS Tech Solutions

The AI Operations Center governs:

Azure OpenAI

OCR

Speech

Document Intelligence

Evidence Harvester

Clinical Intelligence

Future AI Systems

Across all SNS products.

==================================================

BILLER PLATFORM RULE

==================================================

The Biller Platform belongs to:

SNS Tech Solutions

The Biller Platform manages:

Claims

Eligibility

NOE

Collections

Denials

Appeals

Payment Posting

DDE Operations

Revenue Cycle Operations

Assigned Agencies Only

==================================================

DDE ARCHITECTURE RULE

==================================================

DDE is a core Biller Platform capability.

DDE is NOT an Owner Platform feature.

DDE belongs to:

SNS Tech Solutions

Biller Platform

DDE operations include:

DDE Verification

DDE Eligibility Review

DDE Status Review

DDE Exception Resolution

DDE Response Processing

DDE Submission Validation

DDE Readiness Verification

==================================================

DDE VISIBILITY RULE

==================================================

DDE access is user-specific.

Agency visibility is assignment-based.

Example:

North East Billing

Assigned Biller:

Alex

DDE Authorized:

YES

Assigned Agencies:

Love & Faith Hospice

Angela Hospice

ABC Hospice

Only assigned agencies are visible.

==================================================

FUTURE PRODUCTS RULE

==================================================

All future SNS products inherit this architecture.

Examples:

SNS Home Health

SNS Scribe

Future Biller Products

Future AI Products

No redesign required.

Architecture remains:

SNS Tech Solutions

│

├── Owner Platform

├── Biller Platform

├── AI Operations Center

├── Revenue & Subscription

├── Governance & Audit

├── Platform Settings

│

└── Product Applications

├── SNS Hospice Solutions

├── SNS Home Health

├── SNS Scribe

└── Future Products

==================================================

FINAL RULE

==================================================

SNS Tech Solutions owns platforms.

SNS Hospice Solutions is a product.

Hospice agencies are tenants.

All future GitHub specifications and Figma designs must follow this hierarchy.

No architecture drift permitted.

---

## Status

**LOCKED.** This is a global, enterprise-wide branding and architecture
hierarchy rule. It applies to all GitHub specifications, Figma designs,
product architecture, and future product development. It is a
constraint on naming and structure, not an implementation instruction
— it does not by itself authorize any code, UI, or data model changes.

## Relationship to Other Documents

- This is the master hierarchy that every prior Owner/Biller Platform
  document in this session must be read against:
  - `docs/owner-platform/GOVERNANCE_AND_AUDIT_CENTER_SPECIFICATION.md`,
    `docs/owner-platform/ANALYTICS_AGENCY_HEALTH_INTELLIGENCE_SPECIFICATION.md`,
    `docs/owner-platform/BILLING_AND_LICENSING_MANAGEMENT_SCOPE.md`,
    `docs/owner-platform/REVENUE_AND_SUBSCRIPTION_MANAGEMENT_SPECIFICATION.md`,
    `docs/owner-platform/PLATFORM_SETTINGS_SPECIFICATION.md`, and
    `docs/owner-platform/AI_OPERATIONS_CENTER_SPECIFICATION.md` are all
    **SNS Tech Solutions** platforms, not SNS Hospice Solutions
    features — any future revision of those documents' headers/branding
    should read "SNS Tech Solutions — [Platform Name]", consistent with
    the Correct Branding section above.
  - `docs/biller-platform/TENANT_BILLER_DASHBOARD_SPECIFICATION.md` is
    the Biller Platform (SNS Tech Solutions) surface that services
    agencies inside the SNS Hospice Solutions product; its Assignment-
    Based Visibility and DDE-adjacent claims/eligibility/NOE/collections
    scope map directly onto the DDE Architecture Rule and Biller
    Platform Rule here.
  - `docs/governance/APPROVAL_AND_ESCALATION_STRUCTURE.md`'s Future
    Organizational Structure (SNS Hospice Solutions / SNS Home Health /
    SNS Scribe as separate per-product staffing pools) is the Tenant
    Applications layer of this hierarchy.
  - `docs/roadmap/Owner-Platform-Roadmap.md`,
    `docs/roadmap/Biller-Platform-Roadmap.md`,
    `docs/roadmap/Tenant-Platform-Roadmap.md`, and the rest of
    `/docs/roadmap/` should be read as roadmaps for SNS Tech Solutions
    platforms (Owner, Biller) versus the SNS Hospice Solutions product
    (Tenant Platform) respectively.
  - `docs/production/PRODUCTION_READINESS_CLEANUP_CHECKLIST.md`'s
    tenant agencies (Love & Faith Hospice, Angela Hospice, Silva
    Hospice) are Tenant Agencies operating within the SNS Hospice
    Solutions product, per the Tenant Agencies section above — not
    platforms in their own right.
- Sits alongside `docs/architecture/ARCHITECTURE_LOCK.md` as a second,
  independent LOCKED architecture document: `ARCHITECTURE_LOCK.md`
  governs clinical/evidence architecture; this document governs
  platform/brand hierarchy. Both are binding constraints on future
  specifications and designs.

## Change Log

| Date | Change |
|---|---|
| 2026-09-16 | Document created and locked — SNS Tech Solutions Platform Hierarchy: Master Brand Hierarchy, SNS Tech Solutions Platforms list (Owner Platform, Biller Platform, AI Operations Center, Revenue & Subscription Management, Governance & Audit Center, Platform Settings), Tenant Applications (SNS Hospice Solutions current; SNS Home Health, SNS Scribe future), Tenant Agencies (Love & Faith Hospice, Angela Hospice, Silva Hospice, ABC Hospice), Correct/Incorrect Branding examples, Biller Platform Rule, Owner Platform Rule, AI Operations Center Rule, DDE Architecture Rule and DDE Visibility Rule (assignment-based, user-specific), Future Products Rule (architecture tree diagram), and Final Rule. |
