# Owner Platform Data Repair Plan

Status: **plan only — nothing executed.** No DB writes have been made.

## 1. Discovery: the approved IDs already exist in code, just never seeded

Before proposing a repair, the codebase itself was checked for an
authoritative source of truth on tenant identity — and one exists:
`backend/app/core/protected_tenants.py`. It hardcodes 5 fixed, permanent
tenant UUIDs and documents them as "standing infrastructure/production
tenants, not disposable test fixtures":

| Constant | UUID | Approved Entity |
|---|---|---|
| `PLATFORM_TENANT_ID` | `cccccccc-cccc-cccc-cccc-cccccccccccc` | SNS Hospice Solutions |
| (unnamed, in `PROTECTED_TENANT_IDS`) | `dddddddd-dddd-dddd-dddd-dddddddddddd` | North East Billing |
| (unnamed) | `01271980-0000-0000-0000-000005101977` | Love & Faith Hospice Services, Inc. |
| (unnamed) | `aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa` | Angela Hospice (Training) |
| (unnamed) | `bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb` | Silva Hospice (Training) |

These IDs are **already load-bearing elsewhere in the codebase**, independent
of whatever tenants happen to exist in the dev database:

- `backend/app/api/owner_admin.py` imports `PLATFORM_TENANT_ID` directly and
  uses it to scope the SNS-staff-creation endpoint (`User.tenant_id == PLATFORM_TENANT_ID`).
- `tests/conftest.py` uses `aaaaaaaa-...` (Angela Hospice) as the fixed
  pytest test tenant id.
- `protected_tenants.assert_not_protected()` is meant to be called by any
  bulk-delete/purge routine to refuse deleting these 5 tenants.

**I queried the live database directly: none of these 5 canonical IDs
currently have a `tenants` row.** This is the actual, precise reason the
approved structure "does not exist" — the code was written expecting these
tenants to be seeded, but `seed_tenants.py` (which creates exactly these
entities) was never run with matching env vars.

This also means the 3 current placeholder tenants (`Development Agency` x2,
`Development Platform`) are **not** stand-ins for the approved entities at
all — they're accidental, unrelated bootstrap rows at different, arbitrary
UUIDs, while the real code already points at the canonical IDs above.
Renaming the placeholders in place (keeping their current IDs) would leave
`owner_admin.py` and the test suite pointed at tenant IDs that still don't
exist. The repair must create tenant rows **at the canonical protected IDs**,
not merely rename the existing placeholders.

## 2. Exact tables, records, and blast radius

Live query results (direct SQL against `sns_emr_dev`, the shared dev
database):

| Placeholder tenant | id | Rows referencing it (across all 137 tables with a `tenant_id` column) |
|---|---|---|
| "Development Agency" (env `DEV_TENANT_ID`) | `e106b52e-9352-4e4c-9b4c-40fba15ffeb2` | `users`: 1, `audit_logs`: 1 |
| "Development Platform" (env `DEV_PLATFORM_TENANT_ID`) | `c067f47d-a214-45cb-b6f3-68f1d69b8318` | `users`: 1, `audit_logs`: 3 |
| "Development Agency" (env `DEV_BILLING_TENANT_ID`) | `b1ec833e-d844-4338-92a4-52d555a587c9` | `users`: 1, `audit_logs`: 1 |

No patient, clinical, billing, or claim data of any kind is attached to
any of the 3 placeholder tenants — every other one of the 137
`tenant_id`-bearing tables returned 0 rows for all 3 IDs. Total blast
radius: **3 `users` rows, 5 `audit_logs` rows.**

## 3. Existing relationships / foreign keys

- `users.tenant_id` → `tenants.id` (FK)
- `audit_logs.tenant_id` → `tenants.id` (FK)
- No other table references these 3 tenant rows.
- The 3 `users` rows are the dev login accounts created by
  `admin_bootstrap_service.provision_development_logins()` at backend
  startup (the DPCS admin / platform owner / billing dev logins defined by
  `DEV_DPCS_ADMIN_EMAIL` / `DEV_PLATFORM_OWNER_EMAIL` / `DEV_BILLING_EMAIL`
  in `dev.env`).

## 4. Repair plan (forward-only, no deletion of substantive data)

**Step 1 — Seed the approved entities at their canonical IDs (additive only).**
Add to `dev.env`:

```
DEV_TENANT_PLATFORM_ID=cccccccc-cccc-cccc-cccc-cccccccccccc
DEV_TENANT_BILLING_ID=dddddddd-dddd-dddd-dddd-dddddddddddd
DEV_TENANT_REAL_ID=01271980-0000-0000-0000-000005101977
DEV_TENANT_DUMMY_A=aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa
DEV_TENANT_DUMMY_B=bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb
```

Run `python scripts/seed_tenants.py`. This only ever creates-if-missing or
updates-in-place by primary key — it cannot delete or touch any other
table. Result: 5 new `tenants` rows (SNS Hospice Solutions, North East
Billing, Love & Faith Hospice Services Inc., Angela Hospice, Silva
Hospice), 0 rows changed elsewhere.

**Step 2 — Point dev login provisioning at the real tenants (in place, no ID changes to existing rows).**
Update `dev.env`'s existing bootstrap vars so future logins are created
under the *real* tenants instead of placeholders:

```
DEV_TENANT_ID=01271980-0000-0000-0000-000005101977          # Love & Faith Hospice (was e106b52e...)
DEV_PLATFORM_TENANT_ID=cccccccc-cccc-cccc-cccc-cccccccccccc # SNS Hospice Solutions (was c067f47d...)
DEV_BILLING_TENANT_ID=dddddddd-dddd-dddd-dddd-dddddddddddd  # North East Billing (was b1ec833e...)
```

This does not touch the 3 existing `users`/5 `audit_logs` rows — they keep
their current `tenant_id` values untouched (nothing is deleted or
rewritten). On next backend restart, `provision_development_logins()` looks
up dev accounts by `(email, tenant_id)`; since the new tenant_id values
won't match the old rows, it will **create new** dev-login `users` rows
under the real tenants (not overwrite/delete the old ones).

**Step 3 — Migrate the 3 existing dev-login users' `tenant_id` FK to the real tenants (optional, recommended).**
Rather than leaving 3 duplicate "old" dev accounts orphaned under the
placeholder tenants, re-point their `tenant_id` column (a simple `UPDATE`,
same row, same primary key, same audit trail) to the corresponding
canonical tenant. This preserves the user row's identity, history, and any
audit log entries already tied to its `id` — only the FK changes, exactly
matching your requirement to preserve IDs/relationships/audit history while
converting placeholders into approved entities.

**Step 4 — Remove the now-empty placeholder tenant shells (safe deletion, no substantive data).**
After step 3, the 3 placeholder `tenants` rows have zero remaining
references anywhere in the schema (confirmed in section 2 — no clinical,
billing, or patient data ever pointed at them). They can be deleted safely
with no data loss: they are empty shell rows once their only 3 dependent
`users` rows are re-pointed. This is the "safe removal" path explicitly
permitted as an alternative to mapping.

**No migration is stamped, no database is reset/recreated, no production
data is touched.** This is a data-seed script run plus at most 3 `UPDATE`
statements and 3 `DELETE` statements against already-empty shell rows.

## 5. Where should "North East Billing" live in the schema?

It is **its own `tenants` row** with `tenant_type = 'BILLING'` — not a
sub-record of another tenant, and not a separate table. The schema already
models billing as a first-class tenant type (see `Tenant.tenant_type`
enum values `PLATFORM` / `BILLING` / `PRODUCTION` / `TRAINING` / `DEV` in
`seed_tenants.py`), and `admin_bootstrap_service.py`'s `DEV_BILLING_TENANT_ID`
already treats it as a distinct tenant with `billing_enabled=True` set on
whichever tenant it's pointed at. This matches the "Biller Platform" concept
in the approved structure: a standalone organization, not an attribute of
SNS Hospice Solutions or of the production agency.

## 6. Validation checklist (to run after executing this plan)

- [ ] `SELECT legal_name, tenant_type FROM tenants ORDER BY legal_name;` → SNS Hospice Solutions, North East Billing, Love & Faith Hospice Services Inc., Angela Hospice, Silva Hospice (no `Development Agency`/`Development Platform` rows left, or if kept, 0 referencing rows and clearly excluded from active UI lists)
- [ ] `GET /api/owner/tenants` (or equivalent) returns the same 5 entities
- [ ] Tenant Management UI dropdown/list shows the same 5 entities
- [ ] Dashboard tenant selector shows the same 5 entities
- [ ] The 3 existing dev-login users still authenticate and now show the correct tenant name
- [ ] `pytest` test suite (which depends on `aaaaaaaa-...` as the fixed Angela Hospice test tenant) still passes

## Explicitly not done in this plan

- No database reset, recreate, or migration stamp.
- No deletion of any row containing real user/audit/clinical data.
- No changes to Analytics, AI Command Center, or Billing & Licensing pages.
- No page redesign.

Awaiting approval before executing.
