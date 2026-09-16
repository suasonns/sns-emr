# Architecture Index

Single navigation page for the SNS EMR Evidence Platform and Tenant
Platform intelligence architecture. Start here, or at
[`README_FIRST.md`](./README_FIRST.md), before touching any of the
systems this architecture governs.

## Vision

[`EVIDENCE_TRACEABILITY_VISION.md`](./EVIDENCE_TRACEABILITY_VISION.md) —
why the platform prioritizes evidence discoverability over AI-generated
summaries, and the six required fields (source document, page number,
document date, original text, confidence, extraction source) every
finding must expose.

## Roadmap

- [`INTELLIGENCE_HARVESTER_EVOLUTION.md`](./INTELLIGENCE_HARVESTER_EVOLUTION.md)
  — current harvester state and the 6-phase evolution path (Document
  Intelligence → Evidence Traceability → Clinical → Eligibility →
  Compliance → Narrative Intelligence).
- [`EVIDENCE_INTELLIGENCE_ROADMAP.md`](./EVIDENCE_INTELLIGENCE_ROADMAP.md)
  — the fuller 7-phase roadmap (adds the Evidence Explorer phase) with
  success criteria per phase.

## Protected Decisions

[`ARCHITECTURE_LOCK.md`](./ARCHITECTURE_LOCK.md) — the locked baseline.
Defines Protected Components (`structured_findings.py`, concept
registry, evidence provenance, evidence traceability, document
intelligence pipeline, RN ICA evidence mappings) and the change policy
required to modify them (ADR + migration impact analysis + insufficiency
justification + backward compatibility preservation).

## Implementation Guardrails

[`TENANT_PLATFORM_IMPLEMENTATION_GUARDRAILS.md`](./TENANT_PLATFORM_IMPLEMENTATION_GUARDRAILS.md)
— the 9 mandatory rules for any future implementation work: structured
findings stay canonical, evidence over summary, additive-only layers, no
traceability downgrades, mandatory evidence fields, AI behavior
boundaries, required build sequence, Owners Platform priority, and the
architectural success metric.

## Architecture Decision Records (ADRs)

See the [ADR index](./adr/README.md) for the full table. Currently
accepted:

| ADR | Title |
|---|---|
| [ADR-001](./adr/ADR-001-structured-findings-remain-canonical.md) | Structured Findings Remain Canonical |
| [ADR-002](./adr/ADR-002-evidence-traceability-required.md) | Evidence Traceability Required |
| [ADR-003](./adr/ADR-003-evidence-first-architecture.md) | Evidence-First Architecture |
| [ADR-004](./adr/ADR-004-tenant-platform-deferred-until-owners-platform-complete.md) | Tenant Platform Deferred Until Owners Platform Complete |
| [ADR-005](./adr/ADR-005-narratives-must-be-evidence-backed.md) | Narratives Must Be Evidence-Backed |

## Future Tenant Work Sequence

When Tenant Platform intelligence work resumes (only after Owners
Platform stabilization, roadmap, and backlog review are complete — see
ADR-004), it must proceed in this order, without skipping steps:

```
Evidence Registry
  ↓
Evidence Traceability
  ↓
Evidence Explorer
  ↓
Clinical Intelligence
  ↓
Eligibility Intelligence
  ↓
Compliance Intelligence
  ↓
Narrative Intelligence
```

## Core Principles (preserved across every document above)

1. **Evidence First** — evidence outranks AI-generated summary in every
   module.
2. **Evidence Traceability** — every finding carries source document,
   page, date, excerpt, confidence, and extraction source.
3. **Structured Findings Remain Canonical** — `structured_findings.py`
   is not replaced, bypassed, or duplicated by a competing model.
4. **No Direct AI-to-Field Population** — AI output must pass through
   structured findings, never write directly into clinical fields.
5. **No Unsupported AI Conclusions** — AI may organize, summarize, and
   explain evidence; it may not invent evidence, diagnosis, decline, or
   prognosis.
6. **Narratives Must Be Evidence-Backed** — every narrative statement
   links back to the specific evidence that supports it.
7. **Tenant Platform Deferred Until Owners Platform Completion** — no
   Tenant Platform intelligence implementation begins until Owners
   Platform stabilization, roadmap, and backlog review are complete.

## For Future AI Agents

Read [`README_FIRST.md`](./README_FIRST.md) in full before making any
change involving the Evidence Platform, Intelligence Harvester,
Structured Findings, RN ICA Intelligence, Clinical Intelligence,
Eligibility Intelligence, Compliance Intelligence, Narrative
Intelligence, or Tenant Platform. If a requested change would replace,
bypass, or downgrade a Protected Component, stop and surface the
conflict per `ARCHITECTURE_LOCK.md`'s change process rather than
proceeding.
