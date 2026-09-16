# Production Readiness Requirements

Status: Planning/governance artifact — required checklist for prior to
production deployment. **Do not implement/execute items from this
document unless explicitly instructed** — this defines what must
happen before go-live, it does not authorize performing the sweep now.

## Principle

Production environments must contain only production-required data.

## Platform Sweep (Prior to Production Deployment)

Perform a complete platform sweep and remove:

- [ ] Test data
- [ ] Temporary records
- [ ] Development artifacts
- [ ] Experimental configurations
- [ ] Debug records
- [ ] Obsolete alerts
- [ ] Unused seed data

## Verification (Prior to Production Deployment)

Verify:

- [ ] Backup procedures
- [ ] Restore procedures
- [ ] Data retention policies
- [ ] Storage baseline
- [ ] Audit history integrity

## Relationship to Other Roadmap/Architecture Documents

- Audit history integrity verification should confirm the existing
  audit log system (`backend/app/models/audit_log.py`, see
  `docs/architecture/CERTIFICATION_READINESS_ARCHITECTURE.md` §1.1)
  remains intact and untruncated after the sweep — the sweep must
  remove test/debug data, not legitimate audit history.
- This checklist is a gating requirement for go-live, distinct from
  the `docs/ONC_CERTIFICATION_ROADMAP.md` phases (which govern ONC
  certification specifically, not general production readiness).
- Backup/restore verification should reference whatever environment
  configuration is live at the time (see prior session's `dev.env` /
  `DATABASE_URL` investigation for how environment/database selection
  works in this codebase) — this document does not itself define the
  backup/restore procedure, only requires that it be verified before
  go-live.

## Status

Not started. This is a pre-production gate — do not mark any item
complete until it has actually been verified/performed against the
real production-candidate environment.

## Change Log

| Date | Change |
|---|---|
| 2026-09-16 | Document created: platform sweep + verification checklist required prior to production deployment. |
