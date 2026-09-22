# Owner Platform Data Conformance Report

Scope: verify the *data* backing the 5 Owner Platform pages (Dashboard,
Tenant Management, System Health, User Management, Audit Logs) against the
approved SNS platform organization structure. This is independent of page
layout/design — a page can be visually correct and still be validated
against the wrong entities.

Investigation method: direct SQL query against the live shared dev database
(`sns_emr_dev`) via SQLAlchemy, plus direct reading of
`backend/scripts/seed_tenants.py`, `backend/app/services/admin_bootstrap_service.py`,
and `backend/dev.env`. No assumptions from screenshots or prior reports.

## Root Cause

Two independent tenant-provisioning code paths exist, and only one of them
has ever actually run against this database:

1. **`backend/scripts/seed_tenants.py`** (the real seed script) creates the
   approved roster below, keyed off env vars `DEV_TENANT_PLATFORM_ID`,
   `DEV_TENANT_BILLING_ID`, `DEV_TENANT_REAL_ID`, `DEV_TENANT_DUMMY_A`,
   `DEV_TENANT_DUMMY_B`. **None of these env vars are set in `dev.env`.**
   This script has never been run against this database (or if it was run
   with those vars unset, every entry was skipped — its own log output
   would have said `skipped: ... (ENV_VAR not set)` for all 5 rows).

2. **`backend/app/services/admin_bootstrap_service.py` → `_ensure_tenant()`**
   runs automatically on every backend startup (`app/main.py`) to
   provision login accounts. It reads a *different* set of env vars that
   **are** set in `dev.env` — `DEV_TENANT_ID`, `DEV_PLATFORM_TENANT_ID`,
   `DEV_BILLING_TENANT_ID` — and, finding no existing tenant row at those
   UUIDs, silently auto-creates generic placeholder tenants literally
   named `"Development Agency"` / `"Development Platform"` as a
   side-effect of login provisioning. These were never meant to be the
   platform's real data.

Additionally, `_ensure_tenant()` has a naming bug: it only special-cases
the *platform* tenant (`"Development Platform"`); every other caller
(including the billing identity) falls through to `"Development Agency"`,
which is why the UI shows `"Development Agency"` twice under two different
tenant IDs.

**Nothing was removed by a migration, reset, or code change.** The
approved entities were never created in the first place because the two
env var naming schemes never lined up.

## Live Database Query Result

Directly queried `tenants` table in `sns_emr_dev` (shared by both running
backends):

| id | legal_name | display_name | tenant_type | environment_tag |
|---|---|---|---|---|
| `e106b52e-9352-4e4c-9b4c-40fba15ffeb2` | SNS Development Agency | Development Agency | DEV | DEVELOPMENT |
| `b1ec833e-d844-4338-92a4-52d555a587c9` | SNS Development Agency | Development Agency | DEV | DEVELOPMENT |
| `c067f47d-a214-45cb-b6f3-68f1d69b8318` | SNS Development Platform | Development Platform | DEV | DEVELOPMENT |

That is the entire table. 3 rows, all auto-created placeholders.

## Conformance Table

| Entity | Entity Type | Exists in DB | Exists in API | Exists in UI | Expected Location | Actual Location | Mismatch |
|---|---|---|---|---|---|---|---|
| SNS Hospice Solutions | PLATFORM | ❌ No | ❌ No | ❌ No | Tenant Management, Dashboard, all owner pages | Nowhere | Never seeded — `seed_tenants.py` env var (`DEV_TENANT_PLATFORM_ID`) unset |
| North East Billing | BILLING | ❌ No | ❌ No | ❌ No | Tenant Management, Billing & Licensing | Nowhere | Never seeded — `DEV_TENANT_BILLING_ID` unset |
| Love & Faith Hospice Services, Inc. | PRODUCTION | ❌ No | ❌ No | ❌ No | Tenant Management (production agency) | Nowhere | Never seeded — `DEV_TENANT_REAL_ID` unset |
| Angela Hospice (Training) | TRAINING | ❌ No | ❌ No | ❌ No | Tenant Management (training agency) | Nowhere | Never seeded — `DEV_TENANT_DUMMY_A` unset |
| Silva Hospice (Training) | TRAINING | ❌ No | ❌ No | ❌ No | Tenant Management (training agency) | Nowhere | Never seeded — `DEV_TENANT_DUMMY_B` unset |
| "Development Agency" (×2, distinct IDs) | DEV | ✅ Yes (2 rows) | ✅ Yes | ✅ Yes | Should not exist in a field-testing environment | Present, duplicated | Auto-created side effect of `admin_bootstrap_service._ensure_tenant()`; one of the two is actually the billing placeholder, mislabeled |
| "Development Platform" | DEV | ✅ Yes | ✅ Yes | ✅ Yes | Should not exist in a field-testing environment | Present | Auto-created side effect of `admin_bootstrap_service._ensure_tenant()` |

## Per-Page Impact

- **Tenant Management**: lists exactly the 3 placeholder DEV tenants above; cannot be field-tested against real org structure until reseeded.
- **Dashboard**: tenant selector / "Viewing" dropdown and any tenant-scoped metrics are built from the same 3 placeholder tenants.
- **User Management (SNS Staff & Access)**: platform-staff scoping still works structurally (it's scoped by role, not by which tenant exists), but any tenant-linked staff assignment references only the placeholders.
- **System Health / Audit Logs**: not tenant-specific in the same way, but any tenant-scoped filters (e.g. Audit Logs' Tenant dropdown) only offer the 3 placeholders.

## What Is Required Before Field Testing

1. Add the 5 missing env vars to `dev.env` (`DEV_TENANT_PLATFORM_ID`, `DEV_TENANT_BILLING_ID`, `DEV_TENANT_REAL_ID`, `DEV_TENANT_DUMMY_A`, `DEV_TENANT_DUMMY_B`), each a fresh UUID (or reuse the existing 3 placeholder UUIDs for the platform/billing rows so existing dev logins keep pointing at the same tenant, just correctly renamed).
2. Run `python scripts/seed_tenants.py` — this is idempotent/safe to re-run and updates in place.
3. Decide whether to keep or remove the `Dev Tenant A` / `Dev Tenant B` temporary rows the script also defines (`--drop-temporary` flag exists for pre-production cutover).
4. Fix (separately, not in this report) the `_ensure_tenant()` naming bug so a future unmatched `DEV_BILLING_TENANT_ID` doesn't silently mint another "Development Agency".

No pages were redesigned. No changes were made to Analytics, AI Command Center, or Billing & Licensing.
