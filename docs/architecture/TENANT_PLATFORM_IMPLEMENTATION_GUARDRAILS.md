# Tenant Platform Implementation Guardrails

Status: **mandatory architectural guidance. No code changes, no
implementation, no refactoring in this document.**

## Purpose

This document governs all future implementation work involving:

- Evidence Platform
- Intelligence Harvester
- Document Intelligence
- Evidence Traceability
- Clinical Intelligence
- Eligibility Intelligence
- Compliance Intelligence

**Future developers and future AI agents must review this document
before modifying the tenant platform.**

---

## Rule 1 — Structured Findings Remain the Canonical Evidence Model

Do NOT:

- Replace `structured_findings.py`
- Bypass structured findings
- Create a second, competing evidence model
- Allow direct AI-to-field population

All future intelligence layers must consume structured findings.

---

## Rule 2 — Evidence Is More Important Than Summary

The purpose of SNS EMR is not AI-generated summaries. The purpose of SNS
EMR is discoverable evidence.

Every summary must remain linked to:

- Source document
- Document type
- Page number
- Source excerpt

Evidence cannot be removed for convenience. Evidence cannot be hidden
behind narrative.

---

## Rule 3 — Future Intelligence Must Be Additive

Future layers must sit **above**:

```
Document → Evidence → Structured Findings
```

Future layers — Evidence Explorer, Clinical Intelligence, Eligibility
Intelligence, Compliance Intelligence, Narrative Intelligence — must
consume existing structured findings rather than replacing them.

---

## Rule 4 — No Architecture Downgrade

Future contributors must NOT:

- Reduce traceability
- Remove provenance
- Remove evidence links
- Remove confidence
- Remove source attribution

A simpler implementation is not automatically a better implementation.
**Traceability has priority over simplicity.**

---

## Rule 5 — Evidence Traceability Is Mandatory

Every future finding must support:

```
Document
Page
Date
Excerpt
```

If page numbers become available, page numbers must be preserved. If
coordinates become available, coordinates must be preserved.

AI-generated statements without supporting evidence are prohibited.

---

## Rule 6 — Boundaries on AI Behavior

AI may:

- Organize evidence
- Summarize evidence
- Explain evidence

AI may not:

- Invent evidence
- Invent diagnosis
- Invent prognosis
- Invent decline
- Invent source support

---

## Rule 7 — Tenant Implementation Sequence

When Tenant Platform development resumes, the required order is:

1. Evidence Traceability
2. Evidence Explorer
3. Clinical Intelligence
4. Eligibility Intelligence
5. Compliance Intelligence
6. Narrative Intelligence

Do not skip directly to Narrative Intelligence. Narrative Intelligence
depends on Evidence Traceability.

---

## Rule 8 — Owners Platform Remains Priority

Tenant Platform development remains deferred until:

- Owners Platform stabilization complete
- Owners Platform roadmap complete
- Owners Platform backlog reviewed

---

## Rule 9 — Architectural Success Metric

Success is not:

> "The AI generated a summary."

Success is:

> "A nurse can see exactly where the evidence came from."

The primary question SNS EMR must answer is:

> "Show me where the chart says that."

not:

> "What does the AI think?"
