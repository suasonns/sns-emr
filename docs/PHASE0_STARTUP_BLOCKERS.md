# Phase 0 — Startup Blocker Assessment

Status: read-only diagnostic. Startup was attempted; no schema/data changes were made
(no `alembic upgrade` was executed — the schema-drift blocker below was surfaced by the
app's own read-only startup guard, not by any mutation performed in this session).

## Blocker #1 — CRITICAL — Backend refuses to start (schema drift guard)

- **Symptom:** `python -m uvicorn app.main:app --host 127.0.0.1 --port 8000` starts the process, then fails during FastAPI lifespan startup.
- **Exact error:**
  ```
  RuntimeError: DATABASE SCHEMA DRIFT DETECTED - current=['c5938e119c58'] expected_heads=['f7a8b9c0d1e2']
  ERROR: Application startup failed. Exiting.
  ```
- **Root cause:** `app/main.py`'s `assert_alembic_in_sync()` (called from the `lifespan` handler) compares the connected database's `alembic_version` row against the code's current migration head, and aborts startup on mismatch. The only reachable database, `sns_emr`, is stamped at `c5938e119c58` — a revision ID that does not exist anywhere in `backend/alembic/versions/` (126 files, single head `f7a8b9c0d1e2`).
- **Affected subsystem:** Entire backend (all 512 routes) — the process cannot serve any request.
- **Recommended fix:** Either (a) point `DATABASE_URL` at a database that is actually current with `f7a8b9c0d1e2`, or (b) determine what `sns_emr` actually is and, if it is meant to be the dev database, bring it to head via a normal `alembic upgrade head` run (a Phase 1+ action, not performed here per Phase 0 scope). This decision requires a human call on which database is intended to be canonical — Phase 0 cannot make that call.

## Blocker #2 — CRITICAL — Configured databases do not exist

- **Symptom:** `DATABASE_URL` values in `dev.env`, `backend/dev.env`, and `backend/alembic.ini`'s fallback all name `sns_emr_dev` or `sns_emr_dev_clean`.
- **Exact evidence:** Direct query of `pg_database` on `localhost:5432` returns only `postgres` and `sns_emr`. Neither `sns_emr_dev` nor `sns_emr_dev_clean` exists.
- **Root cause:** Config drift — none of the checked-in/ad hoc config files reference the one database that is physically present.
- **Affected subsystem:** Any startup attempt using the files as-is, unmodified, will fail with a Postgres "database does not exist" error before even reaching the app's schema-drift guard.
- **Recommended fix:** Reconcile config file values with the actual Postgres inventory (human decision — see Blocker #1).

## Blocker #3 — CONFIGURATION — No automatic environment loading

- **Symptom:** `app/core/database.py` calls `load_dotenv(".env.local")` then `load_dotenv()`; neither `backend/.env.local` nor `backend/.env` exists.
- **Root cause:** The only `DATABASE_URL`-bearing files present (`dev.env` variants) do not match either filename `load_dotenv()` looks for, and are not `.gitignore`-excluded dotfiles — they are plain, uncommitted, ad hoc files that must be manually sourced into the process environment.
- **Affected subsystem:** Backend startup requires a human/script to manually export `DATABASE_URL` (and `SECRET_KEY`, `AUTH_MODE`) before every invocation; there is no persistent, automatic configuration path.
- **Recommended fix:** Decide on one canonical env file name that matches what `database.py` actually loads (`.env` or `.env.local`), and populate it — a Phase 1+ decision, not performed here.

## Blocker #4 — STARTUP — No canonical startup script exists

- **Symptom:** No root `package.json`, no `docker-compose*.yml`, no `.vscode/launch.json` or `tasks.json`, no backend runner script.
- **Root cause:** Never checked in.
- **Affected subsystem:** New environment setup / onboarding; not a hard blocker for a developer who already knows the raw commands (see `PHASE0_STARTUP_PROCEDURE.md`).
- **Recommended fix:** Document/commit a startup script — a Phase 1+ documentation action, not performed here.

## Non-blockers confirmed working

- **Postgres service:** running and reachable on `localhost:5432` (3 listeners observed — confirmed via `Get-NetTCPConnection`).
- **Backend Python import:** `import app.main` succeeds cleanly; FastAPI app object builds with 512 routes. The failure is a startup-time (lifespan) guard, not an import/dependency error.
- **Frontend:** `npm run dev` (Vite) starts successfully in ~650ms and serves `http://localhost:5173/`; `GET /login` returns HTTP 200.
- **Dependencies:** No missing Python or Node package errors observed during either startup attempt.

## Summary by severity

| Severity | Count | Items |
|---|---|---|
| CRITICAL | 2 | #1 schema drift guard blocks all backend routes; #2 configured DB names don't exist |
| STARTUP | 1 | #4 no canonical startup script |
| CONFIGURATION | 1 | #3 no automatic env loading |
| DEPENDENCY | 0 | none found |
| ENVIRONMENT | 0 | Postgres itself is healthy; no OS/service-level issue found |
