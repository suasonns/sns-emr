# Recovered Change Manifest

Recovery branch/worktree: `recovery/copilot-session-2026-09-14`
Location: `C:\Users\rdsua\Desktop\copilot-recovery-2026-09-15\recovery-worktree`
Applied against: current `main` HEAD `b552fcb0e90d8eca25beacb55c5b35d3d575d1ee`

All 46 files below share the same recovery source and confidence:

- **Recovered source**: live worktree `C:\dev\SNS EMR\copilot-worktrees\sns-emr\suasonns-psychic-adventure`
  (branch `suasonns-psychic-adventure`, on top of commit `6f3c8ac4`), read via preserved git
  admin metadata from the `.copilot_old` profile copy.
- **Recovery confidence**: **exact** — full file content read directly from the untouched,
  still-existing working tree; not reconstructed from fragments or memory.
- **Evidence timestamp**: file mtimes from 2026-09-14 14:58 through 2026-09-15 01:2x (Pacific),
  consistent with session `c84ba1cc-9d7e-43f0-a9ed-f9eea3e3cd80` events.jsonl ending 2026-09-15
  08:28 UTC.
- **Change type**: 22 modified, 24 created (see candidate-file-list.txt for the split).
- **Patch file**: `patches\suasonns-psychic-adventure-full.patch` (diff against commit `6f3c8ac4`,
  568,331 bytes, 46 files / 8,414 insertions / 309 deletions). Note: this patch does not apply
  cleanly with `git apply` onto current `main` because `main` has diverged from the old session's
  base commit — exact file content was copied directly instead (see below) rather than patched.
- **Missing/conflicting sections**: none for file content. Structural conflict only: applying the
  recovered file set on top of `main` is a rewrite of files that may have independently changed on
  `main` since 6f3c8ac4 diverged (e.g. `backend/app/core/auth.py`, `backend/app/core/roles.py`,
  `sns-emr-frontend/src/owner/pages/UserManagement.jsx`) — review the diff vs current main
  carefully before merging; this is a full-content overwrite of those files' recovered state, not
  a merge of both histories.

## Summary of the feature recovered

Platform/staff RBAC work: account types, departments, job titles, platforms, staff permission
grants, staff lifecycle/profile/audit-log tests, an Owner audit log UI, staff user-management UI
(AddStaffModal, StaffProfileDrawer, AuditEventDrawer), a set-password page, and 5 new Alembic
migrations for the underlying schema changes.

## Validation performed in the isolated recovery worktree

- `git status` / `git diff --cached --stat`: clean, 46 files staged, 8,746 insertions / 535
  deletions vs `main`.
- `python -m py_compile` on all 23 recovered/modified backend `.py` files: **passed, exit 0**.
- Frontend (`sns-emr-frontend`) validation **not run**: `node_modules` is not installed in this
  worktree and installing dependencies was out of scope for a forensic recovery (would also
  violate "do not update dependencies" guidance). Run `npm install && npx tsc --noEmit && npm run
  lint` there before relying on the frontend changes.
- Nothing was committed. `git status` in the recovery worktree still shows all 46 files staged
  but uncommitted, left for your review.

## Preservation statement

- `.copilot_old` was never opened in write mode and was not modified. All git reads used a
  duplicated admin-metadata copy under `profile-copy\`.
- The live worktree `C:\dev\SNS EMR\copilot-worktrees\sns-emr\suasonns-psychic-adventure` was only
  read from (via `--work-tree`), never written to.
- The main repository (`C:\Users\rdsua\.copilot\repos\sns-emr`) and this session's own worktree
  (`suasonns-fantastic-memory`) were untouched except for adding the new
  `recovery/copilot-session-2026-09-14` worktree/branch, which is isolated from both.
