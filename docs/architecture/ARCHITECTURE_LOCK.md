# SNS EMR Tenant Platform Architecture Lock

**Version:** 1.0
**Status:** Approved

## Purpose

Protect foundational architecture from accidental simplification.

This document formally locks the evidence-first architecture direction
established by the documents below. It exists to prevent future drift,
accidental redesign, or silent replacement of the evidence model,
whether by a future developer or a future AI agent working without full
context.

## Protected Components

1. `structured_findings.py`
2. Evidence Registry
3. Evidence Traceability
4. Provenance
5. Clinical Evidence Model
6. RN ICA Concept Registry

## Change Policy

Any future proposal that:

- Replaces structured findings
- Removes provenance
- Removes evidence traceability
- Bypasses Evidence Registry
- Converts evidence into unsupported AI summaries

**MUST:**

1. Create a new ADR
2. Provide migration impact analysis
3. Explain why existing architecture is insufficient
4. Preserve backwards compatibility

**No AI agent may remove these protections without explicit approval.**

## Locked Documents

The following documents, taken together, constitute the locked
architecture baseline for SNS EMR's evidence platform and its future
intelligence layers:

1. [`README_FIRST.md`](./README_FIRST.md) — mandatory entry point and
   protection rules
2. [`EVIDENCE_TRACEABILITY_VISION.md`](./EVIDENCE_TRACEABILITY_VISION.md)
3. [`INTELLIGENCE_HARVESTER_EVOLUTION.md`](./INTELLIGENCE_HARVESTER_EVOLUTION.md)
4. [`EVIDENCE_INTELLIGENCE_ROADMAP.md`](./EVIDENCE_INTELLIGENCE_ROADMAP.md)
5. [`TENANT_PLATFORM_IMPLEMENTATION_GUARDRAILS.md`](./TENANT_PLATFORM_IMPLEMENTATION_GUARDRAILS.md)
6. [`adr/ADR-001-structured-findings-remain-canonical.md`](./adr/ADR-001-structured-findings-remain-canonical.md)
7. [`adr/ADR-002-evidence-traceability-required.md`](./adr/ADR-002-evidence-traceability-required.md)
8. [`adr/ADR-003-evidence-first-architecture.md`](./adr/ADR-003-evidence-first-architecture.md)
9. [`adr/ADR-004-tenant-platform-deferred-until-owners-platform-complete.md`](./adr/ADR-004-tenant-platform-deferred-until-owners-platform-complete.md)
10. [`adr/ADR-005-narratives-must-be-evidence-backed.md`](./adr/ADR-005-narratives-must-be-evidence-backed.md)

## What Is Locked

- **The canonical evidence model.** `structured_findings.py` remains the
  single source of truth for evidence. No parallel or competing model.
- **The evidence-first principle.** Evidence is primary; narrative
  summary is secondary, in every current and future module.
- **The mandatory traceability fields.** Source document, document date,
  document type, page number, source excerpt, and confidence must remain
  attached to every finding and every narrative statement derived from it.
- **The implementation sequence.** Evidence Traceability → Evidence
  Explorer → Clinical Intelligence → Eligibility Intelligence →
  Compliance Intelligence → Narrative Intelligence. This order is locked;
  it may not be reordered or skipped.
- **The Owners Platform priority.** Tenant Platform intelligence work
  remains deferred until Owners Platform stabilization, roadmap, and
  backlog review are complete.

## What Is Not Locked

This lock governs **architectural direction and principles only**. It
does not lock:

- Specific implementation details, file names, or code structure within
  a layer, as long as the layer honors the principles above.
- The exact wording of any individual document — clarifications and
  elaborations are expected as work resumes.
- Timelines, staffing, or prioritization outside of the Owners-Platform-
  first sequencing already established.

## Change Process

This lock is not permanent or unchangeable — it is a deliberate barrier
against casual or uninformed change. To modify a locked principle:

1. Read every document listed above in full.
2. Write a new ADR that explicitly identifies which existing ADR(s) it
   supersedes and why the current architecture is insufficient.
3. Include a migration analysis: what breaks, what must be rebuilt, and
   how existing evidence traceability is preserved or intentionally
   changed.
4. Get explicit confirmation from the project owner before any code is
   written against the new direction.

A future AI agent that encounters an instruction conflicting with this
lock must surface the conflict and request explicit confirmation before
proceeding, rather than silently overriding the locked architecture.

## Why This Exists

Across this project's history, design and data direction have drifted
more than once without a clear record of what was decided and why. This
lock — together with the ADRs and guardrail documents it references —
exists so that future work builds on a stable, explicit, agreed-upon
foundation instead of re-litigating the same architectural decisions
from scratch.
