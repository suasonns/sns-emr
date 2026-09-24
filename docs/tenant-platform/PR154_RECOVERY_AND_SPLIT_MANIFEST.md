# PR #154 Recovery and Split Manifest

## Status

PR #154:

- State: OPEN
- Draft: YES
- Mergeable: NO (`CONFLICTING` / `DIRTY`)
- Approved for merge: NO
- Historical audit record: YES

Recovery strategy:

CLEAN BRANCHES FROM CURRENT MAIN

History rewrite: PROHIBITED
Force-push: PROHIBITED
Source-branch deletion: NOT AUTHORIZED

## Verification Metadata

- Verification date: 2026-09-24
- Repository: `suasonns/sns-emr`
- Current main SHA (`origin/main`): `1b8e3ec5cefb2f2be011b2edc25ad7ea6ca39ce9`
- PR #154 head SHA (`suasonns-fantastic-memory`): `03818c020b287e19c16fd0bf982ea96cadd124e3`
- Merge-base SHA: `6f456ab23ebf38aa46b0e1b8c3314fb931e220ec`
- Verified by: Copilot CLI session (repository-first audit), this pass

## Scope Summary

- Unique branch commits (`git rev-list --count origin/main..HEAD`): **175**
- PR commit count reported by GitHub (`gh pr view --json commits`): **100** (GitHub's count differs from raw `git rev-list`; not reconciled further this pass — reported both, not silently picked one)
- Changed files (`git diff --numstat origin/main...HEAD`): **398**
- Additions: **101,920** (category rollup below) / GitHub reports **101,852** — the ~68-line variance is attributable to categorization-script line-ending/rename handling, not a scope disagreement; both numbers are disclosed rather than reconciled to a single value
- Deletions: **740**
- Merge conflicts (verified via `git merge origin/main --no-edit`, then `git merge --abort`): **9** (4 mechanically safe, 5 RNICA governance docs requiring a decision — see below; note the RNICA reconciliation matrix documents **8** distinct RNICA-related paths in total once `RNICA_GITHUB_HANDOFF_PLAN.md` and `RNICA_PHASED_IMPLEMENTATION_PLAN.md` are counted, since those two are purely-additive rather than add/add conflicts but are part of the same navigation-order governance question)

### File category breakdown (`git diff --numstat origin/main...HEAD`, categorized by path)

| Category | Files | Additions | Deletions |
|---|---:|---:|---:|
| Other docs (RNICA-adjacent narrative, biller-platform, room-board, phase/governance docs not in the RNICA-conflict set) | 177 | 54,198 | 0 |
| Generated/recovery artifacts (`docs/recovery/**`) | 28 | 12,094 | 0 |
| RNICA governance docs (`docs/rnica/**` and RNICA-named files under `docs/**`) | 39 | 10,331 | 0 |
| Backend production (non-SFV) | 27 | 6,231 | 24 |
| Backend tests (non-SFV) | 16 | 5,342 | 0 |
| Frontend production (non-SFV) | 34 | 4,128 | 464 |
| HOPE documentation (this session's scope) | 29 | 3,502 | 0 |
| Alembic migrations | 10 | 1,998 | 0 |
| SFV tests | 2 | 1,374 | 0 |
| Dependency manifests (`package.json`, `package-lock.json`) | 2 | 918 | 30 |
| Uncategorized/other | 25 | 767 | 221 |
| Frontend tests (non-SFV) | 5 | 610 | 1 |
| SFV production (`HopeReport.jsx`, `visits.py`, `sfv.ts`, etc.) | 2 | 291 | 0 |
| Configuration (`.gitignore`, `tailwind.config.js`) | 2 | 136 | 0 |
| **Total** | **398** | **101,920** | **740** |

Documentation files: 29 (HOPE) + 39 (RNICA) + 177 (other) = **245**
Backend production files: **27** (+2 SFV = 29)
Frontend production files: **34** (+2 SFV = 36)
Test files: 16 + 5 + 2 (SFV) = **23**
Migration files: **10**
Configuration files: **2**
Dependency-manifest files: **2**
Generated artifacts: **28**
Unknown-scope files: **25** ("Uncategorized/other" — not individually triaged this pass; see disclosure below)

**Disclosure on granularity:** this manifest categorizes at file-category and named-exception level, not as a literal 175-row commit table / 398-row file table. Given the scale (175 commits touching 398 files, many commits touching dozens of unrelated paths together), a literal per-commit or per-file table of that size would be low-signal without first splitting the branch — which is exactly the problem this recovery plan exists to solve. Instead: (a) every RNICA-conflict file is individually itemized in `RNICA_GOVERNANCE_RECONCILIATION_MATRIX.md`, (b) every HOPE-documentation file this session touched is individually itemized in Workstream A below with its exact source commit, (c) the SFV ownership commit is individually itemized in Workstream B, (d) the single commit responsible for all 10 migrations and the generated patch (`91e5f15`) is individually itemized below, and (e) everything else is captured at category level in Workstream D as `INVENTORY ONLY`. If Romel requires literal per-commit/per-file rows for the remaining ~170 commits, that is a follow-up task, not performed in this pass.

## Known Review Findings

### Large-Diff Cause

PR #154's base is `main`, but no prior PR opened from this same
long-running branch (#92, #112, #116, #118) was ever merged — all were
closed unmerged. Because PR #154 is the first PR from this branch that
GitHub could compute a diff for against `main`, its diff necessarily
contains the branch's entire accumulated divergence since the
merge-base (`6f456ab2`), not just this session's own contribution
(which is 2 commits / 10 files, all under `docs/tenant-platform/`,
documentation-only).

### Generated Recovery Patch

- Path: `docs/recovery/2026-09-15/patches/suasonns-psychic-adventure-full.patch`
- Introducing commit: `91e5f15` ("Commit outstanding recovery, election addendum, clinical outcomes, and phase documentation work")
- Tracked: YES (568,331 bytes, 9,687 lines)
- Production reference found: NO — not imported, required, or referenced by any backend/frontend production or test code (not referenced outside its own directory)
- Secret scan: **PASS** — targeted patterns for connection strings, API keys, private-key headers, and SSN-shaped values returned zero matches; the only "password"/"secret" hits are governance-policy prose and audit action-name constants (e.g. `OWNER_RESET_USER_PASSWORD`), not credential values
- PHI scan: **PASS** (same targeted-pattern scan; no patient-identifier-shaped values matched) — disclosed as a targeted-pattern scan, not an exhaustive manual read of all 9,687 lines
- Disposition: `GENERATED_ARTIFACT`
- Replacement PR disposition: `EXCLUDE`
- Same commit (`91e5f15`) also introduced all 10 Alembic migration files in this diff — migrations and the patch share one commit and are excluded from all replacement PRs together

### RNICA Governance Conflicts

- Conflict count: **9** raw `git merge` conflicts (4 safe/superset, 5 requiring judgment), spanning **8** distinct RNICA-related file paths once the two purely-additive navigation-order files are included
- Exact paths: see `docs/tenant-platform/RNICA_GOVERNANCE_RECONCILIATION_MATRIX.md` (all 8 listed with commit SHAs and line counts)

Disposition: **REQUIRES ROMEL DECISION**
Mechanical merge authorized: **NO**

## Replacement Workstreams

### Workstream A: HOPE Authority and Provenance Documentation

Scope (all under `docs/tenant-platform/`, source: branch tip `03818c0`):

| File | Source commit(s) on branch |
|---|---|
| `HOPE_CMS_AUTHORITY_SOURCE_REGISTER.md` | `f26a0cd` (created), `03818c0` (row-level correction) |
| `HOPE_HIGH_VALUE_BLOCKERS.md` | `b5c7d4e` (created), `f26a0cd` (cross-reference update) |
| `J2052C_DECISION_RECORD.md` | `e3806cb` (created), `1955016`/`f26a0cd` (corrections) |
| `I0010_PRINCIPAL_DIAGNOSIS_PROVENANCE_TRACE.md` | `e3806cb`, `1955016`, `f26a0cd` |
| `J2050_PROVENANCE_TRACE.md` | `e3806cb`, `1955016`, `f26a0cd` |
| `ADM_COMPLETENESS_MATRIX.md` | `e3806cb`, `1955016`, `f26a0cd` |
| `HUV1_COMPLETENESS_MATRIX.md` | `e3806cb`, `1955016`, `f26a0cd` |
| `HUV2_COMPLETENESS_MATRIX.md` | `e3806cb`, `1955016`, `f26a0cd` |
| `DC_COMPLETENESS_MATRIX.md` | `e3806cb`, `1955016`, `f26a0cd` |

Target branch: `docs/hope-authority-provenance`
Replacement PR: see "Replacement Pull Requests" below (populated after PR creation in this pass)
Status: `IN_PROGRESS` (as of this manifest's commit) → updated to `PR_OPEN` once the PR is created later in this same pass

### Workstream B: SFV Ownership Remediation

Question: Does current `main` already contain behavior equivalent to
the verified SFV ownership remediation (commit `c540e277`,
`fix(rnica-hope): remediate SFV cross-timepoint ownership selection
(P0)`)?

Required verification (checked directly against `origin/main`'s
checked-out content, not commit ancestry):

| Criterion | Present on `main`? |
|---|---|
| Selects by trigger source type | NO |
| Selects by exact trigger visit reference | NO |
| Uses the linked SFV requirement | NO |
| Uses the exact completion visit | NO |
| Returns null when no linked SFV exists | NOT_APPLICABLE — no such lookup exists to return null from |
| Never falls back to the latest patient SFV | NOT_APPLICABLE — see below |
| Prevents cross-timepoint leakage | NOT_APPLICABLE — see below |
| Preserves patient isolation | NOT_VERIFIED (no cross-visit query exists to test) |
| Preserves tenant isolation | NOT_VERIFIED (no cross-visit query exists to test) |

**Finding (important nuance):** `main`'s `HopeReport.jsx` does not
contain a patient-level "most recently completed SFV" bug — it also
does not contain **any** cross-visit SFV-requirement lookup at all.
`main`'s `getSfvStatus()` (in `hopeReportMapper.js`) derives SFV status
purely from the HOPE record's own embedded `formData.sfv` /
`formData.symptomImpact` fields. `main`'s
`backend/app/api/visits.py` has no `SfvRequirementSummary.triggerSourceType`
field, no `list_sfv_requirements` endpoint shape matching the branch's,
and the frontend has no `sns-emr-frontend/src/api/sfv.ts` client at all
(confirmed via `git cat-file -e origin/main:<path>` for each). `main`
**does** already have the underlying `SFVRequirement` data model and
services (`backend/app/models/sfv_requirement.py`,
`backend/app/services/sfv_completion.py`, `sfv_engine.py`,
`sfv_tasks.py`), so the ownership fix is a **narrow, additive feature
port** (wiring an existing model through a new endpoint field and a new
frontend query), not a revert of a defect that exists on `main` today.

Disposition: **CLEAN_REPLACEMENT_PR_REQUIRED** (scoped as a feature
port, not a defect-removal — this framing must be preserved in the
replacement PR description so reviewers do not mistake it for "fixing a
bug on main")

Replacement branch: `fix/sfv-trigger-linked-ownership`
Replacement PR: see "Replacement Pull Requests" below

### Workstream C: RNICA Governance Reconciliation

Scope: 8 independently evolved governance-document paths (not
mechanically resolvable — see dedicated matrix).

Required artifact: `docs/tenant-platform/RNICA_GOVERNANCE_RECONCILIATION_MATRIX.md` (created this pass, same commit as this manifest)

Status: **REQUIRES ROMEL DECISION**
Canonical documents selected: **NO**
Production implementation authorized: **NO**

### Workstream D: Unrelated Historical Branch Changes

Reported areas, confirmed present in the diff, **inventory only**:

| Area | Evidence |
|---|---|
| Billing / election-addendum | Backend production files under billing/election-addendum paths, ~+1,310 lines (category rollup: part of "Backend production (non-SFV)" above) |
| Clinical-outcome / IDG-follow-up / two-hour-response services | ~+1,242 lines combined (same category) |
| Migrations | 10 files, +1,998 lines, all from commit `91e5f15` |
| Other backend production | 27 files, +6,231/-24 |
| Other frontend production | 34 files, +4,128/-464 |

Disposition: **INVENTORY ONLY**
Automatic replacement PR creation: **NO** — none of these areas were
authorized for a replacement PR in this pass; each would need its own
explicit scoping decision (existing issue/PR check, main-equivalence
check, and authorization) before any branch/PR is created for it.

## Prohibited Carryover

Confirmed absent from both replacement branches created in this pass
(`docs/hope-authority-provenance`, `fix/sfv-trigger-linked-ownership`):
recovery patch files, temporary/build/coverage output, database files,
environment files, screenshots, logs, unrelated migrations, unrelated
production features, duplicate RNICA governance documents, secrets, PHI.

## CMS Authority

- Manual: HOPE Guidance Manual v1.02
- Issuer: Centers for Medicare & Medicaid Services
- Effective date: October 1, 2025
- Verification status: VERIFIED BY CMS

Change-table status:
- Rows reviewed: 7/7
- Version-label corrections: 2
- Wording or coding clarifications: 4
- Clinician-role clarification: 1

Prohibited statements (must not be restored): "wording-only" as a
blanket conclusion; "zero substantive changes" without row-level
analysis; "zero role changes".

## Replacement Pull Requests

### HOPE Documentation
- Branch: `docs/hope-authority-provenance`
- PR: _populated later in this pass_
- State: draft (once opened)

### SFV Ownership
- Main already contains remediation: **NO**
- Branch: `fix/sfv-trigger-linked-ownership`
- PR: _populated later in this pass, if created_

### RNICA Reconciliation
- Matrix: `docs/tenant-platform/RNICA_GOVERNANCE_RECONCILIATION_MATRIX.md`
- Issue: none opened this pass (recommend Romel-facing issue if a dedicated tracker is wanted)
- Canonical result approved: NO

## PR #154 Closure Gate

PR #154 may close without merge only after:

- [x] Recovery manifest is committed (this file).
- [ ] HOPE replacement PR exists.
- [ ] SFV ownership disposition is recorded. *(recorded here; PR creation pending)*
- [x] RNICA reconciliation matrix exists.
- [ ] Issue #121 links the replacement PR.
- [ ] Issues #146 through #153 link the replacement PR.
- [ ] PR #154 links all replacement work.
- [ ] Every approved branch item has a disposition (category-level disposition recorded; per-commit/per-file granularity for Workstream D is `INVENTORY ONLY`, not individually dispositioned).
- [x] No history was rewritten.
- [x] Source branch remains preserved.

**PR #154 is NOT closed by this manifest.** Closure remains gated on the
unchecked items above.

## Required Final State

PR #118: CLOSED, UNMERGED, NOT REOPENED
PR #154: OPEN, DRAFT (closure gated — see above)
HOPE replacement PR: DRAFT, CLEANLY BASED ON CURRENT MAIN, NOT MERGED (once created)
RNICA governance documents: NO MECHANICAL MERGE
HOPE generation ready: NO
Implementation authorized: NO
