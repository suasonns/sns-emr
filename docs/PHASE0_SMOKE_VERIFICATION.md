# Phase 0 — Smoke Verification

Status: actual evidence recorded this session. No assumptions.

| Check | Command | Result | Evidence |
|---|---|---|---|
| Database reachable | `Get-NetTCPConnection -LocalPort 5432` | ✅ PASS | 3 listeners on `127.0.0.1:5432` |
| Backend app imports | `python -c "import app.main"` | ✅ PASS | `APP IMPORT OK`, `ROUTES 512` |
| Backend starts (serves traffic) | `python -m uvicorn app.main:app --host 127.0.0.1 --port 8000` | ❌ FAIL | Process exits during lifespan startup: `RuntimeError: DATABASE SCHEMA DRIFT DETECTED - current=['c5938e119c58'] expected_heads=['f7a8b9c0d1e2']` |
| Frontend starts | `npm run dev` (Vite, in `sns-emr-frontend/`) | ✅ PASS | `VITE v8.0.16 ready in 652 ms`, served at `http://localhost:5173/` |
| Login page reachable | `Invoke-WebRequest http://localhost:5173/login` | ✅ PASS | HTTP 200 |
| Backend API reachable | `Invoke-WebRequest http://localhost:8000/docs` | ❌ FAIL | "Unable to connect to the remote server" (port 8000 never bound — backend process exited per above) |
| Authentication reachable | N/A (depends on backend) | ❌ FAIL | Cannot test — no backend process listening on 8000 |

## Prior state (before this session's startup attempts)

Before any startup was attempted, **neither** port 8000 nor port 5173 had a listener
(`Get-NetTCPConnection` returned nothing for both) — i.e., no backend or frontend
process was running at the start of Phase 0, despite the open browser canvas
tab pointed at `http://localhost:5173/login` (a stale/cached tab from a prior session,
not a currently-served page).

## Net result

- **Frontend: fully verified working** end-to-end for its own static/dev-server layer.
- **Backend: verified NOT working** — deterministic, reproducible failure at the
  database schema-drift guard, not a flaky or environmental issue.
- **Login page loads visually** (frontend serves the page), but **cannot authenticate**
  because the API it depends on is not running.
