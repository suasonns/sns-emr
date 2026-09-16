# ADR-001: Structured Findings Remain Canonical

## Status

Accepted

## Context

`backend/app/services/evidence/structured_findings.py` is the existing,
proven data model that document harvesting, AI extraction, and RN ICA
field mapping all funnel through today. As intelligence layers (Clinical,
Eligibility, Compliance, Narrative) are added in the future, there is a
risk that a new, competing evidence representation gets introduced
alongside it, or that AI output writes directly into clinical fields
without passing through structured findings at all.

## Decision

Structured Findings remain the single, canonical evidence model for the
SNS EMR platform.

- Do not replace `structured_findings.py`.
- Do not bypass structured findings.
- Do not create a second, competing evidence model.
- Do not allow direct AI-to-field population.

All future intelligence layers must consume structured findings as their
input, not circumvent them.

## Consequences

- New intelligence features are additive layers built on top of
  structured findings, not parallel/alternate pipelines.
- Any proposal to introduce a new evidence model requires a new ADR that
  explicitly supersedes this one and explains the migration path.
- Consumers (Clinical Intelligence, Eligibility Intelligence, etc.) can
  rely on structured findings' shape remaining stable and authoritative.
