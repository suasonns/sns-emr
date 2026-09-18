# BILLING ORGANIZATION DISCOVERY REPORT

STATUS: DISCOVERY APPROVED — SCHEMA DESIGN REVIEW AUTHORIZED (MODULE-
LEVEL + AGENCY COVERAGE & WORKLOAD + EXPANDED AGENCY DETAIL + SCHEMA-
DESIGN ADDENDA) — MIGRATION DESIGN, API DESIGN, AND UI IMPLEMENTATION
REMAIN BLOCKED

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

## SECTION 20 — EXPANDED AGENCY DETAIL DISCOVERY ADDENDUM

This section is the required discovery deliverable for the approved
"Billing Organization → Expanded Agency Detail" implementation
handoff — a detail view reached from Agency Coverage & Workload →
Agency Coverage Matrix → Select Agency (not a new top-level nav item,
not a separate agency-management module). Most underlying entities
were already discovered in Section 18; this addendum documents only
the **delta** items this detail screen additionally depends on.

### 20.1 Route / navigation precedent — REUSE (pattern)

- **Existing pattern:** the codebase already has an established
  master-detail / matrix-row-to-detail navigation convention (e.g.
  patient chart drill-downs under `charts/`). No Agency Coverage
  Matrix route exists yet because Agency Coverage & Workload itself
  (Section 18) has not been implemented. This detail screen must be
  built as a child route of that not-yet-built page, using the
  repository's existing routing conventions — not a new pattern.
- **Decision:** REUSE (routing convention only); the concrete route
  itself is CREATE, dependent on Section 18 landing first.
- **Migration Required:** No (frontend routing only).

### 20.2 Claim model / Open Claims Summary categorization — REUSE + CREATE

- **Existing Model:** `Claim` — `backend/app/billing/models/claim.py`
- **Existing Table:** `claims`
- **Existing Relationships:** FK → `tenants.id`, FK → `patients.id`,
  FK → `billing_cycles.id`, FK → `edi_batches` (`edi_batch_id`)
- **Existing Fields:** `payer_name` (free-text `String(255)`, **not**
  an enum/category), `service_date`, `total_charge`, `total_units`,
  `risk_score`, `status`, `last_status_reason`,
  `claim_control_number`, `exported_at`, `created_at`/`updated_at`/
  `created_by`
- **Existing Constraints/Indexes:** `ix_claim_tenant_status`
  (tenant_id + status)
- **Existing APIs/UI:** Claim submission/EDI infrastructure exists in
  the billing module, but the Biller Platform's own "Claims
  Management" page (per the main handoff document) has not been
  built.
- **Decision:** **REUSE** the `Claim` model and its `tenant_id`/
  `status` index for the raw "Open Claims" count per agency (tenant).
  **CREATE** required for the claim-category breakdown (Medicare
  Hospice / Medi-Cal / Managed Care / Other) requested by the Open
  Claims Summary section — `payer_name` is free text today, not a
  constrained classification, so there is no authoritative "claim
  type" enum to group by yet.
- **Reason:** The approved spec explicitly warns: "Use only
  repository-supported claim classifications... Do not create a
  Medicare Part A or Medicare Part B classification unless the
  authoritative claim model uses those categories for this workflow."
  This discovery confirms the authoritative `Claim` model does **not**
  today carry any such categorization — implementing the Open Claims
  Summary's category breakdown therefore requires either (a) a new
  constrained `claim_category` column on `Claim` (migration), or (b) a
  derived mapping service from existing `payer_name` values to
  categories (no migration, but requires a maintained mapping table/
  config, and is fragile against free-text drift). This addendum
  recommends option (a) but leaves the final decision to the
  implementation phase — it is not resolved here.
- **Migration Required:** Yes, if option (a) is chosen (new column +
  backfill); no new table required for the count itself.
- **Files Affected:** `backend/app/billing/models/claim.py` (possible
  new column), new aggregation service.
- **Verification Evidence:** `backend/app/billing/models/claim.py`.
- **Update:** the enum value list for `claim_category` has since been
  supplied by the user and is now locked — see Section 20.9.

### 20.3 Active Patients count — REUSE (model) + CREATE (aggregation)

- **Existing Model:** `Patient` (general EMR patient model, tenant-
  scoped, already used platform-wide).
- **Decision:** REUSE the `Patient` model itself; CREATE a new
  aggregation service to compute "active patients assigned to this
  agency" for billing-coverage purposes — no existing service was
  found that already produces this specific billing-scoped count
  (confirmed via search; only an unrelated IDG bulk-meeting helper
  matched "active patient" text).
- **Migration Required:** No.
- **Files Affected:** new service function only.
- **Verification Evidence:** repository-wide search for
  `active_patient` show no existing billing-scoped aggregation.

### 20.4 Backup Responsibility Scope — CREATE (new field on 18.10's table)

- **Existing Model:** None. The Agency Coverage assignment table
  recommended in Section 18.8-18.11 (`billing_agency_coverage_assignments`)
  does not yet have a field expressing *which* responsibility a backup
  assignment covers (e.g. "Medicare coverage only").
- **Decision:** CREATE — add a `responsibility_scope` (or
  `backs_up_role`) column to the same coverage-assignment table from
  Section 18, referencing which `coverage_role` (Medicare Biller /
  Medi-Cal Biller) the backup record stands in for. This is an
  extension of the table already recommended in Section 18.10, not a
  new table.
- **Reason:** The approved spec requires backup scope to be explicit
  and separately trackable ("Do not imply that a Medicare-only backup
  also covers Medi-Cal or Managed Care") and to affect Coverage Status
  independently per responsibility.
- **Migration Required:** Yes, as part of the Section 18.8-18.11 table
  (additive column, not a separate migration if sequenced together).
- **Files Affected:** same new model/migration referenced in Section
  18.
- **Verification Evidence:** none found — confirmed CREATE via the
  same repository-wide search performed for Section 18.8-18.11.

### 20.5 Recent Assignment Activity / Assignment History — REUSE (pattern, same as 18.18)

- **Existing Model:** None durable and applicable (see Section 18.18
  correction re: `billing/audit_store.py`).
- **Decision:** REUSE the same new Audit Event table recommended in
  Section 18.18 (modeled on `FacilityPaymentAuditLog`) — "Recent
  Assignment Activity" on this detail screen is a filtered read view
  (by agency) over that same audit table, not a separate history
  mechanism. Do not create a second, parallel history table.
- **Reason:** The required fields for this screen's activity feed
  (Assignment Effective Date, Assignment Action, Affected User,
  Assignment Role, Actor, Actor Role, Agency, Reason/Context) map
  directly onto the fields already specified for the Section 18.18
  audit table (Actor, Actor role, Billing organization, Team, Agency,
  Affected user, Action, Previous state, New state, Reason, Timestamp,
  Correlation ID) plus the coverage assignment's own
  `effective_start_at`. No new entity is needed.
- **Migration Required:** No (beyond the Section 18.18 table itself).
- **Verification Evidence:** Section 18.18 above.

### 20.6 Export Detail — REUSE (pattern, same as 18.19)

- **Decision:** REUSE the same new Export Event table/pattern
  recommended in Section 18.19 (modeled on `ClaimExportLog`). "Export
  Detail" on this screen is the same export mechanism as "Export
  Coverage Report" in Section 18, scoped to a single agency rather
  than the full matrix — same table, different query filter. No
  separate export-audit entity is needed.
- **Migration Required:** No (beyond the Section 18.19 table itself).
- **Verification Evidence:** Section 18.19 above.

### 20.7 Server-side agency authorization — REUSE (service) + CREATE (scope layer)

- **Decision:** Same finding as Section 18.17 (Access Scope) —
  `billing_provider_access_service.py` resolves org-level tenant
  access; the per-agency, per-team, per-role scope check this detail
  screen requires ("Team Leader limited to assigned portfolio," "Staff
  limited to assigned agencies") is CREATE, layered on the existing
  service, not a replacement.
- **Verification Evidence:** Section 18.17 above.

### 20.8 Summary of NEW entities/fields introduced by this addendum

No wholly new tables are introduced beyond what Section 18 already
recommends. This addendum adds two field-level requirements to the
Section 18 recommended schema:
1. A `responsibility_scope` field on the coverage-assignment table
   (Section 20.4), and
2. A `claim_category` column on `Claim` (Section 20.2) to support the
   Open Claims Summary breakdown — the enum value list is now LOCKED
   (Section 20.9); column creation itself remains gated behind
   Migration Design authorization.

### 20.9 Claim Category Enum — LOCKED VALUE LIST

The user has supplied the authoritative, locked value list for the
`claim_category` column proposed in Section 20.2. This resolves the
open question of what values the classification uses, but does **not**
by itself authorize the migration — creating the column remains
subject to the same Schema Design Review / Migration Design
authorization gate as every other change in this report.

**Locked `claim_category` values:**

| # | Value | Category |
|---|---|---|
| 1 | `MEDICARE_HOSPICE` | Medicare Hospice benefit |
| 2 | `MEDICAID` | Medicaid (non-CA / generic) |
| 3 | `MEDI_CAL` | California Medicaid program |
| 4 | `MEDICARE_ADVANTAGE_HMO` | Medicare Advantage — HMO plan |
| 5 | `MEDICARE_ADVANTAGE_PPO` | Medicare Advantage — PPO plan |
| 6 | `COMMERCIAL_HMO` | Commercial payer — HMO plan |
| 7 | `COMMERCIAL_PPO` | Commercial payer — PPO plan |
| 8 | `COMMERCIAL_POS` | Commercial payer — Point of Service plan |
| 9 | `TRICARE` | TRICARE (military/veteran-dependent coverage) |
| 10 | `VETERANS_AFFAIRS` | Veterans Affairs (VA) direct coverage |
| 11 | `PRIVATE_PAY` | Self-pay / private pay, no third-party payer |
| 12 | `OTHER` | Any payer not covered by the above values |

**Enum-count reconciliation (requested verification):** the numbered
table above confirms **12 distinct enum values**, consistent with the
"12-value enum" description elsewhere in this section. The list breaks
down as **11 substantive, named payer categories** (rows 1-11:
`MEDICARE_HOSPICE` through `PRIVATE_PAY`) **plus 1 fallback value**
(row 12: `OTHER`), for 12 total. If the visible count of 11 came from
reading only the named-payer-category rows (1-11) without including
the `OTHER` fallback row, that is the source of the discrepancy —
`OTHER` is a full, distinct enum value in this design (it is
`CheckConstraint`-enforced like every other value, not a null/absent
state), and is required per Section 20.9's design note that no payer
should ever resolve to a missing/unclassified category. **Final locked
enum list, confirmed at 12 values, is the numbered table above —
unchanged from the original submission.**

**Design notes:**
- This is a **flat 12-value enum**, not a nested/hierarchical
  classification — `MEDI_CAL` is its own distinct value from
  `MEDICAID`, and the two Medicare Advantage plan types
  (`MEDICARE_ADVANTAGE_HMO`/`MEDICARE_ADVANTAGE_PPO`) are distinct from
  each other and from `MEDICARE_HOSPICE`.
- **Relationship to Agency Coverage's Medicare/Medi-Cal split (Section
  18/21/22):** the coverage-assignment discriminator (`coverage_role`
  ∈ `MEDICARE_BILLER`/`MEDICAID_MANAGED_CARE_BILLER`) and this new
  `claim_category` enum are **separate concepts and must not be
  merged**. `coverage_role` describes which staff role bills for an
  agency; `claim_category` describes an individual claim's payer type.
  The Open Claims Summary breakdown groups claims by `claim_category`,
  then the UI/reporting layer maps categories to responsible-role
  buckets (e.g. `MEDICARE_HOSPICE` + both Medicare Advantage values →
  "Medicare Biller" bucket; `MEDICAID`/`MEDI_CAL` → "Medi-Cal Biller"
  bucket) — this mapping is a display/reporting concern, not a schema
  relationship, and remains an implementation-phase decision, not
  locked here.
- `OTHER` is retained as a fallback bucket per the approved spec's
  general convention (Coverage Status, Backup Missing, etc. all avoid
  "no value" states); it is not a placeholder for an unimplemented
  category — any payer not matching one of the eleven named values is
  intentionally routed to `OTHER`.
- This value list is a `CheckConstraint`/enum column, following the
  same pattern as every other discriminator in this design
  (`coverage_role`, `backs_up_role`, `specialist_type` — Section
  21.2/22.1) — a closed set, not an open string, consistent with
  Section 22.6's stated extensibility approach (widen the constraint
  via a future migration if a 13th category is ever required).
- **Status:** value list LOCKED. Column creation (migration),
  backfill strategy for existing `Claim` rows, and the
  category-to-responsible-role display mapping remain **not
  authorized** — still gated behind Migration Design authorization,
  which has not been granted.

---


## SECTION 21 — AGENCY COVERAGE SCHEMA-DESIGN ADDENDUM

STATUS: SCHEMA DESIGN DOCUMENTED — STILL DISCOVERY/DESIGN ONLY. NO
SCHEMA, MIGRATION, API, OR UI HAS BEEN CREATED. IMPLEMENTATION REMAINS
BLOCKED.

This section responds to the required Discovery Addendum Verification
Checklist by expanding the single-discriminated-table recommendation
from Section 18.8-18.11 into a concrete, reviewable schema design. It
resolves the open questions raised in Sections 18-20 into specific
proposed decisions. Nothing in this section has been implemented —
it is a design proposal for review, not code.

### 21.1 Assignment Architecture

**Proposed table purpose.** Two new relationship layers are proposed,
kept intentionally separate because they answer two different
questions:

1. **Team-scope relationships** — "who leads/supervises a team as a
   whole" (portfolio-level, not tied to one agency).
2. **Agency-coverage relationships** — "who is individually
   responsible for a specific agency's billing work" (Medicare
   Biller, Medi-Cal/Managed Care Biller, Backup, Specialist).

Team Leader and Billing Supervisor are **not** rows in the
agency-coverage table (this directly resolves Checklist Item 4 /
prior-message point 4). Reason: a Team Leader's and Supervisor's
authority is scoped to the **team's whole portfolio**, not to one
agency at a time. Modeling them as agency-coverage rows would require
one row per agency per team member just to express "leads this team,"
duplicating data on every agency the team covers and making a
leadership change require N row updates instead of one. Team
Leader/Supervisor are therefore team-scope relationships, and the
Agency Coverage Matrix's "Team Leader" column is a **derived/joined
value** (agency → assigned team → team's active Team Leader), not a
stored per-agency fact.

**Assignment ownership.** Every new table below is owned by the
Billing Organization module (`backend/app/billing/models/`), following
the existing convention set by `billing_provider_*` models — new
tables use the `billing_` prefix, not a generic/shared name, to avoid
any risk of collision with unrelated "team"/"assignment" concepts
elsewhere in the codebase (none currently exist, per Section 18.3-18.6
discovery, but the naming convention prevents future ambiguity).

**Assignment lifecycle (applies identically to every new table
below):** `PENDING` (optional, only if an assignment requires approval
before taking effect — not required for MVP, omit unless a future
approval-gate use case is approved) → `ACTIVE` → `INACTIVE` (ended
normally, e.g. superseded) → (never physically deleted). No table
supports a hard delete; ending an assignment always means setting
`status = 'INACTIVE'` and `effective_end_at = now()`, never `DELETE`.

**Assignment status model.** Every new table reuses the exact
constraint-enum pattern already proven on
`BillingProviderOrganizationMembership.status` and
`BillingProviderAgencyAssignment.relationship_status`: a `String`
column, `CheckConstraint` restricting to a fixed set, indexed.
Proposed status set for all new assignment tables:
`{'ACTIVE', 'INACTIVE', 'SUSPENDED'}` (reusing
`BillingProviderOrganizationMembership`'s exact set, since these are
membership-shaped relationships, not the 4-value
`BillingProviderAgencyAssignment` relationship-status set, which
models a different concept — the org-to-agency business relationship,
not an individual work assignment).

**Effective dating strategy.** Every new table reuses the exact
`effective_start_at` (`NOT NULL`) / `effective_end_at` (`NULLABLE`)
pair with the same `CheckConstraint` (`effective_end_at IS NULL OR
effective_end_at >= effective_start_at`) already proven on both
existing assignment models. No new date-range convention is
introduced.

**History preservation strategy.** History is preserved two ways,
deliberately redundant for different consumption needs:
1. **Row-level history** — ended assignment rows are never deleted or
   overwritten; a new row is inserted for the replacement, and the old
   row's `status`/`effective_end_at` are updated to close it out. This
   answers "what was true, and when" via a simple query
   (`WHERE agency_assignment_id = ? AND coverage_role = ?
   ORDER BY effective_start_at`).
2. **Event-level audit history** — a separate append-only audit table
   (Section 21.9) captures the actor, reason, and correlation ID for
   *why* each row-level change happened — information the assignment
   rows themselves do not carry. Recent Assignment Activity (Section
   20.5) reads from the audit table; Coverage determination (Section
   21.6) reads from the assignment rows.

**Audit strategy.** See Section 21.9 (Audit Section) below —
consistent with Section 18.18/20.5's prior recommendation to model on
`FacilityPaymentAuditLog`, now finalized with an exact schema.

### 21.2 Discriminator Definition

**Proposed discriminator values** for the new
`billing_agency_coverage_assignments` table's `coverage_role` column:

| Value | Meaning |
|---|---|
| `MEDICARE_BILLER` | The single individual responsible for Medicare billing for this agency |
| `MEDICAID_MANAGED_CARE_BILLER` | The single individual responsible for Medi-Cal / Managed Care / HMO billing for this agency |
| `BACKUP` | A backup contact standing in for one specific primary responsibility (see 21.6 for the `backs_up_role` sub-field) |
| `SPECIALIST` | An additional specialist assigned to this agency beyond the four core roles (e.g. Room & Board specialist), with a free-text/enum `specialist_type` sub-field |

**Team Leader assignment** — NOT a `coverage_role` value. Modeled
instead as `role_on_team = 'LEADER'` on the new
`billing_team_memberships` table (Section 21.3), scoped to the team,
not the agency.

**Billing Supervisor assignment** — NOT a `coverage_role` value.
Modeled instead as its own team-scope table,
`billing_team_supervisor_assignments` (Section 21.3), because a
Supervisor may oversee multiple teams (a many-to-many relationship
distinct from plain team membership), per the approved spec's
"Billing Supervisor: Assigned teams and agency portfolios" (plural
teams).

**Medicare Biller assignment** — `coverage_role = 'MEDICARE_BILLER'`,
one active row per `agency_assignment_id` (enforced by partial unique
index, Section 21.5).

**Medi-Cal / Managed Care assignment** — `coverage_role =
'MEDICAID_MANAGED_CARE_BILLER'`, one active row per
`agency_assignment_id` (same enforcement).

**Backup Contact assignment** — `coverage_role = 'BACKUP'` plus a
required `backs_up_role` column identifying which of
`MEDICARE_BILLER`/`MEDICAID_MANAGED_CARE_BILLER` this backup stands in
for. One active row per (`agency_assignment_id`, `backs_up_role`)
pair (Section 21.5).

**Additional Specialist assignment** — `coverage_role = 'SPECIALIST'`,
many concurrent active rows allowed per `agency_assignment_id`
(distinguished by an optional `specialist_type` field), since the
approved spec does not restrict specialists to a single person.

**Unsupported assignment types.** `coverage_role` is a
`CheckConstraint`-enforced fixed set of exactly the four values above.
Any future coverage type (e.g. a hypothetical "Room & Board Biller")
requires an explicit migration adding a new enum value plus a locked
spec update — it must not be introduced as free text.

### 21.3 Relationship Scope

**Team-scope relationships** (new tables, both scoped to
`billing_teams`, which is itself scoped to a
`billing_provider_organization_id`):
- `billing_team_memberships` — `billing_team_id`, `user_id`,
  `role_on_team` (`{'LEADER', 'MEMBER'}`), `status`, effective window.
  Partial unique index: at most one `ACTIVE` row with
  `role_on_team = 'LEADER'` per `billing_team_id`.
- `billing_team_supervisor_assignments` — `billing_team_id`,
  `user_id`, `status`, effective window. Many-to-many (a supervisor
  may cover multiple teams; a team could theoretically have more than
  one active supervisor during a transition, though the approved spec
  implies one — enforce "one active supervisor per team" via partial
  unique index unless a future spec explicitly requires co-supervision).

**Agency-scope relationships** (new tables, both scoped to
`billing_provider_agency_assignments.id`, which itself already carries
`tenant_id` and `billing_provider_organization_id` — see 21.4 for why
those are also denormalized onto the new tables):
- `billing_agency_team_assignments` — which team currently covers
  which agency. `agency_assignment_id`, `billing_team_id`, `status`,
  effective window. Partial unique index: at most one `ACTIVE` row per
  `agency_assignment_id` (an agency is covered by exactly one team at
  a time).
- `billing_agency_coverage_assignments` — the discriminated table from
  21.2. `agency_assignment_id`, `coverage_role`, `backs_up_role`
  (nullable, required only when `coverage_role = 'BACKUP'`),
  `specialist_type` (nullable, only when `coverage_role = 'SPECIALIST'`),
  `user_id`, `status`, effective window.

**Billing-organization scope.** Both team-scope tables reach their
organization via `billing_team_id → billing_teams.billing_provider_organization_id`.
Both agency-scope tables reach theirs via
`agency_assignment_id → billing_provider_agency_assignments.billing_provider_organization_id`.
No new table needs its own direct `billing_provider_organization_id`
column for correctness (it is always derivable via FK), but see 21.4
for the denormalization recommendation applied for query/index
performance, consistent with existing codebase convention.

**Team Leader relationship scope — verified.** A Team Leader is scoped
to exactly the team they lead (`billing_team_memberships` row with
`role_on_team = 'LEADER'`); the Agency Coverage Matrix's displayed
"Team Leader" per agency is `agency → billing_agency_team_assignments
(ACTIVE) → billing_team_id → billing_team_memberships (ACTIVE,
role_on_team='LEADER') → user`. Nothing about the Team Leader concept
is stored per-agency.

**Billing Supervisor relationship scope — verified.** Same join
pattern via `billing_team_supervisor_assignments` instead of
`billing_team_memberships`.

**Coverage assignment scope — verified.** Every
`billing_agency_coverage_assignments` row is scoped to exactly one
`agency_assignment_id`, which is itself scoped to exactly one
`tenant_id` (agency) and one `billing_provider_organization_id`
(billing company) via the existing, REUSE-classified
`BillingProviderAgencyAssignment`.

**Assignment hierarchy — verified.** Company President / Billing
Manager / Billing Supervisor / Team Leader / Staff (per the
module-level Section 2 hierarchy) is **not** re-modeled by any of
these new tables — that broader organizational hierarchy remains the
open question already logged in the module-level "Open Questions"
section (whether it lives on
`BillingProviderOrganizationMembership.membership_role` or a separate
table). These new tables only model the **operational** relationships
(team leadership, team supervision, agency coverage) needed for the
Agency Coverage & Workload and Expanded Agency Detail pages; they do
not require the broader hierarchy question to be resolved first,
since "Team Leader" and "Supervisor" are directly identifiable roles
in their own right, independent of where they sit in the president→
staff chain.

### 21.4 Database Design

**Proposed table structure summary:**

| Table | Key Columns |
|---|---|
| `billing_teams` | `id`, `billing_provider_organization_id` (FK), `name`, `status`, `updated_by` |
| `billing_team_memberships` | `id`, `billing_team_id` (FK), `user_id` (FK), `role_on_team`, `status`, `effective_start_at`, `effective_end_at`, `updated_by` |
| `billing_team_supervisor_assignments` | `id`, `billing_team_id` (FK), `user_id` (FK), `status`, `effective_start_at`, `effective_end_at`, `updated_by` |
| `billing_agency_team_assignments` | `id`, `agency_assignment_id` (FK), `billing_team_id` (FK), `tenant_id` (denormalized), `status`, `effective_start_at`, `effective_end_at`, `updated_by` |
| `billing_agency_coverage_assignments` | `id`, `agency_assignment_id` (FK), `tenant_id` (denormalized), `coverage_role`, `backs_up_role`, `specialist_type`, `user_id` (FK), `status`, `effective_start_at`, `effective_end_at`, `updated_by` |
| `billing_agency_coverage_audit_events` | see 21.9 |
| `billing_agency_coverage_export_events` | see 21.10 |

**Required foreign keys:**
- `billing_teams.billing_provider_organization_id` → `billing_provider_organizations.id` (CASCADE)
- `billing_team_memberships.billing_team_id` → `billing_teams.id` (CASCADE)
- `billing_team_memberships.user_id` → `users.id` (CASCADE)
- `billing_team_supervisor_assignments.billing_team_id` → `billing_teams.id` (CASCADE)
- `billing_team_supervisor_assignments.user_id` → `users.id` (CASCADE)
- `billing_agency_team_assignments.agency_assignment_id` → `billing_provider_agency_assignments.id` (CASCADE)
- `billing_agency_team_assignments.billing_team_id` → `billing_teams.id` (RESTRICT — do not allow a team to be deleted while it still covers an agency)
- `billing_agency_team_assignments.tenant_id` → `tenants.id` (CASCADE, denormalized, kept in sync with the parent `agency_assignment_id`'s tenant at write time)
- `billing_agency_coverage_assignments.agency_assignment_id` → `billing_provider_agency_assignments.id` (CASCADE)
- `billing_agency_coverage_assignments.user_id` → `users.id` (RESTRICT — do not allow deleting a user who holds an active coverage assignment; require reassignment first)
- `billing_agency_coverage_assignments.tenant_id` → `tenants.id` (CASCADE, denormalized)
- every table's `updated_by` → `users.id` (SET NULL), matching the existing `BillingProviderOrganization`/`BillingProviderAgencyAssignment` convention

**Required indexes:**
- `billing_teams`: index on `(billing_provider_organization_id, status)`
- `billing_team_memberships`: index on `(billing_team_id, status)`; index on `(user_id, status)`; **partial unique** index on `(billing_team_id)` `WHERE status = 'ACTIVE' AND role_on_team = 'LEADER'`
- `billing_team_supervisor_assignments`: index on `(billing_team_id, status)`; index on `(user_id, status)`; partial unique index on `(billing_team_id)` `WHERE status = 'ACTIVE'`
- `billing_agency_team_assignments`: index on `(agency_assignment_id, status)`; index on `(billing_team_id, status)`; partial unique index on `(agency_assignment_id)` `WHERE status = 'ACTIVE'`
- `billing_agency_coverage_assignments`: index on `(agency_assignment_id, coverage_role, status)`; index on `(user_id, status)` (supports the Organization-Wide Staff Workload aggregation across all of a user's active assignments); partial unique index on `(agency_assignment_id, coverage_role)` `WHERE status = 'ACTIVE' AND coverage_role IN ('MEDICARE_BILLER', 'MEDICAID_MANAGED_CARE_BILLER')`; partial unique index on `(agency_assignment_id, backs_up_role)` `WHERE status = 'ACTIVE' AND coverage_role = 'BACKUP'`
- `billing_agency_coverage_audit_events`: index on `(tenant_id, entity_type, entity_id)` (mirrors `FacilityPaymentAuditLog`'s existing index); index on `(billing_provider_organization_id, created_at)` for the Recent Assignment Activity feed
- `billing_agency_coverage_export_events`: index on `(tenant_id, created_at)`; index on `(exported_by_user_id, created_at)`

**Tenant isolation strategy.** Every table that can be scoped to a
single agency (`billing_agency_team_assignments`,
`billing_agency_coverage_assignments`, and both event tables)
denormalizes a direct `tenant_id` column, following the exact
convention already used by `FacilityPaymentAuditLog` and
`ClaimExportLog` (both carry a direct `tenant_id` rather than requiring
a join), rather than inventing a new isolation pattern. `billing_teams`
and its two membership tables are NOT tenant-scoped (a billing team
belongs to the billing organization, not to any one tenant/agency) —
their isolation boundary is `billing_provider_organization_id`, not
`tenant_id`.

**Organization isolation strategy.** All new tables trace back to
exactly one `billing_provider_organization_id`, either directly
(`billing_teams`) or transitively via `billing_team_id` or
`agency_assignment_id`. No cross-organization team or coverage
assignment is possible by construction (every FK chain terminates at a
single org).

**Team isolation strategy.** `billing_agency_team_assignments` is the
single source of truth for "which team covers this agency" — no other
table is allowed to imply a team relationship (e.g. the coverage table
does not itself carry a `billing_team_id`; a coverage assignment's
team, if ever needed, must be derived via the agency's active team
assignment, not duplicated).

**Assignment ownership.** Every mutation is attributed via
`updated_by` on the row itself (current state) and via `actor_user_id`
on the audit event (historical state at time of change) — both are
populated from the authenticated request context, never client input.

**No duplicate models created.** Every table above is additive; none
replaces or duplicates `BillingProviderOrganization`,
`BillingProviderOrganizationMembership`, `BillingProviderAgencyAssignment`,
`BillingProviderAgencyServiceScope`, `User`, `Claim`, or any other
existing model identified in Sections 1-6/18/20.

### 21.5 Constraint Section (Uniqueness and Overlap)

**Active Team Leader uniqueness.** Partial unique index on
`billing_team_memberships (billing_team_id) WHERE status = 'ACTIVE'
AND role_on_team = 'LEADER'` — guarantees at most one active leader
per team at the database level, not just in application code.

**Active Billing Supervisor uniqueness.** Partial unique index on
`billing_team_supervisor_assignments (billing_team_id) WHERE status =
'ACTIVE'` — at most one active supervisor per team (per current spec
reading; revisit if co-supervision is later approved).

**Active Medicare assignment uniqueness.** Partial unique index on
`billing_agency_coverage_assignments (agency_assignment_id) WHERE
status = 'ACTIVE' AND coverage_role = 'MEDICARE_BILLER'`.

**Active Medi-Cal assignment uniqueness.** Partial unique index on the
same table `WHERE status = 'ACTIVE' AND coverage_role =
'MEDICAID_MANAGED_CARE_BILLER'`. Combined with the Medicare index
above via a single composite partial index on
`(agency_assignment_id, coverage_role) WHERE status = 'ACTIVE' AND
coverage_role IN ('MEDICARE_BILLER', 'MEDICAID_MANAGED_CARE_BILLER')`
— one index enforces both roles' "at most one active" rule
simultaneously while keeping them independently queryable (this
answers Checklist Item / prior point 16, see 21.7).

**Active Backup assignment uniqueness.** Partial unique index on
`(agency_assignment_id, backs_up_role) WHERE status = 'ACTIVE' AND
coverage_role = 'BACKUP'` — at most one active backup per backed-up
role per agency (a Medicare backup and a Medi-Cal backup can coexist;
two simultaneous active Medicare backups cannot).

**Overlapping assignment rules.** Database-level uniqueness indexes
above only constrain *currently active* rows; they do not prevent two
historical (non-active) rows from having overlapping
`effective_start_at`/`effective_end_at` windows. Full date-range
exclusion would require a PostgreSQL `EXCLUDE USING gist` constraint
(needs the `btree_gist` extension) — no existing model in this
codebase uses that pattern (confirmed via review of all `__table_args__`
blocks read in this discovery), so introducing it here would be a new
convention. This addendum recommends **application/service-layer
overlap validation** at write time (reject a new row whose
`[effective_start_at, effective_end_at)` window intersects an existing
row for the same `(agency_assignment_id, coverage_role[, backs_up_role])`
discriminator) as the consistent-with-existing-codebase approach, and
flags the Postgres exclusion-constraint approach as an optional
future hardening step requiring separate approval (it is not assumed
here).

**Duplicate assignment prevention (backup ≠ primary).** Enforced at
the service layer, not the database: before activating a `BACKUP` row
with a given `backs_up_role`, the service must check that its `user_id`
does not equal the `user_id` of the currently `ACTIVE` row with
`coverage_role = backs_up_role` for the same `agency_assignment_id`.
This cannot be expressed as a simple `CHECK` constraint (it requires
comparing across rows), so it is documented here as a required service
invariant, enforced identically at every write path (direct API call,
bulk import, or admin action) — not just the primary UI form.

**Assignment replacement behavior.** Replacing an assignment (e.g. a
new Medicare Biller) is always two writes in one transaction: (1) the
currently `ACTIVE` row for that discriminator is updated to
`status = 'INACTIVE'`, `effective_end_at = now()`; (2) a new row is
inserted with `status = 'ACTIVE'`, `effective_start_at = now()`. Both
writes happen inside the same database transaction as the audit event
insert (Section 21.9), so a failed audit write rolls back the
assignment change — audit and assignment state can never diverge.

### 21.6 Backup Coverage Section

**Backup responsibility scope.** Stored as `backs_up_role` on the
`billing_agency_coverage_assignments` row itself (Section 21.2/21.3) —
not a separate table. A backup row is never ambiguous about what it
backs up.

**Medicare backup rules.** A `BACKUP` row with `backs_up_role =
'MEDICARE_BILLER'` covers only Medicare responsibilities for that
agency; it must not be treated as covering Medi-Cal/Managed Care.

**Medi-Cal backup rules.** A `BACKUP` row with `backs_up_role =
'MEDICAID_MANAGED_CARE_BILLER'` covers only that responsibility.

**Managed Care backup rules.** Managed Care is included under the
`MEDICAID_MANAGED_CARE_BILLER` discriminator per the approved spec's
own grouping ("Medi-Cal / Managed Care Biller" is a single named role
throughout every locked document reviewed) — there is no separate
Managed Care discriminator value; this is a direct, intentional
consequence of the spec's own vocabulary, not a discovery gap.

**Backup Missing handling.** Computed, not stored: if no `ACTIVE` row
exists with `coverage_role = 'BACKUP'` and a given `backs_up_role` for
an agency, the Agency Coverage Matrix/Expanded Agency Detail must
render "Backup Missing" for that responsibility — there is no
`BACKUP_MISSING` row or flag; absence of a row *is* the missing state,
consistent with "Coverage must be determined from assignment records"
(Section 18 rule).

**Partial Coverage derivation** / **Coverage Gap derivation** — see
21.7.

**Backup cannot equal primary assignment — documented.** See the
"Duplicate assignment prevention" rule in 21.5; this is the same rule
restated for this section's checklist item.

### 21.7 Coverage Status Derivation

Coverage Status remains a **computed, non-stored value** (per the
Section 18 rule "Coverage must be determined from assignment
records"), derived at read time from the set of `ACTIVE` rows in
`billing_agency_coverage_assignments` for a given `agency_assignment_id`:

- **Fully Covered:** an `ACTIVE` `MEDICARE_BILLER` row exists (if
  Medicare billing applies to this agency's configuration), an
  `ACTIVE` `MEDICAID_MANAGED_CARE_BILLER` row exists (if applicable),
  and the required backup policy is satisfied (an `ACTIVE` `BACKUP`
  row exists for each backed-up role the org's policy requires).
- **Partial Coverage:** all required primary roles (`MEDICARE_BILLER`/
  `MEDICAID_MANAGED_CARE_BILLER`, as applicable) have an `ACTIVE` row,
  but at least one required `BACKUP` row is missing.
- **Coverage Gap:** a required primary role has no `ACTIVE` row at all
  (no effective responsible biller exists for applicable work).
- **Temporary Coverage / Reassignment Pending:** derived from
  assignment metadata not yet fully specified by the approved spec
  (e.g. a short effective window, or a pending replacement already
  scheduled) — flagged as an **open design question** for the
  implementation phase, since the current schema does not yet carry an
  explicit "temporary" or "pending reassignment" flag; adding one
  (e.g. an `is_temporary` boolean or a `PENDING` status value) is a
  candidate but not decided here.
- **Suspended / Inactive:** derived from the parent
  `billing_provider_agency_assignments.relationship_status` (the
  org-to-agency relationship itself, not the individual coverage
  rows) — if the org-to-agency assignment is `SUSPENDED` or
  `TERMINATED`, Coverage Status for that agency is `Suspended` /
  `Inactive` regardless of the underlying coverage rows, per the
  Section 18 rule "Do not treat inactive or suspended agencies as
  active coverage gaps."

**Derivation source verified.** All of the above reads exclusively
from `billing_provider_agency_assignments.relationship_status` and
`billing_agency_coverage_assignments` rows — no UI label, cache, or
denormalized "coverage_status" column is proposed; this avoids a
second source of truth that could drift from the underlying
assignment data, consistent with the spec's explicit prohibition ("Do
not derive coverage solely from UI labels").

### 21.8 Medicare / Medi-Cal Separation

**Medicare / Medi-Cal / Managed Care assignments remain separate** —
guaranteed structurally, not just by convention: they are different
`coverage_role` enum values in the same table, each independently
constrained by its own partial unique index (Section 21.5), so a
Medicare assignment can never overwrite or be confused with a Medi-Cal
one at the schema level.

**Query strategy.** Both the Agency Coverage Matrix (Section 18) and
Expanded Agency Detail (Section 20) query
`billing_agency_coverage_assignments WHERE agency_assignment_id = ?
AND status = 'ACTIVE'` and group the result set by `coverage_role` in
the application layer — a single query returns all four roles for an
agency, already separated by the `coverage_role` column, with no risk
of the two billing types being merged.

**Reporting strategy.** The Open Claims Summary (Section 20.2)
similarly groups by claim category once that column exists — a
separate concern from coverage-role separation, tracked independently
in Section 20.2/20.8.

**Coverage calculation, Export behavior, UI behavior — verified.**
All three consume the same `coverage_role`-discriminated query result;
none of them introduce a parallel or simplified "Primary Biller"
concept, per the spec's explicit prohibition ("Do not replace both
assignments with one generic Primary Biller").

### 21.9 Assignment History (Audit Section)

**`billing_agency_coverage_audit_events`** (new table, modeled
structurally on `FacilityPaymentAuditLog`, per Sections 18.18/20.5):

| Column | Notes |
|---|---|
| `id` | UUID PK |
| `tenant_id` | FK → `tenants.id`, denormalized, indexed |
| `billing_provider_organization_id` | FK → `billing_provider_organizations.id`, indexed |
| `entity_type` | `CheckConstraint`-enforced: `{'TEAM', 'TEAM_MEMBERSHIP', 'TEAM_SUPERVISOR_ASSIGNMENT', 'AGENCY_TEAM_ASSIGNMENT', 'AGENCY_COVERAGE_ASSIGNMENT'}` |
| `entity_id` | UUID of the affected row, indexed |
| `action` | e.g. `ASSIGNMENT_CREATED`, `ASSIGNMENT_REPLACED`, `ASSIGNMENT_ENDED`, `BACKUP_ASSIGNED`, `BACKUP_SCOPE_CHANGED`, `COVERAGE_STATUS_RECALCULATED` (recalculation events are logged for traceability even though status itself is computed, not stored) |
| `affected_user_id` | FK → `users.id`, SET NULL — the user the assignment is about |
| `actor_user_id` | FK → `users.id`, SET NULL — who made the change |
| `actor_role` | string snapshot of the actor's role at the time of the action |
| `previous_state` | JSON/text snapshot of the row before the change |
| `new_state` | JSON/text snapshot of the row after the change |
| `reason` | nullable text |
| `correlation_id` | UUID, nullable, ties together multi-row transactions (e.g. an end+create replacement pair share one correlation ID) |
| `created_at` | server default `now()` |

**Assignment Create / Update / Replace / Remove — all audited.** Every
write path in Section 21.5 (create, replace, end) inserts exactly one
audit event in the same transaction as the row-level change (never a
separate, best-effort write).

**Backup Coverage Change / Coverage Status Change — audited.** Backup
changes use `action = 'BACKUP_ASSIGNED'` / `'BACKUP_SCOPE_CHANGED'`;
coverage-status recalculation is logged (`action =
'COVERAGE_STATUS_RECALCULATED'`) even though the status value itself
is never persisted, so that "why did coverage status change" remains
traceable via the underlying assignment-row audit trail without
needing a separate stored status history.

**Export — audited.** See Section 21.10.

**Access Request — audited.** Handled by the existing/planned
Authorization Failure "Request Access" flow (Section 18/20's Role-
Based Scope and Authorization Failure requirements) — this addendum
does not introduce a new table for access requests; it is scoped for
the implementation phase alongside the broader Access Scope work
(Section 18.17), using the same `billing_agency_coverage_audit_events`
table with `entity_type` extended to include an `ACCESS_REQUEST` value
if a dedicated request record is not otherwise required — this exact
mechanism is flagged as an implementation-phase decision, not locked
here.

**Actor / Timestamp / Correlation ID — preserved** on every event, per
the column list above.

### 21.10 Export Audit

**`billing_agency_coverage_export_events`** (new table, modeled
structurally on `ClaimExportLog`, per Sections 18.19/20.6):

| Column | Notes |
|---|---|
| `id` | UUID PK |
| `tenant_id` | FK → `tenants.id`, nullable (null = organization-wide export spanning multiple agencies) |
| `billing_provider_organization_id` | FK → `billing_provider_organizations.id`, required |
| `exported_by_user_id` | FK → `users.id`, SET NULL |
| `agency_scope` | nullable — the specific `agency_assignment_id` if a single-agency export (Expanded Agency Detail's "Export Detail"), null for the full matrix export |
| `filters` | JSON snapshot of applied filters at export time |
| `row_count` | integer |
| `result` | `CheckConstraint`-enforced: `{'SUCCESS', 'FAILED'}` |
| `correlation_id` | UUID |
| `created_at` | server default `now()` |

### 21.11 SecureInbox Boundary Section

- No message, conversation, channel, thread, or attachment schema is
  introduced by any table in this addendum.
- The SecureInbox Routing Preview (Section 18.20) remains a read-only
  query over `billing_agency_team_assignments` (for Team Leader/
  Supervisor routing) and `billing_agency_coverage_assignments` (for
  Medicare/Medi-Cal/Backup routing) — no new SecureInbox-specific
  table is created or required.
- Out-of-scope status is retained exactly as locked in
  `docs/communications/COMMUNICATIONS_DISCOVERY_REPORT.md` — this
  addendum does not reopen or modify that document's conclusions.

### 21.12 DDE Dependency Section

- No DDE credential storage, DDE credential display, or DDE-related
  migration is introduced by any table in this addendum.
- Individual DDE Authorization Status (Section 18.15) remains a
  blocked, external dependency on the not-yet-built DDE entities
  referenced in the main handoff document's Section 9 — nothing in
  this schema design changes that dependency or attempts to satisfy it
  early.
- DDE authorization status is explicitly **not** a field on
  `billing_agency_coverage_assignments` or any other table in this
  addendum — coverage assignment (who does the billing work) and DDE
  authorization (whether that person is technically authorized to use
  DDE for a given payer/tenant) are kept as separate concerns, exactly
  as the approved spec requires ("DDE authorization does not belong to
  ... a team... Do not infer or display overall hospice compliance
  from billing assignments").

### 21.13 Implementation Blockers Status

Per the required checklist, the following are now resolved at the
design-documentation level (not implemented):
- Discriminator model: defined (21.2).
- Foreign keys: defined (21.4).
- Active-assignment rules: defined (21.5).
- Backup scope: defined (21.6).
- Coverage logic: defined (21.7), with one explicitly flagged open
  question (Temporary Coverage / Reassignment Pending derivation).
- Medicare/Medi-Cal separation: defined (21.8).
- Assignment history: defined (21.1/21.9).
- Audit behavior: defined (21.9/21.10).
- SecureInbox boundary: defined (21.11), unchanged from the locked
  Communications Discovery Report.
- DDE dependency: defined (21.12), remains blocked as an external
  dependency, not resolved by this schema.

**No schema, migration, API, or UI has been created.** This section is
a reviewable design proposal only. Implementation remains blocked
pending explicit user authorization to proceed past discovery/design.

---

## SECTION 22 — BACKUP RESPONSIBILITY SCOPE DESIGN NOTE

STATUS: SCHEMA DESIGN DOCUMENTED — STILL DISCOVERY/DESIGN ONLY. NO
SCHEMA, MIGRATION, API, OR UI HAS BEEN CREATED. IMPLEMENTATION REMAINS
BLOCKED.

This note expands Section 21.2/21.6's `backs_up_role` field into a
complete design covering allowed values, multi-scope behavior,
overlap rules, and its role in coverage-status/backup-missing
derivation.

### 22.1 Allowed Scope Values

`backs_up_role` is a `CheckConstraint`-enforced column on
`billing_agency_coverage_assignments`, populated only when
`coverage_role = 'BACKUP'` (nullable and unused otherwise). Allowed
values are exactly the two backable primary roles already defined in
Section 21.2:

| Value | Meaning |
|---|---|
| `MEDICARE_BILLER` | This backup row stands in for the agency's Medicare Biller only |
| `MEDICAID_MANAGED_CARE_BILLER` | This backup row stands in for the agency's Medi-Cal / Managed Care Biller only |

No `ALL`, `BOTH`, or combined value is permitted. `SPECIALIST` and
`BACKUP` itself are not valid `backs_up_role` values — a backup always
stands in for one of the two named primary billing roles, never for
another backup and never for a specialist assignment, since the
approved spec scopes backup coverage strictly to "required primary
billing roles."

### 22.2 Multi-Scope Behavior

A single person may serve as backup for more than one responsibility,
but this is modeled as **multiple rows, one per scope** — never a
single row with a multi-value scope field. If Jennifer Liu backs up
both Medicare and Medi-Cal for the same agency, that is two rows:

1. `coverage_role = 'BACKUP'`, `backs_up_role = 'MEDICARE_BILLER'`,
   `user_id = Jennifer Liu`
2. `coverage_role = 'BACKUP'`, `backs_up_role =
   'MEDICAID_MANAGED_CARE_BILLER'`, `user_id = Jennifer Liu`

**Reason:** keeping scope single-valued per row means every downstream
consumer (Coverage Assessment, Open Claims Summary, Export, Recent
Assignment Activity, the future SecureInbox Routing Preview) can
always answer "who backs up X" with one unambiguous, indexable lookup
(`WHERE backs_up_role = ? AND status = 'ACTIVE'`), with no need to
parse or contain-check a multi-value field. It also lets each scope's
backup be ended, replaced, or reassigned independently — replacing the
Medicare backup does not require touching the Medi-Cal backup row.
This directly satisfies the approved spec's requirement that "Do not
imply that a Medicare-only backup also covers Medi-Cal or Managed
Care" at the schema level, not just in UI copy.

### 22.3 Overlapping Scope Rules

- **Within the same scope:** at most one `ACTIVE` `BACKUP` row per
  `(agency_assignment_id, backs_up_role)` pair — enforced by the
  partial unique index already defined in Section 21.5
  (`billing_agency_coverage_assignments (agency_assignment_id,
  backs_up_role) WHERE status = 'ACTIVE' AND coverage_role =
  'BACKUP'`). Two people cannot simultaneously be the active Medicare
  backup for the same agency.
- **Across different scopes:** no conflict — `MEDICARE_BILLER` and
  `MEDICAID_MANAGED_CARE_BILLER` backup rows for the same agency are
  independent rows with independent discriminator values and do not
  share a uniqueness constraint with each other, so both can be
  `ACTIVE` at once (per 22.2).
- **Backup vs. primary (cross-discriminator overlap):** a `BACKUP` row
  with `backs_up_role = X` must not share the same `user_id` as the
  currently `ACTIVE` row with `coverage_role = X` for the same
  `agency_assignment_id` — this is the same service-layer invariant
  already documented in Section 21.5 ("Duplicate assignment
  prevention"), restated here as it directly governs backup scope: a
  Medicare backup can never be the same individual as the active
  Medicare Biller for that agency, checked at every write path, not
  just the UI form.
- **Historical (non-active) overlap:** as with all other assignment
  rows (Section 21.5), historical date-range overlap across ended
  `BACKUP` rows for the same scope is prevented at the service layer
  at write time, not by a database exclusion constraint (consistent
  with the rest of this schema's overlap-handling approach — no
  Postgres `EXCLUDE USING gist` constraint is introduced).

### 22.4 Coverage-Status Derivation (Backup-Specific)

Extending Section 21.7's Coverage Status rules with the exact backup
inputs:

- For **each** backable role that applies to the agency (Medicare,
  Medi-Cal/Managed Care — determined by the agency's configured
  billing responsibilities, not assumed to always be both), coverage
  derivation independently checks:
  1. Does an `ACTIVE` primary row exist for that role
     (`coverage_role = 'MEDICARE_BILLER'` or
     `'MEDICAID_MANAGED_CARE_BILLER'`)?
  2. Does an `ACTIVE` `BACKUP` row exist with `backs_up_role` equal to
     that same role?
- **Fully Covered** requires both (1) and (2) true for every
  applicable role.
- **Partial Coverage** is the specific case where (1) is true for all
  applicable roles but (2) is false for one or more of them — e.g. the
  canonical example already locked in the Expanded Agency Detail spec:
  "Medicare backup contact is assigned. Medi-Cal backup is not
  currently assigned" is exactly "(1) true for both roles, (2) true
  for Medicare only" — Partial Coverage, not Fully Covered.
- **Coverage Gap** is reserved for a missing *primary* ((1) false for
  any applicable role) — a missing backup alone never produces
  Coverage Gap, only Partial Coverage, per the spec's own distinction
  between the two statuses.

### 22.5 Backup Missing Derivation

"Backup Missing" is a **computed UI label, not a stored value**,
derived per role, independently:

- For a given `agency_assignment_id` and a given applicable
  `backs_up_role`, if no `ACTIVE` `BACKUP` row exists with that
  `backs_up_role`, the UI renders "Backup Missing" **scoped to that
  specific role** (e.g. "Medi-Cal backup not currently assigned"), not
  a blanket "Backup Missing" that could be misread as applying to both
  roles.
- Backup Missing for any applicable role always downgrades Coverage
  Status from Fully Covered to Partial Coverage (per 22.4) — it never
  independently produces Coverage Gap.
- Backup Missing is computed identically wherever coverage is
  displayed — Agency Coverage Matrix (Section 18), Expanded Agency
  Detail (Section 20), and Export output (Sections 18.19/20.6/21.10) —
  all three read the same absence-of-row condition; none of them
  caches or duplicates a "backup missing" flag anywhere.

### 22.6 Scope Limitation vs. Future Extensibility

This is a deliberate, intentional limitation, not an oversight:

- **Current scope is closed, not open-ended.** `backs_up_role` is
  restricted by a `CheckConstraint` to exactly the two values in 22.1
  (`MEDICARE_BILLER`, `MEDICAID_MANAGED_CARE_BILLER`) because those are
  the only two roles the approved spec defines as "required primary
  billing roles" needing mandatory backup coverage. `SPECIALIST`
  assignments (Section 21.2/21.6) are explicitly excluded from backup
  scope in this design — the approved spec treats Additional
  Specialist as a supplementary capability, not a required-coverage
  role, so it has no backup-coverage requirement to satisfy.
- **No backup scope is defined for Team Leader or Billing Supervisor.**
  Those are team-scope relationships (Section 21.1/21.3), not
  agency-coverage rows, and are out of scope for `backs_up_role`
  entirely — this design does not model backup coverage for team
  leadership roles, only for the two primary billing roles.
- **Extensibility mechanism, if ever required, is additive, not
  structural.** Because `backs_up_role` is a `CheckConstraint` on a
  string/enum column (not a hard-coded application-layer switch), a
  future backable role (e.g. a specialist role later promoted to
  "required primary" status) would be added by widening the
  constraint's allowed value list and adding the corresponding
  discriminator handling — the same pattern already used for
  `coverage_role` and `specialist_type` (Section 21.2). This requires
  a migration when it happens; it is **not pre-built, not enabled, and
  not implied to exist today**. No specialist backup scope, generic
  "other" scope, or open string value is included in the current
  design.
- **Decision:** backup scope is intentionally limited to the two named
  roles only. No specialist backup scope is authorized, implemented,
  or planned as part of this schema design. Any future need for
  specialist backup coverage is a distinct, separately-authorized
  design/migration decision, not something this design silently
  accommodates.

---

## SECTION 23 — ORGANIZATION & TEAMS PAGE-LEVEL DISCOVERY ADDENDUM

STATUS: DISCOVERY VALIDATION COMPLETE — DESIGN MAPPING ONLY. NO
SCHEMA, MIGRATION, API, OR UI HAS BEEN CREATED. This addendum responds
to the approved, locked, Figma-approved "Organization & Teams"
handoff (the first of the three Billing Organization pages, alongside
Agency Coverage & Workload — Sections 18-22 — and the not-yet-detailed
Access Administration page). Per this document's discovery-first
convention, the "implementation planning" requested is captured here
as REUSE/EXTEND/CREATE mapping; no code, schema, or migration file has
been created. If the user intends to authorize actual schema/migration
work now, that authorization should be given explicitly and separately
from this discovery step, consistent with every prior gate in this
report.

### 23.1 Organization Metrics — REUSE (models) + CREATE (aggregation)

- **Existing Models:** `BillingProviderOrganization`,
  `BillingProviderOrganizationMembership`,
  `BillingProviderAgencyAssignment` (all REUSE, per Discovery Area 1-3
  and Section 18).
- **Decision:** REUSE all three existing models as the source data;
  CREATE a new read-only aggregation/reporting service to compute
  organization-level metrics (headcount, team count, agency count,
  coverage completeness) — no existing service already produces this
  rollup.
- **Migration Required:** No.

### 23.2 Administrative Hierarchy — CREATE (new structure, distinct from Operational Reporting Chain)

- **Existing Models:** `BillingProviderOrganizationMembership` has a
  `role` field (org-level role) but **no** `reports_to`/manager
  relationship or hierarchy depth field — confirmed via the same
  model read performed for Section 18.1.
- **Decision:** CREATE. The approved architecture rule ("Administrative
  authority and operational authority remain separate") means the
  Company President → Billing Manager → Supervisor → Team Leader →
  Staff administrative chain **cannot** be derived from the Section 21
  team-scope tables (`billing_team_memberships`,
  `billing_team_supervisor_assignments`), because those model
  *operational* team leadership/supervision of agency portfolios, not
  *administrative* reporting-line authority. A new structure is
  required — most likely a `reports_to_membership_id` self-referencing
  foreign key on a new/extended organization-membership-scoped table,
  or a separate `billing_administrative_hierarchy` table — the exact
  shape is an open design decision for the schema-design phase, not
  resolved here.
- **Reason:** conflating the two would violate the locked rule that
  "Billing Administrator is not part of the operational reporting
  chain" — an administrator can exist in the administrative hierarchy
  with no corresponding team-leadership or team-membership row at all.
- **Migration Required:** Yes (new table or new column), not yet
  designed in detail.

### 23.3 Operational Reporting Chain — REUSE (Section 21 team-scope tables)

- **Decision:** REUSE `billing_team_memberships` (role_on_team =
  LEADER for Team Leader) and `billing_team_supervisor_assignments`
  from Section 21 directly — Operational Reporting Chain is exactly
  the Team Leader → Staff structure already designed there. No new
  table required beyond Section 21.
- **Reason:** confirms Section 21's team-scope design was correctly
  separated from agency-coverage rows; this page is the first concrete
  consumer of that separation.
- **Migration Required:** No (beyond Section 21's own tables).

### 23.4 Team Portfolio Summaries — REUSE (Section 21 `billing_agency_team_assignments`) + CREATE (aggregation)

- **Decision:** REUSE `billing_agency_team_assignments` (Section 21) as
  the source of "which agencies does this team cover"; CREATE a
  read-only aggregation for per-team portfolio counts (agency count,
  coverage status distribution). The locked reconciliation rule ("Team
  Alpha and Team Beta totals must reconcile to organization totals")
  is a **query-time invariant** to validate — every
  `billing_agency_team_assignments` row must resolve to exactly one
  team and one org-scoped agency assignment, so team-level sums over
  active rows always equal the organization-level count with no
  separate reconciliation table or job needed.
- **Migration Required:** No (beyond Section 21's own tables).

### 23.5 Team Staffing Tables — REUSE (Section 21 `billing_team_memberships`)

- **Decision:** REUSE directly. Team Staffing Tables (per-team roster
  with role_on_team) is a direct read view over
  `billing_team_memberships`; no new entity needed. The locked rule
  "Team staffing assignments support future Agency Coverage
  relationships" is already satisfied by design — `billing_team_id` on
  `billing_agency_team_assignments` (Section 21) is the join key
  between staffing and coverage.
- **Migration Required:** No (beyond Section 21's own tables).

### 23.6 System Role Definitions — CREATE (informational reference only)

- **Existing Models:** the dormant `Role`/`interfaces` model
  (Discovery Area 4) remains confirmed to have zero live consumers and
  must **not** be revived for this purpose — reviving it would risk
  implying it grants permissions, contradicting the locked rule "Role
  definitions are informational and do not grant permissions."
- **Decision:** CREATE a small, informational-only reference structure
  (e.g. a static list/config or a simple non-permission-bearing lookup
  table) purely for display purposes on this page. It must not be
  wired into `require_permission()`/`has_permission()` (still
  unimplemented placeholders per Discovery Area 4) or any access-control
  path — this stays a documentation/display construct only, per the
  locked rule that operational access derives from "role, capability,
  team assignment, agency assignment, account status, and
  action-specific permission" collectively, not from this reference
  list alone.
- **Migration Required:** Only if implemented as a DB-backed lookup
  table rather than static config — an open, low-stakes implementation
  choice, not resolved here.

### 23.7 Recent Organizational Changes — REUSE (Section 18.18/21.9 audit pattern)

- **Decision:** REUSE the same Audit Event design already recommended
  in Section 18.18 and detailed further in Section 21.9
  (`billing_agency_coverage_audit_events`, modeled on
  `FacilityPaymentAuditLog`) — extended in scope to also capture
  organization/team/membership-level changes (not just agency-coverage
  changes), since the locked rule requires "Recent Organizational
  Changes remain append-only and auditable," which is exactly this
  audit table's existing append-only design. No second, parallel audit
  mechanism should be created.
- **Migration Required:** No (beyond the Section 18.18/21.9 table),
  though the audit table's scope/entity-type coverage may need
  broadening at implementation time to include organization- and
  team-level event types alongside agency-coverage event types.

### 23.8 Architecture Rule Cross-Check

- **"Administrative authority and operational authority remain
  separate"** — satisfied by design: Section 23.2 (administrative) and
  Section 23.3/23.5 (operational) are distinct structures with no
  shared table.
- **"Billing Administrator is not part of the operational reporting
  chain"** — satisfied: an administrator exists only in the Section
  23.2 administrative hierarchy, with no requirement to also appear in
  `billing_team_memberships`.
- **"Team portfolios are the authoritative operational structure"** —
  satisfied: Section 23.4/23.5 read directly from Section 21's
  team-scope tables; no competing operational structure is introduced.
- **"Medicare and Medi-Cal assignments remain separate"** — already
  satisfied by the Section 21/22 discriminated coverage design
  (`coverage_role`, `backs_up_role` as distinct enum values, never
  merged).
- **"Role definitions are informational and do not grant permissions"**
  — satisfied by Section 23.6's explicit non-wiring into the
  permission system.
- **"Operational access continues to derive from role, capability,
  team assignment, agency assignment, account status, and
  action-specific permission"** — consistent with the still-open
  Discovery Area 4 finding that a real permission engine does not yet
  exist; this page does not attempt to build that engine, only to
  display the structures (team assignment, agency assignment) that
  will feed it once built.
- **"Recent Organizational Changes remain append-only and auditable"**
  — satisfied by Section 23.7's reuse of the append-only audit design.

### 23.9 Implementation Boundary Confirmation

Per the locked implementation boundary, this discovery explicitly
confirms none of the following are introduced by this addendum: HR
functionality, payroll functionality, employee performance scoring,
SecureInbox messaging functionality, or any merge of operational and
administrative authority structures (Section 23.2 keeps them
structurally distinct). No such functionality appears in any REUSE/
CREATE decision above.

---

## RELATIONSHIP TO OTHER DOCUMENTS

This report is the required discovery deliverable for the approved
"[Biller Platform] Implement Billing Organization" GitHub issue (module
level), the "Billing Organization → Agency Coverage & Workload"
implementation handoff (page level, Section 18-19 addendum), the
"Billing Organization → Expanded Agency Detail" implementation handoff
(detail-view level, Section 20 addendum), the subsequent Discovery
Addendum Review / Discovery Addendum Verification Checklist requests
(schema-design level, Section 21-22 addenda), and the "Billing
Organization → Organization & Teams" implementation handoff (page
level, Section 23 addendum). It satisfies the six module-level
Discovery Areas, the 20-entity Agency Coverage & Workload mapping
requirement, the Expanded Agency Detail Verify-First Requirement, the
full Discovery Addendum Verification Checklist, and the Organization &
Teams discovery validation requirement. It is independent of, and does
not modify:
- `docs/biller-platform/BILLER_PLATFORM_FINAL_IMPLEMENTATION_HANDOFF.md`
  (the canonical Biller Platform spec; Billing Organization, including
  Agency Coverage & Workload and Expanded Agency Detail, will be added
  there as a new page once this discovery is reviewed).
- `docs/biller-platform/BILLER_PLATFORM_DISCOVERY_REPORT.md` (separate,
  still-outstanding addendum for Pages 4-12 entities).
- `docs/communications/COMMUNICATIONS_DISCOVERY_REPORT.md` (APPROVED /
  LOCKED — SecureInbox remains future functionality; Section 18.20
  above confirms the SecureInbox Routing Preview stays display-only,
  per that document's locked Section 9 sequencing).
- `docs/biller-platform/BILLER_PLATFORM_IMPLEMENTATION_VERIFICATION.md`
  — both the Agency Coverage & Workload handoff and the Expanded
  Agency Detail handoff separately require new verification sections
  in that document ("Agency Coverage & Workload Verification" and
  "Expanded Agency Detail Verification") once implementation (not
  discovery) is authorized and complete; not created in this pass.

No schema, migration, model, service, or route changes were made
while producing this report or either addendum.

---

## CHANGE LOG

| Date | Change |
|---|---|
| 2026-09-17 | Document created. Full repository discovery completed for all six required Discovery Areas (Identity/Users, Teams/Structure, Agencies, Permissions, Escalations, SecureInbox Dependencies) per the approved Billing Organization GitHub issue. Headline finding: a working, production billing-organization system already exists (`BillingProviderOrganization`, `BillingProviderOrganizationMembership`, `BillingProviderAgencyAssignment`, `BillingProviderAgencyServiceScope`), exposed through the SNS Tech Solutions owner platform's Billing/Licensing admin page — classified REUSE for the org record and org-to-agency assignment layer. No Team, per-user Agency Coverage, billing-specific Capability Matrix, Escalation Chain, or Workload Metric structures exist anywhere — all classified CREATE. The `require_permission`/`has_permission` functions in `app/core/permissions.py` are confirmed unimplemented placeholders, not a usable fine-grained permission engine. The dormant `Role`/`interfaces` model is confirmed to have zero live consumers and must not be revived. A generic `audit_event()` service is confirmed reusable for the new module's audit-trail requirement. Documentation only; no schema, migrations, tables, models, or routes created or changed. |
| 2026-09-18 | Added Section 18-19: Agency Coverage & Workload page-level discovery addendum, per the approved "Billing Organization → Agency Coverage & Workload" implementation handoff. Mapped all 20 required entities (Billing Organization, Billing Organization Membership, Billing Team, Team Membership, Team Leader Assignment, Billing Supervisor Assignment, Agency Assignment, Medicare Billing Assignment, Medi-Cal/Managed Care Assignment, Backup Coverage Assignment, Additional Specialist Assignment, Assignment Status, Assignment Effective Period, Staff Capability, Individual DDE Authorization Status, Workload Metrics, Access Scope, Audit Event, Export Event, Future SecureInbox Routing Relationship) using the required detailed template (Existing Model/Table/Relationships/Fields/Constraints/Indexes/APIs/UI/Decision/Reason/Migration Required/Files Affected/Verification Evidence). **Correction to the 2026-09-17 entry above:** `backend/app/billing/audit_store.py` was re-verified and found to be an in-memory Python list scoped to patient/billing-cycle events, not a durable, org/agency-scoped audit table — it is NOT a valid reuse target for this module's audit requirement (updated the Classification Summary table's `AssignmentAudit` row accordingly); the correct structural precedent is the database-backed `FacilityPaymentAuditLog`. Also identified `ClaimExportLog` as the correct structural precedent for the new Export Event requirement. Recommended (not locked) that the four coverage-role assignment types (Medicare/Medi-Cal/Backup/Specialist) be modeled as one discriminated `billing_agency_coverage_assignments` table referencing `billing_provider_agency_assignments.id`, following the existing `status` + `effective_start_at`/`effective_end_at` pattern already proven on `BillingProviderOrganizationMembership` and `BillingProviderAgencyAssignment`. Documentation only; no schema, migrations, models, services, or routes created or changed. Page-level implementation (schema, migrations, APIs, UI) for Agency Coverage & Workload remains blocked pending user review of this addendum. |
| 2026-09-18 | Added Section 20: Expanded Agency Detail discovery addendum, per the approved "Billing Organization → Expanded Agency Detail" implementation handoff (a detail view reached from Agency Coverage & Workload → Agency Coverage Matrix → Select Agency, not a new top-level module). Confirmed no wholly new tables are required beyond Section 18's recommended schema; documented two delta findings: (1) the existing `Claim` model (`backend/app/billing/models/claim.py`) is REUSE for raw Open Claims counts, but its `payer_name` field is free text with no Medicare Hospice/Medi-Cal/Managed Care classification — a new `claim_category` column (CREATE) is an open decision for the Open Claims Summary breakdown; (2) a `responsibility_scope` field must be added (CREATE) to the Section 18.8-18.11 coverage-assignment table so backup assignments can declare which specific role they stand in for. Confirmed "Recent Assignment Activity" and "Export Detail" on this screen reuse the same Section 18.18 (Audit Event) and Section 18.19 (Export Event) tables/patterns rather than introducing parallel history or export mechanisms — flagged and corrected an in-progress drafting error where the "Relationship to Other Documents" heading was inadvertently dropped during the previous two edits; restored. Documentation only; no schema, migrations, models, services, or routes created or changed. Page-level implementation for Expanded Agency Detail remains blocked pending user review of this addendum. |
| 2026-09-18 | Added Section 21: Agency Coverage Schema-Design Addendum, responding to the required Discovery Addendum Verification Checklist. Expanded the single-discriminated-table recommendation into a concrete, reviewable design: Team Leader and Billing Supervisor are modeled as team-scope relationships (new `billing_team_memberships`/`billing_team_supervisor_assignments` tables), not agency-coverage rows, because their authority spans a team's whole portfolio rather than one agency; the Agency Coverage Matrix's "Team Leader" column is a derived join, not a stored per-agency fact. Defined the full `billing_agency_coverage_assignments` design (coverage_role discriminator, backs_up_role, specialist_type, status, effective window), a new `billing_agency_team_assignments` table (which team covers which agency), and two new audit/export tables (`billing_agency_coverage_audit_events` modeled on `FacilityPaymentAuditLog`, `billing_agency_coverage_export_events` modeled on `ClaimExportLog`). Documented required foreign keys, indexes, partial unique constraints (active Team Leader/Supervisor/Medicare/Medi-Cal/Backup uniqueness), overlap-prevention approach (service-layer validation, not a Postgres exclusion constraint), replacement/supersession behavior (two-write transaction: end old row + insert new row + one audit event, never an in-place update or physical delete), append-only history, Medicare/Medi-Cal separation guarantees, and coverage-status derivation logic. Flagged one open question (Temporary Coverage / Reassignment Pending derivation has no schema field yet). Documentation/design only; no schema, migrations, models, services, or routes created or changed. Implementation remains blocked pending user authorization. |
| 2026-09-18 | Added Section 22: Backup Responsibility Scope Design Note, per the Discovery Addendum Review request for one additional design note before Schema Design Review authorization. Documents allowed `backs_up_role` values (`MEDICARE_BILLER`, `MEDICAID_MANAGED_CARE_BILLER` only — no combined/ALL value), multi-scope behavior (one row per backed-up responsibility rather than a multi-value field, so a single backup covering two roles is two independent rows), overlapping-scope rules (partial unique index per role prevents two active backups for the same role; independent roles do not conflict with each other; a backup can never share a user with the active primary it backs up), coverage-status derivation extended per-role (Partial Coverage = all primaries filled but one or more required backups missing; Coverage Gap is reserved for missing primaries only, never for a missing backup alone), and Backup Missing derivation (a computed, per-role UI label reading absence of an active `BACKUP` row with that `backs_up_role`, never a stored flag, computed identically across the matrix, detail view, and export). Documentation/design only; no schema, migrations, models, services, or routes created or changed. Implementation remains blocked pending user authorization. |
| 2026-09-18 | Added Section 22.6: Scope Limitation vs. Future Extensibility clarification, per the Discovery Addendum Review's requested clarification before Schema Design Review authorization. Confirms backup scope is intentionally, deliberately closed to the two named roles (`MEDICARE_BILLER`, `MEDICAID_MANAGED_CARE_BILLER`) only — `SPECIALIST` assignments are explicitly out of backup scope because the approved spec treats them as supplementary capability, not a required-coverage role; Team Leader/Billing Supervisor are also out of scope because they are team-scope relationships, not agency-coverage rows. Documents that any future backable role would require widening the `backs_up_role` CheckConstraint plus a new migration — this is an additive future mechanism, not something pre-built, enabled, or implied by the current design. No specialist backup scope, generic "other" scope, or open string value exists in this schema design today. Documentation/design only; no schema, migrations, models, services, or routes created or changed. Schema Design Review authorized by the user following this clarification; migration design, API design, and UI implementation remain explicitly blocked. |
| 2026-09-18 | Added Section 20.9: Claim Category Enum — Locked Value List. The user supplied a 12-value flat enum (`MEDICARE_HOSPICE`, `MEDICAID`, `MEDI_CAL`, `MEDICARE_ADVANTAGE_HMO`, `MEDICARE_ADVANTAGE_PPO`, `COMMERCIAL_HMO`, `COMMERCIAL_PPO`, `COMMERCIAL_POS`, `TRICARE`, `VETERANS_AFFAIRS`, `PRIVATE_PAY`, `OTHER`), resolving the Section 20.2 open question about what values a new `claim_category` column on `Claim` would use. Documented that this enum is a separate concept from the Section 18/21/22 `coverage_role` discriminator (staff-role assignment vs. per-claim payer classification) and that any category-to-responsible-role display mapping is an implementation-phase decision, not locked here. Explicitly noted the value list being locked does NOT itself authorize column creation — migration, backfill, and mapping work remain gated behind Migration Design authorization, which has not been granted. Documentation only; no schema, migrations, models, services, or routes created or changed. |
| 2026-09-18 | Added Section 23: Organization & Teams page-level discovery addendum, per the approved, locked, Figma-approved "Billing Organization → Organization & Teams" implementation handoff (the first of the three Billing Organization pages). Mapped all seven approved sections (Organization Metrics, Administrative Hierarchy, Operational Reporting Chain, Team Portfolio Summaries, Team Staffing Tables, System Role Definitions, Recent Organizational Changes): confirmed Operational Reporting Chain, Team Portfolio Summaries, and Team Staffing Tables all REUSE the Section 21 team-scope tables (`billing_team_memberships`, `billing_team_supervisor_assignments`, `billing_agency_team_assignments`) directly, with no new tables required; confirmed Recent Organizational Changes REUSEs the Section 18.18/21.9 append-only audit design (scope broadened to org/team-level events). Identified Administrative Hierarchy as CREATE — a new structure distinct from the Section 21 operational team-scope tables, since the locked rule "Administrative authority and operational authority remain separate" and "Billing Administrator is not part of the operational reporting chain" cannot be satisfied by reusing those tables; exact shape (self-referencing FK vs. separate table) is an open schema-design decision, not resolved here. Identified System Role Definitions as CREATE but explicitly informational-only, not wired into the permission system, consistent with the locked rule that role definitions do not grant permissions and with Discovery Area 4's finding that `require_permission`/`has_permission` remain unimplemented placeholders. Cross-checked all locked architecture rules and the implementation boundary (no HR/payroll/performance-scoring/SecureInbox functionality introduced). Documentation/discovery-validation only; no schema, migrations, models, services, or routes created or changed. Actual schema/migration/code implementation for Organization & Teams remains a separate, not-yet-taken step pending explicit authorization to write code, consistent with this report's established discovery-first gating for every other Billing Organization page. |
| 2026-09-18 | Reconciled the Section 20.9 claim_category enum count per the Claim Category Enum Review. Added row numbering (1-12) to the locked value table and an explicit reconciliation note: the list contains exactly 12 distinct enum values, breaking down as 11 substantive named payer categories (`MEDICARE_HOSPICE` through `PRIVATE_PAY`) plus 1 fallback value (`OTHER`); no value was added, removed, or renamed. The likely source of the "11 visible values" observation is reading only the 11 named-category rows without the `OTHER` fallback row — `OTHER` is confirmed to be a full, CheckConstraint-enforced enum value, not a null/absent state, per the existing Section 20.9 design note. Final locked list is unchanged from the original submission. Documentation only; no schema, migrations, models, services, or routes created or changed. Per the user's gate, Schema Design Review is now approved following this reconciliation; migration design, API design, and UI implementation remain explicitly blocked. |
