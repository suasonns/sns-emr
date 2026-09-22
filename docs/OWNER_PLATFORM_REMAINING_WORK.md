# Owner Platform — Remaining Work

Current-state inventory only. No recommendations, no future architecture, no recovery
discussion. Source: `OwnerDashboard.jsx` `NAV_ITEMS` (9 sections) cross-checked against
`main`'s `sns-emr-frontend/src/owner/pages/` and backend `owner_admin.py` /
`owner_billing_licensing.py`.

## CORRECTION (screenshot-driven re-verification)

Screenshots of the running Owner Platform show a "PREVIEW — SAMPLE DATA" badge on the
Dashboard. Re-checking the actual routed component tree confirms this and **corrects the
Dashboard row below**, which previously (incorrectly) cited `DashboardOverview.jsx` as the
live, fully-wired Dashboard:

- `OwnerDashboard.jsx` line 21/160/178 actually renders **`DashboardOverviewV2.jsx`** for the
  `dashboard` tab — not `DashboardOverview.jsx`. The latter is an orphaned file: it is not
  exported from `owner/pages/index.js`'s usage here and not referenced by any route.
- `DashboardOverviewV2.jsx`'s own header comment states it "renders the full approved Figma
  visual using the same SAMPLE figures the design was reviewed with... every AI/metric panel
  carries a visible 'PREVIEW — sample data' badge." Only the Agencies pill row (tenant list) is
  wired to real data; the Operations Briefing narrative, Platform Pulse health score, Actions &
  Insights list, and Business Snapshot (revenue/adoption/support) have **no backend at all**.
  The comment also references `docs/future-improvements/owner/` for tracked backend work — that
  directory does not exist in this repo.
- **Dashboard status is therefore corrected from COMPLETE to PARTIAL** (see table below).

Additionally, re-checking **AI Command Center** confirms it is worse than a passive shell: its
`ANOMALIES` / `PREDICTIONS` / `RECOMMENDATIONS` / `ACTIVITY_LOG` are hardcoded fake records that
render identically to real data whenever the backend returns no `recent_incidents` (which it
always does today, since no such backend exists) — but unlike the Dashboard, **it renders with
no "PREVIEW" badge**, so a user cannot tell this fabricated content isn't live. This is a bigger
field-testing risk than a simple "not started" label conveys.

`Settings.jsx`, `BillingLicensing.jsx`, and `AuditLogs.jsx` were re-checked against this same
concern and confirmed to already show honest "not available yet" states or explicit
"no mock data" comments — no fabricated data was found in those three.

## Owner Platform navigation map (current state)

| # | Nav key | Section | Status | On `main` today | In recovery branch (unmerged) |
|---|---|---|---|---|---|
| 1 | `dashboard` | Dashboard | PARTIAL (corrected) | Live component is **`DashboardOverviewV2.jsx`**, not `DashboardOverview.jsx`. Only the Agencies pill row is real; Operations Briefing, Platform Pulse, Actions & Insights, and Business Snapshot are hardcoded sample figures, each rendered with a "PREVIEW — SAMPLE DATA" badge per the file's own header comment | Unchanged |
| 2 | `tenants` | Agency Management (Tenant Management) | COMPLETE | Live (`TenantManagement.jsx`, 520 lines — onboarding, financials toggle, admin creation, all backend-wired) | Unchanged |
| — | `health` | System Health | COMPLETE | Live (`SystemHealth.jsx`, backend `system_health()` endpoint) | Unchanged |
| 3 | `users` | Staff Management (User Management) | PARTIAL | Live version is the **old cross-tenant** User Management page | Recovered version (SNS Staff & Access) exists but is **not merged** — code-complete, backend fully tested, frontend build never run |
| 4 | *(cross-cutting, not a nav page)* | RBAC | PARTIAL | Live `roles.py` has no `staff.*` capability model | Recovered `role_can()`/`PLATFORM_PERMISSION_MATRIX` exists but is **not merged**; hierarchy ordering unresolved |
| 5 | `audit` | Audit Logs | PARTIAL | Live version is the original `AuditLogs.jsx` | Recovered version (severity, entity filters, drawer) exists but is **not merged**; checkpoint doc marked it "awaiting design review" |
| 6 | `analytics` | Analytics | PARTIAL | Live (`Analytics.jsx`, 82 lines, wired to `fetchOwnerAdoptionHealth`) — minimal scope | Unchanged |
| 7 | `billing` | Billing & Licensing | PARTIAL | Live (`BillingLicensing.jsx`, 751 lines; backend exists: `owner_billing_licensing.py`, `owner_billing_service.py`, `owner_licensing_service.py`, `owner_revenue_service.py`, migration `e4f5a6b7c8d9`) — frontend code comment states it falls back to "not available yet" states rather than mock data, so live data coverage is not fully confirmed | Unchanged |
| 8 | `settings` | Settings | PARTIAL | Live (`Settings.jsx`, 122 lines — minimal; only fetches tenant list) | Unchanged |
| 9 | `ai` | AI Command Center | NOT STARTED | Live (`AICommandCenter.jsx`, 246 lines) — static UI shell only; chat input is `readOnly`; zero API/import wiring to any backend; hardcoded `ANOMALIES`/`PREDICTIONS`/`RECOMMENDATIONS`/`ACTIVITY_LOG` render with **no "preview/sample" badge**, unlike Dashboard, so fabricated content is indistinguishable from live data | Unchanged |

## The 4 remaining sections after Audit Logs (per code, current nav order shows 4 —
Analytics, Billing & Licensing, Settings, AI Command Center — plus corrected Dashboard,
listed below in full)

### Dashboard
- **Purpose:** Owner landing page ("SNS Operations Command Center").
- **Current implementation state:** PARTIAL — only the Agencies pill row is real.
- **Backend status:** No AI narrative pipeline, no health-scoring service, no revenue/adoption/
  support aggregation exists.
- **Frontend status:** `DashboardOverviewV2.jsx` renders the approved Figma visual with sample
  figures; every AI/metric panel shows a "PREVIEW — SAMPLE DATA" badge by design so it isn't
  mistaken for live data.
- **Database status:** No dedicated schema for the mocked panels.
- **Blockers:** Same backend work called out for AI Command Center/Analytics/Billing overlaps
  (health scoring, revenue/adoption aggregation, AI narrative) is required to make Dashboard real.
  The orphaned `DashboardOverview.jsx` (unused) should be removed or reconciled to avoid confusion
  about which file is authoritative.

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
- **Frontend status:** Static layout, `readOnly` input field, zero API imports. Renders hardcoded
  `ANOMALIES`/`PREDICTIONS`/`RECOMMENDATIONS`/`ACTIVITY_LOG` sample records with **no visible
  "preview/sample" badge**, so it looks like live output.
- **Database status:** None.
- **Blockers:** No backend exists at all; this is a UI mockup, not a partially wired feature. It
  should carry the same "PREVIEW — SAMPLE DATA" style badge the Dashboard uses, so field testers
  don't mistake the fabricated anomalies/predictions for real platform signals.

## A. Completed sections
- Agency Management (Tenant Management)
- System Health

## B. Partially completed sections
- Dashboard (corrected: mostly Figma-sample data behind a "PREVIEW — SAMPLE DATA" badge; only
  Agencies pill row is real)
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
1. Dashboard's live component (`DashboardOverviewV2.jsx`) is a Figma-sample mockup for 3 of its
   4 panels; the orphaned `DashboardOverview.jsx` should be removed or reconciled to stop the
   codebase carrying two dashboards where only one is routed.
2. AI Command Center renders fabricated anomaly/prediction/recommendation data with no visual
   indicator that it is fake, unlike Dashboard — this is a field-testing risk (users may act on
   fabricated "denial spikes"/"churn risk" figures believing they are real).
3. Staff Management / RBAC / Audit Logs recovered code is not yet merged to `main` — it currently
   exists only in the isolated `recovery/copilot-session-2026-09-14` branch.
4. Frontend build/lint/typecheck has never been run against the recovered code.
5. AI Command Center has zero backend implementation.
6. Billing & Licensing's live-data completeness (vs. fallback "not available yet" states) is not
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
