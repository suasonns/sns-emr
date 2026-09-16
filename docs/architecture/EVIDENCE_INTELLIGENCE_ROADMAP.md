# Evidence Intelligence Roadmap

Status: **architecture and planning only.** No code modified, no tenant
functionality modified, no changes to `structured_findings.py`, no
implementation tickets created, no development started by this document.

## Purpose

Document the future evolution of the SNS EMR Evidence Platform.

## Current State

The evidence platform currently consists of
(`backend/app/services/evidence/`):

- `transcription_service.py`
- `ai_extraction_service.py`
- `document_harvest_job.py`
- `document_intelligence_service.py`
- `evidence_resweep_service.py`
- `harvest_service.py`
- `note_draft_service.py`
- `recovery_service.py`
- `rnica_contract.py`
- `structured_findings.py`
- `structured_findings_apply_service.py`
- `structured_findings_reprocess_service.py`

**Current capabilities:**

1. Document harvesting
2. Document classification
3. OCR fallback
4. AI extraction
5. Structured findings generation
6. Concept registry validation
7. RN ICA field mapping
8. Apply engine
9. Reprocessing
10. Evidence persistence

## Assessment

SNS has successfully solved evidence extraction. The future challenge is
no longer extraction. **The future challenge is evidence intelligence.**

## Future Roadmap

### Phase 1 — Evidence Registry Foundation

**Status:** Complete.

Current capabilities:

```
Document → Extraction → Structured Findings → RN ICA Mapping
```

### Phase 2 — Evidence Traceability Layer

**Problem:** current AI summaries expose findings but do not expose
evidence locations.

**Goal:** every finding must be traceable. For every finding, store and
expose:

- Source document
- Document type
- Page number
- Page coordinates (when available)
- Paragraph
- Line number (when available)
- Document date
- Author/provider
- Verbatim supporting quote
- Confidence

Every finding displayed in the UI must support:

```
Finding → Evidence → Document → Page → Quote
```

Clinical users should never have to search manually for evidence.

**Success criteria:** a user can answer "Where did this come from?" with
one click.

### Phase 3 — Evidence Explorer

**Problem:** current UI displays extracted findings as debugging output.

**Goal:** replace finding dumps with evidence navigation. Display:

```
Diagnosis            → Supporting Evidence
Decline Indicator    → Supporting Evidence
Hospitalization      → Supporting Evidence
Goals of Care        → Supporting Evidence
```

Evidence remains primary. Summary remains secondary.

### Phase 4 — Clinical Intelligence Layer

**Current state:** the system recognizes facts.

**Future state:** the system recognizes relationships between facts.

**Input:** structured findings.

**Output:**

- Hospitalization history
- Functional decline
- Nutritional decline
- Symptom burden
- Disease burden
- Care transitions

The system may organize evidence but must not invent evidence.

### Phase 5 — Eligibility Intelligence Layer

**Goal:** use existing evidence to identify:

- LCD-supportive findings
- Documentation gaps
- Recertification support
- Missing decline evidence
- Contradictory evidence

**Output:** evidence-supported clinical review. Not certification. Not
diagnosis. Not physician judgment replacement.

### Phase 6 — Compliance Intelligence Layer

**Goal:** surface:

- HOPE gaps
- RN ICA gaps
- Audit risks
- Missing documentation
- Conflicting documentation

All concerns must remain evidence-backed.

### Phase 7 — Narrative Intelligence Layer

**Goal:** narratives become evidence-linked:

- Admission summaries
- IDG summaries
- HOPE summaries
- RN ICA summaries
- LCD summaries
- ADR summaries

Every narrative statement must link back to source evidence. No
unsupported narrative generation allowed.

## Architectural Principles

1. **Evidence First.** Evidence is more important than summary.
2. **Traceability Required.** Every finding must support: document,
   page, date, quote.
3. **No Fabrication.** AI may organize, summarize, and explain evidence.
   AI may not invent evidence, invent diagnosis, invent decline, or
   invent prognosis.
4. **Structured Findings Remain Canonical.** The future system builds on
   `structured_findings.py`. It does not replace it.
5. **Owners Platform Priority.** No implementation work begins until:
   - Owners Platform stabilization complete
   - Owners Platform roadmap complete
   - Owners Platform backlog reviewed

   Tenant implementation is explicitly deferred. This document exists to
   preserve future direction only.
