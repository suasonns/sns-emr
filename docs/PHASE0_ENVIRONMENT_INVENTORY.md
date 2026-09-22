# Phase 0 — Environment Inventory

Status: read-only investigation. No files modified.

| Path | Purpose | Active/Inactive | Startup Relevance | Conflicts/Duplicates |
|---|---|---|---|---|
| `dev.env` (repo root) | Ad hoc dev credential/env file | Present, NOT auto-loaded | None — not read by any code path found | Duplicate of `backend/dev.env` with a different `DATABASE_URL` dbname (`sns_emr_dev` vs `sns_emr_dev_clean`) |
| `backend/dev.env` | Ad hoc dev credential/env file | Present, NOT auto-loaded | None — not read by any code path found | Same as above; also duplicated by the `.bak` file below |
| `backend/dev.env.bak_20260915_234627` | Timestamped backup of `backend/dev.env` | Present, inactive | None | Stale backup artifact; safe to ignore for startup purposes |
| `backend/.env.example` | Template for local secrets (visit-recording storage vars only) | Present, template only | None — does not contain `DATABASE_URL` at all | N/A |
| `backend/.env` | — | **Does not exist** | N/A | N/A |
| `backend/.env.local` | — | **Does not exist** | N/A | N/A |
| `.env.development` / `.env.production` | — | **Do not exist anywhere in repo** | N/A | N/A |
| `docker-compose*.yml` | — | **Does not exist anywhere in repo** | N/A | There is no Docker-based startup path for this repository |
| `.vscode/launch.json` / `.vscode/tasks.json` | — | **Do not exist** | N/A | N/A |
| root `package.json` | — | **Does not exist** | N/A | Repo has no root-level npm workspace entrypoint |
| `sns-emr-frontend/package.json` | Frontend scripts | Active | `npm run dev` → Vite dev server | None found |
| `backend/alembic.ini` | Alembic config, includes fallback `sqlalchemy.url` | Active (tracked in git since commit `ec639b2`, 2026-06-16) | Yes — used by `alembic` CLI when `DATABASE_URL` env var is absent | Fallback value (`.../sns_emr_dev_clean`) points at a database that does not exist on this Postgres instance (see `PHASE0_DATABASE_VALIDATION.md`) |
| `backend/app/core/database.py` | Runtime DB URL resolution | Active | Calls `load_dotenv(".env.local")` then `load_dotenv()` (plain `.env`), both absent in `backend/`; then reads `os.getenv("DATABASE_URL")` and raises `RuntimeError` if unset | The app has **no automatic environment-file loading path that currently resolves to anything** — `DATABASE_URL` must be exported into the process environment manually before every backend start |
| `backend/scripts/run_isolated_tests.py` | Test runner | Active | Creates/migrates/tears down a fresh isolated Postgres DB per test run (not the same target as dev/runtime) | None — self-contained, no conflict with dev startup |
| No backend start script found | — | — | Backend is started via `python -m uvicorn app.main:app --host <host> --port <port>` directly; no wrapper script exists in the repo | This is an undocumented convention, not a checked-in script |

## Findings
1. **No `.env`/`.env.local` file exists anywhere the app actually loads automatically.** The two `load_dotenv()` calls in `database.py` are effectively no-ops on this machine.
2. **`dev.env` files are untracked, hand-maintained, and mutually inconsistent** — they must be sourced into the shell manually; nothing in the repo does this automatically.
3. **No Docker Compose file exists** in this repository despite being a commonly assumed startup path — do not assume `docker compose up` works here.
4. **No canonical backend/frontend startup script is checked into the repo.** The only real, working commands are the raw `uvicorn` and `npm run dev` invocations, established empirically in Deliverable 0.4.
