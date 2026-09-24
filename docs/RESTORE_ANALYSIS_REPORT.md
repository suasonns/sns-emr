# Analysis: Would Switching DATABASE_URL to sns_emr_dev_clean Restore the Missing Data?

Status: analysis only. No files modified, no restart performed, no code
changed.

## Direct Answer

**Yes — switching `DATABASE_URL` from `sns_emr_dev` to `sns_emr_dev_clean`
would restore all four items**, based on the following verified evidence.

## 1. Schema Compatibility (no migration risk)

```
sns_emr_dev        alembic_version = um2d1c2c3o5u9
sns_emr_dev_clean  alembic_version = um2d1c2c3o5u9
```

Both databases are on the **exact same migration head**. The current
codebase (including the PR91 Staff & Access / RBAC schema merged earlier
this session) is already compatible with `sns_emr_dev_clean` — no
migration would need to run, and no schema mismatch risk exists.

## 2. Loren Shields

Present: `patients` row (mrn `KP-000008733399`, tenant
`01271980-...` = Love & Faith Hospice, status `ACTIVE`), with a
`patient_facesheet` row giving the name, and a matching `admissions` row
(status `ACTIVE`). Would be returned by the census query (see #5).
**Would be restored.**

## 3. Margaret Kessler

Present: `patients` row (mrn `LFH-000002`, same tenant, status `PENDING`),
`patient_facesheet` row, and a matching `admissions` row (status
`PENDING`). **Would be restored.**

## 4. Norma Suarez

Present: `patients` row (mrn `LFH-000003`, same tenant, status `PENDING`),
`patient_facesheet` row. No matching `admissions` row was found in a
direct join, but the census query's admission join is a `LEFT JOIN`
(optional, supplementary fields only) — her core patient/facesheet row is
sufficient for her to appear in the census list, just without an
admission date populated. **Would be restored** (with a possibly-empty
"Admission Date" column).

## 5. Patient Census

Read the full `/audit-dashboard/census` SQL directly: the query selects
`FROM patients p ... WHERE p.tenant_id = :tenant_id`, with an admission
join that is a `LEFT JOIN` (never excludes a patient) and no `status`/
`patient_status` filter of any kind — every patient row for the resolved
tenant is returned, regardless of `PENDING`/`ACTIVE`/other status. The
only additional restriction is role-based (`restrict_to_assigned_rn`),
which only applies to plain RN accounts, not `DPCS_ADMINISTRATOR`/`OWNER`
(both have `VIEW_ALL_TENANT_PATIENTS`). Given the currently-configured dev
login `rsuason@loveandfaithhospice.com` is `DPCS_ADMINISTRATOR` at tenant
`01271980-...`, it would see the tenant's full patient list — all 8
patients under that tenant in `sns_emr_dev_clean`, including Loren,
Kessler, and Norma. **Would be restored.**

## 3 Additional Risk/Continuity Checks (all clear)

- **Login continuity:** the 3 dev-login accounts currently used
  (`romel.suason@suasonns.org` / OWNER, `rsuason@loveandfaithhospice.com` /
  DPCS_ADMINISTRATOR, `billing@sns.local` / BILLING) already exist in
  `sns_emr_dev_clean`, at the *same* tenant IDs currently configured in
  `dev.env`, each with an existing password hash. `admin_bootstrap_service`
  re-syncs these accounts' passwords from `dev.env`'s `DEV_*_PASSWORD`
  values on every backend startup, so logging in with the same current
  credentials would continue to work without any additional change.
- **Tenant ID continuity:** `sns_emr_dev_clean` already has all 5 canonical
  tenants (SNS Hospice Solutions, North East Billing, Love & Faith
  Hospice, Angela Hospice, Silva Hospice) at the identical UUIDs already
  in use — no tenant remapping would be needed.
- **No conflicting/duplicate placeholder tenants:** `sns_emr_dev_clean`
  additionally contains 3 older tenants not in the current roster
  (`Billing Readiness Workflow Demo Agency (DEV)`, `SNS Development
  Platform`, `SNS Development Agency`) — these would simply become visible
  again alongside the 5 canonical ones; they don't block or conflict with
  anything.

## Side Effect Worth Noting (not a blocker)

`sns_emr_dev_clean` contains substantially more historical data than
`sns_emr_dev` currently does: 30 `users` rows (vs. 3) and 10 `admissions`
rows (vs. 0), reflecting real prior development/testing activity (QA
automation accounts, smoke-test accounts, additional staff, etc.). Pointing
at it would surface all of that, not just the 3 named patients — expected
and desired given it's the actual historical dev database, but flagged
here since it's a larger surface area than "just these 3 patients."

## Conclusion

Yes. Based on direct, read-only verification of schema version, tenant
IDs, user accounts, and the exact SQL the Patient Census endpoint runs,
changing `DATABASE_URL` to point at `sns_emr_dev_clean` would restore
Loren Shields, Margaret Kessler, Norma Suarez, and a non-empty Patient
Census — with no migration, no login disruption, and no tenant conflict.

No changes have been made. No restart has been performed. Awaiting further
instruction before taking any action.
