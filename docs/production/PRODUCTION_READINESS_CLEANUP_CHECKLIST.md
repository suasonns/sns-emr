==================================================

SNS PRODUCTION READINESS CLEANUP CHECKLIST

==================================================

PURPOSE

Before SNS Hospice Solutions enters production or field testing, perform a complete platform sweep.

The objective is NOT to clean code.

The objective IS to ensure production contains only production-required assets, records, workflows, configurations, templates, and data.

Development artifacts must never be carried into production.

==================================================

SECTION 1

DATA HYGIENE SWEEP

==================================================

REMOVE

□ Test Patients

□ Test Agencies

□ Test Admissions

□ Test Visits

□ Test Assessments

□ Test RNICA Records

□ Test Narratives

□ Test AI Outputs

□ Test Referrals

□ Test Billing Records

□ Test Claims

□ Test DDE Test Entries

□ Test Alert Events

□ Test Security Events

□ Temporary Uploads

□ Debug Records

□ Experimental Records

□ Fake Documents

□ Seed Data No Longer Required

VERIFY

□ No test patient remains

□ No test documentation remains

□ No development-only records remain

□ No duplicate reference records remain

□ No orphaned attachments exist

□ No orphaned evidence records exist

□ No orphaned AI artifacts exist

□ No orphaned audit references exist

□ No test alerts linked to production records

□ No production records referencing test entities

==================================================

SECTION 2

TENANT CLEANUP

==================================================

VERIFY EACH TENANT

□ Production

□ Development

□ Training

□ Demo

□ Internal

REMOVE

□ Obsolete test tenants

□ Duplicate agencies

□ Abandoned agencies

□ Experimental tenants

VERIFY

□ Tenant ownership

□ Tenant status

□ Managed billing assignments

□ Platform assignments

□ Tenant ownership accurate

□ Tenant environment correctly classified

□ Tenant billing assignments correct

□ Tenant feature flags correct

□ Tenant branding correct

□ Tenant isolation validated

==================================================

SECTION 3

DOCUMENT CLEANUP

==================================================

REMOVE

□ Development PDFs

□ Development screenshots

□ Obsolete mock documents

□ Prototype forms

□ Temporary exports

VERIFY

□ Production templates intact

□ Production workflows intact

□ Production document libraries intact

□ No duplicate templates

□ No obsolete form versions

□ No development-only templates

□ No placeholder documents

□ No broken document links

==================================================

SECTION 4

ALERT CLEANUP

==================================================

REMOVE

□ Development alerts

□ Test alerts

□ Temporary system alerts

□ Expired debug alerts

VERIFY

□ Production alert rules only

□ Active workflows only

□ Alert categories valid

==================================================

SECTION 5

AI CLEANUP

==================================================

REMOVE

□ Experimental AI outputs

□ AI debugging artifacts

□ Temporary AI evidence

□ Obsolete embeddings

□ Obsolete vector records

VERIFY

□ Production prompts

□ Production models

□ Production workflows

□ Production evidence mappings

□ Production prompts loaded

□ Experimental prompts removed

□ Test AI workflows removed

□ Evidence mappings validated

□ Provenance tracking validated

□ AI outputs linked to sources

□ Confidence scoring functioning

□ AI navigation guidance functioning

==================================================

SECTION 6

AUDIT SHIELD VERIFICATION

==================================================

VERIFY

□ Evidence provenance operational

□ Source attribution operational

□ Audit history operational

□ Version history operational

□ Correction tracking operational

□ Immutable records operational

□ Source document opens correctly

□ Source page references function

□ Source attribution function

□ Historical corrections preserved

□ Reversal history preserved

□ Chain-of-custody preserved

□ User attribution preserved

□ Timestamp integrity preserved

VERIFY RANDOM SAMPLES

□ Source links open correctly

□ Evidence references valid

□ Historical records preserved

==================================================

SECTION 7

DATABASE CLEANUP

==================================================

IDENTIFY

□ Largest tables

□ Duplicate records

□ Orphaned records

□ Unused entities

□ Test-generated data

VERIFY

□ Referential integrity

□ Migration integrity

□ No broken foreign keys

□ No abandoned schemas

□ No abandoned migrations

□ No parallel schema versions

□ No deprecated tables

□ No unused indexes

□ No test schemas

□ No experimental databases

==================================================

SECTION 8

BACKUP HEALTH

==================================================

REQUIRED

□ Full backup completed

□ Backup verified

□ Restore test completed

□ Point-in-time recovery verified

□ Backup retention verified

VERIFY

□ Restore test performed on clean environment

□ Restore matches original data

□ Restore includes documents

□ Restore includes audit history

□ Restore includes AI evidence

□ Restore includes alerts

SNS MUST NEVER ENTER PRODUCTION WITHOUT A SUCCESSFUL RESTORE TEST.

Not backup.

Restore.

==================================================

SECTION 9

STORAGE INTELLIGENCE

==================================================

CAPTURE BASELINE

□ Current Database Size

□ Current Document Storage

□ Current Audit Storage

□ Current AI Storage

□ Current Backup Storage

TRACK

□ 30-Day Growth

□ 90-Day Growth

□ Projected Annual Growth

IDENTIFY

□ Largest storage consumers

□ Cleanup opportunities

□ Cost growth risks

□ Largest document consumers

□ Largest AI consumers

□ Largest audit consumers

□ Largest attachment consumers

VERIFY

□ Storage growth monitoring enabled

□ Cleanup candidates identified

□ Storage alert thresholds configured

==================================================

SECTION 10

SECURITY VERIFICATION

==================================================

VERIFY

□ RBAC functioning

□ Owner permissions functioning

□ Tenant isolation functioning

□ Managed billing isolation functioning

□ Authentication functioning

□ Password reset workflows functioning

□ MFA workflows functioning (if enabled)

□ Session management functioning

□ Audit logging functioning

□ Security event tracking functioning

□ Session timeout functioning

□ Permission inheritance functioning

□ Cross-platform access restrictions functioning

==================================================

SECTION 11

WORKFLOW VALIDATION

==================================================

Verify:

□ Admissions workflow

□ RNICA workflow

□ Finalization workflow

□ Alert workflow

□ Audit workflow

□ AI guidance workflow

□ Evidence harvester workflow

□ Navigation workflow

□ Tenant onboarding workflow

A production system can be technically healthy but operationally
broken — this section verifies actual end-to-end workflows function,
not just individual subsystems.

==================================================

SECTION 12

PRODUCTION APPROVAL

==================================================

NO PRODUCTION RELEASE UNTIL:

□ Data sweep completed

□ Tenant cleanup completed

□ Document cleanup completed

□ Alert cleanup completed

□ AI cleanup completed

□ Database cleanup completed

□ Full backup completed

□ Backup validated

□ Restore test validated

□ Point-in-time recovery validated

□ Audit Shield verified

□ Evidence provenance verified

□ Source attribution verified

□ Version history verified

□ Security verification completed

□ RBAC verified

□ Tenant isolation verified

□ Storage baseline captured

□ Growth tracking enabled

□ Production sign-off completed

==================================================

SECTION 13

PRODUCTION BASELINE SNAPSHOTS

==================================================

Capture and archive:

□ Database Size

□ Storage Usage

□ Audit Storage Usage

□ AI Storage Usage

□ Alert Count

□ Tenant Count

□ User Count

□ Active Agencies

These values become the production baseline for future growth tracking.

==================================================

SECTION 14

POST-GO-LIVE MONITORING

==================================================

Monitor:

□ Storage Growth

□ Alert Trends

□ System Incidents

□ Security Events

□ Failed Logins

□ Password Resets

□ Backup Success

□ Restore Readiness

Monitor for first 90 days after launch.

==================================================

FINAL RULE

==================================================

Production environments contain ONLY:

- Production configuration

- Production business rules

- Production templates

- Production workflows

- Production reference data

- Production agencies

- Production documentation

- Production audit history

Production environments DO NOT contain:

- Test patients

- Test agencies

- Test charts

- Test alerts

- Debug records

- Temporary development data

- Experimental AI artifacts

- Obsolete workflows

- Unused development assets

WHEN UNCERTAIN:

DO NOT DELETE.

Investigate first.

Verify ownership.

Verify dependencies.

Then remove only when confirmed unnecessary.

Production data is never destroyed without verification and documented approval.

==================================================

SECTION 15

DEVELOPMENT ARTIFACT DISCOVERY

==================================================

Identify:

□ Test tables

□ Debug tables

□ Temporary migrations

□ Development scripts

□ Deprecated feature flags

□ Experimental AI modules

□ Orphaned storage buckets

□ Temporary file uploads

For each item:

KEEP

REMOVE

REVIEW

No development artifact enters production without classification.

==================================================

SECTION 16

PRODUCTION BLOCKERS

==================================================

SNS MAY NOT ENTER FIELD TESTING OR PRODUCTION IF ANY OF THE FOLLOWING ARE TRUE.

DATA BLOCKERS

□ Test Patients Exist

□ Test Documentation Exists

□ Test Agencies Exist

□ Debug Data Exists

□ Experimental Records Exist

□ Orphaned Records Exist

□ Unclassified Development Data Exists

AUDIT SHIELD BLOCKERS

□ Evidence Provenance Not Working

□ Source Attribution Not Working

□ Source Navigation Not Working

□ Audit History Not Working

□ Version History Not Working

□ Correction Tracking Not Working

BACKUP BLOCKERS

□ Full Backup Missing

□ Backup Validation Failed

□ Restore Test Failed

□ Point-In-Time Recovery Failed

SECURITY BLOCKERS

□ Tenant Isolation Failed

□ RBAC Verification Failed

□ Authentication Failure

□ Audit Logging Failure

□ Security Event Tracking Failure

AI BLOCKERS

□ Production Prompts Not Verified

□ Evidence Mapping Failure

□ Provenance Failure

□ AI Workflow Failure

□ Clinical Intelligence Validation Not Completed

WORKFLOW BLOCKERS

□ RNICA Workflow Not Validated

□ Finalization Workflow Not Validated

□ Alert Workflow Not Validated

□ Navigation Workflow Not Validated

□ Evidence Harvester Workflow Not Validated

NO PRODUCTION RELEASE WHEN ANY BLOCKER IS PRESENT.

==================================================

SECTION 17

PRODUCTION SIGN-OFF CRITERIA

==================================================

REQUIRED APPROVAL AREAS

DATA

□ Data Hygiene Sweep Complete

□ Test Data Removed

□ Duplicate Data Removed

□ Orphaned Data Resolved

TENANTS

□ Tenant Review Complete

□ Tenant Isolation Verified

□ Managed Billing Assignments Verified

DOCUMENTS

□ Production Templates Verified

□ Production Libraries Verified

□ Document References Verified

AI

□ Clinical Intelligence Engine Verified

□ Evidence Harvester Verified

□ Source Attribution Verified

□ Guidance Workflows Verified

AUDIT SHIELD

□ Evidence Provenance Verified

□ Audit History Verified

□ Version History Verified

□ Correction Tracking Verified

SYSTEM HEALTH

□ Storage Baseline Captured

□ Growth Monitoring Enabled

□ Backup Health Verified

□ Restore Health Verified

SECURITY

□ RBAC Verified

□ Authentication Verified

□ Event Tracking Verified

FINAL AUTHORIZATION

□ Platform Owner Approval

□ Production Readiness Review Completed

==================================================

SECTION 18

FINAL PRE-PRODUCTION SWEEP SEQUENCE

==================================================

STEP 1

Freeze Development

- No new feature work

- No schema changes

- No migration changes

--------------------------------------------------

STEP 2

Data Hygiene Sweep

Remove:

- Test Patients

- Test Agencies

- Test Narratives

- Test Assessments

- Test Alerts

- Debug Records

- Experimental Records

Verify:

- No orphaned records

- No duplicate records

--------------------------------------------------

STEP 3

Tenant Review

Review:

- Production Tenants

- Development Tenants

- Training Tenants

- Internal Tenants

Validate:

- Status

- Ownership

- Assignments

--------------------------------------------------

STEP 4

Document Sweep

Remove:

- Development documents

- Mock content

- Temporary files

Verify:

- Templates

- Workflows

- References

--------------------------------------------------

STEP 5

AI Sweep

Remove:

- Experimental prompts

- Test AI outputs

- Debug evidence

Verify:

- Evidence Harvester

- Clinical Intelligence Engine

- Source Attribution

- Guidance Systems

--------------------------------------------------

STEP 6

Audit Shield Verification

Verify:

- Provenance

- Source Navigation

- Audit History

- Version History

- Correction History

--------------------------------------------------

STEP 7

Database Verification

Review:

- Largest tables

- Growth areas

- Storage consumers

Verify:

- Referential integrity

- Schema integrity

--------------------------------------------------

STEP 8

Backup Verification

Create:

- Full Backup

Perform:

- Full Restore Test

Verify:

- Patient Data

- Documents

- Audit History

- AI Evidence

- Alerts

SNS MUST NEVER GO LIVE WITHOUT A SUCCESSFUL RESTORE TEST.

--------------------------------------------------

STEP 9

Storage Baseline

Record:

- Database Size

- Document Storage

- Audit Storage

- AI Storage

- Backup Storage

Record largest storage consumers.

--------------------------------------------------

STEP 10

Security Verification

Verify:

- RBAC

- Tenant Isolation

- Authentication

- Audit Logging

- Security Events

--------------------------------------------------

STEP 11

Workflow Verification

Verify:

- RNICA

- Evidence Harvester

- Finalization

- Alerts

- Navigation

- Tenant Onboarding

--------------------------------------------------

STEP 12

Production Approval

Verify:

- No blockers remain

- All sign-offs completed

- Production package approved

Production deployment may proceed.

==================================================

FINAL PRINCIPLE

==================================================

PRODUCTION MUST CONTAIN ONLY:

- Production configuration

- Production templates

- Production workflows

- Production tenants

- Production reference data

- Production audit history

PRODUCTION MUST NOT CONTAIN:

- Test patients

- Test agencies

- Debug records

- Experimental records

- Temporary development artifacts

WHEN IN DOUBT:

VERIFY FIRST.

DOCUMENT DECISION.

THEN REMOVE.

==================================================

PRODUCTION ZERO-DATA REQUIREMENT

==================================================

Before first production release:

VERIFY

□ No patient records exist

□ No admissions exist

□ No visits exist

□ No RNICA records exist

□ No narratives exist

□ No billing records exist

□ No claims exist

□ No alerts generated from test data

□ No test agencies exist

□ No training agencies exist

□ No demo agencies exist

□ No experimental records exist

□ No development documents exist

□ No uploaded test files exist

Production must launch with:

Configuration = YES

Business Data = NO

Patient Data = NO

Clinical Data = NO

Billing Data = NO

Test Data = NO

==================================================

PRODUCTION SWEEP PASS / FAIL

==================================================

PASS ONLY IF:

Production Database contains:

- System Configuration

- Templates

- Workflows

- Roles

- Permissions

- Platform Settings

AND NOTHING ELSE

==================================================

PRODUCTION DATA MIGRATION STRATEGY

==================================================

FIRST PRODUCTION AGENCY

Love & Faith Hospice

PURPOSE

Love & Faith Hospice becomes the initial production tenant.

No other agency data may enter production until:

□ Production environment validated

□ Workflow validation completed

□ Backup validation completed

□ Restore validation completed

□ Audit Shield validation completed

==================================================

PRE-MIGRATION REQUIREMENTS

==================================================

VERIFY

□ Production sweep completed

□ Development artifacts removed

□ Test patients removed

□ Test documentation removed

□ Test agencies removed

□ Test alerts removed

□ Test AI artifacts removed

Production environment must be clean prior to migration.

==================================================

LOVE & FAITH MIGRATION VALIDATION

==================================================

AFTER MIGRATION VERIFY

□ Patient count matches source system

□ Admissions match source system

□ Visits match source system

□ Orders match source system

□ Certifications match source system

□ Attachments migrated

□ Narratives migrated

□ Audit records migrated

□ Evidence references valid

==================================================

POST-MIGRATION VALIDATION

==================================================

VERIFY

□ RNICA functions

□ Documentation functions

□ Finalization functions

□ Alerts function

□ Reporting functions

□ Audit history functions

□ Evidence provenance functions

==================================================

GO-LIVE REQUIREMENT

==================================================

Love & Faith Hospice becomes the first production validation agency.

Other agencies remain outside production until production stability is confirmed.

==================================================

ENVIRONMENT SEPARATION RULE

==================================================

sns_emr_dev_clean

Permanent Development Environment

This environment is never promoted to production.

This environment may contain:

- Test data

- Development data

- Experimental data

- Validation data

--------------------------------------------------

sns_emr_prod

Production Environment

Created fresh.

Never cloned from development.

Only production configuration is deployed.

Patient data enters production only through approved migration processes.

==================================================

PRODUCTION DATABASE STRATEGY

==================================================

Development Database

sns_emr_dev_clean

Purpose:

Permanent development, testing, AI experiments, workflow validation, migration validation, and future feature work.

This database is never promoted to production.

--------------------------------------------------

Production Database

sns_emr_prod

Purpose:

Permanent production environment.

Created fresh.

Starts with:

- System configuration

- Templates

- Workflows

- Roles

- Permissions

- Alert definitions

- AI configuration

Starts with:

NO patient data.

NO visit data.

NO assessment data.

NO billing data.

NO production records.

--------------------------------------------------

First Production Migration

Love & Faith Hospice

Love & Faith Hospice becomes the Production Validation Agency.

Migration is considered successful only when:

- Record counts match

- Attachments match

- Documents match

- Workflows function

- Audit history functions

- Backup and restore succeed

Only after Love & Faith validation may additional agencies be onboarded.

==================================================

TRAINING AND DEMONSTRATION DATA POLICY

==================================================

SNS prefers de-identified real-world data over synthetic data for:

- Workflow validation

- AI validation

- Evidence Harvester validation

- Clinical Intelligence validation

- RNICA validation

- Staff training

- Demonstration environments

Reason:

De-identified real-world data preserves:

- Clinical complexity

- Documentation noise

- Workflow irregularities

- Real-world edge cases

while protecting patient privacy.

---

## Status

Not started. This is a pre-production/pre-field-testing gate. Do not
mark any item complete until it has actually been verified/performed
against the real production-candidate environment. **Do not execute
any item in this checklist unless explicitly instructed** — this
document defines the requirement, it is not itself authorization to
run the sweep now.

## Relationship to Other Documents

- Mirrors and expands the high-level checklist in
  `docs/roadmap/Production-Readiness-Requirements.md` — that document
  is the roadmap-level summary; this document is the detailed,
  section-by-section execution checklist to actually run against a
  production candidate.
- Section 6 (Audit Shield Verification) and Section 10 (Security
  Verification) must be checked against the already-locked
  architecture in `/docs/architecture/` (`EVIDENCE_TRACEABILITY_VISION.md`,
  `ARCHITECTURE_LOCK.md`) and the existing audit/RBAC implementation
  documented in `docs/architecture/CERTIFICATION_READINESS_ARCHITECTURE.md`
  §1.1–1.2 (`backend/app/models/audit_log.py`, `backend/app/core/roles.py`)
  — verification confirms those systems still function after cleanup,
  it does not redefine them.
- Section 8 (Backup Health) applies the same rigor already used during
  this session's `sns_emr_dev` → `sns_emr_dev_clean` recovery: a
  successful **restore** test, not merely a backup file, is the bar.
- Section 12 (Production Approval) is the final go/no-go gate for the
  base sweep: no production release until every prior section's items
  are complete. Section 13/14 (baseline snapshots, 90-day post-go-live
  monitoring) extend past go-live itself and should be tracked against
  `docs/roadmap/Analytics-And-Agency-Health-Roadmap.md`'s
  storage/growth tracking concepts.
- The Final Rule's "when uncertain, do not delete" principle governs
  every section above — no removal in Sections 1–7 should ever proceed
  without verified ownership/dependencies and documented approval.
- Section 16 (Production Blockers) is the authoritative hard-stop list
  — if any blocker is present, release does not proceed regardless of
  how much of Sections 1–15 has been completed. Section 17 (Production
  Sign-Off Criteria) is the approval checklist a Platform Owner signs
  against. Section 18 (Final Pre-Production Sweep Sequence) is the
  literal step-by-step order of operations to execute all of the above
  — start to finish — when a production/field-testing release is
  actually being prepared.
- The Environment Separation Rule formalizes what `sns_emr_dev_clean`
  is: the permanent development database (currently active — see
  today's `dev.env`), which is never promoted to production. A future
  `sns_emr_prod` database must be created fresh, never cloned from
  development, with patient data entering only through the approved
  Production Data Migration Strategy above (Love & Faith Hospice as
  the first migrated agency).

## Change Log

| Date | Change |
|---|---|
| 2026-09-16 | Document created — full 18-section production readiness cleanup checklist, Production Blockers hard-stop list, Sign-Off Criteria, Final Pre-Production Sweep Sequence, Final Principle, Production Zero-Data Requirement, Production Sweep Pass/Fail gate, Production Data Migration Strategy (Love & Faith Hospice as first production validation agency), Environment Separation Rule (`sns_emr_dev_clean` permanent dev vs. fresh `sns_emr_prod`), consolidated Production Database Strategy, and Training and Demonstration Data Policy (de-identified real-world data preferred over synthetic data). |
