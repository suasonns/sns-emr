<!--
Pull request template. Fill in every applicable section before
requesting review. See docs/architecture/decision-records/ for the ADRs
governing baseline stability and migration review requirements.
-->

## Summary

## Type of Change

- [ ] Application code
- [ ] Database migration
- [ ] Documentation only
- [ ] CI/CD / configuration
- [ ] Other (describe):

## Migration PR Requirements

**Required whenever this PR adds, edits, or removes an Alembic
migration.** Leave this section as "N/A" only if the PR contains no
migration changes.

- Migration revision(s) introduced or modified:
- Down-revision / previous head:
- Linked issue (discovery, regression, or feature issue):
- Linked regression investigation template (if this migration is a fix
  for a regression — see `.github/ISSUE_TEMPLATE/regression_investigation.md`):
- Confirmed `downgrade()` is either:
  - [ ] Fully reversible (schema and data)
  - [ ] Schema-reversible with documented, expected data-content loss
        (e.g. one-time backfill) — justification:
  - [ ] Genuinely irreversible — justification (must be reviewed against
        ADR-002 before this is accepted):
- [ ] Alembic autogenerate drift probe run locally (empty diff)
- [ ] Full downgrade/upgrade roundtrip verified locally

## Verification

- [ ] Relevant tests added or updated
- [ ] Full backend test suite passes locally (if backend/migration
      changes)
- [ ] Frontend build passes locally (if frontend changes)
- [ ] No unrelated files included

## Related

Issue(s):

Related PRs:
