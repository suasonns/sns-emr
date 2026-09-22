# Database Connection Divergence Report: sns_emr_dev vs sns_emr_dev_clean

Status: read-only investigation. No code or data modified.

## 1. Current DATABASE_URL

```
DATABASE_URL=postgresql://<user>:<redacted>@localhost:5432/sns_emr_dev
```

(Value confirmed by direct read of the file; credentials redacted here,
host/port/dbname shown as-is.)

## 2. Source File Providing DATABASE_URL

`backend/dev.env` (in `recovery-worktree`, the codebase actually serving
`localhost:5173`/`localhost:8000`; the same file was later copied into the
session worktree during this session's earlier tenant-repair work).

Important nuance: **this is not the file the application loads on its
own.** `app/core/database.py` only calls `load_dotenv(".env.local")` then
`load_dotenv()` (i.e. a plain `.env`) — neither of which exists in
`backend/` (confirmed: `.env` and `.env.local` are both absent). `dev.env`
is a manually-named, ad hoc file that must be sourced into the process
environment by hand (or by a launch script) before starting uvicorn —
which is exactly the workaround used earlier in this session to get the
backend running at all. There is no `.env`/`.env.local` currently
providing `DATABASE_URL` through the app's normal, automatic loading path.

## 3. Last Commit That Changed It

**None — `dev.env` is not tracked by git at all** (`git ls-files -- dev.env`
returns nothing, and it is not matched by any `.gitignore` rule either —
`.gitignore` only excludes `.env` / `.env.*`, and `dev.env` doesn't start
with a dot, so it simply was never `git add`ed). There is no commit
history to inspect for this file.

Its filesystem metadata is the only available timeline:
- **Created:** 2026-09-15 13:24:03 (today, this session)
- **Last modified:** 2026-09-15 17:24:29 (today, from this session's tenant-repair edits)

This means the `dev.env` currently in use — and its `DATABASE_URL=...sns_emr_dev`
value — is a file that came into existence **today**, not a long-standing
configuration artifact.

By contrast, `alembic.ini` (which IS tracked) has carried a static fallback
`sqlalchemy.url = postgresql://...@127.0.0.1:5432/sns_emr_dev_clean` since
commit `ec639b2` ("Add backend config update and preflight script"),
authored 2026-06-16, and **no commit since has touched that line** — it has
pointed at `sns_emr_dev_clean`, unchanged, for three months.

## 4. Environment Currently Loaded by localhost:5173

`localhost:5173` is served by the `recovery-worktree` frontend dev server,
which calls the backend at `localhost:8000` (`sns-emr-frontend/src/api/census.ts`
and sibling API modules fall back to `http://localhost:8000` when
`VITE_API_BASE_URL` is unset). That backend process is the one just
restarted in this session using `backend/dev.env`'s values loaded manually
into the process environment — i.e. it is connected to **`sns_emr_dev`**,
the empty/placeholder database, not `sns_emr_dev_clean`.

## 5. How the Presentation Environment Resolved to sns_emr_dev_clean

Two independent, git-tracked sources establish that `sns_emr_dev_clean`
was the actual, long-running development database throughout real feature
work — not a one-off:

- `alembic.ini`'s `sqlalchemy.url` has named `sns_emr_dev_clean` since
  2026-06-16 (`ec639b2`), and it is the fallback Alembic uses whenever a
  migration is run without an explicit `DATABASE_URL` override.
- `docs/planning/implementation_checkpoint_001.md` and
  `docs/SNS_STAFF_ACCESS_CHECKPOINT.md` both explicitly document
  `alembic upgrade head` being run and verified against `sns_emr_dev_clean`,
  referring to it in-text as "the local dev DB." Loren Shields, Margaret
  Kessler, and Norma Suarez — along with the correct named tenants — exist
  in exactly that database.

The straightforward reading: whatever `DATABASE_URL` configuration existed
on this machine during the actual development/checkpoint history (an
earlier `.env`/`dev.env` that is no longer present — it was never
committed, so it left no trace once overwritten) pointed at
`sns_emr_dev_clean`, consistent with Alembic's own tracked default. That
is how the "presentation" data — the real named patients and tenants —
ended up living in `sns_emr_dev_clean`.

## 6. Why the Current Environment Resolves to sns_emr_dev

Because today's `dev.env` — created fresh during this session, per its
filesystem timestamp — sets `DATABASE_URL` to `sns_emr_dev` (no `_clean`
suffix), a database name that differs from the long-standing, checkpoint-
verified `sns_emr_dev_clean` by exactly that suffix. Since `dev.env` was
never committed to git, there is no historical record of who chose that
name or why; the most likely explanation given the evidence is a
same-day naming mismatch — either a typo dropping `_clean`, or an
assumption that a fresh/empty dev database should be used — made while
reconstructing a working local environment during this session, without
awareness that `sns_emr_dev_clean` (matching Alembic's own tracked
default) already held the real seeded data.

## Conclusion

This is a same-day configuration divergence, not a historical migration or
a deliberate environment change: a brand-new, uncommitted `dev.env` (created
today) points the running application at an empty database
(`sns_emr_dev`) whose name is one word off from the actual, long-standing,
git-referenced development database (`sns_emr_dev_clean`) that already
contains the real tenants, patients, and checkpoint-verified schema state.

No code or data was changed in the course of this investigation.
