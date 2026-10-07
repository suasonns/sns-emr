# SNS Worktree Protocol

**Status:** Active supporting process
**Purpose:** Ensure every worktree applies the same tracked governance without copying independent rule sets.

## Before worktree creation

- Ensure the source branch contains the committed governance files.
- Record the intended base branch and commit.
- Confirm work scope and applicable feature authorities.
- Confirm no required rule exists only as an untracked file in another worktree.

## Immediately after creation

From the new worktree root, run:

```bash
node scripts/sns-worktree-preflight.mjs
```

Do not implement until strict verification passes and the constitutional session-start template is complete.

## During work

- Stay within approved scope.
- Protect pre-existing modified and untracked files.
- Do not assume changes in another worktree are present.
- Re-run preflight after branch changes, rebases, governance changes, or authority changes.
- Stop affected work on rule conflicts or data-integrity risks.

## Before staging

- Run targeted tests, applicable regressions, typecheck, lint, and production build.
- Run strict governance verification again.
- Inspect `git diff --stat`, `git diff --name-only`, and `git status --short`.
- Confirm no patient data, secrets, unrelated files, migration drift, or forbidden dependencies.
- Present the constitutional completion report and wait for explicit staging authorization.

## Staging and commit

- Never use `git add .` or `git add -A`.
- Stage only explicit approved paths.
- Show `git diff --cached --name-only` and `git diff --cached` before commit.
- Stop if any staged path is out of scope.
- Commit only when explicitly authorized.

## After commit

Report commit hash, exact files, validation results, strict verifier result, and remaining unrelated changes. Confirm governance still passes in the committed state.
