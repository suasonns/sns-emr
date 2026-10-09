# Infection Allergy Test Data — Cleanup & Idempotency Report (Item 5 & Item 6)

**Date:** 2026-10-06
**Environment:** Local dev stack — PostgreSQL `sns_emr_test_rnica_3patients` (`127.0.0.1`), backend `uvicorn`, frontend `vite` (both dev-mode, not production)
**Patient under test:** `53fe69e1-fcd5-4b49-8203-9b890b18b7d6` (shared RNICA Infection test fixture)
**Table:** `patient_allergies`

## 1. Pre-Cleanup State (before this remediation)

Query: `SELECT count(*), count(*) FILTER (WHERE active) FROM patient_allergies WHERE patient_id = '53fe69e1-...'`

| Total rows | Active rows | Inactive rows |
|---|---|---|
| 61 | 2 | 59 |

Active rows at that time (the only clinically visible records):

| allergen_text | type | severity |
|---|---|---|
| pcn | DRUG | SEVERE |
| egg | FOOD | MODERATE |

**Conclusion at that time:** zero duplicates in active/displayed data. The screenshots the owner flagged were captured during a **transient window** while a prior run of `verify-infection-rebuild.mjs` had its 4 test allergies briefly active, before that run's own (non-idempotent, not-guaranteed) teardown deactivated them. Root cause: the script's teardown was not wrapped in `try/finally` and `capture-infection-screenshots.mjs` shares the same hard-coded `PATIENT_ID`/`ASSESSMENT_ID`.

## 2. Remediation Applied

`sns-emr-frontend/scripts/verify-infection-rebuild.mjs` rewritten (commit `d04644b`) to:
- Tag every test run with a unique `RUN_ID` (timestamp + random suffix).
- Track the exact backend-issued `id` for each of the 4 test allergies it creates (via direct REST API diff, not name-matching).
- Wrap the entire test body in `try { ... } finally { ... }` so teardown **always** executes, including on assertion failure or thrown error.
- Delete strictly by tracked `id` via direct `DELETE /patients/{id}/allergies/{allergy_id}` calls (bypassing UI).
- Re-query the API after deletion and fail the run if any tracked ID is still active.

## 3. Idempotency Verification — 5 Consecutive Runs

| Run | RUN_ID | Result | Teardown |
|---|---|---|---|
| 1 | run-2026-10-06T02:30:38.264Z-4gilhd | ALL CHECKS PASSED | 4/4 confirmed removed |
| 2 | run-2026-10-06T02:31:29.371Z-uhlspp | ALL CHECKS PASSED | 4/4 confirmed removed |
| 3 | run-2026-10-06T02:32:14.145Z-28t0ll | ALL CHECKS PASSED | 4/4 confirmed removed |
| 4 | run-2026-10-06T02:32:59.288Z-onghet | ALL CHECKS PASSED | 4/4 confirmed removed |
| 5 | run-2026-10-06T02:33:44.570Z-uc6sc0 | ALL CHECKS PASSED | 4/4 confirmed removed |

Exit code `0` on every run; no FAIL lines in any run's output.

## 4. Post-Cleanup State (after 5 consecutive runs)

| Total rows | Active rows | Inactive rows |
|---|---|---|
| 81 | 2 | 79 |

Active rows — **identical to pre-cleanup baseline, every run:**

| allergen_text | type | severity |
|---|---|---|
| pcn | DRUG | SEVERE |
| egg | FOOD | MODERATE |

Inactive-row growth (79 − 59 = 20) is fully accounted for: 5 runs × 4 soft-deleted test records = 20. This is expected soft-delete audit-trail accumulation (`active=false`, row retained — by design per `backend/app/api/patient_allergies.py` DELETE handler), not a hygiene defect. No row with `active=true` other than the 2 baseline records existed after any run.

## 5. Determination

- **Zero active duplicates** confirmed after each of 5 consecutive runs.
- **Patient returns to exact baseline** (same 2 active allergies, same values) after every run — the script is idempotent.
- The prior duplicate-looking screenshots were a **stale capture artifact**, not a live data-integrity defect; current active data has never shown duplication during this verification.
- **Item 5: satisfied.** **Item 6: satisfied** (5/5 consecutive idempotent runs, script committed separately as `d04644b`).

## 6. Residual Risk (not yet structurally closed)

`capture-infection-screenshots.mjs` still hard-codes the same `PATIENT_ID`/`ASSESSMENT_ID` as `verify-infection-rebuild.mjs`. Running both scripts concurrently could still reproduce a transient-duplicate screenshot, even though the verify script itself is now self-cleaning. Flagging as an open follow-up item: either isolate the two scripts to distinct patients, or document/enforce a "never run concurrently" rule.
