# REPOSITORY GROUNDING CORRECTION REPORT

STATUS: REPOSITORY-GROUNDING CORRECTION IN PROGRESS — THIS REPORT
RECLASSIFIES PRIOR "REUSE" CLAIMS IN SECTIONS 18-27 OF
`BILLING_ORGANIZATION_DISCOVERY_REPORT.md` AGAINST VERIFIED REPOSITORY
EVIDENCE ONLY. NO MODEL, MIGRATION, ENUM, OR REPLACEMENT ENTITY WAS
CREATED WHILE PRODUCING THIS REPORT. PAYER/PLAN ARCHITECTURE WORK
REMAINS PAUSED UNTIL THIS CORRECTION IS REVIEWED.

## PURPOSE AND TRIGGER

While performing repository discovery for the newly-requested
"Configurable Payer and Plan" work (the two pending source documents:
"GitHub Discovery Package — Configurable Payers, Plans, Benefits, and
Billing Responsibility" and "Payer and Plan Architecture — Anti-
Duplication Lock"), a direct repository search (`grep`/model
inspection under `backend/app/`) surfaced that several table/model
names cited in Sections 18-27 of
`docs/biller-platform/BILLING_ORGANIZATION_DISCOVERY_REPORT.md` as
existing "REUSE" evidence **do not exist anywhere in the repository**
(no model class, no `__tablename__`, no Alembic migration, no
occurrence outside the discovery report itself).

Per explicit user instruction, this report:

1. Produces a repository-grounded inventory of the real models/tables
   that exist in the areas Sections 18-27 discuss.
2. Lists every claimed REUSE artifact from those sections.
3. Verifies whether each one actually exists.
4. Verifies whether the real artifact (where one exists under a
   different name) is functionally equivalent to what was claimed.
5. Reclassifies each item as REUSE / EXTEND / CREATE / DO NOT CREATE
   based only on verified repository evidence.

This report does **not** create any model, migration, enum, or
replacement entity. It also does not yet correct the prose of Sections
18-27 in place — that edit is a separate, subsequent step pending the
user's review of this correction report.

## METHOD

Verification was performed by:

- Listing all files under `backend/app/models/`, `backend/app/billing/models/`.
- Direct `view` of the full source of each model file relevant to
  Billing Organization / Organization & Teams / Agency Coverage /
  User Access Detail claims (Sections 18-27).
- Repository-wide case-insensitive text search (`grep`) for every
  backtick-quoted table/model/column identifier extracted from
  Sections 18-27, across `backend/app/` and `backend/alembic/`.
- Direct inspection of `app/core/permissions.py` to verify the
  `require_permission`/`has_permission` placeholder claim.

This is a **targeted, evidence-based spot-check of the artifacts that
most directly informed schema-design conclusions** in Sections 18-27
(the concrete table/model names cited as REUSE evidence for Agency
Coverage & Workload, Organization & Teams, Administrative Hierarchy,
Coverage Assignment/`coverage_role`, and User Access Detail /
Capability). It is not a line-by-line re-verification of every
sentence in a ~3,600-line document — that would be a materially larger
task and can be scoped separately if the user wants it.

## PART 1 — REPOSITORY-GROUNDED INVENTORY (WHAT ACTUALLY EXISTS)

Confirmed real models under `backend/app/billing/models/` and
`backend/app/models/` relevant to the claims under review:

| Real Model Class | Real Table | Key Fields (verified) | Notes |
|---|---|---|---|
| `BillingProviderOrganization` | `billing_provider_organizations` | `name` (unique), `organization_type`, `status` (ACTIVE/INACTIVE), `notes`, `updated_by` | This is the real Billing Organization entity. **No hierarchy/team fields of any kind exist on it.** |
| `BillingProviderOrganizationMembership` | `billing_provider_organization_memberships` | `billing_provider_organization_id`, `user_id`, `membership_role` (**only `MEMBER` or `ADMIN`**), `status` (ACTIVE/INACTIVE/SUSPENDED), `effective_start_at`/`effective_end_at`, `updated_by` | **No `reports_to`, `reports_to_id`, `reports_to_membership_id`, `superior_membership_id`, `subordinate_membership_id`, `level_label`, or any hierarchy-level field exists.** |
| `BillingProviderAgencyAssignment` | `billing_provider_agency_assignments` | `billing_provider_organization_id`, `tenant_id`, `relationship_status` (ACTIVE/SUSPENDED/TERMINATED/PENDING), `effective_start_at`/`effective_end_at`, `updated_by` | This is an **agency-to-billing-organization** relationship (which agencies a billing provider organization services), not a staff/coverage assignment. |
| `BillingProviderAgencyServiceScope` | `billing_provider_agency_service_scopes` | `assignment_id`, `scope` (one of `BILLING_PROVIDER_SERVICE_SCOPES`: BILLING_READINESS, CLAIMS, NOE_TRACKING, ELIGIBILITY, AUTHORIZATION_TRACKING, PAYMENT_POSTING, PAYMENT_RECONCILIATION, FACILITY_COLLECTIONS, CREDIT_BALANCES, AGING_REPORT, DENIALS_APPEALS, EDI, BILLING_REPORTS, FINANCIAL_MONITORING, CAP_MONITORING), `permission_level` (VIEW/EDIT) | This is a **service-scope/permission-level grant per agency assignment**, not a per-payer Coverage Assignment (Medicare Biller, Medi-Cal Biller, etc.). No payer/`claim_category`/`coverage_role` dimension exists on this table at all. |
| `AuditLog` | `audit_logs` | `tenant_id`, `request_id`, `user_id`, `role`, `action`, `entity_type`, `entity_id`, `description`, `event_metadata` (JSON), `created_at` | Real, generic, tenant-scoped, append-only audit table. This **is** a legitimate shared audit framework — but it is a generic `action`/`entity_type`/`entity_id` log, not the purpose-built `billing_agency_coverage_audit_events` table Section 27 cited. |
| `Claim` | `claims` | `tenant_id`, `patient_id`, `billing_cycle_id`, `edi_batch_id`, `payer_name` (free-text `String(255)`, nullable), `service_date`, `total_charge`, `total_units`, `risk_score`, `status` (READY/SENT/ACCEPTED/DENIED/PAID), `claim_control_number`, `exported_at` | **No `claim_category` column. No `payer_id`/`plan_id` FK. No payer-sequence (primary/secondary/tertiary) field.** Single free-text payer name per claim. |
| `ClaimExportLog` | (exists — `app/billing/models/claim_export_log.py`) | not fully re-inspected this pass | Confirmed to exist as a class; not further detailed here. |
| `FacilityPaymentAuditLog` | (exists — `app/billing/models/facility_payment_audit_log.py`) | not fully re-inspected this pass | Confirmed to exist as a class. |
| `Payer` | `payers` | `tenant_id`, `name` (unique), `code`, `payer_type` (free-text: e.g. `MEDICARE`/`MEDICAID`/`PRIVATE`/`HMO`/`PPO`), `status` (ACTIVE/INACTIVE) | Thin payer catalog; no aliases, no identifiers table, no supersession, no legal/display name split. |
| `PatientInsurance` | `patient_insurances` | `payer_type`, `payer_name` (free-text, **not FK to `Payer`**), `subscriber_id`, `group_number`, `coverage_scope` (HOSPICE/MEDICAL_GENERAL/PHARMACY/DENTAL/VISION/VA/OTHER), `priority_order`, `is_active`, `effective_date`/`end_date`, `verified_at`/`verified_by`, `eligibility_status` | |
| `PatientPayer` | `patient_payers` | `payer_name` (free-text), `payer_type` (free-text), `subscriber_id`, `msp_type_code`, `priority_order`, `is_primary`, `facility_name` | A **second, separate** patient-payer table that overlaps `PatientInsurance` — flagged as an existing duplication risk (Part 3). |
| `permissions.require_permission` / `permissions.has_permission` | `app/core/permissions.py` | `require_permission` returns an "authenticated user gate" dependency with a docstring literally stating "Placeholder for fine-grained permissions"; `has_permission(*args, **kwargs)` unconditionally `return True` | **Confirmed accurate** — Section 27's characterization of these as confirmed-unimplemented placeholders was correct and is not being corrected. |

Confirmed **NOT to exist anywhere in the repository** (no model, no
migration, no non-report text occurrence) despite being cited in
Sections 18-27 as REUSE evidence:

- `billing_agency_coverage_assignments`
- `billing_agency_team_assignments`
- `billing_agency_coverage_audit_events`
- `billing_agency_coverage_export_events`
- `billing_teams` (and `billing_team_id`, `billing_team_leader_assignments`, `billing_team_memberships`, `billing_team_supervisor_assignments`, `billing_supervisor_assignments`)
- `billing_administrative_hierarchy` / `billing_administrative_reporting_lines`
- `claim_category` (as a column, enum, or `CheckConstraint`)
- `coverage_role`
- `CapabilityAssignment` (class)
- `WorkforceCapability` (class)
- `payer_category_mapping`

## PART 2 — CLAIMED-REUSE-ARTIFACT VERIFICATION MATRIX

| # | Artifact Claimed (Section) | Claimed As | Exists? | Real Equivalent | Equivalent? | Corrected Classification |
|---|---|---|---|---|---|---|
| 1 | `billing_agency_coverage_assignments` (21, 22, 27) | REUSE — per-payer staff Coverage Assignment table | **NO** | None. Closest real table is `billing_provider_agency_service_scopes`, which stores *service scopes* (BILLING_READINESS, CLAIMS, etc.), not payer/claim-category coverage assignments (Medicare Biller, Medi-Cal Biller, etc.). | **NO** — different concept entirely (functional scope vs. payer responsibility). | **CREATE** (not yet designed against real schema; Sections 21/22/27's "REUSE" claim is retracted) |
| 2 | `billing_agency_team_assignments` (23, 27) | REUSE — Team Portfolio / Team Staffing Table backing store | **NO** | None. No team concept (Team Alpha/Team Beta) exists anywhere in the schema. | **NO** | **CREATE** (Section 23's "Team Portfolio Summary reuse"/"Team Staffing Table reuse" claims are retracted) |
| 3 | `billing_agency_coverage_audit_events` (27) | REUSE — payer/coverage-specific audit table | **NO** | `audit_logs` (`AuditLog`) is real, generic, tenant-scoped, append-only (`action`/`entity_type`/`entity_id`/`event_metadata`). | **PARTIAL** — the *pattern* (shared append-only audit) is real and reusable, but the specific named table is not. | **REUSE (of `audit_logs`, generic)** — not the named table claimed. Requires confirming `entity_type` values needed for coverage/capability events are actually populated by any existing service (not yet verified — open item, Part 4). |
| 4 | `billing_agency_coverage_export_events` (27) | REUSE — export-audit table | **NO** | No dedicated export-event table found for this domain. `AuditLog` could represent an export event generically (`action = "EXPORT"`), but no existing code path was found that writes one for this domain. | **NO** | **CREATE, or EXTEND `AuditLog` usage** (not yet designed) |
| 5 | `coverage_role` (21.2 discriminator) | REUSE — existing column name pattern | **NO** | No column by this name exists on any real table. | **NO** | **CREATE** (this was always described as a *proposed* schema element in Section 21, which is consistent — but Section 27/28.5 language sometimes referred to it as if it already existed on a real table; that framing is corrected here to "proposed, not yet created") |
| 6 | `claim_category` enum + `CheckConstraint` (20.9, 25.6, 25.10, 26, 28) | Described as a "locked" enum with an existing `CheckConstraint` | **NO** | `Claim.payer_name` is the only real payer-classification-adjacent field on `claims`, and it is free-text with no constraint. | **NO** | **CREATE.** The enum *value list* (12 values) and *display-label mapping* remain validly locked as a **design decision** (Sections 20.9/26.4/28 are correct as terminology/architecture decisions), but the document's framing that a `CheckConstraint` and column already exist in the schema is incorrect and is corrected here: **none of it has been implemented yet.** |
| 7 | `CapabilityAssignment` table/class (27) | REUSE — capability-assignment backing store | **NO** | No matching class found anywhere. | **NO** | **CREATE** — Section 27 itself already classified this as CREATE ("capability catalog/assignment tables (CREATE, unchanged)"), so no reclassification needed here; this row confirms that specific call was already correct. |
| 8 | `WorkforceCapability` (27, extracted token) | Ambiguous — appears once as an extracted token, not clearly asserted as REUSE | **NO** | No matching class found. | **NO** | **CREATE** (consistent with item 7; no correction needed to Section 27's own conclusion) |
| 9 | `billing_administrative_hierarchy` / `billing_administrative_reporting_lines` (24) | Discussed as the *target* table name for "Option B — Separate Administrative Hierarchy Relationship Table," **not** claimed as already existing | **NO** | No hierarchy table of any kind exists; `BillingProviderOrganizationMembership.membership_role` only supports `MEMBER`/`ADMIN`. | N/A — Section 24 never claimed this already existed; it was proposed schema design language for a future migration. | **CREATE (unchanged)** — Section 24's own status ("SCHEMA DESIGN REVIEW APPROVED... MIGRATION FILE CREATION... REMAIN BLOCKED") already correctly treated this as not-yet-created. No correction needed, but flagged here for completeness since the token appeared in the extraction. |
| 10 | `BillingProviderOrganization` / `BillingProviderOrganizationMembership` (21, 23, 27) | REUSE — Organization Membership backing store | **YES** | Confirmed real, matches Part 1 table above. | **PARTIAL** — the organization/membership *existence* is correctly REUSE, but membership_role's real value set (`MEMBER`/`ADMIN` only) is much thinner than the "System Role Definitions" (President, Billing Manager, Supervisor, Specialist, Member, etc.) and "Administrative Hierarchy" language in Sections 23/24 implied was already partially modeled. It is not — those richer roles are still fully CREATE/proposed. | **REUSE (existence only) + CREATE (richer role vocabulary and hierarchy)** — this nuance was not previously called out explicitly. |
| 11 | `BillingProviderAgencyAssignment` / `BillingProviderAgencyServiceScope` (18, 21, 27) | REUSE — Agency Assignment storage | **YES** | Confirmed real, matches Part 1 table above. | **YES, for what it actually models** (agency-to-organization relationship + functional service scope/permission level) — but it is **not** a payer/coverage-responsibility assignment, and Sections 21/22/27 sometimes used it interchangeably with the not-yet-existing `billing_agency_coverage_assignments`. | **REUSE (for agency-organization relationship + service scope only)** — corrected to make explicit this table cannot carry payer/`coverage_role`/Coverage Assignment data without an EXTEND or a new table. |
| 12 | `require_permission` / `has_permission` placeholders (Discovery Area 4, Section 27) | Confirmed-unimplemented placeholder authorization | **YES** | Confirmed real and accurately described (Part 1 table). | **YES** | **No correction needed — this claim was accurate.** |
| 13 | `AuditLog` / `audit_logs` (general shared-audit reuse claims across Sections 21-28) | REUSE — shared append-only audit infrastructure | **YES** | Confirmed real (Part 1 table). | **YES, generically** — it is real, tenant-scoped, and append-only, and can represent arbitrary `action`/`entity_type` events. | **REUSE confirmed** — this general claim (as distinct from the specific named tables in items 1-4) holds up. |
| 14 | `Payer` / `PatientInsurance` / `PatientPayer` / `Claim` (28.5, 29 — Payer/Plan work, not Sections 18-27) | Not part of the Sections 18-27 correction scope, but confirmed as part of this same discovery pass | **YES (all four)** | Confirmed real (Part 1 table). | **YES they exist**, but see Part 3 for a duplication-risk finding: `PatientInsurance` and `PatientPayer` appear to be two competing, partially-overlapping models for the same concept. | Out of scope for this correction (belongs to the paused Payer/Plan discovery); recorded here only as supporting evidence. |

## PART 3 — ADDITIONAL DUPLICATION-RISK FINDING (SURFACED INCIDENTALLY)

While verifying Payer/Plan-adjacent models for Part 1, a **second,
independent duplication risk** was found that is relevant to future
work (not part of the Sections 18-27 correction, but recorded here
since it was discovered during this same pass):

- `PatientInsurance` (`patient_insurances`) and `PatientPayer`
  (`patient_payers`) are **two separate, real, currently-coexisting
  tables** that both represent "a payer source a patient has,"
  each with its own `payer_name`/`payer_type`/`subscriber_id`/
  `priority_order` fields, and neither references the other or the
  `Payer` catalog table via foreign key.
- `ServiceCoverageDecision` (`service_coverage_decisions`) —
  a real model with `coverage_intent` (COMFORT/MAINTENANCE/CURATIVE/
  EXTERNAL), `financial_responsibility` (HOSPICE/INSURANCE/
  PATIENT_FAMILY), and `selected_payer_id` — references `PatientPayer`
  (not `PatientInsurance`), while `PayerEligibilityCheck` and
  `EligibilityVerification` reference `PatientInsurance` (not
  `PatientPayer`). This means the two competing patient-payer tables
  are each the system of record for a different part of the existing
  codebase, which is itself a live duplication/consolidation risk
  independent of any new Payer/Plan proposal.
- Two separate eligibility-check models also already coexist:
  `PayerEligibilityCheck` (`payer_eligibility_checks`, simpler,
  FK to `patient_insurance_id`) and `EligibilityVerification`
  (`eligibility_verifications`, richer, tri-state JSONB fields,
  append-only supersession via `superseded_at`, FK to
  `payer_coverage_id` → `patient_insurances`).

**This finding is out of scope for the Sections 18-27 correction and
is not being acted on in this report.** It is recorded here as
supporting repository evidence for whenever the paused Payer/Plan
discovery work resumes, per the Anti-Duplication Lock document's
"Data Consolidation Review" requirement — that work should treat
`PatientInsurance` vs. `PatientPayer` and `PayerEligibilityCheck` vs.
`EligibilityVerification` as its first two Duplication Gates once
resumed.

## PART 4 — OPEN ITEMS FROM THIS CORRECTION

1. **`AuditLog`/`audit_logs` reuse for coverage/capability events
   (item 3, Part 2) is not yet confirmed at the write-path level** —
   no service code was found in this pass that actually writes an
   `AuditLog` row for a coverage-assignment or capability-grant event
   today, because those write paths don't exist yet (the tables they'd
   write to are CREATE, not REUSE). This is expected, not a defect —
   flagged only so it isn't mistaken for confirmed end-to-end reuse.
2. **Sections 18-27's prose has not yet been edited in place.** This
   report is the correction *record*; a follow-up edit pass to
   Sections 18-27 themselves (replacing the retracted REUSE claims
   with corrected language and cross-references to this report) is a
   separate, subsequent step and has not been performed yet, pending
   the user's review of this report.
3. **This was a targeted verification of the concrete artifacts most
   load-bearing for schema-design conclusions**, not an exhaustive
   line-by-line re-read of all ~3,600 lines of Sections 18-27. If the
   user wants full exhaustive re-verification of every claim
   (including narrative/business-rule statements not tied to a
   specific table/column name), that is additional, explicitly
   separate scope.

## PART 5 — SUMMARY RECLASSIFICATION

| Concept | Prior Classification (Sections 18-27) | Corrected Classification |
|---|---|---|
| Billing Provider Organization | REUSE | **REUSE (confirmed accurate)** |
| Organization Membership (role: Member/Admin only) | REUSE | **REUSE (confirmed, but only for the thin Member/Admin role model — not for the richer System Role Definitions vocabulary, which remains CREATE)** |
| Agency Assignment (organization-to-agency + service scope) | REUSE | **REUSE (confirmed, but only for organization-agency relationship + functional service scope — not for payer/coverage responsibility, which remains CREATE)** |
| Coverage Assignment (per-payer staff responsibility, e.g. Medicare Biller) | REUSE (`billing_agency_coverage_assignments`) | **CREATE** (retracted — table does not exist) |
| Team Portfolio / Team Staffing (Team Alpha/Beta) | REUSE (`billing_agency_team_assignments`) | **CREATE** (retracted — table does not exist) |
| Administrative Hierarchy (Option B relationship table) | Already correctly CREATE/proposed | **CREATE (unchanged, no correction needed)** |
| Coverage/Capability Audit Events | REUSE (`billing_agency_coverage_audit_events`) | **REUSE of generic `audit_logs`, not the named table** (partial correction) |
| Export Events | REUSE (`billing_agency_coverage_export_events`) | **CREATE, or EXTEND generic `audit_logs` usage** (retracted as stated) |
| `claim_category` | Described as already schema-constrained (locked enum + CheckConstraint) | **CREATE — the enum value list and display-label decision remain valid as design/terminology, but no column, enum type, or constraint exists yet** |
| `coverage_role` | Implied existing column in places | **CREATE — proposed only, never implemented** |
| Capability Assignment / Workforce Capability | Already correctly CREATE | **CREATE (unchanged, no correction needed)** |
| Shared append-only audit framework (generic) | REUSE | **REUSE (confirmed accurate)** |
| `require_permission`/`has_permission` placeholders | Confirmed-unimplemented | **Confirmed-unimplemented (accurate, unchanged)** |

## STATUS

Documentation/correction only. No model, migration, enum, service,
route, or UI component was created, modified, or replaced while
producing this report. No prior discovery assumption was relied upon —
every classification above is grounded in a direct repository read
performed during this pass. Payer/Plan architecture work
(the two pending source documents) remains paused. Sections 18-27 of
`BILLING_ORGANIZATION_DISCOVERY_REPORT.md` have not yet been edited in
place to reflect these corrections — that is a follow-up step pending
user review of this report.
