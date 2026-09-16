# ADR-004: Tenant Platform Deferred Until Owners Platform Complete

## Status

Accepted

## Context

SNS EMR is developed by a single developer preparing for field testing.
Splitting effort between Owners Platform stabilization and new Tenant
Platform intelligence features (Evidence Traceability, Clinical
Intelligence, etc.) risks leaving both half-finished and unstable ahead
of field testing.

## Decision

Tenant Platform implementation work described in
`EVIDENCE_INTELLIGENCE_ROADMAP.md`, `INTELLIGENCE_HARVESTER_EVOLUTION.md`,
and `TENANT_PLATFORM_IMPLEMENTATION_GUARDRAILS.md` remains deferred until:

- Owners Platform stabilization is complete
- Owners Platform roadmap is complete
- Owners Platform backlog has been reviewed

## Consequences

- These architecture documents describe intended future direction only;
  they do not authorize starting implementation now.
- Any future AI agent or contributor proposing to begin Tenant Platform
  intelligence work must first confirm Owners Platform completion status
  against this ADR.
- This ADR may be superseded once Owners Platform work is confirmed
  complete, at which point a follow-up ADR should record that transition.
