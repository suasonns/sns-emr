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
DOCUMENT 2
==================================================

CREATE:

/docs/biller-platform/BILLING_READINESS_IMPLEMENTATION_SPECIFICATION.md

==================================================
SNS TECH SOLUTIONS
BILLER PLATFORM
BILLING READINESS
REVENUE READINESS CENTER
==================================================

STATUS:

APPROVED
LOCKED
IMPLEMENTATION AUTHORIZED

==================================================
1. PAGE PURPOSE
==================================================

Billing Readiness is:

Revenue Readiness Center
Revenue Protection Center
Revenue Unlock Center

It must answer:

1. Why can't I bill?
2. What is missing?
3. Who owns the fix?
4. How much revenue is affected?
5. What revenue becomes available when resolved?

This page is not a duplicate of the Billing Dashboard.

The Billing Dashboard shows overall revenue position.

Billing Readiness shows the specific blocking and risk conditions preventing revenue from becoming billable, and the accountable path to resolving them.

==================================================
2. ROUTE AND SCOPE
==================================================

Use the existing Biller Platform route if already authoritative.

Do not create a second competing Billing Readiness route.

Scope is one currently selected, assigned SNS Hospice Solutions tenant, identical scoping rules to the Billing Dashboard:

- Requires authentication.
- Requires Biller Platform access.
- Requires selected agency assignment.
- Invalid agency identifiers return access denied or not found without exposing tenant existence.
- Agency switching re-fetches all readiness information within the new authorized scope.
- No data from the previously selected agency may remain visible after switching.

==================================================
3. PERMISSIONS
==================================================

Use the same Permission Matrix defined in
`BILLING_DASHBOARD_IMPLEMENTATION_SPECIFICATION.md` Section 5.

Additional readiness-specific behavior:

- Only users authorized to resolve a given readiness condition category may take resolving action on it.
- Read-Only Billing Auditors may view but not resolve.
- DDE-specific readiness conditions require individual DDE authorization to act on, in addition to tenant assignment.

==================================================
4. READINESS DATA MODELS
==================================================

Use existing authoritative models where available. Reuse the Billing
Work Item, Billing Revenue Event, and DDE Operational Event models
defined in `BILLING_DASHBOARD_IMPLEMENTATION_SPECIFICATION.md`
Sections 7.7-7.9 wherever a readiness condition maps to those
entities. The following additional entities are required.

--------------------------------------------------
4.1 READINESS CONDITION
--------------------------------------------------

Required fields:

- id
- tenant_id
- patient_id, nullable
- claim_id, nullable
- condition_type
- status
- severity
- revenue_impact
- owner_role
- owner_user_id, nullable
- detected_at
- due_at, nullable
- resolved_at, nullable
- resolution_code, nullable
- resolution_note, nullable
- source_record_type
- source_record_id
- correlation_id
- created_at
- updated_at
- version

--------------------------------------------------
4.2 READINESS CONDITION TYPE REGISTRY
--------------------------------------------------

Required fields:

- id
- code
- display_name
- category
- default_severity
- default_owner_role
- regulatory_reference, nullable
- active

--------------------------------------------------
4.3 REVENUE UNLOCK PROJECTION
--------------------------------------------------

Represents the revenue that becomes available if a readiness condition is resolved.

Required fields:

- id
- readiness_condition_id
- projected_amount
- currency
- calculation_basis
- calculated_at
- expires_at, nullable

--------------------------------------------------
4.4 READINESS ASSIGNMENT
--------------------------------------------------

Required fields:

- id
- readiness_condition_id
- assigned_user_id
- assigned_by_user_id
- assigned_at
- status
- due_at, nullable
- reassigned_from_user_id, nullable
- created_at
- updated_at

--------------------------------------------------
4.5 REVENUE RELEASED EVENT
--------------------------------------------------

Required fields:

- id
- tenant_id
- patient_id, nullable
- claim_id, nullable
- readiness_condition_id, nullable
- amount
- currency
- released_at
- released_by_user_id
- source_type
- source_id
- correlation_id
- created_at

Revenue Released events are append-only and correspond to the
"Recent Billing Events & Releases" section shared with the Billing
Dashboard.

==================================================
5. READINESS CONDITION TYPES
==================================================

Required condition types:

- unsigned_order
- certification_incomplete
- face_to_face_missing
- eligibility_risk
- noe_near_deadline
- noe_delayed
- documentation_gap
- timely_filing_risk

DDE-specific condition types:

- dde_verification_required
- dde_eligibility_conflict
- dde_status_unknown
- dde_response_pending
- dde_submission_failure

Use the Readiness Condition Type Registry (Section 4.2) as the single
source of truth for display names, default severity, default owner
role, and regulatory references. Do not hardcode condition metadata in
UI components.

==================================================
6. READINESS DECISION RULES
==================================================

A readiness condition is:

BLOCKING when the associated revenue cannot currently be billed at all.

AT RISK when the revenue can currently be billed but faces a deadline, external dependency, or other approved risk factor that could convert it to blocked or denied if not resolved in time.

RESOLVED when the condition's underlying record has been corrected and verified, and the condition record is closed with a resolution code and timestamp.

A condition must not be marked resolved based on the passage of time alone; resolution requires the underlying blocking fact to be verifiably corrected.

A single claim or patient may have multiple concurrent readiness conditions. Each is tracked independently, but revenue-impact totals must be deduplicated per claim or billable episode exactly as described in the Billing Dashboard Section 8 calculation rules.

==================================================
7. REVENUE CALCULATIONS
==================================================

All Billing Readiness revenue calculations must be identical in method
to the corresponding calculations in
`BILLING_DASHBOARD_IMPLEMENTATION_SPECIFICATION.md` Section 8, so the
two pages never disagree on the same underlying facts.

--------------------------------------------------
7.1 READY REVENUE
--------------------------------------------------

Same definition and calculation as Billing Dashboard Section 8.1.

--------------------------------------------------
7.2 PARTIALLY READY REVENUE
--------------------------------------------------

Partially Ready Revenue equals the sum of unique billable amounts that
have at least one resolved readiness requirement but at least one
remaining unresolved, non-blocking (at-risk) condition.

--------------------------------------------------
7.3 BLOCKED REVENUE
--------------------------------------------------

Same definition and calculation as Billing Dashboard Section 8.2.

--------------------------------------------------
7.4 REVENUE AT RISK
--------------------------------------------------

Same definition and calculation as Billing Dashboard Section 8.3.

--------------------------------------------------
7.5 REVENUE UNLOCK OPPORTUNITY
--------------------------------------------------

Revenue Unlock Opportunity equals the sum of active Revenue Unlock
Projections (Section 4.3) for currently unresolved readiness
conditions, deduplicated per claim or billable episode.

This figure must never exceed total Blocked Revenue plus Revenue At
Risk for the same tenant and as-of timestamp.

--------------------------------------------------
7.6 DDE REVENUE IMPACT
--------------------------------------------------

Same definition and calculation as Billing Dashboard Section 8.8.

==================================================
8. PRIORITY AND SORTING RULES
==================================================

Use the same Priority Calculation approach defined in
`BILLING_DASHBOARD_IMPLEMENTATION_SPECIFICATION.md` Section 10.

Default sort order for readiness conditions:

1. Blocking conditions before at-risk conditions.
2. Nearest due date or statutory deadline.
3. Highest revenue impact.
4. Oldest detected_at.
5. Stable deterministic tie-breaker (id).

Priority must remain explainable: the UI must expose the specific
factors that produced the ordering for any given item.

==================================================
9. REQUIRED UI SECTIONS
==================================================

Implement the approved Figma layout.

Required sections:

1. Revenue Readiness Summary
2. Today's Work Queue
3. Readiness Condition Detail List
4. DDE Health Status
5. Guided Resolution Panel
6. Assignment Accountability
7. Revenue Released Events
8. Assigned Visibility (shared with Billing Dashboard Section 11)

==================================================
10. DDE HEALTH STATUS
==================================================

Display, for the selected tenant and authorized DDE scope:

- Count of unresolved DDE conditions by type
- Oldest unresolved DDE condition age
- DDE authorization status for the current user
- Last successful DDE verification timestamp
- Revenue impact of unresolved DDE conditions

If the current user lacks DDE authorization, display an explicit
unavailable state rather than an empty or zero state.

==================================================
11. GUIDED RESOLUTION BEHAVIOR
==================================================

For each readiness condition, the UI must present:

- A plain-language description of what is missing
- The accountable owner role and, if assigned, the specific user
- The required corrective action
- A link or action to the authorized workflow that resolves it
- The revenue amount that unlocks upon resolution
- The regulatory reference, when one exists in the Condition Type
  Registry

Guided resolution actions must route to existing authorized
workflows. Do not fabricate a shortcut that bypasses required
approvals, signatures, or verifications.

==================================================
12. ASSIGNMENT ACCOUNTABILITY
==================================================

Every open readiness condition should have a clear accountable owner:
either a role (e.g., "Ordering Physician", "Front Office", "Billing
Staff") or a specific assigned user.

Reassignment must be recorded in Readiness Assignment (Section 4.4)
with the prior and new assignee, timestamp, and actor.

Unassigned conditions must be visibly flagged as unassigned rather
than silently defaulting to a role.

==================================================
13. AUTHORIZED SCOPE
==================================================

Billing Readiness operates only on tenants assigned to the current
user's billing organization, identical to the Locked Access Principle
above. It must never display or act on conditions for unassigned
tenants, self-billing agencies, or externally billed agencies not
assigned to the current billing organization.

==================================================
14. REVENUE RELEASED EVENTS
==================================================

A Revenue Released event (Section 4.5) must be created when, and only
when, a readiness condition's resolution causes previously blocked or
at-risk revenue to become billable or ready. Examples:

- Order Signed → Revenue Released
- Certification Completed → Revenue Released
- Eligibility Confirmed → Revenue Released
- DDE Exception Resolved → Revenue Released

These events feed the shared "Recent Billing Events & Releases"
section on both the Billing Dashboard and Billing Readiness pages and
must be identical between the two.

==================================================
15. IMMUTABILITY AND CORRECTION
==================================================

Once a readiness condition is resolved and a Revenue Released event is
recorded, that event is immutable. If a resolution is later found to
be incorrect, create a corrective readiness condition and a
corresponding corrective revenue event; do not edit or delete the
original historical record.

This is consistent with the Production Agency Data Immutability Rule
in `docs/production/PRODUCTION_READINESS_CLEANUP_CHECKLIST.md`, except
for the Angela Hospice and Silva Hospice training/demo agencies, where
direct correction remains permitted.

==================================================
16. REGULATORY REFERENCES
==================================================

Where a readiness condition type has an applicable regulatory basis
(for example, hospice NOE timely-filing requirements, face-to-face
encounter requirements, or certification-of-terminal-illness
requirements), the Readiness Condition Type Registry (Section 4.2)
must store a reference identifier or citation. Do not hardcode
regulatory citations in UI templates; source them from the registry
so they can be corrected centrally.

==================================================
17. EMPTY, LOADING, ERROR, AND STALE STATES
==================================================

LOADING

- Display skeleton states within the approved layout.
- Do not show stale data as current.
- Maintain selected agency context.

EMPTY

Examples:

No Readiness Conditions:
"No revenue readiness issues currently require attention for this
agency."

No DDE Authorization:
"DDE operations are unavailable for this user."

No Assigned Agencies:
"You do not currently have an assigned agency."

ERROR

- Provide a clear human-readable error.
- Provide retry where safe.
- Preserve no partial cross-tenant data.
- Log correlation ID.
- Do not expose stack traces, database details, secrets, or
  unauthorized identifiers.

STALE DATA

- Display last updated time.
- Display stale-data warning.
- Do not label stale information as real-time.

==================================================
18. AUDIT REQUIREMENTS
==================================================

Audit:

- Page access
- Tenant selection
- Readiness condition view and drill-down
- Resolution actions
- Reassignment actions
- DDE review and resolution
- Revenue Released event creation
- Corrective actions
- Export activity

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
19. BILLING READINESS ACCEPTANCE CRITERIA
==================================================

ACCESS

□ Unauthenticated users cannot access the page.
□ Users without Biller Platform permission cannot access the page.
□ Users only see assigned agencies.
□ Direct URL manipulation cannot expose unassigned agencies.
□ Agency switching clears previous agency data.
□ DDE actions require individual DDE authorization.

DATA

□ Every readiness condition is calculated from persisted data.
□ No mock value is presented as real.
□ Revenue totals are deduplicated per claim or billable episode.
□ Monetary calculations use decimal arithmetic.
□ Revenue Unlock Opportunity never exceeds Blocked + At-Risk revenue.
□ Page exposes last-updated time.

WORKFLOW

□ Every condition displays an accountable owner (role or user).
□ Guided resolution links route to authorized existing workflows.
□ Resolution requires a resolution code and note.
□ Reassignment is recorded with prior and new assignee.
□ Revenue Released events are created only on qualifying transitions.
□ Corrections create new corrective records, never edits to history.

AUDIT

□ Page access is auditable.
□ Resolution and reassignment actions are auditable.
□ DDE operations are auditable.
□ Exports are auditable.
□ No secrets appear in logs.

CROSS-PAGE CONSISTENCY

□ Ready Revenue matches between Billing Dashboard and Billing Readiness for the same tenant and as-of timestamp.
□ Blocked Revenue matches between both pages.
□ Revenue At Risk matches between both pages.
□ DDE Exceptions count matches between both pages.
□ Assigned Agency Registry matches between both pages.

==================================================
20. CROSS-PAGE CONSISTENCY TESTS
==================================================

Required automated or documented test coverage:

1. Given identical underlying data, Billing Dashboard and Billing
   Readiness must return identical Ready, Blocked, and At-Risk revenue
   totals for the same tenant and as-of timestamp.
2. Given identical underlying data, DDE Exceptions counts must match
   between both pages.
3. Resolving a readiness condition must be reflected in the Billing
   Dashboard's Revenue Pipeline and Recent Billing Events & Releases
   within the same request/response cycle or documented refresh
   interval.
4. Switching the selected agency must clear and re-scope both pages
   identically.
5. A user without DDE authorization must see the same DDE-unavailable
   state on both pages.

==================================================
21. TEST REQUIREMENTS
==================================================

Required test coverage before implementation is considered complete:

- Unit tests for every revenue calculation in Section 7.
- Unit tests for readiness condition status transitions (Section 6).
- Integration tests for tenant-assignment enforcement (unauthorized
  tenant access must be denied at the API layer, not just hidden in
  the UI).
- Integration tests for DDE authorization enforcement, independent of
  tenant assignment.
- Regression tests confirming immutability of resolved conditions and
  Revenue Released events.
- Cross-page consistency tests per Section 20.
- Audit log assertions for every action listed in Section 18.

==================================================
22. IMPLEMENTATION COMPLETION REPORT
==================================================

Upon completion of implementation for both the Billing Dashboard and
Billing Readiness pages, create:

/docs/biller-platform/BILLER_PLATFORM_IMPLEMENTATION_VERIFICATION.md

This report must document:

- Which existing routes, models, and migrations were found during the
  Verify-First step.
- Which fields/entities already existed vs. were newly added.
- Any deviations from this specification, with justification.
- Test results for all Section 21 requirements.
- Confirmation that Cross-Page Consistency Tests (Section 20) pass.
- Confirmation that no unassigned tenant data is exposed.
- Confirmation that DDE credentials are not stored or logged in
  plaintext.

Do not mark this specification's implementation complete without this
report.

==================================================
FINAL LOCK
==================================================

Both documents:

/docs/biller-platform/BILLING_DASHBOARD_IMPLEMENTATION_SPECIFICATION.md

/docs/biller-platform/BILLING_READINESS_IMPLEMENTATION_SPECIFICATION.md

are:

APPROVED
LOCKED
IMPLEMENTATION AUTHORIZED

No redesign is authorized.

No branding deviation is authorized.

No visibility deviation is authorized.

Future changes must be additive enhancements only, and any change to
locked calculation rules, data models, permission matrices, or
acceptance criteria requires an explicit, documented amendment to
these specifications before code changes are made.

==================================================
END DOCUMENT 2
==================================================

---

## Status

APPROVED / LOCKED / IMPLEMENTATION AUTHORIZED. This document is the
functional, workflow, data, security, and acceptance authority for the
Billing Readiness page (the approved Figma design remains the visual
authority). Implementation is authorized in principle, but per the
Verify-First Requirement above, no code should be written until the
existing routes, models, and calculations have been inspected — this
document alone does not constitute a go-ahead to begin coding without
that verification step, and actual implementation work should still be
kicked off as an explicit, separate task. This document also carries
the shared "FINAL LOCK" statement covering both this document and its
companion Billing Dashboard specification.

## Relationship to Other Documents

- Companion to
  `docs/biller-platform/BILLING_DASHBOARD_IMPLEMENTATION_SPECIFICATION.md`,
  which it shares the Global Implementation Directive, Verify-First
  Requirement, Locked Branding, and Locked Access Principle preamble
  with, and with which its revenue calculations, DDE Exceptions count,
  and Assigned Agency Registry must remain consistent per Section 20
  (Cross-Page Consistency Tests).
- Supersedes/finalizes the Billing Readiness portion of
  `docs/biller-platform/BILLER_PLATFORM_LOCKED_SPECIFICATIONS.md` with
  full implementation-level detail — that document remains the locked
  high-level design; this document is the authoritative build
  specification for it.
- Enforces `docs/architecture/SNS_TECH_SOLUTIONS_PLATFORM_HIERARCHY.md`
  branding and DDE ownership rules.
- Implements the assignment-based visibility model from
  `docs/roadmap/Biller-Platform-Roadmap.md`'s Biller Platform Tenant
  Visibility Rule.
- Its Section 15 (Immutability and Correction) references and remains
  consistent with the Production Agency Data Immutability Rule and the
  Angela/Silva Hospice Data Modification Rule exception in
  `docs/production/PRODUCTION_READINESS_CLEANUP_CHECKLIST.md`.
- Section 22 requires a future
  `docs/biller-platform/BILLER_PLATFORM_IMPLEMENTATION_VERIFICATION.md`
  completion report once both this document and its companion are
  implemented.

## Change Log

| Date | Change |
|---|---|
| 2026-09-16 | Document created — full Billing Readiness implementation specification: shared Global Implementation Directive/Verify-First Requirement/Locked Branding/Locked Access Principle preamble, Page Purpose, Route and Scope, Permissions, 5 Readiness Data Models (Readiness Condition, Readiness Condition Type Registry, Revenue Unlock Projection, Readiness Assignment, Revenue Released Event), Readiness Condition Types (including DDE-specific types), Readiness Decision Rules, Revenue Calculations (Sections 7.1-7.6), Priority and Sorting Rules, 8 Required UI Sections, DDE Health Status, Guided Resolution Behavior, Assignment Accountability, Authorized Scope, Revenue Released Events, Immutability and Correction, Regulatory References, Empty/Loading/Error/Stale States, Audit Requirements, full Acceptance Criteria, Cross-Page Consistency Tests, Test Requirements, Implementation Completion Report requirement, and the shared Final Lock statement. Status: Approved, Locked, Implementation Authorized (subject to Verify-First Requirement before any code change). |
