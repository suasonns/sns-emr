# BILLING ORGANIZATION DISCOVERY REPORT

STATUS: DISCOVERY COMPLETE (MODULE-LEVEL + AGENCY COVERAGE & WORKLOAD
PAGE-LEVEL ADDENDUM) — SCHEMA/MIGRATION/API/MODEL WORK NOT YET
AUTHORIZED

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
- **Audit trail — CORRECTED (see Section 18.5 for full detail):**
  `backend/app/billing/audit_store.py`
  (`build_audit_event`/`append_audit_event`/`list_audit_events`) is
  **not** a durable, database-backed audit service — `AUDIT_EVENTS` is
  a plain in-process Python list, and its schema (`patient_id`,
  `billing_cycle_id`, `claim_control_number`) is scoped to per-patient
  billing-cycle events, not org/team/agency/assignment events. It is
  **not** a valid REUSE target for this module's `AssignmentAudit`
  requirement. The correct, durable, database-backed precedent is
  `backend/app/billing/models/facility_payment_audit_log.py`
  (`FacilityPaymentAuditLog` — tenant-scoped, `entity_type`/`entity_id`,
  `previous_value`/`new_value`, `user_id`, `role`, `reason`,
  `correlation_id`, indexed, real table), which this module's audit
  requirement should follow as a structural pattern (EXTEND-by-pattern,
  not literal reuse of the table itself, since entity types differ).
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
| AssignmentAudit | `FacilityPaymentAuditLog` (structural precedent, not literal reuse) | `facility_payment_audit_log` (precedent table; new table needed for this module) | — | — | — | **CREATE (pattern-EXTEND)** | `billing/audit_store.py` is an in-memory list scoped to patient/billing-cycle events — not durable, not applicable. `FacilityPaymentAuditLog` is the correct durable, tenant-scoped, correlation-ID-bearing structural precedent to follow for a new billing-organization audit table | Yes — new table modeled on the `FacilityPaymentAuditLog` pattern |

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

## SECTION 18 — AGENCY COVERAGE & WORKLOAD PAGE-LEVEL DISCOVERY ADDENDUM

This section is the required discovery deliverable for the approved
"Billing Organization → Agency Coverage & Workload" implementation
handoff, which requires a detailed 20-entity mapping (Existing Model /
Existing Table / Existing Relationships / Existing Fields / Existing
Constraints / Existing Indexes / Existing APIs / Existing UI /
Decision / Reason / Migration Required / Files Affected /
Verification Evidence) before any schema, migration, API, service, or
UI logic for that page is created. Agency Coverage & Workload is one
of three approved Billing Organization pages (Organization & Teams;
Agency Coverage & Workload; Access Administration) — this addendum
covers Agency Coverage & Workload only.

### 18.1 Billing Organization — REUSE

- **Existing Model:** `BillingProviderOrganization`
- **Existing Table:** `billing_provider_organizations`
- **Existing Relationships:** referenced by
  `BillingProviderOrganizationMembership.billing_provider_organization_id`
  and `BillingProviderAgencyAssignment.billing_provider_organization_id`
- **Existing Fields:** `name` (unique, indexed), `organization_type`
  (indexed), `status` (`ACTIVE`/`INACTIVE`, indexed), `notes`,
  `updated_by` (FK → `users.id`)
- **Existing Constraints:** `ck_billing_provider_organization_status_valid`
  (status IN ACTIVE/INACTIVE)
- **Existing Indexes:** unique index on `name`; index on
  `organization_type`; index on `status`; composite
  `ix_billing_provider_org_type_status`
- **Existing APIs:** `GET/POST /organizations`,
  `PATCH /organizations/{id}` in
  `backend/app/billing/api/billing_provider_router.py`
- **Existing UI:** `sns-emr-frontend/src/owner/pages/BillingLicensing.jsx`
  (owner platform, not Biller Platform)
- **Decision:** REUSE
- **Reason:** Already models exactly what "North East Billing Center"
  is — a single billing-company organization record. No new
  organization table is needed.
- **Migration Required:** No
- **Files Affected:** None (read-only reference from new tables)
- **Verification Evidence:**
  `backend/app/billing/models/billing_provider_organization.py`

### 18.2 Billing Organization Membership — REUSE (with scope caveat)

- **Existing Model:** `BillingProviderOrganizationMembership`
- **Existing Table:** `billing_provider_organization_memberships`
- **Existing Relationships:** FK → `billing_provider_organizations.id`
  (CASCADE), FK → `users.id` (CASCADE), `updated_by` FK → `users.id`
  (SET NULL)
- **Existing Fields:** `membership_role` (`MEMBER`/`ADMIN`, default
  `MEMBER`), `status` (`ACTIVE`/`INACTIVE`/`SUSPENDED`, default
  `ACTIVE`), `effective_start_at` (required), `effective_end_at`
  (nullable)
- **Existing Constraints:**
  `ck_billing_provider_membership_role_valid`,
  `ck_billing_provider_membership_status_valid`,
  `ck_billing_provider_membership_effective_window_valid` (end ≥
  start)
- **Existing Indexes:** `ix_bp_org_memberships_org_status`,
  `ix_bp_org_memberships_user_status`, unique partial index
  `uq_bp_org_memberships_active_pair` (one active membership per
  user+org)
- **Existing APIs:** None dedicated (model is consumed internally by
  `billing_provider_access_service.py` only — confirmed no
  `/memberships` route exists in `billing_provider_router.py`)
- **Existing UI:** None
- **Decision:** REUSE for "does this user belong to North East Billing
  Center" — this is the correct record for that fact, and its
  `effective_start_at`/`effective_end_at`/`status` fields are the
  proven pattern this module's new Assignment Status and Assignment
  Effective Period requirements (18.11/18.12) should copy.
- **Reason:** Working, constrained, indexed membership record already
  exists; only its role field (`MEMBER`/`ADMIN`) is too coarse to
  express the 5-level hierarchy (Company President / Billing Manager
  / Supervisor / Team Leader / Staff) — that hierarchy concept is
  CREATE, layered on top, not a replacement of this table.
- **Migration Required:** Only if the hierarchy is later modeled as a
  widened `membership_role` enum (open question, not decided in this
  addendum); no migration required for Agency Coverage & Workload
  itself, which only needs to read membership, not the hierarchy
  level.
- **Files Affected:** None for this page (read-only)
- **Verification Evidence:**
  `backend/app/billing/models/billing_provider_organization_membership.py`,
  `backend/app/billing/services/billing_provider_access_service.py`

### 18.3 Billing Team — CREATE

- **Existing Model:** None
- **Existing Table:** None
- **Existing Relationships:** N/A
- **Existing Fields:** N/A
- **Existing Constraints:** N/A
- **Existing Indexes:** N/A
- **Existing APIs:** None
- **Existing UI:** None (canonical sample teams "Team Alpha" / "Team
  Beta" referenced in the approved spec do not exist anywhere in the
  database or code)
- **Decision:** CREATE
- **Reason:** Confirmed via direct grep — no `Team` class, no `teams`
  table, anywhere in `backend/app`.
- **Migration Required:** Yes — new `billing_teams` table, scoped to a
  `billing_provider_organization_id` (one org, many teams).
- **Files Affected:** new model file under
  `backend/app/billing/models/`, new Alembic revision, new router.
- **Verification Evidence:** repository-wide grep, zero matches for
  `class Team`, `teams` table, `team_leader`, `manager_id`,
  `reports_to`, `supervisor_id`.

### 18.4 Team Membership — CREATE

- **Existing Model:** None (adjacent: `BillingProviderOrganizationMembership`,
  see 18.2 — organization-level, not team-level)
- **Decision:** CREATE
- **Reason:** No team concept exists to have membership in.
- **Migration Required:** Yes — new `billing_team_memberships` table
  (user_id + billing_team_id + status + effective window, following
  the 18.2 pattern).
- **Files Affected:** new model, new migration, new router.
- **Verification Evidence:** Same grep as 18.3.

### 18.5 Team Leader Assignment — CREATE

- **Existing Model:** None
- **Decision:** CREATE
- **Reason:** No manager/leader designation field exists anywhere
  (`User` has no `manager_id`; `BillingProviderOrganizationMembership.membership_role`
  only distinguishes `MEMBER`/`ADMIN`, not "Team Leader").
- **Migration Required:** Yes — either (a) a `role_on_team` column on
  the new `billing_team_memberships` table (18.4), or (b) a dedicated
  `billing_team_leader_assignments` table if a team must support
  co-leadership or leader history distinct from plain membership. This
  addendum documents both options as CREATE; the specific shape is an
  implementation-phase decision, not resolved here.
- **Files Affected:** new column or new table + migration + router.
- **Verification Evidence:** `backend/app/models/user.py` (no
  hierarchy field), `billing_provider_organization_membership.py` (no
  leader designation).

### 18.6 Billing Supervisor Assignment — CREATE

- **Existing Model:** None
- **Decision:** CREATE
- **Reason:** Same finding as 18.5 — no supervisor-of-team-leader
  relationship exists anywhere. The approved Role-Based Scope section
  ("Billing Supervisor: Assigned teams and agency portfolios") is new
  functionality.
- **Migration Required:** Yes — new `billing_supervisor_assignments`
  table (user_id ↔ one or more `billing_teams`), or a supervisor
  reference column on `billing_teams` if one supervisor per team is
  sufficient — open question for implementation phase.
- **Files Affected:** new model/table + migration + router.
- **Verification Evidence:** Same grep as 18.3; also confirmed no
  `supervisor_id` field on `User` or any billing model.

### 18.7 Agency Assignment (org → agency) — REUSE

- **Existing Model:** `BillingProviderAgencyAssignment`
- **Existing Table:** `billing_provider_agency_assignments`
- **Existing Relationships:** FK → `billing_provider_organizations.id`
  (CASCADE), FK → `tenants.id` (CASCADE, i.e. the agency), `updated_by`
  FK → `users.id` (SET NULL); has-many
  `BillingProviderAgencyServiceScope` (cascade delete-orphan)
- **Existing Fields:** `relationship_status`
  (`ACTIVE`/`SUSPENDED`/`TERMINATED`/`PENDING`, default `PENDING`,
  indexed), `effective_start_at` (required), `effective_end_at`
  (nullable)
- **Existing Constraints:**
  `ck_billing_provider_assignment_relationship_status_valid`,
  `ck_billing_provider_assignment_effective_window_valid`
- **Existing Indexes:** `ix_billing_provider_assignment_tenant_status`,
  `ix_billing_provider_assignment_org_status`
- **Existing APIs:** `GET/POST /assignments`,
  `PATCH /assignments/{id}` in `billing_provider_router.py`
- **Existing UI:** `BillingLicensing.jsx` (owner platform)
- **Decision:** REUSE
- **Reason:** This is exactly "which agencies are assigned to the
  billing organization" — the first required question of the Agency
  Coverage & Workload page. The page's "Assigned Agency Scope"
  selector and "Total Assigned Agencies" KPI must be computed from
  this table (filtered to `relationship_status = 'ACTIVE'`), not from
  a new table.
- **Migration Required:** No
- **Files Affected:** None (read-only consumer)
- **Verification Evidence:**
  `backend/app/billing/models/billing_provider_agency_assignment.py`

### 18.8 Medicare Billing Assignment — CREATE

- **Existing Model:** None per-user. Adjacent:
  `BillingProviderAgencyServiceScope` has a `PAYMENT_POSTING` /
  `CLAIMS` scope with `VIEW`/`EDIT` permission levels, but that is an
  **organization-level** capability flag on the org-to-agency
  assignment, not "which individual staff member is the Medicare
  Biller for this agency."
- **Decision:** CREATE
- **Reason:** The approved spec requires per-agency, per-individual
  role separation ("Medicare and Medi-Cal responsibilities must remain
  separate... Do not replace both assignments with one generic Primary
  Biller") — no existing structure expresses this granularity.
- **Migration Required:** Yes — new
  `billing_agency_coverage_assignments` table (or similarly named)
  with a `coverage_role` discriminator (`TEAM_LEADER` / `MEDICARE_BILLER`
  / `MEDICAID_MANAGED_CARE_BILLER` / `BACKUP` / `SPECIALIST`),
  `agency_assignment_id` (FK → `billing_provider_agency_assignments.id`,
  per Open Question 3's recommended direction — see Section 19), a
  `user_id`, `status`, and effective window fields (following the 18.2
  pattern).
- **Files Affected:** new model, new migration, new router, new
  service to compute Coverage Status.
- **Verification Evidence:**
  `backend/app/billing/models/billing_provider_agency_assignment.py`
  (`BillingProviderAgencyServiceScope` class — org-level scope only,
  no user_id field on that class at all).

### 18.9 Medi-Cal / Managed Care Assignment — CREATE

- Same finding, same table/decision as 18.8 — one `coverage_role`
  value (`MEDICAID_MANAGED_CARE_BILLER`) on the same new coverage
  table, not a separate table. Documented as its own line item because
  the approved spec requires the two responsibilities to remain
  logically distinct and separately queryable/reportable, which a
  single discriminated table with a `coverage_role` column satisfies
  without needing two physical tables.

### 18.10 Backup Coverage Assignment — CREATE

- Same finding, same table as 18.8/18.9 (`coverage_role = 'BACKUP'`).
  Reason for CREATE: the approved spec's "Backup Missing" and "Backup
  Contact must be different from active primary billers for the same
  agency" rules require a queryable backup record distinct from
  primary assignments — no existing structure supports this
  distinction. The uniqueness rule (backup ≠ primary biller for same
  agency) should be enforced at the service layer (and ideally a
  `CHECK`/application-level validation), not assumed to be free from
  the schema alone.

### 18.11 Additional Specialist Assignment — CREATE

- Same finding, same table (`coverage_role = 'SPECIALIST'`, with an
  optional `specialist_type` free-text or enum sub-field to be decided
  at implementation time, e.g. for AR specialists or denials
  specialists layered onto a covered agency). No existing structure
  supports this; CREATE.

### 18.12 Assignment Status — REUSE (pattern only, not a shared table)

- **Existing Pattern:** Every existing assignment/membership model in
  this codebase (`BillingProviderOrganizationMembership.status`,
  `BillingProviderAgencyAssignment.relationship_status`) already
  implements a `CheckConstraint`-enforced status enum
  (`ACTIVE`/`INACTIVE`/`SUSPENDED` or
  `ACTIVE`/`SUSPENDED`/`TERMINATED`/`PENDING`).
- **Decision:** REUSE THE PATTERN, CREATE THE COLUMN — the new
  `billing_agency_coverage_assignments` table (18.8-18.11) must carry
  its own `status` column following this exact established
  constraint-enum pattern (values to be finalized at implementation
  time; the approved spec's Coverage Status vocabulary — Fully
  Covered / Partially Covered / Coverage Gap / Temporary Coverary /
  Reassignment Pending / Suspended / Inactive — is a **derived,
  computed page-level value**, not a stored column; only the
  individual assignment's own ACTIVE/INACTIVE/SUSPENDED/PENDING status
  needs to be stored — Coverage Status is calculated from the set of
  assignments per agency, per the spec's own "Coverage must be
  determined from assignment records" rule).
- **Migration Required:** Yes, as part of 18.8's new table.
- **Verification Evidence:** `billing_provider_organization_membership.py`,
  `billing_provider_agency_assignment.py` (both existing `status`
  patterns).

### 18.13 Assignment Effective Period — REUSE (pattern only)

- **Existing Pattern:** `effective_start_at` / `effective_end_at` with
  a `CheckConstraint` requiring `end >= start` already exists
  identically on both `BillingProviderOrganizationMembership` and
  `BillingProviderAgencyAssignment`.
- **Decision:** REUSE THE PATTERN, CREATE THE COLUMNS on the new
  coverage table (18.8-18.11) — do not invent a different date-range
  convention.
- **Migration Required:** Yes, as part of 18.8's new table.
- **Verification Evidence:** Same two files as 18.12.

### 18.14 Staff Capability — CREATE

- **Existing Model:** `STAFF_CAPABILITIES` /
  `PLATFORM_PERMISSION_MATRIX` in `backend/app/core/roles.py` —
  confirmed in the module-level discovery (Section 4/Discovery Area 4
  above) to be explicitly scoped to the `staff.*` platform-admin
  namespace only, not usable for billing capabilities.
- **Decision:** CREATE
- **Reason:** No change from the module-level finding. The
  capabilities implied by this page's authorization model
  (`billing_org.coverage.view`, `billing_org.coverage.export`,
  `billing_org.assignment.view`, `billing_org.assignment.manage`,
  `billing_org.workload.view`, `billing_org.workload.review`,
  `billing_org.routing_preview.view`) do not exist anywhere.
- **Migration Required:** Yes — new capability catalog +
  user/role-to-capability assignment tables (`WorkforceCapability` /
  `CapabilityAssignment`, per the module-level discovery Section 4).
- **Files Affected:** new models, new migration, new permission-check
  dependency (since `require_permission()`/`has_permission()` in
  `backend/app/core/permissions.py` are confirmed placeholder stubs —
  see module-level Discovery Area 4 — this page cannot rely on them
  for real enforcement and must build a real capability check).
- **Verification Evidence:** `backend/app/core/roles.py`,
  `backend/app/core/permissions.py`.

### 18.15 Individual DDE Authorization Status — CREATE

- **Existing Model:** None. Confirmed via repository-wide search — no
  match for `DDE` or `direct data entry` anywhere in `backend/app`.
- **Decision:** CREATE
- **Reason:** The main handoff document (`BILLER_PLATFORM_FINAL_IMPLEMENTATION_HANDOFF.md`,
  Section 9, "DDE ARCHITECTURE") already establishes DDE authorization
  as individually-scoped, not organization-wide, future functionality
  requiring an "Individual DDE User Profile" and "DDE Tenant
  Authorization" entity — neither has been built yet anywhere in the
  codebase. For Agency Coverage & Workload specifically, this page
  only needs to **display** a coarse status
  (Authorized/Not Authorized/Pending/Suspended/Expired/Not Required)
  sourced from that future DDE entity — it explicitly must not manage
  DDE credentials itself, per the approved spec's own "Agency Coverage
  & Workload does not manage DDE credentials" rule. This page has a
  **read dependency** on DDE entities that do not exist yet; it cannot
  display real DDE status until the DDE entities from the main handoff
  document are built. Until then, this page must render "Not
  Available" / a clearly-labeled placeholder rather than a fabricated
  status, consistent with the platform-wide "Unavailable values must
  not render as zero" rule in this same spec.
- **Migration Required:** Not by this page directly — depends on the
  separate, not-yet-scheduled DDE entity work referenced in the main
  handoff document.
- **Files Affected:** None yet (blocked dependency, not this page's
  responsibility to build).
- **Verification Evidence:** repository-wide grep, zero matches for
  `DDE`/`direct data entry` in `backend/app`;
  `BILLER_PLATFORM_FINAL_IMPLEMENTATION_HANDOFF.md` Section 9.

### 18.16 Workload Metrics — CREATE

- **Existing Model/Service:** None. No workload/caseload-balancing
  calculation exists anywhere (confirmed in module-level Discovery
  Area 2/Open Question 4).
- **Decision:** CREATE
- **Reason:** The approved spec restricts this page's workload
  calculation to three factual inputs only — Assigned Agencies, Active
  Patients, Open Claims — explicitly excluding Denials, AR, Payment
  Posting, Eligibility, NOE, Room & Board, and Escalations "unless
  discovery verifies authoritative inputs." This discovery confirms:
  **Active Patients** and **Open Claims** counts depend on Patient and
  Claim entities that are outside this module's scope — Claims in
  particular is still CREATE per the main Biller Platform handoff
  document's own Claims Management page (not yet built). This page's
  Workload Metrics must therefore be built as a **computed
  aggregation**, not a stored table, over: (a) the new Agency Coverage
  assignment table (18.8-18.11) for "Assigned Agencies" per staff
  member, and (b) whatever authoritative Patient/Claim counts already
  exist today (Patient model exists and is usable; a production
  "open claim" count depends on the not-yet-built Claims Management
  entities — this is a **cross-module dependency**, not a gap in this
  page's own discovery).
- **Migration Required:** No new persisted workload table required for
  this page (computed at query time); confirm at implementation time
  whether query performance requires a materialized snapshot — if so,
  that would be a later, explicitly-approved addition, not assumed
  here.
- **Files Affected:** new service function(s) only, once the
  dependent Agency Coverage table exists.
- **Verification Evidence:** module-level Discovery Area 2, Open
  Question 4; `backend/app/models/user.py` (no workload fields).

### 18.17 Access Scope — CREATE (composable from existing + new parts)

- **Existing Model/Service:** `billing_provider_access_service.py`
  already resolves organization membership → authorized tenant IDs
  (org-level access scope). No equivalent exists yet for
  team-scope or per-user-assignment scope (Team Leader limited to
  their own portfolio; Staff limited to their own assigned agencies;
  Supervisor limited to assigned teams), which the approved Role-Based
  Scope section requires.
- **Decision:** CREATE (a new access-scope resolution layer that
  composes the existing org-level resolver with the new Team/Coverage
  tables from 18.3-18.11), not a wholesale replacement of
  `billing_provider_access_service.py`.
- **Reason:** The approved formula — "Effective access equals
  Organization Membership + Role + Capability + Team Assignment +
  Agency Assignment + Account Status + Action-Specific Permission" —
  requires inputs from both the existing service and the new tables
  this page introduces; no existing function computes this composite
  today.
- **Migration Required:** No new table strictly required for scope
  resolution itself (it is a computed access-check, not a stored
  entity), assuming Team/Coverage tables (18.3-18.11) exist.
- **Files Affected:** new service function(s) layered on
  `billing_provider_access_service.py`; new FastAPI dependency for
  route guards.
- **Verification Evidence:**
  `backend/app/billing/services/billing_provider_access_service.py`.

### 18.18 Audit Event — CREATE (pattern-EXTEND)

- See Section 18's correction above and the Classification Summary
  table's corrected `AssignmentAudit` row: `billing/audit_store.py` is
  an in-memory, patient/billing-cycle-scoped list and is **not**
  reusable here. `FacilityPaymentAuditLog`
  (`backend/app/billing/models/facility_payment_audit_log.py`) is the
  correct durable, tenant-scoped, `correlation_id`-bearing structural
  precedent (previous_value/new_value/user_id/role/reason columns,
  indexed by tenant+entity).
- **Decision:** CREATE a new audit table for this module, modeled on
  `FacilityPaymentAuditLog`'s shape, capturing the required fields
  (Actor, Actor role, Billing organization, Team, Agency, Affected
  user, Action, Previous state, New state, Reason, Timestamp,
  Correlation ID) per the approved spec's Audit Requirements section.
- **Migration Required:** Yes.
- **Files Affected:** new model, new migration, service calls at every
  mutation point (assignment create/change/remove, backup coverage
  change, coverage-status recompute, workload review, export, access
  denial, access request).
- **Verification Evidence:**
  `backend/app/billing/models/facility_payment_audit_log.py`,
  `backend/app/billing/audit_store.py` (confirmed in-memory, not a
  valid precedent).

### 18.19 Export Event — CREATE (pattern-EXTEND)

- **Existing Model:** `ClaimExportLog`
  (`backend/app/billing/models/claim_export_log.py`) — a real,
  tenant-scoped, database-backed export-audit table (`file_path`,
  `export_type`, `status` SUCCESS/FAILED/RETRIED, `override_used`/
  `override_reason`/`override_approved_by`, `created_by`,
  `created_at`, indexed by patient+billing_cycle and by status).
- **Decision:** CREATE a new export-event table for this module,
  following `ClaimExportLog`'s structural pattern, extended with the
  fields this spec explicitly requires that `ClaimExportLog` does not
  have today: exporting user, billing organization, selected agency
  scope, filters, row count, result, and correlation ID.
- **Reason:** `ClaimExportLog` is scoped to
  `patient_id`/`billing_cycle_id` (claims export), not billing-org/
  agency-coverage export — not directly reusable, but its
  tenant-scoping + status + override-tracking shape is the correct
  template to follow rather than inventing a new export-audit
  convention.
- **Migration Required:** Yes.
- **Files Affected:** new model, new migration, export endpoint +
  service.
- **Verification Evidence:**
  `backend/app/billing/models/claim_export_log.py`.

### 18.20 Future SecureInbox Routing Relationship — NOT BUILT (by design)

- **Existing Model:** None, and per the approved spec and the locked
  `COMMUNICATIONS_DISCOVERY_REPORT.md`, none should be built under
  this scope.
- **Decision:** N/A — explicitly out of scope. The "SecureInbox
  Routing Preview" section of this page is display-only and must
  **derive from** the new Agency Coverage assignment table (18.8-
  18.11) at read time (Team Leader / Medicare Biller / Medi-Cal Biller
  / Backup Contact / Billing Supervisor per agency) — it must not
  create, reference, or hard-code any message/conversation/channel/
  attachment model, per both this spec and the locked Communications
  Discovery Report.
- **Migration Required:** No.
- **Files Affected:** read-only UI/service that queries 18.8-18.11 and
  18.6 (Supervisor) records; nothing new persisted.
- **Verification Evidence:**
  `docs/communications/COMMUNICATIONS_DISCOVERY_REPORT.md` (locked,
  Section 9).

---

## SECTION 19 — OPEN QUESTIONS CARRIED FORWARD

The module-level Open Questions (original "OPEN QUESTIONS FOR NEXT
PLANNING PHASE" section above) remain unresolved. This addendum adds:

5. Should the new Agency Coverage assignment table (18.8-18.11) be a
   single table with a `coverage_role` discriminator column (Team
   Leader / Medicare Biller / Medi-Cal Biller / Backup / Specialist),
   or four+ separate tables? This addendum recommends the single
   discriminated-table approach (fewer joins for the Agency Coverage
   Matrix query, simpler uniqueness constraints for "one active
   Medicare Biller per agency"), but this is a recommendation, not a
   locked decision.
6. Should the new Agency Coverage assignment reference
   `billing_provider_agency_assignments.id` (recommended — keeps
   coverage strictly subordinate to an active org-to-agency
   assignment, preventing coverage data from existing for an agency
   that isn't actually assigned to the billing organization) or
   `tenant_id` directly? This addendum recommends the former,
   consistent with Open Question 3 from the module-level discovery.
7. Should "Active Patients" and "Open Claims" in the Workload Metrics
   and Agency Coverage Matrix be computed live at request time, or
   cached/snapshotted for performance? Deferred to implementation
   phase; both approaches are compatible with "Coverage must be
   determined from assignment records," which only constrains
   coverage status, not the patient/claims count mechanism.

No answers to these questions are assumed or implied by this
addendum.

---

## RELATIONSHIP TO OTHER DOCUMENTS

This report is the required discovery deliverable for the approved
"[Biller Platform] Implement Billing Organization" GitHub issue (module
level) and the "Billing Organization → Agency Coverage & Workload"
implementation handoff (page level, Section 18-19 addendum), and
satisfies both the six module-level Discovery Areas and the 20-entity
Agency Coverage & Workload mapping requirement. It is independent of,
and does not modify:
- `docs/biller-platform/BILLER_PLATFORM_FINAL_IMPLEMENTATION_HANDOFF.md`
  (the canonical Biller Platform spec; Billing Organization, including
  Agency Coverage & Workload, will be added there as a new page once
  this discovery is reviewed).
- `docs/biller-platform/BILLER_PLATFORM_DISCOVERY_REPORT.md` (separate,
  still-outstanding addendum for Pages 4-12 entities).
- `docs/communications/COMMUNICATIONS_DISCOVERY_REPORT.md` (APPROVED /
  LOCKED — SecureInbox remains future functionality; Section 18.20
  above confirms the SecureInbox Routing Preview stays display-only,
  per that document's locked Section 9 sequencing).
- `docs/biller-platform/BILLER_PLATFORM_IMPLEMENTATION_VERIFICATION.md`
  — the Agency Coverage & Workload handoff separately requires a new
  "Agency Coverage & Workload Verification" section in that document
  once implementation (not discovery) is authorized and complete; not
  created in this pass.

No schema, migration, model, service, or route changes were made
while producing this report or this addendum.

---

## CHANGE LOG

| Date | Change |
|---|---|
| 2026-09-17 | Document created. Full repository discovery completed for all six required Discovery Areas (Identity/Users, Teams/Structure, Agencies, Permissions, Escalations, SecureInbox Dependencies) per the approved Billing Organization GitHub issue. Headline finding: a working, production billing-organization system already exists (`BillingProviderOrganization`, `BillingProviderOrganizationMembership`, `BillingProviderAgencyAssignment`, `BillingProviderAgencyServiceScope`), exposed through the SNS Tech Solutions owner platform's Billing/Licensing admin page — classified REUSE for the org record and org-to-agency assignment layer. No Team, per-user Agency Coverage, billing-specific Capability Matrix, Escalation Chain, or Workload Metric structures exist anywhere — all classified CREATE. The `require_permission`/`has_permission` functions in `app/core/permissions.py` are confirmed unimplemented placeholders, not a usable fine-grained permission engine. The dormant `Role`/`interfaces` model is confirmed to have zero live consumers and must not be revived. A generic `audit_event()` service is confirmed reusable for the new module's audit-trail requirement. Documentation only; no schema, migrations, tables, models, or routes created or changed. |
| 2026-09-18 | Added Section 18-19: Agency Coverage & Workload page-level discovery addendum, per the approved "Billing Organization → Agency Coverage & Workload" implementation handoff. Mapped all 20 required entities (Billing Organization, Billing Organization Membership, Billing Team, Team Membership, Team Leader Assignment, Billing Supervisor Assignment, Agency Assignment, Medicare Billing Assignment, Medi-Cal/Managed Care Assignment, Backup Coverage Assignment, Additional Specialist Assignment, Assignment Status, Assignment Effective Period, Staff Capability, Individual DDE Authorization Status, Workload Metrics, Access Scope, Audit Event, Export Event, Future SecureInbox Routing Relationship) using the required detailed template (Existing Model/Table/Relationships/Fields/Constraints/Indexes/APIs/UI/Decision/Reason/Migration Required/Files Affected/Verification Evidence). **Correction to the 2026-09-17 entry above:** `backend/app/billing/audit_store.py` was re-verified and found to be an in-memory Python list scoped to patient/billing-cycle events, not a durable, org/agency-scoped audit table — it is NOT a valid reuse target for this module's audit requirement (updated the Classification Summary table's `AssignmentAudit` row accordingly); the correct structural precedent is the database-backed `FacilityPaymentAuditLog`. Also identified `ClaimExportLog` as the correct structural precedent for the new Export Event requirement. Recommended (not locked) that the four coverage-role assignment types (Medicare/Medi-Cal/Backup/Specialist) be modeled as one discriminated `billing_agency_coverage_assignments` table referencing `billing_provider_agency_assignments.id`, following the existing `status` + `effective_start_at`/`effective_end_at` pattern already proven on `BillingProviderOrganizationMembership` and `BillingProviderAgencyAssignment`. Documentation only; no schema, migrations, models, services, or routes created or changed. Page-level implementation (schema, migrations, APIs, UI) for Agency Coverage & Workload remains blocked pending user review of this addendum. |
