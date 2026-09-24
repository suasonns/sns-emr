# RNICA Governance Document Reconciliation Matrix

**STATUS:** DISCOVERY ONLY. NOT A MERGE. NOT AN IMPLEMENTATION AUTHORIZATION.
**MECHANICAL MERGE AUTHORIZED:** NO
**CANONICAL DOCUMENT SELECTED:** NO — for any of the 8 files below.

This document identifies, and does **not** resolve, 8 add/add merge
conflicts between `origin/main` and `suasonns-fantastic-memory` discovered
during a `git merge origin/main --no-edit` investigation that was
**aborted without committing** (branch state unaffected). The prior audit
pass (PR #154 description) reported 5 of these files by name from
screenshots; this pass independently re-derived the full set directly
from git and confirms **8 conflicting paths**, not 5 — the earlier count
undercounted by omitting `RNICA_GITHUB_HANDOFF_PLAN.md` and
`RNICA_PHASED_IMPLEMENTATION_PLAN.md` from the "requires decision" bucket
in some summaries even though both were always part of the 9-conflict
`git merge` output. All 8 are documented here for completeness.

## Status Enum Used Below

`IDENTICAL_MEANING` · `MAIN_SUPERSEDES_BRANCH` · `BRANCH_SUPERSEDES_MAIN` ·
`COMPLEMENTARY` · `CONFLICTING_POLICY` · `DUPLICATE_WITH_DRIFT` ·
`NOT_VERIFIED` · `REQUIRES_ROMEL_DECISION`

Every row below carries **both** an evidence-based classification (what
the content shows) **and** `REQUIRES_ROMEL_DECISION` as the final
disposition, per the explicit instruction that recency, file length,
branch/main location, filename equality, and mechanical 3-way merge are
**not** sufficient justification for selecting a side. The evidence below
is offered as the record needed for that decision, not as the decision
itself.

---

## Document Matrix

| # | File | Merge-base state | `main` introducing/latest commit | Branch introducing/latest commit | main lines | branch lines | Diff shape (vs. main) | Headings differ? |
|---|---|---|---|---|---|---|---|---|
| 1 | `docs/rnica/RNICA_ASSESSMENT_VISIT_CLASSIFICATION_RULES.md` | Does not exist at merge-base (`6f456ab2`); added independently on both sides | `cbbee2a` | `a5564b6` | 396 | 450 | +62/-6 | Yes — branch inlines Appendix A as a full table + "Appendix A Controlling Sources"; main instead **factors Appendix A out** into a new sibling file `docs/rnica/RNICA_AUTHORITY_MATRIX.md` (112 lines, main-only, not present on branch at all) and leaves a one-paragraph pointer in its place |
| 2 | `docs/rnica/RNICA_CLASSIFICATION_TEST_SCENARIOS.md` | Does not exist at merge-base | `cbbee2a` | `a5564b6` | 119 | 109 | -10 (branch is missing content main has) | No — same headings both sides |
| 3 | `docs/rnica/RNICA_VISIT_CLASSIFICATION_DECISION_TABLE.md` | Does not exist at merge-base | `cbbee2a` | `a5564b6` | 105 | 79 | -30 (branch is missing content main has) | main-only: `### 6.1 LVN Encounters a Severe/Qualifying HOPE Symptom (SNS_INTERNAL_WORKFLOW)` |
| 4 | `docs/tenant-platform/RNICA_GITHUB_HANDOFF_PLAN.md` | Does not exist at merge-base | `1ffe6db` | `1ba7fd3` | 97 | 104 | +8 (branch adds; nothing removed) | No — same headings; branch adds a blockquote note, not a new section |
| 5 | `docs/tenant-platform/RNICA_PHASED_IMPLEMENTATION_PLAN.md` | Does not exist at merge-base | `1ffe6db` | `8d25bed` | 430 | 436 | +7 (branch adds; nothing removed) | No — same pattern as #4 |
| 6 | `docs/tenant-platform/RNICA_REDESIGN_SOURCE_OF_TRUTH.md` | Does not exist at merge-base | `1ffe6db` | `86ee0e4` | 537 | 555 | +63/-42 | Yes — `# Screen 3/4/5` renamed and reordered (see Rule-Level section) |
| 7 | `docs/tenant-platform/RNICA_SCREEN_AUTHORITY_MATRIX.md` | Does not exist at merge-base | `1ffe6db` | `7836ca1` | 207 | 225 | +36/-17 | Yes — `## 3./4./5.` renamed and reordered; main additionally carries a **stub annotation** referencing a document that does not exist on `main` (see below) |
| 8 | `docs/tenant-platform/RNICA_WORKFLOW_AUTHORITY_MAP.md` | Does not exist at merge-base | `1ffe6db` | `8b1a5a5` | 140 | 149 | +17/-7 | No new headings, but the screen-order table rows and the ASCII flow diagram are reordered |

**Verification depth disclosure:** all 8 diffs above were generated from
direct blob comparison (`git show <ref>:<path>`), not from the aborted
merge's conflict markers. Files #1–#3 and #6–#8 were read at content
level (not merely heading level); files #4–#5 were confirmed to be
purely additive at content level (no main content removed). This is a
targeted content audit, not an exhaustive line-by-line legal review of
every sentence in all 8 files.

---

## Critical Cross-File Finding: `RNICA_NAVIGATION_SPECIFICATION.md`

- **Exists on branch (`HEAD`) only** — introduced by branch commits
  `49d605e` ("docs+feat(rnica): supersede workflow order 3-5") and
  `4439ff6` ("RNICA: correct workflow order to final 3=Pain 4=Diagnosis
  5=Functional"). **Does not exist on `origin/main`** (`git cat-file -e
  origin/main:...` fails — confirmed, not inferred).
- Its content states: `**[PRODUCT-AUTHORITY DECISION — 2026-09-22]** This
  is the approved order, not a suggestion: 1 Patient Story, 2 Evidence &
  Intake, 3 Pain & Symptom Burden, 4 Diagnosis & LCD, 5 Functional
  Status, 6-13 unchanged.`
- **`main`'s versions of files #7 (`RNICA_SCREEN_AUTHORITY_MATRIX.md`)
  and #8 (`RNICA_WORKFLOW_AUTHORITY_MAP.md`) each contain a matching
  `[PRODUCT-AUTHORITY UPDATE — 2026-09-22]` blockquote** that explicitly
  says the same reorder is "final" and directs the reader to
  `RNICA_NAVIGATION_SPECIFICATION.md` for the canonical order — **but
  that referenced file does not exist on `main`, and `main`'s own table
  body directly below the note still lists the pre-2026-09-22 order**
  (`3. Functional Status | 4. Pain & Symptom Burden | 5. Diagnosis &
  LCD`), contradicting the note immediately above it.
- **The branch's versions of files #6, #7, #8 already carry the
  completed 2026-09-22 reorder throughout** (table body, ASCII flow
  diagram, and — for #7/#8 — the same explanatory blockquote), and the
  branch is the only side that contains the actual authoritative
  companion document the notes point to.
- **Interpretation (evidence, not a decision):** `main` received a
  narrative annotation announcing the 2026-09-22 decision without the
  accompanying full-document update, and without the referenced
  authoritative source document. The branch appears to contain the
  completed implementation of that same already-approved decision. This
  is `BRANCH_SUPERSEDES_MAIN`-shaped evidence for files #6–#8, but is
  still recorded here as `REQUIRES_ROMEL_DECISION` — Romel is the
  authority who can confirm whether the 2026-09-22 decision was in fact
  finalized and whether the branch's companion document should become
  canonical.

---

## Rule-Level Reconciliation

### Files #1–#3 (`docs/rnica/*`) — LVN severe-symptom escalation workflow

- **`main` wording:** Defines a full LVN-escalation control: when an LVN
  visit identifies a severe/qualifying HOPE symptom, the system must
  display "RN Assessment Review Required," create a compliance-review
  item, offer discipline-authorized next actions (Request RN Visit /
  Request RN Assessment Review / Document Existing RN Review), preserve
  specific fields as immutable evidence, and must **not** auto-create or
  auto-classify an SFV. 10 matching test scenarios exist in
  `RNICA_CLASSIFICATION_TEST_SCENARIOS.md` (#10–19), and the rule is
  cross-referenced from `RNICA_AUTHORITY_MATRIX.md`.
- **Branch wording:** No equivalent rule, section, or test scenarios
  exist in any of the 3 files. The branch's Appendix A table also lacks
  the "LVN Identifies Qualifying HOPE Symptom" row present in main's
  separate `RNICA_AUTHORITY_MATRIX.md`.
- **Production/test behavior referenced:** `NOT_VERIFIED` this pass —
  whether any backend/frontend code implements this LVN-escalation
  control was not checked (out of scope for a documentation-reconciliation
  pass; would require a targeted code search).
- **Authority source:** Labeled `SNS_INTERNAL_WORKFLOW` on `main` (an SNS
  operational design decision, not a CMS/federal/state requirement) —
  so its absence from the branch is not a CMS-compliance gap, but it may
  be a real, already-designed discipline-safety control that the branch
  simply predates.
- **Patient-safety / staff-workflow / audit effects:** If main's rule
  reflects an actual implemented (or intended) control, its absence from
  the branch's narrative would not remove code behavior, but merging the
  branch's narrower docs over main's would **silently drop documentation
  of a discipline-escalation safeguard** — a governance regression risk
  if this reconciliation is ever done backwards (branch-wins).
- **Disposition:** `MAIN_SUPERSEDES_BRANCH` (evidence-based) — main
  contains materially more governance content with no corresponding loss.
- **Romel decision required:** Confirm this LVN-escalation rule is
  still the approved design, and if so, port it (and its 10 test
  scenarios, and the `RNICA_AUTHORITY_MATRIX.md` cross-reference) into
  whatever becomes canonical.

### Files #6–#8 (`docs/tenant-platform/*`) — Screen 3-5 navigation order

- **Old order (main's table body, still in effect on main today):**
  3 Functional Status → 4 Pain & Symptom Burden → 5 Diagnosis & LCD.
- **New order (branch's table body, and main's own un-implemented
  annotation):** 3 Pain & Symptom Burden → 4 Diagnosis & LCD →
  5 Functional Status — described on both sides' annotation text as
  "identify pain/symptom burden before establishing diagnosis, then
  interpret functional status with both in context."
- **Production/test behavior referenced:** `NOT_VERIFIED` this pass —
  whether the frontend screen router/navigation component currently
  implements the old or new order was not checked. This is a real,
  checkable fact (a specific route/nav-config file) that should be
  verified before Romel decides, since if production code already
  matches one order, that is strong independent evidence.
- **Authority source:** Both sides label this `SNS_INTERNAL_WORKFLOW` /
  design authority, not CMS/federal/state. This is a pure internal UX
  sequencing decision.
- **Contradiction:** `main` is internally self-contradictory (states the
  new order is "final" in a note, but its own table and diagram still
  show the old order, and the file the note cites does not exist on
  `main`). The branch is internally consistent (table, diagram, and the
  cited companion spec all agree on the new order).
- **Disposition:** `BRANCH_SUPERSEDES_MAIN` (evidence-based, strongest
  finding in this matrix) — but still gated on Romel confirming the
  2026-09-22 decision is genuinely final and that no newer main-only
  reversal exists that this pass did not see.
- **Romel decision required:** (1) Confirm the 2026-09-22 order is
  final. (2) If confirmed, `RNICA_NAVIGATION_SPECIFICATION.md` (branch-
  only today) must be ported to whatever becomes canonical, since two of
  main's own files already depend on it existing.

### Files #4–#5 (`RNICA_GITHUB_HANDOFF_PLAN.md`, `RNICA_PHASED_IMPLEMENTATION_PLAN.md`)

- Purely additive on the branch (same blockquote pointer to
  `RNICA_NAVIGATION_SPECIFICATION.md` seen in files #7–#8). No content
  is removed or contradicted relative to `main`.
- **Disposition:** `COMPLEMENTARY` — safe to carry branch's addition
  forward once (and only once) the files #6–#8 decision is made, since
  the note only makes sense if the referenced spec exists.

---

## Explicit Decision Rule (restated, followed in this pass)

A side was **not** selected based on: commit recency, file length,
branch-vs-main location, filename equality, the outcome of a mechanical
3-way merge, or wording preference. Every disposition above is
justified by: (a) presence/absence of a specific governance rule and
its test coverage (files #1–#3), (b) an internal-consistency check
against a cited, checkable companion document (files #6–#8), or (c)
a strict content-superset relationship with zero loss (files #4–#5).
No production-behavior check, executable test, or new SNS design
decision was used as justification in this pass — those remain
`NOT_VERIFIED` and are called out per row above as still required
before Romel's final call.

---

## Required Output

RNICA CONFLICT FILE COUNT: **8** (supersedes the earlier "5" count
carried in PR #154's description before this pass; PR #154's
description will be corrected to reference this matrix)

RNICA CONFLICT FILES:
1. `docs/rnica/RNICA_ASSESSMENT_VISIT_CLASSIFICATION_RULES.md`
2. `docs/rnica/RNICA_CLASSIFICATION_TEST_SCENARIOS.md`
3. `docs/rnica/RNICA_VISIT_CLASSIFICATION_DECISION_TABLE.md`
4. `docs/tenant-platform/RNICA_GITHUB_HANDOFF_PLAN.md`
5. `docs/tenant-platform/RNICA_PHASED_IMPLEMENTATION_PLAN.md`
6. `docs/tenant-platform/RNICA_REDESIGN_SOURCE_OF_TRUTH.md`
7. `docs/tenant-platform/RNICA_SCREEN_AUTHORITY_MATRIX.md`
8. `docs/tenant-platform/RNICA_WORKFLOW_AUTHORITY_MAP.md`

MAIN VERSIONS: VERIFIED BY REPOSITORY TRACE
BRANCH VERSIONS: VERIFIED BY REPOSITORY TRACE
AUTHORITATIVE COMBINED VERSION: REQUIRES ROMEL DECISION (per file — see
Rule-Level Reconciliation; evidence leans `MAIN_SUPERSEDES_BRANCH` for
files #1–#3 and `BRANCH_SUPERSEDES_MAIN` for files #4–#8)
MECHANICAL MERGE AUTHORIZED: **NO**
RNICA CANONICAL DOCUMENTS SELECTED: **NO**
IMPLEMENTATION AUTHORIZED: **NO**
