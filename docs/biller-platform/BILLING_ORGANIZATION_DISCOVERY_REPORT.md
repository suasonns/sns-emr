# BILLING ORGANIZATION DISCOVERY REPORT

STATUS: DISCOVERY COMPLETE — SCHEMA/MIGRATION/API/MODEL WORK NOT YET AUTHORIZED

Per the approved Billing Organization GitHub Issue ("[Biller Platform]
Implement Billing Organization") and the locked
`BILLER_PLATFORM_FINAL_IMPLEMENTATION_HANDOFF.md` Section 10
(Verify-First Requirement), this report completes repository discovery
for all six required Discovery Areas before any schema, migration,
model, or API work begins. Every claim is backed by an exact file
path. Where nothing was found, that is stated explicitly rather than
guessed.

**Headline finding:** a real, working, database-backed billing
organization system **already exists** in this codebase
(`BillingProviderOrganization` / `BillingProviderOrganizationMembership`
/ `BillingProviderAgencyAssignment` / `BillingProviderAgencyServiceScope`,
under `backend/app/billing/models/` and `backend/app/billing/api/`,
exposed today through the **SNS Tech Solutions owner platform's
Billing/Licensing admin page**, not the Biller Platform). It is the
correct foundation to **REUSE and EXTEND** for the org-to-agency
relationship layer. It does **not**, however, contain any concept of
internal hierarchy levels (Company President → Billing Manager →
Supervisor → Team Leader → Staff), Teams, per-user agency coverage
(Medicare Biller / Medi-Cal Biller / Backup), a billing-specific
capability matrix, escalation chains, or workload metrics — all of
those must be **newly created**, layered on top of the existing
organization/membership/assignment foundation rather than duplicating
it.

---

## DISCOVERY AREA 1 — IDENTITY AND USERS

### User model
- **Existing Model:** `User` — `backend/app/models/user.py`
- **Existing Table:** `users`
- **Existing Service:** role/authorization logic in
  `backend/app/core/roles.py`, `backend/app/core/role_guards.py`,
  `backend/app/core/permissions.py`
- **Existing UI:** staff directory/profile UI exists platform-wide
  (owner `UserManagement.jsx` and others); not billing-org-specific.
- **Existing API:** standard staff/user CRUD endpoints (outside this
  report's scope).
- **Fields relevant to this module:** `tenant_id`, `role` (flat
  string), `access_level`, `active`, `job_title`, `discipline`,
  `staff_type` (Clinical/Administrative/Contracted/Referral),
  `department` (presentational only, "never grants permissions" per
  in-file comment), `platform` (SNS platform name), `account_type`,
  `platform_staff_status`.
- **What is NOT present:** no `manager_id`/`supervisor_id`/
  `reports_to` field, no `team_id`, no hierarchy-level field, no
  billing-organization-specific fields of any kind.
- **Classification: EXTEND.** The `User` table is the correct root
  identity record to attach billing-organization hierarchy/team/
  capability relationships to via new join tables (see Areas 2-4
  below) rather than adding a new parallel identity model. Do not
  create a second "Employee" model — none exists today, and none
  should be created; `User` is the single identity record in this
  codebase.
- **Migration Required:** No changes to `User` itself are anticipated
  — new relationships should be modeled as separate join tables
  referencing `users.id`, consistent with how every other assignment
  model in this codebase (`BillingProviderOrganizationMembership`,
  `BillingProviderAgencyAssignment`, `DocumentNotification`, etc.)
  already references `users.id` rather than adding columns to `User`.
- **Repository Evidence:** `backend/app/models/user.py`

### Role model(s) — two separate, non-overlapping systems found
1. **Active system:** `backend/app/core/roles.py` — flat, hardcoded
   role-name constants and sets (e.g. `BILLING_DEPARTMENT_ROLES =
   {"BILLING", "BILLING_MANAGER", "BILLING_SPECIALIST", "COLLECTIONS",
   "REVENUE_CYCLE"}`), a `normalize_role()`/alias table, a
   `STAFF_CAPABILITIES` set and a `PLATFORM_PERMISSION_MATRIX: dict[str,
   set[str]]` mapping role → capability set — but this matrix is
   **explicitly scoped to the `staff.*` namespace only** (SNS platform
   staff management: invite/suspend/disable/remove/reset-password/etc.
   for platform staff accounts), with an in-file comment stating this
   is "namespaced (`staff.*`) so they can never be confused with the
   separate Tenant Management / Biller Management / Revenue
   Intelligence / Licensing & Billing capability namespaces approved
   for later phases." **It does not contain, and was never intended to
   contain, the billing-specific capabilities this module requires**
   (DDE Access, Claims Submission, Appeals, Payment Posting, AR
   Management, Room & Board Access, Executive Reporting, Agency
   Assignment, Workforce Administration).
2. **Dormant/legacy system:** `Role` model —
   `backend/app/models/role.py` (table `roles`, tied to an
   `interface_id` FK on an `interfaces` table). Confirmed via search
   that this model is imported **only** in `backend/app/models/__init__.py`
   for SQLAlchemy table registration — it is not queried, joined, or
   referenced by any service, route, or authorization check anywhere
   else in the codebase. This is a **dormant/legacy model**, unrelated
   to the active string-based role system above.
- **Classification: EXTEND (the data-driven-matrix pattern) + CREATE
  (a new billing-capability namespace).** The `PLATFORM_PERMISSION_MATRIX`
  pattern (role → set of capability strings, held as data, checked via
  a single lookup function) is a proven, working architectural
  precedent worth following for the new Capability Matrix (Discovery
  Area 4) — but it must be a **new, separate matrix** in its own
  namespace, not an addition to `STAFF_CAPABILITIES`/
  `PLATFORM_PERMISSION_MATRIX`, which are explicitly reserved for
  platform-staff administration only. Do **not** attempt to reuse the
  dormant `Role`/`interfaces` model — it has no live consumers and
  reviving it would create a second, competing role-storage mechanism.
- **Migration Required:** New tables only (no changes to `roles`/
  `interfaces`, which stay untouched and dormant).
- **Repository Evidence:** `backend/app/core/roles.py`,
  `backend/app/models/role.py`, `backend/app/models/__init__.py`

### Authentication / Authorization
- **Existing Service:** `backend/app/core/permissions.py` —
  `require_system_access()`, `require_roles()` (role-string gating,
  fully functional and used throughout clinical endpoints), and two
  **explicit placeholders**: `require_permission(permission: str = "")`
  ("Placeholder for fine-grained permissions. Currently acts as
  authenticated user gate.") and `has_permission(*args, **kwargs) ->
  bool` ("Placeholder permission check", always returns `True`).
- **Classification: EXTEND is not applicable — CREATE.** There is
  **no working fine-grained/capability-based permission engine
  anywhere in the general application** beyond role-string matching;
  the only two functions that look like one are unimplemented stubs.
  Any capability-based access control for this module (Discovery Area
  4) must be built new; it cannot extend `require_permission`/
  `has_permission` because there is nothing real underneath them
  today.
- **Repository Evidence:** `backend/app/core/permissions.py`

---

## DISCOVERY AREA 2 — TEAMS AND STRUCTURE

- **Existing team/department/group model:** **NOT FOUND.** Verified
  by direct search across `backend/app` for a `Team` class, a `teams`
  table, `team_leader`/`manager_id`/`reports_to`/`supervisor_id`
  columns — zero matches anywhere in the codebase.
- **Existing hierarchy/reporting-relationship support:** **NOT
  FOUND.** No user record anywhere carries a manager/supervisor
  reference. `User.department` exists but is explicitly documented in
  its own file as "presentational/organizational only... it never
  grants permissions" (`backend/app/models/user.py`) — it is a label,
  not a structural hierarchy.
- **Adjacent existing structure:**
  `BillingProviderOrganizationMembership` —
  `backend/app/billing/models/billing_provider_organization_membership.py`
  (table `billing_provider_organization_memberships`) links a `User`
  to a `BillingProviderOrganization` with only a flat
  `membership_role` of `MEMBER` or `ADMIN` (see
  `BILLING_PROVIDER_MEMBERSHIP_ROLES = {"MEMBER", "ADMIN"}`), plus
  `status` and an effective date window. This is a working,
  functional membership record, but it has **no team concept and no
  hierarchy levels** (no distinction between Company President,
  Billing Manager, Supervisor, or Team Leader — everyone is either a
  flat MEMBER or ADMIN of the organization).
- **Classification: CREATE** for `BillingTeam` and `TeamMembership`
  (no existing model to reuse or extend for team structure). **EXTEND
  candidate** for `BillingProviderOrganizationMembership`: its
  `membership_role` field could be widened from the current two-value
  set (`MEMBER`/`ADMIN`) to carry the five-level hierarchy (Company
  President / Billing Manager / Supervisor / Team Leader / Staff) if
  the hierarchy is modeled as an organization-wide attribute of
  membership, rather than creating a wholly separate hierarchy table —
  this decision is left open for the next planning phase, not resolved
  here.
- **Migration Required:** Yes — new `BillingTeam` and `TeamMembership`
  tables at minimum; possibly an `ALTER` to
  `billing_provider_organization_memberships.membership_role`'s check
  constraint if that EXTEND path is chosen.
- **Repository Evidence:**
  `backend/app/billing/models/billing_provider_organization_membership.py`,
  `backend/app/models/user.py`

---

## DISCOVERY AREA 3 — AGENCIES

### Agency ↔ Billing Organization relationship (org-level)
- **Existing Model:** `BillingProviderAgencyAssignment` +
  `BillingProviderAgencyServiceScope` —
  `backend/app/billing/models/billing_provider_agency_assignment.py`
- **Existing Table:** `billing_provider_agency_assignments`,
  `billing_provider_agency_service_scopes`
- **Existing Service:** `backend/app/billing/services/billing_provider_access_service.py`
  — resolves, for a given user, which billing-provider organizations
  they belong to (via `BillingProviderOrganizationMembership`), which
  tenants (agencies) are actively assigned to those organizations (via
  `BillingProviderAgencyAssignment`), and computes an effective
  tenant→financials-enabled map (`compute_tenant_financials_enabled_map`).
  This is a genuinely working access-resolution pipeline, not a stub.
- **Existing UI:** `sns-emr-frontend/src/owner/pages/BillingLicensing.jsx`
  — a fully functional CRUD screen (create/edit billing-provider
  organizations, create/edit agency assignments with relationship
  status and service scopes), reachable through the **SNS Tech
  Solutions owner platform**, not the Biller Platform.
- **Existing API:** `backend/app/billing/api/billing_provider_router.py`
  — `GET/POST /organizations`, `PATCH /organizations/{id}`,
  `GET/POST /assignments`, `PATCH /assignments/{id}`. Fully wired to
  the frontend above.
- **Service scopes already defined**
  (`BILLING_PROVIDER_SERVICE_SCOPES`): `BILLING_READINESS`, `CLAIMS`,
  `NOE_TRACKING`, `ELIGIBILITY`, `AUTHORIZATION_TRACKING`,
  `PAYMENT_POSTING`, `PAYMENT_RECONCILIATION`, `FACILITY_COLLECTIONS`,
  `CREDIT_BALANCES`, `AGING_REPORT`, `DENIALS_APPEALS`, `EDI`,
  `BILLING_REPORTS`, `FINANCIAL_MONITORING`, `CAP_MONITORING` — each
  with a `VIEW`/`EDIT` permission level
  (`BILLING_PROVIDER_PERMISSION_LEVELS`). This is conceptually close
  to, but distinct from, the requested Capability Matrix: these scopes
  govern what an entire **billing organization** may see/do for an
  **agency it is assigned to**, not what an individual **staff member**
  within that organization may do.
- **Classification: REUSE.** This is a mature, functional,
  already-in-production org-to-agency relationship layer. It should
  remain the system of record for "which billing organization serves
  which agency, with what service scopes." **EXTEND candidate:** the
  requested Agency Portfolio / Agency Coverage Matrix (Team, Team
  Leader, Medicare Biller, Medi-Cal Biller, Backup Coverage per
  agency) is a finer-grained, per-user/per-team layer that should be
  built as new tables that reference `billing_provider_agency_assignments`
  (or the underlying `tenant_id`) rather than duplicating the
  org-to-agency relationship itself.
- **Migration Required:** No changes anticipated to the existing
  `billing_provider_agency_assignments` / `billing_provider_agency_service_scopes`
  tables; new tables required for per-team/per-user coverage (Area 3
  continued below, "AgencyCoverage").
- **Repository Evidence:**
  `backend/app/billing/models/billing_provider_agency_assignment.py`,
  `backend/app/billing/services/billing_provider_access_service.py`,
  `backend/app/billing/api/billing_provider_router.py`,
  `sns-emr-frontend/src/owner/pages/BillingLicensing.jsx`

---

## DISCOVERY AREA 4 — PERMISSIONS

- **Existing capability-style model (narrow, unrelated namespace):**
  `STAFF_CAPABILITIES` / `PLATFORM_PERMISSION_MATRIX` in
  `backend/app/core/roles.py` — see Discovery Area 1. Reserved for SNS
  platform-staff administration (`staff.*`) only; explicitly not for
  billing capabilities.
- **Existing scope-style model (org-level, not user-level):**
  `BillingProviderAgencyServiceScope` (`VIEW`/`EDIT` per scope per
  org-to-agency assignment) — see Discovery Area 3. Governs
  organization-level access to agency data, not individual staff
  capabilities.
- **Existing RBAC/ACL/permission middleware for general application
  use:** **NOT FOUND as a working system** — `require_permission()`
  and `has_permission()` in `backend/app/core/permissions.py` are
  explicit placeholders (see Discovery Area 1). All real
  authorization in the codebase today is role-string based
  (`require_roles()` / `role_matches()`).
- **Classification: CREATE**, following the **data-driven matrix
  pattern already proven in `PLATFORM_PERMISSION_MATRIX`** as an
  architectural precedent (not a code path to extend — a new,
  separate matrix/table in a new namespace). The nine capabilities
  named in the approved spec (DDE Access, Claims Submission, Appeals,
  Payment Posting, AR Management, Room & Board Access, Executive
  Reporting, Agency Assignment, Workforce Administration) have no
  existing home anywhere in this codebase.
- **Migration Required:** Yes — new `WorkforceCapability` (capability
  catalog) and `CapabilityAssignment` (user ↔ capability, with
  override/audit support) tables.
- **Repository Evidence:** `backend/app/core/roles.py`,
  `backend/app/core/permissions.py`,
  `backend/app/billing/models/billing_provider_agency_assignment.py`

---

## DISCOVERY AREA 5 — ESCALATIONS

- **Existing "escalation" code:** `backend/app/services/escalation.py`
  — `escalate_idg_warnings(meeting)`. This computes a risk level
  (`NONE`/`WARNING`/`ESCALATED`/`CRITICAL`) for **IDG (Interdisciplinary
  Group) meetings** based on how many days old an incomplete meeting
  is. It is entirely specific to IDG meeting scheduling risk and has
  **no concept of an organizational escalation chain, manager
  hierarchy, work-queue ownership, or approval routing.** It is not
  reusable for billing-organization escalation chains.
- **Existing work-queue/task-ownership models:** Task-related models
  referenced elsewhere in this codebase (e.g. `Task`,
  `task_notification_engine.py` from the Communications Discovery
  Report) carry ownership/due-date fields but no escalation-level or
  chain-of-command concept.
- **Existing approval-workflow models:** None found that generalize to
  a reusable escalation chain (e.g. POC physician approval workflows
  exist but are single-purpose clinical approval records, not a
  general escalation-chain primitive).
- **Classification: CREATE.** No reusable escalation-chain structure
  exists anywhere in the codebase. `EscalationChain` and
  `EscalationLevel` (Assigned Biller → Team Leader → Supervisor →
  Billing Manager → Company President, each potentially with an SLA)
  must be built new.
- **Migration Required:** Yes — new `EscalationChain` and
  `EscalationLevel` tables.
- **Repository Evidence:** `backend/app/services/escalation.py`

---

## DISCOVERY AREA 6 — SECUREINBOX DEPENDENCIES

Per the locked `COMMUNICATIONS_DISCOVERY_REPORT.md` (APPROVED /
LOCKED), SecureInbox itself is explicitly **not to be implemented**
here — this area only inventories what future SecureInbox routing
will need to derive from.

- **Notification models:** `Notification`
  (`backend/app/models/notification.py`) and `DocumentNotification`
  (`backend/app/models/document_notification.py`) — both confirmed
  working but orphaned/narrow, per the Communications Discovery
  Report Sections 2.1 and 2.3. No change required here; they remain
  candidate alerting-layer reuse targets for a future SecureInbox, not
  something this module needs to touch.
- **User directory services:** the `User` model itself
  (`backend/app/models/user.py`) is the only "directory" — there is no
  separate directory/lookup service. Any future SecureInbox routing
  preview must resolve names/roles directly from `User` plus whatever
  new Team/AgencyCoverage/CapabilityAssignment tables this module
  creates.
- **Audit trail:** `backend/app/billing/audit_store.py`
  (`build_audit_event`/`append_audit_event`/`list_audit_events`),
  exposed via `backend/app/billing/api/audit_router.py`, is a working,
  billing-scoped audit-event service already in production use. This
  is the correct REUSE target for the "Auditable / Tenant Scoped /
  Traceable / Idempotent" work-item requirements carried over from
  prior locked pages (e.g. Credit Balance Resolution), and for
  `AssignmentAudit` in this module.
- **Assignment services:** `billing_provider_access_service.py` (see
  Discovery Area 3) is the closest existing "assignment resolution"
  service, but it resolves organization-to-agency access, not
  individual-to-agency messaging routes. The new Agency Coverage
  assignments this module creates (Team Leader / Medicare Biller /
  Medi-Cal Biller / Backup Coverage per agency) will be the actual
  data source for the future SecureInbox Routing Preview (Phase 11) —
  confirming the approved architecture ("Billing Organization becomes
  the authoritative routing foundation for SecureInbox... do not
  hard-code user routing relationships").
- **No SecureInbox implementation performed.** Consistent with the
  locked Communications Discovery Report and this module's own Phase
  11 requirement ("Display only. No messaging functionality.").

---

## CLASSIFICATION SUMMARY (ALL CANDIDATE OBJECTS)

| Candidate Object | Existing Model | Existing Table | Existing Service | Existing UI | Existing API | Classification | Reason | Migration Required |
|---|---|---|---|---|---|---|---|---|
| BillingOrganization | `BillingProviderOrganization` | `billing_provider_organizations` | — | `BillingLicensing.jsx` (owner platform) | `billing_provider_router.py` (`/organizations`) | **REUSE** | Already a working, production org record (name, type, status) | No |
| BillingTeam | — | — | — | — | — | **CREATE** | No team/department/group model exists anywhere | Yes — new table |
| TeamMembership | `BillingProviderOrganizationMembership` (adjacent, not equivalent) | `billing_provider_organization_memberships` | `billing_provider_access_service.py` | — | — (model exists, no dedicated CRUD route found) | **CREATE** (new table); **EXTEND** possible for hierarchy levels on the adjacent org-membership record | Existing membership is org-wide flat MEMBER/ADMIN only, no team, no hierarchy levels | Yes — new table, possible ALTER to adjacent model |
| AgencyAssignment (org→agency) | `BillingProviderAgencyAssignment` | `billing_provider_agency_assignments` | `billing_provider_access_service.py` | `BillingLicensing.jsx` | `billing_provider_router.py` (`/assignments`) | **REUSE** | Mature, functional, in-production org-to-agency relationship layer | No |
| AgencyCoverage (Team/Team Leader/Medicare Biller/Medi-Cal Biller/Backup per agency) | — | — | — | — | — | **CREATE** | No per-user/per-team agency coverage concept exists; only org-level assignment exists | Yes — new table |
| WorkforceCapability (capability catalog) | `STAFF_CAPABILITIES` (unrelated namespace) | — | — | — | — | **CREATE** | Existing capability set is `staff.*` platform-admin only, explicitly not for billing capabilities | Yes — new table |
| CapabilityAssignment | `PLATFORM_PERMISSION_MATRIX` (architectural precedent only) | — | — | — | — | **CREATE** | Same pattern worth following; no billing-capability data exists | Yes — new table |
| EscalationChain | — | — | `escalation.py` (unrelated — IDG-meeting-specific) | — | — | **CREATE** | No organizational escalation-chain structure exists | Yes — new table |
| EscalationLevel | — | — | — | — | — | **CREATE** | Same as above | Yes — new table |
| WorkloadMetric | — | — | — | — | — | **CREATE** | No workforce/caseload-balancing calculation exists | Yes — new table |
| AssignmentAudit | `build_audit_event()` / `append_audit_event()` / `list_audit_events()` (reusable) | audit event store used by `backend/app/billing/api/audit_router.py` | `backend/app/billing/audit_store.py` (billing-specific) plus generic `backend/app/services/audit_events.py` / `backend/app/core/audit_events.py` | — | `audit_router.py` (billing) | **REUSE** | A billing-specific, working audit-event build/append/list service already exists in the billing module itself, plus a generic one used across other modules (documents, patients, bereavement, NOE); reuse the billing one rather than building a bespoke audit table | No — call existing service |

---

## OPEN QUESTIONS FOR NEXT PLANNING PHASE

1. Should the five-level hierarchy (Company President / Billing
   Manager / Supervisor / Team Leader / Staff) be modeled as an
   attribute of `BillingProviderOrganizationMembership` (EXTEND path),
   or as its own dedicated hierarchy table independent of team
   membership? This report intentionally leaves this open rather than
   deciding it.
2. Should `BillingTeam` be scoped under a `BillingProviderOrganization`
   (one org, many teams) — this appears to be the only architecture
   consistent with the existing org model, but is not yet formally
   decided.
3. Should Agency Coverage (Medicare Biller / Medi-Cal Biller / Backup)
   reference `BillingProviderAgencyAssignment` directly (one coverage
   record per org-to-agency assignment) or the underlying `tenant_id`
   directly? The former keeps a single source of truth for "is this
   agency actually assigned to this billing org," the latter risks an
   agency having coverage data without an active org assignment.
4. Confirm whether `WorkloadMetric` should be a stored/materialized
   snapshot table (recomputed periodically) or a purely computed view
   over existing Claims/Denials/AR/Room & Board data once those
   entities exist (per the main Biller Platform handoff doc's Pages
   3, 4, 9, 11) — those source entities are themselves still CREATE
   (not yet built), so `WorkloadMetric` has a hard dependency on them.

No answers to these questions are assumed or implied by this report.

---

## RELATIONSHIP TO OTHER DOCUMENTS

This report is the required discovery deliverable for the approved
"[Biller Platform] Implement Billing Organization" GitHub issue, and
satisfies Discovery Areas 1-6 of that issue's Repository Discovery
Plan. It is independent of, and does not modify:
- `docs/biller-platform/BILLER_PLATFORM_FINAL_IMPLEMENTATION_HANDOFF.md`
  (the canonical Biller Platform spec; Billing Organization will be
  added there as a new page once this discovery is reviewed).
- `docs/biller-platform/BILLER_PLATFORM_DISCOVERY_REPORT.md` (separate,
  still-outstanding addendum for Pages 4-12 entities).
- `docs/communications/COMMUNICATIONS_DISCOVERY_REPORT.md` (APPROVED /
  LOCKED — SecureInbox remains future functionality; Discovery Area 6
  above only confirms alignment with that document, per its own
  locked Section 9 sequencing).

No schema, migration, model, service, or route changes were made
while producing this report.

---

## CHANGE LOG

| Date | Change |
|---|---|
| 2026-09-17 | Document created. Full repository discovery completed for all six required Discovery Areas (Identity/Users, Teams/Structure, Agencies, Permissions, Escalations, SecureInbox Dependencies) per the approved Billing Organization GitHub issue. Headline finding: a working, production billing-organization system already exists (`BillingProviderOrganization`, `BillingProviderOrganizationMembership`, `BillingProviderAgencyAssignment`, `BillingProviderAgencyServiceScope`), exposed through the SNS Tech Solutions owner platform's Billing/Licensing admin page — classified REUSE for the org record and org-to-agency assignment layer. No Team, per-user Agency Coverage, billing-specific Capability Matrix, Escalation Chain, or Workload Metric structures exist anywhere — all classified CREATE. The `require_permission`/`has_permission` functions in `app/core/permissions.py` are confirmed unimplemented placeholders, not a usable fine-grained permission engine. The dormant `Role`/`interfaces` model is confirmed to have zero live consumers and must not be revived. A generic `audit_event()` service is confirmed reusable for the new module's audit-trail requirement. Documentation only; no schema, migrations, tables, models, or routes created or changed. |
