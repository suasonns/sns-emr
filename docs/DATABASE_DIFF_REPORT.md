# Diff Report: sns_emr_dev vs sns_emr_dev_clean

Status: read-only investigation. No code or data changed.

## 1. Which Environment File Points to Each Database

| Database | Pointed to by | File status |
|---|---|---|
| `sns_emr_dev` | `backend/dev.env` (`DATABASE_URL=...sns_emr_dev`) — present in both `recovery-worktree` and the session worktree | **Untracked**, never committed to git |
| `sns_emr_dev_clean` | `backend/alembic.ini` (`sqlalchemy.url = ...sns_emr_dev_clean`) | **Tracked**, unchanged since commit `ec639b2` (2026-06-16) |

No file currently sets `DATABASE_URL=...sns_emr_dev_clean` for the running
application. `sns_emr_dev_clean` is only referenced today via Alembic's own
static config file and two historical checkpoint docs — nothing in the
live app-startup path points there anymore.

## 2. Which Startup Path Loads That Environment

- **`sns_emr_dev` (currently active):** loaded only because this session
  manually parsed `backend/dev.env` line-by-line and injected each value
  into the PowerShell process environment *before* launching
  `python -m uvicorn app.main:app --reload --port 8000`. The app's own
  `app/core/database.py` calls `load_dotenv(".env.local")` then
  `load_dotenv()` — neither file exists, so without that manual
  pre-loading step the backend cannot start at all (confirmed earlier:
  it raised `RuntimeError: DATABASE_URL is not set` when started without
  it).
- **`sns_emr_dev_clean` (not currently loaded by anything):** only reachable
  today via `alembic.ini`'s static fallback, which is used exclusively when
  running Alembic commands (e.g. `alembic upgrade head`) without an
  explicit `DATABASE_URL` override — a migration-tool code path, not the
  running FastAPI application's path.

## 3. Did Today's 1:24 PM dev.env Creation Change Database Selection?

**Yes.** Before today, no `dev.env` existed to source at all — the only
git-tracked `DATABASE_URL`-equivalent value on disk was Alembic's static
`sns_emr_dev_clean` fallback. The moment `dev.env` was created today
(13:24, per filesystem `CreationTime`) with
`DATABASE_URL=...sns_emr_dev`, that became the value manually sourced into
every subsequent backend process's environment — which is what the running
backend on port 8000 has used ever since, including through this
session's later tenant-repair restart. Today's file creation is the direct
and sole reason the running application connects to `sns_emr_dev` instead
of `sns_emr_dev_clean`.

## 4. Is localhost:5180 Loading a Different Environment Than the Presentation Build?

**No — 5180 and 5173 are currently identical in this respect, and both
differ from the historical presentation environment.**

Checked `vite.config.ts` (shared shape in both worktrees): the dev server
proxies `/api`, `/audit-dashboard`, `/auth`, `/dashboard`, `/visits`, etc.
to a single `apiTarget` that defaults to `http://localhost:8000` when no
override env var is set. Neither worktree's frontend has a `.env` file
setting a different target. Only one process can bind port 8000 at a
time — right now that's the `recovery-worktree` backend (PID 96752),
connected to `sns_emr_dev` via `dev.env`.

Practical effect: **every frontend** currently running — `localhost:5173`
(recovery-worktree) and `localhost:5180` (session worktree) — proxies
through to the exact same single backend process and therefore the exact
same database, `sns_emr_dev`. There is no divergence between 5173 and
5180 right now. The divergence is between *both of them together* and the
historical "presentation" environment (whichever earlier process, using an
earlier — now gone, never-committed — `.env`/`dev.env`, connected to
`sns_emr_dev_clean` and was the basis of the checkpoint docs and the real
patient/tenant data).

Session worktree's own `dev.env` (copied from recovery-worktree earlier
today, `CreationTime` 16:56) carries the identical `sns_emr_dev` value, so
even if a second backend were started from the session worktree on a
different port, it would also connect to `sns_emr_dev` unless edited.

## 5. Smallest Safe Change to Restore the Presentation Database Connection

Change one line in `backend/dev.env` (in both worktrees, since both copies
currently say the same thing):

```
DATABASE_URL=postgresql://<same user/pass/host/port>/sns_emr_dev_clean
```

i.e. append `_clean` to the existing database name — no other value in the
connection string changes. Then restart the single backend process
currently bound to port 8000 (re-run the same manual dev.env-sourcing +
`uvicorn --reload` sequence used earlier this session) so the new value is
picked up. No schema change, no migration, no data move, and no frontend
code change is required — both `localhost:5173` and `localhost:5180`
would immediately start proxying to the corrected backend/database simply
by virtue of the existing single-backend proxy setup described in section 4.

This is strictly reversible (a one-line env value swap) and does not touch
any committed source file — `dev.env` is untracked either way.

## Summary Table

| Question | Answer |
|---|---|
| File pointing to `sns_emr_dev` | `backend/dev.env` (untracked, created today 13:24) |
| File pointing to `sns_emr_dev_clean` | `backend/alembic.ini` (tracked, unchanged since 2026-06-16) |
| Did today's dev.env change selection? | Yes — it's the sole reason the app connects to `sns_emr_dev` |
| Does 5180 differ from 5173/presentation? | No difference from 5173 (same backend, same DB); both differ from the historical presentation DB |
| Smallest safe fix | Edit `DATABASE_URL` in `dev.env` to end in `sns_emr_dev_clean`, then restart the port-8000 backend |

No code or data was changed in the course of this report.
