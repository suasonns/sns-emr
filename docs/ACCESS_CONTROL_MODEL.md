# SNS Hospice Solutions — Access Control Model Reference

This is the master access-control model for the platform, and how it maps
onto the actual role strings implemented in code (`backend/app/core/roles.py`,
`backend/app/core/auth.py`).

**Design decision:** the roles below were used as a *guide*, not a literal
rename. Every role name already shipped and in use in the database (`OWNER`,
`DPCS_ADMINISTRATOR`, `DPCS`, `ADMINISTRATOR`, `BILLING`, `RN`, `LVN`, `MD`,
`SW`, `CHAPLAIN`, etc.) was kept exactly as-is. The department roles below
that are new were added additively alongside them. Nothing that already
worked was renamed, so no data migration was required for this pass.

## Level 0 — Platform (SNS Hospice Solutions vendor staff)

Platform roles belong to SNS, never to an agency. They must NEVER
automatically gain access to PHI or clinical documentation — this is
enforced in `roles.py` by excluding `PLATFORM_ROLES` from both
`CLINICAL_ADMIN_ROLES` and `FINANCIAL_ADMIN_ROLES`, and `role_matches()`
never gives a platform role an implicit tenant/clinical/financial fallback.

| Model role | Implemented as | Notes |
|---|---|---|
| Platform Owner | `OWNER` | Existing role, unchanged. Owns SNS Hospice Solutions. Can create/suspend tenants (`/api/owner/tenants`), view platform-wide operational metrics. Cannot access patient charts, clinical notes, orders, POC, IDG, or any clinical documentation. Cannot be combined with billing/financial access (enforced explicitly on `/api/dashboard/billing`). |
| Platform Support | `PLATFORM_SUPPORT` | New, additive. Not yet wired to any endpoint — reserved for future support-tooling access. |
| Platform Billing | `PLATFORM_BILLING` | New, additive. Reserved for future SNS-side subscription/invoice management (distinct from agency `BILLING`). |
| Platform Operations | `PLATFORM_OPERATIONS` | New, additive. Reserved for platform health/ops tooling. |
| Platform AI Management | `PLATFORM_AI_MANAGEMENT` | New, additive. Reserved for AI pricing/plan configuration (see AI subscription model below — not yet built). |
| Platform Compliance | `PLATFORM_COMPLIANCE` | New, additive. Reserved for platform-side compliance monitoring. |

## Level 1 — Tenant / Agency

| Model role | Implemented as | Notes |
|---|---|---|
| Agency Owner | `DPCS_ADMINISTRATOR` | Existing role. Used specifically for an agency principal who holds BOTH the DPCS and Administrator titles simultaneously (per hospice accreditation requirements — these are two distinct CoP titles). Gets full clinical-admin + financial-admin fallback within their own tenant (`CLINICAL_ADMIN_ROLES` and `FINANCIAL_ADMIN_ROLES` in `roles.py`). |
| Agency Administrator | `ADMINISTRATOR` / `DPCS` | Existing roles, kept separate for staff who hold only one of the two titles (not both). Both are in `CLINICAL_ADMIN_ROLES`. |

## Level 2 — Clinical Department

| Model role | Implemented as | Notes |
|---|---|---|
| Medical Director | `MEDICAL_DIRECTOR` (aliases: `ALTERNATE_MEDICAL_DIRECTOR`, `MEDICAL_DIRECTOR_DESIGNEE`) | Existing. |
| Attending Physician | `MD`, `DO`, `NP`, `PA` | Existing discipline roles; new `ATTENDING_PHYSICIAN` role also added as a valid role string for future use. |
| RN | `RN` | Existing. |
| LVN | `LVN` (alias: `LPN`) | Existing. |
| CHHA | `CHHA` | New, additive role string (was previously only a `Discipline` enum value for documentation, not a login role). |
| MSW | `SW` (aliases: `MSW`, `LCSW`, `BSW`) | Existing. |
| Chaplain | `CHAPLAIN` | Existing. |
| Volunteer Coordinator | `VOLUNTEER_COORDINATOR` | New, additive. Not yet wired to a dedicated screen. |
| Clinical Supervisor | `CLINICAL_SUPERVISOR` | New, additive. Not yet wired to a dedicated screen. |

## Level 2 — Billing Department

Billing users are NOT clinical users. `BILLING_DEPARTMENT_ROLES` in
`roles.py` grants financial-gate access only, never `CLINICAL_ADMIN_ROLES`
fallback.

| Model role | Implemented as | Notes |
|---|---|---|
| Billing Manager | `BILLING` | Existing role (`billing@sns.local`). New `BILLING_MANAGER` role string also added as an equivalent alternative for future accounts. |
| Billing Specialist | `BILLING_SPECIALIST` | New, additive. |
| Collections | `COLLECTIONS` | New, additive. |
| Revenue Cycle | `REVENUE_CYCLE` | New, additive. |

## Level 2 — QA Department (new)

Read-only access intended (documentation audits, missing signatures,
expiring certifications, survey readiness). **Not yet wired to any
endpoint** — role strings exist (`QA_MANAGER`, `QA_REVIEWER`,
`COMPLIANCE_OFFICER`) but no dashboard/gates reference them yet.

## Level 2 — Intake Department (new)

Role strings exist (`INTAKE_MANAGER`, `INTAKE_COORDINATOR`) but no
dashboard/gates reference them yet. Intended access: referrals, admission
packet, eligibility, demographics, insurance verification.

## Level 2 — Scheduling Department (new)

Role strings exist (`SCHEDULER`, `STAFFING_COORDINATOR`) but no
dashboard/gates reference them yet. Intended access: staff schedules, visit
schedules, route planning — never clinical documentation or billing.

## AI Subscription Model (not yet built)

The full model calls for a platform-controlled AI plan/pricing tree
(Basic/Professional/Enterprise + add-ons like Drug Interaction Engine,
Speech Minutes, Advanced Coding AI, Predictive Analytics), with agency
owners purchasing plans and assigning licenses to staff. This has **not**
been implemented — `tenants.ai_enabled` today is a single on/off flag, not a
tiered subscription. This is future work.

## Key security invariants (already enforced)

- **Platform Owner ≠ Tenant Owner.** `OWNER` never gets `CLINICAL_ADMIN_ROLES`
  fallback — verified via `/api/dashboard/tenant`, `/api/dashboard/clinical-alerts`,
  `/idg/sessions`, `TenantDashboard.jsx` all blocking `OWNER`.
- **Tenant Owner ≠ Billing User** is naturally true since they're different
  role strings, but `DPCS_ADMINISTRATOR` *does* get financial fallback
  (agency owners can see their own agency's billing) — this is intentional
  per the doc ("Agency Owner: ✅ Billing dashboards").
- **Billing User ≠ Clinical User.** `BILLING`/`BILLING_MANAGER`/etc. never
  get `CLINICAL_ADMIN_ROLES` fallback.
- **Platform access separate from tenant access.** `OWNER` and
  `BILLING`/`BILLING_MANAGER` must never be combined into the same login —
  enforced explicitly on `/api/dashboard/billing` (403 for `OWNER`) in
  addition to the `roles.py` fallback exclusion.
