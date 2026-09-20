# README FIRST — Architecture Governance Entry Point

Status: **mandatory architecture governance document.**

## Purpose

This file is the mandatory entry point for all future AI agents,
developers, contributors, and architecture reviews involving the SNS EMR
Tenant Platform.

This document must be treated as architecture governance.

Future implementation work **MUST** review the documents listed below
before any modifications to:

- Evidence Platform
- Intelligence Harvester
- Document Intelligence
- Structured Findings
- RN ICA Intelligence
- Clinical Intelligence
- Eligibility Intelligence
- Compliance Intelligence
- Narrative Intelligence
- Tenant Platform

## Mandatory Reading Order

1. [`EVIDENCE_TRACEABILITY_VISION.md`](./EVIDENCE_TRACEABILITY_VISION.md)
2. [`EVIDENCE_INTELLIGENCE_ROADMAP.md`](./EVIDENCE_INTELLIGENCE_ROADMAP.md)
3. [`TENANT_PLATFORM_IMPLEMENTATION_GUARDRAILS.md`](./TENANT_PLATFORM_IMPLEMENTATION_GUARDRAILS.md)

(See also [`INTELLIGENCE_HARVESTER_EVOLUTION.md`](./INTELLIGENCE_HARVESTER_EVOLUTION.md)
for the phased evolution plan referenced by the roadmap above, and
[`ARCHITECTURE_INDEX.md`](./ARCHITECTURE_INDEX.md) for a single
navigation page across all of the above.)

## Architecture Protection Rules

### Rule 1 — Structured Findings Remain Canonical

Do not:

- Replace `structured_findings.py`
- Bypass structured findings
- Create a competing evidence model
- Create direct AI-to-field writing

Future systems consume structured findings. Future systems do not
replace structured findings.

### Rule 2 — Evidence-First Architecture Is Mandatory

SNS EMR is not a document summarization platform. SNS EMR is an evidence
discovery platform.

Every future intelligence feature must remain capable of answering:

> "Show me where the chart says that."

### Rule 3 — Evidence Traceability Cannot Be Downgraded

Every finding must remain capable of linking back to:

- Source document
- Document date
- Page number (when available)
- Source excerpt
- Confidence

Future development must not remove provenance. Future development must
not hide provenance.

### Rule 4 — Narrative Summaries Are Secondary

Evidence is primary. Narratives exist to organize evidence. Narratives
must not replace evidence visibility.

### Rule 5 — No Unsupported Intelligence

Future AI layers may:

- Organize evidence
- Summarize evidence
- Explain evidence

Future AI layers may not:

- Invent evidence
- Invent diagnosis
- Invent decline
- Invent prognosis

### Rule 6 — Future Tenant Development Sequence

When tenant work resumes:

1. Evidence Traceability
2. Evidence Explorer
3. Clinical Intelligence
4. Eligibility Intelligence
5. Compliance Intelligence
6. Narrative Intelligence

Do not begin with Narrative Intelligence. Do not skip Evidence
Traceability.

### Rule 7 — Owners Platform Priority

Tenant implementation remains deferred until:

- Owners Platform stabilization complete
- Owners Platform roadmap complete
- Owners Platform backlog reviewed

### Rule 8 — Architecture Decision Records

Architecture Decision Records live in [`./adr/`](./adr/) and must be
preserved:

- [ADR-001 — Structured Findings Remain Canonical](./adr/ADR-001-structured-findings-remain-canonical.md)
- [ADR-002 — Evidence Traceability Required](./adr/ADR-002-evidence-traceability-required.md)
- [ADR-003 — Evidence First Architecture](./adr/ADR-003-evidence-first-architecture.md)
- [ADR-004 — Tenant Platform Deferred Until Owners Platform Complete](./adr/ADR-004-tenant-platform-deferred-until-owners-platform-complete.md)
- [ADR-005 — Narratives Must Be Evidence Backed](./adr/ADR-005-narratives-must-be-evidence-backed.md)

Future contributors may add ADRs. Existing ADRs must not be deleted
without a replacement ADR explaining the reason.

### Rule 9 — Future AI Behavior

If a future AI agent proposes replacing:

- `structured_findings.py`
- Evidence provenance
- Document traceability
- Evidence links

the agent must first explain why the existing architecture is
insufficient and provide a migration analysis.

A simpler implementation is not automatically a better implementation.
**Traceability has priority over simplicity.**

## Success Metric

SNS EMR succeeds when users can answer:

> "Where did this information come from?"

with one click.

**The primary product goal is evidence transparency. The primary product
goal is NOT summary generation.**
