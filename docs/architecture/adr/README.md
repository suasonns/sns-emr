# Architecture Decision Records — Index

This directory contains the Architecture Decision Records (ADRs) for the
SNS EMR Evidence Platform and Tenant Platform intelligence direction. See
[`../README_FIRST.md`](../README_FIRST.md) and
[`../ARCHITECTURE_LOCK.md`](../ARCHITECTURE_LOCK.md) for the governance
context these ADRs support.

| ADR | Title | Status |
|---|---|---|
| [ADR-001](./ADR-001-structured-findings-remain-canonical.md) | Structured Findings Remain Canonical | Accepted |
| [ADR-002](./ADR-002-evidence-traceability-required.md) | Evidence Traceability Required | Accepted |
| [ADR-003](./ADR-003-evidence-first-architecture.md) | Evidence-First Architecture | Accepted |
| [ADR-004](./ADR-004-tenant-platform-deferred-until-owners-platform-complete.md) | Tenant Platform Deferred Until Owners Platform Complete | Accepted |
| [ADR-005](./ADR-005-narratives-must-be-evidence-backed.md) | Narratives Must Be Evidence-Backed | Accepted |

## Adding a New ADR

1. Number sequentially (`ADR-006`, `ADR-007`, ...).
2. Use the same section structure as existing ADRs: Status, Context,
   Decision, Consequences.
3. If a new ADR supersedes an existing one, state that explicitly in
   both documents and update the Status column above.
4. Existing ADRs must not be deleted without a replacement ADR explaining
   the reason (per `ARCHITECTURE_LOCK.md`).
5. Add the new ADR to this index.
