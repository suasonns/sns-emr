# TENANT PLATFORM & BILLER PLATFORM — CROSS-PLATFORM BILLING SCHEMA DISCOVERY

STATUS: REPOSITORY DISCOVERY COMPLETE FOR THE AREAS INVESTIGATED BELOW.
DOCUMENTATION ONLY. NO SCHEMA, MIGRATION, API, UI, BACKFILL, OR
RETIREMENT PERFORMED. PAYER/PLAN ARCHITECTURE WORK AND BILLING
ORGANIZATION IMPLEMENTATION REMAIN PAUSED PENDING REVIEW OF THIS AND
THE FOUR SIBLING DOCUMENTS BELOW.

## TRIGGER

Requested by the user's "Tenant Platform and Biller Platform —
Cross-Platform Billing Schema Investigation" directive, issued
immediately after `REPOSITORY_GROUNDING_CORRECTION_REPORT.md` surfaced
that several tables cited as REUSE evidence in Sections 18-27 of
`BILLING_ORGANIZATION_DISCOVERY_REPORT.md` do not exist. This
investigation goes one level broader: it asks whether "SNS Hospice
Solutions Tenant Platform" and "SNS Tech Solutions Biller Platform"
are, in the actual repository, separate systems with potentially
duplicate billing schemas, or a single system.

## FOUNDATIONAL FINDING: THIS IS ONE REPOSITORY, NOT TWO PLATFORMS

**There is no separate "SNS Tech Solutions Biller Platform" codebase.**
The entire application — clinical/tenant-facing EMR and billing —
lives in one repository with two top-level project folders:

- `backend/` — a single FastAPI + SQLAlchemy service. Billing-specific
  code is organized under `backend/app/billing/` (models, services,
  API routers, validators, engine); general/clinical models live under
  `backend/app/models/`. There is one shared Postgres schema — not two
  databases, not two schemas, not a services boundary between
  "Tenant Platform" and "Biller Platform."
- `sns-emr-frontend/` — a single Vite/React app with route trees for
  `tenant/` (clinical/agency-facing pages), `owner/` (platform-owner
  admin console), and `pages/billing/` (billing-operations pages used
  today, tenant/agency-scoped).

**Implication for the investigation's Platform Boundary section:**
the "Tenant Platform owns source records, Biller Platform provides
authorized cross-agency access" architecture described in the source
document is **not yet built** — today, `pages/billing/*` pages operate
within a single tenant/agency context (see `AgencyContext.tsx`,
`BillerShell.tsx` under `sns-emr-frontend/src/components/billing/`),
not across multiple agencies for an external billing company's staff.
The cross-tenant "billing company serving many agencies" concept that
*does* exist in the repository today is a **different, narrower,
already-built feature**: `BillingProviderOrganization` /
`BillingProviderOrganizationMembership` / `BillingProviderAgencyAssignment`
/ `BillingProviderAgencyServiceScope`, which is a **Platform-Owner
licensing/authorization feature** (mounted at
`/api/owner/billing-providers`, consumed only by
`src/owner/pages/BillingLicensing.jsx` and
`src/owner/pages/TenantManagement.jsx`) — **not** the rich
"Organization & Teams / Coverage Assignment / Capability" Biller
Platform UI that Sections 1-29 of
`BILLING_ORGANIZATION_DISCOVERY_REPORT.md` and the approved Figma
references describe. These are two different concepts that happen to
share overlapping vocabulary ("billing organization," "agency
assignment"). This distinction was not previously documented and is a
material finding of this investigation.

## TENANT PLATFORM BILLING INVENTORY (SYSTEM OF RECORD, VERIFIED)

| Concept | Authoritative Model | Table | Scope | Confirmed Consumers |
|---|---|---|---|---|
| Patient identity | `Patient` | `patients` | tenant + agency | entire application |
| Claim | `Claim` | `claims` | tenant | `claims_router.py`, `claim_status_router.py`, `billing_router.py`, `credit_balance_router.py`, `denials_router.py`, `payment_posting_router.py`; services: `billing_engine.py`, `aging_report_service.py`, `claim_financials.py`, `credit_balance_service.py`, `facility_payment_service.py`; frontend: `ClaimsManagementPage.tsx`, `BillingOverviewPage.tsx`, `AgingReportPage.tsx`, `CreditBalanceReportPage.tsx`, `DenialsAppealsPage.tsx`, `PaymentPostingPage.tsx`, `ReportsPage.tsx`, `FacilityCollectionsReportPage.tsx` |
| Patient billing/financial payer responsibility | `PatientPayer` | `patient_payers` | tenant + patient | `app/api/patients.py` (direct CRUD), `claim_financials.py`, `credit_balance_service.py`, `facility_payment_service.py`, `msp_validation_service.py` (payer sequencing/COB) |
| Eligibility-workflow coverage record | `PatientInsurance` | `patient_insurances` | tenant + patient | `eligibility_check_router.py`, `eligibility_workflow_service.py`; frontend: `EligibilityVerificationPage.tsx` |
| Eligibility check (simple) | `PayerEligibilityCheck` | `payer_eligibility_checks` | tenant, FK to `patient_insurances` | same as above |
| Eligibility verification (rich, tri-state, append-only) | `EligibilityVerification` | `eligibility_verifications` | tenant, FK to `patient_insurances` and a source document | `eligibility_check_router.py`, `eligibility_workflow_service.py`, `readiness_dashboard_service.py` |
| Payer catalog | `Payer` | `payers` | tenant | re-exported (not duplicated) into `app.billing.models` for billing-module use; consumed by `Contract` (`payer_id` FK); no direct billing-page consumer found |
| Coverage decision (clinical financial-responsibility) | `ServiceCoverageDecision` | `service_coverage_decisions` | tenant + patient, FK to `PatientPayer` | `app/api/coverage.py` |
| ERA / remittance | `RemittanceAdvice` | `remittance_advices` | tenant | `payment_posting_router.py`, `aging_report_service.py`, `facility_payment_service.py`; frontend: `PaymentPostingPage.tsx`, `BillingOverviewPage.tsx` |
| Payment / adjustment | `Payment`, `PaymentAdjustment` | `payments`, `payment_adjustments` | tenant | `payment_posting_router.py`, `facility_payment_router.py`, `credit_balance_router.py`, `claim_financials.py`, `credit_balance_service.py`, `facility_payment_service.py`, `aging_report_service.py` |
| Denial | `Denial` | `denials` | tenant | `denials_router.py`, `aging_report_service.py`, `credit_balance_service.py`, `claim_financials.py`; frontend: `DenialsAppealsPage.tsx` |
| Appeal | `Appeal` | `appeals` | tenant | `denials_router.py`; frontend: `DenialsAppealsPage.tsx` |
| Credit balance case | `CreditBalanceCase` | `credit_balance_cases` | tenant | `credit_balance_router.py`, `credit_balance_case_service.py`, `credit_balance_service.py`; frontend: `CreditBalanceReportPage.tsx` |
| Hospice cap | `HospiceCapRecord` | `hospice_cap_records` | tenant | `hospice_cap_service.py`; frontend: `CapCalculationPage.tsx` |
| NOE | `NoeEdiSubmission` | `noe_edi_submissions` | tenant | `noe_tracking_router.py`, `noe_edi_builder.py`; frontend: `NoeTrackingPage.tsx` |
| Room & Board / facility reimbursement | `FacilityPaymentExpectation`, `FacilityPaymentAllocation`, `FacilityCollectionAlert` (+ threshold), `FacilityPaymentAuditLog` | `facility_payment_expectations`, `facility_payment_allocations`, `facility_collection_alerts` (+ thresholds table), `facility_payment_audit_logs` | tenant + patient | `facility_payment_router.py`, `facility_payment_service.py`; frontend: `FacilityCollectionsReportPage.tsx` |
| Audit (generic, shared) | `AuditLog` | `audit_logs` | tenant | generic `action`/`entity_type`/`entity_id` log used across multiple domains |

**`FacilityPaymentExpectation` detail (Room & Board):** carries
`responsibility_category` and `expected_funding_source` as its payer-
classification axis, plus `expected_payer_name_snapshot`/
`primary_payer_name_snapshot`/`secondary_payer_name_snapshot` (free-
text snapshots, not FKs) — this is the closest existing real analog to
the proposed "Service Billing Responsibility" entity (Section 29.6
item 7) for the Room & Board domain specifically, and should be
evaluated first before creating a new generic entity if/when
Payer/Plan work resumes (see `TENANT_BILLER_SYSTEM_OF_RECORD_MATRIX.md`
row 7).

## BILLER PLATFORM (CROSS-TENANT BILLING-COMPANY) INVENTORY

| Concept | Authoritative Model | Table | Scope | Confirmed Consumers |
|---|---|---|---|---|
| Billing company (organization) | `BillingProviderOrganization` | `billing_provider_organizations` | platform-wide | `billing_provider_router.py` (`/api/owner/billing-providers/organizations`), `billing_provider_access_service.py`; frontend: `owner/pages/BillingLicensing.jsx`, `owner/pages/TenantManagement.jsx` via `src/api/ownerAdmin.ts` |
| Billing-company user membership | `BillingProviderOrganizationMembership` | `billing_provider_organization_memberships` | platform-wide, role: `MEMBER`/`ADMIN` only | `billing_provider_access_service.py` |
| Assigned tenant/agency | `BillingProviderAgencyAssignment` | `billing_provider_agency_assignments` | tenant + organization | `billing_provider_router.py` (`/assignments`), `billing_provider_access_service.py` |
| Functional service scope + permission level per assignment | `BillingProviderAgencyServiceScope` | `billing_provider_agency_service_scopes` | per-assignment | same as above |

**This is a real, working, consumed feature** — but it is scoped to
**platform-owner licensing** ("which billing company is authorized to
service which tenant, at what functional scope/permission level")
rather than the rich in-app "Organization & Teams" experience (Team
Alpha/Beta portfolios, President/Supervisor/Specialist role
hierarchy, per-payer Coverage Assignments like "Medicare Biller,"
Capability grants, DDE Authorization, Access Review Status) that
Sections 1-29 and the approved Figma references describe. **No
frontend page consumes this feature for that richer purpose today** —
confirmed via full-repository frontend search; the only consumers are
the two Owner-portal pages above.

## HISTORICAL / OLDER BILLING CODE

See `LEGACY_BILLING_SCHEMA_INVENTORY.md` for the dedicated inventory.
Summary: no separate "legacy billing schema" (as a set of superseded
tables) was found. The only historical artifact identified is a small
in-memory dev/demo store (`app/billing/store.py`) whose own docstring
states it has already been superseded by the real `claims` table — see
that document for full detail, consumers, and retirement status.

## CROSS-PLATFORM SHARED-DOMAIN ASSESSMENT

Per the source document's Shared-Domain Rule (one authoritative source
per business fact, shared between platforms): since there is currently
only **one** platform (one repository, one database), there is, by
definition, no cross-platform duplication risk *yet* for Claim,
Payment, Remittance, Denial, Appeal, AR, or Room & Board — each has
exactly one real table today. The duplication risk that **does**
exist is **within** the single platform, between two competing
patient-payer models (`PatientInsurance` vs. `PatientPayer`) — see
`PATIENT_INSURANCE_DUPLICATION_ANALYSIS.md`. This is the concrete,
present-day analog of the "shared authoritative domain" concern the
source document raises, and should be resolved before any future
Tenant/Biller platform split introduces a second real risk of
divergence.

## STATUS

Documentation only. No schema, migration, model, service, route, UI
component, backfill, or retirement created or changed. See the four
sibling documents (`LEGACY_BILLING_SCHEMA_INVENTORY.md`,
`TENANT_BILLER_SYSTEM_OF_RECORD_MATRIX.md`,
`PATIENT_INSURANCE_DUPLICATION_ANALYSIS.md`, and the updated
`REPOSITORY_GROUNDING_CORRECTION_REPORT.md`) for the remaining required
deliverables. Payer/Plan architecture work and Billing Organization
implementation remain paused.
