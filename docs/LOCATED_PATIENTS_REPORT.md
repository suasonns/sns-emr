# Located Patients Report: Loren, Kessler, Norma

Status: read-only investigation. No code or data modified.

## Method

Searched every Postgres database on the local server (26 databases total,
enumerated via `pg_database`), every `patients`/`patient_facesheet` table
found in each, plus checked for `deleted_at` (soft-delete), and any
archive/backup-named tables. Also checked the repository for related
seed/demo scripts as provenance context.

## Result Summary

All three patients exist, but **only in the `sns_emr_dev_clean` database
— not in `sns_emr_dev`**, the database the running application and both
worktrees' backends are currently configured to use (`DATABASE_URL` in
`dev.env`). `sns_emr_dev` has 0 rows in `patients` (confirmed in the prior
Patient Census report). None were soft-deleted (`deleted_at` is `NULL` on
all three) — they were never in the currently-connected database in the
first place.

## 1. Loren

| Field | Value |
|---|---|
| Where found | `sns_emr_dev_clean` database, `patients` + `patient_facesheet` tables (joined via `patient_id`) |
| Database name | `sns_emr_dev_clean` |
| Table name | `patients` (clinical row), `patient_facesheet` (name: "Loren Shields") |
| Patient id | `3ea2f6fa-8dd9-4e3c-9b7d-009ddbe17ab0` |
| MRN | `KP-000008733399` |
| Tenant id | `01271980-0000-0000-0000-000005101977` (Love & Faith Hospice Services, Inc.) |
| Status | `ACTIVE`, `patient_type = PRODUCTION` (not a training/demo fixture) |
| DOB | 1950-07-25 |
| `deleted_at` | `NULL` (not soft-deleted) |
| Notes | Repo has 3 backfill scripts referencing this patient by name (`backfill_loren_hope_comorbidities.py`, `backfill_loren_lcd_eligibility.py`, `backfill_loren_rnica_details.py`) plus `populate_loren_shields.py` — indicates this was a real, actively-developed clinical record, not disposable test data. |

## 2. Kessler

| Field | Value |
|---|---|
| Where found | `sns_emr_dev_clean` database, `patients` + `patient_facesheet` |
| Database name | `sns_emr_dev_clean` |
| Table name | `patients`, `patient_facesheet` (name: "Margaret Kessler") |
| Patient id | `ba24830e-19f8-4b84-bbf3-e88374a6db25` |
| MRN | `LFH-000002` |
| Tenant id | `01271980-0000-0000-0000-000005101977` (Love & Faith Hospice Services, Inc.) |
| Status | `PENDING`, `patient_type = PRODUCTION` |
| DOB | 1938-10-02 |
| `deleted_at` | `NULL` |

## 3. Norma

Two distinct records match "Norma":

**3a. Norma Suarez (real production record)**

| Field | Value |
|---|---|
| Where found | `sns_emr_dev_clean` database, `patients` + `patient_facesheet` |
| Database name | `sns_emr_dev_clean` |
| Table name | `patients`, `patient_facesheet` (name: "Norma Suarez") |
| Patient id | `53fe69e1-fcd5-4b49-8203-9b890b18b7d6` |
| MRN | `LFH-000003` |
| Tenant id | `01271980-0000-0000-0000-000005101977` (Love & Faith Hospice Services, Inc.) |
| Status | `PENDING`, `patient_type = PRODUCTION` |
| DOB | 1956-08-14 |
| `deleted_at` | `NULL` |

**3b. NORMA-TEST-0001 (separate training fixture, no facesheet name on file)**

| Field | Value |
|---|---|
| Where found | `sns_emr_dev_clean` database, `patients` table (no linked `patient_facesheet` row) |
| Database name | `sns_emr_dev_clean` |
| Table name | `patients` |
| Patient id | `4e305b73-3edc-4861-8100-db5521476dca` |
| MRN | `NORMA-TEST-0001` |
| Tenant id | `01271980-0000-0000-0000-000005101977` (Love & Faith Hospice Services, Inc.) |
| Status | `ACTIVE`, `patient_type = TRAINING` |
| Training label | "Disease-category regression fixture (Cancer). Real H&P, OCR'd." |
| `deleted_at` | `NULL` |
| Notes | `cleanup_norma_test_data.py` in `backend/scripts/` is a scoped cleanup script named for this fixture specifically. |

## Where They Were NOT Found

Checked and confirmed absent (query returned 0 matching rows) in all of:
`sns_emr_dev` (current, active DB), `sns_auth_test`, `sns_ci`,
`sns_emr_test`, `sns_emr_test_bf9e5385_5df40610`,
`sns_emr_test_bf9e5385_9a87c52c`, `sns_emr_test_f2557e20_8567d84f`,
`sns_emr_test_f2557e20_9b2eb361`, `sns_emr_test_f2557e20_fe3d3bc3`,
`sns_emr_test_pr59_isolated`, `sns_emr_test_reset_a`, `sns_emr_test_reset_b`,
`sns_ontology_recovery_readonly` (this DB doesn't even have a
`patient_facesheet` table — its `patients.full_name` column also had no
match). No dedicated archive/backup/soft-deleted tables exist anywhere on
the server (`information_schema.tables` search for `%archive%` /
`%backup%` / `%deleted%` returned nothing beyond ordinary
`patient_*` domain tables).

## What `sns_emr_dev_clean` Is

A second, separate Postgres database on the same local server, distinct
from `sns_emr_dev`. It already contains the correct 5 canonical tenants
(SNS Hospice Solutions, North East Billing, Love & Faith Hospice, Angela
Hospice, Silva Hospice) at the same UUIDs used in today's tenant repair,
plus a few additional legacy/demo tenants (`Billing Readiness Workflow Demo
Agency (DEV)`, `SNS Development Platform`, `SNS Development Agency`) not
present in `sns_emr_dev`. It is not referenced by name anywhere in
application code or `dev.env` — nothing currently points the running app
at it. It appears to be a manually-created snapshot/backup of a database
state that once had real patient and tenant data, taken independently of
the `sns_emr_dev` database the app is actually wired to today.

## Conclusion

Loren Shields, Margaret Kessler, and Norma Suarez (plus the separate Norma
training fixture) are not missing or deleted — they exist intact, with no
soft-delete markers, inside `sns_emr_dev_clean`. They are simply not in
the database (`sns_emr_dev`) the application currently connects to. This
is a database-selection/connection-target issue, not a data-loss event.
