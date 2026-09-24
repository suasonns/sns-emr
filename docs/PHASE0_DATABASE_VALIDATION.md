# Phase 0 — Database Target Validation

Status: read-only investigation only. No schema, data, or migration changes were made.
Live database was queried directly this session (`pg_database`, `information_schema.tables`, `alembic_version`).

## 1. Actual values found, by source

| Source file | `DATABASE_URL` host:port/dbname | Loaded automatically by app? |
|---|---|---|
| `dev.env` (repo root) | `localhost:5432/sns_emr_dev` | No |
| `backend/dev.env` | `localhost:5432/sns_emr_dev_clean` | No |
| `backend/dev.env.bak_20260915_234627` | `localhost:5432/sns_emr_dev` | No |
| `backend/alembic.ini` (`sqlalchemy.url`, line 89) | `127.0.0.1:5432/sns_emr_dev_clean` | Only by the `alembic` CLI, only when `DATABASE_URL` env var is unset |
| Process environment (only source `app/core/database.py` actually reads) | whatever was last manually exported | Yes — this is the only value the running app ever sees |

(User/password portion of the connection string is intentionally withheld per policy; it is a static shared dev credential, not needed to explain the conflict below, and is identical across all files.)

## 2. Databases that actually exist on this Postgres instance

Queried directly via `SELECT datname FROM pg_database WHERE datistemplate = false`, against `localhost:5432`:

```
postgres
sns_emr
```

**`sns_emr_dev` does not exist. `sns_emr_dev_clean` does not exist.** Every config file above (`dev.env` x2, `alembic.ini`) names a database that is not present on this Postgres server.

## 3. The one database that does exist: `sns_emr`

- `information_schema.tables` (public schema) row count: **6 tables** — `alembic_version`, `audit_logs`, `patients`, `tasks`, `tenants`, `visits`.
- This is a minimal seed/smoke schema, not the full EMR schema (no `users`, no RNICA tables, no election-addendum tables, etc.). It contains 5 tenant rows and 25 patient rows — plausible seed/demo data, not verified as the "real" checkpoint-referenced dataset.
- `alembic_version` table content: **`c5938e119c58`** — a revision ID that **does not exist anywhere in `backend/alembic/versions/`** (126 migration files present; current single head is `f7a8b9c0d1e2`). This is an orphaned/unknown stamp, not a valid point in the current migration graph.

## 4. Used-by matrix

| Consumer | Target it would actually resolve to | Status |
|---|---|---|
| Backend runtime (`app/core/database.py`) | Whatever `DATABASE_URL` is manually exported before `uvicorn` starts | No file provides this automatically; must be set by hand each session |
| Migrations (`alembic` CLI via `alembic.ini` fallback) | `sns_emr_dev_clean` | **Does not exist** — any bare `alembic` invocation without an explicit env override fails outright |
| Tests (`backend/scripts/run_isolated_tests.py`) | A fresh, isolated, per-run database created/migrated/torn down by the wrapper itself | Not affected by this conflict — self-contained |
| Frontend | No direct DB access; calls backend API at `http://localhost:8000` (hardcoded fallback in `sns-emr-frontend/src/api/*` when `VITE_API_BASE_URL` is unset) | Depends entirely on backend being up |

## 5. Conclusion — canonical database

**No single canonical database currently exists.** Of the three names referenced across all config sources (`sns_emr_dev`, `sns_emr_dev_clean`, `sns_emr`), only `sns_emr` is physically present, and it is stamped at a migration revision that is not reachable from the current migration history — meaning the application's own startup guard (`assert_alembic_in_sync()` in `app/main.py`) refuses to start against it (see `PHASE0_STARTUP_BLOCKERS.md`, Blocker #1).

This directly updates the prior session's `docs/DATABASE_CONNECTION_DIVERGENCE_REPORT.md`, which reasoned from file contents alone and assumed `sns_emr_dev_clean` was a live, populated database — it is not currently reachable on this Postgres instance at all.
