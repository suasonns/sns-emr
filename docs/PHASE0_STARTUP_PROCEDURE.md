# Phase 0 — Canonical Startup Procedure

Status: this procedure was executed exactly as written during this session (see
`PHASE0_SMOKE_VERIFICATION.md` for results). It reflects what actually works today,
not an aspirational process.

> **Known limitation:** Step 2 (backend) currently fails at the final health-check
> due to Blocker #1/#2 in `PHASE0_STARTUP_BLOCKERS.md`. The commands below are the
> correct/only working invocation shape; they do not by themselves fix the database
> mismatch.

## Step 1 — Database
Postgres must already be running as a local service listening on `127.0.0.1:5432`
(confirmed present and listening this session — no start command was required or run).
No Docker Compose path exists in this repo.

## Step 2 — Backend
From `backend/`, with `DATABASE_URL`, `SECRET_KEY`, `AUTH_MODE`, and `APP_ENV`
exported into the current shell (no `.env`/`.env.local` file is auto-loaded — see
Blocker #3):

```
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

## Step 3 — Frontend
From `sns-emr-frontend/`:

```
npm run dev
```

Confirmed this session: starts in ~650ms, serves `http://localhost:5173/`.

## Step 4 — Verification
```
Invoke-WebRequest http://localhost:5173/login   # expect 200
Invoke-WebRequest http://localhost:8000/docs     # expect 200 once backend is healthy
```

## Step 5 — Health check
Backend readiness is currently gated by its own internal `assert_alembic_in_sync()`
lifespan check — if the connected database's `alembic_version` does not match the
code's migration head, the process logs `DATABASE SCHEMA DRIFT DETECTED` and exits
before binding the port. A successful health check requires this check to pass first.

## Step 6 — Expected success indicators
- Frontend: HTTP 200 on `/login`, Vite "ready" log line.
- Backend: `INFO: Application startup complete.` in logs, HTTP 200 on `/docs`, port 8000 accepting connections.
- Both: no `RuntimeError` in backend logs, no missing-module errors in either process.

**Current actual state:** Frontend meets all Step 6 criteria. Backend does not — it
exits before "Application startup complete" due to Blockers #1/#2. Until a database
matching the code's migration head (`f7a8b9c0d1e2`) is designated canonical and
supplied via `DATABASE_URL`, Step 2 cannot succeed as written.
