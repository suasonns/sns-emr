# Patient Census Zero-Result Investigation

Status: read-only investigation. No code, schema, or data changes made.

## 1. Database Contents

Direct SQL query against the live `sns_emr_dev` database:

| Table | Row count (entire table, all tenants) |
|---|---|
| `patients` | **0** |
| `admissions` | **0** |
| `patient_facesheet` | **0** |
| `referrals` | **0** |

There are no patient rows anywhere in the database — not filtered by
tenant, not filtered by status. This is the sole root cause: Patient
Census returns zero because there is zero patient data to return, for
every tenant, under any filter.

## 2. API Response

The Patient Census UI calls `GET /audit-dashboard/census`
(`app/api/audit_dashboard.py:182`, wired from
`sns-emr-frontend/src/api/census.ts:fetchCensusWorkspace`). Reading the
endpoint's query directly: it does a plain `FROM patients p ... WHERE
p.tenant_id = :tenant_id`. With 0 rows in `patients` globally, this query
returns 0 rows for **any** tenant_id, correctly. The endpoint, its SQL, and
its response shape are functioning exactly as designed — there is no bug
in the API layer.

## 3. Tenant Resolution

`_resolve_tenant_id()` (same file, lines ~44-64) resolves the effective
tenant strictly:

1. explicit `tenant_id` query param, else
2. `request.state.tenant_id` (set by tenant-routing middleware), else
3. `db.info["tenant_id"]`, else
4. the authenticated user's own `user.tenant_id`

...then enforces `user.tenant_id != resolved → 403 Tenant mismatch`. This
means a logged-in user can only ever query their own tenant's census — by
design. Checked against the current (post tenant-repair) user roster:

| Email | tenant_id | Tenant |
|---|---|---|
| `romel.suason@suasonns.org` | `cccccccc-...` | SNS Hospice Solutions |
| `rsuason@loveandfaithhospice.com` | `01271980-...` | Love & Faith Hospice Services, Inc. |
| `billing@sns.local` | `dddddddd-...` | North East Billing |

Each of these tenants correctly resolves to itself; each then queries
`patients` scoped to that tenant_id. Since `patients` has 0 rows for every
tenant_id in the table (the table is empty, full stop), tenant resolution
is not the cause — it is working correctly and is irrelevant to this zero
result.

## 4. Admission Filters

`get_audit_dashboard_census`'s `latest_admission` CTE filters
`FROM admissions a WHERE a.tenant_id = :tenant_id`. `admissions` has 0 rows
total, so this CTE also returns nothing for any tenant — again correctly
reflecting an empty table, not a filter defect.

## 5. Census Filters

The frontend (`PatientCensus.jsx`) applies bucket filters (`ALL` /
`ACTIVE` / `DISCHARGED` / `DECEASED` / `REVOKED`) purely client-side, over
whatever `census.patients` array the API already returned. With an empty
array from the API, every bucket filter necessarily shows 0 regardless of
which one is selected — the client-side filter logic is not implicated.

## Why the table is empty

`backend/scripts/` contains multiple patient-related scripts:
- `seed_acceptance_patient.py`, `seed_eligibility_admission_workflow_demo.py`, `seed_readiness_workflow_demo.py`, `seed_user_patient_assignments.py` — seed scripts capable of creating patient/admission data, none of which appear to have been run against this database (0 rows is consistent with none of them ever executing here).
- `remove_dummy_patients.py` — a *targeted* cleanup script that deletes only patients flagged `patient_type IN ('TRAINING','DEMO','TEST')`, `training_label = 'SYNTHETIC TEST DATA'`, or `mrn LIKE 'TEST-%'`. It does not wipe the whole table by design, so on its own it cannot fully explain 0 rows unless every patient that ever existed here was flagged that way.
- `cleanup_norma_test_data.py` — another scoped cleanup script (named after a specific test scenario), not a full-table wipe by name/intent.

The exact sequence of prior actions that left `patients` at 0 is not
determinable from current DB state alone (no row ever existed to inspect,
and no audit_logs entries reference patient creation/deletion in bulk).
What is certain: no patient data currently exists in this database, and no
seed script that creates realistic patient/admission records has been run
against it.

## Conclusion

Patient Census returns zero because **the database has zero patient
rows**, not because of a tenant-resolution defect, a broken API query, or
an incorrect filter. Database, API, tenant resolution, admission query,
and census filter logic were each checked independently and are all
functioning correctly against an empty `patients`/`admissions` dataset.

This is a data-seeding gap (same class of issue as the tenant conformance
finding), not a code defect. No fix has been applied — this is a report
only, per instruction.
