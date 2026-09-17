==================================================
SHARED PURPOSE
==================================================

CREATE AND MAINTAIN BOTH DOCUMENTS:

1. /docs/biller-platform/BILLER_PLATFORM_DATABASE_SCHEMA_AND_MIGRATION_PLAN.md
2. /docs/biller-platform/BILLER_PLATFORM_IMPLEMENTATION_TASK_BREAKDOWN.md

Translate the locked Billing Dashboard and Billing Readiness specifications into:

- Verified database architecture
- Forward-only migration sequencing
- Server-enforced tenant isolation
- Assignment-based biller visibility
- Individual DDE authorization
- Immutable readiness and revenue history
- Explainable revenue calculations
- Auditable implementation tasks

DO NOT BEGIN FEATURE IMPLEMENTATION UNTIL PHASE 0 DISCOVERY IS COMPLETE.

==================================================
DOCUMENT 1
==================================================

CREATE:

/docs/biller-platform/BILLER_PLATFORM_DATABASE_SCHEMA_AND_MIGRATION_PLAN.md

==================================================
SNS TECH SOLUTIONS
BILLER PLATFORM
DATABASE SCHEMA AND MIGRATION PLAN
==================================================

STATUS

APPROVED TARGET ARCHITECTURE

SCHEMA IMPLEMENTATION REQUIRES REPOSITORY VERIFICATION

==================================================
1. NON-NEGOTIABLE DATABASE RULES
==================================================

1. VERIFY FIRST.

2. Do not guess current table names, model names, enum names, foreign keys, indexes, or migration head.

3. Reuse authoritative existing structures whenever they correctly satisfy the requirement.

4. Do not create duplicate tables for data already represented by an authoritative model.

5. All schema changes must be forward-only.

6. Do not use alembic stamp.

7. Do not rewrite, delete, reorder, or squash historical migrations.

8. Do not generate unsafe automigrations.

9. Do not allow schema drift between ORM metadata, Alembic migrations, and PostgreSQL.

10. Never delete production billing, readiness, DDE, revenue, evidence, or audit history.

11. Corrections create new records or append-only corrective events.

12. Every tenant-owned row must carry authoritative tenant scope.

13. Every patient-owned row must also carry tenant scope.

14. Database and API enforcement must prevent cross-tenant access.

15. Monetary fields must use fixed-precision decimal or numeric types, never float.

16. All timestamps must be timezone-aware and stored consistently in UTC.

17. All foreign keys, uniqueness rules, indexes, and delete behaviors must be explicit.

18. Test-created records must be tagged and removed by teardown.

19. Development tests must not leave unexplained persistent data.

20. Production migrations must contain schema and approved configuration only, never test business data.

==================================================
2. PHASE 0: REQUIRED REPOSITORY DISCOVERY
==================================================

Before proposing or creating a migration, inspect and document:

- Current Alembic head
- Current migration graph
- Current SQLAlchemy or ORM models
- Current tenant model
- Current patient model
- Current user model
- Current role and permission models
- Current billing models
- Current claim models
- Current NOE models
- Current eligibility models
- Current payment and remittance models
- Current denial and appeal models
- Current audit event model
- Current evidence or provenance models
- Current workflow task or alert models
- Current billing assignment logic
- Current DDE-related code, fields, integrations, or placeholders
- Current soft-delete, versioning, and immutability patterns
- Existing PostgreSQL constraints, indexes, triggers, views, and materialized views
- Current frontend API contracts used by Billing Dashboard and Billing Readiness

CREATE A DISCOVERY MATRIX WITH THESE COLUMNS:

Requirement

Existing Model or Table

Existing Fields

Existing Constraints

Existing Indexes

Reuse

Extend

New Structure Required

Evidence Path

Notes

Do not continue until every proposed logical entity is classified as:

- REUSE
- EXTEND
- CREATE

==================================================
3. LOGICAL SCHEMA MAP
==================================================

The following names are logical target names.

They are not authorization to create duplicate physical tables.

Map them to existing authoritative structures during discovery.

CORE RELATIONSHIPS:

```
Tenant
  |
  +-- Tenant Billing Assignment
          |
          +-- Billing Organization
                  |
                  +-- Billing Organization Membership
                  |
                  +-- User Tenant Billing Assignment
                  |
                  +-- Individual DDE User Profile
                          |
                          +-- DDE Tenant Authorization

Tenant
  |
  +-- Billable Episode
          |
          +-- Readiness Evaluation
                  |
                  +-- Readiness Conditions
                  |       |
                  |       +-- Evidence References
                  |       +-- Readiness Actions
                  |
                  +-- Revenue Events
                  +-- DDE Operational Events
                  +-- Billing Work Items
```

==================================================
4. BILLING ORGANIZATION
==================================================

PURPOSE

Represents an authorized billing group operating inside the SNS Tech Solutions Biller Platform.

LOGICAL FIELDS

- id: UUID or existing authoritative identifier
- legal_name: text
- display_name: text
- organization_type: controlled value
- status: active, suspended, inactive, archived
- created_at: timestamptz
- updated_at: timestamptz
- created_by_user_id
- updated_by_user_id
- version

REQUIRED CONSTRAINTS

- Legal or normalized organization identity must not duplicate unintentionally.
- Status must use a controlled value.
- Historical organizations referenced by billing events cannot be hard deleted.

REQUIRED INDEXES

- status
- normalized organization name where required
- created_at

==================================================
5. BILLING ORGANIZATION MEMBERSHIP
==================================================

PURPOSE

Assigns an individual user to a billing organization.

LOGICAL FIELDS

- id
- user_id
- billing_organization_id
- role_code
- membership_status
- effective_from
- effective_to, nullable
- created_at
- updated_at
- created_by_user_id
- updated_by_user_id
- version

REQUIRED CONSTRAINTS

- effective_to must not precede effective_from.
- Only one active equivalent membership may exist for the same user and billing organization.
- Membership termination preserves historical activity.

REQUIRED INDEXES

- user_id, membership_status
- billing_organization_id, membership_status
- effective_from, effective_to

==================================================
6. TENANT BILLING ASSIGNMENT
==================================================

PURPOSE

Assigns an SNS Hospice Solutions tenant agency to a billing organization.

LOGICAL FIELDS

- id
- tenant_id
- billing_organization_id
- billing_model
- assignment_status
- effective_from
- effective_to, nullable
- assigned_by_user_id
- assignment_reason
- created_at
- updated_at
- version

BILLING MODEL VALUES

Map to existing controlled values or implement equivalent values:

- sns_managed_billing
- external_biller
- self_billing
- no_billing_access

REQUIRED CONSTRAINTS

- effective_to must not precede effective_from.
- Only valid tenant and billing organization references are allowed.
- An active managed-billing assignment must not overlap another conflicting managed-billing assignment unless an approved multi-biller model is explicitly documented.
- Ending the assignment never deletes historical billing data.

REQUIRED INDEXES

- tenant_id, assignment_status
- billing_organization_id, assignment_status
- effective_from, effective_to

==================================================
7. USER TENANT BILLING ASSIGNMENT
==================================================

PURPOSE

Assigns responsibility for a tenant to an individual within the authorized billing organization.

LOGICAL FIELDS

- id
- tenant_id
- billing_organization_id
- user_id
- assignment_role
- assignment_status
- is_primary
- effective_from
- effective_to, nullable
- assigned_by_user_id
- created_at
- updated_at
- version

REQUIRED CONSTRAINTS

- User must have an active membership in the same billing organization.
- Tenant must have an active assignment to the same billing organization.
- Only one active primary biller may exist per tenant unless multiple-primary behavior is explicitly approved.
- Historical assignments remain preserved.

REQUIRED INDEXES

- user_id, assignment_status
- tenant_id, assignment_status
- billing_organization_id, tenant_id
- tenant_id, is_primary where active

==================================================
8. INDIVIDUAL DDE USER PROFILE
==================================================

PURPOSE

Records whether an individual biller in a billing group is authorized to perform DDE operations.

DDE authorization belongs to the person operating within the billing group.

DO NOT STORE PLAINTEXT DDE PASSWORDS.

LOGICAL FIELDS

- id
- user_id
- billing_organization_id
- authorization_status
- authorization_reference, encrypted or tokenized only if approved
- effective_from
- effective_to, nullable
- verified_at
- verified_by_user_id
- last_reviewed_at
- suspended_at, nullable
- suspension_reason, nullable
- created_at
- updated_at
- version

AUTHORIZATION STATUS

- pending
- verified
- suspended
- expired
- revoked

REQUIRED CONSTRAINTS

- User must belong to the billing organization.
- effective_to must not precede effective_from.
- DDE secrets must never appear in this table unless separately approved secure-secret architecture exists.
- Authorization history cannot be deleted.

REQUIRED INDEXES

- user_id, authorization_status
- billing_organization_id, authorization_status
- effective_from, effective_to

==================================================
9. DDE TENANT AUTHORIZATION
==================================================

PURPOSE

Defines which assigned tenant agencies an individually DDE-authorized biller may operate on.

LOGICAL FIELDS

- id
- dde_user_profile_id
- tenant_id
- authorization_status
- effective_from
- effective_to, nullable
- verified_at
- verified_by_user_id
- created_at
- updated_at
- version

REQUIRED CONSTRAINTS

- DDE user profile must be active and verified.
- Tenant must be actively assigned to the same billing organization.
- Only one equivalent active authorization may exist per DDE profile and tenant.
- Historical authorization must remain preserved.

REQUIRED INDEXES

- dde_user_profile_id, authorization_status
- tenant_id, authorization_status
- tenant_id, dde_user_profile_id

==================================================
10. BILLABLE EPISODE
==================================================

PURPOSE

Provides one authoritative unit for revenue-readiness calculation and deduplication.

Use an existing claim period, billing period, benefit period billing unit, or equivalent authoritative model where available.

LOGICAL FIELDS

- id
- tenant_id
- patient_id
- billing_period_start
- billing_period_end
- payer_id
- claim_id, nullable
- episode_status
- authoritative_billable_amount
- currency
- created_at
- updated_at
- version

REQUIRED CONSTRAINTS

- Amount uses fixed-precision numeric.
- Period end cannot precede period start.
- Tenant must match the patient tenant.
- If claim exists, claim tenant and patient scope must match.
- Duplicate equivalent billable episodes are prohibited.

REQUIRED INDEXES

- tenant_id, episode_status
- tenant_id, patient_id
- tenant_id, billing_period_start, billing_period_end
- claim_id
- payer_id

==================================================
11. READINESS EVALUATION
==================================================

PURPOSE

Stores an immutable result of a billing-readiness evaluation.

Do not overwrite prior evaluations.

LOGICAL FIELDS

- id
- tenant_id
- patient_id
- billable_episode_id
- claim_id, nullable
- evaluation_status
- evaluated_at
- evaluator_type
- evaluated_by_user_id, nullable
- ruleset_version
- source_snapshot_reference
- ready_revenue_amount
- blocked_revenue_amount
- at_risk_revenue_amount
- unlockable_revenue_amount
- supersedes_evaluation_id, nullable
- correlation_id
- created_at

EVALUATION STATUS

- not_ready
- in_progress
- awaiting_external
- ready_to_bill
- submitted
- paid

REQUIRED CONSTRAINTS

- Evaluation amounts use fixed-precision numeric.
- Tenant, patient, episode, and claim scope must agree.
- supersedes_evaluation_id cannot reference itself.
- Historical evaluation rows cannot be updated to rewrite their result.

REQUIRED INDEXES

- tenant_id, evaluated_at descending
- billable_episode_id, evaluated_at descending
- patient_id, evaluated_at descending
- claim_id
- evaluation_status
- correlation_id

CURRENT EVALUATION

Determine current readiness through:

- Existing authoritative current-state pointer, or
- Latest valid non-superseded evaluation

Do not introduce a materialized current pointer without verifying concurrency and rollback behavior.

==================================================
12. READINESS CONDITION
==================================================

PURPOSE

Records each specific condition affecting readiness.

LOGICAL FIELDS

- id
- evaluation_id
- tenant_id
- patient_id
- billable_episode_id
- claim_id, nullable
- condition_type
- condition_status
- severity
- blocking_level
- owner_type
- assigned_user_id, nullable
- amount_impacted
- due_at, nullable
- detected_at
- resolved_at, nullable
- source_type
- source_id
- regulatory_reference_id, nullable
- resolution_code, nullable
- resolution_note, nullable
- created_at
- updated_at
- version

CONDITION TYPES

- unsigned_order
- missing_certification
- missing_face_to_face
- eligibility_issue
- noe_deficiency
- timely_filing_risk
- documentation_gap
- dde_verification_required
- dde_eligibility_conflict
- dde_status_unknown
- dde_response_pending
- dde_submission_failure
- completed_clinical_audit

CONDITION STATUS

- open
- in_progress
- awaiting_external
- resolved
- waived
- superseded

BLOCKING LEVEL

- informational
- warning
- at_risk
- blocking

OWNER TYPE

- billing_team
- clinical_team
- physician
- medical_records
- administrator
- external_party

REQUIRED CONSTRAINTS

- amount_impacted uses fixed-precision numeric.
- resolved conditions require resolved_at.
- Open conditions must not contain a final resolution code.
- Tenant, patient, episode, claim, and evaluation scope must agree.
- completed_clinical_audit cannot be assigned a blocking state.
- Waiver requires actor, reason, authority, and audit history.

REQUIRED INDEXES

- tenant_id, condition_status
- tenant_id, condition_type, condition_status
- billable_episode_id, condition_status
- assigned_user_id, condition_status
- owner_type, condition_status
- due_at where unresolved
- evaluation_id

==================================================
13. READINESS EVIDENCE REFERENCE
==================================================

PURPOSE

Links readiness determinations to their supporting source.

LOGICAL FIELDS

- id
- condition_id
- tenant_id
- source_document_id, nullable
- source_record_type
- source_record_id
- page_number, nullable
- line_start, nullable
- line_end, nullable
- source_excerpt_reference, nullable
- document_date, nullable
- document_author_id, nullable
- captured_at
- created_at

REQUIRED RULES

- Native structured data does not require page or line numbers.
- Uploaded or paginated documents should preserve page and line location when technically available.
- Evidence must retain source identity.
- Evidence cannot be silently replaced.
- Corrected evidence creates a new reference and supersession relationship if needed.

REQUIRED INDEXES

- condition_id
- tenant_id, source_record_type, source_record_id
- source_document_id

==================================================
14. READINESS ACTION
==================================================

PURPOSE

Preserves every assignment, escalation, correction, resolution, and revalidation action.

LOGICAL FIELDS

- id
- condition_id
- tenant_id
- action_type
- actor_user_id
- previous_status
- resulting_status
- reason
- note, nullable
- occurred_at
- correlation_id
- created_at

ACTION TYPES

- assigned
- reassigned
- escalated
- correction_requested
- evidence_added
- resolved
- reopened
- waived
- superseded
- navigated_to_source
- revalidated

REQUIRED RULES

- Append-only.
- Reason required for waiver, reopen, supersede, and manual override.
- Actor and tenant must always be present.
- No physical delete.

REQUIRED INDEXES

- condition_id, occurred_at
- tenant_id, occurred_at
- actor_user_id, occurred_at
- correlation_id

==================================================
15. BILLING WORK ITEM
==================================================

PURPOSE

Supports Today's Work Queue and operational assignment.

LOGICAL FIELDS

- id
- tenant_id
- patient_id, nullable
- billable_episode_id, nullable
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
- resolved_at, nullable
- resolution_code, nullable
- resolution_note, nullable
- version

WORK CATEGORIES

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

REQUIRED RULES

- Work item must point to an authoritative source.
- Duplicate active work items for the same source and category must be prevented.
- Resolution preserves history.
- Clinical obligations cannot be completed by unauthorized billing users.

REQUIRED INDEXES

- tenant_id, status, priority
- tenant_id, category, status
- assigned_user_id, status
- assigned_team, status
- due_at where unresolved
- source_record_type, source_record_id

==================================================
16. BILLING REVENUE EVENT
==================================================

PURPOSE

Creates immutable financial state history.

LOGICAL FIELDS

- id
- tenant_id
- patient_id, nullable
- billable_episode_id, nullable
- claim_id, nullable
- event_type
- amount
- currency
- actor_user_id, nullable for approved system actors
- actor_type
- source_type
- source_id
- occurred_at
- recorded_at
- correlation_id
- metadata
- reverses_event_id, nullable
- created_at

EVENT TYPES

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
- correction
- reversal

REQUIRED RULES

- Append-only.
- Monetary values use fixed-precision numeric.
- Reversal references original event.
- Correction does not overwrite original event.
- revenue_released means available to progress in billing, not paid.
- Claim payment is a separate event.

REQUIRED INDEXES

- tenant_id, occurred_at
- billable_episode_id, occurred_at
- claim_id, occurred_at
- event_type, occurred_at
- correlation_id
- reverses_event_id

==================================================
17. DDE OPERATIONAL EVENT
==================================================

PURPOSE

Stores operational DDE status and exception history.

LOGICAL FIELDS

- id
- tenant_id
- patient_id, nullable
- billable_episode_id, nullable
- claim_id, nullable
- dde_user_profile_id
- event_type
- event_status
- severity
- revenue_impact
- occurred_at
- resolved_at, nullable
- source_reference
- resolution_code, nullable
- resolution_note, nullable
- correlation_id
- created_at

EVENT TYPES

- verification_required
- eligibility_conflict
- status_unknown
- response_pending
- submission_failure
- exception_created
- exception_resolved
- status_reviewed
- connectivity_status_changed

EVENT STATUS

- open
- in_progress
- awaiting_response
- resolved
- superseded

REQUIRED RULES

- DDE user must be individually authorized for the tenant at the time of an operational action.
- DDE credentials must never be written to this table.
- Resolved events remain preserved.
- DDE events map into readiness conditions where revenue progression is affected.

REQUIRED INDEXES

- tenant_id, event_status
- tenant_id, event_type, event_status
- dde_user_profile_id, occurred_at
- claim_id
- billable_episode_id
- correlation_id

==================================================
18. REGULATORY REFERENCE
==================================================

PURPOSE

Supports approved regulation and policy citations displayed with guided correction.

Reuse an existing approved knowledge-source model if available.

LOGICAL FIELDS

- id
- authority
- title
- section_reference
- effective_from
- effective_to, nullable
- source_document_id, nullable
- source_url_reference, nullable
- source_version
- approval_status
- approved_at
- approved_by_user_id
- created_at
- updated_at

RULES

- Only approved references can be displayed as authoritative guidance.
- AI must not invent citations.
- Historical references used in finalized decisions remain preserved.

==================================================
19. DATABASE-LEVEL TENANT ISOLATION
==================================================

Implement defense in depth.

REQUIRED

- tenant_id on tenant-owned billing rows
- Foreign-key scope validation
- Server-side authorization
- Tenant-aware repository queries
- Tenant-aware cache keys
- Tenant-aware export filters
- Tenant-aware background job inputs
- Tenant-aware audit events

Evaluate PostgreSQL row-level security only after reviewing existing architecture.

Do not add row-level security blindly if it conflicts with current transaction, service-account, migration, or support architecture.

If RLS is not used, document the equivalent enforced isolation layer and test coverage.

==================================================
20. DELETE AND RETENTION BEHAVIOR
==================================================

Production billing records:

- No physical delete
- No cascade delete of historical billing events
- No cascade delete of readiness history
- No cascade delete of DDE history
- No cascade delete of evidence history

Recommended foreign-key delete behavior for historical records:

- RESTRICT
- NO ACTION
- Approved nullable reference with preserved snapshot

Do not use CASCADE on immutable business history unless specifically proven safe and approved.

Development test records:

- Must be identifiable
- Must be isolated
- Must be removable through test teardown
- Must never be copied into production

==================================================
21. MIGRATION PLAN
==================================================

Migrations must be small, forward-only, and independently verifiable.

Do not combine all schema changes into one migration.

--------------------------------------------------
MIGRATION 0: BASELINE VERIFICATION
--------------------------------------------------

No schema changes.

Verify:

- Current Alembic head
- Single valid migration lineage
- No pending branches
- ORM metadata matches database
- No abandoned schema
- No undocumented objects
- Existing production-style data preserved

Output:

Baseline verification report.

BLOCKER:

Do not proceed if schema drift exists.

--------------------------------------------------
MIGRATION 1: BILLING ORGANIZATION AND MEMBERSHIP
--------------------------------------------------

Add only missing structures for:

- Billing organization
- Billing organization membership

Verification:

- Upgrade succeeds
- Existing users unaffected
- Membership uniqueness enforced
- Historical membership supported
- Downgrade is not used as production rollback

--------------------------------------------------
MIGRATION 2: TENANT AND USER BILLING ASSIGNMENTS
--------------------------------------------------

Add only missing structures for:

- Tenant billing assignment
- User tenant billing assignment

Verification:

- Assigned agencies resolve correctly
- Unassigned agencies remain inaccessible
- Expired assignments stop future access
- Historical activity remains accessible to authorized auditors

--------------------------------------------------
MIGRATION 3: INDIVIDUAL DDE AUTHORIZATION
--------------------------------------------------

Add only missing structures for:

- DDE user profile
- DDE tenant authorization

Verification:

- DDE access belongs to an individual in the billing group
- Tenant authorization is required
- No plaintext credential storage exists
- Revoked or expired users cannot perform DDE actions

--------------------------------------------------
MIGRATION 4: BILLABLE EPISODE AUTHORITY
--------------------------------------------------

Implement or extend the authoritative deduplication unit.

Verification:

- No duplicate equivalent episodes
- Tenant and patient scope match
- Monetary precision is correct
- Existing claim relationships remain valid

--------------------------------------------------
MIGRATION 5: READINESS EVALUATIONS
--------------------------------------------------

Add or extend immutable readiness evaluation history.

Verification:

- New evaluation does not overwrite old evaluation
- Supersession links work
- Current evaluation resolves deterministically
- Ruleset version is preserved

--------------------------------------------------
MIGRATION 6: READINESS CONDITIONS
--------------------------------------------------

Add or extend readiness condition storage.

Verification:

- Blocker types work
- Owner types work
- Completed clinical audit is not blocking
- Revenue impact uses decimal
- Open and resolved states are valid

--------------------------------------------------
MIGRATION 7: EVIDENCE REFERENCES AND ACTION HISTORY
--------------------------------------------------

Add or extend:

- Readiness evidence references
- Readiness actions

Verification:

- Evidence links remain traceable
- Page and line fields are optional
- Structured sources work without page references
- Action history is append-only
- Waiver and override require reasons

--------------------------------------------------
MIGRATION 8: WORK ITEMS
--------------------------------------------------

Add or extend operational billing work items.

Verification:

- Duplicate active work items are prevented
- Work queues filter by assigned tenant
- Clinical obligations cannot be falsely completed by billing staff
- Resolved items remain in history

--------------------------------------------------
MIGRATION 9: REVENUE EVENTS
--------------------------------------------------

Add or extend immutable revenue event history.

Verification:

- Revenue release, claim submission, acceptance, payment, denial, correction, and reversal remain distinct
- Reversal preserves original event
- Revenue totals deduplicate correctly
- Decimal precision is preserved

--------------------------------------------------
MIGRATION 10: DDE OPERATIONAL EVENTS
--------------------------------------------------

Add or extend DDE event storage.

Verification:

- DDE conditions map to readiness
- Revenue impact is available
- Individual authorization is enforced
- Resolution preserves original event

--------------------------------------------------
MIGRATION 11: REGULATORY REFERENCES
--------------------------------------------------

Only if no authoritative approved model exists.

Verification:

- Only approved references appear in guidance
- Effective dates are preserved
- Historical references remain resolvable

--------------------------------------------------
MIGRATION 12: INDEXES AND CONSTRAINT HARDENING
--------------------------------------------------

Add reviewed:

- Foreign keys
- Check constraints
- Unique indexes
- Partial unique indexes
- Query indexes

Verification:

- Explain plans reviewed for dashboard and readiness queries
- No duplicate active assignments
- No duplicate active work items
- No orphan creation paths
- No unacceptable table locks

--------------------------------------------------
MIGRATION 13: OPTIONAL CURRENT-STATE PROJECTIONS
--------------------------------------------------

Only if necessary after performance testing.

Possible structures:

- Database views
- Materialized views
- Projection tables

Rules:

- Immutable source tables remain authoritative
- Projections must be rebuildable
- Projection failure cannot destroy source history
- Refresh behavior must be documented
- Cross-tenant projection leakage is prohibited

==================================================
22. MIGRATION EXECUTION GATES
==================================================

For every migration:

PRE-MIGRATION

□ Verify current database identity.
□ Verify expected Alembic current revision.
□ Verify expected Alembic head.
□ Create backup.
□ Verify backup.
□ Capture row counts for affected tables.
□ Capture constraints and indexes.
□ Confirm no unexpected test records.
□ Review generated SQL.
□ Review lock and data-rewrite risk.

EXECUTION

□ Run migration in development.
□ Verify upgrade result.
□ Verify ORM metadata alignment.
□ Verify constraints.
□ Verify indexes.
□ Verify tenant isolation.
□ Verify existing workflows.
□ Verify audit behavior.

POST-MIGRATION

□ Compare pre/post row counts.
□ Confirm no records disappeared.
□ Confirm no fields were silently rewritten.
□ Run focused tests.
□ Run migration-head verification.
□ Run schema-drift verification.
□ Record evidence.
□ Clean all test artifacts.

PRODUCTION RULE

Do not use downgrade as the primary repair strategy.

If a production migration requires repair:

- Diagnose
- Preserve data
- Create a forward-only corrective migration
- Verify again

==================================================
23. SCHEMA ACCEPTANCE CRITERIA
==================================================

□ Existing authoritative models are reused.
□ No duplicate billing architecture is created.
□ Migration chain has one expected head.
□ ORM and database match.
□ Tenant-owned rows carry tenant scope.
□ Patient-owned rows match tenant scope.
□ Billing organization assignment is enforced.
□ Individual biller assignment is enforced.
□ Individual DDE authorization is enforced.
□ DDE tenant authorization is enforced.
□ No plaintext DDE credentials exist.
□ Readiness evaluations are immutable.
□ Evidence references are traceable.
□ Readiness actions are append-only.
□ Revenue events are append-only.
□ Corrections and reversals preserve originals.
□ Monetary values use fixed precision.
□ Dashboard totals deduplicate billable episodes.
□ Historical assignments remain preserved.
□ No cross-tenant query path exists.
□ No test artifacts remain after test execution.
□ Backup and restore verification succeeds.

==================================================
END DOCUMENT 1
==================================================

---

## Status

APPROVED TARGET ARCHITECTURE. Schema implementation requires
repository verification (Phase 0 discovery) before any migration is
written. No database changes have been made; this document is the
target architecture and migration sequencing plan only.

## Relationship to Other Documents

- Translates
  `docs/biller-platform/BILLING_DASHBOARD_IMPLEMENTATION_SPECIFICATION.md`
  and
  `docs/biller-platform/BILLING_READINESS_IMPLEMENTATION_SPECIFICATION.md`
  into concrete, verifiable database architecture; those documents
  remain the functional/calculation authority, this document is the
  schema and migration authority.
- Companion to
  `docs/biller-platform/BILLER_PLATFORM_IMPLEMENTATION_TASK_BREAKDOWN.md`,
  which sequences the phased implementation work (Phase 0 Discovery
  through Phase 17 Implementation Verification) that depends on this
  schema plan.
- Enforces the same Locked Branding and Locked Access Principle from
  the two implementation specifications and
  `docs/architecture/SNS_TECH_SOLUTIONS_PLATFORM_HIERARCHY.md`.
- Its Migration 3 (Individual DDE Authorization) and Section 8/9
  entities implement the DDE Visibility Rule from
  `docs/architecture/SNS_TECH_SOLUTIONS_PLATFORM_HIERARCHY.md` and the
  DDE authorization requirements in both implementation specifications.
- Its immutability rules (Sections 11, 14, 16, 20) are consistent with
  the Production Agency Data Immutability Rule in
  `docs/production/PRODUCTION_READINESS_CLEANUP_CHECKLIST.md`.
- Feeds the future
  `docs/biller-platform/BILLER_PLATFORM_DISCOVERY_REPORT.md` (Phase 0
  deliverable) and
  `docs/biller-platform/BILLER_PLATFORM_IMPLEMENTATION_VERIFICATION.md`
  (Phase 17 deliverable) defined in the companion task breakdown.

## Change Log

| Date | Change |
|---|---|
| 2026-09-16 | Document created — full database schema and migration plan: Non-Negotiable Database Rules, Phase 0 Required Repository Discovery, Logical Schema Map, 15 core entities (Billing Organization, Billing Organization Membership, Tenant Billing Assignment, User Tenant Billing Assignment, Individual DDE User Profile, DDE Tenant Authorization, Billable Episode, Readiness Evaluation, Readiness Condition, Readiness Evidence Reference, Readiness Action, Billing Work Item, Billing Revenue Event, DDE Operational Event, Regulatory Reference) with logical fields/constraints/indexes, Database-Level Tenant Isolation, Delete and Retention Behavior, a 14-step forward-only Migration Plan (Migration 0 Baseline Verification through Migration 13 Optional Current-State Projections), Migration Execution Gates (pre/execution/post-migration checklists), and full Schema Acceptance Criteria. Status: Approved Target Architecture; schema implementation requires repository verification before any migration is written. No code or database changes made. |
