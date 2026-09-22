# Owner Platform — Remaining Work

Current-state inventory only. No recommendations, no future architecture, no recovery
discussion. Source: `OwnerDashboard.jsx` `NAV_ITEMS` (9 sections) cross-checked against
`main`'s `sns-emr-frontend/src/owner/pages/` and backend `owner_admin.py` /
`owner_billing_licensing.py`.

## Owner Platform navigation map (current state)

| # | Nav key | Section | Status | On `main` today | In recovery branch (unmerged) |
|---|---|---|---|---|---|
| 1 | `dashboard` | Dashboard | COMPLETE | Live (`DashboardOverview.jsx`, wired to `fetchOwnerDashboard`) | Unchanged |
| 2 | `tenants` | Agency Management (Tenant Management) | COMPLETE | Live (`TenantManagement.jsx`, 520 lines — onboarding, financials toggle, admin creation, all backend-wired) | Unchanged |
| — | `health` | System Health | COMPLETE | Live (`SystemHealth.jsx`, backend `system_health()` endpoint) | Unchanged |
| 3 | `users` | Staff Management (User Management) | PARTIAL | Live version is the **old cross-tenant** User Management page | Recovered version (SNS Staff & Access) exists but is **not merged** — code-complete, backend fully tested, frontend build never run |
| 4 | *(cross-cutting, not a nav page)* | RBAC | PARTIAL | Live `roles.py` has no `staff.*` capability model | Recovered `role_can()`/`PLATFORM_PERMISSION_MATRIX` exists but is **not merged**; hierarchy ordering unresolved |
| 5 | `audit` | Audit Logs | PARTIAL | Live version is the original `AuditLogs.jsx` | Recovered version (severity, entity filters, drawer) exists but is **not merged**; checkpoint doc marked it "awaiting design review" |
| 6 | `analytics` | Analytics | PARTIAL | Live (`Analytics.jsx`, 82 lines, wired to `fetchOwnerAdoptionHealth`) — minimal scope | Unchanged |
| 7 | `billing` | Billing & Licensing | PARTIAL | Live (`BillingLicensing.jsx`, 751 lines; backend exists: `owner_billing_licensing.py`, `owner_billing_service.py`, `owner_licensing_service.py`, `owner_revenue_service.py`, migration `e4f5a6b7c8d9`) — frontend code comment states it falls back to "not available yet" states rather than mock data, so live data coverage is not fully confirmed | Unchanged |
| 8 | `settings` | Settings | PARTIAL | Live (`Settings.jsx`, 122 lines — minimal; only fetches tenant list) | Unchanged |
| 9 | `ai` | AI Command Center | NOT STARTED | Live (`AICommandCenter.jsx`, 246 lines) — static UI shell only; chat input is `readOnly`; zero API/import wiring to any backend | Unchanged |

## The 3 remaining sections after Audit Logs (per code, current nav order shows 4 —
Analytics, Billing & Licensing, Settings, AI Command Center — listed below in full)

### Analytics
- **Purpose:** Platform adoption/usage metrics dashboard for the Owner.
- **Current implementation state:** PARTIAL — small (82-line) page, single data source.
- **Backend status:** `fetchOwnerAdoptionHealth()` endpoint exists and is called.
- **Frontend status:** Implemented, minimal scope, not independently rebuilt/typechecked in this session.
- **Database status:** No dedicated schema beyond what adoption-health already reads.
- **Blockers:** None identified beyond scope (whether 82 lines constitutes complete Analytics is
  a scope question, not a technical blocker).

### Billing & Licensing
- **Purpose:** Platform-level licensing and billing-organization administration.
- **Current implementation state:** PARTIAL — largest of the four (751 lines), most backend
  surface of the four.
- **Backend status:** Real services exist (`owner_billing_service.py`, `owner_licensing_service.py`,
  `owner_revenue_service.py`, `owner_billing_licensing.py` API, schema, migration
  `e4f5a6b7c8d9_add_platform_billing_licensing_tables.py`).
- **Frontend status:** Implemented; in-code comment states it intentionally shows an honest
  "not available yet" state instead of fabricated figures for parts not yet backed live.
- **Database status:** Dedicated migration present (`e4f5a6b7c8d9`).
- **Blockers:** Not independently re-verified in this session whether every displayed metric is
  now live-backed or still in the "not available yet" fallback state described in the code comment.

### Settings
- **Purpose:** Owner-level account/platform settings.
- **Current implementation state:** PARTIAL — minimal (122 lines), fetches tenant list only.
- **Backend status:** No dedicated `owner_settings` backend module found; reuses
  `fetchOwnerTenants()`.
- **Frontend status:** Implemented at minimal scope.
- **Database status:** No dedicated schema found.
- **Blockers:** Scope of what "Settings" is meant to contain is not defined in the reviewed code.

### AI Command Center
- **Purpose:** Platform-level AI assistant/command interface for the Owner.
- **Current implementation state:** NOT STARTED functionally — UI shell only.
- **Backend status:** No backend route, service, or model found anywhere in `backend/` for AI
  command/chat functionality.
- **Frontend status:** Static layout, `readOnly` input field, zero API imports.
- **Database status:** None.
- **Blockers:** No backend exists at all; this is a UI mockup, not a partially wired feature.

## A. Completed sections
- Dashboard
- Agency Management (Tenant Management)
- System Health

## B. Partially completed sections
- Staff Management (recovered, not merged)
- RBAC (recovered, not merged, hierarchy unresolved)
- Audit Logs (recovered, not merged, design-review status unclear)
- Analytics (live, minimal scope)
- Billing & Licensing (live, backend present, some metrics may still be in fallback state)
- Settings (live, minimal scope)

## C. Remaining sections
- AI Command Center (not started — no backend, static frontend shell only)

## D. Dependencies
- Staff Management, RBAC, and Audit Logs merges depend on each other (same batch — see prior
  merge-plan documents; not repeated here).
- Analytics/Billing & Licensing/Settings have no dependency on the unmerged recovery branch — they
  are already live on `main` independently.
- AI Command Center has no existing backend to depend on; it depends on new backend work not yet
  started.

## E. Critical blockers
1. Staff Management / RBAC / Audit Logs recovered code is not yet merged to `main` — it currently
   exists only in the isolated `recovery/copilot-session-2026-09-14` branch.
2. Frontend build/lint/typecheck has never been run against the recovered code.
3. AI Command Center has zero backend implementation.
4. Billing & Licensing's live-data completeness (vs. fallback "not available yet" states) is not
   independently confirmed in this session.

## F. Exact path to finish Owner Platform
1. Merge Staff Management, RBAC, and Audit Logs from the recovery branch (subject to the
   already-identified merge/security decisions on those 3 areas).
2. Run frontend build/lint/typecheck against the merged result.
3. Confirm Billing & Licensing's live-data coverage for every displayed metric.
4. Define and implement AI Command Center's backend (currently zero implementation) and wire the
   existing UI shell to it.
5. Confirm Analytics and Settings scope is considered sufficient, or expand them, per product
   definition (no gap was found beyond their current minimal scope).

## G. What must be completed before Tenant Platform begins
- Steps 1–4 above (Staff Management/RBAC/Audit Logs merged and validated; AI Command Center has a
  working backend) — these are the only 4 sections not already COMPLETE or independently
  functioning on `main` today.
- Analytics and Settings are already live and functioning; no explicit gap was found that would
  block Tenant Platform on their account beyond what's noted above.
