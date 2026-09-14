# Worktree Reconciliation Report

**Generated:** 2026-09-13, against `origin/main` @ `b552fcb0e90d8eca25beacb55c5b35d3d575d1ee`
(merge of PR #89, latest fetched ref at time of report).

Method: for every worktree branch, (1) confirmed ahead/behind vs
`origin/main`, (2) looked up actual GitHub PR history for the branch's
`head_ref` via `gh pr list --search "head:<branch>"`, (3) where a merged PR
was found, verified representative files from the three-dot diff already
exist byte-for-byte reachable in `origin/main` (`git cat-file -e`), (4)
checked on-disk `git status` for uncommitted/untracked drift beyond the
branch tip. No branch was classified from diff-stat alone.

| Worktree path | Branch | Commit | Ahead/Behind vs origin/main | PR history | Unique/unmerged content? | Migrations | Billing logic | RN-ICA logic | Redesign-only | Disk dirty? | **Disposition** |
|---|---|---|---|---|---|---|---|---|---|---|---|
| `.copilot/repos/sns-emr` | `main` | `2b37cf5` | 0/0 (is origin/main ref) | n/a | No | — | — | — | — | Clean | **KEEP** — canonical main checkout |
| `neuro-clinical-reasoning` | `pr57-stroke-coma-ceb` | `5fd6275` | 5/65 | PR #57, #58, #59 — all **MERGED** (2026-09-02/03) | No — confirmed recert manifest/service files already present in `origin/main`; 3-dot diff is pure clean-squash residue (0 deletions) | No | No | No | No | **Dirty** (17 entries: modified recert files + stray JUnit artifacts) | **ARCHIVE** branch (fully merged); discard uncommitted local diff first (needs owner review, not auto-discarded) |
| `suasonns-fuzzy-sniffle` | `suasonns-rn-ica-command-workspace` | `e825556` | 8/239 | PR #7 — **CLOSED, not merged** | **Yes — genuinely abandoned/unmerged** (RN-ICA Clinical Command Workspace pilot) | No | No | Yes | Partial | Clean | **ARCHIVE** — abandoned via closed PR; RN-ICA future work is out of current stabilization scope |
| `suasonns-glowing-sniffle` | `suasonns-review-worktree-fluffy` | `9c6bcae` | 0/239 | No unique commits ahead of origin/main | No | No | No | No | No | **Dirty** (5 entries: modified `patients.py`, `hnp_parser_service.py`, new test file, scratch commit-msg file) | Branch itself fully contained in main → **DELETE** branch; uncommitted disk changes need owner review before worktree removal |
| `suasonns-legendary-giggle` | `suasonns-issue-63c-repository-scope-guard-stabili` | `e9010ec` | 1/63 | **No PR ever opened** | **Yes — real, isolated, unmerged** (`backend/scripts/verify_pr_scope.py` + test suite; CI-only PR-scope-guard replacement) | No | No | No | No | Clean | **KEEP** — self-contained, low-risk CI tooling; needs a PR opened (follow-up, out of current scope) |
| `suasonns-musical-guide` | `suasonns-pr11-gap-fixes` | `36e905b` | 0/309 | No unique commits ahead of origin/main | No | No | No | No | No | Clean | **DELETE** — fully contained in main |
| `suasonns-psychic-guacamole` | `feature/production-hnp-clinical-runtime` | `acc8b0a` | 66/18 | PR #66 **MERGED** 2026-09-06, but branch tip is dated 2026-09-13 (7 days **after** that merge) | **Yes — substantial, genuine unmerged work post-PR#66** (204 files, +32118/-1324 vs origin/main), including OwnerAdmin 401-retry and `t1u2v3w4x5y6`-equivalent migration fixes that overlap with independently re-derived fixes on this session's `fix/billing-readiness-authoritative-reconciliation` branch | Yes | Yes | Partial | Yes (Owner/Tenant shell, Tailwind) | Clean | **MERGE — requires reconciliation.** Do not merge blind: overlapping fixes with `fix/billing-readiness-authoritative-reconciliation` must be diffed function-by-function before a PR is opened, to avoid double-applying or conflicting with already-stabilized logic |
| `suasonns-studious-winner` | `suasonns-billing-readiness-workflow` | `7ed44d5` | 29/11 | PR #80, #84 **MERGED** (2026-09-09/10); branch tip predates PR #84's merge by ~12 min | No — 2-dot diff reduces to 8 files / 133+/-381, consistent with normal squash-merge residue | No | No | No | No | **Dirty** (20 entries: modified chart/facesheet/consent JSX files + demo-patient scratch scripts) | Branch fully merged → **ARCHIVE**; uncommitted disk changes need owner review first |
| `suasonns-super-spoon` | *(detached HEAD)* | `2b37cf5` | identical to `main` | n/a | No | — | — | — | — | Clean | **DELETE** — detached worktree, identical to main, no unique ref |
| `suasonns-upgraded-garbanzo` | `suasonns-structured-findings-backfill` | `fc427e1` | 3/134 | PR #19 **MERGED** (2026-08-29); referenced PR #21 also merged (different head branch, same feature family) | No — all key files (`reprocess_structured_findings.py`, `evidence_resweep_service.py`, `structured_findings_reprocess_service.py`) confirmed present in `origin/main` | No | No | No | No | **Dirty** (13 untracked debug/scratch scripts: `check_marker.py`, `dump_full.py`, `export_kessler_formdata.py`, etc.) | Branch fully merged → **DELETE**; untracked files are disposable debug scratch, safe to discard |
| `wt-alert-inbox` | `feature/alert-inbox-v1` | `ca79502` | 6/18 | PR #74 — **OPEN, not merged** | **Yes — active, in-flight work** (AI Patient Summary + Alert Inbox) | No | No | No | Partial | Clean | **KEEP** — open PR pending normal review; do not touch |
| `hotfix-main` | `hotfix/owner-financials-fetch-and-overlap` | `edfa4d9` | 0/5 | No unique commits ahead of origin/main | No — future-date validation behavior already reconciled into main | No | Yes (financials) | No | No | Clean | **DELETE** — fully contained in main |
| `rebuild-billing-readiness` | `fix/billing-readiness-authoritative-reconciliation` | `7b56b74` | 9/0 | *(this session's deliverable — no PR yet)* | Yes — the zero-failure baseline stabilization itself | Yes (test-only) | Yes (readiness fixes) | Yes (scoping fix) | No | Clean | **MERGE** — open a PR against `origin/main`; this is the stabilized deliverable |

## Summary by disposition

- **KEEP (3):** `main` checkout, `suasonns-issue-63c-...` (needs a PR), `wt-alert-inbox` (open PR #74).
- **MERGE (2):** `fix/billing-readiness-authoritative-reconciliation` (ready for PR), `feature/production-hnp-clinical-runtime` (needs reconciliation review first — do not merge blind).
- **ARCHIVE (2):** `pr57-stroke-coma-ceb`, `suasonns-billing-readiness-workflow` (both fully merged upstream; each worktree has uncommitted local drift that must be reviewed, not silently discarded, before removal).
- **DELETE (5):** `suasonns-review-worktree-fluffy`, `suasonns-pr11-gap-fixes`, detached `suasonns-super-spoon`, `suasonns-structured-findings-backfill`, `hotfix/owner-financials-fetch-and-overlap` (all fully contained in `origin/main`, no unique unmerged content).

No branch received an UNKNOWN disposition. Actual worktree deletion/archival
is **not executed by this report** — several worktrees carry uncommitted
local changes that must be reviewed by their owning session/engineer first,
and this session does not have authority to discard another session's
in-progress disk state.
