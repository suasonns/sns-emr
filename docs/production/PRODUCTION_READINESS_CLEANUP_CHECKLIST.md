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

==================================================

SECTION 10

SECURITY VERIFICATION

==================================================

VERIFY

□ RBAC functioning

□ Owner permissions functioning

□ Tenant isolation

□ Tenant isolation functioning

□ Managed billing isolation functioning

□ Authentication functioning

□ Password reset workflows functioning

□ MFA workflows functioning (if enabled)

□ Session management functioning

□ Audit logging functioning

□ Security event tracking functioning

==================================================

SECTION 11

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

SECTION 12

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

SECTION 13

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

SECTION 14

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
- Section 11 (Production Approval) is the final go/no-go gate: no
  production release until every prior section's items are complete.
  Section 12/13 (baseline snapshots, 90-day post-go-live monitoring)
  extend past go-live itself and should be tracked against
  `docs/roadmap/Analytics-And-Agency-Health-Roadmap.md`'s
  storage/growth tracking concepts.
- The Final Rule's "when uncertain, do not delete" principle governs
  every section above — no removal in Sections 1–7 should ever proceed
  without verified ownership/dependencies and documented approval.

## Change Log

| Date | Change |
|---|---|
| 2026-09-16 | Document created — full 14-section production readiness cleanup checklist plus Final Rule. |
