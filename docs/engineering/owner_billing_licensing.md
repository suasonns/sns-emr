# Owner Portal — Billing & Licensing Management

**Status:** ✅ Final Approved (Frontend + Backend + Database + API + Migration Validation Complete)
**Commit:** `1827f58578b7a71c3b7cd96f2f7d98ae129525f6`
**Branch:** `feature/production-hnp-clinical-runtime` (PR #66)
**Date:** 2026-09-05

This document exists so future developers understand what this feature
is, what it owns, what it does not own, and where its known limitations
are before extending it.

---

## 1. Purpose / Ownership

Billing & Licensing is the **Platform Owner's** view of what SNS
charges each tenant agency for use of the platform (subscription plan,
seats, invoices, payments). It is **platform-side billing**, not
tenant-side clinical billing.

It is explicitly distinct from, and must never be conflated with:

| This feature (Platform Billing) | NOT this feature (Clinical/Payer Billing) |
|---|---|
| `app.models.subscription_plan.SubscriptionPlan` | `app.billing.models.contract.Contract` (payer contract) |
| `app.models.tenant_subscription.TenantSubscription` | — |
| `app.models.platform_invoice.PlatformInvoice` | `app.billing.models.payment.Payment` (claim-level ERA remittance) |
| `app.models.platform_payment.PlatformPayment` | `app.billing.services.billing_readiness_service` (tenant-scoped NOE/claim readiness) |
| `app.models.license_allocation.LicenseAllocation` | `app.billing.services.revenue_service` (tenant's own hospice claim revenue from payers) |

**Rule of thumb:** if the money flows *tenant → payer* (Medicare,
Medicaid, private insurance) it is clinical/payer billing and lives in
`app.billing.*`. If the money flows *tenant → SNS* (subscription fees,
license seats), it is platform billing and lives in the models/services
listed in this document.

---

## 2. Data Model

### `SubscriptionPlan` (platform-wide catalog, NOT tenant-scoped)
The list of plans SNS offers (e.g. price tiers, seat allowances). One
row per plan, shared across all tenants.

### `TenantSubscription` (tenant-scoped)
A tenant's subscription to a plan. FK to `tenants.id` and
`subscription_plans.id`. Carries `status` (`ACTIVE` / `TRIAL` /
`PAST_DUE` / `SUSPENDED` / `CANCELLED`), `seats_licensed`,
`monthly_rate_override` (null = use the plan's list price),
`start_date`, `renewal_date`. A tenant may accumulate a history of
subscriptions over time; the "current" one is selected by latest
`created_at`.

### `PlatformInvoice` (tenant-scoped)
An SNS → tenant invoice against a subscription. FK to `tenants.id` and
`tenant_subscriptions.id`. `status`: `PENDING` / `PAID` / `OVERDUE` /
`VOID`.

### `PlatformPayment` (tenant-scoped)
A tenant → SNS payment against an invoice. FK to `tenants.id` and
`platform_invoices.id`. `status`: `SUCCESS` / `PENDING` / `OVERDUE`.

### `LicenseAllocation` (tenant-scoped)
Per-tenant, per-plan-tier seat snapshot. Kept as its own table (rather
than a scalar column on `TenantSubscription`) so a tenant split across
multiple plan tiers can be represented without redesigning
`TenantSubscription` — this mirrors the frontend's
`LicenseAllocation[]` array shape (one row per plan tier).

Migration: `backend/alembic/versions/e4f5a6b7c8d9_add_platform_billing_licensing_tables.py`
(down_revision `d2e3f4a5b6c7`). Verified: fresh-DB `alembic upgrade
head`, `alembic downgrade -1`, and re-`upgrade head` all succeed
cleanly.

---

## 3. Services

All three live in `backend/app/services/` and only ever return real
query results — no fabricated figures. When a table has no rows yet,
they return `None` / `[]`, never an invented number.

- **`OwnerBillingService`** — Client Billing Overview rows, Recent
  Payments, Upcoming Outstandings. Derives the client-row `status`
  pill (`PAID` / `OVERDUE` / `PENDING` / `TRIAL`) from
  `TenantSubscription.status` plus the tenant's latest
  `PlatformInvoice.status` — it does **not** surface
  `TenantSubscription.status` directly, since that enum
  (`ACTIVE`/`TRIAL`/`PAST_DUE`/`SUSPENDED`/`CANCELLED`) doesn't match
  the UI's billing-status contract.
- **`OwnerLicensingService`** — license allocations, total seats used
  vs. allocated, upcoming renewals.
- **`OwnerRevenueService`** — revenue KPIs (total monthly revenue,
  outstanding invoice totals, active/licensed agency counts, average
  revenue per agency), revenue-by-agency breakdown.

---

## 4. API Endpoints

All under `/api/owner/billing-licensing`, registered in
`backend/app/api/registry.py`, guarded by `require_owner` (Platform
Owner role only):

| Method | Path | Returns |
|---|---|---|
| GET | `/api/owner/billing-licensing` | Full `BillingLicensingResponse` (all sections in one call) |
| GET | `/api/owner/billing-licensing/kpis` | `RevenueMetrics` only |
| GET | `/api/owner/billing-licensing/licenses` | `LicenseAllocation[]` |
| GET | `/api/owner/billing-licensing/invoices` | `InvoiceSummary[]` (upcoming outstandings) |
| GET | `/api/owner/billing-licensing/payments` | `PaymentHistory[]` |
| GET | `/api/owner/billing-licensing/revenue` | `RevenueByAgency[]` |
| GET | `/api/owner/billing-licensing/tenants` | Tenant list for the agency filter |

All endpoints accept an optional `tenant_id` query param to scope
results to one agency.

DTOs: `backend/app/schemas/owner_billing_licensing.py`. This module's
docstring states the field-for-field mirror contract with
`sns-emr-frontend/src/api/ownerAdmin.ts` — **keep both in sync when
either changes.**

`BillingLicensingResponse.data_available` is `true` only when at least
one real subscription/client/KPI record exists; `unavailable_reason`
gives a human-readable explanation when it's `false`.

---

## 5. Frontend

- **Page:** `sns-emr-frontend/src/owner/pages/BillingLicensing.jsx`
  — KPI cards, Client Billing Overview table (with agency/status
  filter), Revenue Contribution, Recent History, Upcoming
  Outstandings, License Allocation Summary. Uses the Owner Portal's
  shared `COLORS`/`S` design tokens; no standalone sidebar/footer.
- **API client:** `fetchOwnerBillingLicensing()` +
  `OwnerBillingLicensingResponse` types in
  `sns-emr-frontend/src/api/ownerAdmin.ts`.
- **Routing:** exported from `sns-emr-frontend/src/owner/pages/index.js`,
  added to `NAV_ITEMS` and the `renderPage()` switch in
  `sns-emr-frontend/src/owner/OwnerDashboard.jsx` (`key: 'billing'`).
  No new route logic — reuses the existing generic `/owner/:section`
  route.
- **States:** loading / empty ("Not Available Yet") / error, never
  fabricated data. Populated-data rendering was verified against the
  live API (see §7).

---

## 6. Pre-Merge Validation Performed

- ✅ `alembic upgrade head` on a completely fresh, empty database.
- ✅ `alembic downgrade -1` then `alembic upgrade head` again (rollback
  safety).
- ✅ Inserted one real `SubscriptionPlan`, `TenantSubscription` (against
  an existing tenant), and `PlatformInvoice`; confirmed
  `GET /api/owner/billing-licensing` returns real, non-empty,
  contract-correct data.
- ✅ Fixed a status-field mismatch found during validation: the
  service was leaking raw `TenantSubscription`/`PlatformInvoice` enum
  values (`ACTIVE`, `PENDING`) instead of the documented
  `PAID/OVERDUE/PENDING/TRIAL` and `UPCOMING/OVERDUE` contract values.
- ✅ `npx tsc -b --noEmit` passes clean.
- ✅ Confirmed no clinical, patient, claim, billing-workflow, or
  hospice-documentation tables/models/services were touched by this
  feature. Unrelated, already-uncommitted patient-contact-harvesting
  files present in the working tree were explicitly excluded from this
  commit.

---

## 7. Future Enhancements (not built, explicitly deferred)

- **Generate Invoice** button (currently disabled, "Not available
  yet") — no invoice-creation workflow exists yet, only read queries.
- **Financial Alerts / Financial Notifications banner** (Tenant
  Financials → Insights → Financial Hub) — queued as a future backlog
  item per prior product direction; not part of this feature.
- Automated billing/NOE/claim-status email notifications — blocked on
  SMTP infrastructure, which does not exist yet; tracked separately
  from this feature.
- `RenewalSummary` DTO exists in the schema module but has no
  dedicated endpoint yet (renewal dates are currently only visible
  via the licensing endpoint's per-tenant rows).

## 8. Known Limitations

- No real tenant has an active platform subscription in production —
  every table is empty until Owner Portal admins are given an
  onboarding workflow (not built) to create `TenantSubscription` /
  `PlatformInvoice` rows for real agencies. Today the only rows in any
  environment are the manually-inserted dev/validation smoke-test data
  described in §6, and that data was not committed.
- `seats_used` (as opposed to `seats_licensed`) is only populated via
  `OwnerLicensingService`; the Client Billing Overview endpoint alone
  always reports it as `null` — a caller needs the `/licenses`
  endpoint (or the combined root endpoint) to get seat utilization.
- No write/mutation endpoints exist yet (no create/update invoice,
  payment, or subscription API) — this feature is currently read-only
  reporting on top of tables that must be populated some other way
  (e.g. a future admin onboarding flow or a billing-system
  integration).
