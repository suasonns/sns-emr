# Evidence Traceability Vision

Status: **architectural guidance only — no code changes, no implementation
in this document.**

## Purpose

Define SNS EMR's future evidence-first AI architecture. This document
establishes the design principle that governs every current and future
AI-generated summary module across the platform.

## Core Principle

**The system shall not prioritize AI-generated summaries. The system
shall prioritize evidence discoverability.**

An AI summary is a convenience layer over evidence that already exists in
the clinical record. It is never the source of truth, and it must never
be presented in a way that obscures, replaces, or outranks the underlying
evidence. The system's primary job is to make the evidence easy to find,
verify, and audit — the narrative text is secondary and always
subordinate to it.

## Required Behavior for Every Extracted Finding

For every finding an AI module extracts or summarizes, the user must be
able to view, at minimum:

| Field | Description |
|---|---|
| Source document | The specific document the finding was extracted from |
| Page number | The exact page (or equivalent locator) within that document |
| Document date | The date the source document was created/signed/filed |
| Original text | The verbatim source text the finding was derived from |
| Confidence | The AI's confidence score/level for this extraction |
| Extraction source | Which model/pipeline/rule produced this finding |

No narrative statement may be rendered without a way to reach these six
fields for the evidence behind it. If any one of them is unavailable for
a given finding, the finding must be visually marked as unverified/
low-confidence rather than presented as equivalent to a fully-sourced
finding.

## Scope: Modules Governed by This Vision

This principle applies to all current and future narrative-generating
modules, including but not limited to:

- Clinical Summary
- LCD Summary
- HOPE Summary
- RN ICA Summary
- ADR Review Summary
- Eligibility Summary

Any new AI summarization module added to the platform in the future is
expected to conform to this same standard by default, not as an
afterthought.

## Required User Experience Pattern

Every narrative statement produced by these modules must render with a
direct, in-line link back to its supporting evidence — not a separate
"sources" appendix the user has to hunt for. The expected interaction
pattern:

1. User reads a narrative statement (e.g. "Patient's decline is
   consistent with hospice eligibility criteria for FTT.")
2. User can click/expand directly from that statement to see the exact
   source document, page, date, original text, confidence, and
   extraction source that produced it.
3. If a statement is a synthesis of multiple pieces of evidence, all
   contributing sources must be individually reachable from that
   statement — not merged into a single, unattributed citation.

The AI is expected to **explain where the evidence came from**, not
simply report a conclusion. A conclusion without a reachable evidence
trail is not an acceptable output from any module governed by this
vision.

## What This Document Is Not

- This is **not** an implementation spec, API contract, or data model
  design. No schemas, endpoints, or UI components are defined here.
- This is **not** a tenant-platform (patient-facing/agency-facing)
  implementation plan.
- This is **Owners Platform documentation only** — architectural intent
  to guide future design and engineering decisions, not a build order.

## Why This Matters

Clinical and compliance staff must be able to trust — and independently
verify — every AI-assisted statement in the record. An unsourced summary
is a liability in a regulated hospice/EMR context: it cannot be defended
in an audit, an ADR response, or a survey without a clear path back to
the original documentation. Prioritizing evidence discoverability over
polished narrative language is a deliberate, permanent architectural
choice, not a temporary constraint.
