==================================================
GLOBAL IMPLEMENTATION DIRECTIVE
==================================================

STATUS:

APPROVED
LOCKED
IMPLEMENTATION AUTHORIZED

The approved Figma designs are the visual authority.

These specifications are the functional, workflow, data, security, and acceptance authority.

Do not redesign either page.

Do not substitute generic cards, mock workflows, invented calculations, or unrelated billing features.

Do not add Owner Platform functionality.

Do not remove approved DDE visibility.

Do not expose unassigned tenants.

==================================================
VERIFY-FIRST REQUIREMENT
==================================================

Before editing code:

1. Inspect the existing Biller Platform routes.
2. Inspect the existing page components.
3. Inspect current authorization and assignment logic.
4. Inspect current database models and migrations.
5. Inspect current billing readiness calculations.
6. Inspect current claims, NOE, eligibility, payment, denial, audit, and DDE-related structures.
7. Identify which approved fields already exist.
8. Identify which approved fields require additive implementation.
9. Document exact files and database objects affected.
10. Preserve working functionality.

Do not guess existing model names.

Do not create duplicate models when an authoritative model already exists.

Do not rename existing production-facing models without documented necessity.

Do not use alembic stamp.

Do not create schema drift.

Do not use unsafe automigrations.

Use forward-only, reviewed, additive migrations when schema changes are required.

==================================================
LOCKED BRANDING
==================================================

All Owner Platform and Biller Platform pages belong to:

SNS Tech Solutions

Biller Platform branding must display:

SNS Tech Solutions
Biller Platform

Do not display:

SNS Hospice Solutions
Biller Platform

SNS Hospice Solutions is the tenant product.

Example tenant context:

SNS Hospice Solutions Tenant
Angela Hospice (Training)

==================================================
LOCKED ACCESS PRINCIPLE
==================================================

Visibility follows assignment.

Access follows assignment.

Responsibility follows assignment.

A Biller Platform user may only see tenant agencies assigned to that user or the user's authorized billing group.

A user must not gain access to a tenant merely by modifying:

- URL parameters
- Request payloads
- Query parameters
- Browser storage
- Client state
- API identifiers

Tenant assignment must be enforced server-side on every request.

==================================================
DOCUMENT 1
==================================================

CREATE:

/docs/biller-platform/BILLING_DASHBOARD_IMPLEMENTATION_SPECIFICATION.md

==================================================
SNS TECH SOLUTIONS
BILLER PLATFORM
BILLING DASHBOARD
==================================================

STATUS:

APPROVED
LOCKED
IMPLEMENTATION AUTHORIZED

==================================================
1. PAGE PURPOSE
==================================================

The Billing Dashboard is the revenue operations command center for billing personnel.

It must answer:

1. Where is the money?
2. What revenue is ready?
3. What revenue is blocked?
4. What revenue is at risk?
5. What requires action today?
6. What may be recovered?
7. What affects collections?
8. What affects cash flow?
9. What DDE conditions require attention?

This is not a subscription-management page.

This is not an Owner Platform revenue page.

This is not an agency health analytics page.

==================================================
2. PAGE CONTEXT
==================================================

Platform:

SNS Tech Solutions Biller Platform

Scope:

One currently selected, assigned SNS Hospice Solutions tenant.

The user may switch only among assigned agencies.

Example:

Billing Organization:
North East Billing Center

Assigned Agencies:
- Love & Faith Hospice, Production
- Angela Hospice, Training
- Silva Hospice, Demo

Current Agency:
Angela Hospice, Training

==================================================
3. ROUTE REQUIREMENTS
==================================================

Use the existing Biller Platform route if already authoritative.

If no route exists, use the repository's established routing convention.

Do not create a second competing Billing Dashboard route.

Required routing behavior:

- Route requires authentication.
- Route requires Biller Platform access.
- Route requires selected agency assignment.
- Invalid agency identifiers return access denied or not found without exposing tenant existence.
- Agency switching re-fetches all dashboard information within the new authorized scope.
- No data from the previously selected agency may remain visible after switching.

==================================================
4. AUTHORIZED USER TYPES
==================================================

Supported roles may include:

- Billing Staff
- Billing Manager
- Revenue Cycle Staff
- Collections Staff
- Payment Posting Staff
- Biller Platform Administrator
- Authorized Read-Only Billing Auditor

Role names must follow existing repository authority.

Do not invent parallel role names if equivalent roles already exist.

==================================================
5. PERMISSION MATRIX
==================================================

BILLING STAFF

May:

- View assigned agencies
- View dashboard revenue summaries
- View work queue
- View billing priorities
- View DDE operational status when individually authorized
- Open permitted billing work items
- Record permitted follow-up actions

May not:

- Assign tenants
- Change billing organization assignments
- Change subscription terms
- Change revenue-sharing agreements
- Grant DDE authorization
- View unassigned agencies

--------------------------------------------------

BILLING MANAGER

May perform Billing Staff actions plus:

- Reassign billing work within authorized billing scope
- Review escalation queues
- Review denial recovery
- Review collections results
- Approve actions where existing policy permits
- Export permitted audit logs

--------------------------------------------------

PAYMENT POSTING STAFF

May:

- View assigned payment queues
- Post or reconcile payments where authorized
- View collections and remittance-related information
- Record posting exceptions

May not receive unrelated clinical access.

--------------------------------------------------

READ-ONLY BILLING AUDITOR

May:

- View authorized events, calculations, and histories
- Export permitted audit material

May not:

- Modify operational records
- Submit claims
- Resolve DDE exceptions
- Reassign work

--------------------------------------------------

PLATFORM OWNER

Has governance authority but is not the default operational actor.

The Platform Owner must not be assigned routine daily billing work merely because the Platform Owner has maximum authority.

==================================================
6. MINIMUM NECESSARY DATA RULE
==================================================

Display only billing-relevant information needed to perform the authorized workflow.

Do not expose broad clinical narratives on summary dashboards.

Patient-specific access, when permitted, must be available only through authorized drill-down workflows.

All patient and agency access must be audited.

==================================================
7. REQUIRED DATA MODELS
==================================================

Use existing authoritative models where available.

The following logical entities must be supported.

Names below are conceptual unless matching models already exist.

--------------------------------------------------
7.1 BILLING ORGANIZATION
--------------------------------------------------

Required fields:

- id
- legal_name
- display_name
- status
- created_at
- updated_at

--------------------------------------------------
7.2 BILLING USER MEMBERSHIP
--------------------------------------------------

Required fields:

- id
- user_id
- billing_organization_id
- role
- status
- effective_from
- effective_to
- created_at
- updated_at

--------------------------------------------------
7.3 TENANT BILLING ASSIGNMENT
--------------------------------------------------

Required fields:

- id
- tenant_id
- billing_organization_id
- assignment_status
- billing_model
- effective_from
- effective_to
- assigned_by_user_id
- created_at
- updated_at

Assignment history must be preserved.

An assignment ending must not delete historical billing activity.

--------------------------------------------------
7.4 USER TENANT BILLING ASSIGNMENT
--------------------------------------------------

Required when work is assigned to an individual biller.

Fields:

- id
- user_id
- tenant_id
- billing_organization_id
- assignment_role
- assignment_status
- effective_from
- effective_to
- assigned_by_user_id
- created_at
- updated_at

--------------------------------------------------
7.5 DDE USER PROFILE
--------------------------------------------------

DDE authorization belongs to an individual operating within a billing group.

Required fields:

- id
- user_id
- billing_organization_id
- authorization_status
- authorization_verified_at
- authorization_verified_by
- last_reviewed_at
- effective_from
- effective_to
- status
- created_at
- updated_at

Do not store plaintext DDE passwords.

Do not expose credentials in UI, logs, exports, telemetry, or error messages.

If secure credential storage is later approved, it requires a separate security specification.

--------------------------------------------------
7.6 DDE TENANT AUTHORIZATION
--------------------------------------------------

Required fields:

- id
- dde_user_profile_id
- tenant_id
- status
- effective_from
- effective_to
- verified_at
- verified_by
- created_at
- updated_at

This entity distinguishes:

SNS tenant billing assignment

from

individual DDE authorization for that tenant.

--------------------------------------------------
7.7 BILLING WORK ITEM
--------------------------------------------------

Required fields:

- id
- tenant_id
- patient_id, nullable only when work is not patient-specific
- claim_id, nullable
- category
- status
- priority
- assigned_team
- assigned_user_id, nullable
- due_at, nullable
- revenue_impact
- source_record_type
- source_record_id
- created_at
- updated_at
- resolved_at
- resolution_code
- resolution_note
- version

Supported categories include:

- claim_ready_to_submit
- noe_due
- order_awaiting_signature
- denial_awaiting_action
- eligibility_review
- payment_posting
- dde_response_pending
- dde_eligibility_review
- dde_status_check
- dde_exception_resolution

Use existing enums if authoritative equivalents exist.

--------------------------------------------------
7.8 BILLING REVENUE EVENT
--------------------------------------------------

Required fields:

- id
- tenant_id
- patient_id, nullable
- claim_id, nullable
- event_type
- amount
- currency
- actor_user_id
- source_type
- source_id
- occurred_at
- recorded_at
- correlation_id
- metadata
- immutable_version_reference

Event types include:

- revenue_ready
- revenue_blocked
- revenue_at_risk
- revenue_released
- claim_submitted
- claim_accepted
- claim_paid
- claim_denied
- recovery_identified
- recovery_completed
- payment_posted

Revenue event history must be append-only.

Corrections must create corrective events rather than overwrite history.

--------------------------------------------------
7.9 DDE OPERATIONAL EVENT
--------------------------------------------------

Required fields:

- id
- tenant_id
- patient_id, nullable
- claim_id, nullable
- dde_user_profile_id
- event_type
- status
- revenue_impact
- occurred_at
- resolved_at, nullable
- source_reference
- resolution_code, nullable
- resolution_note, nullable
- correlation_id
- created_at

Supported event types include:

- verification_required
- eligibility_conflict
- status_unknown
- response_pending
- submission_failure
- exception_created
- exception_resolved
- status_reviewed

==================================================
8. DASHBOARD CALCULATION RULES
==================================================

All amounts:

- Must be scoped to the selected authorized tenant.
- Must use one authoritative monetary field.
- Must avoid counting the same claim or revenue event more than once.
- Must exclude voided or superseded amounts according to authoritative event state.
- Must use decimal monetary arithmetic.
- Must not use floating-point calculations.
- Must include an as-of timestamp.

--------------------------------------------------
8.1 READY REVENUE
--------------------------------------------------

Ready Revenue equals the sum of unique billable amounts for items that:

- Have completed required readiness checks
- Have no unresolved blocking condition
- Have not already been submitted
- Have not been paid
- Have not been voided
- Belong to the selected tenant

If an authoritative claim-ready amount does not exist, do not estimate silently.

Display unavailable until calculation inputs are complete.

--------------------------------------------------
8.2 BLOCKED REVENUE
--------------------------------------------------

Blocked Revenue equals the sum of unique billable amounts associated with unresolved blocking conditions.

Examples:

- Missing required certification
- Missing required signature
- Missing required face-to-face documentation
- Unresolved eligibility blocker
- Unresolved NOE blocker
- DDE submission failure
- DDE eligibility conflict that prevents progression

A claim with multiple blockers must be counted once in the total.

Blocking categories may count occurrences separately, but the total blocked revenue must be deduplicated by authoritative claim or billable episode.

--------------------------------------------------
8.3 REVENUE AT RISK
--------------------------------------------------

Revenue At Risk equals unique revenue not completely blocked but exposed to:

- Filing deadlines
- Pending external action
- Expiring eligibility
- NOE timing risk
- Certification timing risk
- DDE response delay
- DDE status uncertainty
- Other approved risk conditions

Blocked revenue and at-risk revenue must not be double-counted in the headline totals unless the UI explicitly labels overlapping amounts.

Default: deduplicate and place the item in the most severe applicable state.

--------------------------------------------------
8.4 PENDING PAYMENTS
--------------------------------------------------

Pending Payments equals accepted or submitted reimbursement amounts awaiting confirmed payment according to current authoritative claim lifecycle state.

Exclude:

- Paid
- Denied without active appeal
- Voided
- Reversed
- Duplicate submissions

--------------------------------------------------
8.5 DENIED REVENUE
--------------------------------------------------

Denied Revenue equals the sum of active denied amounts not yet recovered, reversed, or finally closed.

--------------------------------------------------
8.6 RECOVERY OPPORTUNITIES
--------------------------------------------------

Recovery Opportunities equals denied or underpaid revenue with an active and valid recovery path.

Do not include closed, abandoned, expired, duplicate, or fully recovered items.

--------------------------------------------------
8.7 EXPECTED WEEKLY COLLECTIONS
--------------------------------------------------

Use an existing approved forecasting model if one exists.

If no model exists:

- Do not invent a confidence model.
- Mark forecast as unavailable.
- Implement only after forecast inputs and methodology are approved.

Any displayed forecast must provide:

- Calculation date
- Included claim states
- Confidence or methodology label
- Exclusions

--------------------------------------------------
8.8 DDE EXCEPTIONS
--------------------------------------------------

DDE Exceptions count unresolved DDE operational events for the selected tenant and authorized DDE scope.

DDE Revenue Impact equals the deduplicated sum of affected claim or billable episode amounts.

==================================================
9. REQUIRED UI SECTIONS
==================================================

Implement the approved Figma layout.

Required sections:

1. Executive Revenue Summary
2. Today's Work Queue
3. Billing Priorities
4. Cash Forecast
5. Revenue Pipeline
6. Collections Summary
7. Revenue At Risk Analysis
8. Denial Health Overview
9. Top Denial Reasons
10. Assigned Visibility
11. Assigned Agency Registry
12. Recent Billing Events & Releases

Required DDE visibility:

- DDE Exceptions KPI
- DDE Responses Pending
- DDE Eligibility Reviews
- DDE Status Checks
- DDE Exception Resolution
- DDE risks within Revenue At Risk
- DDE authorization in Assigned Visibility

==================================================
10. PRIORITY CALCULATION
==================================================

Do not invent opaque scores.

Priority must be explainable.

Priority inputs may include:

- Hard statutory or payer deadline
- Revenue impact
- Days remaining
- Blocker severity
- Denial age
- External dependency
- Existing escalation
- Repeated failure

If a computed score is used, the UI must expose the reasons contributing to the priority.

Default ordering:

1. Immediate deadline or irreversible revenue-loss risk
2. Highest severity
3. Highest revenue impact
4. Oldest unresolved item
5. Stable deterministic tie-breaker

==================================================
11. ASSIGNED VISIBILITY BEHAVIOR
==================================================

Display:

- Billing organization
- Current agency
- Assigned primary biller
- DDE authorization status
- Assigned agency list
- Agency classification

Agency classifications:

- Production
- Training
- Demo

The section title is:

Assigned Agency Registry

Do not use:

Tenant Agency Registry

==================================================
12. AUDIT REQUIREMENTS
==================================================

Audit:

- Dashboard access
- Tenant selection
- Patient or claim drill-down
- Export activity
- Clearinghouse synchronization
- Work-item assignment
- Work-item resolution
- DDE review
- DDE exception resolution
- Revenue state changes
- Manual override
- Forecast generation
- Payment posting
- Claim submission or release

Every event must preserve:

- Actor
- Timestamp
- Tenant
- Billing organization
- Action
- Source object
- Previous state when applicable
- New state when applicable
- Reason
- Correlation ID

Do not log credentials or sensitive secret values.

==================================================
13. EMPTY, LOADING, AND ERROR STATES
==================================================

LOADING

- Display skeleton states within the approved layout.
- Do not show stale data as current.
- Maintain selected agency context.

EMPTY

Examples:

No Assigned Agencies:
"You do not currently have an assigned agency."

No DDE Authorization:
"DDE operations are unavailable for this user."

No Work Items:
"No billing work requires attention for this agency."

No Revenue Data:
"Revenue data is not yet available for the selected agency."

ERROR

- Provide a clear human-readable error.
- Provide retry where safe.
- Preserve no partial cross-tenant data.
- Log correlation ID.
- Do not expose stack traces, database details, secrets, or unauthorized identifiers.

STALE DATA

- Display last updated time.
- Display stale-data warning.
- Do not label stale information as real-time.

==================================================
14. PERFORMANCE REQUIREMENTS
==================================================

- Avoid one query per card.
- Prefer a server-generated scoped dashboard response or safe parallel aggregation.
- Use indexed tenant, status, date, claim, assignment, and DDE lookup paths.
- Prevent N+1 queries.
- Paginate activity and detailed lists.
- Do not load patient narratives into the dashboard response.
- Cache only with tenant-aware and permission-aware keys.
- Invalidate caches after material billing events.
- Never share cached results across tenant scopes.

==================================================
15. BILLING DASHBOARD ACCEPTANCE CRITERIA
==================================================

ACCESS

□ Unauthenticated users cannot access the page.
□ Users without Biller Platform permission cannot access the page.
□ Users only see assigned agencies.
□ Direct URL manipulation cannot expose unassigned agencies.
□ Agency switching clears previous agency data.
□ DDE actions require individual DDE authorization.

BRANDING

□ Header displays SNS Tech Solutions.
□ Header identifies Biller Platform.
□ Tenant context identifies SNS Hospice Solutions tenant.
□ Agency type badge is visible.

DATA

□ Every KPI is calculated from persisted data.
□ No mock value is presented as real.
□ Every value includes selected tenant scope.
□ Revenue totals are deduplicated.
□ Monetary calculations use decimal arithmetic.
□ Page exposes last-updated time.

WORKFLOW

□ Work queue opens the correct authorized destination.
□ Billing priorities use explainable ordering.
□ Revenue At Risk includes DDE conditions.
□ Assigned Agency Registry lists assigned agencies only.
□ Revenue Released events appear after qualified transitions.

AUDIT

□ Page access is auditable.
□ Exports are auditable.
□ DDE operations are auditable.
□ Tenant switching is auditable.
□ Manual overrides require a reason.
□ No secrets appear in logs.

UX

□ User can identify revenue position within 30 seconds.
□ User can identify today's highest-priority work.
□ User can identify current agency context.
□ User can identify DDE status.
□ Empty, loading, stale, and error states exist.
□ Layout matches approved Figma baseline.

==================================================
END DOCUMENT 1
==================================================

---

## Status

APPROVED / LOCKED / IMPLEMENTATION AUTHORIZED. This document is the
functional, workflow, data, security, and acceptance authority for the
Billing Dashboard page (the approved Figma design remains the visual
authority). Implementation is authorized in principle, but per the
Verify-First Requirement above, no code should be written until the
existing routes, models, and calculations have been inspected as
described in Section "Verify-First Requirement" — this document alone
does not constitute a go-ahead to begin coding without that
verification step, and actual implementation work should still be
kicked off as an explicit, separate task.

## Relationship to Other Documents

- Supersedes/finalizes the Billing Dashboard portion of
  `docs/biller-platform/BILLER_PLATFORM_LOCKED_SPECIFICATIONS.md` with
  full implementation-level detail (data models, calculation rules,
  permission matrix, audit requirements, acceptance criteria) — that
  document remains the locked high-level design; this document is the
  authoritative build specification for it.
- Enforces `docs/architecture/SNS_TECH_SOLUTIONS_PLATFORM_HIERARCHY.md`
  branding (SNS Tech Solutions Biller Platform, never SNS Hospice
  Solutions Biller Platform) and the DDE Architecture/Visibility Rules
  there.
- Implements the assignment-based visibility model from
  `docs/roadmap/Biller-Platform-Roadmap.md`'s Biller Platform Tenant
  Visibility Rule at the data-model level (Tenant Billing Assignment,
  User Tenant Billing Assignment, DDE Tenant Authorization).
- Its companion document,
  `docs/biller-platform/BILLING_READINESS_IMPLEMENTATION_SPECIFICATION.md`,
  must share the same authoritative Ready/Blocked/At-Risk revenue
  calculations and DDE exception counts (Section 20,
  Cross-Page Consistency Tests, in that document).
- After implementation, a
  `docs/biller-platform/BILLER_PLATFORM_IMPLEMENTATION_VERIFICATION.md`
  completion report is required per Section 22 of the companion
  Billing Readiness document.

## Change Log

| Date | Change |
|---|---|
| 2026-09-16 | Document created — full Billing Dashboard implementation specification: Global Implementation Directive, Verify-First Requirement, Locked Branding, Locked Access Principle, Page Purpose, Page Context, Route Requirements, Authorized User Types, Permission Matrix, Minimum Necessary Data Rule, 9 required data models (Billing Organization, Billing User Membership, Tenant Billing Assignment, User Tenant Billing Assignment, DDE User Profile, DDE Tenant Authorization, Billing Work Item, Billing Revenue Event, DDE Operational Event), Dashboard Calculation Rules (Ready/Blocked/At-Risk Revenue, Pending Payments, Denied Revenue, Recovery Opportunities, Expected Weekly Collections, DDE Exceptions), 12 Required UI Sections, Priority Calculation, Assigned Visibility Behavior, Audit Requirements, Empty/Loading/Error/Stale States, Performance Requirements, and full Acceptance Criteria. Status: Approved, Locked, Implementation Authorized (subject to Verify-First Requirement before any code change). |
