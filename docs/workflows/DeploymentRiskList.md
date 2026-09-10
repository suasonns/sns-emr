# Deployment Risk List

Risks and residual items to be aware of at merge/deploy time for the
Billing Readiness / Eligibility / Admissions SSOT workstream
(Priorities 1-8).

## Low Risk

- **`PatientFaceSheet.benefit_period_number/start/end` columns are now
  vestigial.** They are no longer read or written by any code path, but
  were left in place (no migration) per the "no new workstreams"
  directive. No functional risk, but a future cleanup PR should drop
  these columns once confirmed nothing external depends on them.
- **Pre-existing test defects** (see Open Defects List) are unrelated to
  this branch but will still show up in a full CI run of `tests/`; CI
  configuration for this repo should already tolerate/triage these
  (they predate this branch), but flagging in case CI gating changes.

## Medium Risk

- **Large diff surface for a single PR** (86 files changed across
  Priorities 1-8, ~11.4k insertions). While each priority was developed,
  tested, and regression-checked incrementally, reviewers should expect
  a substantial review. Recommend reviewing by priority/commit rather
  than as one flat diff, since the branch's commit history is organized
  by priority.
- **`docs/workflows/SourceOfTruthMatrix.md` reflects the final SSOT
  state as of Priority 6.** If any further facesheet fields are added
  post-merge, they should be checked against this matrix before being
  made independently editable, to avoid reintroducing the class of
  violation found and fixed for Benefit Period.

## Out of Scope (explicitly, per direction during this project)

- No NGS Connex / CMS / Medicare eligibility lookup integration was
  built or is planned as part of this PR -- insurance/payer verification
  remains an external, staff-performed process; SNS only stores,
  reviews, and audits the result. This is intentional, not a gap.

## Screenshots / Live Environment Verification

Live dev servers (frontend/backend) were not confirmed running in this
session at the time of writing this report, so before-merge visual
verification screenshots were not captured here. Recommend a short manual
smoke pass (login → patient facesheet → benefit period display →
billing readiness dashboard) against a running dev environment before
final merge approval, since this was requested as part of the
"Deployment Readiness Checklist" but could not be produced without a live
server in this session.

## Overall Assessment

No blocking deployment risks identified. The single real SSOT violation
found during audit (Benefit Period) has been fixed and re-verified.
Backend and frontend regressions are clean apart from documented,
pre-existing, unrelated defects. Recommend proceeding to PR review and
merge, with the live-environment smoke pass above as the one outstanding
manual verification step.
