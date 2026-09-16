# Intelligence Harvester Evolution

Status: **planning and architecture only — no code changes, no
tenant-platform implementation, no refactoring, no modifications to
`structured_findings.py` in this document.**

## Purpose

Document the future evolution path of SNS EMR's intelligence harvester
and evidence engine.

## Current State

The current system successfully performs:

- Document harvesting
- Evidence extraction
- Concept normalization
- Structured findings generation
- RN ICA field mapping
- Evidence application

Primary components (`backend/app/services/evidence/`):

- `document_harvest_job.py`
- `document_intelligence_service.py`
- `harvest_service.py`
- `structured_findings.py`
- `structured_findings_apply_service.py`
- `evidence_resweep_service.py`

The current architecture is **fact extraction-focused**.

## Future State

The architecture should evolve from:

```
Documents → Structured Findings → Form Population
```

into:

```
Documents
  → Evidence Registry
  → Structured Findings
  → Clinical Intelligence
  → Compliance Intelligence
  → Eligibility Intelligence
  → Narrative Generation
  → Form Population
```

## Phase 1 (Complete) — Document Intelligence

**Objectives:**
- Identify documents
- Classify documents
- Extract evidence
- Normalize findings
- Preserve source excerpts

**Status:** Complete.

## Phase 2 (Future) — Evidence Traceability Layer

**Objectives:** every finding must contain:

- Source document
- Document date
- Document type
- Page number
- Paragraph
- Original text
- Confidence
- Extraction source

**Goal:** every finding must be auditable. AI must expose evidence
rather than create unsupported conclusions.

## Phase 3 (Future) — Clinical Intelligence Layer

**Objectives:** reason across findings. Identify:

- Terminal conditions
- Related diagnoses
- Functional decline
- Nutritional decline
- Hospitalization burden
- Symptom burden
- Goals-of-care patterns

**Output:** clinical interpretation — not simple extraction.

## Phase 4 (Future) — Eligibility Intelligence Layer

**Objectives:** evaluate evidence supporting:

- LCD criteria
- Six-month prognosis indicators
- Disease-specific support
- Ongoing decline
- Recertification support

**Output:** evidence-supported eligibility assessment. Not physician
replacement. Not certification. Only clinical support.

## Phase 5 (Future) — Compliance Intelligence Layer

**Objectives:** identify:

- Missing evidence
- Contradictory evidence
- Unsupported diagnoses
- HOPE data gaps
- RN ICA data gaps
- Audit risks
- ADR risks

**Output:** compliance readiness dashboard.

## Phase 6 (Future) — Narrative Intelligence Layer

**Objectives:** generate:

- Admission summaries
- IDG summaries
- LCD support summaries
- HOPE summaries
- RN ICA summaries
- Recertification narratives

All narrative content must be linked to supporting evidence. Narrative
statements without evidence links are prohibited.

## Architectural Guardrails

1. **Evidence first.** Evidence always takes precedence over summary.
2. **No fabrication.** AI may organize evidence. AI may explain evidence.
   AI must not invent evidence.
3. **Traceability required.** Every future intelligence feature must
   remain linked to: document, page, source excerpt.
4. **Structured findings remain the source of truth.** Do not replace
   `structured_findings.py`. Future intelligence layers must consume
   structured findings rather than bypass them.
5. **Tenant platform deferred.** This document is future planning only.
   Implementation shall not begin until Owners Platform stabilization
   and completion are achieved.
