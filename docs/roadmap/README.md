# SNS Platform Roadmap Repository

Status: Permanent planning archive — living documents, updated as decisions are made.

## Purpose

These documents preserve platform vision, future development ideas,
workflow decisions, architectural decisions, and product intelligence
so features are not forgotten, recreated differently later, or lost
during future development sessions.

**DO NOT IMPLEMENT ITEMS FROM THESE DOCUMENTS UNLESS EXPLICITLY
INSTRUCTED.** Every file in this directory is a planning artifact and
future-development repository, not a work order. Appearing in a
roadmap document is not authorization to build it.

## Directory

| Document | Platform area |
|---|---|
| [`Owner-Platform-Roadmap.md`](./Owner-Platform-Roadmap.md) | Platform/agency health, operational intelligence |
| [`Tenant-Platform-Roadmap.md`](./Tenant-Platform-Roadmap.md) | Clinical workflow, RNICA, documentation burden reduction |
| [`Biller-Platform-Roadmap.md`](./Biller-Platform-Roadmap.md) | Billing, revenue cycle, DDE, claim lifecycle |
| [`AI-Clinical-Intelligence-Roadmap.md`](./AI-Clinical-Intelligence-Roadmap.md) | All current and future AI concepts |
| [`Analytics-And-Agency-Health-Roadmap.md`](./Analytics-And-Agency-Health-Roadmap.md) | Operational-friction analytics driving roadmap prioritization |
| [`Audit-Shield-And-Compliance-Roadmap.md`](./Audit-Shield-And-Compliance-Roadmap.md) | Evidence provenance, audit trails, compliance coaching |
| [`Future-Ideas-And-Research.md`](./Future-Ideas-And-Research.md) | Intake log for every new idea before it goes anywhere else |

## Development Rule

Before creating new features:

1. Check roadmap documents.
2. Verify the feature does not already exist as a future concept.
3. Verify platform ownership.
4. Verify no overlap exists between Owner Platform, Tenant Platform,
   and Biller Platform.
5. Update roadmap documents when new design decisions are made.

Roadmap documents become the source of truth for future platform
evolution. They preserve institutional knowledge and prevent ideas
from being lost between development sessions.

## Relationship to `/docs/architecture/`

`/docs/architecture/` governs **approved, locked** architecture
decisions (Evidence Platform, ONC certification readiness) that must
not be violated. `/docs/roadmap/` is different: it is a **capture and
planning** space for ideas, visions, and future concepts that have not
been approved for implementation. An idea can — and should — move from
`Future-Ideas-And-Research.md` through a platform roadmap file and,
only once explicitly approved and built, be reflected back into
`/docs/architecture/` as a locked decision.
