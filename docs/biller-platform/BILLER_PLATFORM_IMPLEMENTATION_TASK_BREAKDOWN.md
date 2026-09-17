==================================================
DOCUMENT 2
==================================================

CREATE:

/docs/biller-platform/BILLER_PLATFORM_IMPLEMENTATION_TASK_BREAKDOWN.md

==================================================
SNS TECH SOLUTIONS
BILLER PLATFORM
IMPLEMENTATION TASK BREAKDOWN
==================================================

STATUS

APPROVED IMPLEMENTATION PLAN

ONE ACTIVE CURRENT PHASE AT A TIME

==================================================
1. EXECUTION RULES
==================================================

1. Only one phase may be marked CURRENT PHASE.

2. Do not begin the next phase until current-phase acceptance criteria pass.

3. Preserve separate sections for:

- Completed Work
- Open Defects
- Verification Evidence
- Current Phase
- Next-Phase Queue

4. Do not rewrite completed history.

5. Do not convert open defects into completed work without verification.

6. Do not use mock success responses where live persisted behavior is required.

7. Do not use synthetic monetary totals in production-facing code.

8. Keep approved Figma layout.

9. Do not redesign during implementation.

10. Apply VERIFY-FIRST before every migration.

11. Use forward-only repairs.

12. Do not use alembic stamp.

13. Do not leave tests, fixtures, debug records, or experimental data in persistent shared databases.

==================================================
PHASE 0
REPOSITORY AND DATABASE DISCOVERY
==================================================

STATUS:

CURRENT PHASE

TASKS

□ Locate Biller Dashboard route and components.
□ Locate Billing Readiness route and components.
□ Locate tenant context provider.
□ Locate authentication and authorization enforcement.
□ Locate billing organization models.
□ Locate user and role models.
□ Locate tenant assignment models.
□ Locate claim and billable-period models.
□ Locate NOE models.
□ Locate eligibility models.
□ Locate certification and order models.
□ Locate denial and appeal models.
□ Locate payment and remittance models.
□ Locate billing-readiness logic.
□ Locate revenue calculation logic.
□ Locate audit event infrastructure.
□ Locate evidence provenance infrastructure.
□ Locate current DDE structures.
□ Inspect Alembic graph.
□ Verify database current revision and head.
□ Verify ORM/database alignment.
□ Produce REUSE / EXTEND / CREATE matrix.
□ Identify approved Figma components that already exist.
□ Identify exact files expected to change.

DELIVERABLE

/docs/biller-platform/BILLER_PLATFORM_DISCOVERY_REPORT.md

BLOCKERS

- Unknown migration head
- Multiple unexpected migration heads
- Schema drift
- Unknown database identity
- Uncommitted migration changes
- Unclassified existing models

EXIT CRITERIA

□ Discovery report complete.
□ Every logical entity classified.
□ Current migration state verified.
□ No unresolved schema drift.
□ Exact implementation surface documented.

==================================================
PHASE 1
ASSIGNMENT-BASED ACCESS FOUNDATION
==================================================

TASKS

□ Reuse or implement billing organization.
□ Reuse or implement billing organization membership.
□ Reuse or implement tenant billing assignment.
□ Reuse or implement individual tenant biller assignment.
□ Enforce assignment expiration.
□ Implement assigned-agency selector.
□ Implement server-side assignment guards.
□ Implement Assigned Agency Registry.
□ Add production, training, and demo badges.
□ Audit tenant switching.
□ Add cross-tenant denial tests.
□ Add cache isolation tests.

EXIT CRITERIA

□ Billers see assigned agencies only.
□ URL manipulation cannot expose other tenants.
□ Agency switching clears previous tenant information.
□ Expired assignments stop access.
□ Historical activity remains preserved.
□ No cross-tenant cache leakage exists.

==================================================
PHASE 2
INDIVIDUAL DDE AUTHORIZATION FOUNDATION
==================================================

TASKS

□ Reuse or implement DDE user profile.
□ Reuse or implement DDE tenant authorization.
□ Associate DDE user with billing organization.
□ Associate DDE authorization with assigned tenant.
□ Add verification, suspension, expiration, and revocation states.
□ Add DDE authorization display to Authorized Scope.
□ Prevent DDE action without individual authorization.
□ Prevent plaintext credential persistence.
□ Add DDE authorization audit events.
□ Add DDE scope tests.

EXIT CRITERIA

□ DDE authorization belongs to an individual.
□ Individual remains within authorized billing group context.
□ DDE tenant authorization is required.
□ Non-authorized users cannot perform DDE operations.
□ No credentials appear in logs, UI, exports, or database fields.
□ Authorization changes are auditable.

==================================================
PHASE 3
AUTHORITATIVE BILLABLE EPISODE AND REVENUE MODEL
==================================================

TASKS

□ Identify authoritative claim or billing-period unit.
□ Add billable episode only if no equivalent exists.
□ Enforce tenant/patient consistency.
□ Enforce monetary precision.
□ Prevent duplicate billable episodes.
□ Define authoritative amount source.
□ Define voided, superseded, reversed, submitted, accepted, paid, and denied states.
□ Implement revenue-state service.
□ Add deduplication tests.
□ Document calculation formulas.

EXIT CRITERIA

□ One authoritative deduplication unit exists.
□ Monetary totals use decimal arithmetic.
□ Duplicate claims do not inflate totals.
□ Revenue states are explicit.
□ Calculation formulas are documented.

==================================================
PHASE 4
READINESS EVALUATION ENGINE
==================================================

TASKS

□ Implement immutable readiness evaluations.
□ Preserve ruleset version.
□ Preserve source snapshot reference.
□ Implement superseding evaluations.
□ Implement current-evaluation resolution.
□ Implement readiness states:
   - Not Ready
   - In Progress
   - Awaiting External
   - Ready To Bill
   - Submitted
   - Paid
□ Add concurrency and duplicate-evaluation protection.
□ Add historical evaluation view.
□ Add evaluation audit events.

EXIT CRITERIA

□ Recalculation creates a new evaluation.
□ Prior evaluations remain accessible.
□ Current evaluation resolves deterministically.
□ Paid is the terminal lifecycle display state.
□ Ruleset version and actor are preserved.

==================================================
PHASE 5
READINESS CONDITIONS AND EVIDENCE
==================================================

TASKS

□ Implement readiness condition types.
□ Implement blocking levels.
□ Implement owner categories.
□ Implement due dates and severity.
□ Implement evidence references.
□ Reuse Evidence Harvester provenance where authoritative.
□ Support source document, page, line, date, author, and structured source reference.
□ Implement readiness action history.
□ Require reasons for overrides and waivers.
□ Implement guided navigation targets.
□ Implement revalidation action.
□ Add approved regulatory-reference linking.

EXIT CRITERIA

□ Every blocker explains what is wrong.
□ Every blocker identifies ownership.
□ Every blocker explains revenue impact.
□ Every blocker has a resolution path.
□ Evidence sources are traceable.
□ Signed clinical records are never silently modified.
□ Corrections follow authorized correction or addendum workflow.

==================================================
PHASE 6
DDE OPERATIONAL EVENTS AND READINESS MAPPING
==================================================

TASKS

□ Implement DDE operational event types.
□ Map DDE events to readiness conditions.
□ Add DDE verification required.
□ Add DDE eligibility conflict.
□ Add DDE response pending.
□ Add DDE status unknown.
□ Add DDE submission failure.
□ Add DDE exception creation and resolution.
□ Add amount impacted.
□ Add assigned DDE user.
□ Add days outstanding.
□ Add resolution path.
□ Implement DDE Health Status source.
□ Display Unknown when no authoritative live health source exists.
□ Add DDE audit history.

EXIT CRITERIA

□ DDE blockers affect readiness calculations.
□ DDE Submission Failure can block progression.
□ DDE responses appear in work queues.
□ DDE Health never displays fabricated Online status.
□ DDE exception resolution preserves original history.
□ DDE operations require active individual authorization.

==================================================
PHASE 7
BILLING WORK QUEUES AND ACCOUNTABILITY
==================================================

TASKS

□ Implement or extend billing work items.
□ Prevent duplicate active work items.
□ Build Today's Work Queue.
□ Build Revenue Unlock Priorities.
□ Build Assignment Accountability.
□ Add team ownership.
□ Add individual assignment where authorized.
□ Add deadlines.
□ Add escalation.
□ Add past-due counts.
□ Add guided resolution actions.
□ Prevent billers from completing clinical or physician obligations.
□ Add work-item audit events.

EXIT CRITERIA

□ Work items link to authoritative source records.
□ Duplicate work items are prevented.
□ Clinical actions remain attributable to clinical actors.
□ Biller may request, assign, escalate, and revalidate.
□ Priority logic is explainable.
□ No employee performance scores are generated.

==================================================
PHASE 8
REVENUE CALCULATION SERVICE
==================================================

TASKS

□ Implement Ready Revenue.
□ Implement Blocked Revenue.
□ Implement Revenue At Risk.
□ Implement Partially Ready Revenue.
□ Implement Revenue Unlock Opportunity.
□ Implement Pending Payments.
□ Implement Denied Revenue.
□ Implement Recovery Opportunities.
□ Implement DDE revenue impact.
□ Implement category overlap disclosure.
□ Add as-of timestamp.
□ Add ruleset version.
□ Add calculation trace output for debugging and audit.
□ Add deduplication and overlap tests.

EXIT CRITERIA

□ Headline totals are deduplicated.
□ Category overlap is disclosed.
□ Blocked and At Risk values do not silently double count.
□ Submitted and Paid are excluded from Ready Revenue.
□ Unlock Opportunity requires a valid resolution path.
□ Calculations match between Dashboard and Readiness.

==================================================
PHASE 9
BILLING READINESS API
==================================================

TASKS

□ Build one tenant-scoped readiness summary endpoint or approved equivalent.
□ Build work-queue endpoint.
□ Build readiness-breakdown endpoint.
□ Build revenue-at-risk endpoint.
□ Build assignment-accountability endpoint.
□ Build authorized-scope endpoint.
□ Build assigned-agency endpoint.
□ Build DDE Health endpoint.
□ Build activity-feed endpoint.
□ Build guided-resolution actions.
□ Add pagination.
□ Add stale-data indicators.
□ Add correlation IDs.
□ Add authorization tests.

EXIT CRITERIA

□ APIs are tenant scoped.
□ APIs enforce assignment server-side.
□ DDE APIs enforce individual authorization.
□ No clinical narrative is loaded unnecessarily.
□ Empty, stale, loading, and error contracts are defined.
□ All endpoints have automated tests.

==================================================
PHASE 10
BILLING READINESS UI
==================================================

TASKS

□ Apply SNS Tech Solutions branding.
□ Preserve Biller Platform label.
□ Display SNS Hospice Solutions tenant context.
□ Implement top revenue cards.
□ Implement Revenue Readiness Overview.
□ Implement DDE Health Status.
□ Implement Today's Work Queue.
□ Implement Readiness Pipeline.
□ Implement Revenue Unlock Forecast.
□ Implement Revenue Unlock Priorities.
□ Implement Readiness Breakdown.
□ Implement Assignment Accountability.
□ Implement Authorized Scope.
□ Implement Assigned Agency Registry.
□ Implement Revenue At Risk.
□ Implement Activity Feed.
□ Implement guided navigation prompts.
□ Implement responsive layout.
□ Implement loading skeletons.
□ Implement empty states.
□ Implement error states.
□ Implement stale-data warning.
□ Compare to locked Figma.

EXIT CRITERIA

□ Layout matches approved Figma.
□ Cards remain readable at supported widths.
□ DDE Health is visible.
□ User can locate the largest blocker quickly.
□ User can identify who owns the fix.
□ User can identify revenue unlock opportunity.
□ No unassigned agency appears.

==================================================
PHASE 11
BILLING DASHBOARD API
==================================================

TASKS

□ Build dashboard summary endpoint or approved scoped aggregation.
□ Build revenue-pipeline endpoint.
□ Build cash-forecast contract.
□ Build collections-summary endpoint.
□ Build denial-health endpoint.
□ Build top-denial-reasons endpoint.
□ Build DDE exception summary.
□ Build billing-priorities endpoint.
□ Build Recent Billing Events and Releases endpoint.
□ Reuse Billing Readiness calculations.
□ Do not implement duplicate dashboard formulas.
□ Add cross-page consistency tests.

FORECAST RULE

If no approved forecasting methodology exists:

- Do not fabricate forecast values.
- Return unavailable with reason.
- Do not display invented confidence percentages.

EXIT CRITERIA

□ Dashboard and Readiness share authoritative calculation services.
□ Dashboard values are persisted or authoritatively calculated.
□ No mock financial data is presented as real.
□ Forecast methodology is documented or unavailable.
□ Performance tests pass.

==================================================
PHASE 12
BILLING DASHBOARD UI
==================================================

TASKS

□ Apply SNS Tech Solutions branding.
□ Display current assigned tenant.
□ Implement Executive Revenue Summary.
□ Implement Today's Work Queue.
□ Implement Billing Priorities.
□ Implement Cash Forecast.
□ Implement Revenue Pipeline.
□ Implement Collections Summary.
□ Implement Revenue At Risk.
□ Implement Denial Health.
□ Implement Top Denial Reasons.
□ Implement Assigned Visibility.
□ Implement Assigned Agency Registry.
□ Implement DDE Exceptions.
□ Implement Recent Billing Events and Releases.
□ Implement loading, empty, error, and stale states.
□ Compare to locked Figma.

EXIT CRITERIA

□ Layout matches approved Figma.
□ DDE is visible.
□ Assigned agencies only are displayed.
□ User can identify revenue, risk, and priority quickly.
□ Dashboard links open matching filtered workflows.
□ No Owner Platform data appears.

==================================================
PHASE 13
AUDIT, IMMUTABILITY, AND CORRECTION
==================================================

TASKS

□ Audit page access.
□ Audit agency switching.
□ Audit exports.
□ Audit claim release.
□ Audit work assignment.
□ Audit work resolution.
□ Audit DDE review.
□ Audit DDE exception resolution.
□ Audit manual override.
□ Audit revenue-state change.
□ Implement correction events.
□ Implement reversal events.
□ Verify no destructive update rewrites history.
□ Verify correlation IDs.
□ Verify no secrets in audit logs.

EXIT CRITERIA

□ Actor, role, tenant, action, source, previous state, new state, reason, and timestamp are preserved.
□ Original records survive corrections.
□ Revenue events are append-only.
□ DDE events are append-only.
□ No credentials appear in logs.

==================================================
PHASE 14
SECURITY AND TENANT ISOLATION
==================================================

TASKS

□ Test URL manipulation.
□ Test request-body tenant substitution.
□ Test query-parameter substitution.
□ Test client-storage tampering.
□ Test identifier enumeration.
□ Test expired assignment.
□ Test revoked DDE authorization.
□ Test cross-tenant cache.
□ Test export scope.
□ Test background-job scope.
□ Test read-only auditor restrictions.
□ Test Platform Owner authority without routine assignment.

EXIT CRITERIA

□ No cross-tenant access exists.
□ No unassigned agency metadata leaks.
□ DDE scope cannot be bypassed.
□ Export scope matches UI scope.
□ Cache keys include tenant and permission context.

==================================================
PHASE 15
PERFORMANCE AND RELIABILITY
==================================================

TASKS

□ Eliminate N+1 queries.
□ Add reviewed indexes.
□ Analyze dashboard query plans.
□ Analyze readiness query plans.
□ Paginate activity.
□ Avoid patient narrative retrieval.
□ Add safe cache invalidation.
□ Add retry behavior for approved external sync.
□ Add stale-data behavior.
□ Add DDE unavailable behavior.
□ Verify concurrent readiness recalculation.
□ Verify concurrent assignment change.

EXIT CRITERIA

□ Query plans use expected indexes.
□ Tenant scope is present in database access paths.
□ Page does not execute one query per card.
□ Stale data is disclosed.
□ External failure does not corrupt local state.

==================================================
PHASE 16
TESTING AND CLEANUP
==================================================

TASKS

□ Run unit tests.
□ Run integration tests.
□ Run UI tests.
□ Run data-isolation tests.
□ Run migration tests.
□ Run backup test.
□ Run restore test.
□ Run cross-page consistency tests.
□ Run DDE permission tests.
□ Run calculation tests.
□ Remove all test-created records.
□ Remove debug artifacts.
□ Verify no fixture data remains in shared persistent database.
□ Verify database growth after testing.
□ Document any cleanup performed.

EXIT CRITERIA

□ All required tests pass.
□ Restore test succeeds.
□ No test artifacts remain.
□ No unexplained data remains.
□ No schema drift exists.
□ Alembic current matches expected head.

==================================================
PHASE 17
IMPLEMENTATION VERIFICATION
==================================================

CREATE:

/docs/biller-platform/BILLER_PLATFORM_IMPLEMENTATION_VERIFICATION.md

REQUIRED CONTENT

- Completed work
- Open defects
- Verification evidence
- Current migration head
- Files changed
- Models reused
- Models extended
- Models created
- Migrations created
- Constraints added
- Indexes added
- API routes
- Permission enforcement
- Calculation formulas
- DDE authorization behavior
- DDE readiness mapping
- Audit events
- Test commands
- Test results
- Backup result
- Restore result
- Test cleanup result
- Storage impact
- Known limitations
- Deferred enhancements
- Figma comparison
- Cross-page consistency result
- Cross-tenant isolation result

FINAL DECLARATIONS

□ No alembic stamp used.
□ No unsafe automigration used.
□ No historical migration rewritten.
□ No cross-tenant access found.
□ No test artifacts remain.
□ No mock financial values presented as production data.
□ Billing Dashboard matches approved Figma.
□ Billing Readiness matches approved Figma.
□ DDE is active in readiness and dashboard architecture.
□ Branding displays SNS Tech Solutions.
□ Assigned Agency Registry lists only assigned agencies.

==================================================
FINAL IMPLEMENTATION BLOCKERS
==================================================

DO NOT DECLARE COMPLETE IF:

- Schema discovery is incomplete
- Migration head is unknown
- Schema drift exists
- Revenue formulas conflict across pages
- DDE authorization is organization-wide instead of individual
- Cross-tenant access exists
- Tests leave persistent records
- Restore testing fails
- History is overwritten
- Financial totals use floating point
- Mock values appear as real
- Approved Figma sections are missing
- SNS Hospice Solutions is incorrectly used as Biller Platform owner branding

==================================================
FINAL LOCK
==================================================

SNS Tech Solutions Branding:
LOCKED

Biller Platform Architecture:
LOCKED

Billing Dashboard Design:
LOCKED

Billing Readiness Design:
LOCKED

Assignment-Based Tenant Visibility:
LOCKED

Individual DDE Authorization Within Billing Group:
LOCKED

DDE Readiness Integration:
LOCKED

Immutable Evaluation and Revenue History:
LOCKED

Future changes must be explicitly approved enhancements.

No architectural redesign during implementation.

---

## Status

APPROVED IMPLEMENTATION PLAN. Only one phase may be marked CURRENT
PHASE at a time; Phase 0 (Repository and Database Discovery) is
currently marked CURRENT PHASE. No implementation work (code,
migrations, or feature changes) has been performed as part of creating
this document — this is the planning artifact that will govern future
implementation work, phase by phase, once explicitly kicked off.

## Relationship to Other Documents

- Sequences the implementation of
  `docs/biller-platform/BILLING_DASHBOARD_IMPLEMENTATION_SPECIFICATION.md`
  and
  `docs/biller-platform/BILLING_READINESS_IMPLEMENTATION_SPECIFICATION.md`
  into 18 phases (Phase 0 through Phase 17).
- Depends on
  `docs/biller-platform/BILLER_PLATFORM_DATABASE_SCHEMA_AND_MIGRATION_PLAN.md`
  for the underlying schema and forward-only migration sequence
  referenced throughout Phases 1-9.
- Phase 0's deliverable,
  `docs/biller-platform/BILLER_PLATFORM_DISCOVERY_REPORT.md`, and
  Phase 17's deliverable,
  `docs/biller-platform/BILLER_PLATFORM_IMPLEMENTATION_VERIFICATION.md`,
  are both future documents not yet created.
- Enforces the same Locked Branding, Locked Access Principle, and DDE
  individual-authorization rules established in
  `docs/architecture/SNS_TECH_SOLUTIONS_PLATFORM_HIERARCHY.md` and both
  implementation specifications.
- The Final Lock section restates and extends the LOCKED status
  already established in
  `docs/biller-platform/BILLER_PLATFORM_LOCKED_SPECIFICATIONS.md`.

## Change Log

| Date | Change |
|---|---|
| 2026-09-16 | Document created — full implementation task breakdown: Execution Rules, and 18 phases (Phase 0 Repository and Database Discovery [marked CURRENT PHASE] through Phase 17 Implementation Verification), each with tasks and exit criteria: Phase 1 Assignment-Based Access Foundation, Phase 2 Individual DDE Authorization Foundation, Phase 3 Authoritative Billable Episode and Revenue Model, Phase 4 Readiness Evaluation Engine, Phase 5 Readiness Conditions and Evidence, Phase 6 DDE Operational Events and Readiness Mapping, Phase 7 Billing Work Queues and Accountability, Phase 8 Revenue Calculation Service, Phase 9 Billing Readiness API, Phase 10 Billing Readiness UI, Phase 11 Billing Dashboard API, Phase 12 Billing Dashboard UI, Phase 13 Audit/Immutability/Correction, Phase 14 Security and Tenant Isolation, Phase 15 Performance and Reliability, Phase 16 Testing and Cleanup, Phase 17 Implementation Verification. Plus Final Implementation Blockers and the shared Final Lock statement. Status: Approved Implementation Plan; Phase 0 is the current phase; no implementation work performed by creating this document. |
